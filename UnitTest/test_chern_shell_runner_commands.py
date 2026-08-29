"""Tests for chern-shell runner commands (test_runner/runner_envs/ssh register)."""
import unittest
from unittest import mock

from CelebiChrono.interface.chern_shell import commands_environment
from CelebiChrono.interface.chern_shell import commands_task
from CelebiChrono.interface.chern_shell.commands_environment import (
    EnvironmentCommands, _parse_update_runner_args,
)
from CelebiChrono.interface.chern_shell.commands_task import TaskCommands
from CelebiChrono.interface.chern_shell.completions import ChernShellCompletions


class TestParseUpdateRunnerArgs(unittest.TestCase):

    """Test Parse Update Runner Args."""
    def test_new_settings_options(self):
        """Test new settings options."""
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
        """Test ssh options."""
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
        """Test existing options still work."""
        name, kwargs = _parse_update_runner_args(
            "cern --url https://x --token t --backend-type reana "
            "--use-kerberos --eos-mount-point /eos")
        self.assertEqual(name, "cern")
        self.assertEqual(kwargs["url"], "https://x")
        self.assertEqual(kwargs["use_kerberos"], True)
        self.assertEqual(kwargs["eos_mount_point"], "/eos")


class TestRunnerShellCommands(unittest.TestCase):

    """Test Runner Shell Commands."""
    def setUp(self):
        """Set Up."""
        self.cmds = EnvironmentCommands.__new__(EnvironmentCommands)

    def test_do_test_runner(self):
        """Test do test runner."""
        with mock.patch.object(commands_environment, "shell") as shell:
            shell.test_runner.return_value = mock.MagicMock(
                messages=[("ok", "success")], colored=lambda: "rendered")
            self.cmds.do_test_runner("pkufarm212")
        shell.test_runner.assert_called_once_with("pkufarm212", timeout=None)

    def test_do_runner_envs(self):
        """Test do runner envs."""
        with mock.patch.object(commands_environment, "shell") as shell:
            shell.runner_envs.return_value = mock.MagicMock(
                messages=[("ok", "success")], colored=lambda: "rendered")
            self.cmds.do_runner_envs("pkufarm212")
        shell.runner_envs.assert_called_once_with("pkufarm212")

    def test_do_test_runner_requires_name(self):
        """Test do test runner requires name."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch("builtins.print") as pr:
            self.cmds.do_test_runner("")
        shell.test_runner.assert_not_called()
        self.assertTrue(pr.called)

    def test_do_whereabouts(self):
        """Test do whereabouts."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch("builtins.print"):
            shell.whereabouts.return_value = mock.MagicMock(
                messages=[("ok", "success")], colored=lambda: "rendered")
            self.cmds.do_whereabouts("")
        shell.whereabouts.assert_called_once_with()

    def test_do_register_runner_ssh_flow(self):
        """Test do register runner ssh flow."""
        answers = iter(["ssh", "cluster", "h", "u", "", "22", "/remote"])
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch("builtins.input", lambda prompt="": next(answers)):
            shell.register_runner.return_value = mock.MagicMock(messages=[])
            self.cmds.do_register_runner("")
        shell.register_runner.assert_called_once_with(
            "cluster", "", "", "ssh",
            ssh_host="h", ssh_user="u", ssh_port=22, remote_workdir="/remote")

    def test_do_register_runner_reana_flow_kept(self):
        """Test do register runner reana flow kept."""
        answers = iter(["reana", "cern", "https://reana.cern.ch", "tok"])
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch("builtins.input", lambda prompt="": next(answers)):
            shell.register_runner.return_value = mock.MagicMock(messages=[])
            self.cmds.do_register_runner("")
        shell.register_runner.assert_called_once_with(
            "cern", "https://reana.cern.ch", "tok", "reana")

    def test_do_purge_ssh_runner_cache_confirms_and_calls(self):
        """Test do purge ssh runner cache confirms and calls."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch.object(commands_environment,
                                  "_impression_scopes",
                                  return_value=[("proj", "imp-uuid")]), \
                mock.patch("builtins.input", return_value="y"), \
                mock.patch("builtins.print"):
            shell.purge_ssh_runner_cache.return_value = mock.MagicMock(
                messages=[("ok", "success")], colored=lambda: "rendered")
            self.cmds.do_purge_ssh_runner_cache("pkufarm212")
        shell.purge_ssh_runner_cache.assert_called_once_with(
            "pkufarm212", project="proj", impression="imp-uuid")

    def test_do_purge_ssh_runner_cache_cancels_on_no(self):
        """Test do purge ssh runner cache cancels on no."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch.object(commands_environment,
                                  "_impression_scopes",
                                  return_value=[("proj", "imp-uuid")]), \
                mock.patch("builtins.input", return_value="n"), \
                mock.patch("builtins.print") as pr:
            self.cmds.do_purge_ssh_runner_cache("pkufarm212")
        shell.purge_ssh_runner_cache.assert_not_called()
        self.assertTrue(pr.called)

    def test_do_purge_ssh_runner_cache_requires_name(self):
        """Test do purge ssh runner cache requires name."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch.object(commands_environment,
                                  "_impression_scopes",
                                  return_value=[("proj", "imp-uuid")]), \
                mock.patch("builtins.print") as pr:
            self.cmds.do_purge_ssh_runner_cache("")
        shell.purge_ssh_runner_cache.assert_not_called()
        self.assertTrue(pr.called)

    def test_do_purge_ssh_runner_cache_no_impression(self):
        """Test do purge ssh runner cache refuses without an impression."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch.object(commands_environment,
                                  "_impression_scopes",
                                  return_value=[]), \
                mock.patch("builtins.input") as inp, \
                mock.patch("builtins.print") as pr:
            self.cmds.do_purge_ssh_runner_cache("pkufarm212")
        shell.purge_ssh_runner_cache.assert_not_called()
        self.assertFalse(inp.called)
        self.assertTrue(pr.called)

    def test_do_purge_ssh_runner_cache_folder_batch(self):
        """Test do purge in a folder delegates the batch to the shell fn."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch.object(commands_environment,
                                  "_impression_scopes",
                                  return_value=[("proj", "abc1234"),
                                                ("proj", "def5678")]), \
                mock.patch("builtins.input", return_value="y"), \
                mock.patch("builtins.print"):
            shell.purge_ssh_runner_cache.return_value = mock.MagicMock(
                messages=[("ok", "success")], colored=lambda: "rendered")
            self.cmds.do_purge_ssh_runner_cache("pkufarm212")
        shell.purge_ssh_runner_cache.assert_called_once_with("pkufarm212")

    def test_do_cache_results_confirms_and_calls(self):
        """Test do cache results confirms and calls."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch.object(commands_environment,
                                  "_impression_scopes",
                                  return_value=[("proj", "imp-uuid")]), \
                mock.patch("builtins.input", return_value="y"), \
                mock.patch("builtins.print"):
            shell.cache_results.return_value = mock.MagicMock(
                messages=[("ok", "success")], colored=lambda: "rendered")
            self.cmds.do_cache_results("pkufarm212")
        shell.cache_results.assert_called_once_with("pkufarm212")

    def test_do_cache_results_cancels_on_no(self):
        """Test do cache results cancels on no."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch.object(commands_environment,
                                  "_impression_scopes",
                                  return_value=[("proj", "imp-uuid")]), \
                mock.patch("builtins.input", return_value="n"), \
                mock.patch("builtins.print") as pr:
            self.cmds.do_cache_results("pkufarm212")
        shell.cache_results.assert_not_called()
        self.assertTrue(pr.called)

    def test_do_cache_results_requires_name(self):
        """Test do cache results requires name."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch.object(commands_environment,
                                  "_impression_scopes",
                                  return_value=[("proj", "imp-uuid")]), \
                mock.patch("builtins.print") as pr:
            self.cmds.do_cache_results("")
        shell.cache_results.assert_not_called()
        self.assertTrue(pr.called)

    def test_do_cache_results_folder_batch(self):
        """Test do cache results in a folder delegates the batch."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch.object(commands_environment,
                                  "_impression_scopes",
                                  return_value=[("proj", "abc1234"),
                                                ("proj", "def5678")]), \
                mock.patch("builtins.input", return_value="y"), \
                mock.patch("builtins.print"):
            shell.cache_results.return_value = mock.MagicMock(
                messages=[("ok", "success")], colored=lambda: "rendered")
            self.cmds.do_cache_results("pkufarm212")
        shell.cache_results.assert_called_once_with("pkufarm212")

    def test_do_cache_results_no_impression(self):
        """Test do cache results refuses without an impression."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch.object(commands_environment,
                                  "_impression_scopes",
                                  return_value=[]), \
                mock.patch("builtins.input") as inp, \
                mock.patch("builtins.print") as pr:
            self.cmds.do_cache_results("pkufarm212")
        shell.cache_results.assert_not_called()
        self.assertFalse(inp.called)
        self.assertTrue(pr.called)


    def test_do_sync_live(self):
        """Test do sync live."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch("builtins.print"):
            shell.sync_live.return_value = mock.MagicMock(
                messages=[("Synced live set: 1 live", "")],
                colored=lambda: "rendered")
            self.cmds.do_sync_live("")
        shell.sync_live.assert_called_once_with()

    def _plan(self, purge_count, lines=("Dry run", "")):
        """A dry-run plan Message stand-in with a purge count."""
        plan = mock.MagicMock(messages=[lines], colored=lambda: "plan")
        plan.data = {"purge_count": purge_count}
        return plan

    def test_do_purge_stale_cache_confirms_and_runs(self):
        """Test do purge stale cache plans, confirms, and runs."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch("builtins.print"), \
                mock.patch("builtins.input", return_value="y"):
            done = mock.MagicMock(
                messages=[("Purged 1 cache entries", "")],
                colored=lambda: "done")
            shell.purge_stale_cache.side_effect = [
                self._plan(1), done]
            self.cmds.do_purge_stale_cache("pkufarm")
        shell.purge_stale_cache.assert_has_calls([
            mock.call("pkufarm", dry_run=True),
            mock.call("pkufarm")])

    def test_do_purge_stale_cache_dry_run_stops(self):
        """Test do purge stale cache --dry-run never purges."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch("builtins.print"), \
                mock.patch("builtins.input") as inp:
            shell.purge_stale_cache.return_value = self._plan(2)
            self.cmds.do_purge_stale_cache("--dry-run pkufarm")
        shell.purge_stale_cache.assert_called_once_with(
            "pkufarm", dry_run=True)
        inp.assert_not_called()

    def test_do_purge_stale_cache_dry_run_after_runner(self):
        """Test do purge stale cache --dry-run after the runner token."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch("builtins.print"), \
                mock.patch("builtins.input") as inp:
            shell.purge_stale_cache.return_value = self._plan(2)
            self.cmds.do_purge_stale_cache("pkufarm --dry-run")
        shell.purge_stale_cache.assert_called_once_with(
            "pkufarm", dry_run=True)
        inp.assert_not_called()

    def test_do_purge_stale_cache_nothing_to_purge_no_confirm(self):
        """Test an empty plan needs no confirmation."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch("builtins.print"), \
                mock.patch("builtins.input") as inp:
            shell.purge_stale_cache.return_value = self._plan(0)
            self.cmds.do_purge_stale_cache("pkufarm")
        shell.purge_stale_cache.assert_called_once_with(
            "pkufarm", dry_run=True)
        inp.assert_not_called()

    def test_do_purge_stale_cache_yes_skips_confirm(self):
        """Test do purge stale cache --yes skips the prompt."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch("builtins.print"), \
                mock.patch("builtins.input") as inp:
            done = mock.MagicMock(
                messages=[("Purged 1 cache entries", "")],
                colored=lambda: "done")
            shell.purge_stale_cache.side_effect = [
                self._plan(1), done]
            self.cmds.do_purge_stale_cache("--yes pkufarm")
        shell.purge_stale_cache.assert_has_calls([
            mock.call("pkufarm", dry_run=True),
            mock.call("pkufarm")])
        inp.assert_not_called()

    def test_do_purge_stale_cache_cancels(self):
        """Test do purge stale cache cancels on no."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch("builtins.print"), \
                mock.patch("builtins.input", return_value="n"):
            shell.purge_stale_cache.return_value = self._plan(1)
            self.cmds.do_purge_stale_cache("pkufarm")
        shell.purge_stale_cache.assert_called_once_with(
            "pkufarm", dry_run=True)

    def test_do_purge_stale_cache_requires_name(self):
        """Test do purge stale cache requires a runner name."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch("builtins.print") as pr:
            self.cmds.do_purge_stale_cache("--dry-run")
        shell.purge_stale_cache.assert_not_called()
        self.assertTrue(pr.called)

    def test_do_purge_stale_workflows_confirms_and_runs(self):
        """Test do purge stale workflows plans, confirms, and runs."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch("builtins.print"), \
                mock.patch("builtins.input", return_value="y"):
            done = mock.MagicMock(
                messages=[("Purged 1 workflows", "")],
                colored=lambda: "done")
            shell.purge_stale_workflows.side_effect = [
                self._plan(1), done]
            self.cmds.do_purge_stale_workflows("pkufarm")
        shell.purge_stale_workflows.assert_has_calls([
            mock.call("pkufarm", dry_run=True),
            mock.call("pkufarm")])

    def test_do_purge_stale_workflows_dry_run_stops(self):
        """Test do purge stale workflows --dry-run never purges."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch("builtins.print"), \
                mock.patch("builtins.input") as inp:
            shell.purge_stale_workflows.return_value = self._plan(2)
            self.cmds.do_purge_stale_workflows("--dry-run pkufarm")
        shell.purge_stale_workflows.assert_called_once_with(
            "pkufarm", dry_run=True)
        inp.assert_not_called()

    def test_do_purge_stale_workflows_cancels(self):
        """Test do purge stale workflows cancels on no."""
        with mock.patch.object(commands_environment, "shell") as shell, \
                mock.patch("builtins.print"), \
                mock.patch("builtins.input", return_value="n"):
            shell.purge_stale_workflows.return_value = self._plan(1)
            self.cmds.do_purge_stale_workflows("pkufarm")
        shell.purge_stale_workflows.assert_called_once_with(
            "pkufarm", dry_run=True)

