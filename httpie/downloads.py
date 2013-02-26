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

PROGRESS_TPL = '{percentage:0.2f} % ({downloaded}) of {total} ({speed}/s)'
FINISHED_TPL = '{downloaded} of {total} in {time}s ({speed}/s)'


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
        self.bytes_total = 0
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

        self.bytes_total = int(response.headers.get('Content-Length'), 0)
        self.bytes_total_humanized = humanize_bytes(self.bytes_total)

        self.time_started = time()
        self.time_prev = self.time_started

        stream = RawStream(
            msg=HTTPResponse(response),
            with_headers=False,
            with_body=True,
            on_body_chunk_downloaded=self._on_progress
        )

        self.progress_file.write('Saving to %s\n' % self.output_file.name)
        self._report_status()

        return stream, self.output_file

    def has_finished(self):
        return self.bytes_downloaded == self.bytes_total

    def _get_unique_output_filename(self, url, content_type):
        suffix = 0
        fn = None
        while True:
            fn = self._get_output_filename(
                url=url,
                content_type=content_type,
                suffix=suffix
            )
            if not os.path.exists(fn):
                break
            suffix += 1
        return fn

    def _get_output_filename(self, url, content_type, suffix=None):

        fn = urlsplit(url).path.rstrip('/')
        fn = os.path.basename(fn) if fn else 'index'

        if suffix:
            fn += '-' + str(suffix)

        if '.' not in fn:
            ext = mimetypes.guess_extension(content_type.split(';')[0])
            if ext:
                fn += ext

        return fn

    def _on_progress(self, chunk):
        """
        A download progress callback.

        :param chunk: A chunk of response body data that has just
                      been downloaded and written to the output.
        :type chunk: bytes

        """
        self.bytes_downloaded += len(chunk)
        self._report_status()

    def _report_status(self):
        now = time()

        # Update the reported speed on the first chunk and once in a while.
        if not self.bytes_downloaded_prev or now - self.time_prev >= .6:
            self.speed = (
                (self.bytes_downloaded - self.bytes_downloaded_prev)
                / (now - self.time_prev)
            )
            self.time_prev = now
            self.bytes_downloaded_prev = self.bytes_downloaded

            self.progress_file.write(CLEAR_LINE)
            self.progress_file.write(PROGRESS_TPL.format(
                percentage=self.bytes_downloaded / self.bytes_total * 100,
                downloaded=humanize_bytes(self.bytes_downloaded),
                total=self.bytes_total_humanized,
                speed=humanize_bytes(self.speed)
            ))

        # Report avg. speed and total time when finished.
        if self.has_finished():
            bytes_downloaded = self.bytes_downloaded - self.bytes_resumed_from
            time_taken = time() - self.time_started
            self.progress_file.write(CLEAR_LINE)
            self.progress_file.write(FINISHED_TPL.format(
                downloaded=humanize_bytes(bytes_downloaded),
                total=humanize_bytes(self.bytes_total),
                speed=humanize_bytes(bytes_downloaded / time_taken),
                time=time_taken,
            ))
            self.progress_file.write('\n')
            self.output_file.close()

        self.progress_file.flush()
