"""CLI utilities registration tests."""

from CelebiChrono.celebi_cli.cli import cli


def test_migrate_impressions_command_registered():
    """Test migrate impressions command registered."""
    assert "migrate-impressions" in cli.commands


def test_stats_impressions_command_registered():
    """Test stats impressions command registered."""
    assert "stats-impressions" in cli.commands
