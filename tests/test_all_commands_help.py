"""
Integration test to verify all celebi-cli commands are properly registered.
This test checks that the help system works for all commands without
requiring a Celebi project environment.
"""
import pytest
from click.testing import CliRunner
from CelebiChrono.celebi_cli.cli import cli

# List of all commands from celebi-cli --help output
ALL_COMMANDS = [
    'add-algorithm',
    'add-host',
    'add-input',
    'add-parameter',
    'add-parameter-subtask',
    'cd',
    'cdproject',
    'changes',
    'collect',
    'config',
    'cp',
    'create-algorithm',
    'create-data',
    'create-task',
    'danger',
    'edit',
    'error-log',
    'history',
    'hosts',
    'import',
    'impress',
    'jobs',
    'ls',
    'mkdir',
    'mv',
    'mvfile',
    'navigate',
    'postshell',
    'preshell',
    'register-runner',
    'remove-input',
    'remove-runner',
    'rm',
    'rm-parameter',
    'rmfile',
    'runners',
    'send',
    'set-env',
    'set-mem',
    'short-ls',
    'status',
    'submit',
    'trace',
    'tree',
    'view',
    'viewurl',
]

@pytest.mark.parametrize("command", ALL_COMMANDS)
def test_command_help(command):
    """Test that each command's --help option works."""
    runner = CliRunner()
    result = runner.invoke(cli, [command, '--help'])

    # Command should either show help or give a reasonable error
    # (not crash with ImportError or similar)
    assert result.exit_code in [0, 1], f"Command {command} failed with exit code {result.exit_code}"

    # If exit code is 0, help should be displayed
    if result.exit_code == 0:
        assert 'Usage:' in result.output or 'Options:' in result.output, \
            f"Command {command} didn't show help text"

    # If exit code is 1, it should be a reasonable error (not ImportError)
    if result.exit_code == 1:
        # Check it's not an ImportError or similar fatal error
        assert 'ImportError' not in result.output, \
            f"Command {command} has ImportError: {result.output}"
        assert 'ModuleNotFoundError' not in result.output, \
            f"Command {command} has ModuleNotFoundError: {result.output}"

def test_main_help():
    """Test that the main celebi-cli --help shows all commands."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])

    assert result.exit_code == 0, "Main help failed"
    assert 'Usage:' in result.output, "Main help doesn't show usage"
    assert 'Commands:' in result.output, "Main help doesn't show commands list"

    # Check that all expected commands are in the help output
    help_text = result.output.lower()
    for command in ALL_COMMANDS:
        # Some commands might have hyphens converted to spaces in help
        command_in_help = command.replace('-', ' ')
        assert command_in_help in help_text or command in help_text, \
            f"Command {command} not found in main help"

def test_command_count():
    """Verify we have the expected number of commands."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])

    # Count commands in help output (lines starting with 2 spaces)
    command_lines = [line.strip() for line in result.output.split('\n')
                     if line.startswith('  ') and line.strip()
                     and not line.startswith('  --')]

    print(f"Found {len(command_lines)} commands in help output")
    print(f"Expected at least 37 commands (found {len(ALL_COMMANDS)})")

    assert len(command_lines) >= 37, f"Expected at least 37 commands, found {len(command_lines)}"
    assert len(ALL_COMMANDS) >= 37, f"Expected at least 37 commands in ALL_COMMANDS list, found {len(ALL_COMMANDS)}"