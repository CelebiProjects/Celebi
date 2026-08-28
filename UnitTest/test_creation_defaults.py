"""Creation-time defaults come from the user settings, write paths only.

The read fallbacks are deliberately NOT wired to user settings: celebi.yaml
is hashed into the impression, so a read-time fallback would let two users
share an impression id while executing in different environments.
"""
import os
import tempfile
import unittest
from unittest import mock

import yaml

from CelebiChrono.interface.shell_modules import task_configuration
from CelebiChrono.kernel import vtask
from CelebiChrono.utils import metadata


class CreationTestCase(unittest.TestCase):

    """Base case with an isolated HOME and a stub project directory."""

    config = ""

    def setUp(self):
        """Isolate HOME, write the case's config, prepare a parent dir."""
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
        self.work = os.path.join(self.home_path, "proj")
        os.makedirs(self.work, exist_ok=True)

    def make_task(self, name="t"):
        """Run create_task under a stubbed parent object type."""
        path = os.path.join(self.work, name)
        with mock.patch.object(vtask, "VObject") as vobj:
            vobj.return_value.object_type.return_value = "project"
            vobj.return_value.invariant_path.return_value = name
            vtask.create_task(path)
        return path

    @staticmethod
    def read_yaml(path):
        """Read a task's celebi.yaml as a dict."""
        with open(os.path.join(path, "celebi.yaml"), encoding="utf-8") as f:
            return yaml.safe_load(f.read())


class TestCreationDefaultsConfigured(CreationTestCase):

    """Configured values are written into the new task."""

    config = (
        "default_runner: farm\n"
        "auto_download: false\n"
        "cache_on_runner: true\n"
        "task_environment: myimage:1.0\n"
    )

    def test_default_runner_written_from_setting(self):
        """The configured runner is recorded on the new task."""
        path = self.make_task()
        local = metadata.TwoTierConfigFile(path + "/.celebi/config.json")
        self.assertEqual(local.read_variable("default_runner"), "farm")

    def test_auto_download_written_from_setting(self):
        """The configured auto_download is recorded on the new task."""
        path = self.make_task()
        local = metadata.TwoTierConfigFile(path + "/.celebi/config.json")
        self.assertIs(local.read_variable("auto_download"), False)

    def test_cache_on_runner_written_from_setting(self):
        """cache_on_runner is now recorded at creation, not left implicit."""
        path = self.make_task()
        local = metadata.TwoTierConfigFile(path + "/.celebi/config.json")
        self.assertIs(local.read_variable("cache_on_runner"), True)

    def test_task_environment_written_from_setting(self):
        """The configured environment lands in celebi.yaml."""
        path = self.make_task()
        self.assertEqual(self.read_yaml(path)["environment"], "myimage:1.0")


class TestCreationDefaultsUnconfigured(CreationTestCase):

    """With no config, creation matches the previous hardcoded behaviour."""

    config = ""

    def test_defaults_match_previous_behaviour(self):
        """Unconfigured creation is byte-for-byte what it always was."""
        path = self.make_task()
        local = metadata.TwoTierConfigFile(path + "/.celebi/config.json")
        self.assertIs(local.read_variable("auto_download"), True)
        self.assertEqual(local.read_variable("default_runner"), "local")
        self.assertEqual(
            self.read_yaml(path)["environment"],
            "reanahub/reana-env-root6:6.18.04",
        )


class TestReadPathsNotWired(CreationTestCase):

    """The read fallbacks must ignore user settings entirely."""

    config = "task_environment: myimage:1.0\n"

    def test_environment_read_does_not_fall_back_to_setting(self):
        """A celebi.yaml without `environment` must NOT inherit the setting.

        If it did, two users would share an impression id while running in
        different environments -- identical hash, different computation.
        """
        obj = vtask.VTask.__new__(vtask.VTask)
        obj.path = os.path.join(self.work, "bare")
        os.makedirs(obj.path, exist_ok=True)
        with open(
            os.path.join(obj.path, "celebi.yaml"), "w", encoding="utf-8"
        ) as f:
            f.write("descriptor: bare\n")
        self.assertEqual(obj.environment(), "")


class TestTemplateEnvironments(CreationTestCase):

    """The `config` command's generated template uses the settings."""

    config = (
        "task_environment: myimage:1.0\n"
        "algorithm_environment: myscript\n"
    )

    def _run_config(self, object_type):
        """Run config() for a stub object of the given type with no yaml."""
        obj = mock.MagicMock()
        obj.is_task_or_algorithm.return_value = True
        obj.object_type.return_value = object_type
        obj.path = os.path.join(self.work, f"obj-{object_type}")
        os.makedirs(obj.path, exist_ok=True)
        with mock.patch.object(task_configuration, "MANAGER") as manager, \
                mock.patch.object(task_configuration.subprocess, "call"):
            manager.current_object.return_value = obj
            task_configuration.config()
        with open(
            os.path.join(obj.path, "celebi.yaml"), encoding="utf-8"
        ) as f:
            return f.read()

    def test_task_template_uses_task_environment(self):
        """A new task template carries the configured task environment."""
        self.assertIn("myimage:1.0", self._run_config("task"))

    def test_algorithm_template_uses_algorithm_environment(self):
        """A new algorithm template carries the configured environment."""
        self.assertIn("myscript", self._run_config("algorithm"))

    def test_task_template_is_valid_yaml(self):
        """The generated task template must be readable once written.

        The old template emitted a literal `parameters: {{}}`, which is
        unparseable YAML, so every later read of the file raised.
        """
        data = yaml.safe_load(self._run_config("task"))
        self.assertIsInstance(data, dict)
        self.assertEqual(data["parameters"], {})

    def test_algorithm_template_is_valid_yaml(self):
        """The generated algorithm template must be readable once written."""
        data = yaml.safe_load(self._run_config("algorithm"))
        self.assertIsInstance(data, dict)


if __name__ == "__main__":
    unittest.main()
