from unittest.mock import MagicMock

from tests.whist.server.base_token_case import TestCaseWithToken
from whist.server.database.game import GameInDb
from whist.server.services.password import PasswordService


class CreateGameTestCase(TestCaseWithToken):
    def setUp(self) -> None:
        super().setUp()
        self.game_in_db_mock = MagicMock(create_with_pwd=MagicMock())
        self.app.dependency_overrides[GameInDb] = lambda: self.game_in_db_mock
        self.game_service_mock.add = MagicMock(return_value=1)
        self.app.dependency_overrides[PasswordService] = lambda: MagicMock(hash=MagicMock(
            return_value='abc'))

    def test_post_game(self):
        data = {'game_name': 'test', 'password': 'abc'}
        response = self.client.post(url='/game/create', json=data, headers=self.headers)
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(1, response.json()['game_id'])
        self.game_service_mock.create_with_pwd.assert_called_once_with(
            game_name='test', hashed_password='abc', creator=self.player_mock)

    def test_post_game_without_pwd(self):
        data = {'game_name': 'test'}
        response = self.client.post(url='/game/create', json=data, headers=self.headers)
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(1, response.json()['game_id'])
        self.game_service_mock.create_with_pwd.assert_called_once_with(
            game_name='test', hashed_password=None, creator=self.player_mock)

    def test_post_game_without_name(self):
        data = {'password': 'abc'}
        response = self.client.post(url='/game/create', json=data, headers=self.headers)
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual('"game_name" is required.', response.json()['detail'])

    def test_post_game_with_settings(self):
        data = {'game_name': 'test', 'password': 'abc', 'min_player': 1, 'max_player': 1}
        response = self.client.post(url='/game/create', json=data, headers=self.headers)
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(1, response.json()['game_id'])
        self.game_service_mock.create_with_pwd.assert_called_once_with(
            game_name='test', hashed_password='abc', creator=self.player_mock, min_player=1,
            max_player=1)
