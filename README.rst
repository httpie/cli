HTTPie: a CLI, cURL-like tool for humans
########################################

HTTPie (pronounced *aitch-tee-tee-pie*) is a command line HTTP client.
Its goal is to make CLI interaction with web services as human-friendly
as possible. It provides a simple ``http`` command that allows for sending
arbitrary HTTP requests using a simple and natural syntax, and displays
colorized output. HTTPie can be used for testing, debugging, and
generally interacting with HTTP servers.


.. class:: no-web no-pdf

    |pypi| |build| |coverage| |downloads| |gitter|


.. class:: no-web no-pdf

    .. image:: https://raw.githubusercontent.com/jakubroztocil/httpie/master/httpie.gif
        :alt: HTTPie in action
        :width: 100%
        :align: center


.. contents::

.. section-numbering::



Main features
=============


* Expressive and intuitive syntax
* Formatted and colorized terminal output
* Built-in JSON support
* Forms and file uploads
* HTTPS, proxies, and authentication
* Arbitrary request data
* Custom headers
* Persistent sessions
* Wget-like downloads
* Linux, macOS and Windows support
* Plugins
* Documentation
* Test coverage


.. class:: no-web

    .. image:: https://raw.githubusercontent.com/jakubroztocil/httpie/master/httpie.png
        :alt: HTTPie compared to cURL
        :width: 100%
        :align: center


Installation
============


macOS
-----


On macOS, HTTPie can be installed via `Homebrew <https://brew.sh/>`_
(recommended):

.. code-block:: bash

    $ brew install httpie


A MacPorts *port* is also available:

.. code-block:: bash

    $ port install httpie

Linux
-----

Most Linux distributions provide a package that can be installed using the
system package manager, for example:

.. code-block:: bash

    # Debian, Ubuntu, etc.
    $ apt-get install httpie

.. code-block:: bash

    # Fedora
    $ dnf install httpie

.. code-block:: bash

    # CentOS, RHEL, ...
    $ yum install httpie

.. code-block:: bash

    # Arch Linux
    $ pacman -S httpie


Windows, etc.
-------------

A universal installation method (that works on Windows, Mac OS X, Linux, …,
and always provides the latest version) is to use `pip`_:


.. code-block:: bash

    # Make sure we have an up-to-date version of pip and setuptools:
    $ pip install --upgrade pip setuptools

    $ pip install --upgrade httpie


(If ``pip`` installation fails for some reason, you can try
``easy_install httpie`` as a fallback.)


Python version
--------------

Starting with version 2.0.0 (currently under development) Python 3.6+ is required.


Unstable version
----------------

You can also install the latest unreleased development version directly from
the ``master`` branch on GitHub.  It is a work-in-progress of a future stable
release so the experience might be not as smooth.


.. class:: no-pdf

|build|


On macOS you can install it with Homebrew:

.. code-block:: bash

    $ brew install httpie --HEAD


Otherwise with ``pip``:

.. code-block:: bash

    $ pip install --upgrade https://github.com/jakubroztocil/httpie/archive/master.tar.gz


Verify that now we have the
`current development version identifier <https://github.com/jakubroztocil/httpie/blob/0af6ae1be444588bbc4747124e073423151178a0/httpie/__init__.py#L5>`_
with the ``-dev`` suffix, for example:

.. code-block:: bash

    $ http --version
    1.0.0-dev


Usage
=====


Hello World:


.. code-block:: bash

    $ http httpie.org


Synopsis:

.. code-block:: bash

    $ http [flags] [METHOD] URL [ITEM [ITEM]]


See also ``http --help``.


Examples
--------

Custom `HTTP method`_, `HTTP headers`_ and `JSON`_ data:

.. code-block:: bash

    $ http PUT example.org X-API-Token:123 name=John


Submitting `forms`_:

.. code-block:: bash

    $ http -f POST example.org hello=World


See the request that is being sent using one of the `output options`_:

.. code-block:: bash

    $ http -v example.org


Use `Github API`_ to post a comment on an
`issue <https://github.com/jakubroztocil/httpie/issues/83>`_
with `authentication`_:

.. code-block:: bash

    $ http -a USERNAME POST https://api.github.com/repos/jakubroztocil/httpie/issues/83/comments body='HTTPie is awesome! :heart:'


Upload a file using `redirected input`_:

.. code-block:: bash

    $ http example.org < file.json


Download a file and save it via `redirected output`_:

.. code-block:: bash

    $ http example.org/file > file


Download a file ``wget`` style:

.. code-block:: bash

    $ http --download example.org/file

Use named `sessions`_ to make certain aspects or the communication persistent
between requests to the same host:

.. code-block:: bash

    $ http --session=logged-in -a username:password httpbin.org/get API-Key:123

    $ http --session=logged-in httpbin.org/headers


Set a custom ``Host`` header to work around missing DNS records:

.. code-block:: bash

    $ http localhost:8000 Host:example.com

..


HTTP method
===========

The name of the HTTP method comes right before the URL argument:

.. code-block:: bash

    $ http DELETE example.org/todos/7


Which looks similar to the actual ``Request-Line`` that is sent:

.. code-block:: http

    DELETE /todos/7 HTTP/1.1


When the ``METHOD`` argument is omitted from the command, HTTPie defaults to
either ``GET`` (with no request data) or ``POST`` (with request data).


Request URL
===========

