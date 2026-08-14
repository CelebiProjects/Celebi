"""Tests for shell-layer runner management functions."""
import os
import tempfile
import unittest
from unittest import mock

from CelebiChrono.interface.shell_modules import communication


class TestShellRunnerManagement(unittest.TestCase):

    def _cherncc(self, **attrs):
        cc = mock.MagicMock()
        for key, value in attrs.items():
            setattr(cc, key, value)
        return cc

    def test_register_runner_forwards_settings(self):
        cc = self._cherncc(register_runner=mock.MagicMock(return_value=True))
        with mock.patch.object(communication, "ChernCommunicator") as cls:
            cls.instance.return_value = cc
            communication.register_runner(
                "local", "", "", "native", workdir="/data", cores=8)
        cc.register_runner.assert_called_once_with(
            "local", "", "", "native",
            settings={"workdir": "/data", "cores": 8})

    def test_test_runner_renders_checks(self):
        cc = self._cherncc(test_runner=mock.MagicMock(return_value={
            "status": "failed",
            "checks": {
                "snakemake": {"ok": True, "version": "8.1.0"},
                "conda": {"ok": False, "error": "not found in PATH"},
            }}))
        with mock.patch.object(communication, "ChernCommunicator") as cls:
            cls.instance.return_value = cc
            message = communication.test_runner("local")
        text = str(message)
        self.assertIn("8.1.0", text)
        self.assertIn("not found in PATH", text)

    def test_test_runner_shows_error_message(self):
        cc = self._cherncc(test_runner=mock.MagicMock(return_value={
            "status": "error",
            "message": "Runner 'ghost' not found"}))
        with mock.patch.object(communication, "ChernCommunicator") as cls:
            cls.instance.return_value = cc
            message = communication.test_runner("ghost")
        self.assertIn("Runner 'ghost' not found", str(message))

    def test_runners_writes_completion_cache(self):
        tmp = tempfile.mkdtemp()
        cc = self._cherncc(
            dite_status=mock.MagicMock(return_value="connected"),
            runners=mock.MagicMock(return_value=["local"]),
            runners_config=mock.MagicMock(return_value=[{
                "name": "local", "backend_type": "native",
                "settings": {"cores": 8},
                "health": {"status": "ok", "checked_at": "2026-08-13T10:00:00"}}]),
            runners_url=mock.MagicMock(return_value=[""]),
            runner_connection=mock.MagicMock(return_value={"status": "Connected"}),
        )
        with mock.patch.object(communication, "ChernCommunicator") as cls, \
                mock.patch.dict(os.environ, {"HOME": tmp}):
            cls.instance.return_value = cc
            message = communication.runners()
        from CelebiChrono.utils.metadata import YamlFile
        cache = YamlFile(os.path.join(tmp, ".celebi", "readline.yaml"))
        self.assertEqual(cache.read_variable("runners", []), ["local"])
        self.assertIn("ok", str(message))

    def test_add_host_calls_communicator(self):
        cc = self._cherncc()
        with mock.patch.object(communication, "ChernCommunicator") as cls:
            cls.instance.return_value = cc
            communication.add_host("myhost", "127.0.0.1:3315")
        cc.add_host.assert_called_once_with("127.0.0.1:3315")

    def test_runner_envs_renders_list(self):
        cc = self._cherncc(runner_envs=mock.MagicMock(return_value={
            "envs": [
                {"name": "base", "path": "/opt/conda", "active": True},
                {"name": "celebi", "path": "/opt/conda/envs/celebi", "active": False},
            ], "error": None}))
        with mock.patch.object(communication, "ChernCommunicator") as cls:
            cls.instance.return_value = cc
            message = communication.runner_envs("cluster")
        text = str(message)
        self.assertIn("base", text)
        self.assertIn("celebi", text)
        self.assertIn("/opt/conda/envs/celebi", text)

    def test_runner_envs_shows_error(self):
        cc = self._cherncc(runner_envs=mock.MagicMock(return_value={
            "envs": [], "error": "conda not found in PATH"}))
        with mock.patch.object(communication, "ChernCommunicator") as cls:
            cls.instance.return_value = cc
            message = communication.runner_envs("local")
        self.assertIn("conda not found", str(message))
