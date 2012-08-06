***********************
HTTPie: cURL for Humans
***********************

v0.2.7

HTTPie is a **command line HTTP client** whose goal is to make CLI interaction
with HTTP-based services as **human-friendly** as possible. It provides a
simple ``http`` command that allows for sending arbitrary HTTP requests with a
simple and natural syntax, and displays colorized responses. HTTPie can be used
for **testing, debugging**, and generally **interacting** with HTTP servers.


.. image:: https://github.com/jkbr/httpie/raw/master/httpie.png
    :alt: HTTPie compared to cURL
    :width: 835
    :height: 835


HTTPie is written in Python, and under the hood it uses the excellent
`Requests`_ and `Pygments`_ libraries.


**Table of Contents**


.. contents::
    :local:
    :depth: 1
    :backlinks: none



=============
Main Features
=============

* Expressive and intuitive syntax
* Formatted and colorized terminal output
* Built-in JSON support
* Forms and file uploads
* HTTPS and authorization
* Arbitrary request data
* Custom headers
* Python 2.6 and Python 3 support
* Linux, Mac OS X and Windows support
* Documentation
* Test coverage


============
Installation
============

The latest **stable version** of HTTPie can always be installed or updated
to via `pip`_ (prefered)
or ``easy_install``:

.. code-block:: bash

    $ pip install -U httpie


.. code-block:: bash

    $ easy_install httpie


Or, you can install the **development version** directly from GitHub:


.. image:: https://secure.travis-ci.org/jkbr/httpie.png
    :target: http://travis-ci.org/jkbr/httpie
    :alt: Build Status of the master branch


.. code-block:: bash

    $ pip install -U https://github.com/jkbr/httpie/tarball/master


There are also packages available for `Ubuntu`_, `Debian`_, and possibly other
Linux distributions as well.


===========
Quick Start
===========


Hello World:


.. code-block:: bash

    $ http httpie.org


Synopsis:

.. code-block:: bash

    $ http [flags] [METHOD] URL [ITEM [ITEM]]


See also ``http --help``.


--------
Examples
--------


Send a ``HEAD`` request:

.. code-block:: bash

    $ http HEAD example.org


Submit a form:

.. code-block:: bash

    $ http --form POST example.org hello=World


Send a ``PUT`` request with a custom header and some JSON data:

.. code-block:: bash

    $ http PUT example.org X-API-Token:123 name='David Bowie'

See the request that is being sent:

.. code-block:: bash

    $ http --verbose example.org


Use `Github API`_ to post a comment on an issue:

.. code-block:: bash

    $ http -a USERNAME POST https://api.github.com/repos/jkbr/httpie/issues/83/comments body='HTTPie is awesome!'


Upload a file:

.. code-block:: bash

    $ http example.org < file.json


Download a file:

.. code-block:: bash

    $ http example.org/file > file

============
HTTP Method
============

The name of the HTTP method comes right before the URL argument:

.. code-block:: bash

    $ http DELETE example.org/todos/7


It makes the command look similar to the actual ``Request-Line`` that is sent:

.. code-block:: http

    DELETE /todos/7 HTTP/1.1


When the ``METHOD`` argument is **omitted** from the command, HTTPie defaults to
either ``GET`` or ``POST``. This depends on whether you are sending
some data:

.. code-block:: bash

    $ http example.org/todos text='Check out HTTPie'


.. code-block:: http

    POST /todos HTTP/1.1


, or no data at all:

.. code-block:: bash

    $ http example.org/todos


.. code-block:: http

    GET /todos HTTP/1.1


===========
Request URL
===========

The only information HTTPie needs to perform a request is a URL.
The default scheme is, somewhat unsurprisingly, ``http://``,
and can be omitted from the argument – ``http example.org`` works just fine.

If find yourself manually constructing URLs with **querystring parameters**
on the terminal, you may appreciate the ``param==value`` syntax for appending
URL parameters so that you don't have to worry about escaping the ``&``
separators. To search for ``HTTPie`` on Google Images you could use this
command:

