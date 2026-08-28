"""Tests for celebi-cli runner commands."""
import unittest
from unittest import mock

from click.testing import CliRunner

from CelebiChrono.celebi_cli.commands.execution_management import (
    cache_results_command, purge_ssh_runner_cache_command,
    register_runner_command, runner_envs_command, test_runner_command,
    update_runner_command, whereabouts_command,
)


class TestCliRunnerCommands(unittest.TestCase):

    """Test Cli Runner Commands."""
    def setUp(self):
        """Set Up."""
        self.runner = CliRunner()

    def test_register_runner_passes_settings(self):
        """Test register runner passes settings."""
        with mock.patch("CelebiChrono.interface.shell.register_runner") as fn:
            result = self.runner.invoke(register_runner_command, [
                "local", "", "", "native",
                "--workdir", "/data", "--cores", "8",
            ])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with("local", "", "", "native",
                                   workdir="/data", cores=8)

    def test_register_runner_ssh_options(self):
        """Test register runner ssh options."""
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
        """Test update runner passes settings."""
        with mock.patch("CelebiChrono.interface.shell.update_runner") as fn:
            result = self.runner.invoke(update_runner_command, [
                "local", "--cores", "16", "--conda-path", "/opt/conda/bin/conda",
            ])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with("local", cores=16,
                                   conda_path="/opt/conda/bin/conda")

    def test_test_runner_command(self):
        """Test test runner command."""
        with mock.patch("CelebiChrono.interface.shell.test_runner") as fn:
            result = self.runner.invoke(test_runner_command, ["local"])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with("local", timeout=None)

    def test_purge_ssh_runner_cache_command(self):
        """Test purge ssh runner cache command passes options through."""
        with mock.patch("CelebiChrono.interface.shell.purge_ssh_runner_cache") as fn:
            result = self.runner.invoke(purge_ssh_runner_cache_command, [
                "farm", "--project", "proj", "--impression", "imp-a", "--yes",
            ])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with("farm", project="proj", impression="imp-a",
                                   dry_run=False)

    def test_purge_ssh_runner_cache_dry_run(self):
        """Test purge ssh runner cache dry run skips confirmation."""
        with mock.patch("CelebiChrono.interface.shell.purge_ssh_runner_cache") as fn:
            result = self.runner.invoke(purge_ssh_runner_cache_command, [
                "farm", "--dry-run",
            ])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with("farm", project=None, impression=None,
                                   dry_run=True)

    def test_purge_ssh_runner_cache_confirmation_aborts(self):
        """Test purge ssh runner cache aborts when confirmation declines."""
        with mock.patch("CelebiChrono.interface.shell.purge_ssh_runner_cache") as fn:
            result = self.runner.invoke(purge_ssh_runner_cache_command,
                                        ["farm"], input="n\n")
        self.assertEqual(result.exit_code, 1)
        fn.assert_not_called()

    def test_cache_results_command(self):
        """Test cache results command delegates to the shell function."""
        with mock.patch("CelebiChrono.interface.shell.cache_results") as fn:
            result = self.runner.invoke(cache_results_command, ["farm"])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with("farm")

    def test_whereabouts_command(self):
        """Test whereabouts command delegates to the shell function."""
        with mock.patch("CelebiChrono.interface.shell.whereabouts") as fn:
            result = self.runner.invoke(whereabouts_command, [])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()

    def test_runner_envs_command(self):
        """Test the runner envs command."""
        with mock.patch("CelebiChrono.interface.shell.runner_envs") as fn:
            result = self.runner.invoke(runner_envs_command, ["cluster"])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with("cluster")