The only information HTTPie needs to perform a request is a URL.
The default scheme is, somewhat unsurprisingly, ``http://``,
and can be omitted from the argument – ``http example.org`` works just fine.


Querystring parameters
----------------------

If you find yourself manually constructing URLs with querystring parameters
on the terminal, you may appreciate the ``param==value`` syntax for appending
URL parameters. With that, you don't have to worry about escaping the ``&``
separators for your shell. Also, special characters in parameter values,
will also automatically escaped (HTTPie otherwise expects the URL to be
already escaped). To search for ``HTTPie logo`` on Google Images you could use
this command:

.. code-block:: bash

    $ http www.google.com search=='HTTPie logo' tbm==isch


.. code-block:: http

    GET /?search=HTTPie+logo&tbm=isch HTTP/1.1



URL shortcuts for ``localhost``
-------------------------------

Additionally, curl-like shorthand for localhost is supported.
This means that, for example ``:3000`` would expand to ``http://localhost:3000``
If the port is omitted, then port 80 is assumed.

.. code-block:: bash

    $ http :/foo


.. code-block:: http

    GET /foo HTTP/1.1
    Host: localhost


.. code-block:: bash

    $ http :3000/bar


.. code-block:: http

    GET /bar HTTP/1.1
    Host: localhost:3000


.. code-block:: bash

    $ http :


.. code-block:: http

    GET / HTTP/1.1
    Host: localhost


Other default schemes
---------------------