.. code-block:: bash

    $ http GET www.google.com search==HTTPie tbm==isch


.. code-block:: http

    GET /?search=HTTPie&tbm=isch HTTP/1.1


=============
Request Items
=============

There are five different *request item* types that provide a
convenient mechanism for specifying HTTP headers, simple JSON and
form data, files, and URL parameters.

They are key/value pairs specified after the URL. All have in
common that they become part of the actual request that is sent and that
their type is distinguished only by the separator used:
``:``, ``=``, ``:=``, ``@``, and ``==``.

+-----------------------+-----------------------------------------------------+
| Item Type             | Description                                         |
+=======================+=====================================================+
| HTTP Headers          | Arbitrary HTTP header, e.g. ``X-API-Token:123``.    |
| ``Name:Value``        |                                                     |
+-----------------------+-----------------------------------------------------+
| URL parameters        | Appends the given name/value pair as a query        |
| ``name==value``       | string parameter to the URL.                        |
|                       | The ``==`` separator is used                        |
+-----------------------+-----------------------------------------------------+
| Data Fields           | Request data fields to be serialized as a JSON      |
| ``field=value``       | object (default), or to be form encoded (``--form`` |
|                       | / ``-f``).                                          |
+-----------------------+-----------------------------------------------------+
| Raw JSON fields       | Useful when sending JSON and one or                 |
| ``field:=json``       | more fields need to be a ``Boolean``, ``Number``,   |
|                       | nested ``Object``, or an ``Array``,  e.g.,          |
|                       | ``meals:='["ham","spam"]'`` or ``pies:=[1,2,3]``    |
|                       | (note the quotes).                                  |
+-----------------------+-----------------------------------------------------+
| Files                 | Only available with ``-f`` / ``--form``.            |
| ``field@/dir/file``   | For example ``screenshot@~/Pictures/img.png``.      |
|                       | The presence of a file field results                |
|                       | in a ``multipart/form-data`` request.               |
+-----------------------+-----------------------------------------------------+

You can use ``\`` to escape characters that shouldn't be used as separators
(or parts thereof). e.g., ``foo\==bar`` will become a data key/value
pair (``foo=`` and ``bar``) instead of a URL parameter.

No that data fields aren't the only way to specify request data,
`redirected input`_ allows passing arbitrary data to be sent with the request.


====
JSON
====

JSON is the *lingua franca* of modern web services and it is also the
**default content type** HTTPie uses:

If your command includes some data items, they are serialized as a JSON
object by default. HTTPie also automatically sets the following headers,
both of which can be overwritten:

================    =======================================
``Content-Type``    ``application/json; charset=utf-8``
``Accept``          ``application/json``
================    =======================================

You can use ``--json`` / ``-j`` to set ``Accept`` to ``application/json``
regardless of whether you are sending data (it's a shortcut for using setting
the header via the usual header notation –
``http url Accept:application/json``).

Simple example:

.. code-block:: bash

    $ http PUT example.org name=John email=john@example.org

.. code-block:: http

    PUT / HTTP/1.1
    Accept: application/json
    Accept-Encoding: identity, deflate, compress, gzip
    Content-Type: application/json; charset=utf-8
    Host: example.org
    User-Agent: HTTPie/0.2.7dev

    {
        "name": "John",
        "email": "john@example.org"
    }


Non-string fields use the ``:=`` separator, which allows you to embed raw JSON
into the resulting object:

.. code-block:: bash

    $ http PUT api.example.com/person/1 name=John age:=29 married:=false hobbies:='["http", "pies"]'


.. code-block:: http

    PUT /person/1 HTTP/1.1
    Accept: application/json
    Content-Type: application/json; charset=utf-8
    Host: api.example.com
    User-Agent: HTTPie/0.2.7dev

    {
        "age": 29,
        "hobbies": [
            "http",
            "pies"
        ],
        "married": false,
        "name": "John"
    }



