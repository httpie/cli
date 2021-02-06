==========
Change Log
==========

This document records all notable changes to `HTTPie <https://httpie.org>`_.
This project adheres to `Semantic Versioning <https://semver.org/>`_.



`2.4.0`_ (2021-02-06)
---------------------
* Added support for ``--session`` cookie expiration based on ``Set-Cookie: max-age=<n>``. (`#1029`_)
* Show a ``--check-status`` warning with ``--quiet`` as well, not only when the output si redirected. (`#1026`_)
* Fixed upload with ``--session`` (`#1020`_).
* Fixed a missing blank line between request and response (`#1006`_).


`2.3.0`_ (2020-10-25)
-------------------------

* Added support for streamed uploads (`#201`_).
* Added support for multipart upload streaming (`#684`_).
* Added support for body-from-file upload streaming (``http pie.dev/post @file``).
* Added ``--chunked`` to enable chunked transfer encoding (`#753`_).
* Added ``--multipart`` to allow ``multipart/form-data`` encoding for non-file ``--form`` requests as well.
* Added support for preserving field order in multipart requests (`#903`_).
* Added ``--boundary`` to allow a custom boundary string for ``multipart/form-data`` requests.
* Added support for combining cookies specified on the CLI and in a session file (`#932`_).
* Added out of the box SOCKS support with no extra installation (`#904`_).
* Added ``--quiet, -q`` flag to enforce silent behaviour.
* Fixed the handling of invalid ``expires`` dates in ``Set-Cookie`` headers (`#963`_).
* Removed Tox testing entirely (`#943`_).


`2.2.0`_ (2020-06-18)
-------------------------

* Added support for custom content types for uploaded files (`#668`_).
* Added support for ``$XDG_CONFIG_HOME`` (`#920`_).
* Added support for ``Set-Cookie``-triggered cookie expiration (`#853`_).
* Added ``--format-options`` to allow disabling sorting, etc. (`#128`_)
* Added ``--sorted`` and ``--unsorted`` shortcuts for (un)setting all sorting-related ``--format-options``. (`#128`_)
* Added ``--ciphers`` to allow configuring OpenSSL ciphers (`#870`_).
* Added ``netrc`` support for auth plugins. Enabled for ``--auth-type=basic``
  and ``digest``, 3rd parties may opt in (`#718`_, `#719`_, `#852`_, `#934`_).
* Fixed built-in plugins-related circular imports (`#925`_).


`2.1.0`_ (2020-04-18)
---------------------

* Added ``--path-as-is`` to bypass dot segment (``/../`` or ``/./``)
  URL squashing (`#895`_).
* Changed the default ``Accept`` header value for JSON requests from
  ``application/json, */*`` to ``application/json, */*;q=0.5``
  to clearly indicate preference (`#488`_).
* Fixed ``--form`` file upload mixed with redirected ``stdin`` error handling
  (`#840`_).


`2.0.0`_ (2020-01-12)
-------------------------
* Removed Python 2.7 support (`EOL Jan 2020 <https://www.python.org/doc/sunset-python-2/>`_).
* Added ``--offline`` to allow building an HTTP request and printing it but not
  actually sending it over the network.
* Replaced the old collect-all-then-process handling of HTTP communication
  with one-by-one processing of each HTTP request or response as they become
  available. This means that you can see headers immediately,
  see what is being sent even if the request fails, etc.
* Removed automatic config file creation to avoid concurrency issues.
* Removed the default 30-second connection ``--timeout`` limit.
* Removed Python’s default limit of 100 response headers.
* Added ``--max-headers`` to allow setting the max header limit.
* Added ``--compress`` to allow request body compression.
* Added ``--ignore-netrc`` to allow bypassing credentials from ``.netrc``.
* Added ``https`` alias command with ``https://`` as the default scheme.
* Added ``$ALL_PROXY`` documentation.
* Added type annotations throughout the codebase.
* Added ``tests/`` to the PyPi package for the convenience of
  downstream package maintainers.
* Fixed an error when ``stdin`` was a closed fd.
* Improved ``--debug`` output formatting.


`1.0.3`_ (2019-08-26)
---------------------

