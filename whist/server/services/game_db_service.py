"""Game database connector"""
from typing import Optional

from bson import ObjectId
from whist.core.user.player import Player

from whist.server.database import db
from whist.server.database.room import RoomInDb
from whist.server.services.error import RoomNotFoundError, GameNotUpdatedError


class RoomDatabaseService:
    """
    Handles interactions with the game database.
    """
    _instance = None
    _rooms = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RoomDatabaseService, cls).__new__(cls)
            cls._rooms = db.game
        return cls._instance

    # pylint: disable=too-many-arguments
    @classmethod
    def create_with_pwd(cls, game_name: str, creator: Player, hashed_password: Optional[str] = None,
                        min_player: Optional[int] = None,
                        max_player: Optional[int] = None) -> 'RoomInDb':
        """
        Factory method to create a Game in database object.
        :param game_name: name of this session
        :param creator: player object of the host
        :param hashed_password: the hash value of the password required to join
        :param min_player: the minimum amount of player to start a room
        :param max_player: the maximum amount of player that can join this session
        :return: the Game object
        """
        min_player = 4 if min_player is None else int(min_player)
        max_player = 4 if max_player is None else int(max_player)
        room = RoomInDb.create(game_name, creator, min_player, max_player)
        return RoomInDb(**room.dict(), hashed_password=hashed_password)

    @classmethod
    def add(cls, room: RoomInDb) -> str:
        """
        Adds a game to the database.
        :param room: to be added
        :return: The id of the successful added game.
        """
        try:
            room: RoomInDb = cls.get_by_name(room.room_name)
            return str(room.id)
        except RoomNotFoundError:
            room_id = cls._rooms.insert_one(room.dict(exclude={'id'}))
            return str(room_id.inserted_id)

    @classmethod
    def all(cls) -> [RoomInDb]:
        """
        Returns all rooms in the database.
        """
        return [RoomInDb(**room) for room in cls._rooms.find()]

    @classmethod
    def get(cls, room_id: str) -> RoomInDb:
        """
        Retrieves a room from the database.
        :param room_id: of the room
        :return: the room database object
        """
        room = cls._rooms.find_one(ObjectId(room_id))
        if room is None:
            raise RoomNotFoundError(room_id)
        return RoomInDb(**room)

    @classmethod
    def get_by_name(cls, room_name: str) -> RoomInDb:
        """
        Similar to 'get(room_id)', but queries by room_name instead of room id.
        :param room_name: of the room
        :return: the room database object
        """
        room = cls._rooms.find_one({'table.name': room_name})
        if room is None:
            raise RoomNotFoundError(game_name=room_name)
        return RoomInDb(**room)

    @classmethod
    def save(cls, room: RoomInDb) -> None:
        """
        Saves an updated game object to the database.
        :param room: updated game object
        :return: None. Raises GameNotFoundError if it could not find a game with that ID. Raises
        a general GameNotUpdatedError if the game could not be saved.
        """
        query = {'_id': ObjectId(room.id)}
        values = {'$set': room.dict()}
        result = cls._rooms.update_one(query, values)
        if result.matched_count != 1:
            raise RoomNotFoundError(room.id)
        if result.modified_count != 1:
            raise GameNotUpdatedError(room.id)
