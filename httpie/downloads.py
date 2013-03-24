"""
Download mode implementation.

"""
from __future__ import division
import mimetypes
import os
import sys
import errno
from time import time

from .output import RawStream
from .models import HTTPResponse
from .humanize import humanize_bytes
from .compat import urlsplit


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

    def pre_request(self, headers):
        """Called just before the HTTP request is sent.

        Might alter `headers`.

        :type headers: dict

        """
        # Disable content encoding so that we can resume, etc.
        headers['Accept-Encoding'] = ''
        if self._resume:
            try:
                bytes_have = os.path.getsize(self._output_file.name)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise
            else:
                self._resumed_from = bytes_have
                # Set ``Range`` header to resume the download
                # TODO: detect Range support first?
                headers['Range'] = '%d-' % bytes_have

    def start(self, response):
        """
        Initiate and return a stream for `response` body  with progress
        callback attached. Can be called only once.

        :param response: Initiated response object.
        :type response: requests.models.Response

        :return: RawStream, output_file

        """
        assert not self._progress._time_started

        content_length = response.headers.get('Content-Length')
        if content_length:
            content_length = int(content_length)

        if self._output_file:
            if not self._resume:
                self._output_file.seek(0)
                self._output_file.truncate()
        else:
            # TODO: should we take the filename from response.history[0].url?
            # Output file not specified. Pick a name that doesn't exist yet.
            content_type = response.headers.get('Content-Type', '')
            self._output_file = open(
                self._get_unique_output_filename(
                    url=response.url,
                    content_type=content_type,
                ),
                mode='a+b'
            )

        self._progress.start(
            resumed_from=self._resumed_from,
            content_length=content_length
        )

        stream = RawStream(
            msg=HTTPResponse(response),
            with_headers=False,
            with_body=True,
            on_body_chunk_downloaded=self._on_progress,
            # FIXME: large chunks & chunked response => freezes
            chunk_size=1
        )

        self._progress.output.write('Saving to %s\n' % self._output_file.name)
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
            and self._progress.content_length
            and self._progress.content_length != self._progress.downloaded
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
    PROGRESS = '{percentage:0.2f} % ({downloaded}) of {total} ({speed}/s)'
    PROGRESS_NO_CONTENT_LENGTH = '{downloaded} ({speed}/s)'
    SUMMARY = '{downloaded} of {total} in {time:0.5f}s ({speed}/s)\n'

    def __init__(self, output):
        """
        :type output: file

        """
        self.output = output
        self.downloaded = 0
        self.content_length = None
        self._resumed_from = 0
        self._downloaded_prev = 0
        self._content_length_humanized = '?'
        self._time_started = None
        self._time_prev = None
        self._speed = 0

    def start(self, resumed_from=0, content_length=None):
        assert self._time_started is None
        if content_length is not None:
            self._content_length_humanized = humanize_bytes(content_length)
            self.content_length = content_length
        self.downloaded = self._resumed_from = resumed_from
        self._time_started = time()
        self._time_prev = self._time_started

    def chunk_downloaded(self, size):
        self.downloaded += size

    def report(self, interval=.6):
        now = time()

        # Update the reported speed on the first chunk and once in a while.
        if self._downloaded_prev and now - self._time_prev < interval:
            return

        self._speed = (
            (self.downloaded - self._downloaded_prev)
            / (now - self._time_prev)
        )
        self._time_prev = now
        self._downloaded_prev = self.downloaded

        if self.content_length:
            template = self.PROGRESS
            percentage = self.downloaded / self.content_length * 100
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
        downloaded = self.downloaded - self._resumed_from
        time_taken = time() - self._time_started
        self.output.write(self.CLEAR_LINE + self.SUMMARY.format(
            downloaded=humanize_bytes(downloaded),
            total=humanize_bytes(self.downloaded),
            speed=humanize_bytes(downloaded / time_taken),
            time=time_taken,
        ))
