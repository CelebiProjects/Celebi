"""Tests for celebi-cli runner commands."""
import unittest
from unittest import mock

from click.testing import CliRunner

from CelebiChrono.celebi_cli.commands.execution_management import (
    register_runner_command, runner_envs_command, test_runner_command,
    update_runner_command,
)


class TestCliRunnerCommands(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()

    def test_register_runner_passes_settings(self):
        with mock.patch("CelebiChrono.interface.shell.register_runner") as fn:
            result = self.runner.invoke(register_runner_command, [
                "local", "", "", "native",
                "--workdir", "/data", "--cores", "8",
            ])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with("local", "", "", "native",
                                   workdir="/data", cores=8)

    def test_register_runner_ssh_options(self):
        with mock.patch("CelebiChrono.interface.shell.register_runner") as fn:
            result = self.runner.invoke(register_runner_command, [
                "cluster", "", "", "ssh",
                "--ssh-host", "h", "--ssh-user", "u", "--ssh-port", "2222",
                "--remote-workdir", "/remote",
            ])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with("cluster", "", "", "ssh",
                                   ssh_host="h", ssh_user="u", ssh_port=2222,
                                   remote_workdir="/remote")

    def test_update_runner_passes_settings(self):
        with mock.patch("CelebiChrono.interface.shell.update_runner") as fn:
            result = self.runner.invoke(update_runner_command, [
                "local", "--cores", "16", "--conda-path", "/opt/conda/bin/conda",
            ])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with("local", cores=16,
                                   conda_path="/opt/conda/bin/conda")

    def test_test_runner_command(self):
        with mock.patch("CelebiChrono.interface.shell.test_runner") as fn:
            result = self.runner.invoke(test_runner_command, ["local"])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with("local")


if __name__ == "__main__":
    unittest.main()

    def test_runner_envs_command(self):
        with mock.patch("CelebiChrono.interface.shell.runner_envs") as fn:
            result = self.runner.invoke(runner_envs_command, ["cluster"])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with("cluster")
