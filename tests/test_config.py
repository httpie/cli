from utils import _TestEnvironment, http


def test_default_options(httpbin):
    env = _TestEnvironment()
    env.config['default_options'] = ['--form']
    env.config.save()
    r = http(httpbin.url + '/post', 'foo=bar', env=env)
    assert r.json['form'] == {"foo": "bar"}


def test_default_options_overwrite(httpbin):
    env = _TestEnvironment()
    env.config['default_options'] = ['--form']
    env.config.save()
    r = http('--json', httpbin.url + '/post', 'foo=bar', env=env)
    assert r.json['json'] == {"foo": "bar"}


def test_migrate_implicit_content_type():
    config = _TestEnvironment().config

    config['implicit_content_type'] = 'json'
    config.save()
    config.load()
    assert 'implicit_content_type' not in config
    assert not config['default_options']

    config['implicit_content_type'] = 'form'
    config.save()
    config.load()
    assert 'implicit_content_type' not in config
    assert config['default_options'] == ['--form']