When HTTPie is invoked as ``https`` then the default scheme is ``https://``
(``$ https example.org`` will make a request to ``https://example.org``).

You can also use the ``--default-scheme <URL_SCHEME>`` option to create
shortcuts for other protocols than HTTP (possibly supported via plugins).
Example for the `httpie-unixsocket <https://github.com/httpie/httpie-unixsocket>`_ plugin:

.. code-block:: bash

    # Before
    $ http http+unix://%2Fvar%2Frun%2Fdocker.sock/info


.. code-block:: bash

    # Create an alias
    $ alias http-unix='http --default-scheme="http+unix"'


.. code-block:: bash

    # Now the scheme can be omitted
    $ http-unix %2Fvar%2Frun%2Fdocker.sock/info

Request items
=============

There are a few different *request item* types that provide a
convenient mechanism for specifying HTTP headers, simple JSON and
form data, files, and URL parameters.

They are key/value pairs specified after the URL. All have in
common that they become part of the actual request that is sent and that
their type is distinguished only by the separator used:
``:``, ``=``, ``:=``, ``==``, ``@``, ``=@``, and ``:=@``. The ones with an
``@`` expect a file path as value.

+-----------------------+-----------------------------------------------------+
| Item Type             | Description                                         |
+=======================+=====================================================+
| HTTP Headers          | Arbitrary HTTP header, e.g. ``X-API-Token:123``.    |
| ``Name:Value``        |                                                     |
+-----------------------+-----------------------------------------------------+
| URL parameters        | Appends the given name/value pair as a query        |
| ``name==value``       | string parameter to the URL.                        |
|                       | The ``==`` separator is used.                       |
+-----------------------+-----------------------------------------------------+
| Data Fields           | Request data fields to be serialized as a JSON      |
| ``field=value``,      | object (default), or to be form-encoded             |
| ``field=@file.txt``   | (``--form, -f``).                                   |
+-----------------------+-----------------------------------------------------+
| Raw JSON fields       | Useful when sending JSON and one or                 |
| ``field:=json``,      | more fields need to be a ``Boolean``, ``Number``,   |
| ``field:=@file.json`` | nested ``Object``, or an ``Array``,  e.g.,          |
|                       | ``meals:='["ham","spam"]'`` or ``pies:=[1,2,3]``    |
|                       | (note the quotes).                                  |
+-----------------------+-----------------------------------------------------+
| Form File Fields      | Only available with ``--form, -f``.                 |
| ``field@/dir/file``   | For example ``screenshot@~/Pictures/img.png``.      |
|                       | The presence of a file field results                |
|                       | in a ``multipart/form-data`` request.               |
+-----------------------+-----------------------------------------------------+


Note that data fields aren't the only way to specify request data:
`Redirected input`_ is a mechanism for passing arbitrary request data.


Escaping rules
--------------

You can use ``\`` to escape characters that shouldn't be used as separators
(or parts thereof). For instance, ``foo\==bar`` will become a data key/value
pair (``foo=`` and ``bar``) instead of a URL parameter.

Often it is necessary to quote the values, e.g. ``foo='bar baz'``.

If any of the field names or headers starts with a minus
(e.g., ``-fieldname``), you need to place all such items after the special
token ``--`` to prevent confusion with ``--arguments``:

.. code-block:: bash

    $ http httpbin.org/post  --  -name-starting-with-dash=foo -Unusual-Header:bar

.. code-block:: http

    POST /post HTTP/1.1
    -Unusual-Header: bar
    Content-Type: application/json

    {
        "-name-starting-with-dash": "foo"
    }



JSON
====

JSON is the *lingua franca* of modern web services and it is also the
**implicit content type** HTTPie uses by default.


Simple example:

.. code-block:: bash

    $ http PUT example.org name=John email=john@example.org

.. code-block:: http

    PUT / HTTP/1.1
    Accept: application/json, */*
    Accept-Encoding: gzip, deflate
    Content-Type: application/json
    Host: example.org

    {
        "name": "John",
        "email": "john@example.org"
    }


Default behaviour
-----------------


If your command includes some data `request items`_, they are serialized as a JSON
object by default. HTTPie also automatically sets the following headers,
both of which can be overwritten:

================    =======================================
``Content-Type``    ``application/json``
``Accept``          ``application/json, */*``
================    =======================================


Explicit JSON
-------------

You can use ``--json, -j`` to explicitly set ``Accept``
to ``application/json`` regardless of whether you are sending data
(it's a shortcut for setting the header via the usual header notation:
``http url Accept:'application/json, */*'``). Additionally,
HTTPie will try to detect JSON responses even when the
``Content-Type`` is incorrectly ``text/plain`` or unknown.



Non-string JSON fields
----------------------

Non-string fields use the ``:=`` separator, which allows you to embed raw JSON
into the resulting object. Text and raw JSON files can also be embedded into
fields using ``=@`` and ``:=@``:

.. code-block:: bash

    $ http PUT api.example.com/person/1 \
        name=John \
        age:=29 married:=false hobbies:='["http", "pies"]' \  # Raw JSON
        description=@about-john.txt \   # Embed text file
        bookmarks:=@bookmarks.json      # Embed JSON file


.. code-block:: http

    PUT /person/1 HTTP/1.1
    Accept: application/json, */*
    Content-Type: application/json
    Host: api.example.com

    {
        "age": 29,
        "hobbies": [
            "http",
            "pies"
        ],
        "description": "John is a nice guy who likes pies.",
        "married": false,
        "name": "John",
        "bookmarks": {
            "HTTPie": "https://httpie.org",
        }
    }


Please note that with this syntax the command gets unwieldy when sending
complex data. In that case it's always better to use `redirected input`_:

.. code-block:: bash

    $ http POST api.example.com/person/1 < person.json


Forms
=====

Submitting forms is very similar to sending `JSON`_ requests. Often the only
difference is in adding the ``--form, -f`` option, which ensures that
data fields are serialized as, and ``Content-Type`` is set to,
``application/x-www-form-urlencoded; charset=utf-8``. It is possible to make
form data the implicit content type instead of JSON
via the `config`_ file.


Regular forms
-------------

.. code-block:: bash

    $ http --form POST api.example.org/person/1 name='John Smith'


.. code-block:: http

    POST /person/1 HTTP/1.1
    Content-Type: application/x-www-form-urlencoded; charset=utf-8

    name=John+Smith


File upload forms
-----------------

If one or more file fields is present, the serialization and content type is
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

Note that ``@`` is used to simulate a file upload form field, whereas
``=@`` just embeds the file content as a regular text field value.


HTTP headers
============

To set custom headers you can use the ``Header:Value`` notation:

.. code-block:: bash

    $ http example.org  User-Agent:Bacon/1.0  'Cookie:valued-visitor=yes;foo=bar'  \
        X-Foo:Bar  Referer:https://httpie.org/


.. code-block:: http

    GET / HTTP/1.1
    Accept: */*
    Accept-Encoding: gzip, deflate
    Cookie: valued-visitor=yes;foo=bar
    Host: example.org
    Referer: https://httpie.org/
    User-Agent: Bacon/1.0
    X-Foo: Bar


Default request headers
-----------------------

There are a couple of default headers that HTTPie sets:

.. code-block:: http

    GET / HTTP/1.1
    Accept: */*
    Accept-Encoding: gzip, deflate
    User-Agent: HTTPie/<version>
    Host: <taken-from-URL>



Any of these except ``Host`` can be overwritten and some of them unset.



Empty headers and header un-setting
-----------------------------------

To unset a previously specified header
(such a one of the default headers), use ``Header:``:


.. code-block:: bash

    $ http httpbin.org/headers Accept: User-Agent:


To send a header with an empty value, use ``Header;``:


.. code-block:: bash

    $ http httpbin.org/headers 'Header;'


Limiting response headers
-------------------------

The ``--max-headers=n`` options allows you to control the number of headers
HTTPie reads before giving up (the default ``0``, i.e., there’s no limit).


.. code-block:: bash

    $ http --max-headers=100 httpbin.org/get



Cookies
=======

HTTP clients send cookies to the server as regular `HTTP headers`_. That means,
HTTPie does not offer any special syntax for specifying cookies — the usual
``Header:Value`` notation is used:


Send a single cookie:

.. code-block:: bash

    $ http example.org Cookie:sessionid=foo

.. code-block:: http

    GET / HTTP/1.1
    Accept: */*
    Accept-Encoding: gzip, deflate
    Connection: keep-alive
    Cookie: sessionid=foo
    Host: example.org
    User-Agent: HTTPie/0.9.9


Send multiple cookies
(note the header is quoted to prevent the shell from interpreting the ``;``):

.. code-block:: bash

    $ http example.org 'Cookie:sessionid=foo;another-cookie=bar'

.. code-block:: http

    GET / HTTP/1.1
    Accept: */*
    Accept-Encoding: gzip, deflate
    Connection: keep-alive
    Cookie: sessionid=foo;another-cookie=bar
    Host: example.org
    User-Agent: HTTPie/0.9.9


If you often deal with cookies in your requests, then chances are you'd appreciate
the `sessions`_ feature.


Authentication
==============

The currently supported authentication schemes are Basic and Digest
(see `auth plugins`_ for more). There are two flags that control authentication:

===================     ======================================================
``--auth, -a``          Pass a ``username:password`` pair as
                        the argument. Or, if you only specify a username
                        (``-a username``), you'll be prompted for
                        the password before the request is sent.
                        To send an empty password, pass ``username:``.
                        The ``username:password@hostname`` URL syntax is
                        supported as well (but credentials passed via ``-a``
                        have higher priority).

``--auth-type, -A``     Specify the auth mechanism. Possible values are
                        ``basic`` and ``digest``. The default value is
                        ``basic`` so it can often be omitted.
===================     ======================================================



Basic auth
----------


.. code-block:: bash

    $ http -a username:password example.org


Digest auth
-----------


.. code-block:: bash

    $ http -A digest -a username:password example.org


Password prompt
---------------

.. code-block:: bash

    $ http -a username example.org


``.netrc``
----------

Authentication information from your ``~/.netrc``
file is by default honored as well.

For example:

.. code-block:: bash

    $ cat ~/.netrc
    machine httpbin.org
    login httpie
    password test

.. code-block:: bash

    $ http httpbin.org/basic-auth/httpie/test
    HTTP/1.1 200 OK
    [...]

This can be disable with the ``--ignore-netrc`` option:

.. code-block:: bash

    $ http --ignore-netrc httpbin.org/basic-auth/httpie/test
    HTTP/1.1 401 UNAUTHORIZED
    [...]


Auth plugins
------------

Additional authentication mechanism can be installed as plugins.
They can be found on the `Python Package Index <https://pypi.python.org/pypi?%3Aaction=search&term=httpie&submit=search>`_.
Here's a few picks:

* `httpie-api-auth <https://github.com/pd/httpie-api-auth>`_: ApiAuth
* `httpie-aws-auth <https://github.com/httpie/httpie-aws-auth>`_: AWS / Amazon S3
* `httpie-edgegrid <https://github.com/akamai-open/httpie-edgegrid>`_: EdgeGrid
* `httpie-hmac-auth <https://github.com/guardian/httpie-hmac-auth>`_: HMAC
* `httpie-jwt-auth <https://github.com/teracyhq/httpie-jwt-auth>`_: JWTAuth (JSON Web Tokens)
* `httpie-negotiate <https://github.com/ndzou/httpie-negotiate>`_: SPNEGO (GSS Negotiate)
* `httpie-ntlm <https://github.com/httpie/httpie-ntlm>`_: NTLM (NT LAN Manager)
* `httpie-oauth <https://github.com/httpie/httpie-oauth>`_: OAuth
* `requests-hawk <https://github.com/mozilla-services/requests-hawk>`_: Hawk

If HTTPie is not finding your installed plugins then you may need to set the `extra_site_dirs`_
config option.


HTTP redirects
==============

By default, HTTP redirects are not followed and only the first
response is shown:


.. code-block:: bash

    $ http httpbin.org/redirect/3


Follow ``Location``
-------------------

To instruct HTTPie to follow the ``Location`` header of ``30x`` responses
and show the final response instead, use the ``--follow, -F`` option:


.. code-block:: bash

    $ http --follow httpbin.org/redirect/3


Showing intermediary redirect responses
---------------------------------------

If you additionally wish to see the intermediary requests/responses,
then use the ``--all`` option as well:


.. code-block:: bash

    $ http --follow --all httpbin.org/redirect/3



Limiting maximum redirects followed
-----------------------------------

To change the default limit of maximum ``30`` redirects, use the
``--max-redirects=<limit>`` option:


.. code-block:: bash

    $ http --follow --all --max-redirects=5 httpbin.org/redirect/3


Proxies
=======

You can specify proxies to be used through the ``--proxy`` argument for each
protocol (which is included in the value in case of redirects across protocols):

.. code-block:: bash

    $ http --proxy=http:http://10.10.1.10:3128 --proxy=https:https://10.10.1.10:1080 example.org


With Basic authentication:

.. code-block:: bash

    $ http --proxy=http:http://user:pass@10.10.1.10:3128 example.org


Environment variables
---------------------

You can also configure proxies by environment variables ``ALL_PROXY``,
``HTTP_PROXY`` and ``HTTPS_PROXY``, and the underlying Requests library will
pick them up as well. If you want to disable proxies configured through
the environment variables for certain hosts, you can specify them in ``NO_PROXY``.

In your ``~/.bash_profile``:

.. code-block:: bash

 export HTTP_PROXY=http://10.10.1.10:3128
 export HTTPS_PROXY=https://10.10.1.10:1080
 export NO_PROXY=localhost,example.com


SOCKS
-----

Homebrew-installed HTTPie comes with SOCKS proxy support out of the box.
To enable SOCKS proxy support for non-Homebrew  installations, you'll
might need to install ``requests[socks]`` manually using ``pip``:


.. code-block:: bash

    $ pip install -U requests[socks]

Usage is the same as for other types of `proxies`_:

.. code-block:: bash

    $ http --proxy=http:socks5://user:pass@host:port --proxy=https:socks5://user:pass@host:port example.org


HTTPS
=====


Server SSL certificate verification
-----------------------------------

To skip the host's SSL certificate verification, you can pass ``--verify=no``
(default is ``yes``):

.. code-block:: bash

    $ http --verify=no https://example.org


Custom CA bundle
----------------

You can also use ``--verify=<CA_BUNDLE_PATH>`` to set a custom CA bundle path:

.. code-block:: bash

    $ http --verify=/ssl/custom_ca_bundle https://example.org



Client side SSL certificate
---------------------------
To use a client side certificate for the SSL communication, you can pass
the path of the cert file with ``--cert``:

.. code-block:: bash

    $ http --cert=client.pem https://example.org


If the private key is not contained in the cert file you may pass the
path of the key file with ``--cert-key``:

.. code-block:: bash

    $ http --cert=client.crt --cert-key=client.key https://example.org


SSL version
-----------

Use the ``--ssl=<PROTOCOL>`` to specify the desired protocol version to use.
This will default to SSL v2.3 which will negotiate the highest protocol that both
the server and your installation of OpenSSL support. The available protocols
are ``ssl2.3``, ``ssl3``, ``tls1``, ``tls1.1``, ``tls1.2``, ``tls1.3``. (The actually
available set of protocols may vary depending on your OpenSSL installation.)

.. code-block:: bash

    # Specify the vulnerable SSL v3 protocol to talk to an outdated server:
    $ http --ssl=ssl3 https://vulnerable.example.org


Output options
==============

By default, HTTPie only outputs the final response and the whole response
message is printed (headers as well as the body). You can control what should
be printed via several options:

=================   =====================================================
``--headers, -h``   Only the response headers are printed.
``--body, -b``      Only the response body is printed.
``--verbose, -v``   Print the whole HTTP exchange (request and response).
                    This option also enables ``--all`` (see below).
``--print, -p``     Selects parts of the HTTP exchange.
=================   =====================================================

``--verbose`` can often be useful for debugging the request and generating
documentation examples:

.. code-block:: bash

    $ http --verbose PUT httpbin.org/put hello=world
    PUT /put HTTP/1.1
    Accept: application/json, */*
    Accept-Encoding: gzip, deflate
    Content-Type: application/json
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


What parts of the HTTP exchange should be printed
-------------------------------------------------

All the other `output options`_ are under the hood just shortcuts for
the more powerful ``--print, -p``. It accepts a string of characters each
of which represents a specific part of the HTTP exchange:

==========  ==================
Character   Stands for
==========  ==================
``H``       request headers
``B``       request body
``h``       response headers
``b``       response body
==========  ==================

Print request and response headers:

.. code-block:: bash

    $ http --print=Hh PUT httpbin.org/put hello=world


Viewing intermediary requests/responses
---------------------------------------

To see all the HTTP communication, i.e. the final request/response as
well as any possible  intermediary requests/responses, use the ``--all``
option. The intermediary HTTP communication include followed redirects
(with ``--follow``), the first unauthorized request when HTTP digest
authentication is used (``--auth=digest``), etc.

.. code-block:: bash

    # Include all responses that lead to the final one:
    $ http --all --follow httpbin.org/redirect/3


The intermediary requests/response are by default formatted according to
``--print, -p`` (and its shortcuts described above). If you'd like to change
that, use the ``--history-print, -P`` option. It takes the same
arguments as ``--print, -p`` but applies to the intermediary requests only.


.. code-block:: bash

    # Print the intermediary requests/responses differently than the final one:
    $ http -A digest -a foo:bar --all -p Hh -P H httpbin.org/digest-auth/auth/foo/bar


Conditional body download
-------------------------

As an optimization, the response body is downloaded from the server
only if it's part of the output. This is similar to performing a ``HEAD``
request, except that it applies to any HTTP method you use.

Let's say that there is an API that returns the whole resource when it is
updated, but you are only interested in the response headers to see the
status code after an update:

.. code-block:: bash

    $ http --headers PATCH example.org/Really-Huge-Resource name='New Name'


Since we are only printing the HTTP headers here, the connection to the server
is closed as soon as all the response headers have been received.
Therefore, bandwidth and time isn't wasted downloading the body
which you don't care about. The response headers are downloaded always,
even if they are not part of the output


Redirected Input
================

The universal method for passing request data is through redirected ``stdin``
(standard input)—piping. Such data is buffered and then with no further
processing used as the request body. There are multiple useful ways to use
piping:

Redirect from a file:

.. code-block:: bash

    $ http PUT example.com/person/1 X-API-Token:123 < person.json


Or the output of another program:

.. code-block:: bash

    $ grep '401 Unauthorized' /var/log/httpd/error_log | http POST example.org/intruders


You can use ``echo`` for simple data:

.. code-block:: bash

    $ echo '{"name": "John"}' | http PATCH example.com/person/1 X-API-Token:123


You can also use a Bash *here string*:

.. code-block:: bash

    $ http example.com/ <<<'{"name": "John"}'


You can even pipe web services together using HTTPie:

.. code-block:: bash

    $ http GET https://api.github.com/repos/jakubroztocil/httpie | http POST httpbin.org/post


You can use ``cat`` to enter multiline data on the terminal:

.. code-block:: bash

    $ cat | http POST example.com
    <paste>
    ^D


.. code-block:: bash

    $ cat | http POST example.com/todos Content-Type:text/plain
    - buy milk
    - call parents
    ^D


On OS X, you can send the contents of the clipboard with ``pbpaste``:

.. code-block:: bash

    $ pbpaste | http PUT example.com


Passing data through ``stdin`` cannot be combined with data fields specified
on the command line:


.. code-block:: bash

    $ echo 'data' | http POST example.org more=data   # This is invalid


To prevent HTTPie from reading ``stdin`` data you can use the
``--ignore-stdin`` option.


Request data from a filename
----------------------------

An alternative to redirected ``stdin`` is specifying a filename (as
``@/path/to/file``) whose content is used as if it came from ``stdin``.

It has the advantage that the ``Content-Type``
header is automatically set to the appropriate value based on the
filename extension. For example, the following request sends the
verbatim contents of that XML file with ``Content-Type: application/xml``:

.. code-block:: bash

    $ http PUT httpbin.org/put @/data/file.xml


Terminal output
===============

HTTPie does several things by default in order to make its terminal output
easy to read.


Colors and formatting
---------------------

Syntax highlighting is applied to HTTP headers and bodies (where it makes
sense). You can choose your preferred color scheme via the ``--style`` option
if you don't like the default one (see ``$ http --help`` for the possible
values).

