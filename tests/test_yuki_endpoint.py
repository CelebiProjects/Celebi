"""Regression tests for local auto-port discovery and project fallback."""

import os

import pytest

from CelebiChrono.interface.shell_modules import reana_booking
from CelebiChrono.kernel.chern_communicator import ChernCommunicator
from CelebiChrono.utils import csys


@pytest.fixture
def endpoints(tmp_path, monkeypatch):
    """Provide independently configured Yuki state and project hosts."""
    project = tmp_path / "project"
    state = tmp_path / "yuki"
    run_dir = state / "run"
    run_dir.mkdir(parents=True)
    (project / ".celebi").mkdir(parents=True)
    monkeypatch.setenv("YUKIDIR", str(state))
    monkeypatch.setattr(csys, "project_path", lambda: str(project))
    client = ChernCommunicator()
    client.add_host("remote.example:9430")
    return client, run_dir


def test_local_port_takes_priority_and_follows_restart(endpoints):
    client, run_dir = endpoints
    port_file = run_dir / "yuki.port"
    (run_dir / "yuki.pid").write_text(f"{os.getpid()}\n", encoding="ascii")
    for port in (41000, 42000):
        port_file.write_text(f"{port}\n", encoding="ascii")
        assert client.serverurl() == f"127.0.0.1:{port}"
        assert reana_booking._get_yuki_server_url() == client.serverurl()
    port_file.unlink()
    assert client.serverurl() == "remote.example:9430"
    assert reana_booking._get_yuki_server_url() == "remote.example:9430"


@pytest.mark.parametrize("contents", [b"0\n", b"65536\n", b"bad port\n", b"\xff"])
def test_invalid_local_port_uses_project_address(endpoints, contents):
    client, run_dir = endpoints
    (run_dir / "yuki.port").write_bytes(contents)
    assert client.serverurl() == "remote.example:9430"


def test_stale_pid_does_not_override_project_address(endpoints, monkeypatch):
    client, run_dir = endpoints
    (run_dir / "yuki.port").write_text("41000\n", encoding="ascii")
    (run_dir / "yuki.pid").write_text("1234\n", encoding="ascii")

    def dead_process(pid, signal):
        assert (pid, signal) == (1234, 0)
        raise ProcessLookupError

    monkeypatch.setattr(os, "kill", dead_process)
    assert client.serverurl() == "remote.example:9430"


def test_no_project_address_or_local_port_uses_default(endpoints):
    client, _ = endpoints
    os.unlink(client.config_file.file_path)
    assert client.serverurl() == "127.0.0.1:3315"
