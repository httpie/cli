<div class='hidden-website'>

# HTTPie documentation

</div>

HTTPie (pronounced _aitch-tee-tee-pie_) is a command-line HTTP client.
Its goal is to make CLI interaction with web services as human-friendly as possible.
HTTPie is designed for testing, debugging, and generally interacting with APIs & HTTP servers.
The `http` & `https` commands allow for creating and sending arbitrary HTTP requests.
They use simple and natural syntax and provide formatted and colorized output.

<div class='hidden-website'>

## About this document

This documentation is best viewed at [httpie.io/docs](https://httpie.org/docs).

You can select your corresponding HTTPie version as well as run examples directly from the browser using a [termible.io](https://termible.io?utm_source=httpie-readme) embedded terminal.

If you are reading this on GitHub, then this text covers the current *development* version.
You are invited to submit fixes and improvements to the docs by editing [this file](https://github.com/httpie/httpie/blob/master/docs/README.md).

</div>

## Main features

- Expressive and intuitive syntax
- Formatted and colorized terminal output
- Built-in JSON support
- Forms and file uploads
- HTTPS, proxies, and authentication
- Arbitrary request data
- Custom headers
- Persistent sessions
- Wget-like downloads
- Linux, macOS, Windows, and FreeBSD support
- Plugins
- Documentation
- Test coverage

## Installation

<div data-installation-instructions>

<!--
THE INSTALLATION SECTION IS GENERATED

Do not edit here, but in docs/installation/.

-->

- [Universal](#universal)
- [macOS](#macos)
- [Windows](#windows)
- [Linux](#linux)
- [FreeBSD](#freebsd)

### Universal

#### PyPi

Please make sure you have Python 3.6 or newer (`python --version`).

```bash
# Install httpie
$ python -m pip install --upgrade pip wheel
$ python -m pip install httpie
```

```bash
# Upgrade httpie
$ python -m pip install --upgrade pip wheel
$ python -m pip install --upgrade httpie
```

### macOS

#### Homebrew

To install [Homebrew](https://brew.sh/), see [its installation](https://docs.brew.sh/Installation).

```bash
# Install httpie
$ brew update
$ brew install httpie
```

```bash
# Upgrade httpie
$ brew update
$ brew upgrade httpie
```

#### MacPorts

To install [MacPorts](https://www.macports.org/), see [its installation](https://www.macports.org/install.php).

```bash
# Install httpie
$ port selfupdate
$ port install httpie
```

```bash
# Upgrade httpie
$ port selfupdate
$ port upgrade httpie
```

#### Spack (macOS)

To install [Spack](https://spack.readthedocs.io/en/latest/index.html), see [its installation](https://spack.readthedocs.io/en/latest/getting_started.html#installation).

```bash
# Install httpie
$ spack install httpie
```

```bash
# Upgrade httpie
$ spack install httpie
```

### Windows

#### Chocolatey

To install [Chocolatey](https://chocolatey.org/), see [its installation](https://chocolatey.org/install).

```bash
# Install httpie
$ choco install httpie
```

```bash
# Upgrade httpie
$ choco upgrade httpie
```

### Linux

#### Snapcraft (Linux)

To install [Snapcraft](https://snapcraft.io/), see [its installation](https://snapcraft.io/docs/installing-snapd).

```bash
# Install httpie
$ snap install httpie
```

```bash
# Upgrade httpie
$ snap refresh httpie
```

#### Linuxbrew

To install [Linuxbrew](https://docs.brew.sh/Homebrew-on-Linux), see [its installation](https://docs.brew.sh/Homebrew-on-Linux#install).

```bash
# Install httpie
$ brew update
$ brew install httpie
```

```bash
# Upgrade httpie
$ brew update
$ brew upgrade httpie
```

#### Debian and Ubuntu

Also works for other Debian-derived distributions like MX Linux, Linux Mint, deepin, Pop!_OS, KDE neon, Zorin OS, elementary OS, Kubuntu, Devuan, Linux Lite, Peppermint OS, Lubuntu, antiX, Xubuntu, etc.

```bash
# Install httpie
$ apt update
$ apt install httpie
```

```bash
# Upgrade httpie
$ apt update
$ apt upgrade httpie
```

#### Fedora

```bash
# Install httpie
$ dnf update
$ dnf install httpie
```

```bash
# Upgrade httpie
$ dnf update
$ dnf upgrade httpie
```

#### CentOS and RHEL

Also works for other RHEL-derived distributions like ClearOS, Oracle Linux, etc.

```bash
# Install httpie
$ yum update
$ yum install epel-release
$ yum install httpie
```

```bash
# Upgrade httpie
$ yum update
$ yum upgrade httpie
```

#### Alpine Linux

```bash
# Install httpie
$ apk update
$ apk add httpie
```

```bash
# Upgrade httpie
$ apk update
$ apk add --upgrade httpie
```

#### Gentoo

```bash
# Install httpie
$ emerge --sync
$ emerge httpie
```

```bash
# Upgrade httpie
$ emerge --sync
$ emerge --update httpie
```

#### Arch Linux

Also works for other Arch-derived distributions like ArcoLinux, EndeavourOS, Artix Linux, etc.

```bash
# Install httpie
$ pacman -Sy httpie
```

```bash
# Upgrade httpie
$ pacman -Syu httpie
```

#### Void Linux

```bash
# Install httpie
$ xbps-install -Su
$ xbps-install -S httpie
```

```bash
# Upgrade httpie
$ xbps-install -Su
$ xbps-install -Su httpie
```

#### Spack (Linux)

To install [Spack](https://spack.readthedocs.io/en/latest/index.html), see [its installation](https://spack.readthedocs.io/en/latest/getting_started.html#installation).

```bash
# Install httpie
$ spack install httpie
```

```bash
# Upgrade httpie
$ spack install httpie
```

### FreeBSD

#### FreshPorts

```bash
# Install httpie
$ pkg install www/py-httpie
```

```bash
# Upgrade httpie
$ pkg upgrade www/py-httpie
```

<!-- /GENERATED SECTION -->

</div>

### Unstable version

You can also install the latest unreleased development version directly from the `master` branch on GitHub.
It is a work-in-progress of a future stable release so the experience might be not as smooth.

You can install it on Linux, macOS, Windows, or FreeBSD with `pip`:

```bash
$ python -m pip install --upgrade https://github.com/httpie/httpie/archive/master.tar.gz
```

Or on macOS, and Linux, with Homebrew:

```bash
$ brew uninstall --force httpie
$ brew install --HEAD httpie
```

And even on macOS, and Linux, with Snapcraft:

```bash
$ snap remove httpie
$ snap install httpie --edge
```

Verify that now you have the [current development version identifier](https://github.com/httpie/httpie/blob/master/httpie/__init__.py#L6) with the `.dev0` suffix, for example:

```bash
$ http --version
# 2.6.0
```

## Usage

Hello World:

```bash
$ https httpie.io/hello
```

Synopsis:

```bash
$ http [flags] [METHOD] URL [ITEM [ITEM]]
```

See also `http --help`.

### Examples

Custom [HTTP method](#http-method), [HTTP headers](#http-headers) and [JSON](#json) data:

```bash
$ http PUT pie.dev/put X-API-Token:123 name=John
```

Submitting [forms](#forms):

```bash
$ http -f POST pie.dev/post hello=World
```

See the request that is being sent using one of the [output options](#output-options):

```bash
$ http -v pie.dev/get
```

Build and print a request without sending it using [offline mode](#offline-mode):

```bash
$ http --offline pie.dev/post hello=offline
```

Use [GitHub API](https://developer.github.com/v3/issues/comments/#create-a-comment) to post a comment on an [issue](https://github.com/httpie/httpie/issues/83) with [authentication](#authentication):

```bash
$ http -a USERNAME POST https://api.github.com/repos/httpie/httpie/issues/83/comments body='HTTPie is awesome! :heart:'
```

Upload a file using [redirected input](#redirected-input):

```bash
$ http pie.dev/post < files/data.json
```

Download a file and save it via [redirected output](#redirected-output):

```bash
$ http pie.dev/image/png > image.png
```

Download a file `wget` style:

```bash
$ http --download pie.dev/image/png
```

Use named [sessions](#sessions) to make certain aspects of the communication persistent between requests to the same host:

```bash
$ http --session=logged-in -a username:password pie.dev/get API-Key:123
```

```bash
$ http --session=logged-in pie.dev/headers
```

Set a custom `Host` header to work around missing DNS records:

```bash
$ http localhost:8000 Host:example.com
```

## HTTP method

The name of the HTTP method comes right before the URL argument:

```bash
$ http DELETE pie.dev/delete
```

Which looks similar to the actual `Request-Line` that is sent:

```http
DELETE /delete HTTP/1.1
```

In addition to the standard methods (`GET`, `POST`, `HEAD`, `PUT`, `PATCH`, `DELETE`, etc.), you can use custom method names, for example:

```bash
$ http AHOY pie.dev/post
```

There are no restrictions regarding which request methods can include a body. You can send an empty `POST` request:

```bash
$ http POST pie.dev/post
```

You can also make `GET` requests contaning a body:

```bash
$ http GET pie.dev/get hello=world
```

### Optional `GET` and `POST`

The `METHOD` argument is optional, and when you don’t specify it, HTTPie defaults to:

- `GET` for requests without body
- `POST` for requests with body

Here we don’t specify any request data, so both commands will send the same `GET` request:

```bash
$ http GET pie.dev/get
```

```bash
$ http pie.dev/get
```

Here, on the other hand, we do have some data, so both commands will make the same `POST` request:

```bash
$ http POST pie.dev/post hello=world
```

```bash
$ http pie.dev/post hello=world
```

## Request URL

The only information HTTPie needs to perform a request is a URL.

The default scheme is `http://` and can be omitted from the argument:

```bash
$ http example.org
# => http://example.org
```

HTTPie also installs an `https` executable, where the default scheme is `https://`:

```bash
$ https example.org
# => https://example.org
```

### Querystring parameters

If you find yourself manually constructing URLs with querystring parameters on the terminal, you may appreciate the `param==value` syntax for appending URL parameters.

With that, you don’t have to worry about escaping the `&` separators for your shell. Additionally, any special characters in the parameter name or value get automatically URL-escaped (as opposed to the parameters specified in the full URL, which HTTPie doesn’t modify).

```bash
$ http https://api.github.com/search/repositories q==httpie per_page==1
```

```http
GET /search/repositories?q=httpie&per_page=1 HTTP/1.1
```

### URL shortcuts for `localhost`

Additionally, curl-like shorthand for localhost is supported.
This means that, for example, `:3000` would expand to `http://localhost:3000`
If the port is omitted, then port 80 is assumed.

```bash
$ http :/foo
```

```http
GET /foo HTTP/1.1
Host: localhost
```

```bash
$ http :3000/bar
```

```http
GET /bar HTTP/1.1
Host: localhost:3000
```

```bash
$ http :
```

```http
GET / HTTP/1.1
Host: localhost
```

### Other default schemes

When HTTPie is invoked as `https` then the default scheme is `https://` (`$ https example.org` will make a request to `https://example.org`).

You can also use the `--default-scheme <URL_SCHEME>` option to create shortcuts for other protocols than HTTP (possibly supported via [plugins](https://pypi.org/search/?q=httpie)). Example for the [httpie-unixsocket](https://github.com/httpie/httpie-unixsocket) plugin:

```bash
# Before
$ http http+unix://%2Fvar%2Frun%2Fdocker.sock/info
```

```bash
# Create an alias
$ alias http-unix='http --default-scheme="http+unix"'
```

```bash
# Now the scheme can be omitted
$ http-unix %2Fvar%2Frun%2Fdocker.sock/info
```

### `--path-as-is`

The standard behavior of HTTP clients is to normalize the path portion of URLs by squashing dot segments as a typically filesystem would:

```bash
$ http -v example.org/./../../etc/password
```

```http
GET /etc/password HTTP/1.1
```

The `--path-as-is` option allows you to disable this behavior:

```bash
$ http --path-as-is -v example.org/./../../etc/password
```

```http
GET /../../etc/password HTTP/1.1
```

## Request items

There are a few different *request item* types that provide a convenient mechanism for specifying HTTP headers, simple JSON and form data, files, and URL parameters.

They are key/value pairs specified after the URL. All have in common that they become part of the actual request that is sent and that their type is distinguished only by the separator used: `:`, `=`, `:=`, `==`, `@`, `=@`, and `:=@`. The ones with an `@` expect a file path as value.

|                                                    Item Type | Description                                                                                                                                                                                                            |
| -----------------------------------------------------------: | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|                                    HTTP Headers `Name:Value` | Arbitrary HTTP header, e.g. `X-API-Token:123`                                                                                                                                                                          |
|                                 URL parameters `name==value` | Appends the given name/value pair as a querystring parameter to the URL. The `==` separator is used.                                                                                                                   |
|                 Data Fields `field=value`, `field=@file.txt` | Request data fields to be serialized as a JSON object (default), to be form-encoded (with `--form, -f`), or to be serialized as `multipart/form-data` (with `--multipart`)                                             |
|                                Raw JSON fields `field:=json` | Useful when sending JSON and one or more fields need to be a `Boolean`, `Number`, nested `Object`, or an `Array`, e.g., `meals:='["ham","spam"]'` or `pies:=[1,2,3]` (note the quotes)                                 |
| File upload fields `field@/dir/file`, `field@file;type=mime` | Only available with `--form`, `-f` and `--multipart`. For example `screenshot@~/Pictures/img.png`, or `'cv@cv.txt;type=text/markdown'`. With `--form`, the presence of a file field results in a `--multipart` request |

Note that the structured data fields aren’t the only way to specify request data:
[raw request body](#raw-request-body) is a mechanism for passing arbitrary request data.

### Escaping rules

You can use `\` to escape characters that shouldn’t be used as separators (or parts thereof). For instance, `foo\==bar` will become a data key/value pair (`foo=` and `bar`) instead of a URL parameter.

Often it is necessary to quote the values, e.g. `foo='bar baz'`.

If any of the field names or headers starts with a minus (e.g. `-fieldname`), you need to place all such items after the special token `--` to prevent confusion with `--arguments`:

```bash
$ http pie.dev/post -- -name-starting-with-dash=foo -Unusual-Header:bar
```

```http
POST /post HTTP/1.1
-Unusual-Header: bar
Content-Type: application/json

{
    "-name-starting-with-dash": "foo"
}
```

## JSON

JSON is the *lingua franca* of modern web services and it is also the **implicit content type** HTTPie uses by default.

Simple example:

```bash
$ http PUT pie.dev/put name=John email=john@example.org
```

```http
PUT / HTTP/1.1
Accept: application/json, */*;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/json
Host: pie.dev

{
    "name": "John",
    "email": "john@example.org"
}
```

### Default behavior

If your command includes some data [request items](#request-items), they are serialized as a JSON object by default. HTTPie also automatically sets the following headers, both of which can be overwritten:

|         Header | Value                         |
| -------------: | ----------------------------- |
| `Content-Type` | `application/json`            |
|       `Accept` | `application/json, */*;q=0.5` |

### Explicit JSON

You can use `--json, -j` to explicitly set `Accept` to `application/json` regardless of whether you are sending data (it’s a shortcut for setting the header via the usual header notation: `http url Accept:'application/json, */*;q=0.5'`).
Additionally, HTTPie will try to detect JSON responses even when the `Content-Type` is incorrectly `text/plain` or unknown.

### Non-string JSON fields

Non-string JSON fields use the `:=` separator, which allows you to embed arbitrary JSON data into the resulting JSON object.
Additionally, text and raw JSON files can also be embedded into fields using `=@` and `:=@`:

```bash
$ http PUT pie.dev/put \
    name=John \                        # String (default)
    age:=29 \                          # Raw JSON — Number
    married:=false \                   # Raw JSON — Boolean
    hobbies:='["http", "pies"]' \      # Raw JSON — Array
    favorite:='{"tool": "HTTPie"}' \   # Raw JSON — Object
    bookmarks:=@files/data.json \      # Embed JSON file
    description=@files/text.txt        # Embed text file
```

```http
PUT /person/1 HTTP/1.1
Accept: application/json, */*;q=0.5
Content-Type: application/json
Host: pie.dev

{
    "age": 29,
    "hobbies": [
        "http",
        "pies"
    ],
    "description": "John is a nice guy who likes pies.",
    "married": false,
    "name": "John",
    "favorite": {
        "tool": "HTTPie"
    },
    "bookmarks": {
        "HTTPie": "https://httpie.org",
    }
}
```

### Raw and complex JSON

Please note that with the [request items](#request-items) data field syntax, commands can quickly become unwieldy when sending complex structures.
In such cases, it’s better to pass the full raw JSON data via [raw request body](#raw-request-body), for example:

```bash
$ echo -n '{"hello": "world"}' | http POST pie.dev/post
```

```bash
$ http --raw '{"hello": "world"}' POST pie.dev/post
```

```bash
$ http POST pie.dev/post < files/data.json
```

Furthermore, the structure syntax only allows you to send an object as the JSON document, but not an array, etc.
Here, again, the solution is to use [redirected input](#redirected-input).

## Forms

Submitting forms is very similar to sending [JSON](#json) requests.
Often the only difference is in adding the `--form, -f` option, which ensures that data fields are serialized as, and `Content-Type` is set to `application/x-www-form-urlencoded; charset=utf-8`.
It is possible to make form data the implicit content type instead of JSON via the [config](#config) file.

### Regular forms

```bash
$ http --form POST pie.dev/post name='John Smith'
```

```http
POST /post HTTP/1.1
Content-Type: application/x-www-form-urlencoded; charset=utf-8

name=John+Smith
```

### File upload forms

If one or more file fields is present, the serialization and content type is `multipart/form-data`:

```bash
$ http -f POST pie.dev/post name='John Smith' cv@~/files/data.xml
```

The request above is the same as if the following HTML form were submitted:

```html
<form enctype="multipart/form-data" method="post" action="http://example.com/jobs">
    <input type="text" name="name" />
    <input type="file" name="cv" />
</form>
```

Please note that `@` is used to simulate a file upload form field, whereas `=@` just embeds the file content as a regular text field value.

When uploading files, their content type is inferred from the file name. You can manually override the inferred content type:

```bash
$ http -f POST pie.dev/post name='John Smith' cv@'~/files/data.bin;type=application/pdf'
```

To perform a `multipart/form-data` request even without any files, use `--multipart` instead of `--form`:

```bash
$ http --multipart --offline example.org hello=world
```

```http
POST / HTTP/1.1
Content-Length: 129
Content-Type: multipart/form-data; boundary=c31279ab254f40aeb06df32b433cbccb
Host: example.org

--c31279ab254f40aeb06df32b433cbccb
Content-Disposition: form-data; name="hello"

world
--c31279ab254f40aeb06df32b433cbccb--
```

File uploads are always streamed to avoid memory issues with large files.

By default, HTTPie uses a random unique string as the multipart boundary but you can use `--boundary` to specify a custom string instead:

```bash
$ http --form --multipart --boundary=xoxo --offline example.org hello=world
```

```http
POST / HTTP/1.1
Content-Length: 129
Content-Type: multipart/form-data; boundary=xoxo
Host: example.org

--xoxo
Content-Disposition: form-data; name="hello"

world
--xoxo--
```

If you specify a custom `Content-Type` header without including the boundary bit, HTTPie will add the boundary value (explicitly specified or auto-generated) to the header automatically:

```bash
$ http --form --multipart --offline example.org hello=world Content-Type:multipart/letter
```

```http
POST / HTTP/1.1
Content-Length: 129
Content-Type: multipart/letter; boundary=c31279ab254f40aeb06df32b433cbccb
Host: example.org

--c31279ab254f40aeb06df32b433cbccb
Content-Disposition: form-data; name="hello"

world
--c31279ab254f40aeb06df32b433cbccb--
```

## HTTP headers

To set custom headers you can use the `Header:Value` notation:

```bash
$ http pie.dev/headers User-Agent:Bacon/1.0 'Cookie:valued-visitor=yes;foo=bar' \
    X-Foo:Bar Referer:https://httpie.org/
```

```http
GET /headers HTTP/1.1
Accept: */*
Accept-Encoding: gzip, deflate
Cookie: valued-visitor=yes;foo=bar
Host: pie.dev
Referer: https://httpie.org/
User-Agent: Bacon/1.0
X-Foo: Bar
```

### Default request headers

There are a couple of default headers that HTTPie sets:

```http
GET / HTTP/1.1
Accept: */*
Accept-Encoding: gzip, deflate
User-Agent: HTTPie/<version>
Host: <taken-from-URL>
```

Any of these can be overwritten and some of them unset (see below).

### Empty headers and header un-setting

To unset a previously specified header (such a one of the default headers), use `Header:`:

```bash
$ http pie.dev/headers Accept: User-Agent:
```

To send a header with an empty value, use `Header;`, with a semicolon:

```bash
$ http pie.dev/headers 'Header;'
```

### Limiting response headers

The `--max-headers=n` options allows you to control the number of headers HTTPie reads before giving up (the default `0`, i.e., there’s no limit).

```bash
$ http --max-headers=100 pie.dev/get
```

## Offline mode

Use `--offline` to construct HTTP requests without sending them anywhere.
With `--offline`, HTTPie builds a request based on the specified options and arguments, prints it to `stdout`, and then exits. It works completely offline; no network connection is ever made. This has a number of use cases, including:

Generating API documentation examples that you can copy & paste without sending a request:

```bash
$ http --offline POST server.chess/api/games API-Key:ZZZ w=magnus b=hikaru t=180 i=2
```

```bash
$ http --offline MOVE server.chess/api/games/123 API-Key:ZZZ p=b a=R1a3 t=77
```

Generating raw requests that can be sent with any other client:

```bash
# 1. save a raw request to a file:
$ http --offline POST pie.dev/post hello=world > request.http
```

```bash
# 2. send it over the wire with, for example, the fantastic netcat tool:
$ nc pie.dev 80 < request.http
```

You can also use the `--offline` mode for debugging and exploring HTTP and HTTPie, and for “dry runs”.

`--offline` has the side-effect of automatically activating `--print=HB`, i.e., both the request headers and the body
are printed. You can customize the output with the usual [output options](#output-options), with the exception where there
is no response to be printed. You can use `--offline` in combination with all the other options (e.g. `--session`).

## Cookies

HTTP clients send cookies to the server as regular [HTTP headers](#http-headers).
That means, HTTPie does not offer any special syntax for specifying cookies — the usual `Header:Value` notation is used:

Send a single cookie:

```bash
$ http pie.dev/cookies Cookie:sessionid=foo
```

```http
GET / HTTP/1.1
Accept: */*
Accept-Encoding: gzip, deflate
Connection: keep-alive
Cookie: sessionid=foo
Host: pie.dev
User-Agent: HTTPie/0.9.9
```

Send multiple cookies (note: the header is quoted to prevent the shell from interpreting the `;`):

```bash
$ http pie.dev/cookies 'Cookie:sessionid=foo;another-cookie=bar'
```

```http
GET / HTTP/1.1
Accept: */*
Accept-Encoding: gzip, deflate
Connection: keep-alive
Cookie: sessionid=foo;another-cookie=bar
Host: pie.dev
User-Agent: HTTPie/0.9.9
```

If you often deal with cookies in your requests, then you’d appreciate
the [sessions](#sessions) feature.

## Authentication

The currently supported authentication schemes are Basic and Digest (see [auth plugins](#auth-plugins) for more). There are two flags that control authentication:

|              Flag | Arguments                                                                                                                                                                                                                                                                                                                                 |
| ----------------: | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|      `--auth, -a` | Pass a `username:password` pair as the argument. Or, if you only specify a username (`-a username`), you’ll be prompted for the password before the request is sent. To send an empty password, pass `username:`. The `username:password@hostname` URL syntax is supported as well (but credentials passed via `-a` have higher priority) |
| `--auth-type, -A` | Specify the auth mechanism. Possible values are `basic`, `digest`, or the name of any [auth plugins](#auth-plugins) you have installed. The default value is `basic` so it can often be omitted                                                                                                                                           |

### Basic auth

```bash
$ http -a username:password pie.dev/basic-auth/username/password
```

### Digest auth

```bash
$ http -A digest -a username:password pie.dev/digest-auth/httpie/username/password
```

### Password prompt

```bash
$ http -a username pie.dev/basic-auth/username/password
```

### Empty password

```bash
$ http -a username: pie.dev/headers
```

### `.netrc`

Authentication information from your `~/.netrc` file is by default honored as well.

For example:

```bash
$ cat ~/.netrc
machine pie.dev
login httpie
password test
```

```bash
$ http pie.dev/basic-auth/httpie/test
HTTP/1.1 200 OK
[...]
```

This can be disabled with the `--ignore-netrc` option:

```bash
$ http --ignore-netrc pie.dev/basic-auth/httpie/test
HTTP/1.1 401 UNAUTHORIZED
[...]
```

### Auth plugins

Additional authentication mechanism can be installed as plugins.
They can be found on the [Python Package Index](https://pypi.python.org/pypi?%3Aaction=search&term=httpie&submit=search).
Here are a few picks:

- [httpie-api-auth](https://github.com/pd/httpie-api-auth): ApiAuth
- [httpie-aws-auth](https://github.com/httpie/httpie-aws-auth): AWS / Amazon S3
- [httpie-edgegrid](https://github.com/akamai-open/httpie-edgegrid): EdgeGrid
- [httpie-hmac-auth](https://github.com/guardian/httpie-hmac-auth): HMAC
- [httpie-jwt-auth](https://github.com/teracyhq/httpie-jwt-auth): JWTAuth (JSON Web Tokens)
- [httpie-negotiate](https://github.com/ndzou/httpie-negotiate): SPNEGO (GSS Negotiate)
- [httpie-ntlm](https://github.com/httpie/httpie-ntlm): NTLM (NT LAN Manager)
- [httpie-oauth](https://github.com/httpie/httpie-oauth): OAuth
- [requests-hawk](https://github.com/mozilla-services/requests-hawk): Hawk

## HTTP redirects

By default, HTTP redirects are not followed and only the first
response is shown:

```bash
$ http pie.dev/redirect/3
```

### Follow `Location`

To instruct HTTPie to follow the `Location` header of `30x` responses
and show the final response instead, use the `--follow, -F` option:

```bash
$ http --follow pie.dev/redirect/3
```

With `307 Temporary Redirect` and `308 Permanent Redirect`, the method and the body of the original request
are reused to perform the redirected request. Otherwise, a body-less `GET` request is performed.

### Showing intermediary redirect responses

If you wish to see the intermediary requests/responses,
then use the `--all` option:

```bash
$ http --follow --all pie.dev/redirect/3
```

### Limiting maximum redirects followed

To change the default limit of maximum `30` redirects, use the `--max-redirects=<limit>` option:

```bash
$ http --follow --all --max-redirects=2 pie.dev/redirect/3
```

## Proxies

You can specify proxies to be used through the `--proxy` argument for each protocol (which is included in the value in case of redirects across protocols):

```bash
$ http --proxy=http:http://10.10.1.10:3128 --proxy=https:https://10.10.1.10:1080 example.org
```

With Basic authentication:

```bash
$ http --proxy=http:http://user:pass@10.10.1.10:3128 example.org
```

### Environment variables

You can also configure proxies by environment variables `ALL_PROXY`, `HTTP_PROXY` and `HTTPS_PROXY`, and the underlying [Requests library](https://python-requests.org/) will pick them up.
If you want to disable proxies configured through the environment variables for certain hosts, you can specify them in `NO_PROXY`.

In your `~/.bash_profile`:

```bash
export HTTP_PROXY=http://10.10.1.10:3128
export HTTPS_PROXY=https://10.10.1.10:1080
export NO_PROXY=localhost,example.com
```

### SOCKS

Usage for SOCKS is the same as for other types of [proxies](#proxies):

```bash
$ http --proxy=http:socks5://user:pass@host:port --proxy=https:socks5://user:pass@host:port example.org
```

## HTTPS

### Server SSL certificate verification

To skip the host’s SSL certificate verification, you can pass `--verify=no` (default is `yes`):

```bash
$ http --verify=no https://pie.dev/get
```

### Custom CA bundle

You can also use `--verify=<CA_BUNDLE_PATH>` to set a custom CA bundle path:

```bash
$ http --verify=/ssl/custom_ca_bundle https://example.org
```

### Client side SSL certificate

To use a client side certificate for the SSL communication, you can pass
the path of the cert file with `--cert`:

```bash
$ http --cert=client.pem https://example.org
```

If the private key is not contained in the cert file, you may pass the
path of the key file with `--cert-key`:

```bash
$ http --cert=client.crt --cert-key=client.key https://example.org
```

### SSL version

Use the `--ssl=<PROTOCOL>` option to specify the desired protocol version to use.
This will default to SSL v2.3 which will negotiate the highest protocol that both the server and your installation of OpenSSL support.
The available protocols are `ssl2.3`, `ssl3`, `tls1`, `tls1.1`, `tls1.2`, `tls1.3`.
(The actually available set of protocols may vary depending on your OpenSSL installation.)

```bash
# Specify the vulnerable SSL v3 protocol to talk to an outdated server:
$ http --ssl=ssl3 https://vulnerable.example.org
```

### SSL ciphers

You can specify the available ciphers with `--ciphers`.
It should be a string in the [OpenSSL cipher list format](https://www.openssl.org/docs/man1.1.0/man1/ciphers.html).

```bash
$ http --ciphers=ECDHE-RSA-AES128-GCM-SHA256 https://pie.dev/get
```

Note: these cipher strings do not change the negotiated version of SSL or TLS, they only affect the list of available cipher suites.

To see the default cipher string, run `http --help` and see the `--ciphers` section under SSL.

## Output options

By default, HTTPie only outputs the final response and the whole response
message is printed (headers as well as the body). You can control what should
be printed via several options:

|          Option | What is printed                                                                                    |
| --------------: | -------------------------------------------------------------------------------------------------- |
| `--headers, -h` | Only the response headers are printed                                                              |
|    `--body, -b` | Only the response body is printed                                                                  |
| `--verbose, -v` | Print the whole HTTP exchange (request and response). This option also enables `--all` (see below) |
|   `--print, -p` | Selects parts of the HTTP exchange                                                                 |
|   `--quiet, -q` | Don't print anything to `stdout` and `stderr`                                                      |

### What parts of the HTTP exchange should be printed

All the other [output options](#output-options) are under the hood just shortcuts for the more powerful `--print, -p`.
It accepts a string of characters each of which represents a specific part of the HTTP exchange:

| Character | Stands for       |
| --------: | ---------------- |
|       `H` | request headers  |
|       `B` | request body     |
|       `h` | response headers |
|       `b` | response body    |

Print request and response headers:

```bash
$ http --print=Hh PUT pie.dev/put hello=world
```

### Verbose output

`--verbose` can often be useful for debugging the request and generating documentation examples:

```bash
$ http --verbose PUT pie.dev/put hello=world
PUT /put HTTP/1.1
Accept: application/json, */*;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/json
Host: pie.dev
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
```

### Quiet output

`--quiet` redirects all output that would otherwise go to `stdout` and `stderr` to `/dev/null` (except for errors and warnings).
This doesn’t affect output to a file via `--output` or `--download`.

```bash
# There will be no output:
$ http --quiet pie.dev/post enjoy='the silence'
```

If you’d like to silence warnings as well, use `-q` or `--quiet` twice:

```bash
# There will be no output, even in case of an unexpected response status code:
$ http -qq --check-status pie.dev/post enjoy='the silence without warnings'
```

### Viewing intermediary requests/responses

To see all the HTTP communication, i.e. the final request/response as well as any possible intermediary requests/responses, use the `--all` option.
The intermediary HTTP communication include followed redirects (with `--follow`), the first unauthorized request when HTTP digest authentication is used (`--auth=digest`), etc.

```bash
# Include all responses that lead to the final one:
$ http --all --follow pie.dev/redirect/3
```

The intermediary requests/responses are by default formatted according to `--print, -p` (and its shortcuts described above).

If you’d like to change that, use the `--history-print, -P` option.
It takes the same arguments as `--print, -p` but applies to the intermediary requests only.

```bash
# Print the intermediary requests/responses differently than the final one:
$ http -A digest -a foo:bar --all -p Hh -P H pie.dev/digest-auth/auth/foo/bar
```

### Conditional body download

As an optimization, the response body is downloaded from the server only if it’s part of the output.
This is similar to performing a `HEAD` request, except that it applies to any HTTP method you use.

Let’s say that there is an API that returns the whole resource when it is updated, but you are only interested in the response headers to see the status code after an update:

```bash
$ http --headers PATCH pie.dev/patch name='New Name'
```

Since you are only printing the HTTP headers here, the connection to the server is closed as soon as all the response headers have been received.
Therefore, bandwidth and time isn’t wasted downloading the body which you don’t care about.
The response headers are downloaded always, even if they are not part of the output

## Raw request body

In addition to crafting structured [JSON](#json) and [forms](#forms) requests with the [request items](#request-items) syntax, you can provide a raw request body that will be sent without further processing.
These two approaches for specifying request data (i.e., structured and raw) cannot be combined.

There’re three methods for passing raw request data: piping via `stdin`,
`--raw='data'`, and `@/file/path`.

### Redirected Input

The universal method for passing request data is through redirected `stdin`
(standard input)—piping.

By default, `stdin` data is buffered and then with no further processing used as the request body.
If you provide `Content-Length`, then the request body is streamed without buffering.
You may also use `--chunked` to enable streaming via [chunked transfer encoding](#chunked-transfer-encoding)
or `--compress, -x` to [compress the request body](#compressed-request-body).

There are multiple useful ways to use piping:

Redirect from a file:

```bash
$ http PUT pie.dev/put X-API-Token:123 < files/data.json
```

Or the output of another program:

```bash
$ grep '401 Unauthorized' /var/log/httpd/error_log | http POST pie.dev/post
```

You can use `echo` for simple data:

```bash
$ echo -n '{"name": "John"}' | http PATCH pie.dev/patch X-API-Token:123
```

You can also use a Bash *here string*:

```bash
$ http pie.dev/post <<<'{"name": "John"}'
```

You can even pipe web services together using HTTPie:

```bash
$ http GET https://api.github.com/repos/httpie/httpie | http POST pie.dev/post
```

You can use `cat` to enter multiline data on the terminal:

```bash
$ cat | http POST pie.dev/post
<paste>
^D
```

```bash
$ cat | http POST pie.dev/post Content-Type:text/plain
- buy milk
- call parents
^D
```

On macOS, you can send the contents of the clipboard with `pbpaste`:

```bash
$ pbpaste | http PUT pie.dev/put
```

Passing data through `stdin` **can't** be combined with data fields specified on the command line:

```bash
$ echo -n 'data' | http POST example.org more=data  # This is invalid
```

To prevent HTTPie from reading `stdin` data you can use the `--ignore-stdin` option.

### Request data via `--raw`

In a situation when piping data via `stdin` is not convenient (for example,
when generating API docs examples), you can specify the raw request body via
the `--raw` option.

```bash
$ http --raw 'Hello, world!' pie.dev/post
```

```bash
$ http --raw '{"name": "John"}' pie.dev/post
```

### Request data from a filename

An alternative to redirected `stdin` is specifying a filename (as `@/path/to/file`) whose content is used as if it came from `stdin`.

It has the advantage that the `Content-Type` header is automatically set to the appropriate value based on the filename extension.
For example, the following request sends the verbatim contents of that XML file with `Content-Type: application/xml`:

```bash
$ http PUT pie.dev/put @files/data.xml
```

File uploads are always streamed to avoid memory issues with large files.

## Chunked transfer encoding

You can use the `--chunked` flag to instruct HTTPie to use `Transfer-Encoding: chunked`:

```bash
$ http --chunked PUT pie.dev/put hello=world
```

```bash
$ http --chunked --multipart PUT pie.dev/put hello=world foo@files/data.xml
```

```bash
$ http --chunked pie.dev/post @files/data.xml
```

```bash
$ cat files/data.xml | http --chunked pie.dev/post
```

## Compressed request body

You can use the `--compress, -x` flag to instruct HTTPie to use `Content-Encoding: deflate` and compress the request data:

```bash
$ http --compress pie.dev/post @files/data.xml
```

```bash
$ cat files/data.xml | http --compress pie.dev/post
```

If compressing the data does not save size, HTTPie sends it untouched. To always compress the data, specify `--compress, -x` twice:

```bash
$ http -xx PUT pie.dev/put hello=world
```

## Terminal output

HTTPie does several things by default in order to make its terminal output easy to read.

### Colors and formatting

Syntax highlighting is applied to HTTP headers and bodies (where it makes sense).
You can choose your preferred color scheme via the --style option if you don’t like the default one.
There are dozens of styles available, here are just a few notable ones:

|     Style | Description                                                                                                                         |
| --------: | ----------------------------------------------------------------------------------------------------------------------------------- |
|    `auto` | Follows your terminal ANSI color styles. This is the default style used by HTTPie                                                   |
| `default` | Default styles of the underlying Pygments library. Not actually used by default by HTTPie. You can enable it with `--style=default` |
| `monokai` | A popular color scheme. Enable with `--style=monokai`                                                                               |
|  `fruity` | A bold, colorful scheme. Enable with `--style=fruity`                                                                               |
|         … | See `$ http --help` for all the possible `--style` values                                                                           |

Use one of these options to control output processing:

|            Option | Description                                                   |
| ----------------: | ------------------------------------------------------------- |
|    `--pretty=all` | Apply both colors and formatting. Default for terminal output |
| `--pretty=colors` | Apply colors                                                  |
| `--pretty=format` | Apply formatting                                              |
|   `--pretty=none` | Disables output processing. Default for redirected output     |

HTTPie looks at `Content-Type` to select the right syntax highlighter and formatter for each message body. If that fails (e.g., the server provides the wrong type), or you prefer a different treatment, you can manually overwrite the mime type for a response with `--response-mime`:

```bash
$ http --response-mime=text/yaml pie.dev/get
```

Formatting has the following effects:

- HTTP headers are sorted by name.
- JSON data is indented, sorted by keys, and unicode escapes are converted
  to the characters they represent.
- XML and XHTML data is indented.

You can further control the applied formatting via the more granular [format options](#format-options).

### Format options

The `--format-options=opt1:value,opt2:value` option allows you to control how the output should be formatted
when formatting is applied. The following options are available:

|           Option | Default value | Shortcuts                |
| ---------------: | :-----------: | ------------------------ |
|   `headers.sort` |    `true`     | `--sorted`, `--unsorted` |
|    `json.format` |    `true`     | N/A                      |
|    `json.indent` |      `4`      | N/A                      |
| `json.sort_keys` |    `true`     | `--sorted`, `--unsorted` |
|     `xml.format` |    `true`     | N/A                      |
|     `xml.indent` |      `2`      | N/A                      |

For example, this is how you would disable the default header and JSON key
sorting, and specify a custom JSON indent size:

```bash
$ http --format-options headers.sort:false,json.sort_keys:false,json.indent:2 pie.dev/get
```

There are also two shortcuts that allow you to quickly disable and re-enable
sorting-related format options (currently it means JSON keys and headers):
`--unsorted` and `--sorted`.

This is something you will typically store as one of the default options in your [config](#config) file.

### Redirected output

HTTPie uses a different set of defaults for redirected output than for [terminal output](#terminal-output).
The differences being:

- Formatting and colors aren’t applied (unless `--pretty` is specified).
- Only the response body is printed (unless one of the [output options](#output-options) is set).
- Also, binary data isn’t suppressed.

The reason is to make piping HTTPie’s output to another programs and downloading files work with no extra flags.
Most of the time, only the raw response body is of an interest when the output is redirected.

Download a file:

```bash
$ http pie.dev/image/png > image.png
```

Download an image of an [Octocat](https://octodex.github.com/images/original.jpg), resize it using [ImageMagick](https://imagemagick.org/), and upload it elsewhere:

```bash
$ http octodex.github.com/images/original.jpg | convert - -resize 25% - | http example.org/Octocats
```

Force colorizing and formatting, and show both the request and the response in `less` pager:

```bash
$ http --pretty=all --verbose pie.dev/get | less -R
```

The `-R` flag tells `less` to interpret color escape sequences included HTTPie’s output.

You can create a shortcut for invoking HTTPie with colorized and paged output by adding the following to your `~/.bash_profile`:

```bash
function httpless {
    # `httpless example.org'
    http --pretty=all --print=hb "$@" | less -R;
}
```

### Binary data

Binary data is suppressed for terminal output, which makes it safe to perform requests to URLs that send back binary data.
Binary data is also suppressed in redirected but prettified output.
The connection is closed as soon as we know that the response body is binary,

```bash
$ http pie.dev/bytes/2000
```

You will nearly instantly see something like this:

```http
HTTP/1.1 200 OK
Content-Type: application/octet-stream

+-----------------------------------------+
| NOTE: binary data not shown in terminal |
+-----------------------------------------+
```

### Display encoding

HTTPie tries to do its best to decode message bodies when printing them to the terminal correctly. It uses the encoding specified in the `Content-Type` `charset` attribute. If a message doesn’t define its charset, we auto-detect it. For very short messages (1–32B), where auto-detection would be unreliable, we default to UTF-8. For cases when the response encoding is still incorrect, you can manually overwrite the response charset with `--response-charset`:

```bash
$ http --response-charset=big5 pie.dev/get
```

## Download mode

HTTPie features a download mode in which it acts similarly to `wget`.

When enabled using the `--download, -d` flag, response headers are printed to the terminal (`stderr`), and a progress bar is shown while the response body is being saved to a file.

```bash
$ http --download https://github.com/httpie/httpie/archive/master.tar.gz
```

```http
HTTP/1.1 200 OK
Content-Disposition: attachment; filename=httpie-master.tar.gz
Content-Length: 257336
Content-Type: application/x-gzip

Downloading 251.30 kB to "httpie-master.tar.gz"
Done. 251.30 kB in 2.73862s (91.76 kB/s)
```

### Downloaded filename

There are three mutually exclusive ways through which HTTPie determines
the output filename (with decreasing priority):

1. You can explicitly provide it via `--output, -o`. The file gets overwritten if it already exists (or appended to with `--continue, -c`).
2. The server may specify the filename in the optional `Content-Disposition` response header. Any leading dots are stripped from a server-provided filename.
3. The last resort HTTPie uses is to generate the filename from a combination of the request URL and the response `Content-Type`. The initial URL is always used as the basis for the generated filename — even if there has been one or more redirects.

To prevent data loss by overwriting, HTTPie adds a unique numerical suffix to the filename when necessary (unless specified with `--output, -o`).

### Piping while downloading

You can also redirect the response body to another program while the response headers and progress are still shown in the terminal:

```bash
$ http -d https://github.com/httpie/httpie/archive/master.tar.gz | tar zxf -
```

### Resuming downloads

If `--output, -o` is specified, you can resume a partial download using the `--continue, -c` option.
This only works with servers that support `Range` requests and `206 Partial Content` responses.
If the server doesn’t support that, the whole file will simply be downloaded:

```bash
$ http -dco file.zip example.org/file
```

`-dco` is shorthand for `--download` `--continue` `--output`.

### Other notes

- The `--download` option only changes how the response body is treated.
- You can still set custom headers, use sessions, `--verbose, -v`, etc.
- `--download` always implies `--follow` (redirects are followed).
- `--download` also implies `--check-status` (error HTTP status will result in a non-zero exist static code).
- HTTPie exits with status code `1` (error) if the body hasn’t been fully downloaded.
- `Accept-Encoding` can't be set with `--download`.

## Streamed responses

Responses are downloaded and printed in chunks.
This allows for streaming and large file downloads without using too much memory.
However, when [colors and formatting](#colors-and-formatting) are applied, the whole response is buffered and only then processed at once.

### Disabling buffering

You can use the `--stream, -S` flag to make two things happen:

1. The output is flushed in much smaller chunks without any buffering, which makes HTTPie behave kind of like `tail -f` for URLs.
2. Streaming becomes enabled even when the output is prettified: It will be applied to each line of the response and flushed immediately. This makes it possible to have a nice output for long-lived requests, such as one to the [Twitter streaming API](https://developer.twitter.com/en/docs/tutorials/consuming-streaming-data).

### Example use cases

Prettified streamed response:

```bash
$ http --stream pie.dev/stream/3
```

Streamed output by small chunks à la `tail -f`:

```bash
# Send each new line (JSON object) to another URL as soon as it arrives from a streaming API:
$ http --stream pie.dev/stream/3 | while read line; do echo "$line" | http pie.dev/post ; done
```

## Sessions

By default, every request HTTPie makes is completely independent of any previous ones to the same host.

However, HTTPie also supports persistent sessions via the `--session=SESSION_NAME_OR_PATH` option.
In a session, custom [HTTP headers](#http-headers) (except for the ones starting with `Content-` or `If-`), [authentication](#authentication), and [cookies](#cookies) (manually specified or sent by the server) persist between requests to the same host.

```bash
# Create a new session:
$ http --session=./session.json pie.dev/headers API-Token:123
```

```bash
# Inspect / edit the generated session file:
$ cat session.json
```

```bash
# Re-use the existing session — the API-Token header will be set:
$ http --session=./session.json pie.dev/headers
```

All session data, including credentials, cookie data, and custom headers are stored in plain text.
That means session files can also be created and edited manually in a text editor—they are regular JSON.
It also means that they can be read by anyone who has access to the session file.

### Named sessions

You can create one or more named session per host. For example, this is how you can create a new session named `user1` for `pie.dev`:

```bash
$ http --session=user1 -a user1:password pie.dev/get X-Foo:Bar
```

From now on, you can refer to the session by its name (`user1`).
When you choose to use the session again, all previously specified authentication or HTTP headers will automatically be set:

```bash
$ http --session=user1 pie.dev/get
```

To create or reuse a different session, simply specify a different name:

```bash
$ http --session=user2 -a user2:password pie.dev/get X-Bar:Foo
```

Named sessions’ data is stored in JSON files inside the `sessions` subdirectory of the [config](#config) directory, typically `~/.config/httpie/sessions/<host>/<name>.json` (`%APPDATA%\httpie\sessions\<host>\<name>.json` on Windows).

If you have executed the above commands on a Unix machine, you should be able list the generated sessions files using:

```bash
$ ls -l ~/.config/httpie/sessions/pie.dev
```

### Anonymous sessions

Instead of giving it a name, you can also directly specify a path to a session file.
This allows for sessions to be re-used across multiple hosts:

```bash
# Create a session:
$ http --session=/tmp/session.json example.org
```

```bash
# Use the session to make a request to another host:
$ http --session=/tmp/session.json admin.example.org
```

```bash
# You can also refer to a previously created named session:
$ http --session=~/.config/httpie/sessions/another.example.org/test.json example.org
```

When creating anonymous sessions, please remember to always include at least one `/`, even if the session files is located in the current directory (i.e. `--session=./session.json` instead of just `--session=session.json`), otherwise HTTPie assumes a named session instead.

### Readonly session

To use the original session file without updating it from the request/response exchange after it has been created, specify the session name via `--session-read-only=SESSION_NAME_OR_PATH` instead.

```bash
# If the session file doesn’t exist, then it is created:
$ http --session-read-only=./ro-session.json pie.dev/headers Custom-Header:orig-value
```

```bash
# But it is not updated:
$ http --session-read-only=./ro-session.json pie.dev/headers Custom-Header:new-value
```

### Cookie Storage Behavior

**TL;DR:** Cookie storage priority: Server response > Command line request > Session file

To set a cookie within a Session there are three options:

1. Get a `Set-Cookie` header in a response from a server

   ```bash
   $ http --session=./session.json pie.dev/cookie/set?foo=bar
   ```

2. Set the cookie name and value through the command line as seen in [cookies](#cookies)

   ```bash
   $ http --session=./session.json pie.dev/headers Cookie:foo=bar
   ```

3. Manually set cookie parameters in the JSON file of the session

   ```json
   {
       "__meta__": {
       "about": "HTTPie session file",
       "help": "https://httpie.org/doc#sessions",
       "httpie": "2.2.0-dev"
       },
       "auth": {
           "password": null,
           "type": null,
           "username": null
       },
       "cookies": {
           "foo": {
               "expires": null,
               "path": "/",
               "secure": false,
               "value": "bar"
               }
       }
   }
   ```

Cookies will be set in the session file with the priority specified above.
For example, a cookie set through the command line will overwrite a cookie of the same name stored in the session file.
If the server returns a `Set-Cookie` header with a cookie of the same name, the returned cookie will overwrite the preexisting cookie.

Expired cookies are never stored.
If a cookie in a session file expires, it will be removed before sending a new request.
If the server expires an existing cookie, it will also be removed from the session file.

## Config

HTTPie uses a simple `config.json` file.
The file doesn’t exist by default but you can create it manually.

### Config file directory

To see the exact location for your installation, run `http --debug` and look for `config_dir` in the output.

The default location of the configuration file on most platforms is `$XDG_CONFIG_HOME/httpie/config.json` (defaulting to `~/.config/httpie/config.json`).

For backwards compatibility, if the directory `~/.httpie` exists, the configuration file there will be used instead.

On Windows, the config file is located at `%APPDATA%\httpie\config.json`.

The config directory can be changed by setting the `$HTTPIE_CONFIG_DIR` environment variable:

```bash
$ export HTTPIE_CONFIG_DIR=/tmp/httpie
$ http pie.dev/get
```

### Configurable options

Currently, HTTPie offers a single configurable option:

#### `default_options`

An `Array` (by default empty) of default options that should be applied to every invocation of HTTPie.

For instance, you can use this config option to change your default color theme:

```bash
$ cat ~/.config/httpie/config.json
```

```json
{
    "default_options": [
        "--style=fruity"
    ]
}
```

Technically, it is possible to include any HTTPie options in there.
However, it is not recommended to modify the default behavior in a way that would break your compatibility with the wider world as that may become confusing.

### Un-setting previously specified options

Default options from the config file, or specified any other way, can be unset for a particular invocation via `--no-OPTION` arguments passed via the command line (e.g., `--no-style` or `--no-session`).

## Scripting

When using HTTPie from shell scripts, it can be handy to set the `--check-status` flag.
It instructs HTTPie to exit with an error if the HTTP status is one of `3xx`, `4xx`, or `5xx`.
The exit status will be `3` (unless `--follow` is set), `4`, or `5`, respectively.

```bash
#!/bin/bash

if http --check-status --ignore-stdin --timeout=2.5 HEAD pie.dev/get &> /dev/null; then
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
```

### Best practices

The default behavior of automatically reading `stdin` is typically not desirable during non-interactive invocations.
You most likely want to use the `--ignore-stdin` option to disable it.

It is a common *gotcha* that without this option HTTPie seemingly hangs.
What happens is that when HTTPie is invoked, for example, from a cron job, `stdin` is not connected to a terminal.
Therefore, the rules for [redirected input](#redirected-input) apply, i.e. HTTPie starts to read it expecting that the request body will be passed through.
And since there’s neither data nor `EOF`, it will get stuck. So unless you’re piping some data to HTTPie, the `--ignore-stdin` flag should be used in scripts.

Also, it might be good to set a connection `--timeout` limit to prevent your program from hanging if the server never responds.

## Meta

### Interface design

The syntax of the command arguments closely correspond to the actual HTTP requests sent over the wire.
It has the advantage that it’s easy to remember and read.
You can often translate an HTTP request to an HTTPie argument list just by inlining the request elements.
For example, compare this HTTP request:

```http
POST /post HTTP/1.1
Host: pie.dev
X-API-Key: 123
User-Agent: Bacon/1.0
Content-Type: application/x-www-form-urlencoded

name=value&name2=value2
```

with the HTTPie command that sends it:

```bash
$ http -f POST pie.dev/post \
    X-API-Key:123 \
    User-Agent:Bacon/1.0 \
    name=value \
    name2=value2
```

Notice that both the order of elements and the syntax are very similar, and that only a small portion of the command is used to control HTTPie and doesn’t directly correspond to any part of the request (here, it’s only `-f` asking HTTPie to send a form request).

The two modes, `--pretty=all` (default for terminal) and `--pretty=none` (default for [redirected output](#redirected-output)), allow for both user-friendly interactive use and usage from scripts, where HTTPie serves as a generic HTTP client.

In the future, the command line syntax and some of the `--OPTIONS` may change slightly, as HTTPie improves and new features are added.
All changes are recorded in the [change log](#change-log).

### Community and Support

HTTPie has the following community channels:

- [GitHub Issues](https://github.com/httpie/httpie/issues) for bug reports and feature requests
- [Discord server](https://httpie.io/discord) to ask questions, discuss features, and for general API development discussion
- [StackOverflow](https://stackoverflow.com) to ask questions (make sure to use the [httpie](https://stackoverflow.com/questions/tagged/httpie) tag)
- Twitter; where you can tweet directly to (and follow!) [@httpie](https://twitter.com/httpie)

### Related projects

#### Dependencies

Under the hood, HTTPie uses these two amazing libraries:

- [Requests](https://python-requests.org) — Python HTTP library for humans
- [Pygments](https://pygments.org/) — Python syntax highlighter

#### HTTPie friends

HTTPie plays exceptionally well with the following tools:

- [http-prompt](https://github.com/httpie/http-prompt) — an interactive shell for HTTPie featuring autocomplete and command syntax highlighting
- [jq](https://stedolan.github.io/jq/) — CLI JSON processor that works great in conjunction with HTTPie

Helpers to convert from other client tools:

- [CurliPie](https://curlipie.now.sh/) help convert cURL command line to HTTPie command line

#### Alternatives

- [httpcat](https://github.com/httpie/httpcat) — a lower-level sister utility of HTTPie for constructing raw HTTP requests on the command line
- [curl](https://curl.haxx.se) — a "Swiss knife" command line tool and an exceptional library for transferring data with URLs.

### Contributing

See [CONTRIBUTING](https://github.com/httpie/httpie/blob/master/CONTRIBUTING.md).

### Change log

See [CHANGELOG](https://github.com/httpie/httpie/blob/master/CHANGELOG.md).

### Artwork

- [README Animation](https://raw.githubusercontent.com/httpie/httpie/master/httpie.gif) by [Allen Smith](https://github.com/loranallensmith).

### Licence

BSD-3-Clause: [LICENSE](https://github.com/httpie/httpie/blob/master/LICENSE).

### Authors

[Jakub Roztocil](https://roztocil.co) ([@jakubroztocil](https://twitter.com/jakubroztocil)) created HTTPie and [these fine people](https://github.com/httpie/httpie/AUTHORS.md) have contributed.
