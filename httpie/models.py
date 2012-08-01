import os
import sys
from requests.compat import urlparse, is_windows, bytes, str


class Environment(object):
    """Holds information about the execution context.

    Groups various aspects of the environment in a changeable object
    and allows for mocking.

    """

    #noinspection PyUnresolvedReferences
    is_windows = is_windows

    progname = os.path.basename(sys.argv[0])
    if progname not in ['http', 'https']:
        progname = 'http'

    stdin_isatty = sys.stdin.isatty()
    stdin = sys.stdin
    stdout_isatty = sys.stdout.isatty()
    stdout = sys.stdout
    stderr = sys.stderr

    # Can be set to 0 to disable colors completely.
    colors = 256 if '256color' in os.environ.get('TERM', '') else 88

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)

    def init_colors(self):
        # We check for real Window here, not self.is_windows as
        # it could be mocked.
        if (is_windows and not self.__colors_initialized
            and self.stdout == sys.stdout):
            import colorama.initialise
            self.stdout = colorama.initialise.wrap_stream(
                self.stdout, autoreset=False,
                convert=None, strip=None, wrap=True)
            self.__colors_initialized = True
    __colors_initialized = False


class HTTPMessage(object):
    """Model representing an HTTP message."""

    def __init__(self, orig):
        self._orig = orig

    @property
    def content_type(self):
        return str(self._orig.headers.get('Content-Type', ''))


class HTTPResponse(HTTPMessage):
    """A `requests.models.Response` wrapper."""

    @property
    def line(self):
        """Return Status-Line"""
        original = self._orig.raw._original_response
        return str('HTTP/{version} {status} {reason}'.format(
             version='.'.join(str(original.version)),
             status=original.status,
             reason=original.reason
         ))

    @property
    def headers(self):
        return str(self._orig.raw._original_response.msg)

    @property
    def encoding(self):
        return self._orig.encoding or 'utf8'

    @property
    def body(self):
        # Only now the response body is fetched.
        # Shouldn't be touched unless the body is actually needed.
        return self._orig.content


class HTTPRequest(HTTPMessage):
    """A `requests.models.Request` wrapper."""

    @property
    def line(self):
        """Return Request-Line"""
        url = urlparse(self._orig.url)

        # Querystring
        qs = ''
        if url.query or self._orig.params:
            qs = '?'
            if url.query:
                qs += url.query
            # Requests doesn't make params part of ``request.url``.
            if self._orig.params:
                if url.query:
                    qs += '&'
                #noinspection PyUnresolvedReferences
                qs += type(self._orig)._encode_params(self._orig.params)

        # Request-Line
        return str('{method} {path}{query} HTTP/1.1'.format(
            method=self._orig.method,
            path=url.path or '/',
            query=qs
        ))

    @property
    def headers(self):
        headers = dict(self._orig.headers)
        content_type = headers.get('Content-Type')

        if isinstance(content_type, bytes):
            # Happens when uploading files.
            # TODO: submit a bug report for Requests
            headers['Content-Type'] = str(content_type)

        if 'Host' not in headers:
            headers['Host'] = urlparse(self._orig.url).netloc

        return '\n'.join('%s: %s' % (name, value)
                         for name, value in headers.items())

    @property
    def encoding(self):
        return 'utf8'

    @property
    def body(self):
        """Reconstruct and return the original request body bytes."""
        if self._orig.files:
            # TODO: would be nice if we didn't need to encode the files again
            # FIXME: Also the boundary header doesn't match the one used.
            for fn, fd in self._orig.files.values():
                # Rewind the files as they have already been read before.
                fd.seek(0)
            body, _ = self._orig._encode_files(self._orig.files)
        else:
            try:
                body = self._orig.data
            except AttributeError:
                # requests < 0.12.1
                body = self._orig._enc_data

            if isinstance(body, dict):
                #noinspection PyUnresolvedReferences
                body = type(self._orig)._encode_params(body)

            if isinstance(body, str):
                body = body.encode('utf8')

        return body
