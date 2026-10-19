"""Tests for the interactive cleanup wizard."""

from unittest import mock

from click.testing import CliRunner

from CelebiChrono.celebi_cli.cli import cli
from CelebiChrono.utils.message import Message


def _message(**data):
    result = Message()
    result.data.update(data)
    return result


def test_homekeep_can_skip_every_category():
    """Declining all categories never contacts cleanup services."""
    with mock.patch("CelebiChrono.interface.shell.gc_impressions") as local, \
            mock.patch("CelebiChrono.interface.shell.runners") as runners:
        result = CliRunner().invoke(cli, ["homekeep"], input="n\nn\nn\n")

    assert not result.exit_code, result.output
    assert "nothing was deleted" in result.output
    local.assert_not_called()
    runners.assert_not_called()


def test_homekeep_previews_local_gc_before_execution():
    """Local cleanup runs a dry-run before its confirmed execution."""
    preview = _message(unreachable_objects=3)
    executed = _message(unreachable_objects=3, deleted_objects=2)
    with mock.patch("CelebiChrono.interface.shell.gc_impressions",
                    side_effect=[preview, executed]) as gc:
        result = CliRunner().invoke(
            cli, ["homekeep", "--grace-days", "7"],
            input="y\nn\nn\ny\n",
        )

    assert not result.exit_code, result.output
    assert gc.call_args_list == [
        mock.call(grace_days=7, dry_run=True),
        mock.call(grace_days=7, dry_run=False),
    ]


def test_homekeep_selected_runner_previews_each_remote_category():
    """One runner can clean workflows and cache after separate previews."""
    runners = _message(runners=[{"name": "farm", "backend_type": "ssh"}])
    workflows = [_message(purge_count=2), _message(purge_count=2)]
    caches = [_message(purge_count=1), _message(purge_count=1)]
    with mock.patch("CelebiChrono.interface.shell.runners",
                    return_value=runners), \
            mock.patch("CelebiChrono.interface.shell.purge_stale_workflows",
                       side_effect=workflows) as purge_workflows, \
            mock.patch("CelebiChrono.interface.shell.purge_stale_cache",
                       side_effect=caches) as purge_cache:
        result = CliRunner().invoke(
            cli, ["homekeep"], input="n\ny\ny\n1\ny\ny\n")

    assert not result.exit_code, result.output
    assert purge_workflows.call_args_list == [
        mock.call("farm", dry_run=True),
        mock.call("farm", dry_run=False),
    ]
    assert purge_cache.call_args_list == [
        mock.call("farm", dry_run=True),
        mock.call("farm", dry_run=False),
    ]


def test_homekeep_skips_cache_for_non_ssh_runner():
    """Native runners do not receive unsupported cache purge requests."""
    runners = _message(runners=[{"name": "local", "backend_type": "native"}])
    with mock.patch("CelebiChrono.interface.shell.runners",
                    return_value=runners), \
            mock.patch("CelebiChrono.interface.shell.purge_stale_cache") as purge:
        result = CliRunner().invoke(
            cli, ["homekeep"], input="n\nn\ny\nall\n")

    assert not result.exit_code, result.output
    assert "has no SSH impression cache" in result.output
    purge.assert_not_called()


def test_interactive_shell_homekeep_uses_same_wizard():
    """The persistent shell and one-shot CLI share the homekeep flow."""
    from CelebiChrono.interface.chern_shell.commands_documentation import (
        DocumentationCommands,
    )

    commands = DocumentationCommands()
    with mock.patch(
            "CelebiChrono.celebi_cli.commands.maintenance.run_homekeep") as run:
        commands.do_homekeep("")

    run.assert_called_once_with()
