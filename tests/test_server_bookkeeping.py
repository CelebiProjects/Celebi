"""Real local Git tests for bookkeep publishing and credential exclusions."""
import subprocess
import pytest
from CelebiChrono.interface.shell_modules.server_booking import publish_git
from CelebiChrono.interface.shell_modules.server_booking import forbidden

def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True,
                          text=True).stdout.strip()

@pytest.fixture
def repository(tmp_path):
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "--bare", "-b", "main", str(remote))
    root = tmp_path / "project"
    git(tmp_path, "init", "-b", "main", str(root))
    git(root, "config", "user.email", "test@example.com")
    git(root, "config", "user.name", "Test")
    (root / "code.py").write_text("print('first')")
    git(root, "add", "code.py")
    git(root, "commit", "-m", "initial")
    git(root, "remote", "add", "origin", str(remote))
    git(root, "push", "-u", "origin", "main")
    return root, remote

def test_commit_tag_push_excludes_local_credentials(repository):
    root, remote = repository
    (root / "code.py").write_text("print('published')")
    (root / ".celebi").mkdir()
    (root / ".celebi/bookkeeping.local.json").write_text('{"token":"secret"}')
    (root / ".celebi/hosts.json").write_text('{"token":"secret"}')
    commit = publish_git(root, "publish", "v1")
    assert git(remote, "rev-parse", "main") == commit
    assert git(remote, "rev-parse", "refs/tags/v1") == commit
    assert "bookkeeping.local.json" not in git(root, "ls-tree", "-r", "--name-only", "HEAD")
    assert "hosts.json" not in git(root, "ls-tree", "-r", "--name-only", "HEAD")
    with pytest.raises(ValueError, match="Tag already exists"):
        publish_git(root, "again", "v1")

def test_tracked_secret_is_rejected_before_commit(repository):
    root, remote = repository
    (root / ".env").write_text("TOKEN=secret")
    git(root, "add", ".env")
    before = git(root, "rev-parse", "HEAD")
    with pytest.raises(ValueError, match="Remove local credentials"):
        publish_git(root, "publish", "v1")
    assert git(root, "rev-parse", "HEAD") == before

def test_remote_tag_conflict_does_not_create_commit(repository):
    root, remote = repository
    git(remote, "tag", "v1", "main")
    (root / "code.py").write_text("changed")
    before = git(root, "rev-parse", "HEAD")
    with pytest.raises(ValueError, match="Tag already exists"):
        publish_git(root, "publish", "v1")
    assert git(root, "rev-parse", "HEAD") == before


@pytest.mark.parametrize("staged", [False, True])
def test_environment_definitions_are_published_and_can_be_updated(repository, staged):
    root, remote = repository
    spec = root / ".celebi-env/analysis.yaml"
    spec.parent.mkdir()
    spec.write_text("dependencies:\n  - python=3.12\n")
    if staged:
        git(root, "add", ".celebi-env/analysis.yaml")
    commit = publish_git(root, "Publish environment")
    assert git(remote, "show", commit + ":.celebi-env/analysis.yaml") == spec.read_text().strip()
    assert publish_git(root) == commit  # Already-tracked definitions remain allowed.
    spec.write_text("dependencies:\n  - python=3.13\n")
    updated = publish_git(root, "Update environment")
    assert updated != commit
    assert "python=3.13" in git(remote, "show", "main:.celebi-env/analysis.yaml")


@pytest.mark.parametrize("path", [
    ".celebi-env/.env", ".celebi-env/.env.local",
    ".celebi-env/hosts.json", ".celebi-env/config.local.json",
    ".celebi-env/bookkeeping.local.json", ".celebi-env/stageout/result.txt",
    ".celebi-workspace/result.txt", ".celebi-workaround/result.txt",
])
def test_environment_directory_does_not_bypass_existing_exclusions(path):
    assert forbidden(path)


@pytest.mark.parametrize("path", [".celebi-env/analysis.yaml", ".celebi-env/root-dev.yml"])
def test_environment_specification_paths_are_shareable(path):
    assert not forbidden(path)
