"""Celebi CLI main entry point with categorized, flat commands."""
import inspect

import click
from CelebiChrono.utils.debug_logging import setup_logging
from .commands import (
    navigation, file_operations, object_creation, task_configuration,
    execution_management, communication, visualization, utilities, booking,
    project_management,
)
from .commands import liveness


COMMAND_SECTIONS = (
    ("Projects", (
        "init", "list-projects", "ls-projects", "use-project",
        "register-project", "remove-project", "project-path", "project-uuid",
        "cd-project",
    )),
    ("Browse and inspect", (
        "cd", "ls", "short-ls", "tree", "status", "predecessors",
        "successors", "draw-dag", "draw-dag-graphviz",
    )),
    ("Create objects", (
        "create-task", "create-algorithm", "create-data", "create-data-list",
        "create-lhcb-ap-list", "create-multi-tasks", "create-multi-data", "mkdir",
    )),
    ("Configure tasks and algorithms", (
        "config", "add-algorithm", "add-input", "input", "remove-input",
        "add-multi-inputs", "remove-multi-inputs", "set-parameter",
        "remove-parameter", "add-parameter-subtask", "set-environment",
        "set-memory-limit", "set-descriptor", "request-runner", "auto-download",
        "cache-on-runner",
    )),
    ("Files and content", (
        "cat", "display", "edit", "edit-script", "edit-readme", "comment",
        "import", "import-file", "add-source", "cp", "mv", "rm", "move-file",
        "remove-file", "replace",
    )),
    ("Run workflows", (
        "submit", "test", "cancel",
    )),
    ("Results and logs", (
        "log", "engine-logs", "collect", "collect-outputs", "collect-logs",
        "refresh-filelists", "check-results", "export", "imgcat",
    )),
    ("Data and transfer", (
        "upload-data", "register-ssh-data", "attach-data", "verify-data",
        "transfer", "purge-data", "whereabouts", "cache-results", "add-apd-token",
    )),
    ("Impressions and provenance", (
        "impress", "impression", "view", "view-url", "search-impression",
        "trace", "history", "changes", "watermark", "bookkeep",
        "bookkeeping-url", "open-bookkeeping",
    )),
    ("Runners and capacity", (
        "runners", "register-runner", "update-runner", "remove-runner",
        "test-runner", "install-environment", "runner-environments",
        "yuki-overview", "hosts",
        "add-host", "refresh-distribution",
    )),
    ("Settings and services", (
        "user-config", "cache-policy", "dite", "set-dite", "booking-server",
        "register-booking-server", "book-reana",
        "register-celebi-server",
    )),
    ("Maintenance and recovery", (
        "doctor", "purge", "purge-old-impressions", "purge-impressions",
        "homekeep",
        "gc-impressions", "pack-impressions", "migrate-impressions",
        "impression-stats", "purge-ssh-runner-cache", "purge-stale-cache",
        "purge-stale-workflows", "stop-orphaned-workflows", "stop-workflow",
        "sync-live",
    )),
    ("Advanced and developer", (
        "workaround", "workaround-vre", "danger-call", "danger", "preshell",
        "postshell", "clean-impressions",
    )),
    ("Shell utilities", (
        "help", "helpme", "system-shell",
    )),
)


COMPATIBILITY_COMMANDS = {
    "add-parameter": "set-parameter",
    "bookkeep-url": "bookkeeping-url",
    "cd": "`cd` inside the interactive `celebi` shell instead",
    "cdproject": "use-project",
    "config-cache-invalidation-mode": "cache-policy",
    "kill": "cancel",
    "kill-running-workflows": "stop-orphaned-workflows",
    "kill-workflow": "stop-workflow",
    "mvfile": "move-file",
    "navigate": "project-path",
    "rm-parameter": "remove-parameter",
    "rmfile": "remove-file",
    "runner-envs": "runner-environments",
    "set-env": "set-environment",
    "set-mem": "set-memory-limit",
    "stats-impressions": "impression-stats",
    "viewurl": "view-url",
}
HELP_HIDDEN_COMMANDS = set(COMPATIBILITY_COMMANDS)


