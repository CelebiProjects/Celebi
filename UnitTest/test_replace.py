"""Tests for the ``replace`` command core logic.

The replace command walks a folder, renames the objects whose names contain
the search string, and updates the input paths and aliases of the tasks and
algorithms found in the walk.
"""
# pylint: disable=too-many-lines
import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

import yaml
from click.testing import CliRunner

from CelebiChrono.kernel.chern_cache import ChernCache
from CelebiChrono.kernel.vobject import VObject
from CelebiChrono.interface.shell_modules.replace_operations import replace
from CelebiChrono.utils.message import Message

CHERN_CACHE = ChernCache.instance()


def _write_json(path, data):
    """Write json data to the file at path."""
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(data, stream)


def _make_object(path, object_type):
    """Create a plain directory object (project or directory)."""
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, ".celebi"), exist_ok=True)
    _write_json(os.path.join(path, ".celebi", "config.json"),
                {"object_type": object_type})


def _make_task(path, predecessors=None, aliases=None, successors=None):
    """Create a task object with the given arcs and aliases.

    Args:
        path: Absolute path of the task.
        predecessors: List of invariant paths of the input objects.
        aliases: Mapping alias -> invariant path of the input objects.
        successors: List of invariant paths of the successor objects.
    """
    os.makedirs(path)
    with open(os.path.join(path, "celebi.yaml"), "w",
              encoding="utf-8") as stream:
        yaml.safe_dump({"alias": sorted(aliases or {}),
                        "environment": "reanahub/reana-env-root6:6.18.04",
                        "kubernetes_memory_limit": "256Mi"}, stream)
    with open(os.path.join(path, "README.md"), "w",
              encoding="utf-8") as stream:
        stream.write("")
    os.makedirs(os.path.join(path, ".celebi"), exist_ok=True)
    config = {
        "object_type": "task",
        "predecessors": list(predecessors or []),
        "successors": list(successors or []),
        "alias_to_path": dict(aliases or {}),
        "path_to_alias": {p: a for a, p in (aliases or {}).items()},
        "impression": "",
        "impressions": [],
        "output_md5s": {},
        "output_md5": "",
    }
    _write_json(os.path.join(path, ".celebi", "config.json"), config)


def _make_project():
    """Create a temporary Celebi project and return its root path."""
    root = os.path.realpath(tempfile.mkdtemp())
    _make_object(root, "project")
    with open(os.path.join(root, ".celebi", "project.json"), "w",
              encoding="utf-8") as stream:
        stream.write("")
    return root


def _invariant_paths(obj):
    """Return the invariant paths of the predecessors of obj."""
    return [pred.invariant_path() for pred in obj.predecessors()]


