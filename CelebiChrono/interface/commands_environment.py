"""
Environment and Execution Command Handlers for Chern Shell.

This module contains command handlers for environment settings
and job execution management.
"""
# pylint: disable=broad-exception-caught
from ..interface import shell
from ..interface.ChernManager import get_manager


MANAGER = get_manager()


class EnvironmentCommands:
    """Mixin class providing environment and execution command handlers."""

    def do_set_environment(self, arg: str) -> None:
        """Set environment for current object."""
        try:
            environment = arg.split()[0]
            shell.set_environment(environment)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide an environment name. {e}")
        except Exception as e:
            print(f"Error setting environment: {e}")

    def do_setenv(self, arg: str) -> None:
        """Set environment for current object (alias for set-environment)."""
        try:
            environment = arg.split()[0]
            shell.set_environment(environment)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide an environment name. {e}")
        except Exception as e:
            print(f"Error setting environment: {e}")

    def do_set_memory_limit(self, arg: str) -> None:
        """Set memory limit for current object."""
        try:
            memory_limit = arg.split()[0]
            shell.set_memory_limit(memory_limit)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a memory limit. {e}")
        except Exception as e:
            print(f"Error setting memory limit: {e}")

    def do_auto_download(self, arg: str) -> None:
        """Enable or disable auto download."""
        try:
            auto_download = arg.split()[0]
            if auto_download == "on":
                MANAGER.current_object().set_auto_download(True)
            elif auto_download == "off":
                MANAGER.current_object().set_auto_download(False)
            else:
                print("please input on or off")
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide 'on' or 'off'. {e}")
        except Exception as e:
            print(f"Error setting auto download: {e}")

    def do_config(self, _: str) -> None:
        """Edit configuration."""
        try:
            shell.config()
        except Exception as e:
            print(f"Error accessing config: {e}")

    def do_submit(self, arg: str) -> None:
        """Submit current object."""
        try:
            if arg == "":
                shell.submit()
            else:
                obj = arg.split()[0]
                shell.submit(obj)
        except Exception as e:
            print(f"Error submitting: {e}")

    def do_kill(self, _: str) -> None:
        """Kill current object process."""
        try:
            MANAGER.current_object().kill()
        except Exception as e:
            print(f"Error killing process: {e}")

    def do_runners(self, _: str) -> None:
        """Show available runners."""
        try:
            shell.runners()
        except Exception as e:
            print(f"Error showing runners: {e}")

    def do_register_runner(self, arg: str) -> None:
        """Register a new runner."""
        try:
            args = arg.split()
            runner = args[0]
            url = args[1]
            secret = args[2]
            shell.register_runner(runner, url, secret)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide runner name, URL, and secret. {e}")
        except Exception as e:
            print(f"Error registering runner: {e}")

    def do_remove_runner(self, arg: str) -> None:
        """Remove a runner."""
        try:
            obj = arg.split()[0]
            shell.remove_runner(obj)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a runner name. {e}")
        except Exception as e:
            print(f"Error removing runner: {e}")
