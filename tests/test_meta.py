import pytest

from httpie.models import ELAPSED_TIME_LABEL
from httpie.output.formatters.colors import PIE_STYLE_NAMES
from .utils import http, MockEnvironment, COLOR


def test_meta_elapsed_time(httpbin):
    r = http('--meta', httpbin + '/delay/1')
    assert f'{ELAPSED_TIME_LABEL}: 1.' in r


def test_meta_extended_tls(remote_httpbin_secure):
    r = http('--verify=no', '--meta', remote_httpbin_secure + '/get')
    assert 'Connected to' in r
    assert 'Connection secured using' in r
    assert 'Server certificate' in r
    assert 'Certificate validity' in r
    assert 'Issuer' in r
    assert 'Revocation status' in r

    # If this fail, you missed two extraneous RC after the metadata render.
    # see output/streams.py L89
    # why do we need two? short story, in case of redirect, expect metadata to appear multiple times,
    # and we don't want them glued to the request line for example.
    assert str(r).endswith("\n\n")


@pytest.mark.parametrize('style', ['auto', 'fruity', *PIE_STYLE_NAMES])
def test_meta_elapsed_time_colors(httpbin, style):
    r = http('--style', style, '--meta', httpbin + '/get', env=MockEnvironment(colors=256))
    assert COLOR in r
    assert ELAPSED_TIME_LABEL in r
