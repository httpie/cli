from socket import socket
from multiprocessing import Process

from flask import Flask, make_response

from .utils import http

app = Flask(__name__)


@app.route('/')
def main():
    response = make_response()
    response.set_cookie('hello', value='world')
    response.set_cookie('oatmeal_raisin', value='is the best')
    return response


def available_port():
    conn = socket()
    conn.bind(('', 0))
    port = conn.getsockname()[1]
    conn.close()
    return port


def test_cookie_parser():
    port = available_port()
    server = Process(target=app.run, kwargs={'port': 8888})
    try:
        server.start()
        response = http(f'http://localhost:{port}/')
        assert 'Set-Cookie: hello=world; Path=/' in response
        assert 'Set-Cookie: oatmeal_raisin="is the best"; Path=/' in response
    finally:
        server.terminate()
        server.join()
