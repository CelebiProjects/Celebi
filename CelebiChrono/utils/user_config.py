"""User-level configuration stored in ``~/.celebi/config.yaml``.

This module is the single place that knows which user settings exist, what
they default to, and what they mean. Adding a new configurable is one entry
in :data:`SETTINGS` -- it then automatically appears in the generated
template, in ``user-config --list``, and is readable through :func:`get`.
"""
import os
import sys
import textwrap
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

import yaml

from . import csys
from . import metadata

_MISSING = object()

# `open` exists only on macOS; the freedesktop equivalent is xdg-open.
_DEFAULT_FILE_OPENER = "open" if sys.platform == "darwin" else "xdg-open"


@dataclass(frozen=True)
class Setting:
    """One user-configurable setting.

    Attributes:
        name: The YAML key, as written in ``~/.celebi/config.yaml``.
        default: Value used when the key is absent from the file.
        description: One-line explanation, rendered as a YAML comment.
        choices: Optional allowed values, for documentation and completion.
    """

    name: str
    default: Any
    description: str
    choices: Tuple[str, ...] = field(default_factory=tuple)


SETTINGS: Tuple[Setting, ...] = (
    Setting(
        name="editor",
        default="vi",
        description=(
            "Editor used by `config`, `edit-script` and `readme`."
        ),
    ),
    Setting(
        name="file_opener",
        default=_DEFAULT_FILE_OPENER,
        description=(
            "Program used to open a local file, e.g. by `view local:...`."
        ),
    ),
    Setting(
        name="browser",
        default="",
        description=(
            "Command used to open a URL. Leave empty to use the system "
            "default browser."
        ),
    ),
    Setting(
        name="default_runner",
        default="local",
        description=(
            "Runner assigned to newly created tasks. Existing tasks keep "
            "whatever they were created with."
        ),
    ),
    Setting(
        name="auto_download",
        default=True,
        description=(
            "Whether newly created tasks download their outputs "
            "automatically."
        ),
    ),
    Setting(
        name="cache_on_runner",
        default=False,
        description=(
            "Whether newly created tasks cache their results on the runner."
        ),
    ),
    Setting(
        name="dag_output_dir",
        default="~/Downloads",
        description=(
            "Directory where `draw-dag` writes its output."
        ),
    ),
    Setting(
        name="task_environment",
        default="reanahub/reana-env-root6:6.18.04",
        description=(
            "Environment written into a new task's celebi.yaml. Changing "
            "this changes the impression of tasks created afterwards."
        ),
    ),
    Setting(
        name="algorithm_environment",
        default="script",
        description=(
            "Environment written into a new algorithm's celebi.yaml."
        ),
    ),
)


def _setting(name: str) -> Optional[Setting]:
    """Look up a registered setting by name, or None if unregistered."""
    for setting in SETTINGS:
        if setting.name == name:
            return setting
    return None


def config_path() -> str:
    """Return the path of the user configuration file."""
    return os.path.join(csys.local_config_dir(), "config.yaml")


def get(name: str, default: Any = None) -> Any:
    """Read a user setting, falling back to its registered default.

    Args:
        name: The setting name, normally one registered in :data:`SETTINGS`.
        default: Override for the fallback. Used when the setting is not
            registered, or to force a different fallback at a call site.

    Returns:
        The configured value, or the registered default when the file has no
        such key, does not exist, or is empty or malformed.
    """
    if default is None:
        setting = _setting(name)
        if setting is not None:
            default = setting.default
    return metadata.YamlFile(config_path()).read_variable(name, default)


def get_path(name: str, default: Any = None) -> str:
    """Read a path-valued setting with ``~`` expanded.

    Args:
        name: The setting name.
        default: Override for the fallback, as in :func:`get`.

    Returns:
        The configured path with a leading ``~`` resolved to the home
        directory, ready to pass to the filesystem.
    """
    return os.path.expanduser(get(name, default))


@dataclass(frozen=True)
class SettingValue:
    """A setting resolved against the current configuration file.

    Attributes:
        name: The setting name.
        value: The value in force, whether configured or defaulted.
        is_set: True when the value came from the file rather than the default.
        description: The registry description, for display.
    """

    name: str
    value: Any
    is_set: bool
    description: str


def describe() -> List[SettingValue]:
    """Resolve every registered setting against the configuration file.

    Returns:
        One :class:`SettingValue` per entry in :data:`SETTINGS`, in registry
        order, each flagged according to whether the file supplied the value.
    """
    yaml_file = metadata.YamlFile(config_path())
    rows = []
    for setting in SETTINGS:
        value = yaml_file.read_variable(setting.name, _MISSING)
        is_set = value is not _MISSING
        rows.append(SettingValue(
            name=setting.name,
            value=value if is_set else setting.default,
            is_set=is_set,
            description=setting.description,
        ))
    return rows


def render_template() -> str:
    """Render a commented YAML scaffold documenting every setting.

    The values written are the built-in defaults, so the file is immediately
    editable rather than an empty stub.
    """
    lines = [
        "# Celebi user configuration.",
        "#",
        "# The values below are the built-in defaults. Change one to override",
        "# it, or delete its line to fall back to the default.",
        "",
    ]
    for setting in SETTINGS:
        lines.extend(textwrap.wrap(
            setting.description, width=76,
            initial_indent="# ", subsequent_indent="# ",
        ))
        if setting.choices:
            lines.extend(textwrap.wrap(
                f"Choices: {', '.join(setting.choices)}", width=76,
                initial_indent="# ", subsequent_indent="# ",
            ))
        entry = yaml.dump(
            {setting.name: setting.default}, default_flow_style=False
        )
        lines.append(entry.strip())
        lines.append("")
    return "\n".join(lines)


def ensure_exists() -> bool:
    """Create the configuration file with the scaffold if it is absent.

    An existing file is never rewritten, so hand-edited settings and comments
    always survive.

    Returns:
        True if the file was created by this call, False if it already existed.
    """
    path = config_path()
    if os.path.exists(path):
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(render_template())
    return True
