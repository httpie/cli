➜  ~ http --debug get 'localhost:5173/api/shopify_fulfillment/fetch_tracking_numbers?order_names[]=#1001.1&timestamp=1669900140'  
HTTPie 3.2.2
Requests 2.31.0
Pygments 2.17.2
Python 3.12.0 (main, Oct  2 2023, 12:03:24) [Clang 15.0.0 (clang-1500.0.40.1)]
/opt/homebrew/Cellar/httpie/3.2.2_3/libexec/bin/python
Darwin 23.1.0

<Environment {'apply_warnings_filter': <function Environment.apply_warnings_filter at 0x102e6afc0>,
 'args': Namespace(),
 'as_silent': <function Environment.as_silent at 0x102e6ae80>,
 'colors': 256,
 'config': {'default_options': []},
 'config_dir': PosixPath('/Users/francis/.config/httpie'),
 'devnull': <property object at 0x102e596c0>,
 'is_windows': False,
 'log_error': <function Environment.log_error at 0x102e6af20>,
 'program_name': 'http',
 'quiet': 0,
 'rich_console': <functools.cached_property object at 0x102e71c70>,
 'rich_error_console': <functools.cached_property object at 0x102e70920>,
 'show_displays': True,
 'stderr': <_io.TextIOWrapper name='<stderr>' mode='w' encoding='utf-8'>,
 'stderr_isatty': True,
 'stdin': <_io.TextIOWrapper name='<stdin>' mode='r' encoding='utf-8'>,
 'stdin_encoding': 'utf-8',
 'stdin_isatty': True,
 'stdout': <_io.TextIOWrapper name='<stdout>' mode='w' encoding='utf-8'>,
 'stdout_encoding': 'utf-8',
 'stdout_isatty': True}>

<PluginManager {'adapters': [],
 'auth': [<class 'httpie.plugins.builtin.BasicAuthPlugin'>,
          <class 'httpie.plugins.builtin.DigestAuthPlugin'>,
          <class 'httpie.plugins.builtin.BearerAuthPlugin'>],
 'converters': [],
 'formatters': [<class 'httpie.output.formatters.headers.HeadersFormatter'>,
                <class 'httpie.output.formatters.json.JSONFormatter'>,
                <class 'httpie.output.formatters.xml.XMLFormatter'>,
                <class 'httpie.output.formatters.colors.ColorFormatter'>]}>

>>> requests.request(**{'auth': None,
 'data': RequestJSONDataDict(),
 'headers': <HTTPHeadersDict('User-Agent': b'HTTPie/3.2.2')>,
 'method': 'get',
 'params': <generator object MultiValueOrderedDict.items at 0x103d8a3e0>,
 'url': 'http://localhost:5173/api/shopify_fulfillment/fetch_tracking_numbers?order_names[]=%231001.1
&timestamp=1669900140'})

HTTP/1.1 200 OK
Access-Control-Allow-Origin: *
Connection: keep-alive
Date: Tue, 12 Dec 2023 23:50:28 GMT
Keep-Alive: timeout=5
Transfer-Encoding: chunked
