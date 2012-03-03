## HTTPie: cURL for humans

HTTPie is a CLI frontend for [python-requests](http://python-requests.org) built out of frustration. It provides an `http` command that can be used to easily issue HTTP requests. It is meant to be used by humans to interact with HTTP-based APIs and web servers. The response headers are colorized and the body is syntax-highlighted if its `Content-Type` is known to [Pygments](http://pygments.org/) (unless the output is redirected).

![httpie](https://github.com/jkbr/httpie/raw/master/httpie.png)


### Installation

    pip install httpie


### Usage

    http [flags] METHOD URL [header:value | data-field-name=value]*

The default request `Content-Type` is `application/json` and data fields are automatically serialized as a JSON `Object`, so this:

    http PATCH api.example.com/person/1 X-API-Token:123 name=John email=john@example.org

Will issue the following request:

    PATCH /person/1 HTTP/1.1
    User-Agent: HTTPie/0.1
    X-API-Token: 123
    Content-Type: application/json; charset=utf-8

    {"name": "John", "email": "john@example.org"}

You can use the `--form` flag to set `Content-Type` and serialize the data as `application/x-www-form-urlencoded`.

The data to be sent can also be passed via `stdin`:

    http PUT api.example.com/person/1 X-API-Token:123 < person.json

Most of the flags mirror the arguments you would use with `requests.request`. See `http -h`:

    usage: http [-h] [--json | --form] [--traceback] [--ugly] [--headers | --body]
                [--style STYLE] [--auth AUTH] [--verify VERIFY] [--proxy PROXY]
                [--allow-redirects] [--file PATH] [--timeout TIMEOUT]
                method URL [item [item ...]]

    HTTPie - cURL for humans.

    positional arguments:
      method                HTTP method to be used for the request (GET, POST,
                            PUT, DELETE, PATCH, ...).
      URL                   Protocol defaults to http:// if the URL does not
                            include it.
      item                  HTTP header (key:value) or data field (key=value)

    optional arguments:
      -h, --help            show this help message and exit
      --json, -j            Serialize data items as a JSON object and set Content-
                            Type to application/json, if not specified.
      --form, -f            Serialize data items as form values and set Content-
                            Type to application/x-www-form-urlencoded, if not
                            specified.
      --traceback           Print a full exception traceback should one be raised
                            by `requests`.
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
