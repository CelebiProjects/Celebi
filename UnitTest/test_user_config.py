"""Tests for the user-level settings registry in ~/.celebi/config.yaml."""
import os
import sys
import tempfile
import unittest
from unittest import mock

import yaml

from CelebiChrono.utils import user_config


class UserConfigTestCase(unittest.TestCase):

    """Base case that points HOME at an empty temp dir."""

    def setUp(self):
        """Isolate HOME so no real user config is read or written."""
        # pylint: disable=consider-using-with
        self.home = tempfile.TemporaryDirectory()
        self.addCleanup(self.home.cleanup)
        self.home_path = os.path.realpath(self.home.name)
        patcher = mock.patch.dict(os.environ, {"HOME": self.home_path})
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_config(self, text):
        """Write raw text to the user config file."""
        os.makedirs(os.path.dirname(user_config.config_path()), exist_ok=True)
        with open(user_config.config_path(), "w", encoding="utf-8") as f:
            f.write(text)


class TestGet(UserConfigTestCase):

    """Reading settings with registry-supplied defaults."""

    def test_get_returns_registry_default_when_file_absent(self):
        """With no config.yaml on disk, get() falls back to the registry."""
        self.assertFalse(os.path.exists(user_config.config_path()))
        self.assertEqual(user_config.get("editor"), "vi")

    def test_get_returns_configured_value(self):
        """A value set in the file wins over the registry default."""
        self.write_config("editor: emacs\n")
        self.assertEqual(user_config.get("editor"), "emacs")

    def test_get_falls_back_when_file_is_empty(self):
        """An empty file is not an error -- the default still applies."""
        self.write_config("")
        self.assertEqual(user_config.get("editor"), "vi")

    def test_get_falls_back_when_file_is_not_a_mapping(self):
        """A malformed (non-mapping) file degrades to the default."""
        self.write_config("- just\n- a\n- list\n")
        self.assertEqual(user_config.get("editor"), "vi")

    def test_get_unregistered_name_returns_explicit_default(self):
        """An unregistered key has no registry default, so the caller's wins."""
        self.assertEqual(user_config.get("nope", "fallback"), "fallback")


class TestRenderTemplate(UserConfigTestCase):

    """The generated scaffold shown to a first-time user."""

    def test_template_is_valid_yaml(self):
        """The scaffold must parse, or we would ship a broken config."""
        data = yaml.safe_load(user_config.render_template())
        self.assertIsInstance(data, dict)

    def test_template_covers_every_registered_setting(self):
        """Every registry entry appears as a key with its default value."""
        data = yaml.safe_load(user_config.render_template())
        for setting in user_config.SETTINGS:
            self.assertIn(setting.name, data)
            self.assertEqual(data[setting.name], setting.default)

    def test_template_documents_each_setting_as_a_comment(self):
        """Each description is rendered as a comment, for discoverability."""
        text = user_config.render_template()
        # Comments wrap, so rejoin continuation lines before searching.
        flattened = " ".join(
            line.lstrip("# ").strip() for line in text.splitlines()
        )
        for setting in user_config.SETTINGS:
            self.assertIn(setting.description, flattened)

    def test_template_lines_stay_readable(self):
        """No line runs past 79 columns, so the file reads well in any editor."""
        for line in user_config.render_template().splitlines():
            self.assertLessEqual(len(line), 79, line)


class TestEnsureExists(UserConfigTestCase):

    """Creating the file without ever clobbering an existing one."""

    def test_creates_file_with_template_when_absent(self):
        """First run writes the scaffold and reports that it created it."""
        created = user_config.ensure_exists()
        self.assertTrue(created)
        self.assertTrue(os.path.exists(user_config.config_path()))
        with open(user_config.config_path(), encoding="utf-8") as f:
            self.assertEqual(f.read(), user_config.render_template())

    def test_leaves_existing_file_untouched(self):
        """An existing file is never rewritten -- settings must survive."""
        self.write_config("editor: emacs  # hand-written\n")
        created = user_config.ensure_exists()
        self.assertFalse(created)
        with open(user_config.config_path(), encoding="utf-8") as f:
            self.assertEqual(f.read(), "editor: emacs  # hand-written\n")

    def test_created_file_is_readable_by_get(self):
        """The scaffold round-trips: get() reads the defaults back out."""
        user_config.ensure_exists()
        self.assertEqual(user_config.get("editor"), "vi")


