"""Read-only project EOS inventory through a small REANA job."""
import json
import time
import uuid

import click


def format_size(value):
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB"):
        if value < 1024 or unit == "PiB":
            return f"{value:.1f} {unit}"
        value /= 1024


def display(state, as_json):
    if as_json:
        click.echo(json.dumps(state, indent=2))
        return
    click.echo(f"Scan: {state['id']}  Status: {state['status']}")
    if state.get("workflow"):
        click.echo(f"REANA workflow: {state['workflow']}")
    if state.get("error"):
        click.echo(state["error"])
    report = state.get("report")
    if not report:
        return
    click.echo(f"EOS root: {report['root']}")
    click.echo(f"Scanned: {report['finished_at']} (logical bytes, not physical disk usage)")
    click.echo("Project UUID                      Category        Size          Files  Impressions")
    for project in report["projects"]:
        for category, usage in project["usage"].items():
            click.echo(f"{project['project']}  {category:10}  "
                       f"{format_size(usage['bytes']):>12}  "
                       f"{usage['files']:7}  {usage['impressions']:11}")
        click.echo(f"  Live set: {project['live_updated_at'] or 'not synced'}"
                   f"; usable: {project['live_set_usable']}")
        if not project["complete"]:
            click.echo("  INCOMPLETE: measured sizes are lower bounds; see --json for errors.")
    unassigned = report.get("unassigned_usage", {})
    if unassigned.get("entries"):
        click.echo(f"Unassigned (unknown project): {format_size(unassigned['bytes'])}, "
                   f"{unassigned['files']} files, {unassigned['entries']} entries")
    if not report["complete"]:
        click.echo("INCOMPLETE scan: inaccessible/unattributed entries are not counted as zero.")
    click.echo(report["note"])


@click.command(name="eos-usage")
@click.argument("runner", required=False)
@click.option("--all-projects", is_flag=True, help="Scan every project under this runner's EOS root.")
@click.option("--scan-id", help="Query an existing scan; does not submit a new job.")
@click.option("--wait/--no-wait", default=True, show_default=True)
@click.option("--timeout", type=click.IntRange(min=1), default=600, show_default=True,
              help="Polling budget in seconds; expiry keeps the REANA job running.")
@click.option("--json", "as_json", is_flag=True, help="Include per-impression counts and reasons.")
def eos_usage_command(runner, all_projects, scan_id, wait, timeout, as_json):
    """Measure EOS cache usage by project via a read-only REANA job.

    Default scope is the current project; --all-projects scans the runner's
    configured EOS root. Live sets older than 24h classify as unknown.
    Non-live means explicitly superseded, not automatically safe to delete.
    """
    from CelebiChrono.kernel.chern_communicator import ChernCommunicator
    from CelebiChrono.interface.shell_modules.communication import _current_project
    communicator = ChernCommunicator.instance()
    try:
        if scan_id:
            if runner or all_projects:
                raise click.UsageError("--scan-id cannot be combined with RUNNER/--all-projects")
            state = communicator.eos_usage_status(scan_id)
        else:
            if not runner:
                raise click.UsageError("RUNNER is required to start a scan")
            project_dir, project_uuid = _current_project()
            if not project_uuid and not all_projects:
                raise click.UsageError("Run inside a project or use --all-projects")
            if project_uuid:
                from CelebiChrono.kernel.liveness import compute_live_sets
                live, superseded = compute_live_sets(project_dir)
                communicator.put_live_set(project_uuid, live, superseded)
            scan_id = uuid.uuid4().hex
            # Print before POST: even an HTTP timeout leaves a recoverable identity.
            click.echo(f"Scan ID: {scan_id}\nResume: celebi-cli eos-usage --scan-id {scan_id}",
                       err=True)
            state = communicator.start_eos_usage(
                runner, scan_id, None if all_projects else project_uuid)
        deadline = time.monotonic() + timeout
        while wait and state["status"] not in ("done", "failed", "submission_unknown"):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                click.echo(f"Still pending. Resume: celebi-cli eos-usage --scan-id {scan_id}",
                           err=True)
                break
            time.sleep(min(5, remaining))
            state = communicator.eos_usage_status(scan_id)
        display(state, as_json)
        if state["status"] in ("failed", "submission_unknown"):
            raise click.ClickException(
                "REANA scan failed or submission is uncertain; inspect the reported scan ID")
    except click.ClickException:
        raise
    except Exception as exc:
        suffix = f"; resume with --scan-id {scan_id}" if scan_id else ""
        raise click.ClickException(f"EOS usage query failed: {exc}{suffix}") from exc
