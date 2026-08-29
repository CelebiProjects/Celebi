"""
Communication functions for shell interface.

Functions for managing hosts, runners, and DITE communication.
"""
import os
import time

from ...utils import csys
from ...utils.message import Message
from ...utils import metadata
from ...kernel.chern_communicator import ChernCommunicator
from ._manager import MANAGER


def _update_runner_completion_cache(runner_names):
    """Persist runner names for interactive-shell tab completion."""
    cache_path = os.path.join(os.environ["HOME"], ".celebi", "readline.yaml")
    metadata.YamlFile(cache_path).write_variable("runners", runner_names)


def add_host(host: str, url: str) -> Message:
    """Add a host to the communicator.

    Registers a new host with the Chern communicator system, enabling
    communication with remote services and runners. Hosts are used for
    distributed task execution and data transfer.

    Args:
        host (str): Unique identifier name for the host.
        url (str): Network address or URL where the host is accessible.

    Examples:
        add_host localhost http://127.0.0.1:8080
        add_host cluster-01 https://cluster.example.com/api

    Returns:
        Message: Formatted message confirming host addition.

    Note:
        - Host names must be unique within the communicator
        - URL should be accessible from the current network
        - Host configuration is persisted in project settings
    """
    message = Message()
    cherncc = ChernCommunicator.instance()
    cherncc.add_host(url)
    message.add(f"Host '{host}' added with URL: {url}", "success")
    return message


def hosts() -> Message:
    """Show all hosts and their status.

    Displays a formatted table of all configured hosts with their current
    connection status. Host status indicates whether the communicator can
    successfully connect to each host.

    Args:
        None: Function takes no parameters.

    Examples:
        hosts()  # Display all hosts and their status

    Returns:
        Message: Formatted message containing host table with status indicators.

    Note:
        - Status "ok" indicates successful connection
        - Status "unconnected" indicates connection failure
        - Colors are used to visually distinguish statuses
        - Host list is retrieved from Chern communicator
    """
    message = Message()
    cherncc = ChernCommunicator.instance()
    host_list = cherncc.hosts()
    message.add(f"{'HOSTS':<20}{'STATUS':20}\n", "title0")
    for host in host_list:
        host_status = cherncc.host_status(host)
        color_tag = {"ok": "ok", "unconnected": "warning"}[host_status]
        message.add(f"{host:<20}", "normal")
        message.add(f"{host_status:20}\n", color_tag)
    return message


def dite() -> Message:
    """Show DITE information.

    Displays information about the Distributed Task Execution (DITE) system,
    including connection status, configuration details, and available services.
    DITE manages distributed task execution across multiple runners.

    Args:
        None: Function takes no parameters.

    Examples:
        dite()  # Display DITE system information

    Returns:
        Message: Formatted message containing DITE details.

    Note:
        - DITE must be properly configured for distributed execution
        - Information includes connection URLs and service status
        - Requires Chern communicator to be initialized
    """
    message = Message()
    cherncc = ChernCommunicator.instance()
    dite_info = cherncc.dite_info()
    message.add(str(dite_info), "normal")
    return message


def set_dite(url: str = "") -> Message:
    """Set DITE connection.

    Configures or updates the Distributed Task Execution (DITE) server URL
    for the current project. The URL is persisted in project configuration
    and used for all subsequent distributed task operations.

    Args:
        url (str, optional): DITE server URL to connect to. If empty string,
            function displays current configuration without changes.

    Examples:
        set_dite https://dite.example.com/api
        set_dite()  # Show current DITE configuration

    Returns:
        Message: Formatted message confirming DITE URL update.

    Note:
        - URL is saved to project's .celebi/hosts.json file
        - Empty URL parameter displays current configuration
        - Changes affect all distributed operations in the project
        - Requires project to be initialized
    """
    message = Message()
    project_path = csys.project_path()
    config_path = os.path.join(project_path, ".celebi", "hosts.json")
    config_file = metadata.ConfigFile(config_path)
    if url:
        config_file.write_variable("serverurl", url)
        message.add(f"DITE URL set to: {url}", "success")
    return message


