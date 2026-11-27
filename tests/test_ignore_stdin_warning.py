"""Regression tests for --ignore-stdin warning on failed requests with stdin (#1525)."""

import io
from unittest.mock import patch

import requests

from httpie.cli.definition import parser
from httpie.context import Environment
from httpie.core import program


def _make_pair(status_code: int, body=b'leaked-stdin'):
    req = requests.Request('POST', 'http://example.com/api', data=body).prepare()
    resp = requests.Response()
    resp.status_code = status_code
    resp.reason = 'Bad Request' if status_code == 400 else 'OK'
    payload = b'Bad Request' if status_code == 400 else b'OK'
    resp.raw = io.BytesIO(payload)
    resp.raw.version = 11
    resp.raw.status = status_code
    resp.raw.reason = resp.reason
    resp.request = req
    resp.url = req.url
    return [req, resp]


def _run_program(cli_args, status_code, stdin_isatty=False, stdin_bytes=b'leaked-stdin'):
    stdout = io.BytesIO()
    stderr = io.StringIO()
    stdin = io.BytesIO(stdin_bytes)
    env = Environment(
        stdin=stdin,
        stdin_isatty=stdin_isatty,
        stdout=stdout,
        stdout_isatty=False,
        stderr=stderr,
        stderr_isatty=False,
    )
    args = parser.parse_args(args=cli_args, env=env)
    messages = _make_pair(
        status_code,
        body=stdin_bytes if not args.ignore_stdin and not stdin_isatty else None,
    )
    with patch('httpie.core.collect_messages', return_value=messages):
        program(args=args, env=env)
    return stderr.getvalue()


def test_warns_about_ignore_stdin_on_failed_request_with_stdin():
    err = _run_program(['http://example.com/api'], status_code=400, stdin_isatty=False)
    assert '--ignore-stdin' in err


def test_no_warning_when_ignore_stdin_is_passed():
    err = _run_program(['--ignore-stdin', 'http://example.com/api'], status_code=400, stdin_isatty=False)
    assert '--ignore-stdin' not in err


def test_no_warning_on_successful_request_with_stdin():
    err = _run_program(['http://example.com/api'], status_code=200, stdin_isatty=False)
    assert '--ignore-stdin' not in err