=====
Forms
=====

Submitting forms is very similar to sending `JSON`_ requests. Often the only
difference is in adding the ``--form`` / ``-f`` option, which ensures that
data fields are serialized and ``Content-Type`` is set to
``application/x-www-form-urlencoded; charset=utf-8``.

-------------
Regular Forms
-------------

.. code-block:: bash

    $ http --form POST api.example.org/person/1 name='John Smith' email=john@example.org


.. code-block:: http

    POST /person/1 HTTP/1.1
    User-Agent: HTTPie/0.2.7dev
    Content-Type: application/x-www-form-urlencoded; charset=utf-8

    name=John+Smith&email=john%40example.org


-----------------
File Upload Forms
-----------------

When one or more file fields are present, the content type is
``multipart/form-data``:

.. code-block:: bash

    $ http -f POST example.com/jobs name='John Smith' cv@~/Documents/cv.pdf


The request above is the same as if the following HTML form were
submitted:

.. code-block:: html

    <form enctype="multipart/form-data" method="post" action="http://example.com/jobs">
        <input type="text" name="name" />
        <input type="file" name="cv" />
    </form>


============
HTTP Headers
============

To set custom headers you can use the ``Header:Value`` notation:

.. code-block:: bash

    $ http example.org  User-Agent:Bacon/1.0  Cookie:valued-visitor=yes  X-Foo:Bar  Referer:http://httpie.org/


.. code-block:: http

    GET / HTTP/1.1
    Accept: */*
    Accept-Encoding: identity, deflate, compress, gzip
    Cookie: valued-visitor=yes
    Host: example.org
    Referer: http://httpie.org/
    User-Agent: Bacon/1.0
    X-Foo: Bar


There are a couple of default headers that HTTPie sets, but they can easily
be overwritten:

.. code-block:: http

    GET / HTTP/1.1
    Accept: */*
    Accept-Encoding: identity, deflate, compress, gzip
    User-Agent: HTTPie/<version>
    Host: <taken-from-URL>


====
Auth
====

The currently supported authorization schemes are Basic and Digest (more to
come). There are two flags that control authorization:

===================     ======================================================
``--auth, -a``          Pass a ``username:password`` pair as
                        the argument. Or, if you only specify a username
                        (``-a username``), you'll be prompted for
                        the password before the request is sent.
                        To send a an empty password, pass ``username:``.

``--auth-type``         Specify the auth mechanism. Possible values are
                        ``basic`` and ``digest``. The default value is
                        ``basic`` so it can often be omitted.
===================     ======================================================


Basic auth:


.. code-block:: bash

    $ http -a username:password example.org


Digest auth:


.. code-block:: bash

    $ http --auth-type=digest -a username:password example.org


With password prompt:

.. code-block:: bash

    $ http -a username example.org


==============
Output Options
==============

By default, HTTPie outputs the whole response message (headers as well as the
body).

You can control what should be printed via several options:

=================   =====================================================
``--headers, -h``   Only the response headers are printed.
``--body, -b``      Only the response body is printed.
``--verbose, -v``   Print the whole HTTP exchange (request and response).
``--print, -p``     Selects parts of the HTTP exchange.
=================   =====================================================

``--verbose`` can often be useful for debugging the request and generating
documentation examples:

.. code-block:: bash

    $ http --verbose PUT httpbin.org/put hello=world
    PUT /put HTTP/1.1
    Accept: application/json
    Accept-Encoding: identity, deflate, compress, gzip
    Content-Type: application/json; charset=utf-8
    Host: httpbin.org
    User-Agent: HTTPie/0.2.7dev

    {
        "hello": "world"
    }


    HTTP/1.1 200 OK
    Connection: keep-alive
    Content-Length: 477
    Content-Type: application/json
    Date: Sun, 05 Aug 2012 00:25:23 GMT
    Server: gunicorn/0.13.4

    {
        […]
    }


