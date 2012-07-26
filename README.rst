=======================
HTTPie: cURL for humans
=======================

**HTTPie is a CLI HTTP utility** built out of frustration with existing tools.
Its goal is to make CLI interaction with HTTP-based services as
**human-friendly** as possible. HTTPie provides an ``http`` command that allows
for issuing **arbitrary HTTP** requests using a **simple and natural syntax**,
and displays **colorized responses**:

.. image:: https://github.com/jkbr/httpie/raw/master/httpie.png
    :alt: HTTPie compared to cURL

HTTPie supports Python 2.6+ (including Python 3.x and PyPy) and has been tested
under Mac OS X, Linux and Windows. It also has a
comprehensive `suite of tests`_ with `continuous integration`_.

Under the hood, the excellent `Requests`_ and `Pygments`_ Python libraries
are used.


Installation
============

The latest **stable version** of HTTPie can always be installed or updated
to via `pip`_ (prefered)
or ``easy_install``::

    pip install -U httpie
    # easy_install pip

Or, you can install the **development version** directly from GitHub:

.. image:: https://secure.travis-ci.org/jkbr/httpie.png
    :target: http://travis-ci.org/jkbr/httpie
    :alt: Build Status of the master branch

::

    pip install -U https://github.com/jkbr/httpie/tarball/master

There are also packages available for `Ubuntu`_, `Debian`_ and possibly other
distributions as well.


Usage
=====

Hello world::

    http httpie.org

Synopsis::

    http [flags] [METHOD] URL [items]

There are five different types of key/value pair ``items`` available:

+-----------------------+-----------------------------------------------------+
| **Headers**           | Arbitrary HTTP headers. The ``:`` character is      |
| ``Name:Value``        | used to separate a header's name from its value,    |
|                       | e.g., ``X-API-Token:123``.                          |
+-----------------------+-----------------------------------------------------+
| **Simple data         | Included in the request body and depending on the   |
| fields**              | ``Content-Type`` they are automatically serialized  |
| ``field=value``       | as a JSON ``Object`` (default) or                   |
|                       | ``application/x-www-form-urlencoded``               |
|                       | (``--form``/  ``-f``). Data items use ``=``         |
|                       | as the separator, e.g., ``hello=world``.            |
+-----------------------+-----------------------------------------------------+
| **Raw JSON fields**   | Useful when the ``Content-Type`` is JSON and one or |
| ``field:=json``       | more fields need to be a ``Boolean``, ``Number``,   |
|                       | nested ``Object``, or an ``Array``. It's because    |
|                       | simple data items are always serialized as a        |
|                       | ``String``. E.g., ``pies:=[1,2,3]``, or             |
|                       | ``'meals:=["ham","spam"]'`` (note the quotes).      |
|                       | It may be more convenient to pass the whole JSON    |
|                       | body via ``stdin`` when it's more complex           |
|                       | (see examples bellow).                              |
+-----------------------+-----------------------------------------------------+
| **File fields**       | Only available with ``-f`` / ``--form``. Use ``@``  |
| ``field@/dir/file``   | as the separator, e.g.,                             |
|                       | ``screenshot@~/Pictures/img.png``.                  |
|                       | The presence of a file field results                |
|                       | into a ``multipart/form-data`` request.             |
+-----------------------+-----------------------------------------------------+
| **Query string        | Appends the given name/value pair as a query        |
| parameters**          | string parameter to the URL.                        |
| ``name==value``       | The ``==`` separator is used                        |
+-----------------------+-----------------------------------------------------+


All ``items`` come after the URL, and, unlike ``flags``, they become part of
the actual request being is sent. Their types are distinguished by the
separator used.


Examples
--------
::

    http PATCH api.example.com/person/1 X-API-Token:123 name=John email=john@example.org age:=29

The following request is issued::

    PATCH /person/1 HTTP/1.1
    User-Agent: HTTPie/0.1
    X-API-Token: 123
    Content-Type: application/json; charset=utf-8

    {"name": "John", "email": "john@example.org", "age": 29}