Also, the following formatting is applied:

* HTTP headers are sorted by name.
* JSON data is indented, sorted by keys, and unicode escapes are converted
  to the characters they represent.

One of these options can be used to control output processing:

====================   ========================================================
``--pretty=all``       Apply both colors and formatting.
                       Default for terminal output.
``--pretty=colors``    Apply colors.
``--pretty=format``    Apply formatting.
``--pretty=none``      Disables output processing.
                       Default for redirected output.
====================   ========================================================

Binary data
-----------

Binary data is suppressed for terminal output, which makes it safe to perform
requests to URLs that send back binary data. Binary data is suppressed also in
redirected, but prettified output. The connection is closed as soon as we know
that the response body is binary,

.. code-block:: bash

    $ http example.org/Movie.mov


You will nearly instantly see something like this:

.. code-block:: http

    HTTP/1.1 200 OK
    Accept-Ranges: bytes
    Content-Encoding: gzip
    Content-Type: video/quicktime
    Transfer-Encoding: chunked

    +-----------------------------------------+
    | NOTE: binary data not shown in terminal |
    +-----------------------------------------+


Redirected output
=================

HTTPie uses a different set of defaults for redirected output than for
`terminal output`_. The differences being:

* Formatting and colors aren't applied (unless ``--pretty`` is specified).
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


