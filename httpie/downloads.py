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


CLEAR_LINE = '\r\033[K'
TPL_PROGRESS = '{percentage:0.2f} % ({downloaded}) of {total} ({speed}/s)'
TPL_PROGRESS_NO_CONTENT_LENGTH = '{downloaded} ({speed}/s)'
TPL_SUMMARY = '{downloaded} of {total} in {time:0.5f}s ({speed}/s)\n'


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
        self.output_file = output_file
        self.progress_file = progress_file
        self.resume = resume

        self.bytes_resumed_from = 0
        self.content_length = None
        self.bytes_downloaded = 0
        self.bytes_downloaded_prev = 0
        self.bytes_total_humanized = ''
        self.time_started = None
        self.time_prev = None
        self.speed = 0

    def alter_request_headers(self, headers):
        """Called just before a download request is sent."""
        # Disable content encoding so that we can resume, etc.
        headers['Accept-Encoding'] = ''
        if self.resume:
            try:
                bytes_have = os.path.getsize(self.output_file.name)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise
            else:
                self.bytes_resumed_from = self.bytes_downloaded = bytes_have
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
        assert not self.time_started

        if self.output_file:
            if not self.resume:
                self.output_file.seek(0)
                self.output_file.truncate()
        else:
            # TODO: should we take the filename from response.history[0].url?
            # TODO: --download implies --follow
            # Output file not specified. Pick a name that doesn't exist yet.
            content_type = response.headers.get('Content-Type', '')
            self.output_file = open(
                self._get_unique_output_filename(
                    url=response.url,
                    content_type=content_type,
                ),
                mode='a+b'
            )

        self.content_length = response.headers.get('Content-Length')
        if self.content_length:
            self.content_length = int(self.content_length)

        self.bytes_total_humanized = (humanize_bytes(self.content_length)
                                      if self.content_length else '?')

        self.time_started = time()
        self.time_prev = self.time_started

        stream = RawStream(
            msg=HTTPResponse(response),
            with_headers=False,
            with_body=True,
            on_body_chunk_downloaded=self._on_progress,
            # FIXME: large chunks & chunked response freezes
            chunk_size=1
        )

        self.progress_file.write('Saving to %s\n' % self.output_file.name)
        self.report_status()

        return stream, self.output_file

    def report_status(self, interval=.6):
        now = time()

        # Update the reported speed on the first chunk and once in a while.
        if self.bytes_downloaded_prev and now - self.time_prev < interval:
            return

        self.speed = (
            (self.bytes_downloaded - self.bytes_downloaded_prev)
            / (now - self.time_prev)
        )
        self.time_prev = now
        self.bytes_downloaded_prev = self.bytes_downloaded

        if self.content_length:
            template = TPL_PROGRESS
            percentage = self.bytes_downloaded / self.content_length * 100
        else:
            template = TPL_PROGRESS_NO_CONTENT_LENGTH
            percentage = None

        self.progress_file.write(CLEAR_LINE + template.format(
            percentage=percentage,
            downloaded=humanize_bytes(self.bytes_downloaded),
            total=self.bytes_total_humanized,
            speed=humanize_bytes(self.speed)
        ))

        self.progress_file.flush()

    def finished(self):
        self.output_file.close()

        bytes_downloaded = self.bytes_downloaded - self.bytes_resumed_from
        time_taken = time() - self.time_started
        self.progress_file.write(CLEAR_LINE + TPL_SUMMARY.format(
            downloaded=humanize_bytes(bytes_downloaded),
            total=humanize_bytes(self.bytes_downloaded),
            speed=humanize_bytes(bytes_downloaded / time_taken),
            time=time_taken,
        ))
        self.progress_file.flush()

    def _on_progress(self, chunk):
        """
        A download progress callback.

        :param chunk: A chunk of response body data that has just
                      been downloaded and written to the output.
        :type chunk: bytes

        """
        self.bytes_downloaded += len(chunk)
        self.report_status()

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