class SectionedGroup(click.Group):
    """Render the flat CLI as task-oriented sections without nesting it."""

    def format_commands(self, ctx, formatter):
        shown = set()
        for heading, names in COMMAND_SECTIONS:
            rows = []
            for name in names:
                if name in HELP_HIDDEN_COMMANDS:
                    continue
                command = self.get_command(ctx, name)
                if command is None or command.hidden or name in shown:
                    continue
                rows.append((name, command.get_short_help_str()))
                shown.add(name)
            if rows:
                with formatter.section(heading):
                    formatter.write_dl(rows)

        other_rows = []
        for name in self.list_commands(ctx):
            if name in shown or name in HELP_HIDDEN_COMMANDS:
                continue
            command = self.get_command(ctx, name)
            if command is not None and not command.hidden:
                other_rows.append((name, command.get_short_help_str()))
        if other_rows:
            with formatter.section("Other commands"):
                formatter.write_dl(other_rows)

        aliases = []
        for alias, replacement in COMPATIBILITY_COMMANDS.items():
            if self.get_command(ctx, alias) is not None:
                aliases.append((alias, f"Compatibility alias; use {replacement}."))
        if aliases:
            with formatter.section("Compatibility aliases"):
                formatter.write_dl(aliases)


@click.group(cls=SectionedGroup)
@click.option("--debug", is_flag=True, default=False,
              help="Enable verbose logging in ~/.celebi/logs/celebi.log")
def cli(debug):
    """Celebi CLI commands for project management."""
    setup_logging(debug=debug)

# Commands will be registered here
cli.add_command(project_management.init_command)
cli.add_command(project_management.list_projects_command)
cli.add_command(project_management.use_project_command)
cli.add_command(project_management.register_project_command)
cli.add_command(project_management.remove_project_command)
cli.add_command(navigation.cd_command)
cli.add_command(navigation.tree_command)
cli.add_command(navigation.status_command)
cli.add_command(navigation.navigate_command)
cli.add_command(navigation.cdproject_command)
cli.add_command(navigation.short_ls_command)
cli.add_command(navigation.project_uuid_command)

# File operations commands (9 commands)
cli.add_command(file_operations.ls_command)
cli.add_command(file_operations.cat_command)
cli.add_command(file_operations.display_command)
cli.add_command(file_operations.mv_command)
cli.add_command(file_operations.cp_command)
cli.add_command(file_operations.rm_command)
cli.add_command(file_operations.rmfile_command)
cli.add_command(file_operations.mvfile_command)
cli.add_command(file_operations.replace_command)
cli.add_command(file_operations.import_command)
cli.add_command(file_operations.workaround_vre_command)
cli.add_command(file_operations.upload_data_command)
cli.add_command(file_operations.add_input_command)
cli.add_command(file_operations.add_source_command)
cli.add_command(file_operations.transfer_command)
cli.add_command(file_operations.export_command)

# Object creation commands (6 commands)
cli.add_command(object_creation.create_algorithm_command)
cli.add_command(object_creation.create_task_command)
cli.add_command(object_creation.create_multi_tasks_command)
cli.add_command(object_creation.create_data_command)
cli.add_command(object_creation.create_multi_data_command)
cli.add_command(object_creation.create_data_list_command)
cli.add_command(object_creation.mkdir_command)
cli.add_command(object_creation.attach_data_command)
cli.add_command(object_creation.verify_data_command)
cli.add_command(object_creation.register_ssh_data_command)
cli.add_command(object_creation.create_lhcb_ap_list_command)