class TestRunnerCompletions(unittest.TestCase):

    """Test Runner Completions."""
    def setUp(self):
        """Set Up."""
        self.comp = ChernShellCompletions.__new__(ChernShellCompletions)
        self.comp.readline_file = mock.MagicMock()
        self.comp.readline_file.read_variable.return_value = ["cern", "local", "pkufarm212"]

    def test_complete_test_runner(self):
        """Test complete test runner."""
        self.assertEqual(self.comp.complete_test_runner("p", "test_runner p", 0, 0),
                         ["pkufarm212"])

    def test_complete_runner_envs(self):
        """Test complete runner envs."""
        self.assertEqual(self.comp.complete_runner_envs("", "runner_envs ", 0, 0),
                         ["cern", "local", "pkufarm212"])

    def test_complete_register_ssh_data(self):
        """Test complete register ssh data."""
        self.assertEqual(self.comp.complete_register_ssh_data(
            "p", "register-ssh-data p", 0, 0), ["pkufarm212"])

    def test_complete_purge_ssh_runner_cache(self):
        """Test complete purge ssh runner cache."""
        self.assertEqual(self.comp.complete_purge_ssh_runner_cache(
            "p", "purge-ssh-runner-cache p", 0, 0), ["pkufarm212"])

    def test_complete_cache_results(self):
        """Test complete cache results."""
        self.assertEqual(self.comp.complete_cache_results(
            "p", "cache-results p", 0, 0), ["pkufarm212"])


