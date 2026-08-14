"""Tests for chern-shell runner commands (test_runner/runner_envs/ssh register)."""
import unittest
from unittest import mock

from CelebiChrono.interface.chern_shell import commands_environment
from CelebiChrono.interface.chern_shell.commands_environment import (
    EnvironmentCommands, _parse_update_runner_args,
)
from CelebiChrono.interface.chern_shell.completions import ChernShellCompletions


class TestParseUpdateRunnerArgs(unittest.TestCase):

    def test_new_settings_options(self):
        name, kwargs = _parse_update_runner_args(
            "local --workdir /data --cores 8 --mem-mb 4096 "
            "--conda-path /opt/conda/bin/conda --snakemake-path /usr/bin/snakemake")
        self.assertEqual(name, "local")
        self.assertEqual(kwargs["workdir"], "/data")
        self.assertEqual(kwargs["cores"], 8)
        self.assertEqual(kwargs["mem_mb"], 4096)
        self.assertEqual(kwargs["conda_path"], "/opt/conda/bin/conda")
        self.assertEqual(kwargs["snakemake_path"], "/usr/bin/snakemake")

    def test_ssh_options(self):
        name, kwargs = _parse_update_runner_args(
            "cluster --ssh-host h --ssh-user u --ssh-port 2222 "
            "--ssh-key-path /k --remote-workdir /remote")
        self.assertEqual(name, "cluster")
        self.assertEqual(kwargs["ssh_host"], "h")
        self.assertEqual(kwargs["ssh_user"], "u")
        self.assertEqual(kwargs["ssh_port"], 2222)
        self.assertEqual(kwargs["ssh_key_path"], "/k")
        self.assertEqual(kwargs["remote_workdir"], "/remote")

    def test_existing_options_still_work(self):
        name, kwargs = _parse_update_runner_args(
            "cern --url https://x --token t --backend-type reana "
            "--use-kerberos --eos-mount-point /eos")
        self.assertEqual(name, "cern")
        self.assertEqual(kwargs["url"], "https://x")
        self.assertEqual(kwargs["use_kerberos"], True)
        self.assertEqual(kwargs["eos_mount_point"], "/eos")


class TestRunnerShellCommands(unittest.TestCase):

    def setUp(self):
        self.cmds = EnvironmentCommands.__new__(EnvironmentCommands)

    def test_do_test_runner(self):
        with mock.patch.object(commands_environment, "shell") as shell:
            shell.test_runner.return_value = mock.MagicMock(
                messages=[("ok", "success")], colored=lambda: "rendered")
            self.cmds.do_test_runner("pkufarm212")
        shell.test_runner.assert_called_once_with("pkufarm212")

    def test_do_runner_envs(self):
        with mock.patch.object(commands_environment, "shell") as shell:
            shell.runner_envs.return_value = mock.MagicMock(
                messages=[("ok", "success")], colored=lambda: "rendered")
            self.cmds.do_runner_envs("pkufarm212")
        shell.runner_envs.assert_called_once_with("pkufarm212")

    def test_do_test_runner_requires_name(self):
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch("builtins.print") as pr:
            self.cmds.do_test_runner("")
        shell.test_runner.assert_not_called()
        self.assertTrue(pr.called)

    def test_do_register_runner_ssh_flow(self):
        answers = iter(["ssh", "cluster", "h", "u", "", "22", "/remote"])
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch("builtins.input", lambda prompt="": next(answers)):
            shell.register_runner.return_value = mock.MagicMock(messages=[])
            self.cmds.do_register_runner("")
        shell.register_runner.assert_called_once_with(
            "cluster", "", "", "ssh",
            ssh_host="h", ssh_user="u", ssh_port=22, remote_workdir="/remote")

    def test_do_register_runner_reana_flow_kept(self):
        answers = iter(["reana", "cern", "https://reana.cern.ch", "tok"])
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch("builtins.input", lambda prompt="": next(answers)):
            shell.register_runner.return_value = mock.MagicMock(messages=[])
            self.cmds.do_register_runner("")
        shell.register_runner.assert_called_once_with(
            "cern", "https://reana.cern.ch", "tok", "reana")


class TestRunnerCompletions(unittest.TestCase):

    def setUp(self):
        self.comp = ChernShellCompletions.__new__(ChernShellCompletions)
        self.comp.readline_file = mock.MagicMock()
        self.comp.readline_file.read_variable.return_value = ["cern", "local", "pkufarm212"]

    def test_complete_test_runner(self):
        self.assertEqual(self.comp.complete_test_runner("p", "test_runner p", 0, 0),
                         ["pkufarm212"])

    def test_complete_runner_envs(self):
        self.assertEqual(self.comp.complete_runner_envs("", "runner_envs ", 0, 0),
                         ["cern", "local", "pkufarm212"])


if __name__ == "__main__":
    unittest.main()
