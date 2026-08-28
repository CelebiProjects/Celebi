"""The editor setting resolves identically at every call site.

These are characterization tests for a behaviour-preserving refactor: they
pass both before and after the four duplicated `editor` reads are routed
through CelebiChrono.utils.user_config.
"""
import os
import tempfile
import unittest
from unittest import mock

from CelebiChrono.celebi_cli.commands import execution_management as cli_exec
from CelebiChrono.interface.chern_shell import commands_documentation
from CelebiChrono.interface.chern_shell.commands_documentation import (
    DocumentationCommands)
from CelebiChrono.interface.shell_modules import task_configuration
from CelebiChrono.kernel import vobject


def _script_message(path):
    """A get_script_path-style Message stand-in."""
    msg = mock.MagicMock()
    msg.success = True
    msg.data = {"path": path}
    msg.messages = []
    return msg


class EditorResolutionTestCase(unittest.TestCase):

    """Base case writing a known editor into an isolated HOME."""

    editor = "my-editor"

    def setUp(self):
        """Isolate HOME and write `editor: my-editor` into the config."""
        # pylint: disable=consider-using-with
        self.home = tempfile.TemporaryDirectory()
        self.addCleanup(self.home.cleanup)
        home_path = os.path.realpath(self.home.name)
        patcher = mock.patch.dict(os.environ, {"HOME": home_path})
        patcher.start()
        self.addCleanup(patcher.stop)

        celebi_dir = os.path.join(home_path, ".celebi")
        os.makedirs(celebi_dir, exist_ok=True)
        with open(
            os.path.join(celebi_dir, "config.yaml"), "w", encoding="utf-8"
        ) as f:
            f.write(f"editor: {self.editor}\n")


class TestEditReadme(EditorResolutionTestCase):

    """kernel/vobject.py edit_readme()."""

    def test_uses_configured_editor(self):
        """edit_readme launches the configured editor."""
        obj = vobject.VObject.__new__(vobject.VObject)
        obj.path = "/tmp/some-object"
        with mock.patch.object(vobject.subprocess, "call") as call:
            obj.edit_readme()
        command = call.call_args[0][0]
        self.assertIn(self.editor, command)


class TestConfigCommand(EditorResolutionTestCase):

    """shell_modules/task_configuration.py config()."""

    def test_uses_configured_editor(self):
        """config() opens the object's celebi.yaml in the configured editor."""
        obj = mock.MagicMock()
        obj.is_task_or_algorithm.return_value = True
        obj.path = os.path.join(self.home.name, "obj")
        os.makedirs(obj.path, exist_ok=True)
        with open(
            os.path.join(obj.path, "celebi.yaml"), "w", encoding="utf-8"
        ) as f:
            f.write("environment: script\n")

        with mock.patch.object(task_configuration, "MANAGER") as manager, \
                mock.patch.object(task_configuration.subprocess, "call") as call:
            manager.current_object.return_value = obj
            task_configuration.config()
        self.assertEqual(call.call_args[0][0][0], self.editor)


class TestEditScriptShell(EditorResolutionTestCase):

    """chern_shell/commands_documentation.py do_edit_script()."""

    def test_uses_configured_editor(self):
        """do_edit_script launches the configured editor."""
        cmds = DocumentationCommands.__new__(DocumentationCommands)
        with mock.patch.object(commands_documentation, "shell") as sh, \
                mock.patch.object(
                    commands_documentation.subprocess, "call") as call:
            sh.get_script_path.return_value = _script_message("/tmp/s.sh")
            cmds.do_edit_script("s.sh")
        self.assertEqual(call.call_args[0][0][0], self.editor)


class TestEditScriptCli(EditorResolutionTestCase):

    """celebi_cli/commands/execution_management.py edit_command()."""

    def test_uses_configured_editor(self):
        """`celebi-cli edit` launches the configured editor."""
        with mock.patch(
            "CelebiChrono.interface.shell.get_script_path"
        ) as get_path, \
                mock.patch.object(cli_exec.subprocess, "call") as call:
            get_path.return_value = _script_message("/tmp/s.sh")
            cli_exec.edit_command.callback("s.sh")
        self.assertEqual(call.call_args[0][0][0], self.editor)


if __name__ == "__main__":
    unittest.main()
