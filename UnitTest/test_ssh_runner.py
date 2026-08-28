"""Tests for CelebiChrono.utils.ssh_runner."""
import os
from unittest import mock

from CelebiChrono.utils import ssh_runner


class FakeChannel:
    """Scripted channel: events are ("out"|"err", bytes)."""

    def __init__(self, events, exit_code=0, exit_codes=None, order=None):
        self._events = list(events)
        self._exit_code = exit_code
        self._exit_codes = list(exit_codes) if exit_codes else []
        self._order = order
        self._exec_command = None

    def exec_command(self, command):
        """Record the command."""
        self._exec_command = command
        if self._order is not None:
            self._order.append(("exec", command))

    def recv_ready(self):
        """True when the next event is stdout."""
        return bool(self._events) and self._events[0][0] == "out"

    def recv_stderr_ready(self):
        """True when the next event is stderr."""
        return bool(self._events) and self._events[0][0] == "err"

    def recv(self, _nbytes):
        """Pop the next stdout event."""
        return self._pop("out")

    def recv_stderr(self, _nbytes):
        """Pop the next stderr event."""
        return self._pop("err")

    def _pop(self, stream):
        if self._events and self._events[0][0] == stream:
            return self._events.pop(0)[1]
        return b""

    def exit_status_ready(self):
        """True once all events are drained."""
        return not self._events

    def recv_exit_status(self):
        """Return the next scripted exit code."""
        if self._exit_codes:
            return self._exit_codes.pop(0)
        return self._exit_code


class FakeTransport:
    """Yields a scripted channel."""

    def __init__(self, channel):
        self._channel = channel

    def open_session(self):
        """Return the scripted channel."""
        return self._channel


class FakeSFTP:
    """Records uploaded files."""

    def __init__(self, order=None):
        self.puts = []
        self._order = order

    def put(self, local, remote):
        """Record the upload."""
        self.puts.append((local, remote))
        if self._order is not None:
            self._order.append(("put", local, remote))

    def close(self):
        """No-op."""


class FakeClient:
    """Records connect() and exposes fakes."""

    def __init__(self, channel=None, order=None):
        self.connect_kwargs = None
        self.closed = False
        self.order = order if order is not None else []
        self._channel = channel or FakeChannel([], order=self.order)
        if self._channel._order is None:
            self._channel._order = self.order
        self._sftp = FakeSFTP(order=self.order)

    def set_missing_host_key_policy(self, _policy):
        """Accept the policy."""

    def connect(self, **kwargs):
        """Record the connect arguments."""
        self.connect_kwargs = kwargs

    def get_transport(self):
        """Return the fake transport."""
        return FakeTransport(self._channel)

    def open_sftp(self):
        """Return the fake sftp."""
        return self._sftp

    def close(self):
        """Mark closed."""
        self.closed = True


def _patch_paramiko(client):
    fake_paramiko = mock.MagicMock()
    fake_paramiko.SSHClient.return_value = client
    return mock.patch.object(ssh_runner, "paramiko", fake_paramiko)


def test_connect_writes_key_content_to_temp_file():
    """Key content is written to a 600 temp file passed as key_filename."""
    client = FakeClient()
    runner = ssh_runner.SshRunner(host="h", user="u", port=2222,
                                  key_content="-----BEGIN KEY-----")
    with _patch_paramiko(client):
        runner.connect()
    kwargs = client.connect_kwargs
    assert kwargs["hostname"] == "h"
    assert kwargs["username"] == "u"
    assert kwargs["port"] == 2222
    key_file = kwargs["key_filename"]
    assert os.path.exists(key_file)
    assert os.stat(key_file).st_mode & 0o777 == 0o600
    with open(key_file, encoding="utf-8") as f:
        assert f.read() == "-----BEGIN KEY-----"


def test_connect_uses_key_path_when_no_content(tmp_path):
    """An existing client-side key_path is passed through untouched."""
    key_file = tmp_path / "id_rsa"
    key_file.write_text("KEY")
    client = FakeClient()
    runner = ssh_runner.SshRunner(host="h", user="u", key_path=str(key_file))
    with _patch_paramiko(client):
        runner.connect()
    assert client.connect_kwargs["key_filename"] == str(key_file)


def test_connect_missing_key_path_raises():
    """A nonexistent key_path raises ValueError instead of a paramiko error."""
    client = FakeClient()
    runner = ssh_runner.SshRunner(host="h", user="u",
                                  key_path="/nonexistent/id_rsa")
    with _patch_paramiko(client):
        try:
            runner.connect()
        except ValueError as e:
            assert "/nonexistent/id_rsa" in str(e)
        else:
            raise AssertionError("expected ValueError")


