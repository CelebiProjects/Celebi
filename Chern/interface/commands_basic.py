"""
Basic Operations Command Handlers for Chern Shell.

This module contains command handlers for basic object operations.
"""
# pylint: disable=broad-exception-caught
from ..interface import shell
from ..interface.ChernManager import get_manager


MANAGER = get_manager()


class BasicCommands:
    """Mixin class providing basic operation command handlers."""

    def do_ls(self, _: str) -> None:
        """List contents of current object."""
        try:
            message = MANAGER.current_object().ls()
            print(message.colored())
        except Exception as e:
            print(f"Error listing contents: {e}")

    def do_status(self, _: str) -> None:
        """Show status of current object."""
        try:
            print(shell.status().colored())
        except Exception as e:
            print(f"Error showing status: {e}")

    def do_collect(self, _: str) -> None:
        """Collect data for current object."""
        try:
            MANAGER.current_object().collect()
        except Exception as e:
            print(f"Error collecting data: {e}")

    def do_display(self, arg: str) -> None:
        """Display a file from current object."""
        try:
            filename = arg.split()[0]
            MANAGER.current_object().display(filename)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a filename. {e}")
        except Exception as e:
            print(f"Error displaying file: {e}")

    def do_cat(self, arg: str) -> None:
        """Display file contents."""
        try:
            MANAGER.current_object().cat(arg)
        except Exception as e:
            print(f"Error displaying file: {e}")