def runners() -> Message:  # pylint: disable=too-many-locals
    """Display all available runners.

    Retrieves and displays information about all task execution runners
    available through the DITE system. Shows runner names, connection URLs,
    and current status (Connected/Disconnected).

    Args:
        None: Function takes no parameters.

    Examples:
        runners()  # List all available runners with status

    Returns:
        Message: Formatted message object containing runner information table,
        status indicators, and connection details. Includes warning if DITE
        is not connected.

    Note:
        - Requires DITE connection to be established
        - Runner status indicates current connectivity
        - Information is retrieved from Chern communicator
        - Message uses color coding for status display
    """
    message = Message()
    cherncc = ChernCommunicator.instance()
    dite_status = cherncc.dite_status()
    if dite_status == "unconnected":
        message.add("DITE unconnected, please connect first", "warning")
        return message
    runner_list = cherncc.runners()
    message.add(f"Number of runners: {len(runner_list)}\n", "title0")
    if runner_list:
        configs = cherncc.runners_config() or []
        config_map = {cfg.get("name", ""): cfg for cfg in configs}
        urls = cherncc.runners_url()
        for runner, url in zip(runner_list, urls):
            cfg = config_map.get(runner, {})
            message.add(f"{'Name: ':<20}{runner}", "normal")
            message.add(f"\n{'URL: ':<20}{url}", "normal")
            backend_type = cfg.get("backend_type", "reana")
            message.add(f"\n{'Backend: ':<20}{backend_type}", "normal")
            use_kerberos = cfg.get("use_kerberos", False)
            message.add(f"\n{'Kerberos: ':<20}{use_kerberos}", "normal")
            eos_mount = cfg.get("eos_mount_point", "")
            if eos_mount:
                message.add(f"\n{'EOS mount: ':<20}{eos_mount}", "normal")
            cvmfs_list = cfg.get("cvmfs", [])
            if cvmfs_list:
                message.add(f"\n{'CVMFS: ':<20}{', '.join(cvmfs_list)}", "normal")
            message.add("\n")
            info = cherncc.runner_connection(runner)
            message.add(f"{'Status: ':<20}", "info")
            if info['status'] == "Connected":
                message.add(f"{info['status']}\n", "success" )
            else:
                message.add(f"{info['status']}\n", "warning" )
            health = cfg.get("health", {})
            health_status = health.get("status", "untested")
            health_tag = {"ok": "success", "failed": "error"}.get(
                health_status, "normal")
            checked_at = health.get("checked_at", "")
            suffix = f" ({checked_at})" if checked_at else ""
            message.add(f"{'Health: ':<20}{health_status}{suffix}\n", health_tag)
            settings = cfg.get("settings", {})
            if settings.get("workdir"):
                message.add(f"{'Workdir: ':<20}{settings['workdir']}\n", "normal")
            if settings.get("cores"):
                message.add(f"{'Cores: ':<20}{settings['cores']}\n", "normal")
            message.add("------------\n")
    try:
        _update_runner_completion_cache(runner_list)
    except Exception:
        pass
    return message


def _resolve_ssh_key(settings: dict, resolve_default: bool) -> None:
    """Resolve the ssh private key for upload, in-place on settings.

    If ssh_key_path points at an existing CLIENT-side file, its content is
    moved into ssh_key_data (the server stores it and decides the path).
    A client-side-missing path passes through as a server-side path.
    With resolve_default (registration), a missing ssh_key_path falls back
    to ~/.ssh/id_rsa then ~/.ssh/id_ed25519 when they exist.
    """
    key_path = settings.get("ssh_key_path")
    if key_path is None and resolve_default:
        for candidate in ("~/.ssh/id_rsa", "~/.ssh/id_ed25519"):
            expanded = os.path.expanduser(candidate)
            if os.path.exists(expanded):
                key_path = expanded
                break
    if not key_path:
        return
    expanded = os.path.expanduser(key_path)
    if os.path.exists(expanded):
        with open(expanded, "r", encoding="utf-8") as f:
            settings["ssh_key_data"] = f.read()
        settings.pop("ssh_key_path", None)
    else:
        settings["ssh_key_path"] = expanded


