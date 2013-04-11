# coding=utf-8
"""
Download mode implementation.

"""
from __future__ import division
import os
import re
import sys
import errno
import mimetypes
from time import time
import threading

from .output import RawStream
from .models import HTTPResponse
from .utils import humanize_bytes
from .compat import urlsplit


PARTIAL_CONTENT = 206


CLEAR_LINE = '\r\033[K'
PROGRESS = '{spinner} {percentage: 6.2f}% ({downloaded}) of {total} ({speed}/s)'
PROGRESS_NO_CONTENT_LENGTH = '{spinner} {downloaded} ({speed}/s)'
SUMMARY = 'Done. {downloaded} of {total} in {time:0.5f}s ({speed}/s)\n'
SPINNER = '|/-\\'


class ContentRangeError(ValueError):
    pass


def _parse_content_range(content_range, resumed_from):
    """
    Parse and validate Content-Range header.

    <http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html>

    :param content_range: the value of a Content-Range response header
                          eg. "bytes 21010-47021/47022"
    :param resumed_from: first byte pos. from the Range request header
    :return: total size of the response body when fully downloaded.

    """
    pattern = (
        '^bytes (?P<first_byte_pos>\d+)-(?P<last_byte_pos>\d+)'
        '/(\*|(?P<instance_length>\d+))$'
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


class Download(object):

    def __init__(self, output_file=None,
                 resume=False, progress_file=sys.stderr):
        """
        :param resume: Should the download resume if partial download
                       already exists.
        :type resume: bool

        :param output_file: The file to store response body in. If not
                            provided, it will be guessed from the response.
        :type output_file: file

        :param progress_file: Where to report download progress.
        :type progress_file: file

        """
        self._output_file = output_file
        self._resume = resume
        self._resumed_from = 0

        self._progress = Progress()
        self._progress_reporter = ProgressReporter(
            progress=self._progress,
            output=progress_file
        )

    def pre_request(self, request_headers):
        """Called just before the HTTP request is sent.

        Might alter `request_headers`.

        :type request_headers: dict

        """
        # Disable content encoding so that we can resume, etc.
        request_headers['Accept-Encoding'] = None
        if self._resume:
            try:
                bytes_have = os.path.getsize(self._output_file.name)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise
            else:
                # Set ``Range`` header to resume the download
                # TODO: Use "If-Range: mtime" to make sure it's fresh?
                request_headers['Range'] = 'bytes=%d-' % bytes_have
                self._resumed_from = bytes_have

    def start(self, response):
        """
        Initiate and return a stream for `response` body  with progress
        callback attached. Can be called only once.

        :param response: Initiated response object with headers already fetched
        :type response: requests.models.Response

        :return: RawStream, output_file

        """
        assert not self._progress.time_started

        try:
            total_size = int(response.headers['Content-Length'])
        except (KeyError, ValueError):
            total_size = None

        if self._output_file:
            if self._resume and response.status_code == PARTIAL_CONTENT:
                content_range = response.headers.get('Content-Range')
                if content_range:
                    total_size = _parse_content_range(
                        content_range, self._resumed_from)

            else:
                self._resumed_from = 0
                self._output_file.seek(0)
                self._output_file.truncate()
        else:
            # TODO: Should the filename be taken from response.history[0].url?
            # Output file not specified. Pick a name that doesn't exist yet.
            content_type = response.headers.get('Content-Type', '')
            self._output_file = open(
                self._get_unique_output_filename(
                    url=response.url,
                    content_type=content_type,
                ),
                mode='a+b'
            )

        self._progress.started(
            resumed_from=self._resumed_from,
            total_size=total_size
        )

        stream = RawStream(
            msg=HTTPResponse(response),
            with_headers=False,
            with_body=True,
            on_body_chunk_downloaded=self._on_progress,
            # TODO: Find the optimal chunk size.
            # The smaller it is the slower it gets, but gives better feedback.
            chunk_size=10
        )

        self._progress_reporter.output.write(
            'Saving to "%s"\n' % self._output_file.name)
        self._progress_reporter.report()

        return stream, self._output_file

    def finish(self):
        assert not self._output_file.closed
        self._output_file.close()
        self._progress.finished()

    @property
    def interrupted(self):
        return (
            self._output_file.closed
            and self._progress.total_size
            and self._progress.total_size != self._progress.downloaded
        )

    def _on_progress(self, chunk):
        """
        A download progress callback.

        :param chunk: A chunk of response body data that has just
                      been downloaded and written to the output.
        :type chunk: bytes

        """
        self._progress.chunk_downloaded(len(chunk))

    def _get_unique_output_filename(self, url, content_type):
        suffix = 0
        while True:
            fn = self._get_output_filename(url, content_type, suffix)
            if not os.path.exists(fn):
                return fn
            suffix += 1

    def _get_output_filename(self, url, content_type, suffix=None):

        suffix = '' if not suffix else '-' + str(suffix)

        fn = urlsplit(url).path.rstrip('/')
        fn = os.path.basename(fn) if fn else 'index'

        if '.' in fn:
            base, ext = os.path.splitext(fn)
        else:
            base = fn
            ext = mimetypes.guess_extension(content_type.split(';')[0]) or ''

        return base + suffix + ext


class Progress(object):

    def __init__(self):
        self.downloaded = 0
        self.total_size = None
        self.resumed_from = 0
        self.total_size_humanized = '?'
        self.time_started = None
        self.time_finished = None

    def started(self, resumed_from=0, total_size=None):
        assert self.time_started is None
        if total_size is not None:
            self.total_size_humanized = humanize_bytes(total_size)
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


class ProgressReporter(object):

    def __init__(self, progress, output, interval=.1, speed_interval=.7):
        """

        :type progress: Progress
        :type output: file
        """
        self.progress = progress
        self.output = output
        self._prev_bytes = 0
        self._prev_time = time()
        self._speed = 0
        self._spinner_pos = 0
        self._interval = interval
        self._speed_interval = speed_interval
        super(ProgressReporter, self).__init__()

    def report(self):
        if self.progress.has_finished:
            self.sum_up()
        else:
            self.report_speed()
            # TODO: quit on KeyboardInterrupt
            threading.Timer(self._interval, self.report).start()

    def report_speed(self):

        downloaded = self.progress.downloaded
        now = time()

        if self.progress.total_size:
            template = PROGRESS
            percentage = (
                downloaded / self.progress.total_size * 100)
        else:
            template = PROGRESS_NO_CONTENT_LENGTH
            percentage = None

        if now - self._prev_time >= self._speed_interval:
            # Update reported speed
            self._speed = (
                (downloaded - self._prev_bytes) / (now - self._prev_time))
            self._prev_time = now
            self._prev_bytes = downloaded

        self.output.write(CLEAR_LINE)
        self.output.write(template.format(
            spinner=SPINNER[self._spinner_pos],
            percentage=percentage,
            downloaded=humanize_bytes(downloaded),
            total=self.progress.total_size_humanized,
            speed=humanize_bytes(self._speed)
        ))
        self.output.flush()

        if downloaded > self._prev_bytes:
            self._spinner_pos += 1
            if self._spinner_pos == len(SPINNER):
                self._spinner_pos = 0

    def sum_up(self):
        actually_downloaded = (
            self.progress.downloaded - self.progress.resumed_from)
        time_taken = self.progress.time_finished - self.progress.time_started

        self.output.write(CLEAR_LINE)
        self.output.write(SUMMARY.format(
            downloaded=humanize_bytes(actually_downloaded),
            total=humanize_bytes(self.progress.downloaded),
            speed=humanize_bytes(actually_downloaded / time_taken),
            time=time_taken,
        ))
        self.output.flush()
