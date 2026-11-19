"""Preview, execute and independently verify EOS cache cleanup."""
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

import click
from .eos_usage import format_size

TERMINAL = {"planned", "done", "partial", "failed", "preflight_failed"}


def refresh_local_live(communicator, projects, clear_projects=()):
    """Use isolated Celebi processes so caches cannot leak between projects."""
    from CelebiChrono.interface.shell_modules.communication import _current_project
    config_path = Path.home() / ".celebi" / "config.json"
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    paths = list(config.get("projects_path", {}).values())
    current_path, _ = _current_project()
    if current_path:
        paths.append(current_path)  # The current checkout takes precedence.
    found = {}
    for path in paths:
        try:
            project = json.loads((Path(path) / ".celebi/config.json").read_text())["project_uuid"]
            if project in projects and project not in clear_projects:
                found[project] = path
        except (OSError, ValueError, KeyError, TypeError):
            continue
    code = ("import json,sys; from CelebiChrono.kernel.liveness import compute_live_sets; "
            "live,superseded=compute_live_sets(sys.argv[1]); "
            "print('LIVE_RESULT='+json.dumps({'live':live,'superseded':superseded}))")
    for project, path in found.items():
        result = subprocess.run([sys.executable, "-c", code, path], cwd=path,
                                capture_output=True, text=True, timeout=240, check=True)
        line = next(line for line in reversed(result.stdout.splitlines())
                    if line.startswith("LIVE_RESULT="))
        data = json.loads(line[len("LIVE_RESULT="):])
        communicator.put_live_set(project, data["live"], data["superseded"])
        click.echo(f"Refreshed live set: {project}", err=True)
    missing = set(projects) - set(clear_projects) - set(found)
    if missing:
        click.echo("No local checkout to refresh: " + ", ".join(sorted(missing)), err=True)
    return missing


def show_plan(state, as_json=False):
    if as_json:
        click.echo(json.dumps(state, indent=2))
        return
    manifest = state["manifest"]
    entries = manifest["entries"]
    click.echo(f"EOS cleanup plan: {state['id']}  Status: {state['status']}")
    click.echo(f"Root: {manifest['root']}")
    click.echo(f"Delete {len(entries)} directories, "
               f"{format_size(sum(e['bytes'] for e in entries))}")
    for project in manifest["projects"]:
        rows = [e for e in entries if e["project"] == project]
        scope = "ALL (including live)" if project in manifest["clear_projects"] else "selected non-live/unknown"
        click.echo(f"  {project}: {scope}; {len(rows)} directories, "
                   f"{format_size(sum(e['bytes'] for e in rows))}")
    click.echo(f"Protected live directories: {len(manifest['protected'])}; "
               f"unattributed entries skipped: {manifest['skipped_unattributed']}")
    click.echo(f"Manifest SHA256: {state['manifest_sha256']}")
    if state.get("error"):
        click.echo(state["error"])
    if state.get("verification"):
        check = state["verification"]
        click.echo(f"Independent verification: {check['status']}; "
                   f"remaining targets: {len(check.get('remaining', []))}; "
                   f"missing protected paths: {len(check.get('protected_missing', []))}")


def poll(communicator, state, timeout):
    deadline = time.monotonic() + timeout
    while state["status"] not in TERMINAL:
        if time.monotonic() >= deadline:
            click.echo(f"Still pending. Resume: celebi-cli eos-cleanup --plan-id {state['id']}",
                       err=True)
            break
        time.sleep(min(5, max(0, deadline - time.monotonic())))
        state = communicator.eos_cleanup_status(state["id"])
    return state


@click.command(name="eos-cleanup")
@click.argument("runner", required=False)
@click.option("--scan-id", help="Build a preview from a completed, recent EOS scan.")
@click.option("--plan-id", help="Query an existing plan, or execute it with --execute.")
@click.option("--all-projects", is_flag=True, help="Include all projects in the scan.")
@click.option("--project", "projects", multiple=True, help="Project UUID; repeat for multiple projects.")
@click.option("--include-unknown", is_flag=True, help="Also select unknown caches with a project owner.")
@click.option("--clear-project", "clear_projects", multiple=True,
              help="Explicitly clear ALL cache for this project UUID, including live.")