def register_runner(runner: str, url: str, secret: str, backend_type: str,
                    **kwargs) -> Message:
    """Register a runner with DITE.

    Registers a new task execution runner with the Distributed Task Execution
    (DITE) system. Runners execute tasks and must be registered before they
    can be used for distributed computation.

    Args:
        runner (str): Unique identifier name for the runner.
        url (str): Network address where the runner service is accessible.
        secret (str): Authentication secret or token for runner access.
        backend_type (str): Type of execution backend (e.g., "docker", "slurm").
        **kwargs: Optional runner settings (e.g. workdir, cores, mem_mb),
            forwarded to DITE as the runner's settings.

    Examples:
        register_runner local-runner http://localhost:8080 secret123 docker
        register_runner gpu-cluster https://cluster.example.com token456 slurm

    Returns:
        Message: Formatted message confirming runner registration.

    Note:
        - Runner names must be unique within DITE
        - URL must be accessible from DITE server
        - Secret is used for secure communication
        - Backend type determines execution environment
    """
    message = Message()
    cherncc = ChernCommunicator.instance()
    if backend_type == "ssh":
        _resolve_ssh_key(kwargs, resolve_default=True)
    try:
        cherncc.register_runner(runner, url, secret, backend_type,
                                settings=kwargs or None)
        message.add(f"Runner '{runner}' registered", "success")
    except (ConnectionError, RuntimeError) as e:
        message.add(str(e), "error")
        return message
    try:
        _update_runner_completion_cache(cherncc.runners())
    except Exception:
        pass
    return message


def test_runner(runner: str, timeout: int = None) -> Message:
    """Probe a runner's capabilities (snakemake/conda/workdir) via DITE."""
    message = Message()
    cherncc = ChernCommunicator.instance()
    try:
        result = cherncc.test_runner(runner, timeout=timeout)
    except ConnectionError as e:
        message.add(str(e), "error")
        return message
    status = result.get("status", "unknown")
    tag = {"ok": "success", "failed": "error", "error": "error"}.get(
        status, "warning")
    message.add(f"Runner '{runner}': {status}", tag)
    if status != "ok" and result.get("message"):
        message.add(result["message"], tag if tag == "warning" else "error")
        return message
    for name, check in result.get("checks", {}).items():
        if check.get("ok"):
            detail = check.get("version") or check.get("path") or "ok"
            message.add(f"\n  {name:<20}{detail}", "success")
        else:
            message.add(f"\n  {name:<20}{check.get('error', 'failed')}", "error")
    return message


def _impression_scopes():
    """(project_uuid, impression_uuid) scopes to act on.

    The current object's own impression — or, when the current object is
    a folder, every impressed subobject beneath it (recursively).
    """
    try:
        current = MANAGER.current_object()
    except Exception:  # pylint: disable=broad-exception-caught
        return []
    if current.object_type() in ("project", "directory"):
        scopes = []
        for obj in current.sub_objects_recursively():
            imp = obj.impression()
            if imp is not None:
                scopes.append((obj.project_uuid(), imp.uuid))
        return scopes
    imp = current.impression()
    if imp is None:
        return []
    return [(current.project_uuid(), imp.uuid)]


