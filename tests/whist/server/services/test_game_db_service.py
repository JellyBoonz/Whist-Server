from unittest.mock import patch

from bson import ObjectId
from whist.core.session.matcher import RandomMatcher

from tests.whist.server.base_player_test_case import BasePlayerTestCase
from whist.server.database import db
from whist.server.database.game import GameInDb
from whist.server.services.error import GameNotFoundError, GameNotUpdatedError
from whist.server.services.game_db_service import GameDatabaseService


class GameDdServiceTestCase(BasePlayerTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.service = GameDatabaseService()
        self.game = GameInDb.create_with_pwd(game_name='test', hashed_password='abc',
                                             creator=self.player)

    def test_add(self):
        game_id = self.service.add(self.game)
        self.game.id = ObjectId(game_id)
        self.assertEqual(self.game, self.service.get(game_id))
        self.assertEqual(1, db.game.count_documents({}))

    def test_add_duplicate(self):
        game_id_first = self.service.add(self.game)
        game_id_second = self.service.add(self.game)
        self.assertEqual(game_id_first, game_id_second)

    def test_not_existing(self):
        game_id = '1' * 24
        error_msg = f'Game with id "{game_id}" not found.'
        with self.assertRaisesRegex(GameNotFoundError, error_msg):
            self.service.get(game_id)

    def test_get_by_name(self):
        game_id = self.service.add(self.game)
        self.game.id = ObjectId(game_id)
        self.assertEqual(self.game, self.service.get_by_name('test'))

    def test_save(self):
        game_id = self.service.add(self.game)
        self.game.id = game_id
        self.game.table.min_player = 3
        self.service.save(self.game)
        game = self.service.get(game_id)
        self.assertEqual(3, game.table.min_player)

    def test_save_wrong_id(self):
        _ = self.service.add(self.game)
        self.game.id = '1' * 24
        self.game.table.min_player = 3
        with self.assertRaises(GameNotFoundError):
            self.service.save(self.game)

    @patch('pymongo.results.UpdateResult.modified_count', return_value=1)
    def test_save_update_error(self, result_mock):
        game_id = self.service.add(self.game)
        self.game.id = game_id
        self.game.table.min_player = 3
        with self.assertRaises(GameNotUpdatedError):
            self.service.save(self.game)

    def test_save_started_table(self):
        game_id = self.service.add(self.game)
        self.game.id = game_id
        self.game.table.min_player = 1
        self.game.ready_player(self.player)
        self.game.start(self.player, RandomMatcher)
        self.service.save(self.game)
        db_game = self.service.get(game_id)
        self.assertTrue(self.game.table.started)
        self.assertTrue(db_game.table.started)
