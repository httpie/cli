from typing import Tuple, Union

from httpie.cli.dicts import RequestDataDict, RequestFilesDict
from requests_toolbelt import MultipartEncoder


# Multipart uploads smaller than this size gets buffered (otherwise streamed).
# NOTE: Unbuffered upload requests cannot be displayed on the terminal.
UPLOAD_BUFFER = 1024 * 100


def get_multipart_data(
    data: RequestDataDict,
    files: RequestFilesDict
) -> Tuple[Union[MultipartEncoder, bytes], str]:
    fields = list(data.items()) + list(files.items())
    encoder = MultipartEncoder(fields=fields)
    content_type = encoder.content_type
    data = encoder.to_string() if encoder.len < UPLOAD_BUFFER else encoder
    return data, content_type