def purge_ssh_runner_cache(runner: str, project: str = None,
                           impression: str = None,
                           dry_run: bool = False) -> Message:
    """Purge cached impressions from an ssh runner via DITE.

    Defaults to the current object's impression — or every impressed
    subobject when run inside a folder; an explicit impression skips the
    context lookup. Never purges the whole runner cache.
    """
    message = Message()
    if not impression:
        scopes = _impression_scopes()
        if not scopes:
            message.add("Current object has no impression — impress it "
                        "first, or pass an impression explicitly.", "error")
            return message
    else:
        scopes = [(project, impression)]
    cherncc = ChernCommunicator.instance()
    total_purged = 0
    registered_purged = False
    for scope_project, scope_imp in scopes:
        try:
            result = cherncc.purge_runner_cache(runner, project=scope_project,
                                                impression=scope_imp,
                                                dry_run=dry_run)
        except ConnectionError as e:
            message.add(str(e), "error")
            return message
        if "error" in result:
            message.add(result["error"], "error")
            return message
        purged, skipped = result.get("purged", []), result.get("skipped", [])
        total_purged += len(purged)
        entries = "entry" if len(purged) == 1 else "entries"
        if result.get("dry_run"):
            message.add(f"Dry run: {len(purged)} cache {entries} would be "
                        f"purged from runner '{runner}' "
                        f"(imp {scope_imp[:7]}…)", "warning")
        else:
            message.add(f"Purged {len(purged)} cache {entries} from "
                        f"runner '{runner}' (imp {scope_imp[:7]}…)",
                        "success")
        for entry in skipped:
            message.add(f"\n  Skipped: {entry['impression']} — "
                        f"{entry['reason']}", "warning")
        if any(entry.get("kind") == "registered" for entry in purged):
            registered_purged = True
    if len(scopes) > 1:
        message.add(f"Total: purged {total_purged} cache entries from "
                    f"runner '{runner}'",
                    "success" if total_purged else "warning")
    if registered_purged:
        message.add("Registered data lives only on this runner — restore "
                    "it with register-ssh-data.", "warning")
    return message


def cache_results(runner: str) -> Message:
    """Cache runner-resident results on that runner via DITE.

    Acts on the current object's impression — or every impressed
    subobject when run inside a folder. Each job fast-copies the
    workflow's stageout into the runner's managed impressions cache and
    records the copy in the distribution registry.
    """
    message = Message()
    scopes = _impression_scopes()
    if not scopes:
        message.add("Current object has no impression — impress it first.",
                    "error")
        return message
    cherncc = ChernCommunicator.instance()
    total_cached = 0
    for scope_project, scope_imp in scopes:
        try:
            resp = cherncc.cache_results(runner, scope_project, scope_imp)
        except ConnectionError as e:
            message.add(str(e), "error")
            return message
        if "error" in resp:
            message.add(resp["error"], "error")
            return message
        job_id = resp.get("job_id", "")
        if not job_id:
            message.add("cache-results: server returned no job id", "error")
            return message
        print(f"cache-results: job {job_id[:8]}... started on '{runner}' "
              f"(imp {scope_imp[:7]}…)")
        consecutive_unknowns = 0
        while True:
            time.sleep(3)
            state = cherncc.cache_results_status(job_id)
            status = state.get("status", "unknown")
            if status == "unknown":
                consecutive_unknowns += 1
                if consecutive_unknowns >= 10:
                    message.add(f"cache-results: no status for job "
                                f"{job_id[:8]}... after 30s; giving up",
                                "error")
                    return message
                continue
            consecutive_unknowns = 0
            if status == "copying":
                continue
            if status == "done":
                result = state.get("result") or {}
                cached = result.get("cached", 0)
                total_cached += cached
                message.add(f"Cached {cached} files from runner '{runner}' "
                            f"(imp {scope_imp[:7]}…)", "success")
                break
            if status == "failed":
                message.add(f"cache-results failed: {state.get('error')}",
                            "error")
                return message
            message.add(f"cache-results: unexpected status '{status}'",
                        "warning")
            return message
    if len(scopes) > 1:
        message.add(f"Total: cached {total_cached} files from runner "
                    f"'{runner}'",
                    "success" if total_cached else "warning")
    return message


def _human_bytes(num_bytes):
    """Human-readable byte count (B/KB/MB/GB)."""
    if num_bytes is None:
        return ""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"  # pragma: no cover


