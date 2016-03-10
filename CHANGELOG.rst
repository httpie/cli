==========
Change Log
==========

This document records all notable changes to `HTTPie <http://httpie.org>`_.
This project adheres to `Semantic Versioning <http://semver.org/>`_.


`1.0.0-dev`_ (Unreleased)
-------------------------

* Added ``Content-Type`` of files uploaded in ``multipart/form-data`` requests
* Added ``--ssl=<PROTOCOL>`` to specify the desired SSL/TLS protocol version
  to use for HTTPS requests.
* Added JSON detection with ``--json, -j`` to work around incorrect
  ``Content-Type``
* Added ``--all`` to show intermediate responses such as redirects (with ``--follow``)
* Added ``--print-others, -P WHAT`` to specify formatting of intermediate responses
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
* Fixed handling of ``Content-Type`` with multiple ``+subtype`` parts


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
  (see `httpie-unixsocket <https://github.com/msabramo/httpie-unixsocket>`_
  and `httpie-http2 <https://github.com/jkbrzt/httpie-http2>`_)


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


`0.1`_ (2012-02-25)
-------------------

* Initial public release


.. _`0.1`: https://github.com/jkbrzt/httpie/commit/b966efa
.. _0.1.4: https://github.com/jkbrzt/httpie/compare/b966efa...0.1.4
.. _0.1.5: https://github.com/jkbrzt/httpie/compare/0.1.4...0.1.5
.. _0.1.6: https://github.com/jkbrzt/httpie/compare/0.1.5...0.1.6
.. _0.2.0: https://github.com/jkbrzt/httpie/compare/0.1.6...0.2.0
.. _0.2.1: https://github.com/jkbrzt/httpie/compare/0.2.0...0.2.1
.. _0.2.2: https://github.com/jkbrzt/httpie/compare/0.2.1...0.2.2
.. _0.2.5: https://github.com/jkbrzt/httpie/compare/0.2.2...0.2.5
.. _0.2.6: https://github.com/jkbrzt/httpie/compare/0.2.5...0.2.6
.. _0.2.7: https://github.com/jkbrzt/httpie/compare/0.2.5...0.2.7
.. _0.3.0: https://github.com/jkbrzt/httpie/compare/0.2.7...0.3.0
.. _0.4.0: https://github.com/jkbrzt/httpie/compare/0.3.0...0.4.0
.. _0.4.1: https://github.com/jkbrzt/httpie/compare/0.4.0...0.4.1
.. _0.5.0: https://github.com/jkbrzt/httpie/compare/0.4.1...0.5.0
.. _0.5.1: https://github.com/jkbrzt/httpie/compare/0.5.0...0.5.1
.. _0.6.0: https://github.com/jkbrzt/httpie/compare/0.5.1...0.6.0
.. _0.7.1: https://github.com/jkbrzt/httpie/compare/0.6.0...0.7.1
.. _0.8.0: https://github.com/jkbrzt/httpie/compare/0.7.1...0.8.0
.. _0.9.0: https://github.com/jkbrzt/httpie/compare/0.8.0...0.9.0
.. _0.9.1: https://github.com/jkbrzt/httpie/compare/0.9.0...0.9.1
.. _0.9.2: https://github.com/jkbrzt/httpie/compare/0.9.1...0.9.2
.. _0.9.3: https://github.com/jkbrzt/httpie/compare/0.9.2...0.9.3
.. _1.0.0-dev: https://github.com/jkbrzt/httpie/compare/0.9.3...master
