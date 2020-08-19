from typing import Tuple, Union

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

    data = encoder.to_string() if encoder.len < UPLOAD_BUFFER else encoder
    return data, content_type
