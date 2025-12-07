"""
Navigation Command Handlers for Chern Shell.

This module contains command handlers for navigation operations.
"""
# pylint: disable=broad-exception-caught,no-member,import-outside-toplevel
import os
from ..interface import shell
from ..interface.ChernManager import get_manager


MANAGER = get_manager()


class NavigationCommands:
    """Mixin class providing navigation command handlers."""

    def do_cd_project(self, arg: str) -> None:
        """Switch project."""
        try:
            project = arg.split()[0]
            shell.cd_project(project)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a project name. {e}")

    def do_cd(self, arg: str) -> None:
        """Switch directory or object."""
        try:
            from ..utils import csys
            myobject = arg.split()[0]
            shell.cd(myobject)
            current_project_name = MANAGER.get_current_project()
            current_path = os.path.relpath(
                MANAGER.c.path, csys.project_path(MANAGER.c.path)
            )
            # pylint: disable=attribute-defined-outside-init
            self.prompt = (
                f"[Celebi][{current_project_name}][{current_path}]\n>>>> "
            )
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a directory or object name. {e}")
        except Exception as e:
            print(f"Error changing directory: {e}")

    def do_ls_projects(self, _: str) -> None:
        """List all projects."""
        try:
            MANAGER.ls_projects()
        except Exception as e:
            print(f"Error listing projects: {e}")