All the other options are just a shortcut for ``--print`` / ``-p``.
It accepts a string of characters each of which represents a specific part of
the HTTP exchange:

==========  ==================
Character   Stands for
==========  ==================
``H``       Request headers.
``B``       Request body.
``h``       Response headers.
``b``       Response body.
==========  ==================

Print both the request and response headers:

.. code-block:: bash

    $ http --print=Hh PUT httpbin.org/put hello=world


-------------------------
Conditional Body Download
-------------------------

As an optimization, the response body is downloaded from the server
only if it's part of the output. This is similar to performing a ``HEAD``
request, except that it applies to any HTTP method you use.

Let's say that there is an API that returns the whole resource when it is
updated, but you are only interested in the response headers to see the
status code after the update:

.. code-block:: bash

    $ http --headers PATCH example.org/Really-Huge-Resource name='New Name'


Since we are only printing the HTTP headers here, the connection to server
is closed as soon as all the response headers have been received.
Therefore, bandwidth and time isn't wasted downloading the body
which you don't care about.

The response headers are downloaded always, even if they are not part of
the output


================
Redirected Input
================

**A universal method for passing request data is through redirected** ``stdin``
(standard input). Such data is buffered and then with no further processing
used as the request body. There are multiple useful ways to use piping:

Redirect from a file:

.. code-block:: bash

    $ http PUT example.com/person/1 X-API-Token:123 < person.json


Or the output of another program:

.. code-block:: bash

    $ grep /var/log/httpd/error_log '401 Unauthorized' | http POST example.org/intruders


You can use ``echo`` for simple data:

.. code-block:: bash

    $ echo '{"name": "John"}' | http PATCH example.com/person/1 X-API-Token:123


You can even pipe web services together using HTTPie:

.. code-block:: bash

    $ http GET https://api.github.com/repos/jkbr/httpie | http POST httpbin.org/post


You can use ``cat`` to enter multiline data on the terminal:

.. code-block:: bash

    $ cat | http POST example.com⏎
    <paste>
    ^D


.. code-block:: bash

    $ cat | http POST example.com/todos Content-Type:text/plain⏎
    - buy milk
    - call parents
    ^D


On OS X, you can send the contents of the clipboard with ``pbpaste``:

.. code-block:: bash

    $ pbpaste | http PUT example.com


Passing data through ``stdin`` cannot be combined with data fields specified
on the command line.


-------------------------
Body Data From a Filename
-------------------------

**An alternative to redirected** ``stdin`` is specifying a filename (as
``@/path/to/file``) whose content is used as if it came from ``stdin``.

It has the advantage that **the** ``Content-Type``
**header will automatically be set** to the appropriate value based on the
filename extension. For example, the following request sends the
verbatim contents of that XML file with ``Content-Type: application/xml``:

.. code-block:: bash

    $ http PUT httpbin.org/put @/data/file.xml


=================
Terminal Output
=================

HTTPie does several things by default to make its terminal output easy to read.


---------------------
Colors and Formatting
---------------------

Syntax highlighting is applied to HTTP headers and bodies (where it makes
sense). Also, the following formatting is used:

* HTTP headers are sorted by name.
* JSON data is indented, sorted by keys, and unicode escapes are converted
  to the characters they represent.

Colorizing and formatting can be disabled with ``--ugly, -u``.


-----------
Binary data
-----------

Binary data is suppressed for terminal output, which makes it safe to perform
requests to URLs send back binary data. Binary data is suppressed also in
redirected, but prettified output. The connection is closed as soon as we know
that the response body is binary,

.. code-block:: bash

    http example.org/File.mov


You will immediately see something like this:

.. code-block:: http

    HTTP/1.1 200 OK
    Accept-Ranges: bytes
    Content-Encoding: gzip
    Content-Type: video/quicktime
    Transfer-Encoding: chunked

    +-----------------------------------------+
    | NOTE: binary data not shown in terminal |
    +-----------------------------------------+


