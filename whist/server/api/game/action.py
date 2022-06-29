"""Route to interaction with a table."""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Security, HTTPException, status
from pydantic import BaseModel
from whist.core.error.table_error import PlayerNotJoinedError, TableNotReadyError
from whist.core.session.matcher import RandomMatcher, RoundRobinMatcher, Matcher
from whist.core.user.player import Player

from whist.server.database.error import PlayerNotCreatorError
from whist.server.database.room import RoomInDb
from whist.server.services.authentication import get_current_user
from whist.server.services.channel_service import ChannelService
from whist.server.services.error import RoomNotFoundError
from whist.server.services.error import UserNotReadyError
from whist.server.services.room_db_service import RoomDatabaseService
from whist.server.web_socket.events.event import RoomStartedEvent

router = APIRouter(prefix='/game')


class StartModel(BaseModel):
    """
    A model to ease data posting to start a room.
    """
    matcher_type: Optional[str] = None

    @property
    def matcher(self) -> Matcher:
        """
        Gets the matcher posted to start the route.
        """
        return RoundRobinMatcher if self.matcher_type == 'robin' else RandomMatcher


# Most of them are injections.
# pylint: disable=too-many-arguments
@router.post('/action/start/{game_id}', status_code=200)
def start_room(room_id: str, model: StartModel, background_tasks: BackgroundTasks,
               user: Player = Security(get_current_user),
               room_service=Depends(RoomDatabaseService),
               channel_service: ChannelService = Depends(ChannelService)) -> dict:
    """
    Allows the creator of the table to start it.
    :param room_id: unique identifier of the room
    :param model: model containing configuration of the room.
    :param background_tasks: asynchronous handler
    :param user: Required to identify if the user is the creator.
    :param room_service: Injection of the room database service. Requires to interact with the
    database.
    :param channel_service: Injection of the websocket channel manager.
    :return: dictionary containing the status of whether the table has been started or not.
    Raises 403 exception if the user has not the appropriate privileges.
    """
    room: RoomInDb = room_service.get(room_id)

    try:
        room.start(user, model.matcher)
        room.current_rubber.current_game().next_hand()
        room_service.save(room)
        background_tasks.add_task(channel_service.notify, room_id, RoomStartedEvent())
    except PlayerNotCreatorError as start_exception:
        message = 'Player has not administrator rights at this table.'
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from start_exception
    except TableNotReadyError as ready_error:
        message = 'At least one player is not ready and therefore the table cannot be started'
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from ready_error
    else:
        return {'status': 'started'}


@router.post('/action/ready/{room_id}', status_code=200)
def ready_player(room_id: str, user: Player = Security(get_current_user),
                 game_service=Depends(RoomDatabaseService)) -> dict:
    """
    A player can mark theyself to be ready.
    :param room_id: unique identifier of the room
    :param user: Required to identify the user.
    :param game_service: Injection of the room database service. Requires to interact with the
    database.
    :return: dictionary containing the status of whether the action was successful.
    Raises 403 exception if the user has not be joined yet.
    """

    room = game_service.get(room_id)

    try:
        room.ready_player(user)
        game_service.save(room)
    except PlayerNotJoinedError as ready_error:
        message = 'Player has not joined the table yet.'
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from ready_error
    return {'status': f'{user.username} is ready'}


@router.post('/action/unready/{room_id}', status_code=200)
def unready_player(room_id: str, user: Player = Security(get_current_user),
                   game_service=Depends(RoomDatabaseService)) -> dict:
    """
    A player can mark themself to be unready.
    :param room_id: unique identifier of the room
    :param user: Required to identify the user.
    :param game_service: Injection of the room database service. Requires to interact with the
    database.
    :return: dictionary containing the status of whether the action was successful.
    Raises 403 exception if the user has not be joined yet.
    Raises 404 exception if game_id is not found
    Raises 400 exception if player is not ready
    """

    room = game_service.get(room_id)

    try:
        room.unready_player(user)
        game_service.save(room)
    except PlayerNotJoinedError as join_error:
        message = 'Player not joined yet.'
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from join_error
    except RoomNotFoundError as game_error:
        message = 'Room id not found'
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from game_error
    except UserNotReadyError as ready_error:
        message = 'Player not ready'
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from ready_error
    return {'status': f'{user.username} is unready'}
