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


Usage
-----

Hello world::

    http GET httpie.org

Synopsis::

    http [flags] METHOD URL [items]

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


It can easily be changed to a 'form' request using the ``-f`` (or ``--form``) flag, which produces::

    PATCH /person/1 HTTP/1.1
    User-Agent: HTTPie/0.1
    X-API-Token: 123
    Content-Type: application/x-www-form-urlencoded; charset=utf-8

    age=29&name=John&email=john%40example.org

It is also possible to send ``multipart/form-data`` requests, i.e., to simulate a file upload form submission. It is done using the ``--form`` / ``-f`` flag and passing one or more file fields::

    http -f POST example.com/jobs name=John cv@~/Documents/cv.pdf

The above will send the same request as if the following HTML form were submitted::

    <form enctype="multipart/form-data" method="post" action="http://example.com/jobs">
        <input type="text" name="name" />
        <input type="file" name="cv" />
    </form>

A whole request body can be passed in via ``stdin`` instead::

    echo '{"name": "John"}' | http PATCH example.com/person/1 X-API-Token:123
    # Or:
    http POST example.com/person/1 X-API-Token:123 < person.json


Flags
^^^^^
Most of the flags mirror the arguments understood by ``requests.request``. See ``http -h`` for more details::

    usage: http [-h] [--version] [--json | --form] [--traceback]
                       [--pretty | --ugly]
                       [--print OUTPUT_OPTIONS | --verbose | --headers | --body]
                       [--style STYLE] [--auth AUTH] [--auth-type {basic,digest}]
                       [--verify VERIFY] [--proxy PROXY] [--allow-redirects]
                       [--timeout TIMEOUT]
                       METHOD URL [ITEM [ITEM ...]]

    HTTPie - cURL for humans. <http://httpie.org>

    positional arguments:
      METHOD                The HTTP method to be used for the request (GET, POST,
                            PUT, DELETE, PATCH, ...).
      URL                   The protocol defaults to http:// if the URL does not
                            include one.
      ITEM                  A key-value pair whose type is defined by the
                            separator used. It can be an HTTP header
                            (header:value), a data field to be used in the request
                            body (field_name=value), a raw JSON data field
                            (field_name:=value) or a file field
                            (field_name@/path/to/file). You can use a backslash to
                            escape a colliding separator in the field name.

    optional arguments:
      -h, --help            show this help message and exit
      --version             show program's version number and exit
      --json, -j            (default) Data items are serialized as a JSON object.
                            The Content-Type and Accept headers are set to
                            application/json (if not set via the command line).
      --form, -f            Data items are serialized as form fields. The Content-
                            Type is set to application/x-www-form-urlencoded (if
                            not specifid). The presence of any file fields results
                            into a multipart/form-data request.
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
                            monokai, murphy, native, pastie, perldoc, solarized,
                            tango, trac, vim, vs. Defaults to solarized. For this
                            option to work properly, please make sure that the
                            $TERM environment variable is set to "xterm-256color"
                            or similar (e.g., via `export TERM=xterm-256color' in
                            your ~/.bashrc).
      --auth AUTH, -a AUTH  username:password
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


Contributors
------------

`View contributors on GitHub <https://github.com/jkbr/httpie/contributors>`_.


Changelog
---------

* `New in development version <https://github.com/jkbr/httpie/compare/0.2.0...master>`_
* 0.2.0 (2012-04-25)
    * Added Python 3 support.
    * Added the ability to print the HTTP request as well as the response (see ``--print`` and ``--verbose``).
    * Added support for Digest authentication.
    * Added file upload support (``http -f POST file_field_name@/path/to/file``).
    * Improved syntax highlighting for JSON.
    * Added support for field name escaping.
    * Many bug fixes.
    * `Complete changelog <https://github.com/jkbr/httpie/compare/0.1.6...0.2.0>`_

* `0.1.6 <https://github.com/jkbr/httpie/compare/0.1.4...0.1.6>`_ (2012-03-04)
