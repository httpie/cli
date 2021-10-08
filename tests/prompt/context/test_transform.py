from httpie.prompt.context import Context
from httpie.prompt.context import transform as t


def test_extract_args_for_httpie_main_get():
    c = Context('http://localhost/things')
    c.headers.update({
        'Authorization': 'ApiKey 1234',
        'Accept': 'text/html'
    })
    c.querystring_params.update({
        'page': '2',
        'limit': '10'
    })

    args = t.extract_args_for_httpie_main(c, method='get')
    assert args == ['GET', 'http://localhost/things', 'limit==10', 'page==2',
                    'Accept:text/html', 'Authorization:ApiKey 1234']


def test_extract_args_for_httpie_main_post():
    c = Context('http://localhost/things')
    c.headers.update({
        'Authorization': 'ApiKey 1234',
        'Accept': 'text/html'
    })
    c.options.update({
        '--verify': 'no',
        '--form': None
    })
    c.body_params.update({
        'full name': 'Jane Doe',
        'email': 'jane@example.com'
    })

    args = t.extract_args_for_httpie_main(c, method='post')
    assert args == ['--form', '--verify', 'no',
                    'POST', 'http://localhost/things',
                    'email=jane@example.com', 'full name=Jane Doe',
                    'Accept:text/html', 'Authorization:ApiKey 1234']


def test_extract_raw_json_args_for_httpie_main_post():
    c = Context('http://localhost/things')
    c.body_json_params.update({
        'enabled': True,
        'items': ['foo', 'bar'],
        'object': {
            'id': 10,
            'name': 'test'
        }
    })

    args = t.extract_args_for_httpie_main(c, method='post')
    assert args == ['POST', 'http://localhost/things',
                    'enabled:=true', 'items:=["foo", "bar"]',
                    'object:={"id": 10, "name": "test"}']


def test_format_to_httpie_get():
    c = Context('http://localhost/things')
    c.headers.update({
        'Authorization': 'ApiKey 1234',
        'Accept': 'text/html'
    })
    c.querystring_params.update({
        'page': '2',
        'limit': '10',
        'name': ['alice', 'bob bob']
    })

    output = t.format_to_httpie(c, method='get')
    assert output == ("http GET http://localhost/things "
                      "limit==10 name==alice 'name==bob bob' page==2 "
                      "Accept:text/html 'Authorization:ApiKey 1234'\n")


def test_format_to_httpie_post():
    c = Context('http://localhost/things')
    c.headers.update({
        'Authorization': 'ApiKey 1234',
        'Accept': 'text/html'
    })
    c.options.update({
        '--verify': 'no',
        '--form': None
    })
    c.body_params.update({
        'full name': 'Jane Doe',
        'email': 'jane@example.com'
    })

    output = t.format_to_httpie(c, method='post')
    assert output == ("http --form --verify=no POST http://localhost/things "
                      "email=jane@example.com 'full name=Jane Doe' "
                      "Accept:text/html 'Authorization:ApiKey 1234'\n")


def test_format_to_http_prompt_1():
    c = Context('http://localhost/things')
    c.headers.update({
        'Authorization': 'ApiKey 1234',
        'Accept': 'text/html'
    })
    c.querystring_params.update({
        'page': '2',
        'limit': '10'
    })

    output = t.format_to_http_prompt(c)
    assert output == ("cd http://localhost/things\n"
                      "limit==10\n"
                      "page==2\n"
                      "Accept:text/html\n"
                      "'Authorization:ApiKey 1234'\n")


def test_format_to_http_prompt_2():
    c = Context('http://localhost/things')
    c.headers.update({
        'Authorization': 'ApiKey 1234',
        'Accept': 'text/html'
    })
    c.options.update({
        '--verify': 'no',
        '--form': None
    })
    c.body_params.update({
        'full name': 'Jane Doe',
        'email': 'jane@example.com'
    })

    output = t.format_to_http_prompt(c)
    assert output == ("--form\n"
                      "--verify=no\n"
                      "cd http://localhost/things\n"
                      "email=jane@example.com\n"
                      "'full name=Jane Doe'\n"
                      "Accept:text/html\n"
                      "'Authorization:ApiKey 1234'\n")


def test_format_raw_json_string_to_http_prompt():
    c = Context('http://localhost/things')
    c.body_json_params.update({
        'bar': 'baz',
    })

    output = t.format_to_http_prompt(c)
    assert output == ("cd http://localhost/things\n"
                      "bar:='\"baz\"'\n")


def test_extract_httpie_options():
    c = Context('http://localhost')
    c.options.update({
        '--verify': 'no',
        '--form': None
    })

    output = t._extract_httpie_options(c, excluded_keys=['--form'])
    assert output == ['--verify', 'no']
