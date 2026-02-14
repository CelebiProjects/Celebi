import click
from .commands import navigation, file_operations, object_creation, task_configuration, execution_management, communication, visualization

@click.group()
def cli():
    """Celebi CLI commands for project management."""
    pass

# Commands will be registered here
cli.add_command(navigation.cd_command)
cli.add_command(navigation.tree_command)
cli.add_command(navigation.status_command)
cli.add_command(navigation.navigate_command)
cli.add_command(navigation.cdproject_command)
cli.add_command(navigation.short_ls_command)
cli.add_command(navigation.jobs_command)

# File operations commands (9 commands)
cli.add_command(file_operations.ls_command)
cli.add_command(file_operations.mv_command)
cli.add_command(file_operations.cp_command)
cli.add_command(file_operations.rm_command)
cli.add_command(file_operations.rmfile_command)
cli.add_command(file_operations.mvfile_command)
cli.add_command(file_operations.import_command)
cli.add_command(file_operations.send_command)
cli.add_command(file_operations.add_input_command)

# Object creation commands (4 commands)
cli.add_command(object_creation.create_algorithm_command)
cli.add_command(object_creation.create_task_command)
cli.add_command(object_creation.create_data_command)
cli.add_command(object_creation.mkdir_command)

# Task configuration commands (9 commands)
cli.add_command(task_configuration.remove_input_command)
cli.add_command(task_configuration.add_algorithm_command)
cli.add_command(task_configuration.add_parameter_command)
cli.add_command(task_configuration.rm_parameter_command)
cli.add_command(task_configuration.add_parameter_subtask_command)
cli.add_command(task_configuration.set_env_command)
cli.add_command(task_configuration.set_mem_command)
cli.add_command(task_configuration.add_host_command)
cli.add_command(task_configuration.hosts_command)

# Execution management commands (8 commands)
cli.add_command(execution_management.runners_command)
cli.add_command(execution_management.register_runner_command)
cli.add_command(execution_management.remove_runner_command)
cli.add_command(execution_management.submit_command)
cli.add_command(execution_management.collect_command)
cli.add_command(execution_management.error_log_command)
cli.add_command(execution_management.view_command)
cli.add_command(execution_management.edit_command)

# Communication commands (7 commands)
cli.add_command(communication.config_command)
cli.add_command(communication.danger_command)
cli.add_command(communication.trace_command)
cli.add_command(communication.history_command)
cli.add_command(communication.changes_command)
cli.add_command(communication.preshell_command)
cli.add_command(communication.postshell_command)
cli.add_command(communication.impress_command)

# Visualization commands (2 commands)
cli.add_command(visualization.view_command)
cli.add_command(visualization.viewurl_command)