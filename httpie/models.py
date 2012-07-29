import os
import sys
from requests.compat import urlparse, is_windows, bytes, str


class Environment(object):
    """Holds information about the execution context.

    Groups various aspects of the environment in a changeable object
    and allows for mocking.

    """
    progname = os.path.basename(sys.argv[0])
    if progname not in ['http', 'https']:
        progname = 'http'

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

    stderr = sys.stderr

    # Can be set to 0 to disable colors completely.
    colors = 256 if '256color' in os.environ.get('TERM', '') else 88

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)


class HTTPMessage(object):
    """Model representing an HTTP message."""

    def __init__(self, line, headers, body, encoding=None, content_type=None):
        """All args are a `str` except for `body` which is a `bytes`."""

        assert isinstance(line, str)
        assert content_type is None or isinstance(content_type, str)
        assert isinstance(body, bytes)

        self.line = line  # {Request,Status}-Line
        self.headers = headers
        self.body = body
        self.encoding = encoding
        self.content_type = content_type

    @classmethod
    def from_response(cls, response):
        """Make an `HTTPMessage` from `requests.models.Response`."""
        encoding = response.encoding or None
        original = response.raw._original_response
        response_headers = response.headers
        status_line = str('HTTP/{version} {status} {reason}'.format(
            version='.'.join(str(original.version)),
            status=original.status,
            reason=original.reason
        ))
        body = response.content

        return cls(line=status_line,
                   headers=str(original.msg),
                   body=body,
                   encoding=encoding,
                   content_type=str(response_headers.get('Content-Type', '')))

    @classmethod
    def from_request(cls, request):
        """Make an `HTTPMessage` from `requests.models.Request`."""

        url = urlparse(request.url)

        # Querystring
        qs = ''
        if url.query or request.params:
            qs = '?'
            if url.query:
                qs += url.query
            # Requests doesn't make params part of ``request.url``.
            if request.params:
                if url.query:
                    qs += '&'
                #noinspection PyUnresolvedReferences
                qs += type(request)._encode_params(request.params)

        # Request-Line
        request_line = str('{method} {path}{query} HTTP/1.1'.format(
            method=request.method,
            path=url.path or '/',
            query=qs
        ))

        # Headers
        headers = dict(request.headers)
        content_type = headers.get('Content-Type')

        if isinstance(content_type, bytes):
            # Happens when uploading files.
            # TODO: submit a bug report for Requests
            content_type = headers['Content-Type'] = content_type.decode('utf8')

        if 'Host' not in headers:
            headers['Host'] = url.netloc
        headers = '\n'.join('%s: %s' % (name, value)
                            for name, value in headers.items())

        # Body
        if request.files:
            body, _ = request._encode_files(request.files)
        else:
            try:
                body = request.data
            except AttributeError:
                # requests < 0.12.1
                body = request._enc_data

            if isinstance(body, dict):
                #noinspection PyUnresolvedReferences
                body = type(request)._encode_params(body)

            if isinstance(body, str):
                body = body.encode('utf8')

        return cls(line=request_line,
                   headers=headers,
                   body=body,
                   content_type=content_type)
