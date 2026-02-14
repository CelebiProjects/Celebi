import pytest
from click.testing import CliRunner
from CelebiChrono.celebi_cli.cli import cli

def test_cd_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['cd', 'test_path'])
    assert result.exit_code == 0

def test_tree_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['tree'])
    assert result.exit_code == 0

def test_status_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['status'])
    assert result.exit_code == 0

def test_navigate_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['navigate'])
    assert result.exit_code == 0

def test_cdproject_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['cdproject', 'test_project'])
    assert result.exit_code == 0

def test_short_ls_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['short-ls'])
    assert result.exit_code == 0

def test_jobs_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['jobs'])
    assert result.exit_code == 0