class TestReplace(unittest.TestCase):

    """Tests for the replace command core logic."""

    def setUp(self):
        """Set up."""
        self.cwd = os.getcwd()
        self.root = _make_project()

    def tearDown(self):
        """Tear down."""
        os.chdir(self.cwd)
        shutil.rmtree(self.root, ignore_errors=True)
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

    def _make_tasks_dir(self):
        """Create the tasks directory in the project."""
        tasks = os.path.join(self.root, "tasks")
        _make_object(tasks, "directory")
        return tasks

    def test_renames_matching_tasks_in_walk(self):
        """Tasks whose names contain the search string are renamed."""
        os.chdir(self.root)
        tasks = self._make_tasks_dir()
        gen = os.path.join(tasks, "fooGen")
        _make_task(gen)
        VObject(gen).impress()

        message = replace("Gen", "Prod", VObject(tasks))

        self.assertTrue(message.success, str(message))
        self.assertTrue(os.path.isdir(os.path.join(tasks, "fooProd")))
        self.assertFalse(os.path.exists(gen))

    def test_renames_nested_parent_and_child(self):
        """A matching parent directory and a matching child are both renamed."""
        os.chdir(self.root)
        tasks = self._make_tasks_dir()
        parent = os.path.join(tasks, "fooA")
        _make_object(parent, "directory")
        child = os.path.join(parent, "fooA_task")
        _make_task(child)
        VObject(child).impress()

        message = replace("fooA", "fooB", VObject(tasks))

        self.assertTrue(message.success, str(message))
        self.assertTrue(os.path.isdir(
            os.path.join(tasks, "fooB", "fooB_task")))
        self.assertFalse(os.path.exists(parent))

    def test_single_pass_when_replacement_contains_search(self):
        """Each object is renamed only once, even if B contains A."""
        os.chdir(self.root)
        tasks = self._make_tasks_dir()
        gen = os.path.join(tasks, "fooGen")
        _make_task(gen)
        VObject(gen).impress()

        message = replace("Gen", "Gen2", VObject(tasks))

        self.assertTrue(message.success, str(message))
        self.assertTrue(os.path.isdir(os.path.join(tasks, "fooGen2")))
        self.assertFalse(os.path.exists(os.path.join(tasks, "fooGen22")))
        self.assertFalse(os.path.exists(gen))

    def test_updates_input_path_for_renamed_target_in_walk(self):
        """The input of a task is updated when its target is renamed."""
        os.chdir(self.root)
        tasks = self._make_tasks_dir()
        gen = os.path.join(tasks, "fooGen")
        _make_task(gen, successors=["tasks/fooAna"])
        ana = os.path.join(tasks, "fooAna")
        _make_task(ana, predecessors=["tasks/fooGen"],
                   aliases={"genfoo": "tasks/fooGen"})
        VObject(gen).impress()

        message = replace("Gen", "Prod", VObject(tasks))

        self.assertTrue(message.success, str(message))
        ana_obj = VObject(ana)
        self.assertEqual(_invariant_paths(ana_obj), ["tasks/fooProd"])
        config = ana_obj.config_file.read_variable("alias_to_path", {})
        self.assertEqual(config, {"genfoo": "tasks/fooProd"})
        config = ana_obj.config_file.read_variable("path_to_alias", {})
        self.assertEqual(config, {"tasks/fooProd": "genfoo"})

    def test_updates_input_path_for_target_outside_walk(self):
        """The input path is substituted even if the target is not walked."""
        os.chdir(self.root)
        tasks = self._make_tasks_dir()
        outside = os.path.join(self.root, "outside")
        _make_object(outside, "directory")
        old_target = os.path.join(outside, "xGen")
        _make_task(old_target, successors=["tasks/fooAna"])
        new_target = os.path.join(outside, "xProd")
        _make_task(new_target, successors=["tasks/fooAna"])
        ana = os.path.join(tasks, "fooAna")
        _make_task(ana, predecessors=["outside/xGen"],
                   aliases={"genfoo": "outside/xGen"})

        message = replace("Gen", "Prod", VObject(tasks))

        self.assertTrue(message.success, str(message))
        ana_obj = VObject(ana)
        self.assertEqual(_invariant_paths(ana_obj), ["outside/xProd"])
        config = ana_obj.config_file.read_variable("alias_to_path", {})
        self.assertEqual(config, {"genfoo": "outside/xProd"})
        self.assertTrue(os.path.isdir(old_target))

    def test_reports_failure_when_updated_target_missing(self):
        """A failed add-input is reported as an error of the command."""
        os.chdir(self.root)
        tasks = self._make_tasks_dir()
        outside = os.path.join(self.root, "outside")
        _make_object(outside, "directory")
        old_target = os.path.join(outside, "xGen")
        _make_task(old_target, successors=["tasks/fooAna"])
        ana = os.path.join(tasks, "fooAna")
        _make_task(ana, predecessors=["outside/xGen"],
                   aliases={"genfoo": "outside/xGen"})

        message = replace("Gen", "Prod", VObject(tasks))

        self.assertFalse(message.success)
        ana_obj = VObject(ana)
        self.assertEqual(_invariant_paths(ana_obj), [])

    def test_updates_alias_only(self):
        """An alias containing A is renamed while its path is untouched."""
        os.chdir(self.root)
        tasks = self._make_tasks_dir()
        plain = os.path.join(tasks, "plain")
        _make_task(plain, successors=["tasks/fooAna"])
        ana = os.path.join(tasks, "fooAna")
        _make_task(ana, predecessors=["tasks/plain"],
                   aliases={"genfoo": "tasks/plain"})

        message = replace("gen", "GEN", VObject(tasks))

        self.assertTrue(message.success, str(message))
        ana_obj = VObject(ana)
        self.assertEqual(_invariant_paths(ana_obj), ["tasks/plain"])
        config = ana_obj.config_file.read_variable("alias_to_path", {})
        self.assertEqual(config, {"GENfoo": "tasks/plain"})
        self.assertTrue(os.path.isdir(plain))

    def test_dry_run_changes_nothing(self):
        """A dry run reports the plan but leaves everything untouched."""
        os.chdir(self.root)
        tasks = self._make_tasks_dir()
        gen = os.path.join(tasks, "fooGen")
        _make_task(gen)
        VObject(gen).impress()

        message = replace("Gen", "Prod", VObject(tasks), dry_run=True)

        self.assertTrue(message.success, str(message))
        self.assertIn("fooProd", str(message))
        self.assertTrue(os.path.isdir(gen))
        self.assertFalse(os.path.exists(os.path.join(tasks, "fooProd")))

    def test_project_root_never_renamed(self):
        """The project root is never renamed, its contents still are."""
        os.chdir(self.root)
        tasks = self._make_tasks_dir()
        child = os.path.join(tasks, "projA_task")
        _make_task(child)
        VObject(child).impress()

        message = replace("projA", "projB", VObject(self.root))

        self.assertTrue(message.success, str(message))
        self.assertTrue(os.path.isdir(self.root))
        self.assertTrue(os.path.isdir(
            os.path.join(tasks, "projB_task")))
        self.assertFalse(os.path.exists(child))

    def test_walk_root_directory_renamed(self):
        """The walked folder itself is renamed when its name matches."""
        os.chdir(self.root)
        tasks = self._make_tasks_dir()
        gen = os.path.join(tasks, "fooGen")
        _make_task(gen, successors=["tasks/fooAna"])
        ana = os.path.join(tasks, "fooAna")
        _make_task(ana, predecessors=["tasks/fooGen"],
                   aliases={"genfoo": "tasks/fooGen"})
        VObject(gen).impress()
        VObject(ana).impress()

        message = replace("task", "job", VObject(tasks))

        self.assertTrue(message.success, str(message))
        renamed = os.path.join(self.root, "jobs")
        self.assertTrue(os.path.isdir(os.path.join(renamed, "fooGen")))
        self.assertFalse(os.path.exists(tasks))
        ana_obj = VObject(os.path.join(renamed, "fooAna"))
        self.assertEqual(_invariant_paths(ana_obj), ["jobs/fooGen"])

    def test_updates_input_when_run_inside_task(self):
        """The input update works when the walk root is the task itself."""
        os.chdir(self.root)
        data = os.path.join(self.root, "Data")
        _make_task(data)
        small = os.path.join(self.root, "SmallData")
        _make_task(small, successors=["FitTask_ssh"])
        ana = os.path.join(self.root, "FitTask_ssh")
        _make_task(ana, predecessors=["SmallData"],
                   aliases={"gen": "SmallData"})
        os.chdir(ana)

        message = replace("SmallData", "Data", VObject(ana))

        self.assertTrue(message.success, str(message))
        ana_obj = VObject(ana)
        self.assertEqual(_invariant_paths(ana_obj), ["Data"])
        config = ana_obj.config_file.read_variable("alias_to_path", {})
        self.assertEqual(config, {"gen": "Data"})

    def test_add_input_missing_target_message(self):
        """add_input reports the object type for a missing target."""
        os.chdir(self.root)
        ana = os.path.join(self.root, "fooAna")
        _make_task(ana)
        obj = VObject(ana)
        with contextlib.redirect_stdout(io.StringIO()) as buffer:
            obj.add_input("does/not/exist", "gen")
        self.assertIn("The input is required to be a task.",
                      buffer.getvalue())
        self.assertNotIn("{self.object_type()}", buffer.getvalue())


