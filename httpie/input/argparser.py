"""Parsing and processing of CLI input (args, auth credentials, files, stdin).

"""
import errno
import re
import sys
from argparse import ArgumentParser, ArgumentTypeError

from httpie.compat import urlsplit, str
from httpie.input.argtypes import (
    KeyValueArgType,
    AuthCredentials,
    parse_auth,
)
from httpie.input.constants import (
    URL_SCHEME_RE,
    HTTP_POST,
    HTTP_GET,
    OUT_RESP_BODY,
    OUTPUT_OPTIONS,
    PRETTY_MAP,
    PRETTY_STDOUT_TTY_ONLY,
    OUTPUT_OPTIONS_DEFAULT,
    OUTPUT_OPTIONS_DEFAULT_STDOUT_REDIRECTED,
    SEP_CREDENTIALS,
    SEP_GROUP_DATA_ITEMS,
    SEP_GROUP_ALL_ITEMS,
)
from httpie.input.exceptions import ParseError
from httpie.input.requestitems import parse_items
from httpie.plugins import plugin_manager
from httpie.utils import get_content_type


class ArgParser(ArgumentParser):
    """
    Adds additional logic to `argparse.ArgumentParser`.

    Handles all input (CLI args, file args, stdin), applies defaults,
    and performs extra validation.

    """

    def __init__(self, *args, **kwargs):
        kwargs['add_help'] = False
        super(ArgParser, self).__init__(*args, **kwargs)

    # noinspection PyMethodOverriding
    def parse_args(self, env, args=None, namespace=None):
        self.env = env
        self.args, no_options = super(ArgParser, self).parse_known_args(
            args=args,
            namespace=namespace,
        )
        if self.args.debug:
            self.args.traceback = True

        self._apply_no_options(no_options)
        self._validate_download_options()
        self._setup_standard_streams()
        self._process_output_options()
        self._process_pretty_options()
        self._process_method()
        self._parse_items()
        self._process_stdin()
        self._process_url()
        self._process_auth()

        return self.args

    def _print_message(self, message, file=None):
        # Sneak in our stderr/stdout.
        file = {
            sys.stdout: self.env.stdout,
            sys.stderr: self.env.stderr,
            None: self.env.stderr
        }.get(file, file)
        if not hasattr(file, 'buffer') and isinstance(message, str):
            message = message.encode(self.env.stdout_encoding)
        super(ArgParser, self)._print_message(message, file)

    def _setup_standard_streams(self):
        """
        Modify `env.stdout` and `env.stdout_isatty` based on args, if needed.

        """
        self.args.output_file_specified = bool(self.args.output_file)
        if self.args.download:
            # FIXME: Come up with a cleaner solution.
            if not self.args.output_file and not self.env.stdout_isatty:
                # Use stdout as the download output file.
                self.args.output_file = self.env.stdout
            # With `--download`, we write everything that would normally go to
            # `stdout` to `stderr` instead. Let's replace the stream so that
            # we don't have to use many `if`s throughout the codebase.
            # The response body will be treated separately.
            self.env.stdout = self.env.stderr
            self.env.stdout_isatty = self.env.stderr_isatty
        elif self.args.output_file:
            # When not `--download`ing, then `--output` simply replaces
            # `stdout`. The file is opened for appending, which isn't what
            # we want in this case.
            self.args.output_file.seek(0)
            try:
                self.args.output_file.truncate()
            except IOError as e:
                if e.errno == errno.EINVAL:
                    # E.g. /dev/null on Linux.
                    pass
                else:
                    raise
            self.env.stdout = self.args.output_file
            self.env.stdout_isatty = False

    def _process_auth(self):
        # TODO: refactor
        self.args.auth_plugin = None
        default_auth_plugin = plugin_manager.get_auth_plugins()[0]
        auth_type_set = self.args.auth_type is not None
        url = urlsplit(self.args.url)

        if self.args.auth is None and not auth_type_set:
            if url.username is not None:
                # Handle http://username:password@hostname/
                username = url.username
                password = url.password or ''
                self.args.auth = AuthCredentials(
                    key=username,
                    value=password,
                    sep=SEP_CREDENTIALS,
                    orig=SEP_CREDENTIALS.join([username, password])
                )

        if self.args.auth is not None or auth_type_set:
            if not self.args.auth_type:
                self.args.auth_type = default_auth_plugin.auth_type
            plugin = plugin_manager.get_auth_plugin(self.args.auth_type)()

            if plugin.auth_require and self.args.auth is None:
                self.error('--auth required')

            plugin.raw_auth = self.args.auth
            self.args.auth_plugin = plugin
            already_parsed = isinstance(self.args.auth, AuthCredentials)

            if self.args.auth is None or not plugin.auth_parse:
                self.args.auth = plugin.get_auth()
            else:
                if already_parsed:
                    # from the URL
                    credentials = self.args.auth
                else:
                    credentials = parse_auth(self.args.auth)

                if (not credentials.has_password() and
                        plugin.prompt_password):
                    if self.args.ignore_stdin:
                        # Non-tty stdin read by now
                        self.error(
                            'Unable to prompt for passwords because'
                            ' --ignore-stdin is set.'
                        )
                    credentials.prompt_password(url.netloc)
                self.args.auth = plugin.get_auth(
                    username=credentials.key,
                    password=credentials.value,
                )

    def _process_url(self):
        if not URL_SCHEME_RE.match(self.args.url):
            scheme = self.args.default_scheme + "://"

            # See if we're using curl style shorthand for localhost (:3000/foo)
            shorthand = re.match(r'^:(?!:)(\d*)(/?.*)$', self.args.url)
            if shorthand:
                port = shorthand.group(1)
                rest = shorthand.group(2)
                self.args.url = scheme + 'localhost'
                if port:
                    self.args.url += ':' + port
                self.args.url += rest
            else:
                self.args.url = scheme + self.args.url

    def _apply_no_options(self, no_options):
        """For every `--no-OPTION` in `no_options`, set `args.OPTION` to
        its default value. This allows for un-setting of options, e.g.,
        specified in config.

        """
        invalid = []

        for option in no_options:
            if not option.startswith('--no-'):
                invalid.append(option)
                continue

            # --no-option => --option
            inverted = '--' + option[5:]
            for action in self._actions:
                if inverted in action.option_strings:
                    setattr(self.args, action.dest, action.default)
                    break
            else:
                invalid.append(option)

        if invalid:
            msg = 'unrecognized arguments: %s'
            self.error(msg % ' '.join(invalid))

    def _process_stdin(self):
        if not self.args.ignore_stdin and not self.env.stdin_isatty:
            self._body_from_file(self.env.stdin)

    def _body_from_file(self, fd):
        """
        There can only be one source of request data.

        Bytes are always read.

        """
        if self.args.data:
            self.error('Request body (from stdin or a file) and request '
                       'data (key=value) cannot be mixed.')
        self.args.data = getattr(fd, 'buffer', fd).read()

        return

        if self.args.data:
            self.error(
                'Request body (from stdin or a file) and request '
                'data (key=value) cannot be mixed.'
            )
        f = getattr(fd, 'buffer', fd)
        if not self.args.chunked:
            data = f
        else:
            def stream():
                # http://docs.python-requests.org/en/master/user/advanced/#chunk-encoded-requests
                for chunk in f.read(8192):
                    yield chunk

            data = stream()
        self.args.data = data

    def _process_method(self):
        """Set `args.method` if not specified to either POST or GET
        based on whether the request has data or not.

        """
        if self.args.method is None:
            # Invoked as `http URL'.
            assert not self.args.items
            if not self.args.ignore_stdin and not self.env.stdin_isatty:
                self.args.method = HTTP_POST
            else:
                self.args.method = HTTP_GET

        # FIXME: False positive, e.g., "localhost" matches but is a valid URL.
        elif not re.match('^[a-zA-Z]+$', self.args.method):
            # Invoked as `http URL item+'. The URL is now in `args.method`
            # and the first ITEM is now incorrectly in `args.url`.
            try:
                # Parse the URL as an ITEM and store it as the first ITEM arg.
                self.args.items.insert(0, KeyValueArgType(
                    *SEP_GROUP_ALL_ITEMS).__call__(self.args.url))

            except ArgumentTypeError as e:
                if self.args.traceback:
                    raise
                self.error(e.args[0])

            else:
                # Set the URL correctly
                self.args.url = self.args.method
                # Infer the method
                has_data = (
                    (not self.args.ignore_stdin and
                     not self.env.stdin_isatty) or
                    any(item.sep in SEP_GROUP_DATA_ITEMS
                        for item in self.args.items)
                )
                self.args.method = HTTP_POST if has_data else HTTP_GET

    def _parse_items(self):
        """Parse `args.items` into `args.headers`, `args.data`, `args.params`,
         and `args.files`.

        """
        try:
            items = parse_items(items=self.args.items, is_form=self.args.form)
        except ParseError as e:
            if self.args.traceback:
                raise
            self.error(e.args[0])
        else:
            self.args.headers = items.headers
            self.args.data = items.data
            self.args.files = items.files
            self.args.params = items.params

        if self.args.files and not self.args.form:
            # `http url @/path/to/file`
            file_fields = list(self.args.files.keys())
            if file_fields != ['']:
                self.error(
                    'Invalid file fields (perhaps you meant --form?): %s'
                    % ','.join(file_fields))

            fn, fd, ct = self.args.files['']
            self.args.files = {}

            self._body_from_file(fd)

            if 'Content-Type' not in self.args.headers:
                content_type = get_content_type(fn)
                if content_type:
                    self.args.headers['Content-Type'] = content_type

    def _process_output_options(self):
        """Apply defaults to output options, or validate the provided ones.

        The default output options are stdout-type-sensitive.

        """

        def check_options(value, option):
            unknown = set(value) - OUTPUT_OPTIONS
            if unknown:
                self.error('Unknown output options: {0}={1}'.format(
                    option,
                    ','.join(unknown)
                ))

        if self.args.verbose:
            self.args.all = True

        if self.args.output_options is None:
            if self.args.verbose:
                self.args.output_options = ''.join(OUTPUT_OPTIONS)
            else:
                self.args.output_options = (
                    OUTPUT_OPTIONS_DEFAULT
                    if self.env.stdout_isatty
                    else OUTPUT_OPTIONS_DEFAULT_STDOUT_REDIRECTED
                )

        if self.args.output_options_history is None:
            self.args.output_options_history = self.args.output_options

        check_options(self.args.output_options, '--print')
        check_options(self.args.output_options_history, '--history-print')

        if self.args.download and OUT_RESP_BODY in self.args.output_options:
            # Response body is always downloaded with --download and it goes
            # through a different routine, so we remove it.
            self.args.output_options = str(
                set(self.args.output_options) - set(OUT_RESP_BODY))

    def _process_pretty_options(self):
        if self.args.prettify == PRETTY_STDOUT_TTY_ONLY:
            self.args.prettify = PRETTY_MAP[
                'all' if self.env.stdout_isatty else 'none']
        elif (self.args.prettify and self.env.is_windows and
                  self.args.output_file):
            self.error('Only terminal output can be colorized on Windows.')
        else:
            # noinspection PyTypeChecker
            self.args.prettify = PRETTY_MAP[self.args.prettify]

    def _validate_download_options(self):
        if not self.args.download:
            if self.args.download_resume:
                self.error('--continue only works with --download')
        if self.args.download_resume and not (
                self.args.download and self.args.output_file):
            self.error('--continue requires --output to be specified')
