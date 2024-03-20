import pytest

from httpie.models import ELAPSED_TIME_LABEL, ELAPSED_DNS_RESOLUTION_LABEL, ELAPSED_ESTABLISH_CONN, ELAPSED_REQUEST_SEND, ELAPSED_TLS_HANDSHAKE
from httpie.output.formatters.colors import PIE_STYLE_NAMES
from .utils import http, MockEnvironment, COLOR


def test_meta_elapsed_time(httpbin):
    r = http('--meta', httpbin + '/delay/1')
    assert f'{ELAPSED_TIME_LABEL}: 1.' in r
    assert ELAPSED_DNS_RESOLUTION_LABEL in r
    assert ELAPSED_ESTABLISH_CONN in r
    assert ELAPSED_REQUEST_SEND in r


def test_meta_extended_tls(remote_httpbin_secure):
    r = http('--verify=no', '--meta', remote_httpbin_secure + '/get')
    assert 'Connected to' in r
    assert 'Connection secured using' in r
    assert 'Server certificate' in r
    assert 'Certificate validity' in r
    assert 'Issuer' in r
    assert 'Revocation status' in r
    assert ELAPSED_TLS_HANDSHAKE in r


@pytest.mark.parametrize('style', ['auto', 'fruity', *PIE_STYLE_NAMES])
def test_meta_elapsed_time_colors(httpbin, style):
    r = http('--style', style, '--meta', httpbin + '/get', env=MockEnvironment(colors=256))
    assert COLOR in r
    assert ELAPSED_TIME_LABEL in r