@click.option("--execute", is_flag=True, help="Execute after showing and confirming the preview.")
@click.option("--yes", "-y", is_flag=True, help="Confirm the displayed manifest without prompting.")
@click.option("--wait/--no-wait", default=True, help="Wait for cleanup and independent verification.")
@click.option("--timeout", type=click.IntRange(min=1), default=600, show_default=True)
@click.option("--json", "as_json", is_flag=True, help="Show full manifest and reports as JSON.")
def eos_cleanup_command(runner, scan_id, plan_id, all_projects, projects, include_unknown,
                        clear_projects, execute, yes, wait, timeout, as_json):
    """Preview EOS cleanup by default. Deletion requires --execute.

    RUNNER starts a read-only scan first; --scan-id reuses one with metadata
    fingerprints. Without --all-projects/--project, scope is the current project.
    Unknown/unattributed directories are never silently included.
    """
    from CelebiChrono.kernel.chern_communicator import ChernCommunicator
    from CelebiChrono.interface.shell_modules.communication import _current_project
    communicator = ChernCommunicator.instance()
    try:
        if yes and not execute:
            raise click.UsageError("--yes requires --execute")
        if as_json and execute and not yes:
            raise click.UsageError("JSON execution requires --yes; inspect the preview first")
        if plan_id:
            if runner or scan_id or all_projects or projects or clear_projects or include_unknown:
                raise click.UsageError("--plan-id cannot be combined with new scope options")
            state = communicator.eos_cleanup_status(plan_id)
        else:
            if bool(runner) == bool(scan_id):
                raise click.UsageError("Provide either RUNNER or --scan-id")
            if all_projects and projects:
                raise click.UsageError("Choose --all-projects or --project")
            selected = list(projects)
            if not all_projects and not selected:
                _, current = _current_project()
                if not current:
                    raise click.UsageError("Choose --all-projects/--project or enter a project")
                selected = [current]
            if not all_projects and not set(clear_projects) <= set(selected):
                raise click.UsageError("--clear-project must be in the selected scope")
            if runner:
                scan_id = uuid.uuid4().hex
                click.echo(f"Read-only scan: {scan_id}; resume with eos-cleanup --scan-id {scan_id} "
                           "and the same scope flags", err=True)
                scan = communicator.start_eos_usage(
                    runner, scan_id, selected[0] if len(selected) == 1 else None)
            else:
                scan = communicator.eos_usage_status(scan_id)
            deadline = time.monotonic() + timeout
            while scan["status"] not in ("done", "failed", "submission_unknown"):
                if time.monotonic() >= deadline:
                    raise click.ClickException(f"Scan pending; resume with --scan-id {scan_id}")
                time.sleep(5)
                scan = communicator.eos_usage_status(scan_id)
            if scan["status"] != "done":
                raise click.ClickException(f"EOS scan {scan_id}: {scan['status']}")
            if all_projects:
                selected = [p["project"] for p in scan["report"]["projects"]]
            refresh_local_live(communicator, selected, clear_projects)
            state = communicator.plan_eos_cleanup(scan_id, selected, include_unknown, clear_projects)
            plan_id = state["id"]
        if state["status"] == "planned":
            if as_json and execute:
                click.echo(json.dumps(state, indent=2), err=True)
            else:
                show_plan(state, as_json)
            if not execute or not state["manifest"]["entries"]:
                if not as_json:
                    click.echo(f"Preview only. Execute: celebi-cli eos-cleanup --plan-id {plan_id} --execute")
                return state
            if not yes and not click.confirm("Permanently delete exactly this EOS manifest?", default=False):
                click.echo("EOS cleanup cancelled; nothing deleted.")
                return state
            # Existing plans also need a current live check. Server refuses changed plans.
            refresh_local_live(communicator, state["manifest"]["projects"],
                               state["manifest"]["clear_projects"])
            click.echo(f"Cleanup plan: {plan_id}; resume with eos-cleanup --plan-id {plan_id}", err=True)
            state = communicator.execute_eos_cleanup(plan_id, state["manifest_sha256"])
        if wait:
            state = poll(communicator, state, timeout)
        show_plan(state, as_json)
        if state["status"] in ("failed", "partial", "preflight_failed"):
            raise click.ClickException("Cleanup incomplete; inspect the saved plan/report. No automatic retry.")
        return state
    except click.ClickException:
        raise
    except Exception as exc:
        resume = f"; query --plan-id {plan_id}" if plan_id else ""
        raise click.ClickException(f"EOS cleanup failed: {exc}{resume}") from exc
