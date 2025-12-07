"""
Documentation and Impression Command Handlers for Chern Shell.

This module contains command handlers for documentation, help,
and impression management.
"""
# pylint: disable=broad-exception-caught
from ..interface import shell
from ..interface.ChernManager import get_manager


MANAGER = get_manager()


class DocumentationCommands:
    """Mixin class providing documentation command handlers."""

    def do_comment(self, arg: str) -> None:
        """Add a comment to current object."""
        try:
            MANAGER.current_object().comment(arg)
        except Exception as e:
            print(f"Error adding comment: {e}")

    def do_edit_readme(self, _: str) -> None:
        """Edit README for current object."""
        try:
            MANAGER.current_object().edit_readme()
        except Exception as e:
            print(f"Error editing README: {e}")

    def do_edit_script(self, arg: str) -> None:
        """Edit a script file."""
        try:
            obj = arg.split()[0]
            shell.edit_script(obj)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a script name. {e}")
        except Exception as e:
            print(f"Error editing script: {e}")

    def do_helpme(self, arg: str) -> None:
        """Get help for current object."""
        try:
            print(MANAGER.current_object().helpme(arg).colored())
        except Exception as e:
            print(f"Error getting help: {e}")

    def do_impress(self, _: str) -> None:
        """Create impression of current object."""
        try:
            MANAGER.current_object().impress()
        except Exception as e:
            print(e)

    def do_impression(self, _: str) -> None:
        """Get impression of current object."""
        try:
            impression = MANAGER.current_object().impression()
            print(impression)
        except Exception as e:
            print(f"Error getting impression: {e}")

    def do_view(self, arg: str) -> None:
        """View impressions."""
        try:
            if arg != "":
                shell.view(arg)
            else:
                shell.view()
        except Exception as e:
            print(f"Error viewing impressions: {e}")

    def do_clean_impressions(self, _: str) -> None:
        """Clean impressions (developer only)."""
        try:
            print("Very dangerous operation only for developer")
            print("cleaning impression")
            MANAGER.current_object().clean_impressions()
        except Exception as e:
            print(f"Error cleaning impressions: {e}")
