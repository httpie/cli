"""
Download mode implementation.

"""
import mimetypes
import os
import re
from mailbox import Message
from time import monotonic
from typing import IO, Optional, Tuple
from urllib.parse import urlsplit

import requests

from .models import HTTPResponse, OutputOptions
from .output.streams import RawStream
from .context import Environment


PARTIAL_CONTENT = 206


class ContentRangeError(ValueError):
    pass


def parse_content_range(content_range: str, resumed_from: int) -> int:
    """
    Parse and validate Content-Range header.

    <https://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html>

    :param content_range: the value of a Content-Range response header
                          eg. "bytes 21010-47021/47022"
    :param resumed_from: first byte pos. from the Range request header
    :return: total size of the response body when fully downloaded.

    """
    if content_range is None:
        raise ContentRangeError('Missing Content-Range')

    pattern = (
        r'^bytes (?P<first_byte_pos>\d+)-(?P<last_byte_pos>\d+)'
        r'/(\*|(?P<instance_length>\d+))$'
    )
    match = re.match(pattern, content_range)

    if not match:
        raise ContentRangeError(
            f'Invalid Content-Range format {content_range!r}')

    content_range_dict = match.groupdict()
    first_byte_pos = int(content_range_dict['first_byte_pos'])
    last_byte_pos = int(content_range_dict['last_byte_pos'])
    instance_length = (
        int(content_range_dict['instance_length'])
        if content_range_dict['instance_length']
        else None
    )

    # "A byte-content-range-spec with a byte-range-resp-spec whose
    # last- byte-pos value is less than its first-byte-pos value,
    # or whose instance-length value is less than or equal to its
    # last-byte-pos value, is invalid. The recipient of an invalid
    # byte-content-range- spec MUST ignore it and any content
    # transferred along with it."
    if (first_byte_pos > last_byte_pos
        or (instance_length is not None
            and instance_length <= last_byte_pos)):
        raise ContentRangeError(
            f'Invalid Content-Range returned: {content_range!r}')

    if (first_byte_pos != resumed_from
        or (instance_length is not None
            and last_byte_pos + 1 != instance_length)):
        # Not what we asked for.
        raise ContentRangeError(
            f'Unexpected Content-Range returned ({content_range!r})'
            f' for the requested Range ("bytes={resumed_from}-")'
        )

    return last_byte_pos + 1


def filename_from_content_disposition(
    content_disposition: str
) -> Optional[str]:
    """
    Extract and validate filename from a Content-Disposition header.

    :param content_disposition: Content-Disposition value
    :return: the filename if present and valid, otherwise `None`

    """
    # attachment; filename=jakubroztocil-httpie-0.4.1-20-g40bd8f6.tar.gz

    msg = Message(f'Content-Disposition: {content_disposition}')
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

        if ext == '.htm':
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
    if hasattr(os, 'pathconf') and 'PC_NAME_MAX' in os.pathconf_names:
        max_len = os.pathconf(directory, 'PC_NAME_MAX')
    return max_len


def trim_filename_if_needed(filename: str, directory='.', extra=0) -> str:
    max_len = get_filename_max_length(directory) - extra
    if len(filename) > max_len:
        filename = trim_filename(filename, max_len)
    return filename


def get_unique_filename(filename: str, exists=os.path.exists) -> str:
    attempt = 0
    while True:
        suffix = f'-{attempt}' if attempt > 0 else ''
        try_filename = trim_filename_if_needed(filename, extra=len(suffix))
        try_filename += suffix
        if not exists(try_filename):
            return try_filename
        attempt += 1


