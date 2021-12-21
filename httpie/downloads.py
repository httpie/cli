"""
Download mode implementation.

"""
import mimetypes
import os
import re
import sys
import threading
from mailbox import Message
from time import sleep, monotonic
from typing import IO, Optional, Tuple
from urllib.parse import urlsplit

import requests

from .models import HTTPResponse, OutputOptions
from .output.streams import RawStream
from .utils import humanize_bytes


PARTIAL_CONTENT = 206

CLEAR_LINE = '\r\033[K'
PROGRESS = (
    '{percentage: 6.2f} %'
    ' {downloaded: >10}'
    ' {speed: >10}/s'
    ' {eta: >8} ETA'
)
PROGRESS_NO_CONTENT_LENGTH = '{downloaded: >10} {speed: >10}/s'
SUMMARY = 'Done. {downloaded} in {time:0.5f}s ({speed}/s)\n'
SPINNER = '|/-\\'


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
        output_file: IO = None,
        resume: bool = False,
        progress_file: IO = sys.stderr
    ):
        """
        :param resume: Should the download resume if partial download
                       already exists.

        :param output_file: The file to store response body in. If not
                            provided, it will be guessed from the response.

        :param progress_file: Where to report download progress.

        """
        self.finished = False
        self.status = DownloadStatus()
        self._output_file = output_file
        self._resume = resume
        self._resumed_from = 0
        self._progress_reporter = ProgressReporterThread(
            status=self.status,
            output=progress_file
        )

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

        self.status.started(
            resumed_from=self._resumed_from,
            total_size=total_size
        )

        output_options = OutputOptions.from_message(final_response, headers=False, body=True)
        stream = RawStream(
            msg=HTTPResponse(final_response),
            output_options=output_options,
            on_body_chunk_downloaded=self.chunk_downloaded,
        )

        self._progress_reporter.output.write(
            f'Downloading {humanize_bytes(total_size) + " " if total_size is not None else ""}'
            f'to "{self._output_file.name}"\n'
        )
        self._progress_reporter.start()

        return stream, self._output_file

    def finish(self):
        assert not self.finished
        self.finished = True
        self.status.finished()

    def failed(self):
        self._progress_reporter.stop()

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

    def __init__(self):
        self.downloaded = 0
        self.total_size = None
        self.resumed_from = 0
        self.time_started = None
        self.time_finished = None

    def started(self, resumed_from=0, total_size=None):
        assert self.time_started is None
        self.total_size = total_size
        self.downloaded = self.resumed_from = resumed_from
        self.time_started = monotonic()

    def chunk_downloaded(self, size):
        assert self.time_finished is None
        self.downloaded += size

    @property
    def has_finished(self):
        return self.time_finished is not None

    def finished(self):
        assert self.time_started is not None
        assert self.time_finished is None
        self.time_finished = monotonic()


class ProgressReporterThread(threading.Thread):
    """
    Reports download progress based on its status.

    Uses threading to periodically update the status (speed, ETA, etc.).

    """

    def __init__(
        self,
        status: DownloadStatus,
        output: IO,
        tick=.1,
        update_interval=1
    ):
        super().__init__()
        self.status = status
        self.output = output
        self._tick = tick
        self._update_interval = update_interval
        self._spinner_pos = 0
        self._status_line = ''
        self._prev_bytes = 0
        self._prev_time = monotonic()
        self._should_stop = threading.Event()

    def stop(self):
        """Stop reporting on next tick."""
        self._should_stop.set()

    def run(self):
        while not self._should_stop.is_set():
            if self.status.has_finished:
                self.sum_up()
                break

            self.report_speed()
            sleep(self._tick)

    def report_speed(self):
        now = monotonic()
        if now - self._prev_time >= self._update_interval:
            downloaded = self.status.downloaded
            speed = ((downloaded - self._prev_bytes)
                     / (now - self._prev_time))

            if not self.status.total_size:
                self._status_line = PROGRESS_NO_CONTENT_LENGTH.format(
                    downloaded=humanize_bytes(downloaded),
                    speed=humanize_bytes(speed),
                )
            else:
                percentage = (downloaded / self.status.total_size * 100
                              if self.status.total_size
                              else 0)

                if not speed:
                    eta = '-:--:--'
                else:
                    s = int((self.status.total_size - downloaded) / speed)
                    h, s = divmod(s, 60 * 60)
                    m, s = divmod(s, 60)
                    eta = f'{h}:{m:0>2}:{s:0>2}'

                self._status_line = PROGRESS.format(
                    percentage=percentage,
                    downloaded=humanize_bytes(downloaded),
                    speed=humanize_bytes(speed),
                    eta=eta,
                )

            self._prev_time = now
            self._prev_bytes = downloaded

        self.output.write(
            f'{CLEAR_LINE} {SPINNER[self._spinner_pos]} {self._status_line}'
        )
        self.output.flush()

        self._spinner_pos = (self._spinner_pos + 1) % len(SPINNER)

    def sum_up(self):
        actually_downloaded = (
            self.status.downloaded - self.status.resumed_from)
        time_taken = self.status.time_finished - self.status.time_started
        speed = actually_downloaded / time_taken if time_taken else actually_downloaded

        self.output.write(CLEAR_LINE)

        self.output.write(SUMMARY.format(
            downloaded=humanize_bytes(actually_downloaded),
            total=(self.status.total_size
                   and humanize_bytes(self.status.total_size)),
            speed=humanize_bytes(speed),
            time=time_taken,
        ))
        self.output.flush()
