import zlib
import functools
from typing import Any, Callable, IO, Iterable, Optional, Tuple, Union, TYPE_CHECKING
from urllib.parse import urlencode

import requests
from requests.utils import super_len

if TYPE_CHECKING:
    from requests_toolbelt import MultipartEncoder

from .cli.dicts import MultipartRequestDataDict, RequestDataDict


class ChunkedStream:
    def __iter__(self) -> Iterable[Union[str, bytes]]:
        raise NotImplementedError


class ChunkedUploadStream(ChunkedStream):
    def __init__(self, stream: Iterable, callback: Callable):
        self.callback = callback
        self.stream = stream

    def __iter__(self) -> Iterable[Union[str, bytes]]:
        for chunk in self.stream:
            self.callback(chunk)
            yield chunk


class ChunkedMultipartUploadStream(ChunkedStream):
    chunk_size = 100 * 1024

    def __init__(self, encoder: 'MultipartEncoder'):
        self.encoder = encoder

    def __iter__(self) -> Iterable[Union[str, bytes]]:
        while True:
            chunk = self.encoder.read(self.chunk_size)
            if not chunk:
                break
            yield chunk


def as_bytes(data: Union[str, bytes]) -> bytes:
    if isinstance(data, str):
        return data.encode()
    else:
        return data


CallbackT = Callable[[bytes], bytes]


def _wrap_function_with_callback(
    func: Callable[..., Any],
    callback: CallbackT
) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        chunk = func(*args, **kwargs)
        callback(chunk)
        return chunk
    return wrapped


def _prepare_file_for_upload(
    file: Union[IO, 'MultipartEncoder'],
    callback: CallbackT,
    chunked: bool = False,
    content_length_header_value: Optional[int] = None,
) -> Union[bytes, IO, ChunkedStream]:
    if not super_len(file):
        # Zero-length -> assume stdin.
        if content_length_header_value is None and not chunked:
            # Read the whole stdin to determine `Content-Length`.
            #
            # TODO: Instead of opt-in --chunked, consider making
            #   `Transfer-Encoding: chunked` for STDIN opt-out via
            #   something like --no-chunked.
            #   This would be backwards-incompatible so wait until v3.0.0.
            #
            file = as_bytes(file.read())
    else:
        file.read = _wrap_function_with_callback(
            file.read,
            callback
        )

    if chunked:
        from requests_toolbelt import MultipartEncoder
        if isinstance(file, MultipartEncoder):
            return ChunkedMultipartUploadStream(
                encoder=file,
            )
        else:
            return ChunkedUploadStream(
                stream=file,
                callback=callback,
            )
    else:
        return file


def prepare_request_body(
    raw_body: Union[str, bytes, IO, 'MultipartEncoder', RequestDataDict],
    body_read_callback: CallbackT,
    offline: bool = False,
    chunked: bool = False,
    content_length_header_value: Optional[int] = None,
) -> Union[bytes, IO, ChunkedStream]:
    is_file_like = hasattr(raw_body, 'read')
    if isinstance(raw_body, (bytes, str)):
        body = as_bytes(raw_body)
    elif isinstance(raw_body, RequestDataDict):
        body = as_bytes(urlencode(raw_body, doseq=True))
    else:
        body = raw_body

    if offline:
        if is_file_like:
            return as_bytes(raw_body.read())
        else:
            return body

    if is_file_like:
        return _prepare_file_for_upload(
            body,
            chunked=chunked,
            callback=body_read_callback,
            content_length_header_value=content_length_header_value
        )
    elif chunked:
        return ChunkedUploadStream(
            stream=iter([body]),
            callback=body_read_callback
        )
    else:
        return body


def get_multipart_data_and_content_type(
    data: MultipartRequestDataDict,
    boundary: str = None,
    content_type: str = None,
) -> Tuple['MultipartEncoder', str]:
    from requests_toolbelt import MultipartEncoder

    encoder = MultipartEncoder(
        fields=data.items(),
        boundary=boundary,
    )
    if content_type:
        content_type = content_type.strip()
        if 'boundary=' not in content_type:
            content_type = f'{content_type}; boundary={encoder.boundary_value}'
    else:
        content_type = encoder.content_type

    data = encoder
    return data, content_type


def compress_request(
    request: requests.PreparedRequest,
    always: bool,
):
    deflater = zlib.compressobj()
    if isinstance(request.body, str):
        body_bytes = request.body.encode()
    elif hasattr(request.body, 'read'):
        body_bytes = request.body.read()
    else:
        body_bytes = request.body
    deflated_data = deflater.compress(body_bytes)
    deflated_data += deflater.flush()
    is_economical = len(deflated_data) < len(body_bytes)
    if is_economical or always:
        request.body = deflated_data
        request.headers['Content-Encoding'] = 'deflate'
        request.headers['Content-Length'] = str(len(deflated_data))
