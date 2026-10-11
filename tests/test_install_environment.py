"""Project-scoped runner environment commands."""

from unittest import mock

from click.testing import CliRunner

from CelebiChrono.celebi_cli.cli import cli
from CelebiChrono.interface.shell_modules import communication


def test_cli_install_environment_help_describes_default_spec():
    result = CliRunner().invoke(cli, ["install-environment", "--help"])

    assert result.exit_code == 0
    assert "RUNNER NAME" in result.output
    assert ".celebi-env/NAME.yaml" in result.output
    assert "Install or update a project environment" in result.output


def test_install_environment_uses_project_default_yaml(tmp_path):
    spec_dir = tmp_path / ".celebi-env"
    spec_dir.mkdir()
    (spec_dir / "analysis.yaml").write_text(
        "name: ignored\ndependencies:\n  - python=3.12\n", encoding="utf-8")
    communicator = mock.Mock()
    communicator.install_environment.return_value = {"job_id": "job-1"}
    communicator.install_environment_status.return_value = {
        "status": "done",
        "result": {"path": "/remote/environments/project-1/analysis"},
    }

    with mock.patch.object(communication, "_current_project",
                           return_value=(str(tmp_path), "project-1")), \
            mock.patch.object(communication.ChernCommunicator, "instance",
                              return_value=communicator):
        result = communication.install_environment("ihep", "analysis")

    communicator.install_environment.assert_called_once_with(
        "ihep", "project-1", "analysis",
        "name: ignored\ndependencies:\n  - python=3.12\n")
    assert any("is ready" in text for text, _style in result.messages)


def test_runner_environments_is_scoped_to_current_project():
    communicator = mock.Mock()
    communicator.runner_envs.return_value = {"envs": []}
    with mock.patch.object(communication, "_current_project_uuid",
                           return_value="project-1"), \
            mock.patch.object(communication.ChernCommunicator, "instance",
                              return_value=communicator):
        communication.runner_envs("cluster")

    communicator.runner_envs.assert_called_once_with("cluster", "project-1")
