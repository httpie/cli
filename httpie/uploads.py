from typing import Tuple, Union

from requests.utils import super_len
from requests_toolbelt import MultipartEncoder

from httpie.cli.dicts import RequestDataDict, RequestFilesDict


# Multipart uploads smaller than this size gets buffered (otherwise streamed).
# NOTE: Unbuffered upload requests cannot be displayed on the terminal.
UPLOAD_BUFFER = 1024 * 100


def get_multipart_data_and_content_type(
    data: RequestDataDict,
    files: RequestFilesDict,
    boundary: str = None,
    content_type: str = None,
) -> Tuple[Union[MultipartEncoder, bytes], str]:
    fields = list(data.items()) + list(files.items())
    encoder = MultipartEncoder(
        fields=fields,
        boundary=boundary,
    )
    if content_type:
        content_type = content_type.strip()  # maybe auto-strip all headers somewhere
        if 'boundary=' not in content_type:
            content_type = f'{content_type}; boundary={encoder.boundary_value}'
    else:
        content_type = encoder.content_type

    data = encoder.to_string() if 0 and encoder.len < UPLOAD_BUFFER else encoder
    return data, content_type


class Stdin:

    def __init__(self, stdin, callback):
        self.callback = callback
        self.stdin = stdin

    def __iter__(self):
        for chunk in self.stdin:
            print("__iter__() =>", chunk)
            self.callback(chunk)
            yield chunk

    @classmethod
    def is_stdin(cls, obj):
        return super_len(obj) == 0


def wrap_request_data(data, callback=lambda chunk: print('chunk', chunk)):
    if hasattr(data, 'read'):
        if Stdin.is_stdin(data):
            data = Stdin(data, callback=callback)
        else:
            orig_read = data.read

            def new_read(*args):
                val = orig_read(*args)
                print('read() =>', val)
                callback(callback)
                return val

            data.read = new_read

    return data
