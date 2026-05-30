"""REANA Repository Booking module.

Handles direct communication with REANA REST API to upload
Celebi project files as a workspace catalog entry.
"""
import os
import fnmatch
from logging import getLogger

import requests
import yaml

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

    def _auth_params(self, extra=None):
        """Build query params with access_token.

        Args:
            extra: Additional query params to include

        Returns:
            dict: Query parameters including access_token
        """
        params = {"access_token": self.access_token}
        if extra:
            params.update(extra)
        return params

    def book_project(self, project_path: str, project_name: str) -> Message:
        """Book a Celebi project to REANA.

        Uploads all project files to a REANA workflow named
        'celebi-{project_name}'. Creates the workflow if it does not exist.

        Args:
            project_path: Absolute path to the Celebi project directory
            project_name: Name of the project

        Returns:
            Message: Success or error message with REANA workflow URL
        """
        if not os.path.isdir(project_path):
            message = Message()
            message.add(f"Invalid project path: {project_path}\n", "error")
            return message

        message = Message()
        workflow_name = f"celebi-{project_name}"

        # Check if workflow exists
        workflow = self._get_workflow(workflow_name)
        if workflow is None:
            message.add(f"Creating REANA workflow '{workflow_name}'...\n", "normal")
            workflow = self._create_workflow(workflow_name)
            message.add(f"Workflow created: {workflow_name}\n", "success")
        else:
            message.add(f"Using existing REANA workflow '{workflow_name}'\n", "success")

        workflow_id = workflow.get("id", workflow.get("name", workflow_name))

        # Upload files
        message.add("Uploading project files...\n", "normal")
        try:
            self._upload_files(workflow_id, project_path)
            message.add("Files uploaded successfully.\n", "success")
            message.add(
                f"REANA workspace: {self.server_url}/api/workflows/{workflow_id}/workspace\n",
                "info",
            )
        except requests.exceptions.RequestException as e:
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
        """Get workflow by name, or None if not found.

        Args:
            name: Workflow name to search for

        Returns:
            dict or None: Workflow dict if found, None otherwise
        """
        try:
            response = requests.get(
                f"{self.server_url}/api/workflows",
                params=self._auth_params({
                    "search": name,
                    "size": 100,
                    "type": "batch",
                }),
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])
            for item in items:
                if item.get("name") == name:
                    return item
            return None
        except requests.exceptions.RequestException as e:
            logger.warning("Failed to list workflows: %s", e)
            return None

    def _create_workflow(self, name: str):
        """Create a new minimal workflow on REANA.

        Args:
            name: Name for the new workflow

        Returns:
            dict: Created workflow information

        Raises:
            RuntimeError: If workflow creation fails
        """
        spec_path = os.path.join(
            os.path.dirname(__file__), "reana_booking_spec.yaml"
        )
        with open(spec_path, "r", encoding="utf-8") as f:
            reana_specification = yaml.safe_load(f)

        payload = {
            "reana_specification": reana_specification,
        }

        response = requests.post(
            f"{self.server_url}/api/workflows",
            params=self._auth_params({"workflow_name": name}),
            json=payload,
            timeout=self.timeout,
            verify=self.verify_ssl,
        )
        response.raise_for_status()
        result = response.json()

        if not result.get("workflow_id") and not result.get("name"):
            raise RuntimeError(f"Workflow creation failed: {result}")

        return result

    def _upload_files(self, workflow_id: str, project_path: str):
        """Upload project files to REANA workflow workspace.

        Args:
            workflow_id: REANA workflow ID
            project_path: Path to project directory

        Raises:
            requests.exceptions.RequestException: On upload failure
        """
        for root, dirs, files in os.walk(project_path):
            # Filter out ignored directories to avoid descending into them
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
                    response = requests.post(
                        f"{self.server_url}/api/workflows/{workflow_id}/workspace",
                        params=self._auth_params({"file_name": relative_path}),
                        data=file_content,
                        headers={"Content-Type": "application/octet-stream"},
                        timeout=self.timeout,
                        verify=self.verify_ssl,
                    )
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    logger.warning("Failed to upload %s: %s", relative_path, e)

    def _should_ignore(self, relative_path: str) -> bool:
        """Check if a relative path should be ignored during upload.

        Args:
            relative_path: Path relative to project root

        Returns:
            bool: True if path should be skipped
        """
        normalized = relative_path.replace(os.sep, "/")
        for pattern in DEFAULT_IGNORE_PATTERNS:
            if fnmatch.fnmatch(normalized, pattern):
                return True
        return False