Force colorizing and formatting, and show both the request and the response in
``less`` pager:

.. code-block:: bash

    $ http --pretty=all --verbose example.org | less -R


The ``-R`` flag tells ``less`` to interpret color escape sequences included
HTTPie`s output.

You can create a shortcut for invoking HTTPie with colorized and paged output
by adding the following to your ``~/.bash_profile``:

.. code-block:: bash

    function httpless {
        # `httpless example.org'
        http --pretty=all --print=hb "$@" | less -R;
    }


Download mode
=============

HTTPie features a download mode in which it acts similarly to ``wget``.

When enabled using the ``--download, -d`` flag, response headers are printed to
the terminal (``stderr``), and a progress bar is shown while the response body
is being saved to a file.

.. code-block:: bash

    $ http --download https://github.com/jakubroztocil/httpie/archive/master.tar.gz

.. code-block:: http

    HTTP/1.1 200 OK
    Content-Disposition: attachment; filename=httpie-master.tar.gz
    Content-Length: 257336
    Content-Type: application/x-gzip

    Downloading 251.30 kB to "httpie-master.tar.gz"
    Done. 251.30 kB in 2.73862s (91.76 kB/s)


Downloaded filename
--------------------

There are three mutually exclusive ways through which HTTPie determines
the output filename (with decreasing priority):

