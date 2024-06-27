"""
Download mode implementation.

"""
import mimetypes
import os
import re
from mailbox import Message
from time import monotonic
from typing import IO, Optional, Tuple, List, Union
from urllib.parse import urlsplit

import niquests

from .models import HTTPResponse, OutputOptions
from .output.streams import RawStream
from .context import Environment
from .utils import split_header_values


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


def get_content_length(response: niquests.Response) -> Optional[int]:
    try:
        return int(response.headers['Content-Length'])
    except (KeyError, ValueError, TypeError):
        pass


def get_decodeable_content_encodings(encoded_response: niquests.Response) -> Optional[List[str]]:
    content_encoding = encoded_response.headers.get('Content-Encoding')
    if not content_encoding:
        return None
    applied_encodings = split_header_values(content_encoding)
    try:
        supported_decoders = encoded_response.raw.CONTENT_DECODERS
    except AttributeError:
        supported_decoders = ['gzip', 'deflate']
    for encoding in applied_encodings:
        if encoding not in supported_decoders:
            return None
    return applied_encodings


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

        """
        self.finished = False
        self.status = DownloadStatus(env=env)
        self._output_file_created = False
        self._output_file = output_file
        self._resume = resume
        self._resumed_from = 0

    def pre_request(self, request_headers: dict):
        """Called just before the HTTP request is sent.

        Might alter `request_headers`.

        """
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
        final_response: niquests.Response
    ) -> Tuple[RawStream, IO]:
        """
        Initiate and return a stream for `response` body  with progress
        callback attached. Can be called only once.

        :param initial_url: The original requested URL
        :param final_response: Initiated response object with headers already fetched

        :return: RawStream, output_file

        """
        assert not self.status.time_started

        # Even though we specify `Accept-Encoding: identity`, the server might still encode the response.
        # In such cases, the reported size will be of the decoded content, not the downloaded bytes.
        # This is a limitation of the underlying Niquests library <https://github.com/jawah/niquests/issues/127>.
        decoded_from = get_decodeable_content_encodings(final_response)
        total_size = get_content_length(final_response)

        if not self._output_file:
            self._output_file = self._get_output_file_from_response(
                initial_url=initial_url,
                final_response=final_response,
            )
            self._output_file_created = True
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
            total_size=total_size,
            decoded_from=decoded_from,
        )

        return stream, self._output_file

    def finish(self):
        assert not self.finished
        self.finished = True
        self.status.finished()
        # we created the output file in the process, closing it now.
        if self._output_file_created:
            self._output_file.close()

    def failed(self):
        self.status.terminate()

    @property
    def is_interrupted(self) -> bool:
        return self.status.is_interrupted

    def chunk_downloaded(self, chunk_or_new_total: Union[bytes, int]) -> None:
        """
        A download progress callback.

        :param chunk_or_new_total: A chunk of response body data that has just
                      been downloaded and written to the output.

        """
        if isinstance(chunk_or_new_total, int):
            self.status.set_total(chunk_or_new_total)
        else:
            self.status.chunk_downloaded(len(chunk_or_new_total))

    @staticmethod
    def _get_output_file_from_response(
        initial_url: str,
        final_response: niquests.Response,
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


DECODED_FROM_SUFFIX = ' - decoded using {encodings}'


class DownloadStatus:
    """Holds details about the download status."""

    def __init__(self, env):
        self.env = env
        self.downloaded = 0
        self.total_size = None
        self.decoded_from = []
        self.resumed_from = 0
        self.time_started = None
        self.time_finished = None
        self.display = None

    def started(self, output_file, resumed_from=0, total_size=None, decoded_from: List[str] = None):
        assert self.time_started is None
        self.total_size = total_size
        self.decoded_from = decoded_from
        self.downloaded = self.resumed_from = resumed_from
        self.time_started = monotonic()
        self.start_display(output_file=output_file)

    def start_display(self, output_file):
        from httpie.output.ui.rich_progress import (
            DummyProgressDisplay,
            ProgressDisplayNoTotal,
            ProgressDisplayFull
        )
        message = f'Downloading to {output_file.name}'
        summary_suffix = ''

        if self.decoded_from:
            encodings = ', '.join(f'`{enc}`' for enc in self.decoded_from)
            message_suffix = DECODED_FROM_SUFFIX.format(encodings=encodings)
        else:
            message_suffix = ''

        if not self.env.show_displays:
            progress_display_class = DummyProgressDisplay
        else:
            has_reliable_total = self.total_size is not None

            if has_reliable_total:
                progress_display_class = ProgressDisplayFull
            else:
                progress_display_class = ProgressDisplayNoTotal

        self.display = progress_display_class(
            env=self.env,
            total_size=self.total_size,
            resumed_from=self.resumed_from,
            description=message + message_suffix,
            summary_suffix=summary_suffix,
        )
        self.display.start()

    def chunk_downloaded(self, size):
        assert self.time_finished is None
        self.downloaded += size
        self.display.update(size)

    def set_total(self, total: int) -> None:
        assert self.time_finished is None
        prev_value = self.downloaded
        self.downloaded = total
        self.display.update(total - prev_value)

    @property
    def has_finished(self):
        return self.time_finished is not None

    @property
    def is_interrupted(self):
        return (
            self.has_finished
            and self.total_size is not None
            and not self.decoded_from
            and self.total_size != self.downloaded
        )

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
        if self.display:
            self.display.stop(self.time_spent)

    def terminate(self):
        if self.display:
            self.display.stop(self.time_spent)