# Task configuration commands (9 commands)
cli.add_command(task_configuration.remove_input_command)
cli.add_command(task_configuration.add_multi_inputs_command)
cli.add_command(task_configuration.remove_multi_inputs_command)
cli.add_command(task_configuration.add_algorithm_command)
cli.add_command(task_configuration.add_parameter_command)
cli.add_command(task_configuration.rm_parameter_command)
cli.add_command(task_configuration.add_parameter_subtask_command)
cli.add_command(task_configuration.set_env_command)
cli.add_command(task_configuration.set_mem_command)
cli.add_command(task_configuration.set_descriptor_command)
cli.add_command(task_configuration.auto_download_command)
cli.add_command(task_configuration.cache_on_runner_command)
cli.add_command(task_configuration.add_host_command)
cli.add_command(task_configuration.hosts_command)
cli.add_command(task_configuration.add_apd_token_command)
cli.add_command(task_configuration.user_config_command)

# Execution management commands
cli.add_command(execution_management.runners_command)
cli.add_command(execution_management.register_runner_command)
cli.add_command(execution_management.update_runner_command)
cli.add_command(execution_management.remove_runner_command)
cli.add_command(execution_management.runner_envs_command)
cli.add_command(execution_management.install_environment_command)
cli.add_command(execution_management.test_runner_command)
cli.add_command(execution_management.purge_ssh_runner_cache_command)
cli.add_command(execution_management.refresh_distribution_command)
cli.add_command(execution_management.yuki_overview_command)
cli.add_command(execution_management.cache_results_command)
cli.add_command(execution_management.whereabouts_command)
cli.add_command(execution_management.submit_command)
cli.add_command(execution_management.kill_command)
cli.add_command(execution_management.collect_command)
cli.add_command(execution_management.log_command)
cli.add_command(execution_management.edit_command)
cli.add_command(execution_management.test_command)
cli.add_command(execution_management.purge_command)
cli.add_command(execution_management.purge_old_impressions_command)
cli.add_command(execution_management.purge_impressions_command)
cli.add_command(execution_management.homekeep_command)
cli.add_command(execution_management.check_results_command)
cli.add_command(execution_management.collect_outputs_command)
cli.add_command(execution_management.collect_logs_command)
cli.add_command(execution_management.engine_logs_command)
cli.add_command(execution_management.refresh_filelists_command)
cli.add_command(execution_management.purge_data_command)

cli.add_command(liveness.kill_running_workflows_command)
cli.add_command(liveness.kill_workflow_command)
cli.add_command(liveness.sync_live_command)
cli.add_command(liveness.purge_stale_cache_command)
cli.add_command(liveness.purge_stale_workflows_command)

# Communication commands
cli.add_command(communication.config_command)
cli.add_command(communication.config_cache_invalidation_mode_command)
cli.add_command(communication.danger_command)
cli.add_command(communication.trace_command)
cli.add_command(communication.history_command)
cli.add_command(communication.changes_command)
cli.add_command(communication.comment_command)
cli.add_command(communication.edit_readme_command)
cli.add_command(communication.impression_command)
cli.add_command(communication.preshell_command)
cli.add_command(communication.postshell_command)
cli.add_command(communication.impress_command)
cli.add_command(communication.dite_command)
cli.add_command(communication.set_dite_command)
cli.add_command(communication.request_runner_command)
cli.add_command(communication.search_impression_command)

# Visualization commands
cli.add_command(visualization.view_command)
cli.add_command(visualization.viewurl_command)
cli.add_command(visualization.imgcat_command)
cli.add_command(visualization.draw_dag_command)

# Utility commands
cli.add_command(utilities.watermark_command)
cli.add_command(utilities.doctor_command)
cli.add_command(utilities.bookkeep_command)
cli.add_command(utilities.bookkeep_url_command)
cli.add_command(utilities.open_bookkeeping_command)
cli.add_command(utilities.predecessors_command)
cli.add_command(utilities.successors_command)
cli.add_command(utilities.gc_impressions_command)
cli.add_command(utilities.pack_impressions_command)
cli.add_command(utilities.migrate_impressions_command)
cli.add_command(utilities.stats_impressions_command)

