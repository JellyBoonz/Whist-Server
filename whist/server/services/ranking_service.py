"""Handles all internal request related to ranking and ratings of users."""
from whist.core.user.player import Player

from whist.server.database import db


class RankingService:
    """
    Service to retrieve information of users' ranking based of their rating.
    """
    _instance = None
    _user = None

    _ASCENDING = 1
    _DESCENDING = -1

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RankingService, cls).__new__(cls)
            cls._users = db.user
        return cls._instance

    @classmethod
    def all(cls, order: str) -> list[Player]:
        """
        Returns a list of all users in order of their rating.
        :param order: Integer either 1 for ascending or -1 for descending order.
        """
        mongodb_order = cls._convert_order_to_mongodb(order)
        ranked_users = cls._user.find().sort({'rating': mongodb_order})
        return ranked_users

    @classmethod
    def _convert_order_to_mongodb(cls, order: str) -> int:
        """
        Converts the string ascending and descending to the required integers 1 and -1
        :param order: string 'ascending' or 'descending'
        :return: 1 or -1
        """
        if order == 'ascending':
            return cls._ASCENDING
        if order == 'descending':
            return cls._DESCENDING

        raise ValueError(f'"order" must either be "ascending" or "descending", but was "{order}"')