class Downloader:

    def __init__(
        self,
        env: Environment,
        output_file: IO = None,
        resume: bool = False
    ):
        """
        :param resume: Should the download resume if partial download
                       already exists.

        :param output_file: The file to store response body in. If not
                            provided, it will be guessed from the response.

        :param progress_file: Where to report download progress.

        """
        self.finished = False
        self.status = DownloadStatus(env=env)
        self._output_file = output_file
        self._resume = resume
        self._resumed_from = 0

    def pre_request(self, request_headers: dict):
        """Called just before the HTTP request is sent.

        Might alter `request_headers`.

        """
        # Ask the server not to encode the content so that we can resume, etc.
        request_headers['Accept-Encoding'] = 'identity'
        if self._resume:
            bytes_have = os.path.getsize(self._output_file.name)
            if bytes_have:
                # Set ``Range`` header to resume the download
                # TODO: Use "If-Range: mtime" to make sure it's fresh?
                request_headers['Range'] = f'bytes={bytes_have}-'
                self._resumed_from = bytes_have

    def start(
        self,
        initial_url: str,
        final_response: requests.Response
    ) -> Tuple[RawStream, IO]:
        """
        Initiate and return a stream for `response` body  with progress
        callback attached. Can be called only once.

        :param initial_url: The original requested URL
        :param final_response: Initiated response object with headers already fetched

        :return: RawStream, output_file

        """
        assert not self.status.time_started

        # FIXME: some servers still might sent Content-Encoding: gzip
        # <https://github.com/httpie/httpie/issues/423>
        try:
            total_size = int(final_response.headers['Content-Length'])
        except (KeyError, ValueError, TypeError):
            total_size = None

        if not self._output_file:
            self._output_file = self._get_output_file_from_response(
                initial_url=initial_url,
                final_response=final_response,
            )
        else:
            # `--output, -o` provided
            if self._resume and final_response.status_code == PARTIAL_CONTENT:
                total_size = parse_content_range(
                    final_response.headers.get('Content-Range'),
                    self._resumed_from
                )

            else:
                self._resumed_from = 0
                try:
                    self._output_file.seek(0)
                    self._output_file.truncate()
                except OSError:
                    pass  # stdout

        output_options = OutputOptions.from_message(final_response, headers=False, body=True)
        stream = RawStream(
            msg=HTTPResponse(final_response),
            output_options=output_options,
            on_body_chunk_downloaded=self.chunk_downloaded,
        )

        self.status.started(
            output_file=self._output_file,
            resumed_from=self._resumed_from,
            total_size=total_size
        )

        return stream, self._output_file

    def finish(self):
        assert not self.finished
        self.finished = True
        self.status.finished()

    def failed(self):
        self.status.terminate()

    @property
    def interrupted(self) -> bool:
        return (
            self.finished
            and self.status.total_size
            and self.status.total_size != self.status.downloaded
        )

    def chunk_downloaded(self, chunk: bytes):
        """
        A download progress callback.

        :param chunk: A chunk of response body data that has just
                      been downloaded and written to the output.

        """
        self.status.chunk_downloaded(len(chunk))

    @staticmethod
    def _get_output_file_from_response(
        initial_url: str,
        final_response: requests.Response,
    ) -> IO:
        # Output file not specified. Pick a name that doesn't exist yet.
        filename = None
        if 'Content-Disposition' in final_response.headers:
            filename = filename_from_content_disposition(
                final_response.headers['Content-Disposition'])
        if not filename:
            filename = filename_from_url(
                url=initial_url,
                content_type=final_response.headers.get('Content-Type'),
            )
        unique_filename = get_unique_filename(filename)
        return open(unique_filename, buffering=0, mode='a+b')


class DownloadStatus:
    """Holds details about the download status."""

    def __init__(self, env):
        self.env = env
        self.downloaded = 0
        self.total_size = None
        self.resumed_from = 0
        self.time_started = None
        self.time_finished = None

    def started(self, output_file, resumed_from=0, total_size=None):
        assert self.time_started is None
        self.total_size = total_size
        self.downloaded = self.resumed_from = resumed_from
        self.time_started = monotonic()
        self.start_display(output_file=output_file)

    def start_display(self, output_file):
        from httpie.output.ui.rich_progress import (
            DummyDisplay,
            StatusDisplay,
            ProgressDisplay
        )

        message = f'Downloading to {output_file.name}'
        if self.env.show_displays:
            if self.total_size is None:
                # Rich does not support progress bars without a total
                # size given. Instead we use status objects.
                self.display = StatusDisplay(self.env)
            else:
                self.display = ProgressDisplay(self.env)
        else:
            self.display = DummyDisplay(self.env)

        self.display.start(
            total=self.total_size,
            at=self.downloaded,
            description=message
        )

    def chunk_downloaded(self, size):
        assert self.time_finished is None
        self.downloaded += size
        self.display.update(size)

    @property
    def has_finished(self):
        return self.time_finished is not None

    @property
    def time_spent(self):
        if (
            self.time_started is not None
            and self.time_finished is not None
        ):
            return self.time_finished - self.time_started
        else:
            return None

    def finished(self):
        assert self.time_started is not None
        assert self.time_finished is None
        self.time_finished = monotonic()
        if hasattr(self, 'display'):
            self.display.stop(self.time_spent)

    def terminate(self):
        if hasattr(self, 'display'):
            self.display.stop(self.time_spent)
