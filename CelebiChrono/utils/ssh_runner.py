""" Direct SSH execution helper used by `test ssh <runner>`.

Connects to a remote machine with paramiko, uploads a tar over SFTP,
extracts it, and streams command output line by line as it arrives.
"""
import os
import shlex
import tempfile
import time

import paramiko


def _chomp(buf):
    """Split a byte buffer on newlines, keeping the trailing partial line."""
    if "\n" not in buf:
        return [], buf
    *lines, tail = buf.split("\n")
    return lines, tail


def _noop(_line):
    """Default line consumer doing nothing."""


def _sftp_makedirs(sftp, path):
    """Create a remote directory tree with SFTP (os.makedirs equivalent)."""
    current = ""
    for part in path.strip("/").split("/"):
        current += "/" + part
        try:
            sftp.stat(current)
        except IOError:
            sftp.mkdir(current)


def sanitized_env_prefix(conda_base=""):
    """Shell prefix that resets PYTHONPATH/LD_LIBRARY_PATH and curates PATH.

    Drops the ambient shell environment so runs never depend on the
    submitter's .bashrc etc. When ``conda_base`` is given, its bin dir
    leads the curated PATH (needed for conda activation).
    """
    path_bits = []
    if conda_base:
        path_bits.append(f"{conda_base}/bin")
    path_bits += ["$HOME/.local/bin", "/usr/local/bin", "/usr/bin", "/bin"]
    return ('unset PYTHONPATH LD_LIBRARY_PATH; '
            f'export PATH="{":".join(path_bits)}"; ')


class SshRunner:
    """A direct SSH connection to a remote machine."""

    def __init__(self, host, user, port=22, *, key_content="", key_path=""):  # pylint: disable=too-many-arguments
        self._host = host
        self._user = user
        self._port = port
        self._key_content = key_content
        self._key_path = key_path
        self._client = None
        self._key_file = None

    def connect(self):
        """Open the connection and return self."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        kwargs = {
            "hostname": self._host,
            "port": self._port,
            "username": self._user,
            "timeout": 30,
            "banner_timeout": 30,
        }
        if self._key_content:
            # pylint: disable=consider-using-with
            # The temp file lives until close(); a with block ends too early.
            self._key_file = tempfile.NamedTemporaryFile(
                "w", prefix="celebi_key_", delete=False)
            os.chmod(self._key_file.name, 0o600)
            self._key_file.write(self._key_content)
            self._key_file.flush()
            kwargs["key_filename"] = self._key_file.name
        elif self._key_path:
            expanded = os.path.expanduser(self._key_path)
            if not os.path.exists(expanded):
                raise ValueError(f"SSH key file not found: {self._key_path}")
            kwargs["key_filename"] = expanded
        client.connect(**kwargs)
        self._client = client
        return self

    def close(self):
        """Close the connection and remove any temp key file."""
        if self._client is not None:
            self._client.close()
            self._client = None
        if self._key_file is not None:
            self._key_file.close()
            os.unlink(self._key_file.name)
            self._key_file = None

    def __enter__(self):
        return self.connect()

    def __exit__(self, _exc_type, _exc_value, _traceback):
        self.close()

    def exec_stream(self, command, cwd=None, on_line=None):
        """Run a command remotely, delivering output lines live.

        Returns the remote exit code.
        """
        if on_line is None:
            on_line = _noop
        channel = self._client.get_transport().open_session()
        if cwd:
            command = f"cd {shlex.quote(cwd)} && {command}"
        channel.exec_command(command)
        out_buf = err_buf = ""
        while not channel.exit_status_ready():
            if channel.recv_ready():
                out_buf += channel.recv(65536).decode("utf-8", errors="replace")
            if channel.recv_stderr_ready():
                err_buf += channel.recv_stderr(65536).decode("utf-8",
                                                             errors="replace")
            out_lines, out_buf = _chomp(out_buf)
            err_lines, err_buf = _chomp(err_buf)
            for line in out_lines:
                on_line(line)
            for line in err_lines:
                on_line(line)
            time.sleep(0.05)
        while channel.recv_ready():
            out_buf += channel.recv(65536).decode("utf-8", errors="replace")
        while channel.recv_stderr_ready():
            err_buf += channel.recv_stderr(65536).decode("utf-8",
                                                         errors="replace")
        for line in out_buf.splitlines() + err_buf.splitlines():
            if line:
                on_line(line)
        return channel.recv_exit_status()

    def conda_base_dir(self):
        """Return the remote conda base dir from `conda info --base`.

        Returns an empty string when conda is unavailable remotely.
        """
        lines = []
        code = self.exec_stream("conda info --base", on_line=lines.append)
        if code:
            return ""
        return lines[0].strip() if lines else ""

    def put_tar(self, local_tar, remote_dir):
        """Upload a tar.gz and extract it into remote_dir on the remote.

        The remote dir tree is created over SFTP (no extra exec round trip),
        and a single exec extracts the tar and removes it — each exec costs
        seconds of remote shell startup.
        """
        name = os.path.basename(local_tar)
        remote_tar = f"{remote_dir.rstrip('/')}/{name}"
        sftp = self._client.open_sftp()
        try:
            _sftp_makedirs(sftp, remote_dir)
            sftp.put(local_tar, remote_tar)
        finally:
            sftp.close()
        lines = []
        code = self.exec_stream(
            f"tar -xzf {shlex.quote(remote_tar)} -C {shlex.quote(remote_dir)} && "
            f"rm {shlex.quote(remote_tar)}",
            on_line=lines.append)
        if code:
            raise RuntimeError(
                f"Failed to extract {name} on remote: {'; '.join(lines)}")