It can easily be changed to a **form** request using the ``-f``
(or ``--form``) flag, which produces::

    PATCH /person/1 HTTP/1.1
    User-Agent: HTTPie/0.1
    X-API-Token: 123
    Content-Type: application/x-www-form-urlencoded; charset=utf-8

    age=29&name=John&email=john%40example.org

It is also possible to send ``multipart/form-data`` requests, i.e., to
simulate a **file upload form** submission. It is done using the
``--form`` / ``-f`` flag and passing one or more file fields::

    http -f POST example.com/jobs name=John cv@~/Documents/cv.pdf

The above will send the same request as if the following HTML form were
submitted::

    <form enctype="multipart/form-data" method="post" action="http://example.com/jobs">
        <input type="text" name="name" />
        <input type="file" name="cv" />
    </form>

**Query string parameters** can be added to any request without having to
escape the ``&`` characters. The following request will contain
``?search=donuts&in=fridge`` as the query string part of the URL::

    http GET example.com search==donuts in==fridge

The whole request body can also be passed in **via stdin,** in which
case it will be used with no further processing::

    echo '{"name": "John"}' | http PATCH example.com/person/1 X-API-Token:123
    # Or:
    http POST example.com/person/1 X-API-Token:123 < person.json

That can be used for **piping services together**. The following example
``GET``-s JSON data from the Github API and ``POST``-s it to httpbin.org::

    http GET https://api.github.com/repos/jkbr/httpie | http POST httpbin.org/post

The above can be further simplified by omitting ``GET`` and ``POST`` because
they are both default here as the first command has no request data whereas
the second one has via ``stdin``::

    http https://api.github.com/repos/jkbr/httpie | http httpbin.org/post

Note that when the **output is redirected** (like the examples above), HTTPie
applies a different set of defaults than for a console output. Namely, colors
aren't used (unless ``--pretty`` is set) and only the response body
is printed (unless ``--print`` options specified).

An alternative to ``stdin`` is to pass a filename whose content will be used
as the request body. It has the advantage that the ``Content-Type`` header
will automatically be set to the appropriate value based on the filename
extension. Thus, the following will request will send the verbatim contents
of the file with ``Content-Type: application/xml``::

    http PUT httpbin.org/put @/data/file.xml

When using HTTPie from **shell scripts** it can be useful to use the
``--check-status`` flag. It instructs HTTPie to exit with an error if the
HTTP status is one of ``3xx``, ``4xx``, or ``5xx``. The exit status will
be ``3`` (unless ``--allow-redirects`` is set), ``4``, or ``5``,
respectively::

    #!/bin/bash

    if http --check-status HEAD example.org/health &> /dev/null; then
        echo 'OK!'
    else
        case $? in
            3) echo 'Unexpected 3xx Redirection!' ;;
            4) echo '4xx Client Error!' ;;
            5) echo '5xx Server Error!' ;;
            *) echo 'Other Error!' ;;
        esac
    fi


Flags
-----

