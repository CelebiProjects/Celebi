"""CLI coverage for scoped SSH impression sharing."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from CelebiChrono.celebi_cli.commands.utilities import (
    share_ssh_impressions_command,
)
from CelebiChrono.interface.ChernShell import ChernShell
from CelebiChrono.interface.shell_modules import utilities
from CelebiChrono.utils.message import Message


def test_cli_forwards_export_runner_and_options():
    """The one-shot command needs only an operation and runner."""
    message = Message()
    message.add("ok", "success")
    with patch("CelebiChrono.interface.shell.share_ssh_impressions",
               return_value=message) as share:
        result = CliRunner().invoke(share_ssh_impressions_command, [
            "--export", "--force", "--timeout", "120", "cluster",
        ])
    assert result.exit_code == 0, result.output
    share.assert_called_once_with(
        "cluster", "export", force=True, timeout=120)


def test_cli_requires_exactly_one_operation():
    """Import and export flags are mutually exclusive and required."""
    runner = CliRunner()
    missing = runner.invoke(share_ssh_impressions_command, ["cluster"])
    assert missing.exit_code != 0
    assert "Choose exactly one" in missing.output
    both = runner.invoke(share_ssh_impressions_command, [
        "--import", "--export", "cluster",
    ])
    assert both.exit_code != 0
    assert "Choose exactly one" in both.output


def _task(uuid="a" * 32):
    task = MagicMock()
    task.object_type.return_value = "task"
    task.project_path.return_value = "/project"
    task.project_uuid.return_value = "project-uuid"
    task.impression.return_value = SimpleNamespace(uuid=uuid)
    task.path = "/project/task"
    return task


def test_import_impresses_current_task_before_request():
    """Import refreshes identity and sends only the current task UUID."""
    current = _task()
    communicator = MagicMock()
    communicator.share_ssh_impressions.return_value = {"job_id": "job-1234"}
    communicator.share_ssh_impressions_status.return_value = {
        "status": "done", "result": {
            "count": 1, "impressions": ["a" * 32],
        }}
    with patch.object(utilities.MANAGER, "current_object", return_value=current), \
            patch.object(utilities.ChernCommunicator, "instance",
                         return_value=communicator):
        result = utilities.share_ssh_impressions("cluster", "import")

    assert result.success
    current.impress.assert_called_once_with()
    communicator.share_ssh_impressions.assert_called_once_with(
        "cluster", "project-uuid", "import", ["a" * 32], force=False)


@pytest.mark.parametrize("scope_type", ["directory", "project"])
def test_container_scope_recurses_over_tasks_without_export_impress(scope_type):
    """Directory/project export selects descendant tasks and active IDs."""
    current = MagicMock()
    current.object_type.return_value = scope_type
    current.project_path.return_value = "/project"
    current.project_uuid.return_value = "project-uuid"
    first, second = _task("a" * 32), _task("b" * 32)
    algorithm = MagicMock()
    algorithm.object_type.return_value = "algorithm"
    current.sub_objects_recursively.return_value = [current, first, algorithm, second]
    communicator = MagicMock()
    communicator.share_ssh_impressions.return_value = {"job_id": "job-1234"}
    communicator.share_ssh_impressions_status.return_value = {
        "status": "done", "result": {"count": 2}}
    with patch.object(utilities.MANAGER, "current_object", return_value=current), \
            patch.object(utilities.ChernCommunicator, "instance",
                         return_value=communicator):
        result = utilities.share_ssh_impressions("cluster", "export")

    assert result.success
    current.impress.assert_not_called()
    communicator.share_ssh_impressions.assert_called_once_with(
        "cluster", "project-uuid", "export", ["a" * 32, "b" * 32],
        force=False)


def test_algorithm_scope_is_rejected():
    """Algorithms do not own result sets and are not valid scopes."""
    current = MagicMock()
    current.object_type.return_value = "algorithm"
    current.project_path.return_value = "/project"
    with patch.object(utilities.MANAGER, "current_object", return_value=current):
        result = utilities.share_ssh_impressions("cluster", "export")
    assert not result.success
    assert "task or a directory/project" in result.messages[0][0]


def test_interactive_shell_uses_current_scope(capsys):
    """The persistent shell exposes the same runner-only syntax."""
    message = Message()
    message.add("ok", "success")
    with patch("CelebiChrono.interface.chern_shell.commands_documentation."
               "shell.share_ssh_impressions", return_value=message) as share:
        ChernShell().onecmd(
            "share-ssh-impressions --import cluster --force --timeout 120")
    capsys.readouterr()
    share.assert_called_once_with(
        "cluster", "import", force=True, timeout=120)
