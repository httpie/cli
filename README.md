<br/>
<a href="https://httpie.io target="blank_">
    <img width="285" alt="Httpie-Logo-Lockup-Pink@2x" src="https://user-images.githubusercontent.com/22844059/112143133-5fff7380-8bcf-11eb-85d0-8efdf27f3991.png">
</a>

# The human-friendly HTTP CLI client for working with APIs

<img src="https://raw.githubusercontent.com/httpie/httpie/master/httpie.gif" width="600"/>

<a href="https://httpie.org/docs" target="_blank">
    <img src="https://img.shields.io/badge/stable%20docs-httpie.org%2Fdocs-brightgreen?style=flat-square" />
</a>
<a href="https://pypi.python.org/pypi/httpie" target="_blank">
    <img src="https://img.shields.io/pypi/v/httpie.svg?style=flat-square&label=latest%20stable%20version" />
</a>
<a href="https://codecov.io/gh/httpie/httpie" target="_blank">
    <img src="https://img.shields.io/codecov/c/github/httpie/httpie?style=flat-square" />
</a>
<a href="https://httpie.io/chat" target="_blank">
    <img src="https://img.shields.io/badge/chat-on%20Discord-brightgreen?style=flat-square" />
</a>
<a href="https://pepy.tech/project/httpie" target="_blank">
    <img src="https://pepy.tech/badge/httpie" />
</a>

  HTTPie (<i>pronounced aitch-tee-tee-pie</i> 🥧) is a command-line HTTP client.

The `http` and `https` commands let you send arbitrary HTTP requests for testing, debugging, and generally interacting with APIs & HTTP servers. Commands use simple, natural syntax and provide a formatted and colorized output.

*Go to [httpie.io](https://httpie.io) to learn more.*

## Features 

- Simple syntax
- Formatted and colorized terminal output
- Built-in JSON support
- Forms and file uploads
- HTTPS, proxies, and authentication
- Persistent sessions
- Wget-like downloads
- Linux, macOS and Windows support
- Plugins, such as JWTAuth and OAuth

See the [complete list of features](https://httpie.io/docs).

## Documentation 

Full documentation and installation guides live in [httpie.io/docs](https://httpie.io/docs).

## Installation

HTTPie can be installed using Homebrew on macOS (`brew install httpie`), and `pip` on Linux, Windows and other Operating Systems (e.g. `python -m pip install --upgrade httpie`).

See the [docs](https://httpie.io/docs) for system requirements and full installation instructions.

## Examples 

Hello World:

```
$ https httpie.io/hello
```

Custom [HTTP method](https://httpie.io/docs#http-method), [HTTP headers](https://httpie.io/docs#http-headers) and [JSON](https://httpie.io/docs#json) data:

```
$ http PUT pie.dev/put X-API-Token:123 name=John
```

Build and print a request without sending it using [offline mode](https://httpie.io/docs#offline-mode):

```
$ http --offline pie.dev/post hello=offline
```

Use [GitHub API](https://developer.github.com/v3/issues/comments/#create-a-comment) to post a comment on an [Issue](https://github.com/httpie/httpie/issues/83) with [authentication](https://httpie.io/docs#authentication):

```
$ http -a USERNAME POST https://api.github.com/repos/httpie/httpie/issues/83/comments body='HTTPie is awesome! :heart:'
```

**See [the documentation](https://httpie.io/docs) for a complete list of examples and use cases.** 

## Contributing 

We :sparkling_heart: our contributors! Please read the [contribution guide](https://github.com/httpie/httpie/blob/master/CONTRIBUTING.md) for how to contribute.

If you'd like to request a feature or report a bug, please [create a GitHub Issue](https://github.com/httpie/httpie/issues) using one of the templates provided.

## Community & Support

- Visit the [HTTPie website](https://httpie.io) for full documentation and useful links.

- Join our [Discord server](https://httpie.io/chat) is to ask questions, discuss features, and for general API chat.

- Tweet at [@httpie](https://twitter.com/httpie) on Twitter.

- Use [StackOverflow](https://stackoverflow.com/questions/tagged/httpie) to ask questions and include a `httpie` tag.

- Create [GitHub Issues](https://github.com/httpie/httpie/issues) for bug reports and feature requests.

- Subscribe to the [HTTPie newsletter](https://httpie.io) for occasional updates.

## License 

HTTPie is licensed under the [BSD-3-Clause License](https://github.com/httpie/httpie/blob/master/LICENSE). 
