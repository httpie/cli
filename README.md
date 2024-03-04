<h2 align="center">
    <a href="https://httpie.io" target="blank_">
        <img height="100" alt="HTTPie" src="https://raw.githubusercontent.com/httpie/cli/master/docs/httpie-logo.svg" />
    </a>
    <br>
    HTTPie CLI: human-friendly HTTP client for the API era
</h2>

<div align="center">

[![HTTPie for Desktop](https://img.shields.io/static/v1?label=HTTPie&message=Desktop&color=4B78E6)](https://httpie.io/product)
[![](https://img.shields.io/static/v1?label=HTTPie&message=Web%20%26%20Mobile&color=73DC8C)](https://httpie.io/app)
[![](https://img.shields.io/static/v1?label=HTTPie&message=CLI&color=FA9BFA)](https://httpie.io/cli)
[![Twitter](https://img.shields.io/twitter/follow/httpie?style=flat&color=%234B78E6&logoColor=%234B78E6)](https://twitter.com/httpie)
[![Chat](https://img.shields.io/discord/725351238698270761?style=flat&label=Chat%20on%20Discord&color=%23FA9BFA)](https://httpie.io/discord)

</div>


<div align="center">

[![Docs](https://img.shields.io/badge/stable%20docs-httpie.io%2Fdocs%2Fcli-brightgreen?style=flat&color=%2373DC8C&label=Docs)](https://httpie.org/docs/cli)
[![Latest version](https://img.shields.io/pypi/v/httpie.svg?style=flat&label=Latest&color=%234B78E6&logo=&logoColor=white)](https://pypi.python.org/pypi/httpie)
[![Build](https://img.shields.io/github/actions/workflow/status/httpie/cli/tests.yml?branch=master&color=%23FA9BFA&label=Build)](https://github.com/httpie/cli/actions)
[![Coverage](https://img.shields.io/codecov/c/github/httpie/cli?style=flat&label=Coverage&color=%2373DC8C)](https://codecov.io/gh/httpie/cli)
[![PyPi downloads](https://img.shields.io/pepy/dt/httpie?style=flat&label=Downloads%20from%20PyPi%20only&color=4B78E6)](https://www.pepy.tech/projects/httpie)

</div>

HTTPie (pronounced _aitch-tee-tee-pie_) is a command-line HTTP client.
Its goal is to make CLI interaction with web services as human-friendly as possible.
HTTPie is designed for testing, debugging, and generally interacting with APIs & HTTP servers.
The `http` & `https` commands allow for creating and sending arbitrary HTTP requests.
They use simple and natural syntax and provide formatted and colorized output.

<div align="center">

<img src="https://raw.githubusercontent.com/httpie/cli/master/docs/httpie-animation.gif" alt="HTTPie in action" width="100%"/>


</div>




## We lost 54k GitHub stars

Please note we recently accidentally made this repo private for a moment, and GitHub deleted our community that took a decade to build. Read the full story here: https://httpie.io/blog/stardust

![](docs/stardust.png)


## Getting started

- [Installation instructions →](https://httpie.io/docs#installation)
- [Full documentation →](https://httpie.io/docs)

## Features

- Expressive and intuitive syntax
- Formatted and colorized terminal output
- Built-in JSON support
- Forms and file uploads
- HTTPS, proxies, and authentication
- Arbitrary request data
- Custom headers
- Persistent sessions
- `wget`-like downloads

[See all features →](https://httpie.io/docs)

## Examples

Hello World:

```bash
https httpie.io/hello
```

Custom [HTTP method](https://httpie.io/docs#http-method), [HTTP headers](https://httpie.io/docs#http-headers) and [JSON](https://httpie.io/docs#json) data:

```bash
http PUT pie.dev/put X-API-Token:123 name=John
```

Build and print a request without sending it using [offline mode](https://httpie.io/docs/cli/offline-mode):

```bash
http --offline pie.dev/post hello=offline
```

Use [GitHub API](https://developer.github.com/v3/issues/comments/#create-a-comment) to post a comment on an [Issue](https://github.com/httpie/cli/issues/83) with [authentication](https://httpie.io/docs#authentication):

```bash
http -a USERNAME POST https://api.github.com/repos/httpie/cli/issues/83/comments body='HTTPie is awesome! :heart:'
```

[See more examples →](https://httpie.io/docs#examples)

## Community & support

- Visit the [HTTPie website](https://httpie.io) for full documentation and useful links.
- Join our [Discord server](https://httpie.io/discord) is to ask questions, discuss features, and for general API chat.
- Tweet at [@httpie](https://twitter.com/httpie) on Twitter.
- Use [StackOverflow](https://stackoverflow.com/questions/tagged/httpie) to ask questions and include a `httpie` tag.
- Create [GitHub Issues](https://github.com/httpie/cli/issues) for bug reports and feature requests.
- Subscribe to the [HTTPie newsletter](https://httpie.io) for occasional updates.

## Contributing

Have a look through existing [Issues](https://github.com/httpie/cli/issues) and [Pull Requests](https://github.com/httpie/cli/pulls) that you could help with. If you'd like to request a feature or report a bug, please [create a GitHub Issue](https://github.com/httpie/cli/issues) using one of the templates provided.

[See contribution guide →](https://github.com/httpie/cli/blob/master/CONTRIBUTING.md)
