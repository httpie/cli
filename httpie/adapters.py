from httpie.cli.dicts import RequestHeadersDict
from requests.adapters import HTTPAdapter


class HTTPieHTTPAdapter(HTTPAdapter):

    def build_response(self, req, resp):
        """Wrap the original headers with the `RequestHeadersDict`
        to preserve multiple headers that have the same name"""

        response = super().build_response(req, resp)
        response.headers = RequestHeadersDict(getattr(resp, "headers", {}))
        return response