# Booking commands
cli.add_command(booking.booking_server_command)
cli.add_command(booking.register_booking_server_command)
cli.add_command(booking.book_reana_command)
cli.add_command(booking.register_celebi_server_command)


# Old spellings remain callable for scripts, but are omitted from normal help.
_COMPATIBILITY_ALIASES = {
    "add-parameter": task_configuration.add_parameter_command,
    "bookkeep-url": utilities.bookkeep_url_command,
    "config-cache-invalidation-mode": communication.config_cache_invalidation_mode_command,
    "kill": execution_management.kill_command,
    "kill-running-workflows": liveness.kill_running_workflows_command,
    "kill-workflow": liveness.kill_workflow_command,
    "mvfile": file_operations.mvfile_command,
    "navigate": navigation.navigate_command,
    "rm-parameter": task_configuration.rm_parameter_command,
    "rmfile": file_operations.rmfile_command,
    "runner-envs": execution_management.runner_envs_command,
    "set-env": task_configuration.set_env_command,
    "set-mem": task_configuration.set_mem_command,
    "stats-impressions": utilities.stats_impressions_command,
    "viewurl": visualization.viewurl_command,
}
for _alias, _command in _COMPATIBILITY_ALIASES.items():
    cli.add_command(_command, name=_alias)


_SHELL_HELP_SOURCES = {
    "bookkeeping-url": "bookkeep_url",
    "booking-server": "check_booking_server",
    "cancel": "kill",
    "create-algorithm": "mkalgorithm",
    "create-data": "mkdata",
    "create-data-list": "mkdatalist",
    "create-task": "mktask",
    "draw-dag": "draw_dag_graphviz",
    "edit": "get_script_path",
    "impression-stats": "stats_impressions",
    "import": "import_file",
    "log": "error_log",
    "move-file": "mv_file",
    "project-path": "navigate",
    "remove-file": "rm_file",
    "remove-parameter": "rm_parameter",
    "runner-environments": "runner_envs",
    "set-environment": "set_environment",
    "set-memory-limit": "set_memory_limit",
    "set-parameter": "add_parameter",
    "stop-orphaned-workflows": "kill_running_workflows",
    "stop-workflow": "kill_workflow",
    "view-url": "viewurl",
}


def _enrich_short_help_from_shell_functions():
    """Reuse detailed operation docs when a Click wrapper only has a summary."""
    from CelebiChrono.interface import shell

    for command_name, command in cli.commands.items():
        if command_name in HELP_HIDDEN_COMMANDS:
            continue
        current = inspect.cleandoc(command.help or "")
        if len(current.splitlines()) > 1:
            continue
        source_name = _SHELL_HELP_SOURCES.get(
            command_name, command_name.replace("-", "_")
        )
        source = getattr(shell, source_name, None)
        detailed = inspect.cleandoc(getattr(source, "__doc__", "") or "")
        if len(detailed.splitlines()) > 1:
            command.help = _format_operation_doc(detailed)


def _format_operation_doc(doc):
    """Convert internal Google-style docstrings into readable CLI prose."""
    sections = {"Args:", "Returns:", "Examples:", "Note:", "Notes:"}
    output = []
    block = []
    mode = "description"

    def flush_block():
        if not block:
            return
        output.extend(("", "\b", *[line.strip() for line in block]))
        block.clear()

    for line in doc.splitlines():
        stripped = line.strip()
        if stripped in sections:
            flush_block()
            if stripped in {"Args:", "Returns:"}:
                mode = "skip"
            else:
                mode = "block"
                output.extend(("", "Examples:" if stripped == "Examples:" else "Notes:"))
            continue
        if mode == "description":
            output.append(line)
        elif mode == "block" and stripped:
            block.append(line)
    flush_block()
    return "\n".join(output).strip()


_enrich_short_help_from_shell_functions()
