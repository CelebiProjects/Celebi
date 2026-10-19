"""Connection loss must not restart publishing or replay mutating Yuki calls."""
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import Mock

import pytest
import requests

from CelebiChrono.interface.shell_modules import server_booking as client


@pytest.mark.parametrize('method,path,body', [
    ('GET', '/api/projects/project/impress/job', None),
    ('POST', '/api/projects/project/bookkeep/authorize', None),
    ('POST', '/api/projects/project/impressions/sync', {'manifest': []}),
    ('POST', '/api/projects/project/impress', {'git_commit': 'a' * 40}),
])
def test_safe_requests_retry_with_identical_body_and_new_connection(monkeypatch, method, path, body):
    monkeypatch.setattr(client.time, 'sleep', lambda _: None)
    session = Mock()
    response = Mock(status_code=200)
    response.json.return_value = {'ok': True}
    session.request.side_effect = [requests.ConnectionError('Remote end closed'), response]
    assert client._request(session, method, 'http://server' + path, body) == {'ok': True}
    assert session.request.call_count == 2
    session.close.assert_called_once()
    for call in session.request.call_args_list:
        assert call.kwargs['json'] == body
        assert call.kwargs['headers']['Connection'] == 'close'
        assert call.kwargs['allow_redirects'] is False


@pytest.mark.parametrize('path,body', [
    ('/book-celebi-server/pack', {'impressions': []}),
    ('/book-celebi-server/upload', {'archives': []}),
    ('/api/projects/project/impress', {}),
    ('/api/projects/project/impress', {'git_commit': None}),
    ('/api/projects/project/impress', {'git_commit': 'HEAD'}),
    ('/api/projects', {}),
])
def test_unsafe_requests_are_not_replayed(path, body):
    session = Mock()
    session.request.side_effect = requests.ConnectionError('possibly accepted')
    with pytest.raises(ValueError, match='1 attempt'):
        client._request(session, 'POST', 'http://server' + path, body)
    assert session.request.call_count == 1


def test_retries_are_bounded_and_error_identifies_stage_without_secrets(monkeypatch):
    monkeypatch.setattr(client.time, 'sleep', lambda _: None)
    session = Mock()
    session.request.side_effect = requests.ConnectionError('https://secret@private')
    with pytest.raises(ValueError, match=r'POST /api/projects/p/impressions/sync.*3 attempt') as error:
        client._request(session, 'POST', 'http://server/api/projects/p/impressions/sync', {})
    assert 'secret' not in str(error.value)
    assert session.request.call_count == session.close.call_count == 3


@pytest.mark.parametrize('failure', [requests.exceptions.SSLError('cert'), requests.ReadTimeout('slow')])
def test_tls_and_timeout_errors_are_not_retried(failure):
    session = Mock()
    session.request.side_effect = failure
    with pytest.raises(ValueError):
        client._request(session, 'GET', 'http://server/status')
    assert session.request.call_count == 1


def test_actual_remote_disconnect_is_recovered_without_whole_workflow_retry():
    observed = []
    class Handler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'
        def do_POST(self):
            body = self.rfile.read(int(self.headers['Content-Length']))
            observed.append((self.path, body, self.headers.get('Connection')))
            if len(observed) == 1:
                self.close_connection = True
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
                return
            payload = b'{"to_upload":[],"grant":null}'
            self.send_response(200)
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(payload)
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with requests.Session() as session:
            session.trust_env = False
            result = client._request(session, 'POST',
                f'http://127.0.0.1:{server.server_port}/api/projects/p/impressions/sync',
                {'manifest': []})
        assert result == {'to_upload': [], 'grant': None}
        assert len(observed) == 2
        assert observed[0] == observed[1]
        assert observed[0][2] == 'close'
        assert json.loads(observed[0][1]) == {'manifest': []}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
