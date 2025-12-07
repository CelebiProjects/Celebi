"""
Advanced Developer Tools Command Handlers for Chern Shell.

This module contains command handlers for advanced operations,
debugging, and system integration.
"""
# pylint: disable=broad-exception-caught
import os
from ..interface import shell
from ..interface.ChernManager import get_manager


MANAGER = get_manager()


class AdvancedCommands:
    """Mixin class providing advanced and developer command handlers."""

    def do_send(self, arg: str) -> None:
        """Send a file or path."""
        try:
            obj = arg.split()[0]
            shell.send(obj)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a path to send. {e}")
        except Exception as e:
            print(f"Error sending: {e}")

    def do_dite(self, _: str) -> None:
        """Show DITE information."""
        try:
            shell.dite()
        except Exception as e:
            print(f"Error accessing DITE: {e}")

    def do_danger_call(self, arg: str) -> None:
        """Dangerous call to execute a command directly."""
        try:
            cmd = arg
            shell.danger_call(cmd)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a command to execute. {e}")
        except Exception as e:
            print(f"Error executing command: {e}")

    def do_workaround(self, arg):
        """Workaround to test/debug the task."""
        try:
            status, info = shell.workaround_preshell()
            if not status:
                print(info)
                return
            # Remember the current path
            path = os.getcwd()
            # Switch to the ~
            os.chdir(info)
            # use docker if arg is docker
            if arg.strip() == "docker":
                os.system(
                    "docker run -it rootproject/root:6.36.00-ubuntu25.04 bash"
                )
            else:
                os.system(os.environ.get("SHELL", "/bin/bash"))
            shell.workaround_postshell()
            # Switch back to the original path
            os.chdir(path)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a command to execute. {e}")
        except Exception as e:
            print(f"Error executing command: {e}")

    def do_trace(self, arg):
        """Trace the execution of the current task."""
        try:
            obj = arg.split()[0] if arg else None
            shell.trace(obj)
        except Exception as e:
            print(f"Error tracing execution: {e}")

    def do_history(self, _arg):
        """Print the history of the current object."""
        try:
            print(shell.history().colored())
        except Exception as e:
            print(f"Error printing history: {e}")

    def do_changes(self, _arg):
        """Print the changes"""
        try:
            print(shell.changes().colored())
        except Exception as e:
            print(f"Error printing changes: {e}")

    def do_system_shell(self, _arg):
        """Enter a system shell (bash). Type 'exit' or Ctrl-D to return."""
        print("Entering system shell. Type 'exit' to return.\n")

        try:
            os.system(os.environ.get("SHELL", "/bin/bash"))
        finally:
            pass

        print("\nReturned to Chern Shell.")