def _render_whereabouts(scope_project, scope_imp, cherncc, message):
    """Fetch and render one impression's data whereabouts.

    Rows use fixed column widths so marks, origins, and file counts
    align across locations:
      {location:<13}{state:<9}{mark} {origin:<11} {files:>4} files
    """
    resp = cherncc.whereabouts(scope_project, scope_imp)
    if "error" in resp:
        message.add(resp["error"], "error")
        return
    message.add(f"Data whereabouts for {scope_imp[:7]}…:")
    yuki = resp.get("yuki")
    if yuki:
        message.add(f"  {'yuki':<13}{'':<9}{'✓'} "
                    f"{(yuki.get('origin') or 'stored'):<11} "
                    f"{yuki.get('files', 0):>4} files · "
                    f"{_human_bytes(yuki.get('bytes'))}")
    else:
        message.add(f"  {'yuki':<13}{'':<9}✗ not in local storage")
    for name, states in (resp.get("runners") or {}).items():
        workflow = states.get("workflow")
        cache = states.get("cache")
        row = f"  {name:<13}workflow "
        row += (f"{'✓' if workflow else '✗'} "
                f"{(workflow.get('origin') if workflow else '—'):<11} "
                f"{workflow.get('files', 0) if workflow else 0:>4} files")
        row += " · cache    "
        row += (f"{'✓' if cache else '✗'} "
                f"{(cache.get('origin') if cache else '—'):<11} "
                f"{cache.get('files', 0) if cache else 0:>4} files")
        message.add(row)
    registered = resp.get("registered")
    if registered:
        message.add(f"  {'registered':<13}{'':<9}on "
                    f"{registered.get('host_runner')} "
                    f"(source: {registered.get('source_path')})")
    if resp.get("note"):
        message.add(f"  note: {resp['note']}", "warning")


def whereabouts() -> Message:
    """Report where each impression's data lives (runner cache / yuki).

    Acts on the current object's impression — or every impressed
    subobject when run inside a folder.
    """
    message = Message()
    scopes = _impression_scopes()
    if not scopes:
        message.add("Current object has no impression — impress it first.",
                    "error")
        return message
    cherncc = ChernCommunicator.instance()
    for scope_project, scope_imp in scopes:
        try:
            _render_whereabouts(scope_project, scope_imp, cherncc, message)
        except ConnectionError as e:
            message.add(str(e), "error")
            return message
    return message


def remove_runner(runner: str) -> Message:
    """Remove a runner from DITE.

    Unregisters a task execution runner from the Distributed Task Execution
    (DITE) system. Removed runners will no longer be available for task
    execution.

    Args:
        runner (str): Name of the runner to remove.

    Examples:
        remove_runner old-runner
        remove_runner deprecated-cluster

    Returns:
        Message: Formatted message confirming runner removal.

    Note:
        - Runner must be registered to be removed
        - Removal affects future task submissions
        - Currently executing tasks may be affected
        - Requires appropriate permissions in DITE
    """
    message = Message()
    cherncc = ChernCommunicator.instance()
    cherncc.remove_runner(runner)
    message.add(f"Runner '{runner}' removed", "success")
    return message


