import os
import sys
from requests.compat import urlparse, is_windows


class Environment(object):
    stdin_isatty = sys.stdin.isatty()
    stdin = sys.stdin

    if is_windows:
        # `colorama` patches `sys.stdout` so its initialization
        # needs to happen before the default environment is set.
        import colorama
        colorama.init()
        del colorama

    stdout_isatty = sys.stdout.isatty()
    stdout = sys.stdout

    # Can be set to 0 to disable colors completely.
    colors = 256 if '256color' in os.environ.get('TERM', '') else 88

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)


class HTTPMessage(object):
    """Model representing an HTTP message."""

    def __init__(self, line, headers, body, content_type=None):
        # {Request,Status}-Line
        self.line = line
        self.headers = headers
        self.body = body
        self.content_type = content_type

    def format(self, prettifier=None, with_headers=True, with_body=True):
        """Return a `unicode` representation of `self`. """
        pretty = prettifier is not None
        bits = []

        if with_headers:
            bits.append(self.line)
            bits.append(self.headers)
            if pretty:
                bits = [
                    prettifier.process_headers('\n'.join(bits))
                ]
            if with_body and self.body:
                bits.append('\n')

        if with_body and self.body:
            if pretty and self.content_type:
                bits.append(prettifier.process_body(
                    self.body, self.content_type))
            else:
                bits.append(self.body)

        return '\n'.join(bit.strip() for bit in bits)

    @staticmethod
    def from_request(request):
        """Make an `HTTPMessage` from `requests.models.Request`."""
        url = urlparse(request.url)
        request_headers = dict(request.headers)
        if 'Host' not in request_headers:
            request_headers['Host'] = url.netloc

        try:
            body = request.data
        except AttributeError:
            # requests < 0.12.1
            body = request._enc_data

        if isinstance(body, dict):
            # --form
            body = request.__class__._encode_params(body)

        request_line = '{method} {path}{query} HTTP/1.1'.format(
            method=request.method,
            path=url.path or '/',
            query='' if url.query is '' else '?' + url.query
        )
        headers = '\n'.join(
            str('%s: %s') % (name, value)
            for name, value
            in request_headers.items()
        )
        return HTTPMessage(
            line=request_line,
            headers=headers,
            body=body,
            content_type=request_headers.get('Content-Type')
        )

    @classmethod
    def from_response(cls, response):
        """Make an `HTTPMessage` from `requests.models.Response`."""
        encoding = response.encoding or 'ISO-8859-1'
        original = response.raw._original_response
        response_headers = response.headers
        status_line = 'HTTP/{version} {status} {reason}'.format(
            version='.'.join(str(original.version)),
            status=original.status,
            reason=original.reason
        )
        body = response.content.decode(encoding) if response.content else ''
        return cls(
            line=status_line,
            headers=str(original.msg),
            body=body,
            content_type=response_headers.get('Content-Type'))
