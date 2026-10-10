"""The interactive shell exposes one consistent command help system."""

from unittest import mock

from CelebiChrono.interface.ChernShell import ChernShell
from CelebiChrono.celebi_cli.cli import COMMAND_SECTIONS
from CelebiChrono.interface.chern_shell.help_text import (
    SHELL_COMPATIBILITY_ALIASES,
    command_help,
)


def _run_help(shell, line, capsys):
    shell.onecmd(line)
    return capsys.readouterr().out.strip()


def test_three_command_help_spellings_are_equivalent(capsys):
    """help, helpme, and --help render the same command documentation."""
    shell = ChernShell()

    standard = _run_help(shell, "help status", capsys)
    contextual = _run_help(shell, "helpme status", capsys)
    inline = _run_help(shell, "status --help", capsys)

    assert standard == contextual == inline
    assert standard.startswith("Usage: status [OPTIONS]")
    assert "--poll-interval" in standard


def test_inline_help_does_not_execute_the_command(capsys):
    """COMMAND --help is intercepted before its operation is called."""
    shell = ChernShell()
    with mock.patch(
            "CelebiChrono.interface.chern_shell.commands_basic.shell.status") as status:
        output = _run_help(shell, "status --help", capsys)

    assert "Usage: status" in output
    status.assert_not_called()


def test_helpme_without_command_is_object_aware(capsys):
    """Bare helpme explains the current object and suggests its workflow."""
    shell = ChernShell()
    current = mock.Mock()
    current.object_type.return_value = "task"
    with mock.patch(
            "CelebiChrono.interface.chern_shell.commands_documentation."
            "MANAGER.current_object",
            return_value=current):
        output = _run_help(shell, "helpme", capsys)

    assert "Celebi help for task" in output
    assert "add-algorithm" in output
    assert "submit" in output
    assert "help COMMAND" in output


def test_bare_help_is_categorized(capsys):
    """Bare help is a categorized command index, not one long flat list."""
    output = _run_help(ChernShell(), "help", capsys)

    assert "Celebi interactive shell commands" in output
    assert "Configure tasks and algorithms:" in output
    assert "Run workflows:" in output
    assert "Shell utilities:" in output
    assert "Compatibility aliases:" in output
    assert "viewbkk" in output
    assert "open-bookkeeping" in output
    assert "Other commands:" not in output


def test_every_shell_command_is_categorized_once():
    """Interactive-only commands belong to the same task-oriented taxonomy."""
    shell = ChernShell()
    commands = {
        name[3:].replace("_", "-")
        for name in shell.get_names()
        if name.startswith("do_") and name != "do_EOF"
    }
    categorized = [name for _, names in COMMAND_SECTIONS for name in names]

    assert len(categorized) == len(set(categorized))
    assert commands <= set(categorized)


def test_every_implemented_shell_command_is_documented():
    """Hidden spellings must be documented aliases rather than silent omissions."""
    shell = ChernShell()
    implemented = {
        name[3:].replace("_", "-")
        for name in dir(shell)
        if name.startswith("do_") and name != "do_EOF"
    }
    categorized = {name for _, names in COMMAND_SECTIONS for name in names}

    assert implemented <= categorized | set(SHELL_COMPATIBILITY_ALIASES)
    assert shell.hidden_command_aliases == set(SHELL_COMPATIBILITY_ALIASES)


def test_every_visible_shell_command_has_help():
    """Every command advertised by the shell has a description and usage."""
    shell = ChernShell()
    commands = {
        name[3:].replace("_", "-")
        for name in shell.get_names()
        if name.startswith("do_") and name != "do_EOF"
    }

    for name in commands:
        text = command_help(shell, name)
        assert not text.startswith("Unknown command:"), name
        assert "Usage:" in text, name
        assert len(text.splitlines()) >= 3, name
