import os
import functools
from typing import Callable, Dict, IO, List, Optional, Tuple, Union

from .argtypes import KeyValueArg
from .constants import (
    SEPARATORS_GROUP_MULTIPART, SEPARATOR_DATA_EMBED_FILE_CONTENTS,
    SEPARATOR_DATA_EMBED_RAW_JSON_FILE, SEPARATOR_GROUP_NESTED_JSON_ITEMS,
    SEPARATOR_DATA_RAW_JSON, SEPARATOR_DATA_STRING, SEPARATOR_FILE_UPLOAD,
    SEPARATOR_FILE_UPLOAD_TYPE, SEPARATOR_HEADER, SEPARATOR_HEADER_EMPTY,
    SEPARATOR_HEADER_EMBED, SEPARATOR_QUERY_PARAM,
    SEPARATOR_QUERY_EMBED_FILE, RequestType
)
from .dicts import (
    BaseMultiDict, MultipartRequestDataDict, RequestDataDict,
    RequestFilesDict, HTTPHeadersDict, RequestJSONDataDict,
    RequestQueryParamsDict,
)
from .exceptions import ParseError
from .nested_json import interpret_nested_json
from ..utils import get_content_type, load_json_preserve_order_and_dupe_keys, split


class RequestItems:

    def __init__(self, request_type: Optional[RequestType] = None):
        self.headers = HTTPHeadersDict()
        self.request_type = request_type
        self.is_json = request_type is None or request_type is RequestType.JSON
        self.data = RequestJSONDataDict() if self.is_json else RequestDataDict()
        self.files = RequestFilesDict()
        self.params = RequestQueryParamsDict()
        # To preserve the order of fields in file upload multipart requests.
        self.multipart_data = MultipartRequestDataDict()

    @classmethod
    def from_args(
        cls,
        request_item_args: List[KeyValueArg],
        request_type: Optional[RequestType] = None,
    ) -> 'RequestItems':
        instance = cls(request_type=request_type)
        rules: Dict[str, Tuple[Callable, dict]] = {
            SEPARATOR_HEADER: (
                process_header_arg,
                instance.headers,
            ),
            SEPARATOR_HEADER_EMPTY: (
                process_empty_header_arg,
                instance.headers,
            ),
            SEPARATOR_HEADER_EMBED: (
                process_embed_header_arg,
                instance.headers,
            ),
            SEPARATOR_QUERY_PARAM: (
                process_query_param_arg,
                instance.params,
            ),
            SEPARATOR_QUERY_EMBED_FILE: (
                process_embed_query_param_arg,
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
            SEPARATOR_GROUP_NESTED_JSON_ITEMS: (
                process_data_nested_json_embed_args,
                instance.data,
            ),
            SEPARATOR_DATA_RAW_JSON: (
                json_only(instance, process_data_raw_json_embed_arg),
                instance.data,
            ),
            SEPARATOR_DATA_EMBED_RAW_JSON_FILE: (
                json_only(instance, process_data_embed_raw_json_file_arg),
                instance.data,
            ),
        }

        if instance.is_json:
            json_item_args, request_item_args = split(
                request_item_args,
                lambda arg: arg.sep in SEPARATOR_GROUP_NESTED_JSON_ITEMS
            )
            if json_item_args:
                pairs = [
                    (arg.key, rules[arg.sep][0](arg))
                    for arg in json_item_args
                ]
                processor_func, target_dict = rules[SEPARATOR_GROUP_NESTED_JSON_ITEMS]
                value = processor_func(pairs)
                target_dict.update(value)

        # Then handle all other items.
        for arg in request_item_args:
            processor_func, target_dict = rules[arg.sep]
            value = processor_func(arg)

            if arg.sep in SEPARATORS_GROUP_MULTIPART:
                instance.multipart_data[arg.key] = value

            if isinstance(target_dict, BaseMultiDict):
                target_dict.add(arg.key, value)
            else:
                target_dict[arg.key] = value

        return instance


JSONType = Union[str, bool, int, list, dict]


def process_header_arg(arg: KeyValueArg) -> Optional[str]:
    return arg.value or None


def process_embed_header_arg(arg: KeyValueArg) -> str:
    return load_text_file(arg).rstrip('\n')


def process_empty_header_arg(arg: KeyValueArg) -> str:
    if not arg.value:
        return arg.value
    raise ParseError(
        f'Invalid item {arg.orig!r} (to specify an empty header use `Header;`)'
    )


def process_query_param_arg(arg: KeyValueArg) -> str:
    return arg.value


def process_embed_query_param_arg(arg: KeyValueArg) -> str:
    return load_text_file(arg).rstrip('\n')


def process_file_upload_arg(arg: KeyValueArg) -> Tuple[str, IO, str]:
    parts = arg.value.split(SEPARATOR_FILE_UPLOAD_TYPE)
    filename = parts[0]
    mime_type = parts[1] if len(parts) > 1 else None
    try:
        f = open(os.path.expanduser(filename), 'rb')
    except OSError as e:
        raise ParseError(f'{arg.orig!r}: {e}')
    return (
        os.path.basename(filename),
        f,
        mime_type or get_content_type(filename),
    )


def process_data_item_arg(arg: KeyValueArg) -> str:
    return arg.value


def process_data_embed_file_contents_arg(arg: KeyValueArg) -> str:
    return load_text_file(arg)


def json_only(items: RequestItems, func: Callable[[KeyValueArg], JSONType]) -> str:
    if items.is_json:
        return func

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> str:
        try:
            ret = func(*args, **kwargs)
        except ParseError:
            ret = None

        # If it is a basic type, then allow it
        if isinstance(ret, (str, int, float)):
            return str(ret)
        else:
            raise ParseError(
                'Can\'t use complex JSON value types with '
                '--form/--multipart.'
            )

    return wrapper


def process_data_embed_raw_json_file_arg(arg: KeyValueArg) -> JSONType:
    contents = load_text_file(arg)
    value = load_json(arg, contents)
    return value


def process_data_raw_json_embed_arg(arg: KeyValueArg) -> JSONType:
    value = load_json(arg, arg.value)
    return value


def process_data_nested_json_embed_args(pairs) -> Dict[str, JSONType]:
    return interpret_nested_json(pairs)


def load_text_file(item: KeyValueArg) -> str:
    path = item.value
    try:
        with open(os.path.expanduser(path), 'rb') as f:
            return f.read().decode()
    except OSError as e:
        raise ParseError(f'{item.orig!r}: {e}')
    except UnicodeDecodeError:
        raise ParseError(
            f'{item.orig!r}: cannot embed the content of {item.value!r},'
            ' not a UTF-8 or ASCII-encoded text file'
        )


def load_json(arg: KeyValueArg, contents: str) -> JSONType:
    try:
        return load_json_preserve_order_and_dupe_keys(contents)
    except ValueError as e:
        raise ParseError(f'{arg.orig!r}: {e}')
