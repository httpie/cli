import os.path
from pathlib import Path

import pytest

from httpie.compat import is_windows
from httpie.config import Config, get_default_config_dir
from utils import HTTP_OK, MockEnvironment, http


def test_default_options(httpbin):
    env = MockEnvironment()
    env.config['default_options'] = ['--form']
    env.config.save()
    r = http(httpbin.url + '/post', 'foo=bar', env=env)
    assert r.json['form'] == {
        "foo": "bar"
    }


def test_config_file_not_valid(httpbin):
    env = MockEnvironment()
    env.create_temp_config_dir()
    with (env.config_dir / Config.FILENAME).open('w') as f:
        f.write('{invalid json}')
    r = http(httpbin + '/get', env=env)
    assert HTTP_OK in r
    assert 'http: warning' in r.stderr
    assert 'invalid config file' in r.stderr


@pytest.mark.skipif(is_windows, reason='cannot chmod 000 on Windows')
def test_config_file_inaccessible(httpbin):
    env = MockEnvironment()
    env.create_temp_config_dir()
    config_path = env.config_dir / Config.FILENAME
    assert not config_path.exists()
    config_path.touch(0o000)
    assert config_path.exists()
    r = http(httpbin + '/get', env=env)
    assert HTTP_OK in r
    assert 'http: warning' in r.stderr
    assert 'cannot read config file' in r.stderr


def test_default_options_overwrite(httpbin):
    env = MockEnvironment()
    env.config['default_options'] = ['--form']
    env.config.save()
    r = http('--json', httpbin.url + '/post', 'foo=bar', env=env)
    assert r.json['json'] == {
        "foo": "bar"
    }


@pytest.mark.skipif(is_windows, reason='XDG_CONFIG_HOME is only supported on *nix')
def test_config_file_location_xdg(monkeypatch, tmp_path):
    monkeypatch.delenv('HTTPIE_CONFIG_DIR', raising=False)
    home = tmp_path.absolute().as_posix()
    monkeypatch.setenv('HOME', home)
    xdg_config_home = tmp_path.joinpath("different_config")
    os.mkdir(xdg_config_home)
    monkeypatch.setenv('XDG_CONFIG_HOME', xdg_config_home.absolute().as_posix())
    assert get_default_config_dir() == xdg_config_home.joinpath('httpie')
    monkeypatch.delenv('XDG_CONFIG_HOME')
    # NB: this should be true even though .config doesn't exist.
    assert get_default_config_dir() == tmp_path.joinpath('.config', 'httpie')
    monkeypatch.setenv('XDG_CONFIG_HOME', 'some/nonabsolute/path')
    assert get_default_config_dir() == tmp_path.joinpath('.config', 'httpie')


@pytest.mark.skipif(is_windows, reason='legacy config file location is only checked on *nix')
def test_config_file_location_legacy(monkeypatch, tmp_path):
    monkeypatch.delenv('HTTPIE_CONFIG_DIR', raising=False)
    home = tmp_path.absolute().as_posix()
    monkeypatch.setenv('HOME', home)
    os.mkdir(tmp_path.joinpath('.httpie'))
    assert get_default_config_dir() == tmp_path.joinpath('.httpie')


@pytest.mark.skipif(not is_windows, reason='windows-only')
def test_config_file_location_windows(monkeypatch):
    monkeypatch.delenv('HTTPIE_CONFIG_DIR', raising=False)
    assert get_default_config_dir() == Path(os.path.expandvars(r'%APPDATA%\httpie'))


def test_config_file_location_custom(monkeypatch, tmp_path):
    httpie_config_dir = tmp_path.joinpath('custom', 'directory')
    monkeypatch.setenv('HTTPIE_CONFIG_DIR', str(httpie_config_dir.absolute()))
    assert get_default_config_dir() == httpie_config_dir
