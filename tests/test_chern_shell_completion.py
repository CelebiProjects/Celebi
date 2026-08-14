"""Test chern shell completion."""
import readline
from pathlib import Path
from unittest.mock import patch

from CelebiChrono.interface.chern_shell.base import ChernShellBase
from CelebiChrono.utils import csys


class _FakeCurrentObject:  # pylint: disable=too-few-public-methods
    """Fake Current Object."""
    def __init__(self, path: str):
        """Init."""
        self.path = path


class _FakeManager:  # pylint: disable=too-few-public-methods
    """Fake Manager."""
    def __init__(self, current_path: str):
        """Init."""
        self.c = _FakeCurrentObject(current_path)

    def get_current_project(self) -> str:
        """Get current project."""
        return "demo-project"


def _make_project_tree(tmp_path: Path) -> tuple[Path, Path]:
    """Make project tree."""
    project_root = tmp_path / "demo-project"
    (project_root / ".celebi").mkdir(parents=True)
    (project_root / ".celebi" / "project.json").write_text("{}", encoding="utf-8")
    (project_root / ".hidden").mkdir()
    (project_root / "alpha").mkdir()
    (project_root / "alpha" / ".hidden").mkdir()
    (project_root / "alpha" / "beta.txt").write_text("x", encoding="utf-8")
    current_path = project_root / "alpha"
    return project_root, current_path


def test_preloop_keeps_project_root_marker_inside_paths(tmp_path):
    """Test preloop keeps project root marker inside paths."""
    original_delims = readline.get_completer_delims()
    project_root, current_path = _make_project_tree(tmp_path)
    shell = ChernShellBase()

    try:
        with patch("CelebiChrono.interface.ChernManager.get_manager",
                   return_value=_FakeManager(str(current_path))):
            shell.preloop()
            assert "@" not in readline.get_completer_delims()
            assert csys.project_path(str(current_path)) == str(project_root)
    finally:
        readline.set_completer_delims(original_delims)


def test_get_completions_preserves_project_relative_prefix(tmp_path):
    """Test get completions preserves project relative prefix."""
    _, current_path = _make_project_tree(tmp_path)
    shell = ChernShellBase()

    matches = shell.get_completions(
        current_path=str(current_path),
        filepath="@/al",
        _line="cd @/al",
    )

    assert matches == ["@/alpha/"]


def test_get_completions_hides_dotfolders_by_default(tmp_path):
    """Test get completions hides dotfolders by default."""
    _, current_path = _make_project_tree(tmp_path)
    shell = ChernShellBase()

    matches = shell.get_completions(
        current_path=str(current_path),
        filepath="@/",
        _line="cd @/",
    )

    assert ".hidden/" not in matches
    assert "@/alpha/" in matches


def test_get_completions_shows_dotfolders_when_typed_explicitly(tmp_path):
    """Test get completions shows dotfolders when typed explicitly."""
    _, current_path = _make_project_tree(tmp_path)
    shell = ChernShellBase()

    matches = shell.get_completions(
        current_path=str(current_path),
        filepath="@/.h",
        _line="cd @/.h",
    )

    assert matches == ["@/.hidden/"]


def test_get_completions_shows_dotfolders_for_current_dir_prefix(tmp_path):
    """Test get completions shows dotfolders for current dir prefix."""
    _, current_path = _make_project_tree(tmp_path)
    shell = ChernShellBase()

    matches = shell.get_completions(
        current_path=str(current_path),
        filepath="./",
        _line="add-input ./",
    )

    assert "./.hidden/" in matches
    assert "./beta.txt" in matches


def test_get_completions_bare_dot_shows_hidden_entries(tmp_path):
    """Test get completions bare dot shows hidden entries."""
    _, current_path = _make_project_tree(tmp_path)
    shell = ChernShellBase()

    matches = shell.get_completions(
        current_path=str(current_path),
        filepath=".",
        _line="add-input .",
    )

    assert ".hidden/" in matches
    assert "./" not in matches