``$ http --help``::

    usage: http [--help] [--version] [--json | --form] [--traceback]
                [--pretty | --ugly]
                [--print OUTPUT_OPTIONS | --verbose | --headers | --body]
                [--style STYLE] [--check-status] [--auth AUTH]
                [--auth-type {basic,digest}] [--verify VERIFY] [--proxy PROXY]
                [--allow-redirects] [--timeout TIMEOUT]
                [METHOD] URL [ITEM [ITEM ...]]

    HTTPie - cURL for humans. <http://httpie.org>

    positional arguments:
      METHOD                The HTTP method to be used for the request (GET, POST,
                            PUT, DELETE, PATCH, ...). If this argument is omitted,
                            then HTTPie will guess the HTTP method. If there is
                            some data to be sent, then it will be POST, otherwise
                            GET.
      URL                   The protocol defaults to http:// if the URL does not
                            include one.
      ITEM                  A key-value pair whose type is defined by the
                            separator used. It can be an HTTP header
                            (header:value), a data field to be used in the request
                            body (field_name=value), a raw JSON data field
                            (field_name:=value), a query parameter (name==value),
                            or a file field (field_name@/path/to/file). You can
                            use a backslash to escape a colliding separator in the
                            field name.

    optional arguments:
      --help                show this help message and exit
      --version             show program's version number and exit
      --json, -j            (default) Data items from the command line are
                            serialized as a JSON object. The Content-Type and
                            Accept headers are set to application/json (if not
                            specified).
      --form, -f            Data items from the command line are serialized as
                            form fields. The Content-Type is set to application/x
                            -www-form-urlencoded (if not specified). The presence
                            of any file fields results into a multipart/form-data
                            request.
      --traceback           Print exception traceback should one occur.
      --pretty              If stdout is a terminal, the response is prettified by
                            default (colorized and indented if it is JSON). This
                            flag ensures prettifying even when stdout is
                            redirected.
      --ugly, -u            Do not prettify the response.
      --print OUTPUT_OPTIONS, -p OUTPUT_OPTIONS
                            String specifying what the output should contain: "H"
                            stands for the request headers, and "B" for the
                            request body. "h" stands for the response headers and
                            "b" for response the body. The default behaviour is
                            "hb" (i.e., the response headers and body is printed),
                            if standard output is not redirected. If the output is
                            piped to another program or to a file, then only the
                            body is printed by default.
      --verbose, -v         Print the whole request as well as the response.
                            Shortcut for --print=HBhb.
      --headers, -h         Print only the response headers. Shortcut for
                            --print=h.
      --body, -b            Print only the response body. Shortcut for --print=b.
      --style STYLE, -s STYLE
                            Output coloring style, one of autumn, borland, bw,
                            colorful, default, emacs, friendly, fruity, manni,
                            monokai, murphy, native, pastie, perldoc, rrt,
                            solarized, tango, trac, vim, vs. Defaults to
                            solarized. For this option to work properly, please
                            make sure that the $TERM environment variable is set
                            to "xterm-256color" or similar (e.g., via `export TERM
                            =xterm-256color' in your ~/.bashrc).
      --check-status        By default, HTTPie exits with 0 when no network or
                            other fatal errors occur. This flag instructs HTTPie
                            to also check the HTTP status code and exit with an
                            error if the status indicates one. When the server
                            replies with a 4xx (Client Error) or 5xx (Server
                            Error) status code, HTTPie exits with 4 or 5
                            respectively. If the response is a 3xx (Redirect) and
                            --allow-redirects hasn't been set, then the exit
                            status is 3. Also an error message is written to
                            stderr if stdout is redirected.
      --auth AUTH, -a AUTH  username:password. If only the username is provided
                            (-a username), HTTPie will prompt for the password.
      --auth-type {basic,digest}
                            The authentication mechanism to be used. Defaults to
                            "basic".
      --verify VERIFY       Set to "no" to skip checking the host's SSL
                            certificate. You can also pass the path to a CA_BUNDLE
                            file for private certs. You can also set the
                            REQUESTS_CA_BUNDLE environment variable. Defaults to
                            "yes".
      --proxy PROXY         String mapping protocol to the URL of the proxy (e.g.
                            http:foo.bar:3128).
      --allow-redirects     Set this flag if full redirects are allowed (e.g. re-
                            POST-ing of data at new ``Location``)
      --timeout TIMEOUT     Float describes the timeout of the request (Use
                            socket.setdefaulttimeout() as fallback).


Contribute
==========

Bug reports and code and documentation patches are greatly appretiated. You can
also help by using the development version of HTTPie and reporting any bugs you
might encounter.

Before working on a new feature or a bug, please browse the `existing issues`_
to see whether it has been previously discussed.

Then fork and clone `the repository`_.

To point the ``http`` command to your local branch during development you can
install HTTPie in an editable mode::

    pip install --editable .

To run the existing suite of tests before a pull request is submitted::

    python setup.py test

`Tox`_ can also be used to conveniently run tests in all of the
`supported Python environments`_::

    # Install tox
    pip install tox

    # Run tests
    tox


Changelog
=========

* `0.2.7dev`_
* `0.2.6`_ (2012-07-26)
    * The short option for ``--headers`` is now ``-h`` (``-t`` has been
      removed, for usage use ``--help``).
    * Form data and URL parameters can have multiple fields with the same name
      (e.g.,``http -f url a=1 a=2``).
    * Added ``--check-status`` to exit with an error on HTTP 3xx, 4xx and
      5xx (3, 4, and 5, respectively).
    * If the output is piped to another program or redirected to a file,
      the default behaviour is to only print the response body.
      (It can still be overwritten via the ``--print`` flag.)
    * Improved highlighting of HTTP headers.
    * Added query string parameters (``param==value``).
    * Added support for terminal colors under Windows.
* `0.2.5`_ (2012-07-17)
    * Unicode characters in prettified JSON now don't get escaped for
      improved readability.
    * --auth now prompts for a password if only a username provided.
    * Added support for request payloads from a file path with automatic
      ``Content-Type`` (``http URL @/path``).
    * Fixed missing query string when displaying the request headers via
      ``--verbose``.
    * Fixed Content-Type for requests with no data.
* `0.2.2`_ (2012-06-24)
    * The ``METHOD`` positional argument can now be omitted (defaults to
      ``GET``, or to ``POST`` with data).
    * Fixed --verbose --form.
    * Added support for `Tox`_.
* `0.2.1`_ (2012-06-13)
    * Added compatibility with ``requests-0.12.1``.
    * Dropped custom JSON and HTTP lexers in favor of the ones newly included
      in ``pygments-1.5``.
* `0.2.0`_ (2012-04-25)
    * Added Python 3 support.
    * Added the ability to print the HTTP request as well as the response
      (see ``--print`` and ``--verbose``).
    * Added support for Digest authentication.
    * Added file upload support
      (``http -f POST file_field_name@/path/to/file``).
    * Improved syntax highlighting for JSON.
    * Added support for field name escaping.
    * Many bug fixes.
* `0.1.6`_ (2012-03-04)


Authors
=======

`Jakub Roztocil`_  (`@jkbrzt`_) created HTTPie and
`these fine people <https://github.com/jkbr/httpie/contributors>`_
have contributed.


.. _suite of tests: https://github.com/jkbr/httpie/blob/master/tests/tests.py
.. _continuous integration: http://travis-ci.org/#!/jkbr/httpie
.. _Requests: http://python-requests.org
.. _Pygments: http://pygments.org/
.. _pip: http://www.pip-installer.org/en/latest/index.html
.. _Tox: http://tox.testrun.org
.. _supported Python environments: https://github.com/jkbr/httpie/blob/master/tox.ini
.. _Ubuntu: http://packages.ubuntu.com/httpie
.. _Debian: http://packages.debian.org/httpie
.. _the repository: https://github.com/jkbr/httpie
.. _Jakub Roztocil: http://roztocil.name
.. _@jkbrzt: https://twitter.com/jkbrzt
.. _existing issues: https://github.com/jkbr/httpie/issues?state=open
.. _0.1.6: https://github.com/jkbr/httpie/compare/0.1.4...0.1.6
.. _0.2.0: https://github.com/jkbr/httpie/compare/0.1.6...0.2.0
.. _0.2.1: https://github.com/jkbr/httpie/compare/0.2.0...0.2.1
.. _0.2.2: https://github.com/jkbr/httpie/compare/0.2.1...0.2.2
.. _0.2.5: https://github.com/jkbr/httpie/compare/0.2.2...0.2.5
.. _0.2.6: https://github.com/jkbr/httpie/compare/0.2.5...0.2.6
.. _0.2.7dev: https://github.com/jkbr/httpie/compare/0.2.6...master
