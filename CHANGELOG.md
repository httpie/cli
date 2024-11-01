# Change Log

This document records all notable changes to [HTTPie](https://httpie.io).
This project adheres to [Semantic Versioning](https://semver.org/).

## [3.2.4](https://github.com/httpie/cli/compare/3.2.3...3.2.4) (2024-11-01)

- Fix default certs loading and unpin `requests`. ([#1596](https://github.com/httpie/cli/issues/1596))

## [3.2.3](https://github.com/httpie/cli/compare/3.2.2...3.2.3) (2024-07-10)

- Fix SSL connections by pinning the `requests` version to `2.31.0`. (#1583, #1581)
- Make it possible to [unset](https://httpie.io/docs/cli/default-request-headers) the `User-Agent` and `Accept-Encoding` request headers. ([#1502](https://github.com/httpie/cli/issues/1502))

## [3.2.2](https://github.com/httpie/cli/compare/3.2.1...3.2.2) (2023-05-19)

- Fixed compatibility with urllib3 2.0.0. ([#1499](https://github.com/httpie/cli/issues/1499))

## [3.2.1](https://github.com/httpie/cli/compare/3.1.0...3.2.1) (2022-05-06)

- Improved support for determining auto-streaming when the `Content-Type` header includes encoding information. ([#1383](https://github.com/httpie/cli/pull/1383))
- Fixed the display of the crash happening in the secondary process for update checks. ([#1388](https://github.com/httpie/cli/issues/1388))

## [3.2.0](https://github.com/httpie/cli/compare/3.1.0...3.2.0) (2022-05-05)

- Added a warning for notifying the user about the new updates. ([#1336](https://github.com/httpie/cli/pull/1336))
- Added support for single binary executables. ([#1330](https://github.com/httpie/cli/pull/1330))
- Added support for man pages (and auto generation of them from the parser declaration). ([#1317](https://github.com/httpie/cli/pull/1317))
- Added `http --manual` for man pages & regular manual with pager. ([#1343](https://github.com/httpie/cli/pull/1343))
- Added support for session persistence of repeated headers with the same name. ([#1335](https://github.com/httpie/cli/pull/1335))
- Added support for sending `Secure` cookies to the `localhost` (and `.local` suffixed domains). ([#1308](https://github.com/httpie/cli/issues/1308))
- Improved UI for the progress bars. ([#1324](https://github.com/httpie/cli/pull/1324))
- Fixed redundant creation of `Content-Length` header on `OPTIONS` requests. ([#1310](https://github.com/httpie/cli/issues/1310))
- Fixed blocking of warning thread on some use cases. ([#1349](https://github.com/httpie/cli/issues/1349))
- Changed `httpie plugins` to the new `httpie cli` namespace as `httpie cli plugins` (`httpie plugins` continues to work as a hidden alias). ([#1320](https://github.com/httpie/cli/issues/1320))
- Soft deprecated the `--history-print`. ([#1380](https://github.com/httpie/cli/pull/1380))

## [3.1.0](https://github.com/httpie/cli/compare/3.0.2...3.1.0) (2022-03-08)

- **SECURITY** Fixed the [vulnerability](https://github.com/httpie/cli/security/advisories/GHSA-9w4w-cpc8-h2fq) that caused exposure of cookies on redirects to third party hosts. ([#1312](https://github.com/httpie/cli/pull/1312))
- Fixed escaping of integer indexes with multiple backslashes in the nested JSON builder. ([#1285](https://github.com/httpie/cli/issues/1285))
- Fixed displaying of status code without a status message on non-`auto` themes. ([#1300](https://github.com/httpie/cli/issues/1300))
- Fixed redundant issuance of stdin detection warnings on some rare cases due to underlying implementation. ([#1303](https://github.com/httpie/cli/pull/1303))
- Fixed double `--quiet` so that it will now suppress all python level warnings. ([#1271](https://github.com/httpie/cli/issues/1271))
- Added support for specifying certificate private key passphrases through `--cert-key-pass` and prompts. ([#946](https://github.com/httpie/cli/issues/946))
- Added `httpie cli export-args` command for exposing the parser specification for the `http`/`https` commands. ([#1293](https://github.com/httpie/cli/pull/1293))
- Improved regulation of top-level arrays. ([#1292](https://github.com/httpie/cli/commit/225dccb2186f14f871695b6c4e0bfbcdb2e3aa28))
- Improved UI layout for standalone invocations. ([#1296](https://github.com/httpie/cli/pull/1296))

## [3.0.2](https://github.com/httpie/cli/compare/3.0.1...3.0.2) (2022-01-24)

[What’s new in HTTPie for Terminal 3.0 →](https://httpie.io/blog/httpie-3.0.0)

- Fixed usage of `httpie` when there is a presence of a config with `default_options`. ([#1280](https://github.com/httpie/cli/pull/1280))

## [3.0.1](https://github.com/httpie/cli/compare/3.0.0...3.0.1) (2022-01-23)

[What’s new in HTTPie for Terminal 3.0 →](https://httpie.io/blog/httpie-3.0.0)

- Changed the value shown as time elapsed from time-to-read-headers to total exchange time. ([#1277](https://github.com/httpie/cli/issues/1277))

## [3.0.0](https://github.com/httpie/cli/compare/2.6.0...3.0.0) (2022-01-21)

[What’s new in HTTPie for Terminal 3.0 →](https://httpie.io/blog/httpie-3.0.0)

- Dropped support for Python 3.6. ([#1177](https://github.com/httpie/cli/issues/1177))
- Improved startup time by 40%. ([#1211](https://github.com/httpie/cli/pull/1211))
- Added support for nested JSON syntax. ([#1169](https://github.com/httpie/cli/issues/1169))
- Added `httpie plugins` interface for plugin management. ([#566](https://github.com/httpie/cli/issues/566))
- Added support for Bearer authentication via `--auth-type=bearer` ([#1215](https://github.com/httpie/cli/issues/1215)).
- Added support for quick conversions of pasted URLs into HTTPie calls by adding a space after the protocol name (`$ https ://pie.dev` → `https://pie.dev`). ([#1195](https://github.com/httpie/cli/issues/1195))
- Added support for _sending_ multiple HTTP header lines with the same name. ([#130](https://github.com/httpie/cli/issues/130))
- Added support for _receiving_ multiple HTTP headers lines with the same name. ([#1207](https://github.com/httpie/cli/issues/1207))
- Added support for basic JSON types on `--form`/`--multipart` when using JSON only operators (`:=`/`:=@`). ([#1212](https://github.com/httpie/cli/issues/1212))
- Added support for automatically enabling `--stream` when `Content-Type` is `text/event-stream`. ([#376](https://github.com/httpie/cli/issues/376))
- Added support for displaying the total elapsed time through `--meta`/`-vv` or `--print=m`. ([#243](https://github.com/httpie/cli/issues/243))
- Added new `pie-dark`/`pie-light` (and `pie`) styles that match with [HTTPie for Web and Desktop](https://httpie.io/product). ([#1237](https://github.com/httpie/cli/issues/1237))
- Added support for better error handling on DNS failures. ([#1248](https://github.com/httpie/cli/issues/1248))
- Added support for storing prompted passwords in the local sessions. ([#1098](https://github.com/httpie/cli/issues/1098))
- Added warnings about the `--ignore-stdin`, when there is no incoming data from stdin. ([#1255](https://github.com/httpie/cli/issues/1255))
- Fixed crashing due to broken plugins. ([#1204](https://github.com/httpie/cli/issues/1204))
- Fixed auto addition of XML declaration to every formatted XML response. ([#1156](https://github.com/httpie/cli/issues/1156))
- Fixed highlighting when `Content-Type` specifies `charset`. ([#1242](https://github.com/httpie/cli/issues/1242))
- Fixed an unexpected crash when `--raw` is used with `--chunked`. ([#1253](https://github.com/httpie/cli/issues/1253))
- Changed the default Windows theme from `fruity` to `auto`. ([#1266](https://github.com/httpie/cli/issues/1266))

## [2.6.0](https://github.com/httpie/cli/compare/2.5.0...2.6.0) (2021-10-14)

[What’s new in HTTPie for Terminal 2.6.0 →](https://httpie.io/blog/httpie-2.6.0)

- Added support for formatting & coloring of JSON bodies preceded by non-JSON data (e.g., an XXSI prefix). ([#1130](https://github.com/httpie/cli/issues/1130))
- Added charset auto-detection when `Content-Type` doesn’t include it. ([#1110](https://github.com/httpie/cli/issues/1110), [#1168](https://github.com/httpie/cli/issues/1168))
- Added `--response-charset` to allow overriding the response encoding for terminal display purposes. ([#1168](https://github.com/httpie/cli/issues/1168))
- Added `--response-mime` to allow overriding the response mime type for coloring and formatting for the terminal. ([#1168](https://github.com/httpie/cli/issues/1168))
- Added the ability to silence warnings through using `-q` or `--quiet` twice (e.g. `-qq`) ([#1175](https://github.com/httpie/cli/issues/1175))
- Added installed plugin list to `--debug` output. ([#1165](https://github.com/httpie/cli/issues/1165))
- Fixed duplicate keys preservation in JSON data. ([#1163](https://github.com/httpie/cli/issues/1163))

## [2.5.0](https://github.com/httpie/cli/compare/2.4.0...2.5.0) (2021-09-06)

[What’s new in HTTPie for Terminal 2.5.0 →](https://httpie.io/blog/httpie-2.5.0)

- Added `--raw` to allow specifying the raw request body without extra processing as
  an alternative to `stdin`. ([#534](https://github.com/httpie/cli/issues/534))
- Added support for XML formatting. ([#1129](https://github.com/httpie/cli/issues/1129))
- Added internal support for file-like object responses to improve adapter plugin support. ([#1094](https://github.com/httpie/cli/issues/1094))
- Fixed `--continue --download` with a single byte to be downloaded left. ([#1032](https://github.com/httpie/cli/issues/1032))
- Fixed `--verbose` HTTP 307 redirects with streamed request body. ([#1088](https://github.com/httpie/cli/issues/1088))
- Fixed handling of session files with `Cookie:` followed by other headers. ([#1126](https://github.com/httpie/cli/issues/1126))

## [2.4.0](https://github.com/httpie/cli/compare/2.3.0...2.4.0) (2021-02-06)

- Added support for `--session` cookie expiration based on `Set-Cookie: max-age=<n>`. ([#1029](https://github.com/httpie/cli/issues/1029))
- Show a `--check-status` warning with `--quiet` as well, not only when the output is redirected. ([#1026](https://github.com/httpie/cli/issues/1026))
- Fixed upload with `--session` ([#1020](https://github.com/httpie/cli/issues/1020)).
- Fixed a missing blank line between request and response ([#1006](https://github.com/httpie/cli/issues/1006)).

## [2.3.0](https://github.com/httpie/cli/compare/2.2.0...2.3.0) (2020-10-25)

- Added support for streamed uploads ([#201](https://github.com/httpie/cli/issues/201)).
- Added support for multipart upload streaming ([#684](https://github.com/httpie/cli/issues/684)).
- Added support for body-from-file upload streaming (`http pie.dev/post @file`).
- Added `--chunked` to enable chunked transfer encoding ([#753](https://github.com/httpie/cli/issues/753)).
- Added `--multipart` to allow `multipart/form-data` encoding for non-file `--form` requests as well.
- Added support for preserving field order in multipart requests ([#903](https://github.com/httpie/cli/issues/903)).
- Added `--boundary` to allow a custom boundary string for `multipart/form-data` requests.
- Added support for combining cookies specified on the CLI and in a session file ([#932](https://github.com/httpie/cli/issues/932)).
- Added out of the box SOCKS support with no extra installation ([#904](https://github.com/httpie/cli/issues/904)).
- Added `--quiet, -q` flag to enforce silent behaviour.
- Fixed the handling of invalid `expires` dates in `Set-Cookie` headers ([#963](https://github.com/httpie/cli/issues/963)).
- Removed Tox testing entirely ([#943](https://github.com/httpie/cli/issues/943)).

## [2.2.0](https://github.com/httpie/cli/compare/2.1.0...2.2.0) (2020-06-18)

- Added support for custom content types for uploaded files ([#668](https://github.com/httpie/cli/issues/668)).
- Added support for `$XDG_CONFIG_HOME` ([#920](https://github.com/httpie/cli/issues/920)).
- Added support for `Set-Cookie`-triggered cookie expiration ([#853](https://github.com/httpie/cli/issues/853)).
- Added `--format-options` to allow disabling sorting, etc. ([#128](https://github.com/httpie/cli/issues/128))
- Added `--sorted` and `--unsorted` shortcuts for (un)setting all sorting-related `--format-options`. ([#128](https://github.com/httpie/cli/issues/128))
- Added `--ciphers` to allow configuring OpenSSL ciphers ([#870](https://github.com/httpie/cli/issues/870)).
- Added `netrc` support for auth plugins. Enabled for `--auth-type=basic`
  and `digest`, 3rd parties may opt in ([#718](https://github.com/httpie/cli/issues/718), [#719](https://github.com/httpie/cli/issues/719), [#852](https://github.com/httpie/cli/issues/852), [#934](https://github.com/httpie/cli/issues/934)).
- Fixed built-in plugins-related circular imports ([#925](https://github.com/httpie/cli/issues/925)).

## [2.1.0](https://github.com/httpie/cli/compare/2.0.0...2.1.0) (2020-04-18)

- Added `--path-as-is` to bypass dot segment (`/../` or `/./`)
  URL squashing ([#895](https://github.com/httpie/cli/issues/895)).
- Changed the default `Accept` header value for JSON requests from
  `application/json, */*` to `application/json, */*;q=0.5`
  to clearly indicate preference ([#488](https://github.com/httpie/cli/issues/488)).
- Fixed `--form` file upload mixed with redirected `stdin` error handling
  ([#840](https://github.com/httpie/cli/issues/840)).

## [2.0.0](https://github.com/httpie/cli/compare/1.0.3...2.0.0) (2020-01-12)

- Removed Python 2.7 support ([EOL Jan 2020](https://www.python.org/doc/sunset-python-2/).
- Added `--offline` to allow building an HTTP request and printing it but not
  actually sending it over the network.
- Replaced the old collect-all-then-process handling of HTTP communication
  with one-by-one processing of each HTTP request or response as they become
  available. This means that you can see headers immediately,
  see what is being sent even if the request fails, etc.
- Removed automatic config file creation to avoid concurrency issues.
- Removed the default 30-second connection `--timeout` limit.
- Removed Python’s default limit of 100 response headers.
- Added `--max-headers` to allow setting the max header limit.
- Added `--compress` to allow request body compression.
- Added `--ignore-netrc` to allow bypassing credentials from `.netrc`.
- Added `https` alias command with `https://` as the default scheme.
- Added `$ALL_PROXY` documentation.
- Added type annotations throughout the codebase.
- Added `tests/` to the PyPi package for the convenience of
  downstream package maintainers.
- Fixed an error when `stdin` was a closed fd.
- Improved `--debug` output formatting.

## [1.0.3](https://github.com/httpie/cli/compare/1.0.2...1.0.3) (2019-08-26)

- Fixed CVE-2019-10751 — the way the output filename is generated for
  `--download` requests without `--output` resulting in a redirect has
  been changed to only consider the initial URL as the base for the generated
  filename, and not the final one. This fixes a potential security issue under
  the following scenario:

  1. A `--download` request with no explicit `--output` is made (e.g.,
     `$ http -d example.org/file.txt`), instructing httpie to
     [generate the output filename](https://httpie.org/doc#downloaded-filename)
     from the `Content-Disposition` response header, or from the URL if the header
     is not provided.
  2. The server handling the request has been modified by an attacker and
     instead of the expected response the URL returns a redirect to another
     URL, e.g., `attacker.example.org/.bash_profile`, whose response does
     not provide  a `Content-Disposition` header (i.e., the base for the
     generated filename becomes `.bash_profile` instead of `file.txt`).
  3. Your current directory doesn’t already contain `.bash_profile`
     (i.e., no unique suffix is added to the generated filename).
  4. You don’t notice the potentially unexpected output filename
     as reported by httpie in the console output
     (e.g., `Downloading 100.00 B to ".bash_profile"`).

  Reported by Raul Onitza and Giulio Comi.

## [1.0.2](https://github.com/httpie/cli/compare/1.0.1...1.0.2) (2018-11-14)

- Fixed tests for installation with pyOpenSSL.

## [1.0.1](https://github.com/httpie/cli/compare/1.0.0...1.0.1) (2018-11-14)

- Removed external URL calls from tests.

## [1.0.0](https://github.com/httpie/cli/compare/0.9.9...1.0.0) (2018-11-02)

- Added `--style=auto` which follows the terminal ANSI color styles.
- Added support for selecting TLS 1.3 via `--ssl=tls1.3`
  (available once implemented in upstream libraries).
- Added `true`/`false` as valid values for `--verify`
  (in addition to `yes`/`no`) and the boolean value is case-insensitive.
- Changed the default `--style` from `solarized` to `auto` (on Windows it stays `fruity`).
- Fixed default headers being incorrectly case-sensitive.
- Removed Python 2.6 support.

## [0.9.9](https://github.com/httpie/cli/compare/0.9.8...0.9.9) (2016-12-08)

- Fixed README.

## [0.9.8](https://github.com/httpie/cli/compare/0.9.6...0.9.8) (2016-12-08)

- Extended auth plugin API.
- Added exit status code `7` for plugin errors.
- Added support for `curses`-less Python installations.
- Fixed `REQUEST_ITEM` arg incorrectly being reported as required.
- Improved `CTRL-C` interrupt handling.
- Added the standard exit status code `130` for keyboard interrupts.

## [0.9.6](https://github.com/httpie/cli/compare/0.9.4...0.9.6) (2016-08-13)

- Added Python 3 as a dependency for Homebrew installations
  to ensure some of the newer HTTP features work out of the box
  for macOS users (starting with HTTPie 0.9.4.).
- Added the ability to unset a request header with `Header:`, and send an
  empty value with `Header;`.
- Added `--default-scheme <URL_SCHEME>` to enable things like
  `$ alias https='http --default-scheme=https`.
- Added `-I` as a shortcut for `--ignore-stdin`.
- Added fish shell completion (located in `extras/httpie-completion.fish`
  in the GitHub repo).
- Updated `requests` to 2.10.0 so that SOCKS support can be added via
  `pip install requests[socks]`.
- Changed the default JSON `Accept` header from `application/json`
  to `application/json, */*`.
- Changed the pre-processing of request HTTP headers so that any leading
  and trailing whitespace is removed.

## [0.9.4](https://github.com/httpie/cli/compare/0.9.3...0.9.4) (2016-07-01)

- Added `Content-Type` of files uploaded in `multipart/form-data` requests
- Added `--ssl=<PROTOCOL>` to specify the desired SSL/TLS protocol version
  to use for HTTPS requests.
- Added JSON detection with `--json, -j` to work around incorrect
  `Content-Type`
- Added `--all` to show intermediate responses such as redirects (with `--follow`)
- Added `--history-print, -P WHAT` to specify formatting of intermediate responses
- Added `--max-redirects=N` (default 30)
- Added `-A` as short name for `--auth-type`
- Added `-F` as short name for `--follow`
- Removed the `implicit_content_type` config option
  (use `"default_options": ["--form"]` instead)
- Redirected `stdout` doesn't trigger an error anymore when `--output FILE`
  is set
- Changed the default `--style` back to `solarized` for better support
  of light and dark terminals
- Improved `--debug` output
- Fixed `--session` when used with `--download`
- Fixed `--download` to trim too long filenames before saving the file
- Fixed the handling of `Content-Type` with multiple `+subtype` parts
- Removed the XML formatter as the implementation suffered from multiple issues

## [0.9.3](https://github.com/httpie/cli/compare/0.9.2...0.9.3) (2016-01-01)

- Changed the default color `--style` from `solarized` to `monokai`
- Added basic Bash autocomplete support (need to be installed manually)
- Added request details to connection error messages
- Fixed `'requests.packages.urllib3' has no attribute 'disable_warnings'`
  errors that occurred in some installations
- Fixed colors and formatting on Windows
- Fixed `--auth` prompt on Windows

## [0.9.2](https://github.com/httpie/cli/compare/0.9.1...0.9.2) (2015-02-24)

- Fixed compatibility with Requests 2.5.1
- Changed the default JSON `Content-Type` to `application/json` as UTF-8
  is the default JSON encoding

## [0.9.1](https://github.com/httpie/cli/compare/0.9.0...0.9.1) (2015-02-07)

- Added support for Requests transport adapter plugins
  (see [httpie-unixsocket](https://github.com/httpie/httpie-unixsocket)
  and [httpie-http2](https://github.com/httpie/httpie-http2))

## [0.9.0](https://github.com/httpie/cli/compare/0.8.0...0.9.0) (2015-01-31)

- Added `--cert` and `--cert-key` parameters to specify a client side
  certificate and private key for SSL
- Improved unicode support
- Improved terminal color depth detection via `curses`
- To make it easier to deal with Windows paths in request items, `\`
  now only escapes special characters (the ones that are used as key-value
  separators by HTTPie)
- Switched from `unittest` to `pytest`
- Added Python `wheel` support
- Various test suite improvements
- Added `CONTRIBUTING`
- Fixed `User-Agent` overwriting when used within a session
- Fixed handling of empty passwords in URL credentials
- Fixed multiple file uploads with the same form field name
- Fixed `--output=/dev/null` on Linux
- Miscellaneous bugfixes

## [0.8.0](https://github.com/httpie/cli/compare/0.7.1...0.8.0) (2014-01-25)

- Added `field=@file.txt` and `field:=@file.json` for embedding
  the contents of text and JSON files into request data
- Added curl-style shorthand for localhost
- Fixed request `Host` header value output so that it doesn't contain
  credentials, if included in the URL

## [0.7.1](https://github.com/httpie/cli/compare/0.6.0...0.7.1) (2013-09-24)

- Added `--ignore-stdin`
- Added support for auth plugins
- Improved `--help` output
- Improved `Content-Disposition` parsing for `--download` mode
- Update to Requests 2.0.0

## [0.6.0](https://github.com/httpie/cli/compare/0.5.1...0.6.0) (2013-06-03)

- XML data is now formatted
- `--session` and `--session-read-only` now also accept paths to
  session files (eg. `http --session=/tmp/session.json example.org`)

## [0.5.1](https://github.com/httpie/cli/compare/0.5.0...0.5.1) (2013-05-13)

- `Content-*` and `If-*` request headers are not stored in sessions
  anymore as they are request-specific

## [0.5.0](https://github.com/httpie/cli/compare/0.4.1...0.5.0) (2013-04-27)

- Added a download mode via `--download`
- Fixes miscellaneous bugs

## [0.4.1](https://github.com/httpie/cli/compare/0.4.0...0.4.1) (2013-02-26)

- Fixed `setup.py`

## [0.4.0](https://github.com/httpie/cli/compare/0.3.0...0.4.0) (2013-02-22)

- Added Python 3.3 compatibility
- Added Requests >= v1.0.4 compatibility
- Added support for credentials in URL
- Added `--no-option` for every `--option` to be config-friendly
- Mutually exclusive arguments can be specified multiple times. The
  last value is used

## [0.3.0](https://github.com/httpie/cli/compare/0.2.7...0.3.0) (2012-09-21)

- Allow output redirection on Windows
- Added configuration file
- Added persistent session support
- Renamed `--allow-redirects` to `--follow`
- Improved the usability of `http --help`
- Fixed installation on Windows with Python 3
- Fixed colorized output on Windows with Python 3
- CRLF HTTP header field separation in the output
- Added exit status code `2` for timed-out requests
- Added the option to separate colorizing and formatting
  (`--pretty=all`, `--pretty=colors` and `--pretty=format`)
  `--ugly` has bee removed in favor of `--pretty=none`

## [0.2.7](https://github.com/httpie/cli/compare/0.2.5...0.2.7) (2012-08-07)

- Added compatibility with Requests 0.13.6
- Added streamed terminal output. `--stream, -S` can be used to enable
  streaming also with `--pretty` and to ensure a more frequent output
  flushing
- Added support for efficient large file downloads
- Sort headers by name (unless `--pretty=none`)
- Response body is fetched only when needed (e.g., not with `--headers`)
- Improved content type matching
- Updated Solarized color scheme
- Windows: Added `--output FILE` to store output into a file
  (piping results in corrupted data on Windows)
- Proper handling of binary requests and responses
- Fixed printing of `multipart/form-data` requests
- Renamed `--traceback` to `--debug`

## [0.2.6](https://github.com/httpie/cli/compare/0.2.5...0.2.6) (2012-07-26)

- The short option for `--headers` is now `-h` (`-t` has been
  removed, for usage use `--help`)
- Form data and URL parameters can have multiple fields with the same name
  (e.g.,`http -f url a=1 a=2`)
- Added `--check-status` to exit with an error on HTTP 3xx, 4xx and
  5xx (3, 4, and 5, respectively)
- If the output is piped to another program or redirected to a file,
  the default behaviour is to only print the response body
  (It can still be overwritten via the `--print` flag.)
- Improved highlighting of HTTP headers
- Added query string parameters (`param==value`)
- Added support for terminal colors under Windows

## [0.2.5](https://github.com/httpie/cli/compare/0.2.2...0.2.5) (2012-07-17)

- Unicode characters in prettified JSON now don't get escaped for
  improved readability
- --auth now prompts for a password if only a username provided
- Added support for request payloads from a file path with automatic
  `Content-Type` (`http URL @/path`)
- Fixed missing query string when displaying the request headers via
  `--verbose`
- Fixed Content-Type for requests with no data

## [0.2.2](https://github.com/httpie/cli/compare/0.2.1...0.2.2) (2012-06-24)

- The `METHOD` positional argument can now be omitted (defaults to
  `GET`, or to `POST` with data)
- Fixed --verbose --form
- Added support for Tox

## [0.2.1](https://github.com/httpie/cli/compare/0.2.0...0.2.1) (2012-06-13)

- Added compatibility with `requests-0.12.1`
- Dropped custom JSON and HTTP lexers in favor of the ones newly included
  in `pygments-1.5`

## [0.2.0](https://github.com/httpie/cli/compare/0.1.6...0.2.0) (2012-04-25)

- Added Python 3 support
- Added the ability to print the HTTP request as well as the response
  (see `--print` and `--verbose`)
- Added support for Digest authentication
- Added file upload support
  (`http -f POST file_field_name@/path/to/file`)
- Improved syntax highlighting for JSON
- Added support for field name escaping
- Many bug fixes

## [0.1.6](https://github.com/httpie/cli/compare/0.1.5...0.1.6) (2012-03-04)

- Fixed `setup.py`

## [0.1.5](https://github.com/httpie/cli/compare/0.1.4...0.1.5) (2012-03-04)

- Many improvements and bug fixes

## [0.1.4](https://github.com/httpie/cli/compare/b966efa...0.1.4) (2012-02-28)

- Many improvements and bug fixes

## [0.1.0](https://github.com/httpie/cli/commit/b966efa) (2012-02-25)

- Initial public release
