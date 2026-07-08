"""Tests for Chern Shell tab completions, especially project-root (@/) paths."""

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from CelebiChrono.interface.chern_shell.base import ChernShellBase


class TestShellCompletions(unittest.TestCase):
    """Tests for ChernShellBase.get_completions."""

    def setUp(self):
        self.shell = ChernShellBase()
        self.project_dir = tempfile.mkdtemp()
        # Sample project structure
        os.makedirs(os.path.join(self.project_dir, "tasks", "task1"))
        os.makedirs(os.path.join(self.project_dir, "tasks", "task2"))
        os.makedirs(os.path.join(self.project_dir, "algorithms", "algo1"))
        os.makedirs(os.path.join(self.project_dir, "data"))

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def test_at_alone_expands_to_at_slash(self):
        """Bare '@' should complete to '@/'."""
        result = self.shell.get_completions(
            self.project_dir, "@", "add_algorithm @"
        )
        self.assertEqual(result, ["@/"])

    @patch("CelebiChrono.interface.chern_shell.base.csys.project_path")
    def test_at_slash_lists_project_root(self, mock_project_path):
        """'@/' should list directories at the project root."""
        mock_project_path.return_value = self.project_dir
        result = self.shell.get_completions(
            self.project_dir, "@/", "add_algorithm @/"
        )
        self.assertIn("@/tasks/", result)
        self.assertIn("@/algorithms/", result)
        self.assertIn("@/data/", result)
        self.assertNotIn("@/.celebi", result)

    @patch("CelebiChrono.interface.chern_shell.base.csys.project_path")
    def test_at_slash_prefix_filters(self, mock_project_path):
        """'@/t' should filter to project-root directories starting with 't'."""
        mock_project_path.return_value = self.project_dir
        result = self.shell.get_completions(
            self.project_dir, "@/t", "add_algorithm @/t"
        )
        self.assertEqual(result, ["@/tasks/"])

    @patch("CelebiChrono.interface.chern_shell.base.csys.project_path")
    def test_at_slash_subdirectory(self, mock_project_path):
        """'@/tasks/' should list task subdirectories."""
        mock_project_path.return_value = self.project_dir
        result = self.shell.get_completions(
            self.project_dir, "@/tasks/", "add_algorithm @/tasks/"
        )
        self.assertIn("@/tasks/task1/", result)
        self.assertIn("@/tasks/task2/", result)

    def test_plain_relative_paths_still_work(self):
        """Relative paths without '@/' should still complete normally."""
        current_path = os.path.join(self.project_dir, "tasks")
        result = self.shell.get_completions(current_path, "t", "add_algorithm t")
        self.assertIn("task1/", result)
        self.assertIn("task2/", result)

    def test_at_slash_outside_project_returns_empty(self):
        """'@/' outside a project should yield no completions."""
        non_project = tempfile.mkdtemp()
        try:
            result = self.shell.get_completions(non_project, "@/", "add_algorithm @/")
            self.assertEqual(result, [])
        finally:
            shutil.rmtree(non_project)


if __name__ == "__main__":
    unittest.main()
