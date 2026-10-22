"""Public entry-point roles, categorized help, and compatibility names."""

from pathlib import Path
import re
from unittest import mock

from click.testing import CliRunner

from CelebiChrono import main
from CelebiChrono.celebi_cli.cli import COMMAND_SECTIONS, HELP_HIDDEN_COMMANDS, cli
from CelebiChrono.interface.ChernShell import ChernShell


def test_celebi_help_presents_the_interactive_shell_only():
    """Legacy launcher subcommands stay callable but out of normal help."""
    result = CliRunner().invoke(main.cli, ["--help"])

    assert result.exit_code == 0
    assert "Start the interactive Celebi shell" in result.output
    assert "--project" in result.output
    assert "attach-data" not in result.output
    assert "book-reana" not in result.output


def test_celebi_cli_help_is_categorized_without_nested_commands():
    """Categories improve discovery while command invocation remains flat."""
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    for heading in (
            "Projects:", "Browse and inspect:", "Create objects:",
            "Configure tasks and algorithms:", "Files and content:",
            "Run workflows:", "Results and logs:", "Data and transfer:",
            "Impressions and provenance:", "Runners and capacity:",
            "Settings and services:", "Maintenance and recovery:",
            "Advanced and developer:", "Compatibility aliases:"):
        assert heading in result.output
    assert "submit" in result.output
    assert "set-environment" in result.output
    for name in HELP_HIDDEN_COMMANDS:
        assert any(
            line.strip().startswith(f"{name} ")
            for line in result.output.splitlines()
        ), name


def test_every_public_cli_command_is_categorized_once():
    """The help taxonomy is complete and has no ambiguous duplicate entries."""
    categorized = [name for _, commands in COMMAND_SECTIONS for name in commands]
    public = {
        name for name, command in cli.commands.items()
        if not command.hidden and name not in HELP_HIDDEN_COMMANDS
    }

    assert len(categorized) == len(set(categorized))
    assert public <= set(categorized)


def test_every_public_cli_command_is_named_in_command_docs():
    """The Read the Docs command reference cannot silently miss a new command."""
    docs_dir = Path(__file__).parents[1] / "docs"
    sources = [
        docs_dir / "commands.rst",
        *sorted((docs_dir / "commands").glob("*.rst")),
    ]
    documentation = "\n".join(path.read_text(encoding="utf-8") for path in sources)
    public = {
        name for name, command in cli.commands.items()
        if not command.hidden and name not in HELP_HIDDEN_COMMANDS
    }

    missing = {
        name for name in public
        if re.search(rf"``{re.escape(name)}(?:``|[ \[])", documentation) is None
    }

    assert not missing, f"Commands missing from docs/commands: {sorted(missing)}"


def test_shell_only_commands_are_session_features_or_named_equivalents():
    """A new shell operation cannot silently omit its one-shot CLI command."""
    shell_commands = {
        name[3:].replace("_", "-")
        for name in ChernShell().get_names()
        if name.startswith("do_") and name != "do_EOF"
    }
    cli_commands = set(cli.commands) - HELP_HIDDEN_COMMANDS
    expected_shell_only = {
        # Commands whose effect requires the persistent interactive session.
        "cd", "cd-project", "help", "helpme", "system-shell",
        # Shell spellings with a public one-shot equivalent.
        "danger-call", "draw-dag-graphviz", "edit-script", "import-file",
        "input", "ls-projects", "workaround",
        # Unsafe legacy cleanup retained only for interactive developers.
        "clean-impressions",
    }

    assert shell_commands - cli_commands == expected_shell_only


def test_legacy_cli_names_still_resolve():
    """Renaming commands does not immediately break existing scripts."""
    runner = CliRunner()
    for name in (
            "add-parameter", "kill", "kill-running-workflows",
            "rm-parameter", "set-env", "set-mem", "stats-impressions",
            "viewurl"):
        result = runner.invoke(cli, [name, "--help"])
        assert result.exit_code == 0, name


def test_every_advertised_cli_command_has_help():
    """Every categorized command renders usage and descriptive text."""
    runner = CliRunner()
    names = {name for _, commands in COMMAND_SECTIONS for name in commands}
    for name in names:
        if name not in cli.commands:
            continue
        result = runner.invoke(cli, [name, "--help"])
        assert result.exit_code == 0, name
        assert f"Usage: cli {name}" in result.output, name
        assert len(result.output.splitlines()) >= 5, name


def test_cli_help_reuses_detailed_operation_documentation():
    """Thin Click wrappers expose examples and constraints from operations."""
    result = CliRunner().invoke(cli, ["add-input", "--help"])

    assert result.exit_code == 0
    assert "Examples:" in result.output
    assert "Notes:" in result.output
    assert "Aliases must be unique" in result.output
    assert "Args:" not in result.output
    assert "Returns:" not in result.output


def test_project_selection_command_updates_registry(tmp_path, monkeypatch):
    """Project selection moved from the shell launcher to celebi-cli."""
    monkeypatch.setattr(
        "CelebiChrono.celebi_cli.commands.project_management.csys.local_config_path",
        lambda: str(tmp_path / "config.json"),
    )
    config = main.metadata.ConfigFile(str(tmp_path / "config.json"))
    config.write_variable("projects_path", {"analysis": "/work/analysis"})

    result = CliRunner().invoke(cli, ["use-project", "analysis"])

    assert result.exit_code == 0
    assert config.read_variable("current_project") == "analysis"


def test_canonical_cancel_uses_existing_implementation():
    """The clearer cancel spelling delegates to the established operation."""
    with mock.patch("CelebiChrono.interface.shell.kill") as cancel:
        result = CliRunner().invoke(cli, ["cancel"])

    assert result.exit_code == 0
    cancel.assert_called_once_with()


def test_add_multi_inputs_uses_half_open_numbered_range():
    """The one-shot CLI exposes the shell's numbered input operation."""
    with mock.patch("CelebiChrono.interface.shell.add_input") as add_input:
        result = CliRunner().invoke(
            cli,
            ["add-multi-inputs", "../task", "input", "5", "--start", "2"],
        )

    assert result.exit_code == 0
    assert add_input.call_args_list == [
        mock.call("../task_2", "input_2"),
        mock.call("../task_3", "input_3"),
        mock.call("../task_4", "input_4"),
    ]


def test_remove_multi_inputs_rejects_an_empty_range():
    """Bulk input commands reject reversed or empty ranges before mutation."""
    with mock.patch("CelebiChrono.interface.shell.remove_input") as remove_input:
        result = CliRunner().invoke(
            cli,
            ["remove-multi-inputs", "input", "3", "--start", "3"],
        )

    assert result.exit_code == 2
    assert "STOP must be greater than START" in result.output
    remove_input.assert_not_called()


def test_create_multi_tasks_sets_each_index_parameter():
    """Bulk task creation configures an index on every created task."""
    successful = mock.Mock(success=True, messages=[])
    with mock.patch(
            "CelebiChrono.interface.shell.mktask",
            return_value=successful) as create, mock.patch(
                "CelebiChrono.interface.shell.add_parameter_subtask",
                return_value=successful) as set_parameter:
        result = CliRunner().invoke(
            cli,
            ["create-multi-tasks", "simulation", "4", "--start", "2"],
        )

    assert result.exit_code == 0
    assert create.call_args_list == [
        mock.call("simulation_2"), mock.call("simulation_3")
    ]
    assert set_parameter.call_args_list == [
        mock.call("simulation_2", "index", "2"),
        mock.call("simulation_3", "index", "3"),
    ]
