"""Git integration creates a default ignore file only when needed."""

import subprocess

from click.testing import CliRunner

from CelebiChrono import main
from CelebiChrono.utils.git_optional import GitOptionalIntegration


EXPECTED_CELEBI_IGNORES = {
    "**/.celebi/config.local.json",
    "**/.celebi/hosts.json",
    "**/.celebi/bookkeeping.local.json",
    ".celebi-env/config.local.json",
    ".celebi-env/hosts.json",
    ".celebi-env/bookkeeping.local.json",
    ".celebi/git_config.json",
    "**/.celebi/impressions",
    "**/.celebi/impressions_store",
    "**/.celebi/cache",
    "**/.celebi/immutable-impress*",
    ".celebi-workspace",
    ".celebi-workaround",
    "stageout",
    ".env",
    ".env.*",
    ".DS_Store",
    "*.pyc",
    "__pycache__/",
}


def test_create_gitignore_when_missing(tmp_path):
    """Recommended rules are written with a trailing newline."""
    integration = GitOptionalIntegration(str(tmp_path))

    assert integration.create_gitignore_if_missing()

    additions = integration.get_recommended_settings()['.gitignore_additions']
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == (
        "\n".join(additions) + "\n"
    )
    assert EXPECTED_CELEBI_IGNORES <= set(additions)
    assert ".celebi-env" not in additions


def test_existing_gitignore_is_not_modified(tmp_path):
    """User-maintained ignore rules remain byte-for-byte unchanged."""
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("custom-rule\n", encoding="utf-8")
    integration = GitOptionalIntegration(str(tmp_path))

    assert not integration.create_gitignore_if_missing()
    assert gitignore.read_text(encoding="utf-8") == "custom-rule\n"


def test_generated_rules_ignore_runtime_state_but_keep_shared_files(tmp_path):
    """The template covers runtime paths without hiding project definitions."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    GitOptionalIntegration(str(tmp_path)).create_gitignore_if_missing()

    ignored = (
        "task/.celebi/config.local.json",
        ".celebi/hosts.json",
        ".celebi/bookkeeping.local.json",
        ".celebi-env/config.local.json",
        ".celebi-env/hosts.json",
        ".celebi-env/bookkeeping.local.json",
        ".celebi/git_config.json",
        ".celebi/impressions",
        ".celebi/impressions_store",
        ".celebi/cache",
        ".celebi/immutable-impress.json",
        ".celebi-workspace/result",
        ".celebi-workaround/result",
        "task/stageout/result.root",
        ".env.local",
        ".DS_Store",
        "task/__pycache__/module.pyc",
    )
    for path in ignored:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "--quiet", path],
            cwd=tmp_path,
            check=False,
        )
        assert not result.returncode, path

    shared = (".celebi/config.json", ".celebi/project.json", ".celebi-env/analysis.yaml")
    for path in shared:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "--quiet", path],
            cwd=tmp_path,
            check=False,
        )
        assert result.returncode == 1, path


def test_celebi_git_enable_creates_missing_gitignore(tmp_path, monkeypatch):
    """The public command creates the file instead of only recommending it."""
    (tmp_path / ".git").mkdir()
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(main.git_cli, ["enable"], input="n\n")

    assert not result.exit_code
    assert (tmp_path / ".gitignore").is_file()
    assert "Created .gitignore" in result.output
