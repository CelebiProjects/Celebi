"""Tests for ChernCommunicator.runner_ssh_config."""
from unittest import mock

import requests

from CelebiChrono.kernel.chern_communicator import ChernCommunicator


class MockResponse:
    """Minimal requests.Response stand-in."""

    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        """Return the canned body."""
        return self._json

    def raise_for_status(self):
        """Raise for 4xx/5xx like requests.Response does."""
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"{self.status_code}")


def test_runner_ssh_config_gets_runner_settings():
    """The GET carries the runner name and returns the config dict."""
    cc = ChernCommunicator.instance()
    config = {"host": "cluster.example.com", "user": "alice", "port": 22,
              "key": "-----BEGIN KEY-----", "key_path": "/srv/keys/r1",
              "remote_workdir": "/data/yuki"}
    with mock.patch("requests.get") as get:
        get.return_value = MockResponse(200, config)
        result = cc.runner_ssh_config("farm")
        assert result == config
        get.assert_called_once()
        args, _kwargs = get.call_args
        assert args[0].endswith("/runner-ssh-config/farm")


def test_runner_ssh_config_passes_environment_param():
    """An environment is sent as a query parameter for server resolution."""
    cc = ChernCommunicator.instance()
    with mock.patch("requests.get") as get:
        get.return_value = MockResponse(200, {"host": "h", "user": "u",
                                              "conda_env": "env_root"})
        result = cc.runner_ssh_config("farm", environment="env_root")
        assert result["conda_env"] == "env_root"
        args, _kwargs = get.call_args
        assert args[0].endswith(
            "/runner-ssh-config/farm?environment=env_root")


def test_runner_ssh_config_unknown_runner_returns_none():
    """A 404 from the server yields None."""
    cc = ChernCommunicator.instance()
    with mock.patch("requests.get") as get:
        get.return_value = MockResponse(404, {"error": "runner 'farm' not found"})
        assert cc.runner_ssh_config("farm") is None


def test_runner_ssh_config_connection_error():
    """Transport failures raise ConnectionError."""
    cc = ChernCommunicator.instance()
    with mock.patch("requests.get") as get:
        get.side_effect = requests.exceptions.ConnectionError("refused")
        try:
            cc.runner_ssh_config("farm")
        except ConnectionError as e:
            assert "refused" in str(e)
        else:
            raise AssertionError("expected ConnectionError")
