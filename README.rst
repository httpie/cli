HTTPie: cURL for humans
=======================

**HTTPie is a CLI HTTP utility** built out of frustration with existing tools. The goal is to make CLI interaction with HTTP-based services as human-friendly as possible.

HTTPie does so by providing an ``http`` command that allows for issuing arbitrary HTTP requests using a **simple and natural syntax** and displaying **colorized responses**:

.. image:: https://github.com/jkbr/httpie/raw/master/httpie.png
    :alt: HTTPie compared to cURL

Under the hood, HTTPie uses the excellent `Requests <http://python-requests.org>`_ and `Pygments <http://pygments.org/>`_ Python libraries.

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

There are three types of key-value pair items available:

Headers
   Arbitrary HTTP headers. The ``:`` character is used to separate a header's name from its value, e.g., ``X-API-Token:123``.

Simple data items
  Data items are included in the request body. Depending on the ``Content-Type``, they are automatically serialized as a JSON ``Object`` (default) or ``application/x-www-form-urlencoded`` (the ``-f`` flag). Data items use ``=`` as the separator, e.g., ``hello=world``.

Raw JSON items
  This item type is needed when ``Content-Type`` is JSON and a field's value is a ``Boolean``, ``Number``,  nested ``Object`` or an ``Array``, because simple data items are always serialized as ``String``. E.g. ``pies:=[1,2,3]``.

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

A whole request body can be passed in via ``stdin`` instead::

    echo '{"name": "John"}' | http PATCH example.com/person/1 X-API-Token:123
    # Or:
    http POST example.com/person/1 X-API-Token:123 < person.json


Flags
^^^^^
Most of the flags mirror the arguments understood by ``requests.request``. See ``http -h`` for more details::

    usage: http [-h] [--version] [--json | --form] [--traceback]
                [--pretty | --ugly] [--headers | --body] [--style STYLE]
                [--auth AUTH] [--verify VERIFY] [--proxy PROXY]
                [--allow-redirects] [--file PATH] [--timeout TIMEOUT]
                METHOD URL [items [items ...]]

    HTTPie - cURL for humans.

    positional arguments:
      METHOD                HTTP method to be used for the request (GET, POST,
                            PUT, DELETE, PATCH, ...).
      URL                   Protocol defaults to http:// if the URL does not
                            include it.
      items                 HTTP header (key:value), data field (key=value) or raw
                            JSON field (field:=value).

    optional arguments:
      -h, --help            show this help message and exit
      --version             show program's version number and exit
      --json, -j            Serialize data items as a JSON object and set Content-
                            Type to application/json, if not specified.
      --form, -f            Serialize data items as form values and set Content-
                            Type to application/x-www-form-urlencoded, if not
                            specified.
      --traceback           Print exception traceback should one occur.
      --pretty, -p          If stdout is a terminal, the response is prettified by
                            default (colorized and indented if it is JSON). This
                            flag ensures prettifying even when stdout is
                            redirected.
      --ugly, -u            Do not prettify the response.
      --headers, -t         Print only the response headers.
      --body, -b            Print only the response body.
      --style STYLE, -s STYLE
                            Output coloring style, one of autumn, borland, bw,
                            colorful, default, emacs, friendly, fruity, manni,
                            monokai, murphy, native, pastie, perldoc, solarized,
                            tango, trac, vim, vs. Defaults to solarized.
      --auth AUTH, -a AUTH  username:password
      --verify VERIFY       Set to "yes" to check the host's SSL certificate. You
                            can also pass the path to a CA_BUNDLE file for private
                            certs. You can also set the REQUESTS_CA_BUNDLE
                            environment variable.
      --proxy PROXY         String mapping protocol to the URL of the proxy (e.g.
                            http:foo.bar:3128).
      --allow-redirects     Set this flag if full redirects are allowed (e.g. re-
                            POST-ing of data at new ``Location``)
      --file PATH           File to multipart upload
      --timeout TIMEOUT     Float describes the timeout of the request (Use
                            socket.setdefaulttimeout() as fallback).


Contributors
------------

`View contributors on GitHub <https://github.com/jkbr/httpie/contributors>`_.


Changelog
---------

* `0.1.6 <https://github.com/jkbr/httpie/compare/0.1.4...0.1.6>`_ (2012-03-04)
