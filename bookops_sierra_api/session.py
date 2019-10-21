from urllib.parse import urljoin

from oauthlib.oauth2 import BackendApplicationClient
from requests import Request
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2.rfc6749.errors import MissingTokenError


class SierraSession(OAuth2Session):
    """
    BookOps Sierra API session wrapper that utilizes Python Requests library

    args:
        base_url: str, base url of your library Sierra API
        key: str, Sierra API client key
        secret: str, Sierra API client secret

    Sierra API documentation:
        https://techdocs.iii.com/sierraapi/Content/titlePage.htm
    Python Requests documentation:
        https://requests.kennethreitz.org/en/master/

    Inherits methods of OAuth2Session (OAuth 2.0) which by itself inherits from
    requests.Session class

    When opened, SierraSession automatically requests an access token
    from Sierra API, which then is passed into headers of each request
    for resources (session and each requests headers are merged following
    requests module logic).

    Session sets default response content type to JSON.

    """

    def __init__(self, base_url, key, secret):

        if type(base_url) is not str:
            raise TypeError('Sierra API base URL is missing')
        if type(key) is not str:
            raise TypeError('Sierra API key must be a string')
        if type(secret) is not str:
            raise TypeError('Sierra API secret must be a string')

        self.base_url = base_url
        self.key = key
        self.secret = secret
        self.token_url = urljoin(self.base_url, 'token')

        client = BackendApplicationClient(client_id=key)
        OAuth2Session.__init__(self, client=client)

        headers = {
            "User-Agent": "BookOps-Sierra-API-wrapper",
            "Accept": "application/json"}
        self.headers.update(headers)

        try:
            self.get_token()
        except MissingTokenError:
            self.close()
            raise

    def get_token(self):
        """
        Uses basic authorization pattern to fetch access token from Sierra API.
        Updates session header with bearer authentication
        """

        auth = HTTPBasicAuth(self.key, self.secret)
        self.fetch_token(token_url=self.token_url, auth=auth)
        if self.access_token is not None:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            self.headers.update(headers)

    def get_bib_by_id(self, bid, full_bib=False, response_format='json'):
        """
        Makes GET /bibs/{id} request - for a bib resource by its id
        args:
            bid: str, Sierra bib number (omit leading b and last character)
            full_bib: Boolean, specifies if to request full bib or
                      abbreviated resource
            response_format: str, default 'json', available 'xml'
        returns tuple:
            API response object and dictionary that includes
            request URL and response code
        """

        endpoint = urljoin(self.base_url, 'bibs/')
        url = urljoin(endpoint, bid)

        if full_bib:
            payload = {
                "fields": "fixedFields,varFields"}
        else:
            payload = {}

        if response_format == 'xml':
            request_headers = {"Accept": "application/xml"}
        else:
            request_headers = {}

        req = Request('GET', url, params=payload, headers=request_headers)
        prepped = self.prepare_request(req)
        request_url = prepped.url

        response = self.send(prepped, timeout=5)

        return {
            'request_url': request_url,
            'response_code': response.status_code,
            'response': response}
