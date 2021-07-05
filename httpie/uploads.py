import zlib
from typing import Callable, IO, Iterable, Tuple, Union
from urllib.parse import urlencode

import requests
from requests.utils import super_len
from requests_toolbelt import MultipartEncoder

from .cli.dicts import MultipartRequestDataDict, RequestDataDict


class ChunkedUploadStream:
    def __init__(self, stream: Iterable, callback: Callable):
        self.callback = callback
        self.stream = stream

    def __iter__(self) -> Iterable[Union[str, bytes]]:
        for chunk in self.stream:
            self.callback(chunk)
            yield chunk


class ChunkedMultipartUploadStream:
    chunk_size = 100 * 1024

    def __init__(self, encoder: MultipartEncoder):
        self.encoder = encoder

    def __iter__(self) -> Iterable[Union[str, bytes]]:
        while True:
            chunk = self.encoder.read(self.chunk_size)
            if not chunk:
                break
            yield chunk


def prepare_request_body(
    body: Union[str, bytes, IO, MultipartEncoder, RequestDataDict],
    body_read_callback: Callable[[bytes], bytes],
    content_length_header_value: int = None,
    chunked=False,
    offline=False,
) -> Union[str, bytes, IO, MultipartEncoder, ChunkedUploadStream]:

    is_file_like = hasattr(body, 'read')

    if isinstance(body, RequestDataDict):
        body = urlencode(body, doseq=True)

    if offline:
        if is_file_like:
            return body.read()
        return body

    if not is_file_like:
        if chunked:
            body = ChunkedUploadStream(
                # Pass the entire body as one chunk.
                stream=(chunk.encode() for chunk in [body]),
                callback=body_read_callback,
            )
    else:
        # File-like object.

        if not super_len(body):
            # Zero-length -> assume stdin.
            if content_length_header_value is None and not chunked:
                #
                # Read the whole stdin to determine `Content-Length`.
                #
                # TODO: Instead of opt-in --chunked, consider making
                #   `Transfer-Encoding: chunked` for STDIN opt-out via
                #   something like --no-chunked.
                #   This would be backwards-incompatible so wait until v3.0.0.
                #
                body = body.read()
        else:
            orig_read = body.read

            def new_read(*args):
                chunk = orig_read(*args)
                body_read_callback(chunk)
                return chunk

            body.read = new_read

        if chunked:
            if isinstance(body, MultipartEncoder):
                body = ChunkedMultipartUploadStream(
                    encoder=body,
                )
            else:
                body = ChunkedUploadStream(
                    stream=body,
                    callback=body_read_callback,
                )

    return body


def get_multipart_data_and_content_type(
    data: MultipartRequestDataDict,
    boundary: str = None,
    content_type: str = None,
) -> Tuple[MultipartEncoder, str]:
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
