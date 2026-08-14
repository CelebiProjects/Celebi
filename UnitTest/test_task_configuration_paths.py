"""Tests for project-root path resolution in task configuration commands."""

import unittest
from unittest.mock import patch, MagicMock

from CelebiChrono.interface.shell_modules import task_configuration
from CelebiChrono.interface.shell_modules._manager import MANAGER


class TestResolveProjectPath(unittest.TestCase):
    """Tests for the _resolve_project_path helper."""

    @patch.object(task_configuration, "csys")
    def test_at_slash_resolves_to_project_root(self, mock_csys):
        """Test at slash resolves to project root."""
        mock_csys.project_path.return_value = "/project"
        result = task_configuration._resolve_project_path("@/tasks/foo")  # pylint: disable=protected-access
        self.assertEqual(result, "/project/tasks/foo")

    @patch.object(task_configuration, "csys")
    def test_at_alone_resolves_to_project_root(self, mock_csys):
        """Test at alone resolves to project root."""
        mock_csys.project_path.return_value = "/project"
        result = task_configuration._resolve_project_path("@")  # pylint: disable=protected-access
        self.assertEqual(result, "/project")

    @patch.object(task_configuration, "csys")
    def test_plain_relative_path_unchanged(self, mock_csys):
        """Test plain relative path unchanged."""
        result = task_configuration._resolve_project_path("tasks/foo")  # pylint: disable=protected-access
        self.assertEqual(result, "tasks/foo")
        mock_csys.project_path.assert_not_called()

    @patch.object(task_configuration, "csys")
    def test_absolute_path_unchanged(self, mock_csys):
        """Test absolute path unchanged."""
        result = task_configuration._resolve_project_path("/abs/path")  # pylint: disable=protected-access
        self.assertEqual(result, "/abs/path")
        mock_csys.project_path.assert_not_called()


class TestAddInputPathResolution(unittest.TestCase):
    """Tests that add_input resolves @/ paths."""

    @patch.object(task_configuration, "csys")
    @patch.object(MANAGER, "current_object")
    def test_add_input_resolves_at_slash_path(self, mock_current_object, mock_csys):
        """Test add input resolves at slash path."""
        mock_csys.project_path.return_value = "/project"
        mock_task = MagicMock()
        mock_task.object_type.return_value = "task"
        mock_current_object.return_value = mock_task

        task_configuration.add_input("@/tasks/prev/output", "result")

        mock_task.add_input.assert_called_once_with(
            "/project/tasks/prev/output", "result"
        )

    @patch.object(task_configuration, "csys")
    @patch.object(MANAGER, "current_object")
    def test_add_input_keeps_plain_path(self, mock_current_object, mock_csys):
        """Test add input keeps plain path."""
        mock_task = MagicMock()
        mock_task.object_type.return_value = "task"
        mock_current_object.return_value = mock_task

        task_configuration.add_input("tasks/prev/output", "result")

        mock_task.add_input.assert_called_once_with("tasks/prev/output", "result")
        mock_csys.project_path.assert_not_called()


class TestAddAlgorithmPathResolution(unittest.TestCase):
    """Tests that add_algorithm resolves @/ paths."""

    @patch.object(task_configuration, "csys")
    @patch.object(MANAGER, "current_object")
    def test_add_algorithm_resolves_at_slash_path(self, mock_current_object, mock_csys):
        """Test add algorithm resolves at slash path."""
        mock_csys.project_path.return_value = "/project"
        mock_task = MagicMock()
        mock_task.object_type.return_value = "task"
        mock_current_object.return_value = mock_task

        task_configuration.add_algorithm("@/algorithms/proc")

        mock_task.add_algorithm.assert_called_once_with("/project/algorithms/proc")

    @patch.object(task_configuration, "csys")
    @patch.object(MANAGER, "current_object")
    def test_add_algorithm_keeps_plain_path(self, mock_current_object, mock_csys):
        """Test add algorithm keeps plain path."""
        mock_task = MagicMock()
        mock_task.object_type.return_value = "task"
        mock_current_object.return_value = mock_task

        task_configuration.add_algorithm("algorithms/proc")

        mock_task.add_algorithm.assert_called_once_with("algorithms/proc")
        mock_csys.project_path.assert_not_called()


class TestAddParameterSubtaskPathResolution(unittest.TestCase):
    """Tests that add_parameter_subtask resolves @/ paths."""

    @patch.object(task_configuration, "csys")
    @patch.object(MANAGER, "current_object")
    @patch.object(MANAGER, "sub_object")
    def test_add_parameter_subtask_resolves_at_slash_path(
        self, mock_sub_object, mock_current_object, mock_csys
    ):
        """Test add parameter subtask resolves at slash path."""
        mock_csys.project_path.return_value = "/project"
        mock_dir = MagicMock()
        mock_dir.object_type.return_value = "directory"
        mock_current_object.return_value = mock_dir
        mock_task = MagicMock()
        mock_task.is_task.return_value = True
        mock_sub_object.return_value = mock_task

        task_configuration.add_parameter_subtask("@/tasks/model", "lr", "0.01")

        mock_sub_object.assert_called_once_with("/project/tasks/model")
        mock_task.add_parameter.assert_called_once_with("lr", "0.01")

    @patch.object(task_configuration, "csys")
    @patch.object(MANAGER, "current_object")
    @patch.object(MANAGER, "sub_object")
    def test_add_parameter_subtask_keeps_plain_path(
        self, mock_sub_object, mock_current_object, mock_csys
    ):
        """Test add parameter subtask keeps plain path."""
        mock_dir = MagicMock()
        mock_dir.object_type.return_value = "directory"
        mock_current_object.return_value = mock_dir
        mock_task = MagicMock()
        mock_task.is_task.return_value = True
        mock_sub_object.return_value = mock_task

        task_configuration.add_parameter_subtask("tasks/model", "lr", "0.01")

        mock_sub_object.assert_called_once_with("tasks/model")
        mock_task.add_parameter.assert_called_once_with("lr", "0.01")
        mock_csys.project_path.assert_not_called()


if __name__ == "__main__":
    unittest.main()
