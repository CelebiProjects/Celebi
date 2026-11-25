"""CLI and transport contract for private credential import."""
from unittest.mock import Mock
import pytest
from click.testing import CliRunner
from CelebiChrono.celebi_cli.cli import cli
from CelebiChrono.kernel.chern_communicator import ChernCommunicator


def test_import_and_bind(tmp_path, monkeypatch):
    keytab = tmp_path / "keytab"
    keytab.write_bytes(b"\x05\x02synthetic")
    client = Mock()
    client.add_secret.return_value = {"name": "cern-keytab", "type": "kerberos"}
    client.bind_secret.return_value = {"message": "bound"}
    monkeypatch.setattr(ChernCommunicator, "instance", lambda: client)
    result = CliRunner().invoke(cli, ["add-secret", "cern-keytab", "--file", str(keytab),
                                     "--type", "kerberos", "--principal", "user@CERN.CH"])
    assert result.exit_code == 0, result.output
    client.add_secret.assert_called_once_with("cern-keytab", str(keytab), "kerberos", "user@CERN.CH")
    result = CliRunner().invoke(cli, ["update-runner", "cern", "--secret", "cern-keytab"])
    assert result.exit_code == 0, result.output
    client.bind_secret.assert_called_once_with("cern", "cern-keytab")
    client.bind_secret.side_effect = RuntimeError("upload failed")
    assert CliRunner().invoke(cli, ["update-runner", "cern", "--secret", "cern-keytab"]).exit_code != 0


def test_transport_binary_no_redirects(tmp_path):
    client = object.__new__(ChernCommunicator)
    client.serverurl = lambda: "https://yuki.example"
    client._request = Mock(return_value=Mock(status_code=201, json=lambda: {"name": "key"}))
    keytab = tmp_path / "key"
    keytab.write_bytes(b"\x05\x02\xff\x00")
    client.add_secret("key", str(keytab), "kerberos", "user@CERN.CH")
    kwargs = client._request.call_args.kwargs
    assert kwargs["files"]["file"][1] == b"\x05\x02\xff\x00"
    assert kwargs["allow_redirects"] is False
    client.serverurl = lambda: "http://remote.example:3315"
    with pytest.raises(ValueError, match="HTTPS"):
        client.add_secret("key", str(keytab), "kerberos", "user@CERN.CH")
    assert client._request.call_count == 1


def test_help():
    assert CliRunner().invoke(cli, ["add-secret", "--help"]).exit_code == 0
    assert "--secret" in CliRunner().invoke(cli, ["update-runner", "--help"]).output
