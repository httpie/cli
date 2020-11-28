from __future__ import division

import os
import errno
import json
import mimetypes
from mailbox import Message
import time
from collections import OrderedDict
from http.cookiejar import parse_ns_headers
from pprint import pformat
from typing import List, Optional, Tuple
from urllib.parse import urlsplit

import requests.auth


def load_json_preserve_order(s):
    return json.loads(s, object_pairs_hook=OrderedDict)


def repr_dict(d: dict) -> str:
    return pformat(d)


def humanize_bytes(n, precision=2):
    # Author: Doug Latornell
    # Licence: MIT
    # URL: https://code.activestate.com/recipes/577081/
    """Return a humanized string representation of a number of bytes.

    Assumes `from __future__ import division`.

    >>> humanize_bytes(1)
    '1 B'
    >>> humanize_bytes(1024, precision=1)
    '1.0 kB'
    >>> humanize_bytes(1024 * 123, precision=1)
    '123.0 kB'
    >>> humanize_bytes(1024 * 12342, precision=1)
    '12.1 MB'
    >>> humanize_bytes(1024 * 12342, precision=2)
    '12.05 MB'
    >>> humanize_bytes(1024 * 1234, precision=2)
    '1.21 MB'
    >>> humanize_bytes(1024 * 1234 * 1111, precision=2)
    '1.31 GB'
    >>> humanize_bytes(1024 * 1234 * 1111, precision=1)
    '1.3 GB'

    """
    abbrevs = [
        (1 << 50, 'PB'),
        (1 << 40, 'TB'),
        (1 << 30, 'GB'),
        (1 << 20, 'MB'),
        (1 << 10, 'kB'),
        (1, 'B')
    ]

    if n == 1:
        return '1 B'

    for factor, suffix in abbrevs:
        if n >= factor:
            break

    # noinspection PyUnboundLocalVariable
    return '%.*f %s' % (precision, n / factor, suffix)


class ExplicitNullAuth(requests.auth.AuthBase):
    """Forces requests to ignore the ``.netrc``.
    <https://github.com/psf/requests/issues/2773#issuecomment-174312831>
    """

    def __call__(self, r):
        return r


def get_content_type(filename):
    """
    Return the content type for ``filename`` in format appropriate
    for Content-Type headers, or ``None`` if the file type is unknown
    to ``mimetypes``.

    """
    mime, encoding = mimetypes.guess_type(filename, strict=False)
    if mime:
        content_type = mime
        if encoding:
            content_type = '%s; charset=%s' % (mime, encoding)
        return content_type


def get_expired_cookies(
    headers: List[Tuple[str, str]],
    now: float = None
) -> List[dict]:

    now = now or time.time()

    def is_expired(expires: Optional[float]) -> bool:
        return expires is not None and expires <= now

    attr_sets: List[Tuple[str, str]] = parse_ns_headers(
        value for name, value in headers
        if name.lower() == 'set-cookie'
    )
    cookies = [
        # The first attr name is the cookie name.
        dict(attrs[1:], name=attrs[0][0])
        for attrs in attr_sets
    ]

    return [
        {
            'name': cookie['name'],
            'path': cookie.get('path', '/')
        }
        for cookie in cookies
        if is_expired(expires=cookie.get('expires'))
    ]


def filename_from_content_disposition(
    content_disposition: str
) -> Optional[str]:
    """
    Extract and validate filename from a Content-Disposition header.

    :param content_disposition: Content-Disposition value
    :return: the filename if present and valid, otherwise `None`

    """
    # attachment; filename=jakubroztocil-httpie-0.4.1-20-g40bd8f6.tar.gz

    msg = Message('Content-Disposition: %s' % content_disposition)
    filename = msg.get_filename()
    if filename:
        # Basic sanitation.
        filename = os.path.basename(filename).lstrip('.').strip()
        if filename:
            return filename


def filename_from_url(url: str, content_type: Optional[str]) -> str:
    fn = urlsplit(url).path.rstrip('/')
    fn = os.path.basename(fn) if fn else 'index'
    if '.' not in fn and content_type:
        content_type = content_type.split(';')[0]
        if content_type == 'text/plain':
            # mimetypes returns '.ksh'
            ext = '.txt'
        else:
            ext = mimetypes.guess_extension(content_type)

        if ext == '.htm':  # Python 3
            ext = '.html'

        if ext:
            fn += ext

    return fn


def trim_filename(filename: str, max_len: int) -> str:
    if len(filename) > max_len:
        trim_by = len(filename) - max_len
        name, ext = os.path.splitext(filename)
        if trim_by >= len(name):
            filename = filename[:-trim_by]
        else:
            filename = name[:-trim_by] + ext
    return filename


def get_filename_max_length(directory: str) -> int:
    max_len = 255
    try:
        pathconf = os.pathconf
    except AttributeError:
        pass  # non-posix
    else:
        try:
            max_len = pathconf(directory, 'PC_NAME_MAX')
        except OSError as e:
            if e.errno != errno.EINVAL:
                raise
    return max_len


def trim_filename_if_needed(filename: str, directory='.', extra=0) -> str:
    max_len = get_filename_max_length(directory) - extra
    if len(filename) > max_len:
        filename = trim_filename(filename, max_len)
    return filename


def get_initial_filename(url: str):
    try:
        headers = requests.head(url, allow_redirects=True).headers
    except Exception:
        # If there's an error while making request here,
        # return the default filename and handle the error on the main request
        filename = filename_from_url(url, '')
        return filename

    filename = filename_from_url(url, headers["Content-Type"])
    content_disposition = None
    if "Content-Disposition" in headers:
        content_disposition = headers["Content-Disposition"]
        filename = filename_from_content_disposition(content_disposition)
    filename = trim_filename_if_needed(filename)
    return filename


def get_unique_filename(filename: str, exists=os.path.exists) -> str:
    attempt = 0
    while True:
        suffix = '-' + str(attempt) if attempt > 0 else ''
        try_filename = trim_filename_if_needed(filename, extra=len(suffix))
        try_filename += suffix
        if not exists(try_filename):
            return try_filename
        attempt += 1
