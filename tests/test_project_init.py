"""Project initialization creates the complete project layout."""

from CelebiChrono.kernel import vproject


def test_init_project_creates_environment_directory(tmp_path, monkeypatch):
    """A new project is ready to hold shareable environment definitions."""
    project = tmp_path / "analysis"
    project.mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "n")
    monkeypatch.setattr(
        vproject.csys,
        "configure_project_cache_policy",
        lambda _path: {"method": "mtime", "mode": "auto", "filesystem": "local"},
    )
    monkeypatch.setattr(
        vproject.csys, "local_config_path", lambda: str(tmp_path / "user.json")
    )

    vproject.init_project(project_uuid="project-uuid")

    assert (project / ".celebi-env").is_dir()
