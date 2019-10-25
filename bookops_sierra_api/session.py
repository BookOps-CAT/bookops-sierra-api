from datetime import date, datetime, timedelta
from urllib.parse import urljoin

from oauthlib.oauth2 import BackendApplicationClient
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2.rfc6749.errors import MissingTokenError
from requests.exceptions import ConnectionError



TIMEOUT = 5


class SierraSession(OAuth2Session):
    """
    BookOps Sierra API session wrapper that utilizes Python Requests library.

    args:
        base_url: str, base url of your library Sierra API
        key: str, Sierra API client key
        secret: str, Sierra API client secret

    Sierra API documentation:
        https://techdocs.iii.com/sierraapi/Content/titlePage.htm
    Python Requests documentation:
        https://requests.kennethreitz.org/en/master/

    Inherits methods of requests_oauthlib.OAuth2Session (OAuth 2.0) which by itself inherits from
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
            "User-Agent": f"BookOps-Sierra-API-wrapper",
            "Accept": "application/json"}
        self.headers.update(headers)

        try:
            self.get_token()
        except MissingTokenError:
            self.close()
            raise
        except ConnectionError:
            self.close()
            raise

    def _set_response_format_header(self, response_format):
        # set reponse format
        # default session header is 'Accept : appplication/json'
        # so there is no need to change unless user requests other

        if response_format == 'xml':
            request_headers = {"Accept": "application/xml"}
        else:
            request_headers = {}

        return request_headers

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

    def bib_get_by_id(self, bid, fields='default', response_format='json'):
        """
        Makes GET /bibs/{id} request - for a bib resource by its id
        args:
            bid: str, Sierra bib number (omit leading b and last character)
            full_bib: Boolean, specifies if to request full bib or
                      abbreviated resource
            response_format: str, default 'json', available 'xml'
        returns:
            response: requests.models.Response instance
        """

        url = urljoin(self.base_url, f'bibs/{bid}')

        payload = {
            "fields": fields
        }

        request_headers = self._set_response_format_header(response_format)

        response = self.get(
            url, params=payload, headers=request_headers, timeout=TIMEOUT)

        return response

    def hold_place_on_item(
            self, pid, iid, pickup_location, needed_by='',
            note='', response_format='json'):
        """
        POST /patrons/{id}/holds/requests endpoint.
        Platces item (iid) hold for specified account (pid).

        Successful Sierra API hold requests returns HTTP code 204

        args:
            pid: str, patron id account
            iid: int, Sierra item id number
            loc: str, pickup location
            needed_by: str, date in ISO 8601 format (yyyy-MM-dd)
            note: str, informational note related to the hold
        returns:
            response: requests.models.Response instance
        """

        if not isinstance(pid, int):
            raise TypeError('patron id (pid) must be an integer')
        if not isinstance(iid, int):
            raise TypeError('item number (iid) argument must be an integer')
        if not isinstance(pickup_location, str):
            raise TypeError('location code argument must be a string')
        if not isinstance(needed_by, str):
            raise TypeError('needed_by parameter must a string')
        if not isinstance(note, str):
            raise TypeError('note parameter must be a string')

        # set reponse format
        request_headers = self._set_response_format_header(response_format)

        # set neededBy date
        if needed_by:
            try:
                datetime.strptime(needed_by, '%Y-%m-%d')
            except ValueError:
                raise
        else:
            # default setting
            needed_by = date.today() + timedelta(days=14)
            needed_by = needed_by.strftime('%Y-%m-%d')

        # construct request url
        url = urljoin(self.base_url, f'patrons/{pid}/holds/requests')

        request_body = {
            'recordType': 'i',
            'recordNumber': iid,
            'pickupLocation': pickup_location,
            'neededBy': needed_by,
            'note': note
        }

        response = self.post(
            url, json=request_body, headers=request_headers, timeout=TIMEOUT)

        return response

    def hold_delete_by_id(self, hid, response_format='json'):
        """
        Delete single hold by hold id
        DELETE /patrons/holds/{holdId}
        Sierra API returns HTTP code 204 if deletion successful,
        its response does not include any content

        args:
            hid: int, hold id
        returns:
            response: requests.models.Response instance

        """
        if not isinstance(hid, int):
            raise TypeError('hold id must be an integer')

        # set reponse format
        request_headers = self._set_response_format_header(response_format)

        # construct request url
        url = urljoin(self.base_url, f'patrons/holds/{hid}')

        response = self.delete(url, headers=request_headers, timeout=TIMEOUT)

        return response

    def hold_get_by_id(
            self, hid, fields='default',
            response_format='json'):
        """
        Retrieves hold data by hold id
        GET patrons/holds/{holdId}

        args:
            hid: int, hold number
            response_fields
            respoinse_format: str, 'json' or 'xml'

        returns:
            response: requests.models.Response instance
        """

        # set reponse format
        request_headers = self._set_response_format_header(response_format)

        # construct request url
        url = urljoin(self.base_url, f'patrons/holds/{hid}')

        payload = {
            'fields': fields
        }

        response = self.get(
            url, params=payload, headers=request_headers, timeout=TIMEOUT)

        return response

    def hold_get_all(
            self, pid, limit=50, offset=0, fields='default',
            response_format='json'):
        """
        Retrieves all holds for particular account
        GET /patrons/{id}/holds

        args:
            pid: int, patron id
            limit: int, maximum number of results
            offset: int, the begining record of the result set retuned
            fields: str, comma-delimited list of fields to retrieve
        returns:
            response: requests.models.Response instance

        """
        if not isinstance(pid, int):
            raise TypeError('patron id (pid) must be an integer')
        if not isinstance(limit, int):
            raise TypeError('limit parameter must be an integer')
        if not isinstance(offset, int):
            raise TypeError('offset parameter must be an intege')
        if not isinstance(fields, str):
            raise TypeError('fields paramater must be a string')

        # set request headers
        request_headers = self._set_response_format_header(response_format)

        # construct endpoint url
        url = urljoin(self.base_url, f'patrons/{pid}/holds')

        # encode request parameters
        payload = {
            "limit": limit,
            "offset": offset,
            "fields": fields
        }

        response = self.get(
            url, params=payload, headers=request_headers, timeout=TIMEOUT)

        return response

    def hold_delete_all(self, pid, response_format='json'):
        """
        Deletes all holds for specified patron account
        DELETE /patrons/{id}/holds

        args:
            pid: int, patron id
            response_format: str, 'json' or 'xml'
        returns:
            response: requests.models.Response instance
        """

        if not isinstance(pid, int):
            raise TypeError('patron id (pid) argument must be an integer')
        if not isinstance(response_format, str):
            raise TypeError('response_format parameter must be a string')

        url = urljoin(self.base_url, f'patrons/{pid}/holds')

        request_headers = self._set_response_format_header(response_format)

        response = self.delete(url, headers=request_headers)

        return response