class TestReplaceInterfaces(unittest.TestCase):

    """Tests for the shell and CLI interfaces of the replace command."""

    def test_shell_do_replace_previews_then_applies(self):
        """The shell handler previews the plan and applies it on yes."""
        from CelebiChrono.interface.chern_shell import commands_file
        from CelebiChrono.interface.chern_shell.commands_file import (
            FileCommands)
        handler = FileCommands.__new__(FileCommands)
        with mock.patch.object(commands_file, "shell") as shell:
            plan = Message()
            plan.add("mv @/a @/b\n", "info")
            done = Message()
            done.add("Renamed @/a -> @/b\n", "info")
            shell.replace.side_effect = [plan, done]
            with mock.patch("builtins.input", return_value="y"):
                handler.do_replace("Gen Prod")
            self.assertEqual(shell.replace.call_count, 2)
            shell.replace.assert_has_calls(
                [mock.call("Gen", "Prod", dry_run=True),
                 mock.call("Gen", "Prod")])

    def test_shell_do_replace_declines(self):
        """The shell handler only previews when the answer is no."""
        from CelebiChrono.interface.chern_shell import commands_file
        from CelebiChrono.interface.chern_shell.commands_file import (
            FileCommands)
        handler = FileCommands.__new__(FileCommands)
        with mock.patch.object(commands_file, "shell") as shell:
            plan = Message()
            plan.add("mv @/a @/b\n", "info")
            shell.replace.return_value = plan
            with mock.patch("builtins.input", return_value="n"):
                handler.do_replace("Gen Prod")
            shell.replace.assert_called_once_with(
                "Gen", "Prod", dry_run=True)

    def test_shell_do_replace_usage_error(self):
        """The shell handler prints usage for a wrong number of arguments."""
        from CelebiChrono.interface.chern_shell import commands_file
        from CelebiChrono.interface.chern_shell.commands_file import (
            FileCommands)
        handler = FileCommands.__new__(FileCommands)
        with mock.patch.object(commands_file, "shell") as shell:
            handler.do_replace("Gen")
            shell.replace.assert_not_called()

    def test_cli_replace_command(self):
        """The CLI command forwards A and B to the shell function."""
        from CelebiChrono.celebi_cli.commands.file_operations import (
            replace_command)
        with mock.patch("CelebiChrono.interface.shell.replace") as fn:
            fn.return_value = Message()
            result = CliRunner().invoke(replace_command, ["Gen", "Prod"])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with("Gen", "Prod", dry_run=False)

    def test_cli_replace_command_dry_run(self):
        """The CLI command passes the dry run flag through."""
        from CelebiChrono.celebi_cli.commands.file_operations import (
            replace_command)
        with mock.patch("CelebiChrono.interface.shell.replace") as fn:
            fn.return_value = Message()
            result = CliRunner().invoke(
                replace_command, ["Gen", "Prod", "--dry-run"])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with("Gen", "Prod", dry_run=True)


if __name__ == "__main__":
    unittest.main()
