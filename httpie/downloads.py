# coding=utf-8
"""
Download mode implementation.

"""
from __future__ import division

import os
import re
import sys
import requests
import threading
from time import sleep, time
from typing import IO, Tuple

from httpie.models import HTTPResponse
from httpie.output.streams import RawStream
from httpie.utils import (
    humanize_bytes, get_unique_filename, get_initial_filename
)


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
            'Invalid Content-Range format %r' % content_range)

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
    if (first_byte_pos >= last_byte_pos
        or (instance_length is not None
            and instance_length <= last_byte_pos)):
        raise ContentRangeError(
            'Invalid Content-Range returned: %r' % content_range)

    if (first_byte_pos != resumed_from
        or (instance_length is not None
            and last_byte_pos + 1 != instance_length)):
        # Not what we asked for.
        raise ContentRangeError(
            'Unexpected Content-Range returned (%r)'
            ' for the requested Range ("bytes=%d-")'
            % (content_range, resumed_from)
        )

    return last_byte_pos + 1


class Downloader:

    def __init__(
        self,
        output_file: IO,
        resume: bool = False,
        progress_file: IO = sys.stderr
    ):
        """
        :param resume: Should the download resume if partial download
                       already exists.

        :param output_dest: The file or dir to store response body in. If not
                            provided, file name will be guessed
                            from the response.

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

    def pre_request(self, url: str, request_headers: dict):
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
                request_headers['Range'] = 'bytes=%d-' % bytes_have
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
        # <https://github.com/jakubroztocil/httpie/issues/423>
        try:
            total_size = int(final_response.headers['Content-Length'])
        except (KeyError, ValueError, TypeError):
            total_size = None

        if not self._output_file:
            # create download output file
            self.output_filename = get_initial_filename(initial_url)
            self._output_file = open(
                get_unique_filename(self.output_filename), "a+b"
            )

        else:
            # output file provided
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
                except IOError:
                    pass  # stdout

        self.status.started(
            resumed_from=self._resumed_from,
            total_size=total_size
        )

        stream = RawStream(
            msg=HTTPResponse(final_response),
            with_headers=False,
            with_body=True,
            on_body_chunk_downloaded=self.chunk_downloaded,
            chunk_size=1024 * 8
        )

        self._progress_reporter.output.write(
            'Downloading %sto "%s"\n' % (
                (humanize_bytes(total_size) + ' '
                 if total_size is not None
                 else ''),
                self._output_file.name
            )
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
        self.time_started = time()

    def chunk_downloaded(self, size):
        assert self.time_finished is None
        self.downloaded += size

    @property
    def has_finished(self):
        return self.time_finished is not None

    def finished(self):
        assert self.time_started is not None
        assert self.time_finished is None
        self.time_finished = time()


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
        self._prev_time = time()
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

        now = time()

        if now - self._prev_time >= self._update_interval:
            downloaded = self.status.downloaded
            try:
                speed = ((downloaded - self._prev_bytes)
                         / (now - self._prev_time))
            except ZeroDivisionError:
                speed = 0

            if not self.status.total_size:
                self._status_line = PROGRESS_NO_CONTENT_LENGTH.format(
                    downloaded=humanize_bytes(downloaded),
                    speed=humanize_bytes(speed),
                )
            else:
                try:
                    percentage = downloaded / self.status.total_size * 100
                except ZeroDivisionError:
                    percentage = 0

                if not speed:
                    eta = '-:--:--'
                else:
                    s = int((self.status.total_size - downloaded) / speed)
                    h, s = divmod(s, 60 * 60)
                    m, s = divmod(s, 60)
                    eta = '{0}:{1:0>2}:{2:0>2}'.format(h, m, s)

                self._status_line = PROGRESS.format(
                    percentage=percentage,
                    downloaded=humanize_bytes(downloaded),
                    speed=humanize_bytes(speed),
                    eta=eta,
                )

            self._prev_time = now
            self._prev_bytes = downloaded

        self.output.write(
            CLEAR_LINE
            + ' '
            + SPINNER[self._spinner_pos]
            + ' '
            + self._status_line
        )
        self.output.flush()

        self._spinner_pos = (self._spinner_pos + 1
                             if self._spinner_pos + 1 != len(SPINNER)
                             else 0)

    def sum_up(self):
        actually_downloaded = (
            self.status.downloaded - self.status.resumed_from)
        time_taken = self.status.time_finished - self.status.time_started

        self.output.write(CLEAR_LINE)

        try:
            speed = actually_downloaded / time_taken
        except ZeroDivisionError:
            # Either time is 0 (not all systems provide `time.time`
            # with a better precision than 1 second), and/or nothing
            # has been downloaded.
            speed = actually_downloaded

        self.output.write(SUMMARY.format(
            downloaded=humanize_bytes(actually_downloaded),
            total=(self.status.total_size
                   and humanize_bytes(self.status.total_size)),
            speed=humanize_bytes(speed),
            time=time_taken,
        ))
        self.output.flush()
