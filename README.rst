HTTPie: cURL for humans
=======================

**HTTPie is a CLI HTTP utility** built out of frustration with existing tools. The goal is to make CLI interaction with HTTP-based services as human-friendly as possible.

HTTPie does so by providing an ``http`` command that allows for issuing arbitrary HTTP requests using a **simple and natural syntax** and displaying **colorized responses**:

.. image:: https://github.com/jkbr/httpie/raw/master/httpie.png
    :alt: HTTPie compared to cURL

Under the hood, HTTPie uses the excellent `Requests <http://python-requests.org>`_ and `Pygments <http://pygments.org/>`_ Python libraries. Python 2.6+ is supported (including 3.x).

Installation
------------

The latest **stable version** of HTTPie can always be installed (or updated to) via `pip <http://www.pip-installer.org/en/latest/index.html>`_::

    pip install -U httpie


Or, you can install the **development version** directly from GitHub:

.. image:: https://secure.travis-ci.org/jkbr/httpie.png
    :target: http://travis-ci.org/jkbr/httpie
    :alt: Build Status of the master branch

::

    pip install -U https://github.com/jkbr/httpie/tarball/master


There are packages available for `Ubuntu <http://packages.ubuntu.com/quantal/httpie>`_ and `Debian <http://packages.debian.org/wheezy/httpie>`_.


Usage
-----

Hello world::

    http httpie.org

Synopsis::

    http [flags] [METHOD] URL [items]

There are four types of key-value pair items available:

Headers (``Name:Value``)
   Arbitrary HTTP headers. The ``:`` character is used to separate a header's name from its value, e.g., ``X-API-Token:123``.

Simple data fields (``field=value``)
  Data items are included in the request body. Depending on the ``Content-Type``, they are automatically serialized as a JSON ``Object`` (default) or ``application/x-www-form-urlencoded`` (the ``-f`` flag). Data items use ``=`` as the separator, e.g., ``hello=world``.

Raw JSON fields (``field:=value``)
  This item type is needed when ``Content-Type`` is JSON and a field's value is a ``Boolean``, ``Number``,  nested ``Object`` or an ``Array``, because simple data items are always serialized as ``String``. E.g. ``pies:=[1,2,3]``.

File fields (``field@/path/to/file``)
  Only available with ``-f`` / ``--form``. Use ``@`` as the separator, e.g., ``screenshot@/path/to/file.png``. The presence of a file field results into a ``multipart/form-data`` request.


Examples
^^^^^^^^
::

    http PATCH api.example.com/person/1 X-API-Token:123 name=John email=john@example.org age:=29


The following request is issued::

    PATCH /person/1 HTTP/1.1
    User-Agent: HTTPie/0.1
    X-API-Token: 123
    Content-Type: application/json; charset=utf-8

    {"name": "John", "email": "john@example.org", "age": 29}


It can easily be changed to a **form** request using the ``-f`` (or ``--form``) flag, which produces::

    PATCH /person/1 HTTP/1.1
    User-Agent: HTTPie/0.1
    X-API-Token: 123
    Content-Type: application/x-www-form-urlencoded; charset=utf-8

    age=29&name=John&email=john%40example.org

It is also possible to send ``multipart/form-data`` requests, i.e., to simulate a **file upload form** submission. It is done using the ``--form`` / ``-f`` flag and passing one or more file fields::

    http -f POST example.com/jobs name=John cv@~/Documents/cv.pdf

The above will send the same request as if the following HTML form were submitted::

    <form enctype="multipart/form-data" method="post" action="http://example.com/jobs">
        <input type="text" name="name" />
        <input type="file" name="cv" />
    </form>

A whole request body can be passed in via **``stdin``** instead, in which case it will be used with no further processing::

    echo '{"name": "John"}' | http PATCH example.com/person/1 X-API-Token:123
    # Or:
    http POST example.com/person/1 X-API-Token:123 < person.json

That can be used for **piping services together**. The following example ``GET``s JSON data from the Github API and ``POST``s it to httpbin.org::

    http -b GET https://api.github.com/repos/jkbr/httpie | http POST httpbin.org/post

The above can be further simplified by omitting ``GET`` and ``POST`` because they are both default here. The first command has no request data, whereas the second one does via ``stdin``::

    http -b https://api.github.com/repos/jkbr/httpie | http httpbin.org/post