* Fixed CVE-2019-10751 — the way the output filename is generated for
  ``--download`` requests without ``--output`` resulting in a redirect has
  been changed to only consider the initial URL as the base for the generated
  filename, and not the final one. This fixes a potential security issue under
  the following scenario:

  1. A ``--download`` request with no explicit ``--output`` is made (e.g.,
     ``$ http -d example.org/file.txt``), instructing httpie to
     `generate the output filename <https://httpie.org/doc#downloaded-filename>`_
     from the ``Content-Disposition`` response header, or from the URL if the header
     is not provided.
  2. The server handling the request has been modified by an attacker and
     instead of the expected response the URL returns a redirect to another
     URL, e.g., ``attacker.example.org/.bash_profile``, whose response does
     not provide  a ``Content-Disposition`` header (i.e., the base for the
     generated filename becomes ``.bash_profile`` instead of ``file.txt``).
  3. Your current directory doesn’t already contain ``.bash_profile``
     (i.e., no unique suffix is added to the generated filename).
  4. You don’t notice the potentially unexpected output filename
     as reported by httpie in the console output
     (e.g., ``Downloading 100.00 B to ".bash_profile"``).

  Reported by Raul Onitza and Giulio Comi.


`1.0.2`_ (2018-11-14)
-------------------------

* Fixed tests for installation with pyOpenSSL.


`1.0.1`_ (2018-11-14)
-------------------------

* Removed external URL calls from tests.


`1.0.0`_ (2018-11-02)
-------------------------

* Added ``--style=auto`` which follows the terminal ANSI color styles.
* Added support for selecting TLS 1.3 via ``--ssl=tls1.3``
  (available once implemented in upstream libraries).
* Added ``true``/``false`` as valid values for ``--verify``
  (in addition to ``yes``/``no``) and the boolean value is case-insensitive.
* Changed the default ``--style`` from ``solarized`` to ``auto`` (on Windows it stays ``fruity``).
* Fixed default headers being incorrectly case-sensitive.
* Removed Python 2.6 support.



`0.9.9`_ (2016-12-08)
---------------------

* Fixed README.


`0.9.8`_ (2016-12-08)
---------------------

* Extended auth plugin API.
* Added exit status code ``7`` for plugin errors.
* Added support for ``curses``-less Python installations.
* Fixed ``REQUEST_ITEM`` arg incorrectly being reported as required.
* Improved ``CTRL-C`` interrupt handling.
* Added the standard exit status code ``130`` for keyboard interrupts.


`0.9.6`_ (2016-08-13)
---------------------

* Added Python 3 as a dependency for Homebrew installations
  to ensure some of the newer HTTP features work out of the box
  for macOS users (starting with HTTPie 0.9.4.).
* Added the ability to unset a request header with ``Header:``, and send an
  empty value with ``Header;``.
* Added ``--default-scheme <URL_SCHEME>`` to enable things like
  ``$ alias https='http --default-scheme=https``.
* Added ``-I`` as a shortcut for ``--ignore-stdin``.
* Added fish shell completion (located in ``extras/httpie-completion.fish``
  in the GitHub repo).
* Updated ``requests`` to 2.10.0 so that SOCKS support can be added via
  ``pip install requests[socks]``.
