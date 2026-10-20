"""Interactive maintenance and cleanup commands."""

from typing import Any

import click

from .execution_management import _handle_result


def _runner_records(result: Any) -> list[dict[str, str]]:
    """Return normalized runner records from the shell runners result."""
    data = getattr(result, "data", {}) or {}
    records = data.get("runners", [])
    normalized = []
    for record in records:
        if isinstance(record, str):
            normalized.append({"name": record, "backend_type": ""})
        elif isinstance(record, dict) and record.get("name"):
            normalized.append({
                "name": str(record["name"]),
                "backend_type": str(record.get("backend_type", "")),
            })
    return normalized


def _select_runners(records: list[dict[str, str]]) -> list[dict[str, str]]:
    """Prompt for a comma-separated runner selection."""
    click.echo("\nAvailable runners:")
    for index, record in enumerate(records, 1):
        backend = record.get("backend_type") or "unknown"
        cache_note = "" if backend in ("ssh", "ihep") else " (no SSH cache)"
        click.echo(f"  {index}. {record['name']} [{backend}]{cache_note}")

    by_name = {record["name"]: record for record in records}
    while True:
        answer = click.prompt(
            "Runners to clean (numbers/names separated by commas, 'all', Enter to skip)",
            default="",
            show_default=False,
        ).strip()
        if not answer:
            return []
        if answer.lower() == "all":
            return records

        selected = []
        invalid = []
        for token in (item.strip() for item in answer.split(",")):
            if not token:
                continue
            if token.isdigit() and 1 <= int(token) <= len(records):
                record = records[int(token) - 1]
            elif token in by_name:
                record = by_name[token]
            else:
                invalid.append(token)
                continue
            if record not in selected:
                selected.append(record)
        if not invalid:
            return selected
        click.echo(f"Unknown runner selection: {', '.join(invalid)}", err=True)


def _cleanup_local(shell: Any, grace_days: int) -> bool:
    """Preview and optionally execute local CAS garbage collection."""
    click.echo("\nLocal impression storage")
    preview = shell.gc_impressions(grace_days=grace_days, dry_run=True)
    _handle_result(preview)
    count = int(getattr(preview, "data", {}).get("unreachable_objects", 0))
    if not count:
        click.echo("No unreachable local CAS objects found.")
        return False
    if not click.confirm(
            f"Delete eligible objects among these {count} unreachable objects?",
            default=False):
        click.echo("Local cleanup skipped.")
        return False
    _handle_result(shell.gc_impressions(grace_days=grace_days, dry_run=False))
    return True


def _cleanup_runner_workflows(shell: Any, runner: str) -> bool:
    """Preview and optionally purge one runner's stale workspaces."""
    click.echo(f"\nRunner '{runner}': workflow workspaces")
    preview = shell.purge_stale_workflows(runner, dry_run=True)
    _handle_result(preview)
    count = int(getattr(preview, "data", {}).get("purge_count", 0))
    if not count:
        click.echo("No stale workflow workspaces are eligible.")
        return False
    if not click.confirm(
            f"Delete {count} stale workflow workspace(s) from '{runner}'?",
            default=False):
        click.echo("Workflow cleanup skipped.")
        return False
    _handle_result(shell.purge_stale_workflows(runner, dry_run=False))
    return True


def _cleanup_runner_cache(shell: Any, record: dict[str, str]) -> bool:
    """Preview and optionally purge one SSH runner's stale cache."""
    runner = record["name"]
    backend = record.get("backend_type", "")
    click.echo(f"\nRunner '{runner}': impression cache")
    if backend not in ("ssh", "ihep"):
        click.echo(f"Skipped: backend '{backend or 'unknown'}' has no SSH impression cache.")
        return False

    preview = shell.purge_stale_cache(runner, dry_run=True)
    _handle_result(preview)
    count = int(getattr(preview, "data", {}).get("purge_count", 0))
    if not count:
        click.echo("No superseded impression cache entries are eligible.")
        return False
    if not click.confirm(
            f"Delete {count} stale impression cache entr"
            f"{'y' if count == 1 else 'ies'} from '{runner}'?",
            default=False):
        click.echo("Cache cleanup skipped.")
        return False
    _handle_result(shell.purge_stale_cache(runner, dry_run=False))
    return True


def run_tidyup(grace_days: int = 14) -> None:
    """Run the shared tidyup questionnaire."""
    from CelebiChrono.interface import shell

    click.echo("Celebi tidyup wizard")
    click.echo("Nothing is deleted until its preview is shown and confirmed.")

    clean_local = click.confirm(
        "Inspect local unreachable impression objects?", default=True)
    clean_workflows = click.confirm(
        "Inspect stale workflow workspaces on runners?", default=True)
    clean_caches = click.confirm(
        "Inspect stale impression caches on runners?", default=True)

    completed = 0
    if clean_local and _cleanup_local(shell, grace_days):
        completed += 1

    if clean_workflows or clean_caches:
        runner_result = shell.runners()
        records = _runner_records(runner_result)
        if not records:
            _handle_result(runner_result)
            click.echo("No runners are available; runner cleanup skipped.")
        else:
            selected = _select_runners(records)
            for record in selected:
                if clean_workflows and _cleanup_runner_workflows(
                        shell, record["name"]):
                    completed += 1
                if clean_caches and _cleanup_runner_cache(shell, record):
                    completed += 1

    if completed:
        click.echo(f"\nTidyup finished: {completed} confirmed operation(s) executed.")
    else:
        click.echo("\nTidyup finished: nothing was deleted.")
