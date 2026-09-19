"""Exercise generated Git hooks through their shell entry point."""

import os
import subprocess
import sys

import pytest

from CelebiChrono.utils.git_optional import GitOptionalIntegration


@pytest.mark.parametrize("outcome", ["issues", "error", "no_config"])
def test_post_merge_hook(tmp_path, outcome):
    project = tmp_path / "project"
    (project / ".git" / "hooks").mkdir(parents=True)
    integration = GitOptionalIntegration(str(project))
    assert integration.install_hooks()

    # Supply a coordinator double so validation cannot modify real project data.
    packages = tmp_path / "packages"
    utils = packages / "CelebiChrono" / "utils"
    utils.mkdir(parents=True)
    (utils.parent / "__init__.py").touch()
    (utils / "__init__.py").touch()
    (utils / "git_merge_coordinator.py").write_text(
        "class GitMergeCoordinator:\n"
        "    def validate_post_merge(self):\n"
        + (
            "        raise RuntimeError('validation failed')\n"
            if outcome == "error"
            else "        return {'success': False, 'issues': ['test issue'], "
            "'repairs': ['test repair']}\n"
        ),
        encoding="utf-8",
    )
    if outcome == "no_config":
        (project / ".celebi" / "git_config.json").unlink()

    # Ensure the hook uses the same interpreter as pytest.
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "python").symlink_to(sys.executable)
    env = dict(os.environ, PYTHONPATH=str(packages))
    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    result = subprocess.run(
        [str(project / ".git" / "hooks" / "post-merge")],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    if outcome == "issues":
        assert "Celebi post-merge validation found issues:" in result.stdout
        assert "  - test issue" in result.stdout
        assert "Automatic repairs performed:\n  - test repair" in result.stdout
    elif outcome == "error":
        assert "Celebi post-merge hook error: validation failed" in result.stdout
    else:
        assert result.stdout == ""
