"""Project registration can give a copied project a fresh identity."""

from unittest import mock

from click.testing import CliRunner

from CelebiChrono import main
from CelebiChrono.celebi_cli.cli import cli
from CelebiChrono.kernel import vproject
from CelebiChrono.utils import metadata


def test_use_project_new_project_replaces_uuid(tmp_path, monkeypatch):
    """The shared project metadata receives the newly generated UUID."""
    project = tmp_path / "analysis"
    project.mkdir()
    project_config = metadata.ConfigFile(str(project / ".celebi" / "config.json"))
    project_config.write_variable("object_type", "project")
    project_config.write_variable("project_uuid", "old-project-uuid")

    monkeypatch.setattr("builtins.input", lambda _prompt="": "n")
    monkeypatch.setattr(vproject.csys, "generate_uuid", lambda: "new-project-uuid")
    monkeypatch.setattr(
        vproject.csys,
        "configure_project_cache_policy",
        lambda _path: {"method": "mtime", "mode": "auto", "filesystem": "local"},
    )
    monkeypatch.setattr(vproject.csys, "local_config_path", lambda: str(tmp_path / "user.json"))

    vproject.use_project(str(project), new_project=True)

    assert project_config.read_variable("project_uuid") == "new-project-uuid"


def test_use_project_preserves_uuid_without_new_project(tmp_path, monkeypatch):
    """Normal registration keeps the existing project identity."""
    project = tmp_path / "analysis"
    project.mkdir()
    project_config = metadata.ConfigFile(str(project / ".celebi" / "config.json"))
    project_config.write_variable("object_type", "project")
    project_config.write_variable("project_uuid", "existing-project-uuid")

    monkeypatch.setattr("builtins.input", lambda _prompt="": "n")
    generate_uuid = mock.Mock(return_value="unexpected-project-uuid")
    monkeypatch.setattr(vproject.csys, "generate_uuid", generate_uuid)
    monkeypatch.setattr(
        vproject.csys,
        "configure_project_cache_policy",
        lambda _path: {"method": "mtime", "mode": "auto", "filesystem": "local"},
    )
    monkeypatch.setattr(vproject.csys, "local_config_path", lambda: str(tmp_path / "user.json"))

    vproject.use_project(str(project))

    assert project_config.read_variable("project_uuid") == "existing-project-uuid"
    generate_uuid.assert_not_called()


def test_celebi_use_forwards_new_project_option():
    """The interactive launcher exposes the requested command spelling."""
    with mock.patch.object(main.vproject, "use_project") as use_project, mock.patch.object(
            main, "start_chern_command_line"):
        result = CliRunner().invoke(main.cli, ["use", ".", "--new-project"])

    assert not result.exit_code
    use_project.assert_called_once_with(".", new_project=True)


def test_register_project_forwards_new_project_option(tmp_path):
    """The one-shot registration command has matching behavior."""
    with mock.patch.object(vproject, "use_project") as use_project:
        result = CliRunner().invoke(
            cli, ["register-project", str(tmp_path), "--new-project"]
        )

    assert not result.exit_code
    use_project.assert_called_once_with(str(tmp_path), new_project=True)
