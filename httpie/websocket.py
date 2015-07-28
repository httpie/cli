import json
from websocket import create_connection


class WebSocketResponse(object):
    def __init__(self, data=None, headers=None, status=200):
        self.data = data.encode()
        self.status = status
        self.headers = headers
        self.ws = True


def handle_ws(url, data=None):
    ws = create_connection(url)
    if not data:
        ws.send(None)
    else:
        ws.send(json.dumps(data))
    result = ws.recv()
    response = WebSocketResponse(result, headers=ws.headers, status=ws.status)
    ws.close()
    return response
