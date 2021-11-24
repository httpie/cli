from httpie.cli.dicts import HTTPHeadersDict
from requests.adapters import HTTPAdapter


class HTTPieHTTPAdapter(HTTPAdapter):

    def build_response(self, req, resp):
        """Wrap the original headers with the `HTTPHeadersDict`
        to preserve multiple headers that have the same name"""

        response = super().build_response(req, resp)
        response.headers = HTTPHeadersDict(getattr(resp, 'headers', {}))
        return response
