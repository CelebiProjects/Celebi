"""REANA Repository Booking module.

Uses the official reana_client library for correct API formatting.
"""
import json
import os
import fnmatch
from logging import getLogger

import yaml

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
            workflow = self._create_workflow(workflow_name, project_path)
            message.add(f"Workflow created: {workflow_name}\n", "success")
        else:
            message.add(f"Using existing REANA workflow '{workflow_name}'\n", "success")

        workflow_id = workflow.get("workflow_id", workflow.get("id", workflow.get("name", workflow_name)))

        # If reusing existing workflow, clear old folders first
        if workflow is not None:
            cleared = self._clear_old_folders(workflow_id, project_path)
            if cleared:
                message.add("Cleared old folders from workspace.\n", "normal")

        # Upload files
        message.add("Uploading project files...\n", "normal")
        try:
            self._upload_files(workflow_id, project_path)
            # Upload reana_repo.yaml so it can be fetched on next booking
            self._upload_repo_yaml(workflow_id, project_path)
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

    def _create_workflow(self, name: str, project_path: str = ""):
        """Create a new minimal workflow on REANA."""
        spec_path = os.path.join(
            os.path.dirname(__file__), "reana_booking_spec.yaml"
        )
        with open(spec_path, "r", encoding="utf-8") as f:
            reana_specification = yaml.safe_load(f)

        # Inject project structure metadata if project_path is provided
        if project_path and os.path.isdir(project_path):
            reana_specification["reana_repo"] = self._build_repo_metadata(project_path)

        result = reana_client.create_workflow(
            reana_specification=reana_specification,
            name=name,
            access_token=self.access_token,
        )

        if not result.get("workflow_id") and not result.get("workflow_name"):
            raise RuntimeError(f"Workflow creation failed: {result}")

        return result

    def _build_repo_metadata(self, project_path: str) -> dict:
        """Build project structure metadata for the reana_repo field.

        Walks the project directory and records Celebi objects
        (tasks, algorithms, directories) with their metadata.

        Args:
            project_path: Path to the Celebi project directory.

        Returns:
            dict: Project structure metadata.
        """
        repo_metadata = {
            "project_name": os.path.basename(os.path.normpath(project_path)),
            "description": "Celebi project structure catalog",
            "objects": [],
        }

        for root, dirs, _files in os.walk(project_path):
            # Skip ignored directories
            dirs[:] = [
                d for d in dirs
                if not self._should_ignore(
                    os.path.relpath(os.path.join(root, d), project_path)
                )
            ]

            for d in dirs:
                dir_path = os.path.join(root, d)
                config_path = os.path.join(dir_path, ".celebi", "config.json")
                if not os.path.exists(config_path):
                    continue

                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                except (json.JSONDecodeError, OSError):
                    continue

                obj_type = config.get("object_type", "")
                if not obj_type:
                    continue

                rel_path = os.path.relpath(dir_path, project_path)
                obj_entry = {
                    "path": rel_path,
                    "type": obj_type,
                }

                # Read celebi.yaml for tasks and algorithms
                if obj_type in ("task", "algorithm"):
                    celebi_yaml_path = os.path.join(dir_path, "celebi.yaml")
                    if os.path.exists(celebi_yaml_path):
                        try:
                            with open(celebi_yaml_path, "r", encoding="utf-8") as f:
                                celebi_meta = yaml.safe_load(f) or {}
                            if "descriptor" in celebi_meta:
                                obj_entry["descriptor"] = celebi_meta["descriptor"]
                            if "environment" in celebi_meta:
                                obj_entry["environment"] = celebi_meta["environment"]
                            if "memory_limit" in celebi_meta:
                                obj_entry["memory_limit"] = celebi_meta["memory_limit"]
                        except (yaml.YAMLError, OSError):
                            pass

                repo_metadata["objects"].append(obj_entry)

        # Sort by path for deterministic output
        repo_metadata["objects"].sort(key=lambda x: x["path"])

        return repo_metadata

    def _sanitize_upload_path(self, relative_path: str) -> str:
        """Convert hidden directory names to readable names for REANA upload.

        REANA's REST API may have issues with hidden file paths (e.g., .celebi).
        This method prefixes hidden directory names with "dot_" so they remain
        identifiable while being REST-API friendly.

        Args:
            relative_path: Original relative path from project root.

        Returns:
            str: Sanitized path with hidden directory names prefixed by dot_.

        Examples:
            .celebi/config.json -> dot_celebi/config.json
            tasks/.hidden/file.txt -> tasks/dot_hidden/file.txt
            src/main.py -> src/main.py
        """
        parts = relative_path.replace(os.sep, "/").split("/")
        sanitized = []
        for part in parts[:-1]:  # All but the file name
            if part.startswith(".") and len(part) > 1:
                sanitized.append(f"dot_{part[1:]}")
            else:
                sanitized.append(part)
        sanitized.append(parts[-1])  # Keep file name unchanged
        return "/".join(sanitized)

    def _upload_files(self, workflow_id: str, project_path: str):
        """Upload project files to REANA workflow workspace."""
        # First pass: count total files to upload
        total_files = 0
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [
                d for d in dirs
                if not self._should_ignore(
                    os.path.relpath(os.path.join(root, d), project_path)
                )
            ]
            for filename in files:
                relative_path = os.path.relpath(os.path.join(root, filename), project_path)
                if not self._should_ignore(relative_path):
                    total_files += 1

        if total_files == 0:
            print("No files to upload.")
            return

        print(f"Uploading {total_files} files...")
        uploaded_count = 0
        failed_count = 0

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
                    failed_count += 1
                    continue

                upload_name = self._sanitize_upload_path(relative_path)
                try:
                    reana_client.upload_file(
                        workflow=workflow_id,
                        file_=file_content,
                        file_name=upload_name,
                        access_token=self.access_token,
                    )
                    uploaded_count += 1
                    if uploaded_count % 10 == 0 or uploaded_count == total_files:
                        print(f"  Progress: {uploaded_count}/{total_files} files uploaded...")
                except Exception as e:
                    logger.warning("Failed to upload %s: %s", relative_path, e)
                    failed_count += 1

        print(f"Upload complete: {uploaded_count} succeeded, {failed_count} failed.")

    def _upload_repo_yaml(self, workflow_id: str, project_path: str):
        """Upload reana_repo.yaml to workspace for future cleanup.

        Args:
            workflow_id: REANA workflow ID.
            project_path: Path to the Celebi project directory.
        """
        repo_metadata = self._build_repo_metadata(project_path)
        yaml_content = yaml.safe_dump(
            repo_metadata,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        ).encode("utf-8")
        print("Uploading reana_repo.yaml...")
        try:
            reana_client.upload_file(
                workflow=workflow_id,
                file_=yaml_content,
                file_name="reana_repo.yaml",
                access_token=self.access_token,
            )
            print("reana_repo.yaml uploaded successfully.")
        except Exception as e:
            logger.warning("Failed to upload reana_repo.yaml: %s", e)

    def _clear_old_folders(self, workflow_id: str, project_path: str) -> bool:
        """Clear old folders from REANA workspace before re-uploading.

        Downloads the existing reana_repo.yaml from the workflow workspace,
        parses it to find old folder paths, and deletes those files.

        Args:
            workflow_id: REANA workflow ID.
            project_path: Local project path.

        Returns:
            bool: True if old folders were cleared (or no reana_repo.yaml found).
        """
        try:
            print("Checking for existing reana_repo.yaml in workspace...")
            old_repo = self._download_workspace_file(workflow_id, "reana_repo.yaml")
            if old_repo is None:
                print("No previous reana_repo.yaml found. Skipping cleanup.")
                return True

            print("Found reana_repo.yaml. Parsing old folder list...")
            old_metadata = yaml.safe_load(old_repo)
            if not old_metadata or "objects" not in old_metadata:
                print("No old folders recorded. Skipping cleanup.")
                return True

            # Get list of current files in workspace
            print("Listing current workspace files...")
            workspace_files = self._list_workspace_files(workflow_id)
            print(f"Found {len(workspace_files)} files in workspace.")

            # Build set of old folder prefixes to delete
            old_prefixes = set()
            for obj in old_metadata["objects"]:
                old_path = obj.get("path", "")
                if old_path:
                    sanitized = self._sanitize_upload_path(old_path)
                    old_prefixes.add(sanitized)

            # Delete files that belong to old folders
            files_to_delete = []
            for file_info in workspace_files:
                file_name = file_info.get("name", "")
                if any(
                    file_name == prefix or file_name.startswith(prefix + "/")
                    for prefix in old_prefixes
                ):
                    files_to_delete.append(file_name)

            if not files_to_delete:
                print("No old files to delete.")
                return True

            print(f"Deleting {len(files_to_delete)} old files...")
            deleted_count = 0
            for idx, file_name in enumerate(files_to_delete, 1):
                try:
                    print(f"  [{idx}/{len(files_to_delete)}] Deleting {file_name}...")
                    self._delete_workspace_file(workflow_id, file_name)
                    deleted_count += 1
                except Exception as e:
                    logger.warning("Failed to delete %s: %s", file_name, e)

            print(f"Deleted {deleted_count}/{len(files_to_delete)} old files.")
            return True

        except Exception as e:
            logger.warning("Failed to clear old folders: %s", e)
            return False

    def _download_workspace_file(self, workflow_id: str, file_name: str):
        """Download a file from REANA workflow workspace.

        Args:
            workflow_id: REANA workflow ID.
            file_name: Name/path of the file to download.

        Returns:
            str or None: File content as string, or None if not found.
        """
        try:
            content, _filename, _is_zip = reana_client.download_file(
                workflow=workflow_id,
                file_name=file_name,
                access_token=self.access_token,
            )
            if isinstance(content, bytes):
                return content.decode("utf-8")
            return content
        except Exception:
            return None

    def _list_workspace_files(self, workflow_id: str) -> list:
        """List files in REANA workflow workspace.

        Args:
            workflow_id: REANA workflow ID.

        Returns:
            list: List of file info dicts with 'name' keys.
        """
        try:
            return reana_client.list_files(
                workflow=workflow_id,
                access_token=self.access_token,
            ) or []
        except Exception:
            return []

    def _delete_workspace_file(self, workflow_id: str, file_name: str):
        """Delete a file from REANA workflow workspace.

        Args:
            workflow_id: REANA workflow ID.
            file_name: Name/path of the file to delete.

        Raises:
            Exception: On deletion failure.
        """
        reana_client.delete_file(
            workflow=workflow_id,
            file_name=file_name,
            access_token=self.access_token,
        )

    def _should_ignore(self, relative_path: str) -> bool:
        """Check if a relative path should be ignored during upload."""
        normalized = relative_path.replace(os.sep, "/")
        for pattern in DEFAULT_IGNORE_PATTERNS:
            if fnmatch.fnmatch(normalized, pattern):
                return True
        return False
