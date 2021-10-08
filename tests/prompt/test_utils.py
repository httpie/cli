from httpie.prompt import utils


def test_colformat_zero_items():
    assert list(utils.colformat([], terminal_width=80)) == []


def test_colformat_one_item():
    assert list(utils.colformat(['hello'], terminal_width=80)) == ['hello']


def test_colformat_single_line():
    items = ['hello', 'world', 'foo', 'bar']
    assert list(utils.colformat(items, terminal_width=80)) == [
        'hello world foo   bar'
    ]


def test_colformat_single_column():
    items = ['chap1.txt', 'chap2.txt', 'chap3.txt', 'chap4.txt',
             'chap5.txt', 'chap6.txt', 'chap7.txt', 'chap8.txt']
    assert list(utils.colformat(items, terminal_width=10)) == [
        'chap1.txt', 'chap2.txt', 'chap3.txt', 'chap4.txt',
        'chap5.txt', 'chap6.txt', 'chap7.txt', 'chap8.txt'
    ]


def test_colformat_multi_columns_no_remainder():
    items = ['chap1.txt', 'chap2.txt', 'chap3.txt', 'chap4.txt',
             'chap5.txt', 'chap6.txt', 'chap7.txt', 'chap8.txt',
             'chap9.txt', 'chap10.txt', 'chap11.txt', 'chap12.txt']
    assert list(utils.colformat(items, terminal_width=50)) == [
        'chap1.txt  chap4.txt  chap7.txt  chap10.txt',
        'chap2.txt  chap5.txt  chap8.txt  chap11.txt',
        'chap3.txt  chap6.txt  chap9.txt  chap12.txt'
    ]


def test_colformat_multi_columns_remainder_1():
    items = ['chap1.txt', 'chap2.txt', 'chap3.txt', 'chap4.txt',
             'chap5.txt', 'chap6.txt', 'chap7.txt', 'chap8.txt',
             'chap9.txt', 'chap10.txt', 'chap11.txt', 'chap12.txt',
             'chap13.txt']
    assert list(utils.colformat(items, terminal_width=50)) == [
        'chap1.txt  chap5.txt  chap9.txt  chap13.txt',
        'chap2.txt  chap6.txt  chap10.txt',
        'chap3.txt  chap7.txt  chap11.txt',
        'chap4.txt  chap8.txt  chap12.txt'
    ]


def test_colformat_multi_columns_remainder_2():
    items = ['chap1.txt', 'chap2.txt', 'chap3.txt', 'chap4.txt',
             'chap5.txt', 'chap6.txt', 'chap7.txt', 'chap8.txt',
             'chap9.txt', 'chap10.txt', 'chap11.txt', 'chap12.txt',
             'chap13.txt', 'chap14.txt']
    assert list(utils.colformat(items, terminal_width=50)) == [
        'chap1.txt  chap5.txt  chap9.txt  chap13.txt',
        'chap2.txt  chap6.txt  chap10.txt chap14.txt',
        'chap3.txt  chap7.txt  chap11.txt',
        'chap4.txt  chap8.txt  chap12.txt'
    ]


def test_colformat_wider_than_terminal():
    items = ['a very long long name', '1111 2222 3333 4444 5555']
    assert list(utils.colformat(items, terminal_width=10)) == [
        'a very long long name',
        '1111 2222 3333 4444 5555'
    ]


def test_colformat_long_short_mixed():
    items = ['a', '1122334455667788', 'hello world', 'foo bar',
             'b', '8877665544332211', 'abcd', 'yeah']
    assert list(utils.colformat(items, terminal_width=50)) == [
        'a                foo bar          abcd',
        '1122334455667788 b                yeah',
        'hello world      8877665544332211'
    ]


def test_colformat_github_top_endpoints():
    items = ['emojis', 'events', 'feeds', 'gists', 'gitignore', 'issues',
             'legacy', 'markdown', 'meta', 'networks', 'notifications',
             'orgs', 'rate_limit', 'repos', 'repositories', 'search',
             'teams', 'user', 'users']
    assert list(utils.colformat(items, terminal_width=136)) == [
        'emojis        gists         legacy        networks      rate_limit''    search        users',  # noqa
        'events        gitignore     markdown      notifications repos         teams',  # noqa
        'feeds         issues        meta          orgs          repositories  user'  # noqa
    ]
