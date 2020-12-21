import os
from typing import Callable, Dict, IO, List, Optional, Tuple, Union

from httpie.cli.argtypes import KeyValueArg
from httpie.cli.constants import (
    SEPARATORS_GROUP_MULTIPART, SEPARATOR_DATA_EMBED_FILE_CONTENTS,
    SEPARATOR_DATA_EMBED_RAW_JSON_FILE,
    SEPARATOR_DATA_RAW_JSON, SEPARATOR_DATA_STRING, SEPARATOR_FILE_UPLOAD,
    SEPARATOR_FILE_UPLOAD_TYPE, SEPARATOR_HEADER, SEPARATOR_HEADER_EMPTY,
    SEPARATOR_QUERY_PARAM,
)
from httpie.cli.dicts import (
    MultipartRequestDataDict, RequestDataDict, RequestFilesDict,
    RequestHeadersDict, RequestJSONDataDict,
    RequestQueryParamsDict,
)
from httpie.cli.exceptions import ParseError
from httpie.utils import (get_content_type, load_json_preserve_order)


class RequestItems:

    def __init__(self, as_form=False):
        self.headers = RequestHeadersDict()
        self.data = RequestDataDict() if as_form else RequestJSONDataDict()
        self.files = RequestFilesDict()
        self.params = RequestQueryParamsDict()
        # To preserve the order of fields in file upload multipart requests.
        self.multipart_data = MultipartRequestDataDict()

    @classmethod
    def from_args(
        cls,
        request_item_args: List[KeyValueArg],
        as_form=False,
    ) -> 'RequestItems':
        instance = cls(as_form=as_form)
        rules: Dict[str, Tuple[Callable, dict]] = {
            SEPARATOR_HEADER: (
                process_header_arg,
                instance.headers,
            ),
            SEPARATOR_HEADER_EMPTY: (
                process_empty_header_arg,
                instance.headers,
            ),
            SEPARATOR_QUERY_PARAM: (
                process_query_param_arg,
                instance.params,
            ),
            SEPARATOR_FILE_UPLOAD: (
                process_file_upload_arg,
                instance.files,
            ),
            SEPARATOR_DATA_STRING: (
                process_data_item_arg,
                instance.data,
            ),
            SEPARATOR_DATA_EMBED_FILE_CONTENTS: (
                process_data_embed_file_contents_arg,
                instance.data,
            ),
            SEPARATOR_DATA_RAW_JSON: (
                process_data_raw_json_embed_arg,
                instance.data,
            ),
            SEPARATOR_DATA_EMBED_RAW_JSON_FILE: (
                process_data_embed_raw_json_file_arg,
                instance.data,
            ),
        }

        for arg in request_item_args:
            processor_func, target_dict = rules[arg.sep]
            value = processor_func(arg)
            target_dict[arg.key] = value

            if arg.sep in SEPARATORS_GROUP_MULTIPART:
                instance.multipart_data[arg.key] = value

        return instance


JSONType = Union[str, bool, int, list, dict]


def process_header_arg(arg: KeyValueArg) -> Optional[str]:
    return arg.value or None


def process_empty_header_arg(arg: KeyValueArg) -> str:
    if arg.value:
        raise ParseError(
            'Invalid item "%s" '
            '(to specify an empty header use `Header;`)'
            % arg.orig
        )
    return arg.value


def process_query_param_arg(arg: KeyValueArg) -> str:
    return arg.value


def process_file_upload_arg(arg: KeyValueArg) -> Tuple[str, IO, str]:
    parts = arg.value.split(SEPARATOR_FILE_UPLOAD_TYPE)
    filename = parts[0]
    mime_type = parts[1] if len(parts) > 1 else None
    try:
        f = open(os.path.expanduser(filename), 'rb')
    except IOError as e:
        raise ParseError('"%s": %s' % (arg.orig, e))
    return (
        os.path.basename(filename),
        f,
        mime_type or get_content_type(filename),
    )


def process_data_item_arg(arg: KeyValueArg) -> str:
    return arg.value


def process_data_embed_file_contents_arg(arg: KeyValueArg) -> str:
    return load_text_file(arg)


def process_data_embed_raw_json_file_arg(arg: KeyValueArg) -> JSONType:
    contents = load_text_file(arg)
    value = load_json(arg, contents)
    return value


def process_data_raw_json_embed_arg(arg: KeyValueArg) -> JSONType:
    value = load_json(arg, arg.value)
    return value


def load_text_file(item: KeyValueArg) -> str:
    path = item.value
    try:
        with open(os.path.expanduser(path), 'rb') as f:
            return f.read().decode()
    except IOError as e:
        raise ParseError('"%s": %s' % (item.orig, e))
    except UnicodeDecodeError:
        raise ParseError(
            '"%s": cannot embed the content of "%s",'
            ' not a UTF8 or ASCII-encoded text file'
            % (item.orig, item.value)
        )


def load_json(arg: KeyValueArg, contents: str) -> JSONType:
    try:
        return load_json_preserve_order(contents)
    except ValueError as e:
        raise ParseError('"%s": %s' % (arg.orig, e))
