"""
Advanced Developer Tools Command Handlers for Chern Shell.

This module contains command handlers for advanced operations,
debugging, and system integration.
"""
# pylint: disable=broad-exception-caught
import os
from ...interface import shell
from ...interface.ChernManager import get_manager


MANAGER = get_manager()


class AdvancedCommands:
    """Mixin class providing advanced and developer command handlers."""

    def do_send(self, arg: str) -> None:
        """
        Send a file or path.

        Parameters
        ----------
        arg : str
            Path to the file or directory to send.
        """
        try:
            obj = arg.split()[0]
            result = shell.send(obj)
            if result.messages:
                print(result.colored())
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a path to send. {e}")
        except Exception as e:
            print(f"Error sending: {e}")

    def do_dite(self, _: str) -> None:
        """
        Show DITE information.
        """
        try:
            print(shell.dite().colored())
        except Exception as e:
            print(f"Error accessing DITE: {e}")

    def do_set_dite(self, arg: str) -> None:
        """
        Set DITE url.

        Parameters
        ----------
        arg : str
            The DITE URL to set.
        """
        try:
            url = arg.split()[0]
            result = shell.set_dite(url)
            if result.messages:
                print(result.colored())
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a DITE URL. {e}")
        except Exception as e:
            print(f"Error setting DITE URL: {e}")

    def do_danger_call(self, arg: str) -> None:
        """
        Dangerous call to execute a command directly.

        Parameters
        ----------
        arg : str
            The command to execute.
        """
        try:
            cmd = arg
            result = shell.danger_call(cmd)
            if result.messages:
                print(result.colored())
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a command to execute. {e}")
        except Exception as e:
            print(f"Error executing command: {e}")

    def do_workaround(self, arg):
        """
        Workaround to test/debug the task.

        Parameters
        ----------
        arg : str
            Optional argument. If 'docker', runs task in Docker container.
        """
        try:
            result = shell.workaround_preshell()
            if not result.success:
                print(result.colored())
                return
            info = result.data["path"]
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
            print("Before postshell")
            os.chdir(path)
            # Ask whether to run postshell
            # Apply the changes made to the code? (y/n):
            answer = input("Apply the changes made to the code? (y/n): ").strip().lower()
            if answer == "y":
                shell.workaround_postshell(info)
            # Switch back to the original path
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a command to execute. {e}")
        except Exception as e:
            print(f"Error executing command: {e}")

    def do_trace(self, arg):
        """
        Trace the execution of the current task.

        Parameters
        ----------
        arg : str
            Optional object name to trace.
        """
        try:
            obj = arg.split()[0] if arg else None
            result = shell.trace(obj)
            if result.messages:
                print(result.colored())
        except Exception as e:
            print(f"Error tracing execution: {e}")

    def do_history(self, _arg):
        """
        Print the history of the current object.
        """
        try:
            print(shell.history().colored())
        except Exception as e:
            print(f"Error printing history: {e}")

    def do_changes(self, _arg):
        """
        Print the changes.
        """
        try:
            print(shell.changes().colored())
        except Exception as e:
            print(f"Error printing changes: {e}")

    def do_watermark(self, _arg):
        """
        Set the watermark.
        """
        try:
            print(shell.watermark().colored())
        except Exception as e:
            print(f"Error handling watermark: {e}")

    def do_system_shell(self, _arg):
        """
        Enter a system shell (bash). Type 'exit' or Ctrl-D to return.
        """
        print("Entering system shell. Type 'exit' to return.\n")

        try:
            os.system(os.environ.get("SHELL", "/bin/bash"))
        finally:
            pass

        print("\nReturned to Chern Shell.")

    def do_doctor(self, _arg):
        """
        Run system diagnostics.
        """
        try:
            print(shell.doctor().colored())
        except Exception as e:
            print(f"Error running diagnostics: {e}")

    def do_add_source(self, arg: str) -> None:
        """Add a source file or directory to current object."""
        try:
            path = arg.split()[0]
            result = shell.add_source(path)
            if result.messages:
                print(result.colored())
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a source path. {e}")
        except Exception as e:
            print(f"Error adding source: {e}")
