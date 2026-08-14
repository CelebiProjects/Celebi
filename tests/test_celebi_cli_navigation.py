"""Test celebi cli navigation."""
from click.testing import CliRunner
from CelebiChrono.celebi_cli.cli import cli

def test_cd_command():
    """Test cd command."""
    runner = CliRunner()
    result = runner.invoke(cli, ['cd', 'test_path'])
    assert not result.exit_code

def test_tree_command():
    """Test tree command."""
    runner = CliRunner()
    result = runner.invoke(cli, ['tree'])
    assert not result.exit_code

def test_status_command():
    """Test status command."""
    runner = CliRunner()
    result = runner.invoke(cli, ['status'])
    assert not result.exit_code

def test_navigate_command():
    """Test navigate command."""
    runner = CliRunner()
    result = runner.invoke(cli, ['navigate'])
    assert not result.exit_code

def test_cdproject_command():
    """Test cdproject command."""
    runner = CliRunner()
    result = runner.invoke(cli, ['cdproject', 'test_project'])
    assert not result.exit_code

def test_short_ls_command():
    """Test short ls command."""
    runner = CliRunner()
    result = runner.invoke(cli, ['short-ls'])
    assert not result.exit_code

def test_jobs_command():
    """Test jobs command."""
    runner = CliRunner()
    result = runner.invoke(cli, ['jobs'])
    assert not result.exit_code

def test_set_descriptor_command():
    """Test set descriptor command."""
    assert 'set-descriptor' in cli.commands
