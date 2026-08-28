"""Tests for the `user-config` command on the shell-module layer."""
import os
import tempfile
import unittest
from unittest import mock

from CelebiChrono.interface.shell_modules import task_configuration
from CelebiChrono.utils import user_config


class UserConfigCommandTestCase(unittest.TestCase):

    """Base case isolating HOME and stubbing out the editor launch."""

    def setUp(self):
        """Isolate HOME and prevent a real editor from being spawned."""
        # pylint: disable=consider-using-with
        self.home = tempfile.TemporaryDirectory()
        self.addCleanup(self.home.cleanup)
        patcher = mock.patch.dict(
            os.environ, {"HOME": os.path.realpath(self.home.name)}
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.call = mock.patch.object(
            task_configuration.subprocess, "call"
        ).start()
        self.addCleanup(mock.patch.stopall)


class TestUserConfigCreates(UserConfigCommandTestCase):

    """Creating the file and opening it."""

    def test_creates_file_when_absent(self):
        """First run writes the scaffold to disk."""
        task_configuration.user_config()
        self.assertTrue(os.path.exists(user_config.config_path()))

    def test_reports_creation(self):
        """The message names the file it created."""
        message = task_configuration.user_config()
        text = "".join(t for t, _ in message.messages)
        self.assertIn(user_config.config_path(), text)
        self.assertIn("Created", text)
        self.assertTrue(message.success)

    def test_opens_file_in_configured_editor(self):
        """The file is opened with the editor from the registry."""
        task_configuration.user_config()
        self.call.assert_called_once_with(["vi", user_config.config_path()])

    def test_honours_configured_editor(self):
        """A configured editor overrides the default."""
        user_config.ensure_exists()
        with open(user_config.config_path(), "w", encoding="utf-8") as f:
            f.write("editor: emacs\n")
        task_configuration.user_config()
        self.call.assert_called_once_with(["emacs", user_config.config_path()])

    def test_does_not_report_creation_when_file_exists(self):
        """An existing file is opened without claiming it was created."""
        user_config.ensure_exists()
        message = task_configuration.user_config()
        text = "".join(t for t, _ in message.messages)
        self.assertNotIn("Created", text)


class TestUserConfigList(UserConfigCommandTestCase):

    """The --list view."""

    def test_list_does_not_open_an_editor(self):
        """Listing is read-only: no editor, no file creation."""
        message = task_configuration.user_config(list_only=True)
        self.call.assert_not_called()
        self.assertFalse(os.path.exists(user_config.config_path()))
        self.assertTrue(message.success)

    def test_list_shows_every_setting_with_its_value(self):
        """Each registered setting and its value in force is listed."""
        message = task_configuration.user_config(list_only=True)
        text = "".join(t for t, _ in message.messages)
        for setting in user_config.SETTINGS:
            self.assertIn(setting.name, text)
        self.assertIn("vi", text)

    def test_list_marks_defaulted_values(self):
        """A value that came from the default is labelled as such."""
        message = task_configuration.user_config(list_only=True)
        text = "".join(t for t, _ in message.messages)
        self.assertIn("default", text.lower())

    def test_list_reflects_configured_value(self):
        """A configured value is shown instead of the default."""
        os.makedirs(os.path.dirname(user_config.config_path()), exist_ok=True)
        with open(user_config.config_path(), "w", encoding="utf-8") as f:
            f.write("editor: emacs\n")
        message = task_configuration.user_config(list_only=True)
        text = "".join(t for t, _ in message.messages)
        self.assertIn("emacs", text)


if __name__ == "__main__":
    unittest.main()