1. You can explicitly provide it via ``--output, -o``.
   The file gets overwritten if it already exists
   (or appended to with ``--continue, -c``).
2. The server may specify the filename in the optional ``Content-Disposition``
   response header. Any leading dots are stripped from a server-provided filename.
3. The last resort HTTPie uses is to generate the filename from a combination
   of the request URL and the response ``Content-Type``.
   The initial URL is always used as the basis for
   the generated filename — even if there has been one or more redirects.


To prevent data loss by overwriting, HTTPie adds a unique numerical suffix to the
filename when necessary (unless specified with ``--output, -o``).


Piping while downloading
------------------------

You can also redirect the response body to another program while the response
headers and progress are still shown in the terminal:

.. code-block:: bash

    $ http -d https://github.com/jakubroztocil/httpie/archive/master.tar.gz |  tar zxf -



Resuming downloads
------------------

If ``--output, -o`` is specified, you can resume a partial download using the
``--continue, -c`` option. This only works with servers that support
``Range`` requests and ``206 Partial Content`` responses. If the server doesn't
support that, the whole file will simply be downloaded:

.. code-block:: bash

    $ http -dco file.zip example.org/file

Other notes
-----------

* The ``--download`` option only changes how the response body is treated.
* You can still set custom headers, use sessions, ``--verbose, -v``, etc.
* ``--download`` always implies ``--follow`` (redirects are followed).
* HTTPie exits with status code ``1`` (error) if the body hasn't been fully
  downloaded.
* ``Accept-Encoding`` cannot be set with ``--download``.


Streamed responses
==================

Responses are downloaded and printed in chunks which allows for streaming
and large file downloads without using too much memory. However, when
`colors and formatting`_ is applied, the whole response is buffered and only
then processed at once.


Disabling buffering
-------------------

You can use the ``--stream, -S`` flag to make two things happen:

1. The output is flushed in much smaller chunks without any buffering,
   which makes HTTPie behave kind of like ``tail -f`` for URLs.

2. Streaming becomes enabled even when the output is prettified: It will be
   applied to each line of the response and flushed immediately. This makes
   it possible to have a nice output for long-lived requests, such as one
   to the Twitter streaming API.


