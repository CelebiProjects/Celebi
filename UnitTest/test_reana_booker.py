"""Unit tests for ReanaBooker."""
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import requests
from colored import Fore, Style
from CelebiChrono.kernel.reana_booker import ReanaBooker, DEFAULT_IGNORE_PATTERNS


class TestReanaBooker(unittest.TestCase):
    """Test cases for ReanaBooker."""

    def setUp(self):
        """Set up test fixtures."""
        self.booker = ReanaBooker("https://reana.example.com", "test-token")

    def test_init(self):
        """Test initialization sets auth correctly."""
        print(Fore.BLUE + "Testing Init..." + Style.RESET)
        self.assertEqual(self.booker.server_url, "https://reana.example.com")
        self.assertEqual(self.booker.access_token, "test-token")
        self.assertTrue(self.booker.verify_ssl)

    def test_init_insecure(self):
        """Test initialization with verify_ssl=False."""
        print(Fore.BLUE + "Testing Init Insecure..." + Style.RESET)
        booker = ReanaBooker("https://reana.example.com", "test-token", verify_ssl=False)
        self.assertFalse(booker.verify_ssl)

    def test_auth_params(self):
        """Test auth params builder includes access_token."""
        print(Fore.BLUE + "Testing Auth Params..." + Style.RESET)
        params = self.booker._auth_params()
        self.assertEqual(params["access_token"], "test-token")

        params = self.booker._auth_params({"search": "test"})
        self.assertEqual(params["access_token"], "test-token")
        self.assertEqual(params["search"], "test")

    def test_should_ignore_exact_matches(self):
        """Test exact pattern matching for ignore rules."""
        print(Fore.BLUE + "Testing Should Ignore Exact..." + Style.RESET)
        self.assertTrue(self.booker._should_ignore(".celebi/config.local.json"))
        self.assertTrue(self.booker._should_ignore("test.pyc"))
        self.assertTrue(self.booker._should_ignore(".DS_Store"))
        self.assertTrue(self.booker._should_ignore("file.tmp"))
        self.assertTrue(self.booker._should_ignore("file.temp"))
        self.assertTrue(self.booker._should_ignore("backup~"))
        self.assertTrue(self.booker._should_ignore("file.swp"))
        self.assertTrue(self.booker._should_ignore("file.swo"))
        self.assertTrue(self.booker._should_ignore("file.~undo-tree~"))

    def test_should_ignore_directory_patterns(self):
        """Test directory prefix matching for ignore rules."""
        print(Fore.BLUE + "Testing Should Ignore Directory..." + Style.RESET)
        self.assertTrue(self.booker._should_ignore(".celebi/impressions/task1.tar.gz"))
        self.assertTrue(self.booker._should_ignore(".celebi/impressions_store/old.data"))
        self.assertTrue(self.booker._should_ignore(".git/config"))
        self.assertTrue(self.booker._should_ignore("__pycache__/module.cpython-39.pyc"))

    def test_should_not_ignore_kept_files(self):
        """Test that config.json and source files are not ignored."""
        print(Fore.BLUE + "Testing Should Not Ignore..." + Style.RESET)
        self.assertFalse(self.booker._should_ignore(".celebi/config.json"))
        self.assertFalse(self.booker._should_ignore("celebi.yaml"))
        self.assertFalse(self.booker._should_ignore("README.md"))
        self.assertFalse(self.booker._should_ignore("src/analysis.py"))
        self.assertFalse(self.booker._should_ignore("tasks/taskA/script.py"))

    def test_should_ignore_project_path_validation(self):
        """Test book_project validates project_path."""
        print(Fore.BLUE + "Testing Project Path Validation..." + Style.RESET)
        result = self.booker.book_project("/nonexistent/path", "test")
        self.assertFalse(result.success)
        self.assertIn("Invalid project path", str(result.messages))

    @patch("CelebiChrono.kernel.reana_booker.requests.get")
    def test_get_workflow_found(self, mock_get):
        """Test finding an existing workflow."""
        print(Fore.BLUE + "Testing Get Workflow Found..." + Style.RESET)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {"name": "celebi-test-project", "id": "workflow-123"}
            ]
        }
        mock_get.return_value = mock_response

        result = self.booker._get_workflow("celebi-test-project")

        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "celebi-test-project")
        self.assertEqual(result["id"], "workflow-123")
        mock_get.assert_called_once()
        # Verify access_token is in query params
        call_kwargs = mock_get.call_args.kwargs
        self.assertIn("params", call_kwargs)
        self.assertEqual(call_kwargs["params"]["access_token"], "test-token")
        self.assertEqual(call_kwargs["params"]["type"], "batch")

    @patch("CelebiChrono.kernel.reana_booker.requests.get")
    def test_get_workflow_not_found(self, mock_get):
        """Test when workflow does not exist."""
        print(Fore.BLUE + "Testing Get Workflow Not Found..." + Style.RESET)
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response

        result = self.booker._get_workflow("celebi-nonexistent")

        self.assertIsNone(result)

    @patch("CelebiChrono.kernel.reana_booker.requests.get")
    def test_get_workflow_connection_error(self, mock_get):
        """Test handling connection error during workflow lookup."""
        print(Fore.BLUE + "Testing Get Workflow Connection Error..." + Style.RESET)
        mock_get.side_effect = requests.exceptions.RequestException("Connection refused")

        result = self.booker._get_workflow("celebi-test")

        self.assertIsNone(result)

    @patch("CelebiChrono.kernel.reana_booker.requests.post")
    @patch("builtins.open", unittest.mock.mock_open(read_data="version: 0.8.0"))
    def test_create_workflow(self, mock_post):
        """Test creating a new workflow."""
        print(Fore.BLUE + "Testing Create Workflow..." + Style.RESET)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "workflow_id": "workflow-456",
            "workflow_name": "celebi-test"
        }
        mock_post.return_value = mock_response

        result = self.booker._create_workflow("celebi-test")

        self.assertEqual(result["workflow_id"], "workflow-456")
        mock_post.assert_called_once()
        # Verify workflow_name and access_token are in query params
        call_kwargs = mock_post.call_args.kwargs
        self.assertIn("params", call_kwargs)
        self.assertEqual(call_kwargs["params"]["access_token"], "test-token")
        self.assertEqual(call_kwargs["params"]["workflow_name"], "celebi-test")

    @patch("CelebiChrono.kernel.reana_booker.requests.post")
    def test_upload_files(self, mock_post):
        """Test uploading files to workflow workspace."""
        print(Fore.BLUE + "Testing Upload Files..." + Style.RESET)
        mock_post.return_value = MagicMock()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files
            with open(os.path.join(tmpdir, "README.md"), "w") as f:
                f.write("# Test")
            os.makedirs(os.path.join(tmpdir, "src"))
            with open(os.path.join(tmpdir, "src", "analysis.py"), "w") as f:
                f.write("print('hello')")
            # Create ignored file
            os.makedirs(os.path.join(tmpdir, ".celebi", "impressions"))
            with open(os.path.join(tmpdir, ".celebi", "impressions", "cache.tar"), "w") as f:
                f.write("ignored")

            self.booker._upload_files("workflow-123", tmpdir)

        # Should upload README.md and src/analysis.py, but not cache.tar
        calls = mock_post.call_args_list
        uploaded_files = []
        for call in calls:
            params = call.kwargs.get("params", {})
            uploaded_files.append(params.get("file_name", ""))

        self.assertIn("README.md", uploaded_files)
        # src/analysis.py should be uploaded (with os.sep normalization)
        src_path = os.path.join("src", "analysis.py")
        self.assertTrue(
            any(src_path in f or f.replace(os.sep, "/") == src_path.replace(os.sep, "/")
                for f in uploaded_files),
            f"Expected {src_path} in uploaded files, got {uploaded_files}"
        )
        # cache.tar should NOT be uploaded
        self.assertTrue(
            all("cache.tar" not in f for f in uploaded_files),
            "cache.tar should not be uploaded"
        )
        # Verify access_token is in query params for each upload
        for call in calls:
            params = call.kwargs.get("params", {})
            self.assertEqual(params.get("access_token"), "test-token")

    @patch("CelebiChrono.kernel.reana_booker.requests.get")
    @patch("CelebiChrono.kernel.reana_booker.requests.post")
    def test_book_project_existing_workflow(self, mock_post, mock_get):
        """Test booking with existing workflow."""
        print(Fore.BLUE + "Testing Book Project Existing..." + Style.RESET)
        # Mock existing workflow
        mock_get.return_value = MagicMock(
            json=lambda: {
                "items": [{"name": "celebi-test", "id": "wf-123"}]
            }
        )
        mock_post.return_value = MagicMock()

        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "README.md"), "w") as f:
                f.write("# Test")

            result = self.booker.book_project(tmpdir, "test")

        self.assertTrue(result.success)
        self.assertIn("Using existing REANA workflow", str(result.messages))

    @patch("CelebiChrono.kernel.reana_booker.requests.get")
    @patch("CelebiChrono.kernel.reana_booker.requests.post")
    @patch("builtins.open", unittest.mock.mock_open(read_data="version: 0.8.0"))
    def test_book_project_new_workflow(self, mock_post, mock_get):
        """Test booking creating new workflow."""
        print(Fore.BLUE + "Testing Book Project New..." + Style.RESET)
        # Mock no existing workflow
        mock_get.return_value = MagicMock(json=lambda: {"items": []})
        # Mock create workflow and file upload
        mock_post.side_effect = [
            MagicMock(json=lambda: {"workflow_id": "wf-456"}),
            MagicMock(),  # file upload
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "README.md"), "w") as f:
                f.write("# Test")

            result = self.booker.book_project(tmpdir, "test")

        self.assertTrue(result.success)
        self.assertIn("Creating REANA workflow", str(result.messages))


if __name__ == "__main__":
    unittest.main()
