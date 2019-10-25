# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch, Mock

from oauthlib.oauth2.rfc6749.tokens import OAuth2Token
from requests.exceptions import ConnectionError
from requests import Response


from context import session, SierraSession, __version__


class TestMockedSierraSession(unittest.TestCase):
    """Tests SierraSession using mocks"""

    def setUp(self):
        self.base = 'https://yourlibraryserver.com/iii/sierra-api/v5/'
        self.key = 'my_key'
        self.secret = 'my_secret'

    def test_session_without_parameters(self):
        with self.assertRaises(TypeError):
            with SierraSession() as s:
                pass

    def test_session_without_base_url(self):
        with self.assertRaises(TypeError):
            with SierraSession(None, self.key, self.secret) as s:
                pass

    def test_session_with_key_none_raises_exception(self):
        key = None
        secret = 'some_secret'
        with self.assertRaises(TypeError):
            with SierraSession(self.base, key, secret) as s:
                pass

    def test_session_with_secret_none_raises_exception(self):
        key = 'some_key'
        secret = None
        with self.assertRaises(TypeError):
            with SierraSession(self.base, key, secret):
                pass

    @patch('context.SierraSession')
    def test_session_with_incorrect_arguments_raises_exception(self, mocked_session):
        mocked_session.side_effect = Exception(ConnectionError)
        with self.assertRaises(ConnectionError):
            with SierraSession(self.base, self.key, self.secret):
                pass

    @patch('context.SierraSession.get_token')
    def test_session_default_headers(self, mocked_token):
        default_headers = {
            'User-Agent': f'BookOps-Sierra-API-wrapper',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': 'application/json',
            'Connection': 'keep-alive'}
        with SierraSession(self.base, self.key, self.secret) as s:
            self.assertEqual(
                s.headers, default_headers)

    @patch('context.SierraSession.send')
    @patch('context.SierraSession.get_token')
    def test_session_token(self, mocked_token, mocked_response):
        bid = '10000002'
        mocked_response.url = f'https://yourlibraryserver.com/iii/sierra-api/v5/{bid}'
        mocked_response.json = {
            "id":"10000002",
            "updatedDate":"2011-10-17T23:42:16Z",
            "createdDate":"2008-12-13T15:46:45Z",
            "deleted":False,
            "suppressed":False,
            "lang":
                {
                    "code":"ger",
                    "name":"German"
                },
            "title":"Dante Alighieri 1985 : in memoriam Hermann Gmelin",
            "author":"",
            "materialType":
                {
                    "code":"a",
                    "value":"BOOK/TEXT"
                },
            "bibLevel":
                {
                "code":"m",
                "value":"MONOGRAPH"
                },
            "publishYear":1985,
            "catalogDate":"2000-12-15",
            "country":
                {
                    "code":"gw ",
                    "name":"Germany"
                }
        }

        with SierraSession(self.base, self.key, self.secret) as s:
            response = s.bib_get_by_id(bid)
            self.assertEqual(response.url, mocked_response.url)


if __name__ == '__main__':
    unittest.main()
