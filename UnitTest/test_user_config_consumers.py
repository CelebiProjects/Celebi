"""file_opener, browser and dag_output_dir are honoured at their call sites."""
import os
import shlex
import tempfile
import unittest
from unittest import mock

from CelebiChrono.interface.chern_shell import commands_documentation
from CelebiChrono.interface.chern_shell.commands_documentation import (
    DocumentationCommands)
from CelebiChrono.interface.shell_modules import visualization
from CelebiChrono.kernel import chern_communicator, vtask
from CelebiChrono.utils import file_utils


class SettingsTestCase(unittest.TestCase):

    """Base case writing a known config into an isolated HOME."""

    config = ""

    def setUp(self):
        """Isolate HOME and write the case's config."""
        # pylint: disable=consider-using-with
        self.home = tempfile.TemporaryDirectory()
        self.addCleanup(self.home.cleanup)
        self.home_path = os.path.realpath(self.home.name)
        patcher = mock.patch.dict(os.environ, {"HOME": self.home_path})
        patcher.start()
        self.addCleanup(patcher.stop)
        if self.config:
            celebi_dir = os.path.join(self.home_path, ".celebi")
            os.makedirs(celebi_dir, exist_ok=True)
            with open(
                os.path.join(celebi_dir, "config.yaml"), "w", encoding="utf-8"
            ) as f:
                f.write(self.config)


class TestFileOpener(SettingsTestCase):

    """kernel/vtask.py view() opens a local file."""

    config = "file_opener: myviewer\n"

    def test_uses_configured_file_opener(self):
        """The configured program is invoked, not a hardcoded `open`."""
        task = vtask.VTask.__new__(vtask.VTask)
        target = os.path.join(self.home_path, "some file.root")
        with open(target, "w", encoding="utf-8") as f:
            f.write("x")
        with mock.patch.object(vtask, "open_subprocess") as opener, \
                mock.patch.object(
                    vtask.VTask, "get_file", return_value=target):
            task.view("local:some file.root")
        self.assertIn("myviewer", opener.call_args[0][0])

    def test_quotes_paths_containing_spaces(self):
        """A path with a space must survive as a single shell argument."""
        task = vtask.VTask.__new__(vtask.VTask)
        target = os.path.join(self.home_path, "some file.root")
        with open(target, "w", encoding="utf-8") as f:
            f.write("x")
        with mock.patch.object(vtask, "open_subprocess") as opener, \
                mock.patch.object(
                    vtask.VTask, "get_file", return_value=target):
            task.view("local:some file.root")
        command = opener.call_args[0][0]
        self.assertEqual(shlex.split(command), ["myviewer", target])


class TestOpenUrlHelper(SettingsTestCase):

    """utils.file_utils.open_url centralises the browser decision."""

    def test_uses_configured_browser_command(self):
        """A configured browser command is invoked with the URL."""
        celebi_dir = os.path.join(self.home_path, ".celebi")
        os.makedirs(celebi_dir, exist_ok=True)
        with open(
            os.path.join(celebi_dir, "config.yaml"), "w", encoding="utf-8"
        ) as f:
            f.write("browser: myff\n")
        with mock.patch.object(file_utils.subprocess, "call") as call, \
                mock.patch.object(file_utils, "webbrowser") as wb:
            file_utils.open_url("http://example.invalid/x")
        wb.open.assert_not_called()
        call.assert_called_once_with(["myff", "http://example.invalid/x"])

    def test_falls_back_to_webbrowser_when_unset(self):
        """With no browser configured the portable module is used."""
        with mock.patch.object(file_utils.subprocess, "call") as call, \
                mock.patch.object(file_utils, "webbrowser") as wb:
            file_utils.open_url("http://example.invalid/x")
        call.assert_not_called()
        wb.open.assert_called_once_with("http://example.invalid/x")


class TestBrowserCallSites(SettingsTestCase):

    """Every URL-opening site routes through the one helper."""

    def test_display_delegates_to_open_url(self):
        """chern_communicator.display opens the export URL via the helper."""
        comm = chern_communicator.ChernCommunicator.__new__(
            chern_communicator.ChernCommunicator)
        comm.project_uuid = "p"
        impression = mock.MagicMock()
        impression.uuid = "i"
        with mock.patch.object(comm, "serverurl", return_value="h:1"), \
                mock.patch.object(chern_communicator, "open_url") as open_url:
            comm.display(impression, "f.png")
        self.assertIn("f.png", open_url.call_args[0][0])

    def test_viewbkk_delegates_to_open_url(self):
        """The bookkeeping URL opens via the helper."""
        cmds = DocumentationCommands.__new__(DocumentationCommands)
        result = mock.MagicMock()
        result.data = {"url": "http://example.invalid/bkk"}
        with mock.patch.object(commands_documentation, "shell") as sh, \
                mock.patch.object(
                    commands_documentation, "open_url") as open_url:
            sh.bookkeep_url.return_value = result
            cmds.do_viewbkk("")
        open_url.assert_called_once_with("http://example.invalid/bkk")

    def test_view_delegates_to_open_url(self):
        """shell_modules.visualization.view opens via the helper."""
        obj = mock.MagicMock()
        obj.impression_in_history.return_value = True
        obj.impview.return_value = "http://example.invalid/v"
        with mock.patch.object(visualization, "MANAGER") as manager, \
                mock.patch.object(visualization, "open_url") as open_url, \
                mock.patch.object(
                    visualization, "_resolve_impression", return_value="u"):
            manager.current_object.return_value = obj
            visualization.view()
        open_url.assert_called_once_with("http://example.invalid/v")


class TestDagOutputDir(SettingsTestCase):

    """draw_dag_graphviz writes where the setting says."""

    config = "dag_output_dir: /var/tmp/mydags\n"

    def test_output_goes_to_configured_dir(self):
        """The configured directory replaces the hardcoded ~/Downloads."""
        with mock.patch.object(visualization, "MANAGER"), \
                mock.patch("graphviz.Digraph") as digraph:
            visualization.draw_dag_graphviz()
        rendered = digraph.return_value.render.call_args
        self.assertIsNotNone(rendered, "render was never called")
        self.assertIn("/var/tmp/mydags", str(rendered))


if __name__ == "__main__":
    unittest.main()