def update_runner(runner: str, **kwargs) -> Message:
    """Update settings for an existing runner.

    Modifies runner configuration stored in DITE without removing and
    re-registering the runner. Only the provided settings are changed.

    Args:
        runner (str): Name of the runner to update.
        **kwargs: Settings to update. Supported keys:
            url (str): Runner service URL.
            token (str): Authentication token.
            backend_type (str): Execution backend type (e.g. "reana", "native").
            use_kerberos (bool): Whether to use Kerberos authentication.
            eos_mount_point (str): EOS mount point path.
            cvmfs (list): List of CVMFS repository names.
            workdir (str): Working directory on the runner.
            cores (int): Number of cores to use.
            mem_mb (int): Memory limit in megabytes.
            conda_path (str): Path to the conda installation.
            snakemake_path (str): Path to the snakemake executable.
            ssh_host (str): SSH host for remote runners.
            ssh_user (str): SSH user for remote runners.
            ssh_key_path (str): Path to the SSH private key.
            ssh_port (int): SSH port for remote runners.
            remote_workdir (str): Working directory on the remote host.

    Returns:
        Message: Formatted message confirming the update.

    Examples:
        update_runner cern --use-kerberos
        update_runner cern --eos-mount-point /eos/home-m/mzhao
        update_runner cern --url https://new-reana.example.com --token abc123

    Note:
        - Runner must already be registered with DITE
        - Settings not provided remain unchanged
    """
    message = Message()
    cherncc = ChernCommunicator.instance()
    settings = {k: v for k, v in kwargs.items() if v is not None}
    if not settings:
        message.add("No settings provided to update.", "warning")
        return message
    _resolve_ssh_key(settings, resolve_default=False)
    try:
        result = cherncc.update_runner(runner, settings)
        message.add(result.get("message", f"Runner '{runner}' updated"), "success")
    except (ConnectionError, RuntimeError) as e:
        message.add(str(e), "error")
    return message


def runner_envs(runner: str) -> Message:
    """List conda environments available on a runner (ssh/native).

    Args:
        runner (str): Name of the registered runner.

    Examples:
        runner_envs pkufarm212
        runner_envs local

    Returns:
        Message: Formatted list of conda environments with paths.
    """
    message = Message()
    cherncc = ChernCommunicator.instance()
    try:
        result = cherncc.runner_envs(runner)
    except ConnectionError as e:
        message.add(str(e), "error")
        return message
    if result.get("error"):
        message.add(result["error"], "error")
        return message
    envs = result.get("envs", [])
    message.add(f"Conda environments on '{runner}' ({len(envs)}):\n", "title0")
    for env in envs:
        marker = "*" if env.get("active") else " "
        name = env.get("name") or "(unnamed)"
        message.add(f"{marker} {name:<30}{env.get('path', '')}\n", "normal")
    return message


def request_runner(runner: str) -> Message:
    """Set the requested runner for current task.

    Specifies which runner should be used for executing the current task.
    The runner must be available through DITE and properly configured.

    Args:
        runner (str): Name of the runner to use for task execution.

    Examples:
        request_runner local
        request_runner gpu-cluster-01

    Returns:
        Message: Formatted message confirming runner request.

    Note:
        - Runner must be registered with DITE
        - Current object must be a task
        - Runner preference is saved with task configuration
        - Default runner can be overridden at submission time
    """
    message = Message()
    MANAGER.current_object().set_default_runner(runner)
    message.add(f"Runner '{runner}' requested", "success")
    return message


def search_impression(partial_uuid: str) -> Message:
    """Search impressions by partial UUID.

    Searches for task execution impressions using a partial UUID match.
    Impressions are visualization snapshots or execution records that can
    be retrieved for analysis or debugging.

    Args:
        partial_uuid (str): Partial UUID string to search for impressions.

    Examples:
        search_impression abc123
        search_impression 2024-01

    Returns:
        Message: Search results containing matching impressions, including
        UUIDs, creation times, and associated task information.

    Note:
        - Partial UUID can match any part of the full UUID
        - Search is case-insensitive
        - Current object context affects search scope
        - Results may include impressions from related tasks
    """
    message = MANAGER.current_object().search_impression(partial_uuid)
    return message


def _current_project():
    """(project_dir, project_uuid) of the current project.

    Returns (None, "") when not inside a Celebi project.
    """
    import os
    from CelebiChrono.utils import metadata
    from CelebiChrono.utils.path_utils import project_path
    try:
        project_dir = project_path()
        if not project_dir:
            return None, ""
        uuid = metadata.ConfigFile(
            os.path.join(project_dir, ".celebi", "config.json")
        ).read_variable("project_uuid", "")
        return project_dir, uuid
    except Exception:  # pylint: disable=broad-exception-caught
        return None, ""


def _current_project_uuid():
    """The current project's uuid, or "" when not inside a project."""
    return _current_project()[1]


