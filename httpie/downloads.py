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

from .output import RawStream
from .models import HTTPResponse
from .utils import humanize_bytes
from .compat import urlsplit

PARTIAL_CONTENT = 206


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
    if (first_byte_pos <= last_byte_pos
        and (instance_length is None
             or instance_length <= last_byte_pos)):
        raise ContentRangeError(
            'Invalid Content-Range returned: %r' % content_range)

    if (first_byte_pos != resumed_from
        or (instance_length is None
            or last_byte_pos + 1 != instance_length)):
        # Not what we asked for.
        raise ContentRangeError(
            'Unexpected Content-Range returned: %r' % content_range)

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
        self._progress = Progress(output=progress_file)
        self._resumed_from = 0

    def pre_request(self, request_headers):
        """Called just before the HTTP request is sent.

        Might alter `request_headers`.

        :type request_headers: dict

        """
        # Disable content encoding so that we can resume, etc.
        request_headers['Accept-Encoding'] = ''
        if self._resume:
            try:
                bytes_have = os.path.getsize(self._output_file.name)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise
            else:
                self._resumed_from = bytes_have
                # Set ``Range`` header to resume the download
                request_headers['Range'] = 'bytes=%d-' % bytes_have

    def start(self, response):
        """
        Initiate and return a stream for `response` body  with progress
        callback attached. Can be called only once.

        :param response: Initiated response object.
        :type response: requests.models.Response

        :return: RawStream, output_file

        """
        assert not self._progress._time_started

        total_size = response.headers.get('Content-Length')
        if total_size:
            total_size = int(total_size)

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
            # FIXME: Large chunks & chunked response => freezes (requests bug?)
            chunk_size=1
        )

        self._progress.output.write(
            'Saving to "%s"\n' % self._output_file.name)
        self._progress.report()

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
        self._progress.report()

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

    CLEAR_LINE = '\r\033[K'
    PROGRESS = '{percentage:0.2f}% ({downloaded}) of {total} ({speed}/s)'
    PROGRESS_NO_CONTENT_LENGTH = '{downloaded} ({speed}/s)'
    SUMMARY = '{downloaded} of {total} in {time:0.5f}s ({speed}/s)\n'

    def __init__(self, output):
        """
        :type output: file

        """
        self.output = output
        self.downloaded = 0
        self.total_size = None
        self._resumed_from = 0
        self._downloaded_prev = 0
        self._content_length_humanized = '?'
        self._time_started = None
        self._time_finished = None
        self._time_prev = None
        self._speed = 0

    def started(self, resumed_from=0, total_size=None):
        assert self._time_started is None
        if total_size is not None:
            self._content_length_humanized = humanize_bytes(total_size)
            self.total_size = total_size
        self.downloaded = self._resumed_from = resumed_from
        self._time_started = time()
        self._time_prev = self._time_started

    def chunk_downloaded(self, size):
        self.downloaded += size

    def report(self, interval=.6):
        now = time()

        # Update the reported speed on the first chunk and then once in a while
        if self._downloaded_prev and now - self._time_prev < interval:
            return

        self._speed = (
            (self.downloaded - self._downloaded_prev)
            / (now - self._time_prev)
        )
        self._time_prev = now
        self._downloaded_prev = self.downloaded

        if self.total_size:
            template = self.PROGRESS
            percentage = self.downloaded / self.total_size * 100
        else:
            template = self.PROGRESS_NO_CONTENT_LENGTH
            percentage = None

        self.output.write(self.CLEAR_LINE + template.format(
            percentage=percentage,
            downloaded=humanize_bytes(self.downloaded),
            total=self._content_length_humanized,
            speed=humanize_bytes(self._speed)
        ))

        self.output.flush()

    def finished(self):
        assert self._time_started is not None
        assert self._time_finished is None
        downloaded = self.downloaded - self._resumed_from
        self._time_finished = time()
        time_taken = self._time_finished - self._time_started
        self.output.write(self.CLEAR_LINE + self.SUMMARY.format(
            downloaded=humanize_bytes(downloaded),
            total=humanize_bytes(self.downloaded),
            speed=humanize_bytes(downloaded / time_taken),
            time=time_taken,
        ))