class TestEngineLogsFetch(unittest.TestCase):

    """Test engine logs fetch flag."""
    def setUp(self):
        """Set Up."""
        from CelebiChrono.interface.chern_shell.commands_execution import (
            CommandsExecution)
        self.cmds = CommandsExecution.__new__(CommandsExecution)

    def test_do_engine_logs_fetch_flag(self):
        """Test do engine logs fetch flag."""
        from CelebiChrono.interface.chern_shell import commands_execution
        with mock.patch.object(commands_execution, "engine_logs") as fn:
            fn.return_value = mock.MagicMock(messages=[])
            self.cmds.do_engine_logs("--fetch")
        fn.assert_called_once_with(fetch=True)

    def test_do_engine_logs_plain(self):
        """Test do engine logs plain."""
        from CelebiChrono.interface.chern_shell import commands_execution
        with mock.patch.object(commands_execution, "engine_logs") as fn:
            fn.return_value = mock.MagicMock(messages=[])
            self.cmds.do_engine_logs("")
        fn.assert_called_once_with(fetch=False)

if __name__ == "__main__":
    unittest.main()


class TestRegisterSshDataShellCommand(unittest.TestCase):

    """Test Register SSH Data Shell Command."""
    def setUp(self):
        """Set Up."""
        self.cmds = TaskCommands.__new__(TaskCommands)

    def test_do_register_ssh_data_parses_args(self):
        """Test do register ssh data parses args."""
        with mock.patch.object(commands_task, "shell") as shell:
            shell.register_ssh_data.return_value = mock.MagicMock(messages=[])
            self.cmds.do_register_ssh_data(
                "pkufarm212 /data/dir --descriptor mydata")
        shell.register_ssh_data.assert_called_once_with(
            "pkufarm212", "/data/dir", "mydata")

    def test_do_register_ssh_data_defaults_descriptor(self):
        """Test do register ssh data defaults descriptor."""
        with mock.patch.object(commands_task, "shell") as shell:
            shell.register_ssh_data.return_value = mock.MagicMock(messages=[])
            self.cmds.do_register_ssh_data("pkufarm212 /data/dir")
        shell.register_ssh_data.assert_called_once_with(
            "pkufarm212", "/data/dir", "")

    def test_do_register_ssh_data_requires_args(self):
        """Test do register ssh data requires args."""
        with mock.patch.object(commands_task, "shell") as shell, \
                mock.patch("builtins.print") as pr:
            self.cmds.do_register_ssh_data("")
        shell.register_ssh_data.assert_not_called()
        self.assertTrue(pr.called)

