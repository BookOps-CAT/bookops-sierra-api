from urllib.parse import urljoin

from oauthlib.oauth2 import BackendApplicationClient
from requests import Request
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session


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

    """

    def __init__(self, base_url, key, secret):

        self.base_url = base_url
        self.key = key
        self.secret = secret

        client = BackendApplicationClient(client_id=key)
        OAuth2Session.__init__(self, client=client)

        headers = {
            "User-Agent": "BookOps-Sierra-API-wrapper",
            "Accept": "application/json"}
        self.headers.update(headers)

        self.get_token()

    def get_token(self):
        """
        Uses basic authorization pattern to fetch access token from Sierra API.
        Updates session header with bearer authentication
        """

        auth = HTTPBasicAuth(self.key, self.secret)
        self.fetch_token(token_url=f'{self.base_url}/token', auth=auth)
        if self.access_token is not None:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            self.headers.update(headers)

    def get_bib_by_id(self, bid, full_bib=False):
        """
        Makes GET /bibs/{id} request - request for a bib resource by its id
        args:
            bid: str, Sierra bib number (omit leading b and last character)
            full_bib: Boolean, specifies if to request full bib or
                      abbreviated resource
        returns tuple:
            API response object and dictionary that includes
            request URL, fullness of bib requested, and response code
        """

        endpoint = urljoin(self.base_url, '/bibs/')
        url = urljoin(endpoint, bid)

        if full_bib:
            payload = {
                "fields": "fixedFields,varFields"}
        else:
            payload = {}

        req = Request('GET', url, params=payload)
        prepped = self.prepare_request(req)
        req_url = prepped.url

        response = self.send(prepped, timeout=5)

        return (
            response,
            {
                'request_url': req_url,
                'full_bib_requested': full_bib,
                'response_code': response.status_code})
