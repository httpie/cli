import requests
from requests.adapters import HTTPAdapter
from urllib3.util import parse_url
from urllib3.response import HTTPResponse
from httpcore import SyncConnectionPool, PlainByteStream


class FileLike:
    def __init__(self, bytestream):
        self._bytestream = iter(bytestream)
        self.closed = False

    def read(self, amt: int = None):
        return next(self._bytestream, b"")

    def close(self):
        self._bytestream.close()
        self.closed = True


class StreamLike:
    def __init__(self, filelike):
        self._filelike = filelike

    def __iter__(self):
        chunk = self._filelike.read(4096)
        while chunk:
            yield chunk
            chunk = self._filelike.read(4096)

    def close():
        pass


class HTTPCoreAdapter(HTTPAdapter):
    def __init__(self):
        self.pool = SyncConnectionPool()

    def send(self, request, stream=False, timeout=None, verify=True,
             cert=None, proxies=None):
        method = request.method.encode("ascii")

        parsed = parse_url(request.url)
        scheme = parsed.scheme.encode("ascii")
        host = parsed.host.encode("ascii")
        port = parsed.port
        target = parsed.path.encode("ascii")
        if parsed.query:
            target += b"?" + parsed.query.encode("ascii")
        url = (scheme, host, port, target)

        headers = [(b'Host', parsed.netloc.encode("ascii"))]
        headers.extend([
            (key, val) for key, val in request.headers.items()
        ])

        if not request.body:
            stream = PlainByteStream(b"")
        elif isinstance(request.body, str):
            stream = PlainByteStream(request.body.encode("utf-8"))
        elif isinstance(request.body, bytes):
            stream = PlainByteStream(request.body)
        else:
            stream = StreamLike(request.body)

        ext = {}

        status_code, headers, stream, ext = self.pool.request(method, url, headers, stream, ext)

        urllib3_response = HTTPResponse(
            body=FileLike(stream),
            headers=[(key.decode("ascii"), val.decode("ascii")) for key, val in headers],
            status=status_code,
            reason=ext['reason'],
            version={'HTTP/0.9': 9, 'HTTP/1.0': 10, 'HTTP/1.1': 11, 'HTTP/2': 20}[ext['http_version']],
            preload_content=False,
        )

        return self.build_response(request, urllib3_response)

    def close(self):
        self.pool.close()