Examples use cases
------------------

Prettified streamed response:

.. code-block:: bash

    $ http --stream -f -a YOUR-TWITTER-NAME https://stream.twitter.com/1/statuses/filter.json track='Justin Bieber'


Streamed output by small chunks alá ``tail -f``:

.. code-block:: bash

    # Send each new tweet (JSON object) mentioning "Apple" to another
    # server as soon as it arrives from the Twitter streaming API:
    $ http --stream -f -a YOUR-TWITTER-NAME https://stream.twitter.com/1/statuses/filter.json track=Apple \
    | while read tweet; do echo "$tweet" | http POST example.org/tweets ; done

Sessions
========

By default, every request HTTPie makes is completely independent of any
previous ones to the same host.


However, HTTPie also supports persistent
sessions via the ``--session=SESSION_NAME_OR_PATH`` option. In a session,
custom `HTTP headers`_ (except for the ones starting with ``Content-`` or ``If-``),
`authentication`_, and `cookies`_
(manually specified or sent by the server) persist between requests
to the same host.


.. code-block:: bash

    # Create a new session
    $ http --session=/tmp/session.json example.org API-Token:123

    # Re-use an existing session — API-Token will be set:
    $ http --session=/tmp/session.json example.org


All session data, including credentials, cookie data,
and custom headers are stored in plain text.
That means session files can also be created and edited manually in a text
editor—they are regular JSON. It also means that they can be read by anyone
who has access to the session file.


Named sessions
--------------


You can create one or more named session per host. For example, this is how
you can create a new session named ``user1`` for ``example.org``:

.. code-block:: bash

    $ http --session=user1 -a user1:password example.org X-Foo:Bar

From now on, you can refer to the session by its name. When you choose to
use the session again, any previously specified authentication or HTTP headers
will automatically be set:

.. code-block:: bash

    $ http --session=user1 example.org

To create or reuse a different session, simple specify a different name:

.. code-block:: bash

    $ http --session=user2 -a user2:password example.org X-Bar:Foo

Named sessions' data is stored in JSON files in the directory
``~/.httpie/sessions/<host>/<name>.json``
(``%APPDATA%\httpie\sessions\<host>\<name>.json`` on Windows).


Anonymous sessions
------------------

Instead of a name, you can also directly specify a path to a session file. This
allows for sessions to be re-used across multiple hosts:

.. code-block:: bash

    $ http --session=/tmp/session.json example.org
    $ http --session=/tmp/session.json admin.example.org
    $ http --session=~/.httpie/sessions/another.example.org/test.json example.org
    $ http --session-read-only=/tmp/session.json example.org


Readonly session
----------------

To use an existing session file without updating it from the request/response
exchange once it is created, specify the session name via
``--session-read-only=SESSION_NAME_OR_PATH`` instead.


Config
======

HTTPie uses a simple JSON config file.



Config file location
--------------------


The default location of the configuration file is ``~/.httpie/config.json``
(or ``%APPDATA%\httpie\config.json`` on Windows). The config directory
location can be changed by setting the ``HTTPIE_CONFIG_DIR``
environment variable. To view the exact location run ``http --debug``.

Configurable options
--------------------

The JSON file contains an object with the following keys:


``default_options``
~~~~~~~~~~~~~~~~~~~


An ``Array`` (by default empty) of default options that should be applied to
every invocation of HTTPie.

For instance, you can use this option to change the default style and output
options: ``"default_options": ["--style=fruity", "--body"]`` Another useful
default option could be ``"--session=default"`` to make HTTPie always
use `sessions`_ (one named ``default`` will automatically be used).
Or you could change the implicit request content type from JSON to form by
adding ``--form`` to the list.


``extra_site_dirs``
~~~~~~~~~~~~~~~~~~~

An ``Array`` (by default empty) of directories that will be appended to Pythons
``sys.path``. This is helpful when you want to use a plugin from outside the
default ``sys.path``.

Perhaps the most common use will be on macOS when HTTPie is installed via
Homebrew and plugins are installed via ``pip``, you'll need to set
``extra_site_dirs`` to something like the example below so that HTTPie can find
your plugins:

.. code-block:: json

    "extra_site_dirs": [
        "/usr/local/lib/python3.7/site-packages",
        "~/Library/Python/3.7/lib/python/site-packages"
    ]

If you are having trouble with HTTPie not finding your plugins then run
``http --debug`` to see the list of dirs being searched, the list of loaded
plugins and what dir each comes from.


``__meta__``
~~~~~~~~~~~~

HTTPie automatically stores some of its metadata here. Please do not change.



Un-setting previously specified options
---------------------------------------

Default options from the config file, or specified any other way,
can be unset for a particular invocation via ``--no-OPTION`` arguments passed
on the command line (e.g., ``--no-style`` or ``--no-session``).



Scripting
=========

When using HTTPie from shell scripts, it can be handy to set the
``--check-status`` flag. It instructs HTTPie to exit with an error if the
HTTP status is one of ``3xx``, ``4xx``, or ``5xx``. The exit status will
be ``3`` (unless ``--follow`` is set), ``4``, or ``5``,
respectively.