class TestDescribe(UserConfigTestCase):

    """The `--list` view of current settings."""

    def test_describe_marks_defaulted_and_set_values(self):
        """Each row says whether the value came from the file or the default."""
        self.write_config("editor: emacs\n")
        rows = user_config.describe()
        by_name = {row.name: row for row in rows}
        self.assertEqual(by_name["editor"].value, "emacs")
        self.assertTrue(by_name["editor"].is_set)

    def test_describe_reports_defaults_when_file_absent(self):
        """With no file, every registered setting reports as defaulted."""
        rows = user_config.describe()
        self.assertEqual(len(rows), len(user_config.SETTINGS))
        for row in rows:
            self.assertFalse(row.is_set)


class TestRegisteredSettings(UserConfigTestCase):

    """The registry contents each setting's consumer relies on."""

    expected_defaults = {
        "editor": "vi",
        "browser": "",
        "default_runner": "local",
        "auto_download": True,
        "cache_on_runner": False,
        "dag_output_dir": "~/Downloads",
        "task_environment": "reanahub/reana-env-root6:6.18.04",
        "algorithm_environment": "script",
    }

    def test_each_setting_is_registered_with_its_default(self):
        """Every consumer's setting exists with the agreed default."""
        registry = {s.name: s.default for s in user_config.SETTINGS}
        for name, default in self.expected_defaults.items():
            self.assertIn(name, registry)
            self.assertEqual(registry[name], default, f"default for {name}")

    def test_file_opener_default_is_platform_appropriate(self):
        """`open` is macOS-only, so other platforms default to xdg-open."""
        expected = "open" if sys.platform == "darwin" else "xdg-open"
        self.assertEqual(user_config.get("file_opener"), expected)

    def test_browser_and_file_opener_are_separate_settings(self):
        """Opening a local file and opening a URL are distinct choices."""
        self.write_config("file_opener: myviewer\nbrowser: myff\n")
        self.assertEqual(user_config.get("file_opener"), "myviewer")
        self.assertEqual(user_config.get("browser"), "myff")

    def test_empty_browser_means_use_webbrowser_module(self):
        """The default is empty, which callers read as "use webbrowser"."""
        self.assertEqual(user_config.get("browser"), "")

    def test_every_setting_has_a_description(self):
        """A setting with no description renders an empty template comment."""
        for setting in user_config.SETTINGS:
            self.assertTrue(setting.description.strip(), setting.name)

    def test_boolean_settings_survive_the_template_round_trip(self):
        """Booleans must come back as bools, not the strings "true"/"false"."""
        user_config.ensure_exists()
        self.assertIs(user_config.get("auto_download"), True)
        self.assertIs(user_config.get("cache_on_runner"), False)


class TestGetPath(UserConfigTestCase):

    """Path-valued settings expand ~ before use."""

    def test_expands_tilde_in_default(self):
        """The ~/Downloads default is expanded, not passed through literally."""
        result = user_config.get_path("dag_output_dir")
        self.assertNotIn("~", result)
        self.assertTrue(os.path.isabs(result))

    def test_expands_tilde_in_configured_value(self):
        """A configured ~ path is expanded too."""
        self.write_config("dag_output_dir: ~/somewhere\n")
        result = user_config.get_path("dag_output_dir")
        self.assertEqual(result, os.path.join(self.home_path, "somewhere"))

    def test_leaves_absolute_path_alone(self):
        """An absolute path is returned unchanged."""
        self.write_config("dag_output_dir: /var/tmp/dags\n")
        self.assertEqual(
            user_config.get_path("dag_output_dir"), "/var/tmp/dags"
        )


if __name__ == "__main__":
    unittest.main()