=================
Redirected Output
=================

HTTPie uses **different defaults** for redirected output than for
`terminal output`_:

* Formatting and colors aren't applied (unless ``--pretty`` is set).
* Only the response body is printed (unless one of the `output options`_ is set).
* Also, binary data isn't suppressed.

The reason is to make piping HTTPie's output to another programs and
downloading files work with no extra flags. Most of the time, only the raw
response body is of an interest when the output is redirected.

Download a file:

.. code-block:: bash

    $ http example.org/Movie.mov > Movie.mov


Download an image of Octocat, resize it using ImageMagick, upload it elsewhere:

.. code-block:: bash

    $ http octodex.github.com/images/original.jpg | convert - -resize 25% -  | http example.org/Octocats


Force colorizing and formatting, and show both the request and response in
``less`` pager:

.. code-block:: bash

    $ http --pretty --verbose example.org | less -R


==================
Streamed Responses
==================

Responses are downloaded and printed in chunks, which allows for streaming
and large file downloads without using too much RAM. However, when
`colors and formatting`_ are applied, the whole response is buffered and only
then processed at once.


You can use the ``--stream, -S`` flag to make two things happen:

1. The output is flushed in **much smaller chunks** without any buffering,
   which makes HTTPie behave kind of like ``tail -f`` for URLs.

2. Streaming becomes enabled even when the output is prettified: It will be
   applied to **each line** of the response and flushed immediately. This makes
   it possible to have a nice output of long-lived requests, such as one
   to the Twitter streaming API.


Prettified streamed response:

.. code-block:: bash

    $ http --stream -f -a YOUR-TWITTER-NAME https://stream.twitter.com/1/statuses/filter.json track='Justin Bieber'


Streamed output by small chunks:

.. code-block:: bash

    # Send each new tweet (JSON object) mentioning "Apple" to another
    # server as soon as it arrives from the Twitter streaming API:
    $ http --stream -f -a YOUR-TWITTER-NAME https://stream.twitter.com/1/statuses/filter.json track=Apple \
    | while read tweet; do echo "$tweet" | http POST example.org/tweets ; done


=========
Scripting
=========

When using HTTPie from **shell scripts**, it can be handy to set the
``--check-status`` flag. It instructs HTTPie to exit with an error if the
HTTP status is one of ``3xx``, ``4xx``, or ``5xx``. The exit status will
be ``3`` (unless ``--allow-redirects`` is set), ``4``, or ``5``,
respectively:

.. code-block:: bash

    #!/bin/bash

    if http --check-status HEAD example.org/health &> /dev/null; then
        echo 'OK!'
    else
        case $? in
            3) echo 'Unexpected HTTP 3xx Redirection!' ;;
            4) echo 'HTTP 4xx Client Error!' ;;
            5) echo 'HTTP 5xx Server Error!' ;;
            *) echo 'Other Error!' ;;
        esac
    fi


================
Interface Design
================

The syntax of the command arguments closely corresponds to the actual HTTP
requests sent over the wire. It has the advantage  that it's easy to remember
and read. It is often possible to translate an HTTP request to an HTTPie
argument list just by inlining the request elements. For example, compare this
HTTP request:

.. code-block:: http

    POST /collection HTTP/1.1
    X-API-Key: 123
    User-Agent: Bacon/1.0
    Content-Type: application/x-www-form-urlencoded

    name=value&name2=value2


with the HTTPie command that sends it:

.. code-block:: bash

    $ http -f POST example.org/collection \
      X-API-Key:123 \
      User-Agent:Bacon/1.0 \
      name=value \
      name2=value2


Notice that both the order of elements and the syntax is very similar,
and that only a small portion of the command is used to control HTTPie and
doesn't directly correspond to any part of the request (here it's only ``-f``
asking HTTPie to send a form request).

