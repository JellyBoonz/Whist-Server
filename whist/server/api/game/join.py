"""
Route to join a game.
"""
from typing import Dict

from fastapi import APIRouter, HTTPException, Security, status, Depends
from whist.core.user.player import Player

from whist.server.database.warning import PlayerAlreadyJoinedWarning
from whist.server.services.authentication import get_current_user
from whist.server.services.channel_service import ChannelService
from whist.server.services.game_db_service import GameDatabaseService
from whist.server.services.password import PasswordService
from whist.server.web_socket.events.event import PlayerJoinedEvent

router = APIRouter(prefix='/game')


# Most of them are injections.
# pylint: disable=too-many-arguments
@router.post('/join/{game_id}', status_code=200)
def join_game(game_id: str, request: Dict[str, str], user: Player = Security(get_current_user),
              pwd_service=Depends(PasswordService),
              game_service=Depends(GameDatabaseService),
              channel_service: ChannelService = Depends(ChannelService)):
    """
    User requests to join a game.
    :param game_id: unique identifier for a game
    :param request: must contain the key 'password'
    :param user: that tries to join the game. Must be authenticated.
    :param pwd_service: Injection of the password service. Required to create and check passwords.
    :param game_service: Injection of the game database service. Requires to interact with the
    database.
    :param channel_service: Injection of the websocket channel manager.
    :return: the status of the join request. 'joined' for successful join
    """
    game = game_service.get(game_id)
    if game.hashed_password is not None:
        game_pwd = request['password']

        if not pwd_service.verify(game_pwd, game.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Wrong game password.",
                headers={"WWW-Authenticate": "Basic"},
            )
    try:
        game.join(user)
        game_service.save(game)
        channel_service.notify(game_id, PlayerJoinedEvent(player=user))
    except PlayerAlreadyJoinedWarning:
        return {'status': 'already joined'}
    return {'status': 'joined'}
