## HTTPie: cURL for humans

HTTPie is a CLI frontend for [python-requests](http://python-requests.org).

![httpie](https://github.com/jkbr/httpie/raw/master/httpie.png)


### Installation

    pip install httpie


### Usage

    httpie [flags] METHOD URL [header:value | data-field-name=value]*

The default request `Content-Type` in `application/json` and data fields are automatically serialized as a JSON `Object`, so this:

    httpie PATCH name=John api.example.com/person/1 X-API-Token:123

Will issue the following request:

    PATCH /person/1 HTTP/1.1
    User-Agent: HTTPie/0.1
    X-API-Token: 123
    Content-Type: application/json; charset=utf-8

    {"name": "John"}
    
You can use the `--form` flag to set `Content-Type` and serialize the data as `application/x-www-form-urlencoded`.

The data to be sent can also be passed via `stdin`:

    httpie PUT api.example.com/person/1 X-API-Token:123 < person.json

Most of the flags mirror the arguments you would use with `requests.request`. See `httpie -h` for more details.