The two modes, ``--pretty, -p`` (default for terminal) and ``--ugly, -u``
(default for redirected output), allow for both user-friendly interactive use
and usage from scripts, where HTTPie serves as a generic HTTP client.


==========
Contribute
==========

Bug reports and code and documentation patches are greatly appretiated. You can
also help by using the development version of HTTPie and reporting any bugs you
might encounter.

Before working on a new feature or a bug, please browse the `existing issues`_
to see whether it has been previously discussed. If the change in question
is a bigger one, it's always good to discuss before your starting working on
it.

Then fork and clone `the repository`_.

It's very useful to point the ``http`` command to your local branch during
development. To do so, install HTTPie with ``pip`` in editable mode:

.. code-block:: bash

    $ pip install --upgrade --force-reinstall --editable .


Please run the existing suite of tests before a pull request is submitted:

.. code-block:: bash

    python setup.py test


`Tox`_ can also be used to conveniently run tests in all of the
`supported Python environments`_:

.. code-b®lock:: bash

    # Install tox
    pip install tox

    # Run tests
    tox


Don't forget to add yourself to `AUTHORS`_.


=======
Authors
=======

`Jakub Roztocil`_  (`@jakubroztocil`_) created HTTPie and `these fine people`_
have contributed.


=======
Licence
=======

Please see `LICENSE`_.


=========
Changelog
=========

* `0.2.8dev`_
* `0.2.7`_ (2012-08-07)
    * Compatibility with Requests 0.13.6.
    * Streamed terminal output. ``--stream`` / ``-S`` can be used to enable
      streaming also with ``--pretty`` and to ensure a more frequent output
      flushing.
    * Support for efficient large file downloads.
    * Sort headers by name (unless ``--ugly``).
    * Response body is fetched only when needed (e.g., not with ``--headers``).
    * Improved content type matching.
    * Updated Solarized color scheme.
    * Windows: Added ``--output FILE`` to store output into a file
      (piping results in corrupted data on Windows).
    * Proper handling of binary requests and responses.
    * Fixed printing of ``multipart/form-data`` requests.
    * Renamed ``--traceback`` to ``--debug``.
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


.. _Requests: http://python-requests.org
.. _Pygments: http://pygments.org/
.. _pip: http://www.pip-installer.org/en/latest/index.html
.. _Tox: http://tox.testrun.org
.. _Github API: http://developer.github.com/v3/issues/comments/#create-a-comment
.. _supported Python environments: https://github.com/jkbr/httpie/blob/master/tox.ini
.. _Ubuntu: http://packages.ubuntu.com/httpie
.. _Debian: http://packages.debian.org/httpie
.. _the repository: https://github.com/jkbr/httpie
.. _these fine people: https://github.com/jkbr/httpie/contributors
.. _Jakub Roztocil: http://roztocil.name
.. _@jakubroztocil: https://twitter.com/jakubroztocil
.. _existing issues: https://github.com/jkbr/httpie/issues?state=open
.. _0.1.6: https://github.com/jkbr/httpie/compare/0.1.4...0.1.6
.. _0.2.0: https://github.com/jkbr/httpie/compare/0.1.6...0.2.0
.. _0.2.1: https://github.com/jkbr/httpie/compare/0.2.0...0.2.1
.. _0.2.2: https://github.com/jkbr/httpie/compare/0.2.1...0.2.2
.. _0.2.5: https://github.com/jkbr/httpie/compare/0.2.2...0.2.5
.. _0.2.6: https://github.com/jkbr/httpie/compare/0.2.5...0.2.6
.. _0.2.7: https://github.com/jkbr/httpie/compare/0.2.5...0.2.7
.. _0.2.8dev: https://github.com/jkbr/httpie/compare/0.2.7...master
.. _README for stable version: https://github.com/jkbr/httpie/tree/0.2.6#readme
.. _AUTHORS: https://github.com/jkbr/httpie/blob/master/AUTHORS.rst
.. _LICENSE: https://github.com/jkbr/httpie/blob/master/LICENSE
