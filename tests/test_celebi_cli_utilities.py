"""CLI utilities registration tests."""

from CelebiChrono.celebi_cli.cli import cli


def test_migrate_impressions_command_registered():
    assert "migrate-impressions" in cli.commands