def sync_live() -> Message:
    """Push the project's live impression set to DITE (best-effort).

    Failures are reported as a warning: a stale set is safe by the
    unknown-is-live rule.
    """
    from CelebiChrono.kernel.liveness import compute_live_sets
    message = Message()
    try:
        project_dir, project_uuid = _current_project()
        if not project_uuid:
            message.add("No project found — run inside a Celebi project.",
                        "error")
            return message
        live, superseded = compute_live_sets(project_dir)
        result = ChernCommunicator.instance().put_live_set(
            project_uuid, live, superseded)
        message.add(f"Synced live set: {result.get('live')} live, "
                    f"{result.get('superseded')} superseded, "
                    f"{result.get('live_workflows')} live workflows")
    except Exception as exc:
        message.add(f"Live-set sync failed (safe to ignore): {exc}",
                    "warning")
    return message


def _merge_sync_lines(message, sync):
    """Merge a best-effort sync-live result into a message."""
    for text, color in sync.messages:
        message.add(f"[sync-live] {text}", color)


def purge_stale_cache(runner: str, dry_run: bool = False) -> Message:
    """Purge superseded impressions' cache entries on a runner.

    The project's live set is re-synced first (best-effort), so the
    purge always sees the freshest liveness data; a failed sync warns
    and never blocks the purge.
    """
    message = Message()
    message.data["purge_count"] = 0
    project_uuid = _current_project_uuid()
    if not project_uuid:
        message.add("No project found — run inside a Celebi project.",
                    "error")
        return message
    _merge_sync_lines(message, sync_live())
    try:
        result = ChernCommunicator.instance().purge_stale_cache(
            runner, dry_run=dry_run, project_uuid=project_uuid)
        message.data["purge_count"] = len(result.get("purged", []))
        for entry in result.get("purged", []):
            message.add(f"Purged cache: {entry.get('project')}/"
                        f"{entry.get('impression')}")
        for entry in result.get("skipped", []):
            message.add(f"Skipped cache: {entry.get('project')}/"
                        f"{entry.get('impression')} — {entry.get('reason')}",
                        "warning")
        if result.get("dry_run"):
            message.add(f"Dry run — {len(result.get('purged', []))} cache "
                        "entries would be purged, nothing was deleted.")
        else:
            message.add(f"Purged {len(result.get('purged', []))} cache "
                        f"entries from runner '{runner}'")
    except Exception as exc:
        message.add(f"Purge failed: {exc}", "error")
    return message


def purge_stale_workflows(runner: str, dry_run: bool = False) -> Message:
    """Delete non-live workflow workspaces on a runner.

    The project's live set is re-synced first (best-effort), so the
    purge always sees the freshest liveness data; a failed sync warns
    and never blocks the purge.
    """
    message = Message()
    message.data["purge_count"] = 0
    project_uuid = _current_project_uuid()
    if not project_uuid:
        message.add("No project found — run inside a Celebi project.",
                    "error")
        return message
    _merge_sync_lines(message, sync_live())
    try:
        result = ChernCommunicator.instance().purge_stale_workflows(
            runner, dry_run=dry_run, project_uuid=project_uuid)
        message.data["purge_count"] = len(result.get("purged", []))
        for entry in result.get("purged", []):
            message.add(f"Purged workflow: {entry.get('project')}/"
                        f"{entry.get('workflow')}")
        for entry in result.get("skipped", []):
            message.add(f"Skipped workflow: {entry.get('project')}/"
                        f"{entry.get('workflow')} — {entry.get('reason')}",
                        "warning")
        if result.get("already_gone"):
            message.add(f"{result['already_gone']} workspace(s) already "
                        "gone, skipped")
        if result.get("dry_run"):
            message.add(f"Dry run — {len(result.get('purged', []))} "
                        "workflows would be purged, nothing was deleted.")
        else:
            message.add(f"Purged {len(result.get('purged', []))} workflows "
                        f"from runner '{runner}'")
    except Exception as exc:
        message.add(f"Purge failed: {exc}", "error")
    return message
