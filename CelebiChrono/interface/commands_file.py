"""
File Management Command Handlers for Chern Shell.

This module contains command handlers for file and directory operations.
"""
# pylint: disable=broad-exception-caught
from ..interface import shell
from ..interface.ChernManager import get_manager


MANAGER = get_manager()


class FileCommands:
    """Mixin class providing file management command handlers."""

    def do_mkdir(self, arg: str) -> None:
        """Create a new directory."""
        try:
            obj = arg.split()[0]
            shell.mkdir(obj)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a directory name. {e}")
        except Exception as e:
            print(f"Error creating directory: {e}")

    def do_mv(self, arg: str) -> None:
        """Move directory or object."""
        try:
            args = arg.split()
            source = args[0]
            destination = args[1]
            shell.mv(source, destination)
        except Exception as e:
            print(f"Error moving object: {e}")

    def do_cp(self, arg: str) -> None:
        """Copy directory or object."""
        try:
            args = arg.split()
            source = args[0]
            destination = args[1]
            shell.cp(source, destination)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide source and destination. {e}")
        except Exception as e:
            print(f"Error copying object: {e}")

    def do_rm(self, arg: str) -> None:
        """Remove an object."""
        try:
            obj = arg.split()[0]
            shell.rm(obj)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide an object to remove. {e}")
        except Exception as e:
            print(f"Error removing object: {e}")

    def do_import(self, arg: str) -> None:
        """Import a file into current object."""
        try:
            obj = arg.split()[0]
            shell.import_file(obj)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a file to import. {e}")
        except Exception as e:
            print(f"Error importing file: {e}")

    def do_import_file(self, arg: str) -> None:
        """Import a file into current object."""
        try:
            obj = arg.split()[0]
            shell.import_file(obj)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a file to import. {e}")
        except Exception as e:
            print(f"Error importing file: {e}")

    def do_rm_file(self, arg: str) -> None:
        """Remove files from current object."""
        try:
            objs = arg.split()
            for obj in objs:
                shell.rm_file(obj)
        except Exception as e:
            print(f"Error removing files: {e}")

    def do_mv_file(self, arg: str) -> None:
        """Move a file within current object."""
        try:
            args = arg.split()
            file1 = args[0]
            file2 = args[1]
            shell.mv_file(file1, file2)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide source and destination files. {e}")
        except Exception as e:
            print(f"Error moving file: {e}")

    def do_export(self, arg: str) -> None:
        """Export file to output path."""
        try:
            args = arg.split()
            filename = args[0]
            output_path = args[1]
            MANAGER.current_object().export(filename, output_path)
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide filename and output path. {e}")
        except Exception as e:
            print(f"Error exporting: {e}")
