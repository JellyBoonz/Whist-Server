"""Game models"""
from typing import Optional

from pydantic import BaseModel, Field
from whist.core.session.table import Table
from whist.core.user.player import Player

from whist.server.database.id_wrapper import PyObjectId
from whist.server.database.warning import PlayerAlreadyJoinedWarning
from whist.server.services.password import PasswordService


class Game(BaseModel):
    """
    Game DAO
    id: unique identifier for a game.
    creator: user id as string of the player how created that session.
    players: list of user ids of player that joined the game.
    """
    id: Optional[PyObjectId] = Field(alias='_id')
    creator: Player
    table: Table = None

    @classmethod
    def create(cls, game_name: str, creator: Player,
               min_player: int = 4, max_player: int = 4) -> 'Game':
        """
        Factory method to create a Game object.
        :param game_name: name of the this session
        :param creator: player object of the host
        :param min_player: the minimum amount of player to start a game
        :param max_player: the maximum amount of player that can join this session
        :return: the Game object
        """
        table = Table(name=game_name, min_player=min_player, max_player=max_player)
        table.join(creator)
        return Game(creator=creator, table=table)

    @property
    def game_name(self) -> str:
        """
        :return: name of the game.
        """
        return self.table.name

    @property
    def players(self) -> list[Player]:
        """
        :return: list of user ids that joined the game.
        """
        return self.table.users.players

    def join(self, user: Player) -> bool:
        """
        Adds the user to this game.
        :param user: user that wants to join.
        :return: True if successful else an error or warning is raised.
        :raise: PlayerAlreadyJoinedWarning when a player tries to join again.
        """
        if user in self.players:
            raise PlayerAlreadyJoinedWarning(
                f'User with name "{user.username}" has already joined.')
        self.table.join(user)
        return True


class GameInDb(Game):
    """
    Game DO
    """
    hashed_password: Optional[str]

    # pylint: disable=too-many-arguments
    @classmethod
    def create_with_pwd(cls, game_name: str, creator: Player, hashed_password: Optional[str] = None,
                        min_player: int = 4, max_player: int = 4) -> 'GameInDb':
        """
        Factory method to create a Game in database object.
        :param game_name: name of the this session
        :param creator: player object of the host
        :param hashed_password: the hash value of the password required to join
        :param min_player: the minimum amount of player to start a game
        :param max_player: the maximum amount of player that can join this session
        :return: the Game object
        """
        game = super().create(game_name, creator, min_player, max_player)
        return GameInDb(**game.dict(), hashed_password=hashed_password)

    def verify_password(self, password: Optional[str]):
        """
        Verifies the password for a specific user.
        :param password: plain text of the password
        :return: True if verified or there was not password set in the first place. All other
        cases returns False.
        """
        if self.hashed_password is None and password is None:
            return True
        return PasswordService.verify(password, self.hashed_password)
