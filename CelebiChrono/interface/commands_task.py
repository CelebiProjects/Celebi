"""
Task Creation and Configuration Command Handlers for Chern Shell.

This module contains command handlers for creating and configuring tasks,
algorithms, and data objects.
"""
# pylint: disable=broad-exception-caught
from ..interface import shell
from ..interface.ChernManager import get_manager


MANAGER = get_manager()


class TaskCommands:
    """Mixin class providing task management command handlers."""

    def do_create_task(self, arg: str) -> None:
        """Create a new task."""
        try:
            obj = arg.split()[0]
            shell.mktask(obj)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a task name. {e}")
        except Exception as e:
            print(f"Error creating task: {e}")

    def do_create_multi_tasks(self, arg: str) -> None:
        """Create multiple tasks with a base name and number of tasks."""
        try:
            objs = arg.split()
            if len(objs) < 2:
                print(
                    "Error: Please provide at least two task arguments: "
                    "base_name and number_of_tasks."
                )
                return
            base_name = objs[0]
            begin_number_of_tasks = 0
            if len(objs) == 3:
                begin_number_of_tasks = int(objs[1])
            end_number_of_tasks = int(objs[-1])
            number_of_tasks = end_number_of_tasks - begin_number_of_tasks
            if number_of_tasks <= 0 or number_of_tasks > 10000:
                print("Error: number_of_tasks should be between 1 and 10000.")
                return
            for i in range(begin_number_of_tasks, end_number_of_tasks):
                task_name = f"{base_name}_{i}"
                shell.mktask(task_name)
                shell.add_parameter_subtask(task_name, "index", str(i))
        except Exception as e:
            print(f"Error creating task: {e}")

    def do_create_algorithm(self, arg: str) -> None:
        """Create a new algorithm."""
        try:
            obj = arg.split()[0]
            shell.mkalgorithm(obj)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide an algorithm name. {e}")
        except Exception as e:
            print(f"Error creating algorithm: {e}")

    def do_create_data(self, arg: str) -> None:
        """Create a new data object."""
        try:
            obj = arg.split()[0]
            shell.mkdata(obj)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a data name. {e}")
        except Exception as e:
            print(f"Error creating data: {e}")

    def do_add_algorithm(self, arg: str) -> None:
        """Add an algorithm to current task."""
        try:
            obj = arg.split()[0]
            shell.add_algorithm(obj)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide an algorithm path. {e}")
        except Exception as e:
            print(f"Error adding algorithm: {e}")

    def do_input(self, arg: str) -> None:
        """Add input to current object."""
        try:
            input_path = arg.split()[0]
            MANAGER.current_object().input(input_path)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide an input path. {e}")
        except Exception as e:
            print(f"Error adding input: {e}")

    def do_add_input(self, arg: str) -> None:
        """Add input with path and alias."""
        try:
            args = arg.split()
            obj1 = args[0]
            obj2 = args[1]
            shell.add_input(obj1, obj2)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide path and alias. {e}")
        except Exception as e:
            print(f"Error adding input: {e}")

    def do_add_multi_inputs(self, arg: str) -> None:
        """Create multiple tasks with a base name and number of tasks."""
        try:
            objs = arg.split()
            if len(objs) < 3:
                print(
                    "Error: Please provide at least tree task arguments: "
                    "path/base_name, alias and number_of_tasks."
                )
                return
            base_name = objs[0]
            alias = objs[1]
            begin_number_of_tasks = 0
            if len(objs) == 4:
                begin_number_of_tasks = int(objs[2])
            end_number_of_tasks = int(objs[-1])
            number_of_tasks = end_number_of_tasks - begin_number_of_tasks
            if number_of_tasks <= 0 or number_of_tasks > 10000:
                print("Error: number_of_tasks should be between 1 and 10000.")
                return
            for i in range(begin_number_of_tasks, end_number_of_tasks):
                task_name = f"{base_name}_{i}"
                alias_index = f"{alias}_{i}"
                shell.add_input(task_name, alias_index)
        except Exception as e:
            print(f"Error creating task: {e}")

    def do_remove_input(self, arg: str) -> None:
        """Remove an input from current object."""
        try:
            obj = arg.split()[0]
            shell.remove_input(obj)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide an input alias to remove. {e}")
        except Exception as e:
            print(f"Error removing input: {e}")

    def do_add_parameter(self, arg: str) -> None:
        """Add a parameter to current task."""
        try:
            args = arg.split()
            obj1 = args[0]
            obj2 = args[1]
            shell.add_parameter(obj1, obj2)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide parameter name and value. {e}")
        except Exception as e:
            print(f"Error adding parameter: {e}")

    def do_remove_parameter(self, arg: str) -> None:
        """Remove a parameter from current task."""
        try:
            obj = arg.split()[0]
            shell.rm_parameter(obj)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a parameter name to remove. {e}")
        except Exception as e:
            print(f"Error removing parameter: {e}")