.. code-block:: bash

    #!/bin/bash

    if http --check-status --ignore-stdin --timeout=2.5 HEAD example.org/health &> /dev/null; then
        echo 'OK!'
    else
        case $? in
            2) echo 'Request timed out!' ;;
            3) echo 'Unexpected HTTP 3xx Redirection!' ;;
            4) echo 'HTTP 4xx Client Error!' ;;
            5) echo 'HTTP 5xx Server Error!' ;;
            6) echo 'Exceeded --max-redirects=<n> redirects!' ;;
            *) echo 'Other Error!' ;;
        esac
    fi


Best practices
--------------

The default behaviour of automatically reading ``stdin`` is typically not
desirable during non-interactive invocations. You most likely want to
use the ``--ignore-stdin`` option to disable it.

It is a common gotcha that without this option HTTPie seemingly hangs.
What happens is that when HTTPie is invoked for example from a cron job,
``stdin`` is not connected to a terminal.
Therefore, rules for `redirected input`_ apply, i.e., HTTPie starts to read it
expecting that the request body will be passed through.
And since there's no data nor ``EOF``, it will be stuck. So unless you're
piping some data to HTTPie, this flag should be used in scripts.

Also, it might be good to set a connection ``--timeout`` limit to prevent
your program from hanging if the server never responds.



Meta
====

Interface design
----------------

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

The two modes, ``--pretty=all`` (default for terminal) and ``--pretty=none``
(default for redirected output), allow for both user-friendly interactive use
and usage from scripts, where HTTPie serves as a generic HTTP client.

As HTTPie is still under heavy development, the existing command line
syntax and some of the ``--OPTIONS`` may change slightly before
HTTPie reaches its final version ``1.0``. All changes are recorded in the
`change log`_.



User support
------------

Please use the following support channels:

* `GitHub issues <https://github.com/jkbr/httpie/issues>`_
  for bug reports and feature requests.
* `Our Gitter chat room <https://gitter.im/jkbrzt/httpie>`_
  to ask questions, discuss features, and for general discussion.
* `StackOverflow <https://stackoverflow.com>`_
  to ask questions (please make sure to use the
  `httpie <https://stackoverflow.com/questions/tagged/httpie>`_ tag).
* Tweet directly to `@clihttp <https://twitter.com/clihttp>`_.
* You can also tweet directly to `@jakubroztocil`_.


Related projects
----------------

Dependencies
~~~~~~~~~~~~

Under the hood, HTTPie uses these two amazing libraries:

* `Requests <https://python-requests.org>`_
  — Python HTTP library for humans
* `Pygments <https://pygments.org/>`_
  — Python syntax highlighter


HTTPie friends
~~~~~~~~~~~~~~

HTTPie plays exceptionally well with the following tools:

* `jq <https://stedolan.github.io/jq/>`_
  — CLI JSON processor that
  works great in conjunction with HTTPie
* `http-prompt <https://github.com/eliangcs/http-prompt>`_
  —  interactive shell for HTTPie featuring autocomplete
  and command syntax highlighting


Alternatives
~~~~~~~~~~~~

* `httpcat <https://github.com/jakubroztocil/httpcat>`_ — a lower-level sister utility
  of HTTPie for constructing raw HTTP requests on the command line.
* `curl <https://curl.haxx.se>`_ — a "Swiss knife" command line tool and
  an exceptional library for transferring data with URLs.


Contributing
------------

See `CONTRIBUTING.rst <https://github.com/jakubroztocil/httpie/blob/master/CONTRIBUTING.rst>`_.


Change log
----------

See `CHANGELOG <https://github.com/jakubroztocil/httpie/blob/master/CHANGELOG.rst>`_.


Artwork
-------

* `Logo <https://github.com/claudiatd/httpie-artwork>`_ by `Cláudia Delgado <https://github.com/claudiatd>`_.
* `Animation <https://raw.githubusercontent.com/jakubroztocil/httpie/master/httpie.gif>`_ by `Allen Smith <https://github.com/loranallensmith>`_ of GitHub.



Licence
-------

BSD-3-Clause: `LICENSE <https://github.com/jakubroztocil/httpie/blob/master/LICENSE>`_.



Authors
-------

`Jakub Roztocil`_  (`@jakubroztocil`_) created HTTPie and `these fine people`_
have contributed.


.. _pip: https://pip.pypa.io/en/stable/installing/
.. _Github API: https://developer.github.com/v3/issues/comments/#create-a-comment
.. _these fine people: https://github.com/jakubroztocil/httpie/contributors
.. _Jakub Roztocil: https://roztocil.co
.. _@jakubroztocil: https://twitter.com/jakubroztocil


.. |pypi| image:: https://img.shields.io/pypi/v/httpie.svg?style=flat-square&label=latest%20stable%20version
    :target: https://pypi.python.org/pypi/httpie
    :alt: Latest version released on PyPi

.. |coverage| image:: https://img.shields.io/codecov/c/github/jakubroztocil/httpie?style=flat-square
    :target: https://codecov.io/gh/jakubroztocil/httpie
    :alt: Test coverage

.. |build| image:: https://github.com/jakubroztocil/httpie/workflows/Build/badge.svg
    :target: https://github.com/jakubroztocil/httpie/actions
    :alt: Build status of the master branch on Mac/Linux/Windows

.. |gitter| image:: https://img.shields.io/gitter/room/jkbrzt/httpie.svg?style=flat-square
    :target: https://gitter.im/jkbrzt/httpie
    :alt: Chat on Gitter

.. |downloads| image:: https://pepy.tech/badge/httpie
    :target: https://pepy.tech/project/httpie
    :alt: Download count

