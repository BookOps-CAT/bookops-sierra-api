# -*- coding: utf-8 -*-

"""
WARNING
    These tests require valid Sierra API credentials
    The credentials should be placed in following location:
     ./Users/[username]/.sierra/test_creds.json
    Their format should be following:
    {
        "base_url":"https://<yourServerName>/iii/sierra-api/v5/",
        "key": "your key",
        "secret": "your secret"}
"""

import json
import os
import unittest

from oauthlib.oauth2.rfc6749.errors import MissingTokenError
from oauthlib.oauth2.rfc6749.tokens import OAuth2Token


from context import SierraSession


class TestSierraSession(unittest.TestCase):
    """Tests SierraSession against actual Sierra API service"""

    def setUp(self):
        # Windows only
        creds_fh = os.path.join(
            'c:\\Users', os.environ.get('USERNAME'), '.sierra\\test_creds.json')
        with open(creds_fh, 'r') as file:
            creds = json.load(file)
            self.base = creds['base_url']
            self.key = creds['key']
            self.secret = creds['secret']

    def test_session_without_parameters(self):
        with self.assertRaises(TypeError):
            with SierraSession() as session:
                pass

    def test_session_without_base_url(self):
        with self.assertRaises(TypeError):
            with SierraSession(None, self.key, self.secret) as session:
                pass

    def test_session_with_key_none_raises_exception(self):
        key = None
        secret = 'some_secret'
        with self.assertRaises(TypeError):
            with SierraSession(self.base, key, secret) as session:
                pass

    def test_session_with_secret_none_raises_exception(self):
        key = 'some_key'
        secret = None
        with self.assertRaises(TypeError):
            with SierraSession(self.base, key, secret):
                pass

    def test_session_with_incorrect_key_raises_exception(self):
        with self.assertRaises(MissingTokenError):
            with SierraSession(self.base, 'invalid_key', self.secret):
                pass

    def test_session_with_invalid_secret_raises_exception(self):
        secret = 'invalid secret'
        with self.assertRaises(MissingTokenError):
            with SierraSession(self.base, self.key, secret) as session:
                pass

    @unittest.skip('only tested in full fun')
    def test_successful_sierra_session(self):
        with SierraSession(self.base, self.key, self.secret) as session:
            self.assertIsInstance(
                session.token, OAuth2Token)

    # @unittest.skip('only tested in full run')
    def test_successful_sierra_sesssion_instance_has_access_token_parameter(self):
        with SierraSession(self.base, self.key, self.secret) as session:
            self.assertIsInstance(session.access_token, str)


if __name__ == '__main__':
    unittest.main()