An alternative to ``stdin`` is to pass a file name whose content will be used as the request body. It has the advantage that the ``Content-Type`` header will automatically be set to the appropriate value based on the filename extension (using the ``mimetypes`` module). Therefore, the following will request will send the verbatim contents of the file with ``Content-Type: application/xml``::

    http PUT httpbin.org/put @/data/file.xml


Flags
^^^^^
Most of the flags mirror the arguments understood by ``requests.request``. See ``http -h`` for more details::

    $ http --help
    usage: http [-h] [--version] [--json | --form] [--traceback]
                [--pretty | --ugly]
                [--print OUTPUT_OPTIONS | --verbose | --headers | --body]
                [--style STYLE] [--auth AUTH] [--auth-type {basic,digest}]
                [--verify VERIFY] [--proxy PROXY] [--allow-redirects]
                [--timeout TIMEOUT]
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
                            (field_name:=value), or a file field
                            (field_name@/path/to/file). You can use a backslash to
                            escape a colliding separator in the field name.

    optional arguments:
      -h, --help            show this help message and exit
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
                            String specifying what should the output contain. "H"
                            stands for the request headers and "B" for the request
                            body. "h" stands for the response headers and "b" for
                            response the body. Defaults to "hb" which means that
                            the whole response (headers and body) is printed.
      --verbose, -v         Print the whole request as well as the response.
                            Shortcut for --print=HBhb.
      --headers, -t         Print only the response headers. Shortcut for
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
      --auth AUTH, -a AUTH  username:password. If the password is omitted (-a
                            username), HTTPie will prompt for it.
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
-----------

`View contributors on GitHub <https://github.com/jkbr/httpie/contributors>`_.

If you have found a bug or have a feature request, the `issue tracker <https://github.com/jkbr/httpie/issues?state=open>`_ is the place to start a discussion about it.

To contribute code or documentation, please first browse the existing issues to see if the feature/bug has previously been discussed. Then fork `the repository <https://github.com/jkbr/httpie>`_, make changes in your develop branch and submit a pull request. Note: Pull requests with tests and documentation are 53.6%  more awesome :)

Before a pull requests is submitted, it's a good idea to run the existing suite of tests::

    python setup.py test

`Tox <http://tox.testrun.org/>`_ can used to conveniently run tests in all of the `supported Python environments <https://github.com/jkbr/httpie/blob/master/tox.ini>`_::

    # Install tox
    pip install tox

    # Run tests
    tox

Changelog
---------

* `0.2.4 <https://github.com/jkbr/httpie/compare/0.2.2...0.2.4>`_ (2012-06-24)
    * Unicode characters in prettified JSON now don't get escaped to improve readability.
    * --auth now prompts for a password if only a username provided.
    * Added support for request payloads from a file path with automatic ``Content-Type`` (``http URL @/path``).
    * Fixed missing query string when displaing the request headers via ``--verbose``.
    * Fixed Content-Type for requests with no data.
* `0.2.2 <https://github.com/jkbr/httpie/compare/0.2.1...0.2.2>`_ (2012-06-24)
    * The ``METHOD`` positional argument can now be omitted (defaults to ``GET``, or to ``POST`` with data).
    * Fixed --verbose --form.
    * Added support for `Tox <http://tox.testrun.org/>`_.
* `0.2.1 <https://github.com/jkbr/httpie/compare/0.2.0...0.2.1>`_ (2012-06-13)
    * Added compatibility with ``requests-0.12.1``.
    * Dropped custom JSON and HTTP lexers in favor of the ones newly included in ``pygments-1.5``.
* `0.2.0 <https://github.com/jkbr/httpie/compare/0.1.6...0.2.0>`_ (2012-04-25)
    * Added Python 3 support.
    * Added the ability to print the HTTP request as well as the response (see ``--print`` and ``--verbose``).
    * Added support for Digest authentication.
    * Added file upload support (``http -f POST file_field_name@/path/to/file``).
    * Improved syntax highlighting for JSON.
    * Added support for field name escaping.
    * Many bug fixes.
* `0.1.6 <https://github.com/jkbr/httpie/compare/0.1.4...0.1.6>`_ (2012-03-04)