def test_exec_stream_yields_interleaved_lines_and_exit_code():
    """Live stdout/stderr chunks are delivered to the callback, then the code."""
    channel = FakeChannel([
        ("out", b"hello wo"),
        ("err", b"bad thi"),
        ("out", b"rld\nnext"),
        ("err", b"ng\n"),
        ("out", b" line\n"),
    ], exit_code=3)
    client = FakeClient(channel=channel)
    runner = ssh_runner.SshRunner(host="h", user="u")
    with _patch_paramiko(client):
        runner.connect()
        seen = []
        code = runner.exec_stream("echo hi", cwd="/data/yuki/tests/x",
                                  on_line=seen.append)
    assert seen == ["hello world", "bad thing", "next line"]
    assert code == 3


def test_exec_stream_prepends_cd_for_cwd():
    """A cwd argument becomes a `cd` prefix on the remote command."""
    channel = FakeChannel([], exit_code=0)
    client = FakeClient(channel=channel)
    runner = ssh_runner.SshRunner(host="h", user="u")
    with _patch_paramiko(client):
        runner.connect()
        runner.exec_stream("echo hi", cwd="/data/yuki/tests/x")
    assert channel._exec_command == "cd /data/yuki/tests/x && echo hi"


def test_put_tar_creates_remote_dir_before_upload():
    """The remote parent dir is created before the SFTP upload runs."""
    client = FakeClient(channel=FakeChannel([], exit_code=0))
    runner = ssh_runner.SshRunner(host="h", user="u")
    with _patch_paramiko(client):
        runner.connect()
        runner.put_tar("/local/workdir.tar.gz", "/data/yuki/tests/x")
    assert client.order[0][0] == "exec"
    assert "mkdir -p" in client.order[0][1]
    assert client.order[1][0] == "put"
    assert client.order[1][2] == "/data/yuki/tests/x/workdir.tar.gz"
    assert client.order[2][0] == "exec"
    assert "tar -xzf" in client.order[2][1]


def test_put_tar_uploads_and_extracts():
    """put_tar SFTP-uploads the tar and extracts it on the remote."""
    channel = FakeChannel([], exit_code=0)
    client = FakeClient(channel=channel)
    runner = ssh_runner.SshRunner(host="h", user="u")
    with _patch_paramiko(client):
        runner.connect()
        runner.put_tar("/local/workdir.tar.gz", "/data/yuki/tests")
    assert client._sftp.puts == [("/local/workdir.tar.gz",
                                  "/data/yuki/tests/workdir.tar.gz")]
    command = channel._exec_command
    assert "tar -xzf" in command and "workdir.tar.gz" in command


def test_put_tar_failure_raises():
    """A nonzero extract exit code raises RuntimeError."""
    client = FakeClient(channel=FakeChannel([], exit_codes=[0, 1]))
    runner = ssh_runner.SshRunner(host="h", user="u")
    with _patch_paramiko(client):
        runner.connect()
        try:
            runner.put_tar("/local/workdir.tar.gz", "/data/yuki/tests")
        except RuntimeError as e:
            assert "extract" in str(e)
        else:
            raise AssertionError("expected RuntimeError")


def test_close_removes_temp_key_and_closes_client():
    """close() cleans up the temp key file and the client."""
    client = FakeClient()
    runner = ssh_runner.SshRunner(host="h", user="u", key_content="KEY")
    with _patch_paramiko(client):
        runner.connect()
        key_file = client.connect_kwargs["key_filename"]
        runner.close()
    assert client.closed
    assert not os.path.exists(key_file)


def test_conda_base_dir_reads_first_line():
    """conda_base_dir runs conda info --base and returns the first line."""
    channel = FakeChannel([("out", b"/opt/conda\nextra\n")], exit_code=0)
    client = FakeClient(channel=channel)
    runner = ssh_runner.SshRunner(host="h", user="u")
    with _patch_paramiko(client):
        runner.connect()
        assert runner.conda_base_dir() == "/opt/conda"
    assert channel._exec_command == "conda info --base"


def test_conda_base_dir_empty_on_failure():
    """A failing conda probe yields an empty base dir."""
    client = FakeClient(channel=FakeChannel([], exit_code=1))
    runner = ssh_runner.SshRunner(host="h", user="u")
    with _patch_paramiko(client):
        runner.connect()
        assert runner.conda_base_dir() == ""


def test_sanitized_env_prefix_without_conda():
    """Without a conda base, the curated PATH keeps only system dirs."""
    prefix = ssh_runner.sanitized_env_prefix("")
    assert prefix == ('unset PYTHONPATH LD_LIBRARY_PATH; '
                      'export PATH="$HOME/.local/bin:/usr/local/bin:'
                      '/usr/bin:/bin"; ')


def test_sanitized_env_prefix_with_conda():
    """With a conda base, its bin dir leads the curated PATH."""
    prefix = ssh_runner.sanitized_env_prefix("/opt/conda")
    assert prefix.startswith("unset PYTHONPATH LD_LIBRARY_PATH; ")
    assert 'export PATH="/opt/conda/bin:$HOME/.local/bin' in prefix
    assert ":$PATH" not in prefix
