"""Shared help rendering for the interactive Celebi shell."""

import inspect
from typing import Optional

import click


OBJECT_GUIDES = {
    "project": (
        "A project is the root of a Celebi analysis. Create objects, inspect the "
        "dependency tree, or submit the tasks below it.",
        (
            "ls", "tree", "status", "create-task", "create-algorithm",
            "create-data", "mkdir", "submit", "bookkeep", "doctor",
        ),
    ),
    "directory": (
        "A directory groups related Celebi objects. Use it for navigation and "
        "bulk operations on its tasks.",
        (
            "ls", "tree", "status", "create-task", "create-algorithm",
            "mkdir", "submit", "collect", "predecessors", "successors",
        ),
    ),
    "task": (
        "A task is an executable analysis instance. Link its algorithm and "
        "inputs, configure parameters, then submit and collect results.",
        (
            "status", "add-algorithm", "add-input", "set-parameter",
            "set-environment", "set-memory-limit", "submit", "log",
            "collect", "impress", "view", "trace",
        ),
    ),
    "algorithm": (
        "An algorithm contains reusable computation logic. Configure its "
        "environment and files without embedding workflow-specific inputs.",
        (
            "ls", "status", "import", "edit-script", "set-environment",
            "set-memory-limit", "set-descriptor", "impress", "history",
            "changes",
        ),
    ),
}


# Interactive-only commands and commands whose shell syntax differs from the
# one-shot CLI need an explicit usage line. Shared commands otherwise reuse
# Click's argument and option documentation.
SHELL_USAGE = {
    "add-multi-inputs": "add-multi-inputs PATH_BASE ALIAS [START] STOP",
    "auto-download": "auto-download {on|off}",
    "cache-on-runner": "cache-on-runner {on|off}",
    "cat": "cat FILE",
    "cd": "cd PATH|INDEX",
    "cd-project": "cd-project PROJECT",
    "check-results": "check-results [RUNNER]",
    "comment": "comment TEXT",
    "create-multi-data": "create-multi-data BASE COUNT",
    "create-multi-tasks": "create-multi-tasks BASE COUNT",
    "danger-call": "danger-call COMMAND",
    "display": "display FILE",
    "draw-dag-graphviz": "draw-dag-graphviz [OUTPUT]",
    "edit-readme": "edit-readme",
    "edit-script": "edit-script FILE",
    "export": "export GLOB",
    "help": "help [COMMAND]",
    "helpme": "helpme [COMMAND]",
    "homekeep": "homekeep",
    "import-file": "import-file PATH",
    "impress": "impress [OBJECT ...]",
    "impression": "impression",
    "install-environment": "install-environment RUNNER NAME [--file YAML]",
    "input": "input PATH ALIAS",
    "ls-projects": "ls-projects",
    "project-path": "project-path",
    "purge-impressions": "purge-impressions",
    "register-runner": "register-runner",
    "remove-multi-inputs": "remove-multi-inputs ALIAS [START] STOP",
    "submit": "submit [OBJECT ...] [--runner RUNNER] [--timeout SECONDS]",
    "system-shell": "system-shell",
    "view": "view [IMPRESSION]",
    "workaround": "workaround [docker] [--reference PATH] [--skip-input PATH]",
}


SHELL_COMPATIBILITY_ALIASES = {
    "add-parameter": "set-parameter",
    "bkkurl": "bookkeeping-url",
    "kill": "cancel",
    "kill-running-workflows": "stop-orphaned-workflows",
    "kill-workflow": "stop-workflow",
    "mv-file": "move-file",
    "navigate": "project-path",
    "rm-file": "remove-file",
    "runner-envs": "runner-environments",
    "setdescriptor": "set-descriptor",
    "setenv": "set-environment",
    "viewbkk": "open-bookkeeping",
    "viewurl": "view-url",
}


def _normalise_command(command: str) -> str:
    return command.strip().split()[0].replace("_", "-") if command.strip() else ""


def _method(shell, command: str):
    return getattr(shell, "do_" + command.replace("-", "_"), None)


def _click_help(command: str) -> Optional[str]:
    """Return Click help for a flat celebi-cli command, if it exists."""
    from ...celebi_cli.cli import cli

    parent = click.Context(cli, info_name="celebi-cli")
    click_command = cli.get_command(parent, command)
    if click_command is None:
        return None
    context = click.Context(click_command, info_name=command, parent=parent)
    text = click_command.get_help(context)
    return text.replace(f"Usage: celebi-cli {command}", f"Usage: {command}", 1)


def command_help(shell, command: str) -> str:
    """Render complete help for one interactive-shell command."""
    command = _normalise_command(command)
    method = _method(shell, command)
    if not command or method is None:
        return f"Unknown command: {command or '<empty>'}\nType `help` to list commands."

    doc = inspect.getdoc(method) or "No description is available."
    doc_lines = doc.splitlines()
    usage = SHELL_USAGE.get(command)

    # Multi-line shell documentation describes shell-specific parsing more
    # accurately than the Click wrapper, so retain it verbatim.
    if len(doc_lines) > 1:
        if any(line.strip().lower().startswith("usage:") for line in doc_lines):
            return doc
        return f"Usage: {usage or command + ' [ARGS]'}\n\n{doc}"

    click_help = _click_help(command)
    if click_help is not None and command not in SHELL_USAGE:
        return click_help

    return f"Usage: {usage or command}\n\n{doc}"


def command_index(shell) -> str:
    """Render categorized help for all visible shell commands."""
    from ...celebi_cli.cli import COMMAND_SECTIONS

    available = {
        name[3:].replace("_", "-")
        for name in shell.get_names()
        if name.startswith("do_") and name not in {"do_EOF"}
    }
    lines = [
        "Celebi interactive shell commands",
        "Use `help COMMAND`, `helpme COMMAND`, or `COMMAND --help` for details.",
    ]
    shown = set()
    for heading, commands in COMMAND_SECTIONS:
        members = [name for name in commands if name in available and name not in shown]
        if not members:
            continue
        lines.extend(("", f"{heading}:"))
        for name in members:
            doc = inspect.getdoc(_method(shell, name)) or ""
            summary = doc.splitlines()[0] if doc else ""
            lines.append(f"  {name:<26} {summary}")
            shown.add(name)

    uncategorized = sorted(available - shown)
    if uncategorized:
        lines.extend(("", "Other commands:"))
        for name in uncategorized:
            doc = inspect.getdoc(_method(shell, name)) or ""
            summary = doc.splitlines()[0] if doc else ""
            lines.append(f"  {name:<26} {summary}")

    aliases = [
        (alias, replacement)
        for alias, replacement in SHELL_COMPATIBILITY_ALIASES.items()
        if _method(shell, alias) is not None
    ]
    if aliases:
        lines.extend(("", "Compatibility aliases:"))
        for alias, replacement in aliases:
            lines.append(f"  {alias:<26} use {replacement}")

    return "\n".join(lines)


def object_help(object_type: str) -> str:
    """Render an object-aware starting point for `helpme`."""
    description, commands = OBJECT_GUIDES.get(
        object_type,
        (
            "Celebi manages projects, directories, algorithms, tasks, and data.",
            ("ls", "tree", "status", "help"),
        ),
    )
    lines = [
        f"Celebi help for {object_type or 'current context'}",
        "",
        description,
        "",
        "Recommended commands:",
    ]
    lines.extend(f"  {command}" for command in commands)
    lines.extend((
        "",
        "Use `help` to list every shell command.",
        "Use `help COMMAND`, `helpme COMMAND`, or `COMMAND --help` for details.",
    ))
    return "\n".join(lines)