* Changed the default JSON ``Accept`` header from ``application/json``
  to ``application/json, */*``.
* Changed the pre-processing of request HTTP headers so that any leading
  and trailing whitespace is removed.


`0.9.4`_ (2016-07-01)
---------------------

* Added ``Content-Type`` of files uploaded in ``multipart/form-data`` requests
* Added ``--ssl=<PROTOCOL>`` to specify the desired SSL/TLS protocol version
  to use for HTTPS requests.
* Added JSON detection with ``--json, -j`` to work around incorrect
  ``Content-Type``
* Added ``--all`` to show intermediate responses such as redirects (with ``--follow``)
* Added ``--history-print, -P WHAT`` to specify formatting of intermediate responses
* Added ``--max-redirects=N`` (default 30)
* Added ``-A`` as short name for ``--auth-type``
* Added ``-F`` as short name for ``--follow``
* Removed the ``implicit_content_type`` config option
  (use ``"default_options": ["--form"]`` instead)
* Redirected ``stdout`` doesn't trigger an error anymore when ``--output FILE``
  is set
* Changed the default ``--style`` back to ``solarized`` for better support
  of light and dark terminals
* Improved ``--debug`` output
* Fixed ``--session`` when used with ``--download``
* Fixed ``--download`` to trim too long filenames before saving the file
* Fixed the handling of ``Content-Type`` with multiple ``+subtype`` parts
* Removed the XML formatter as the implementation suffered from multiple issues



`0.9.3`_ (2016-01-01)
---------------------

* Changed the default color ``--style`` from ``solarized`` to ``monokai``
* Added basic Bash autocomplete support (need to be installed manually)
* Added request details to connection error messages
* Fixed ``'requests.packages.urllib3' has no attribute 'disable_warnings'``
  errors that occurred in some installations
* Fixed colors and formatting on Windows
* Fixed ``--auth`` prompt on Windows


`0.9.2`_ (2015-02-24)
---------------------

* Fixed compatibility with Requests 2.5.1
* Changed the default JSON ``Content-Type`` to ``application/json`` as UTF-8
  is the default JSON encoding


`0.9.1`_ (2015-02-07)
---------------------

* Added support for Requests transport adapter plugins
  (see `httpie-unixsocket <https://github.com/httpie/httpie-unixsocket>`_
  and `httpie-http2 <https://github.com/httpie/httpie-http2>`_)


`0.9.0`_ (2015-01-31)
---------------------

* Added ``--cert`` and ``--cert-key`` parameters to specify a client side
  certificate and private key for SSL
* Improved unicode support
* Improved terminal color depth detection via ``curses``
* To make it easier to deal with Windows paths in request items, ``\``
  now only escapes special characters (the ones that are used as key-value
  separators by HTTPie)
* Switched from ``unittest`` to ``pytest``
* Added Python `wheel` support
* Various test suite improvements
* Added ``CONTRIBUTING``
* Fixed ``User-Agent`` overwriting when used within a session
* Fixed handling of empty passwords in URL credentials
* Fixed multiple file uploads with the same form field name
* Fixed ``--output=/dev/null`` on Linux
* Miscellaneous bugfixes


`0.8.0`_ (2014-01-25)
---------------------

* Added ``field=@file.txt`` and ``field:=@file.json`` for embedding
  the contents of text and JSON files into request data
* Added curl-style shorthand for localhost
* Fixed request ``Host`` header value output so that it doesn't contain
  credentials, if included in the URL


`0.7.1`_ (2013-09-24)
---------------------

* Added ``--ignore-stdin``
* Added support for auth plugins
* Improved ``--help`` output
* Improved ``Content-Disposition`` parsing for ``--download`` mode
* Update to Requests 2.0.0


`0.6.0`_ (2013-06-03)
---------------------

* XML data is now formatted
* ``--session`` and ``--session-read-only`` now also accept paths to
  session files (eg. ``http --session=/tmp/session.json example.org``)


`0.5.1`_ (2013-05-13)
---------------------

* ``Content-*`` and ``If-*`` request headers are not stored in sessions
  anymore as they are request-specific


`0.5.0`_ (2013-04-27)
---------------------

* Added a download mode via ``--download``
* Fixes miscellaneous bugs


`0.4.1`_ (2013-02-26)
---------------------

* Fixed ``setup.py``


`0.4.0`_ (2013-02-22)
---------------------

* Added Python 3.3 compatibility
* Added Requests >= v1.0.4 compatibility
* Added support for credentials in URL
* Added ``--no-option`` for every ``--option`` to be config-friendly
* Mutually exclusive arguments can be specified multiple times. The
  last value is used


`0.3.0`_ (2012-09-21)
---------------------

* Allow output redirection on Windows
* Added configuration file
* Added persistent session support
* Renamed ``--allow-redirects`` to ``--follow``
* Improved the usability of ``http --help``
* Fixed installation on Windows with Python 3
* Fixed colorized output on Windows with Python 3
* CRLF HTTP header field separation in the output
* Added exit status code ``2`` for timed-out requests
* Added the option to separate colorizing and formatting
  (``--pretty=all``, ``--pretty=colors`` and ``--pretty=format``)
  ``--ugly`` has bee removed in favor of ``--pretty=none``


`0.2.7`_ (2012-08-07)
---------------------

* Added compatibility with Requests 0.13.6
* Added streamed terminal output. ``--stream, -S`` can be used to enable
  streaming also with ``--pretty`` and to ensure a more frequent output
  flushing
* Added support for efficient large file downloads
* Sort headers by name (unless ``--pretty=none``)
* Response body is fetched only when needed (e.g., not with ``--headers``)
* Improved content type matching
* Updated Solarized color scheme
* Windows: Added ``--output FILE`` to store output into a file
  (piping results in corrupted data on Windows)
* Proper handling of binary requests and responses
* Fixed printing of ``multipart/form-data`` requests
* Renamed ``--traceback`` to ``--debug``


`0.2.6`_ (2012-07-26)
---------------------

* The short option for ``--headers`` is now ``-h`` (``-t`` has been
  removed, for usage use ``--help``)
* Form data and URL parameters can have multiple fields with the same name
  (e.g.,``http -f url a=1 a=2``)
* Added ``--check-status`` to exit with an error on HTTP 3xx, 4xx and
  5xx (3, 4, and 5, respectively)
* If the output is piped to another program or redirected to a file,
  the default behaviour is to only print the response body
  (It can still be overwritten via the ``--print`` flag.)
* Improved highlighting of HTTP headers
* Added query string parameters (``param==value``)
* Added support for terminal colors under Windows


`0.2.5`_ (2012-07-17)
---------------------

* Unicode characters in prettified JSON now don't get escaped for
  improved readability
* --auth now prompts for a password if only a username provided
* Added support for request payloads from a file path with automatic
  ``Content-Type`` (``http URL @/path``)
* Fixed missing query string when displaying the request headers via
  ``--verbose``
* Fixed Content-Type for requests with no data


`0.2.2`_ (2012-06-24)
---------------------

* The ``METHOD`` positional argument can now be omitted (defaults to
  ``GET``, or to ``POST`` with data)
* Fixed --verbose --form
* Added support for Tox


`0.2.1`_ (2012-06-13)
---------------------

* Added compatibility with ``requests-0.12.1``
* Dropped custom JSON and HTTP lexers in favor of the ones newly included
  in ``pygments-1.5``


`0.2.0`_ (2012-04-25)
---------------------

* Added Python 3 support
* Added the ability to print the HTTP request as well as the response
  (see ``--print`` and ``--verbose``)
* Added support for Digest authentication
* Added file upload support
  (``http -f POST file_field_name@/path/to/file``)
* Improved syntax highlighting for JSON
* Added support for field name escaping
* Many bug fixes


`0.1.6`_ (2012-03-04)
---------------------

* Fixed ``setup.py``


`0.1.5`_ (2012-03-04)
---------------------

* Many improvements and bug fixes


`0.1.4`_ (2012-02-28)
---------------------

* Many improvements and bug fixes


`0.1.0`_ (2012-02-25)
---------------------

* Initial public release


.. _`0.1.0`: https://github.com/httpie/httpie/commit/b966efa
.. _0.1.4: https://github.com/httpie/httpie/compare/b966efa...0.1.4
.. _0.1.5: https://github.com/httpie/httpie/compare/0.1.4...0.1.5
.. _0.1.6: https://github.com/httpie/httpie/compare/0.1.5...0.1.6
.. _0.2.0: https://github.com/httpie/httpie/compare/0.1.6...0.2.0
.. _0.2.1: https://github.com/httpie/httpie/compare/0.2.0...0.2.1
.. _0.2.2: https://github.com/httpie/httpie/compare/0.2.1...0.2.2
.. _0.2.5: https://github.com/httpie/httpie/compare/0.2.2...0.2.5
.. _0.2.6: https://github.com/httpie/httpie/compare/0.2.5...0.2.6
.. _0.2.7: https://github.com/httpie/httpie/compare/0.2.5...0.2.7
.. _0.3.0: https://github.com/httpie/httpie/compare/0.2.7...0.3.0
.. _0.4.0: https://github.com/httpie/httpie/compare/0.3.0...0.4.0
.. _0.4.1: https://github.com/httpie/httpie/compare/0.4.0...0.4.1
.. _0.5.0: https://github.com/httpie/httpie/compare/0.4.1...0.5.0
.. _0.5.1: https://github.com/httpie/httpie/compare/0.5.0...0.5.1
.. _0.6.0: https://github.com/httpie/httpie/compare/0.5.1...0.6.0
.. _0.7.1: https://github.com/httpie/httpie/compare/0.6.0...0.7.1
.. _0.8.0: https://github.com/httpie/httpie/compare/0.7.1...0.8.0
.. _0.9.0: https://github.com/httpie/httpie/compare/0.8.0...0.9.0
.. _0.9.1: https://github.com/httpie/httpie/compare/0.9.0...0.9.1
.. _0.9.2: https://github.com/httpie/httpie/compare/0.9.1...0.9.2
.. _0.9.3: https://github.com/httpie/httpie/compare/0.9.2...0.9.3
.. _0.9.4: https://github.com/httpie/httpie/compare/0.9.3...0.9.4
.. _0.9.6: https://github.com/httpie/httpie/compare/0.9.4...0.9.6
.. _0.9.8: https://github.com/httpie/httpie/compare/0.9.6...0.9.8
.. _0.9.9: https://github.com/httpie/httpie/compare/0.9.8...0.9.9
.. _1.0.0: https://github.com/httpie/httpie/compare/0.9.9...1.0.0
.. _1.0.1: https://github.com/httpie/httpie/compare/1.0.0...1.0.1
.. _1.0.2: https://github.com/httpie/httpie/compare/1.0.1...1.0.2
.. _1.0.3: https://github.com/httpie/httpie/compare/1.0.2...1.0.3
.. _2.0.0: https://github.com/httpie/httpie/compare/1.0.3...2.0.0
.. _2.1.0: https://github.com/httpie/httpie/compare/2.0.0...2.1.0
.. _2.2.0: https://github.com/httpie/httpie/compare/2.1.0...2.2.0
.. _2.3.0: https://github.com/httpie/httpie/compare/2.2.0...2.3.0
.. _2.4.0: https://github.com/httpie/httpie/compare/2.3.0...2.4.0
.. _2.5.0-dev: https://github.com/httpie/httpie/compare/2.4.0...master

.. _#128: https://github.com/httpie/httpie/issues/128
.. _#201: https://github.com/httpie/httpie/issues/201
.. _#488: https://github.com/httpie/httpie/issues/488
.. _#668: https://github.com/httpie/httpie/issues/668
.. _#684: https://github.com/httpie/httpie/issues/684
.. _#718: https://github.com/httpie/httpie/issues/718
.. _#719: https://github.com/httpie/httpie/issues/719
.. _#753: https://github.com/httpie/httpie/issues/753
.. _#840: https://github.com/httpie/httpie/issues/840
.. _#853: https://github.com/httpie/httpie/issues/853
.. _#852: https://github.com/httpie/httpie/issues/852
.. _#870: https://github.com/httpie/httpie/issues/870
.. _#895: https://github.com/httpie/httpie/issues/895
.. _#903: https://github.com/httpie/httpie/issues/903
.. _#920: https://github.com/httpie/httpie/issues/920
.. _#904: https://github.com/httpie/httpie/issues/904
.. _#925: https://github.com/httpie/httpie/issues/925
.. _#932: https://github.com/httpie/httpie/issues/932
.. _#934: https://github.com/httpie/httpie/issues/934
.. _#943: https://github.com/httpie/httpie/issues/943
.. _#963: https://github.com/httpie/httpie/issues/963
.. _#1006: https://github.com/httpie/httpie/issues/1006
.. _#1020: https://github.com/httpie/httpie/issues/1020
.. _#1026: https://github.com/httpie/httpie/issues/1026
.. _#1029: https://github.com/httpie/httpie/issues/1029
