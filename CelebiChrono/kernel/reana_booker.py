"""REANA Repository Booking module.

Uses the official reana_client library for correct API formatting.
"""
import os
import fnmatch
from logging import getLogger

from reana_client.api import client as reana_client
from reana_commons.api_client import BaseAPIClient

from ..utils.message import Message

logger = getLogger("ChernLogger")


DEFAULT_IGNORE_PATTERNS = [
    ".celebi/impressions/*",
    ".celebi/impressions_store/*",
    ".celebi/config.local.json",
    ".git/*",
    "__pycache__/*",
    "*.pyc",
    "*~",
    "*.swp",
    "*.swo",
    "*.~undo-tree~",
    ".DS_Store",
    "*.tmp",
    "*.temp",
]


class ReanaBooker:
    """Handles booking (uploading) a Celebi repository to REANA."""

    def __init__(self, server_url: str, access_token: str, verify_ssl: bool = True):
        """Initialize with REANA server URL and access token.

        Args:
            server_url: REANA server URL (e.g., "https://reana.cern.ch")
            access_token: REANA access token for authentication
            verify_ssl: Whether to verify SSL certificates
        """
        self.server_url = server_url.rstrip("/")
        self.access_token = access_token
        self.verify_ssl = verify_ssl
        self.timeout = 30

    def _setup_env(self):
        """Set REANA_SERVER_URL environment variable for the client."""
        os.environ["REANA_SERVER_URL"] = self.server_url
        # Disable SSL verification if requested
        if not self.verify_ssl:
            os.environ["REANA_CLIENT_VERIFY_SSL"] = "false"
        elif "REANA_CLIENT_VERIFY_SSL" in os.environ:
            del os.environ["REANA_CLIENT_VERIFY_SSL"]
        # Force re-initialization of the API client singleton
        try:
            BaseAPIClient("reana-server")
        except Exception:
            pass

    def book_project(self, project_path: str, project_name: str) -> Message:
        """Book a Celebi project to REANA."""
        if not os.path.isdir(project_path):
            message = Message()
            message.add(f"Invalid project path: {project_path}\n", "error")
            return message

        message = Message()
        workflow_name = f"celebi-{project_name}"

        self._setup_env()

        # Check if workflow exists
        workflow = self._get_workflow(workflow_name)
        if workflow is None:
            message.add(f"Creating REANA workflow '{workflow_name}'...\n", "normal")
            workflow = self._create_workflow(workflow_name)
            message.add(f"Workflow created: {workflow_name}\n", "success")
        else:
            message.add(f"Using existing REANA workflow '{workflow_name}'\n", "success")

        workflow_id = workflow.get("workflow_id", workflow.get("id", workflow.get("name", workflow_name)))

        # Upload files
        message.add("Uploading project files...\n", "normal")
        try:
            self._upload_files(workflow_id, project_path)
            message.add("Files uploaded successfully.\n", "success")
            message.add(
                f"REANA workspace: {self.server_url}/api/workflows/{workflow_id}/workspace\n",
                "info",
            )
        except Exception as e:
            message.add(f"Upload failed: {e}\n", "error")
            message.data["workflow_name"] = workflow_name
            message.data["workflow_id"] = workflow_id
            message.data["server_url"] = self.server_url
            return message

        message.data["workflow_name"] = workflow_name
        message.data["workflow_id"] = workflow_id
        message.data["server_url"] = self.server_url
        return message

    def _get_workflow(self, name: str):
        """Get workflow by name, or None if not found."""
        try:
            workflows = reana_client.get_workflows(
                access_token=self.access_token,
                type="batch",
                search=name,
                size=100,
            )
            for wf in workflows:
                if wf.get("name") == name:
                    return wf
            return None
        except Exception as e:
            logger.warning("Failed to list workflows: %s", e)
            return None

    def _create_workflow(self, name: str):
        """Create a new minimal workflow on REANA."""
        import yaml

        spec_path = os.path.join(
            os.path.dirname(__file__), "reana_booking_spec.yaml"
        )
        with open(spec_path, "r", encoding="utf-8") as f:
            reana_specification = yaml.safe_load(f)

        result = reana_client.create_workflow(
            reana_specification=reana_specification,
            name=name,
            access_token=self.access_token,
        )

        if not result.get("workflow_id") and not result.get("workflow_name"):
            raise RuntimeError(f"Workflow creation failed: {result}")

        return result

    def _upload_files(self, workflow_id: str, project_path: str):
        """Upload project files to REANA workflow workspace."""
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [
                d for d in dirs
                if not self._should_ignore(
                    os.path.relpath(os.path.join(root, d), project_path)
                )
            ]

            for filename in files:
                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, project_path)

                if self._should_ignore(relative_path):
                    continue

                try:
                    with open(file_path, "rb") as f:
                        file_content = f.read()
                except OSError as e:
                    logger.warning("Skipping unreadable file %s: %s", file_path, e)
                    continue

                try:
                    reana_client.upload_file(
                        workflow=workflow_id,
                        file_=file_content,
                        file_name=relative_path,
                        access_token=self.access_token,
                    )
                except Exception as e:
                    logger.warning("Failed to upload %s: %s", relative_path, e)

    def _should_ignore(self, relative_path: str) -> bool:
        """Check if a relative path should be ignored during upload."""
        normalized = relative_path.replace(os.sep, "/")
        for pattern in DEFAULT_IGNORE_PATTERNS:
            if fnmatch.fnmatch(normalized, pattern):
                return True
        return False
