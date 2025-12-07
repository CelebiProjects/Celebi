"""
Base Shell Module for Chern.

This module provides the core functionality for the Chern interactive shell,
including initialization, prompt management, command parsing, and completion.
"""
# pylint: disable=broad-exception-caught,import-outside-toplevel
import cmd
import os
from ..utils import csys
from ..utils.metadata import YamlFile


class ChernShellBase(cmd.Cmd):
    """Base class for Chern Shell with core functionality."""

    intro = ''
    prompt = '[Celebi]'
    file = None
    readline_file = None

    def __init__(self):
        """Initialize the shell and set custom completer delimiters."""
        super().__init__()

    def init(self, manager) -> None:
        """Initialize the shell with current project context."""
        current_project_name = manager.get_current_project()
        current_project_path = manager.get_project_path(current_project_name)
        from ..kernel.vproject import VProject
        manager.p = VProject(current_project_path)
        manager.c = manager.p
        os.chdir(current_project_path)
        self.readline_file = YamlFile(
            os.path.join(os.environ["HOME"], ".chern", "readline.yaml")
        )

    def preloop(self) -> None:
        """Set up the prompt before entering the command loop."""
        # Treat the dash as part of a command name for completion
        import readline
        # Get the default delimiters
        delims = readline.get_completer_delims()

        # Remove characters that appear inside environment names
        for char in ['-', ':', '/', '.']:
            delims = delims.replace(char, '')
        readline.set_completer_delims(delims)

        from .ChernManager import get_manager
        manager = get_manager()
        current_project_name = manager.get_current_project()
        current_path = os.path.relpath(
            manager.c.path, csys.project_path(manager.c.path)
        )
        self.prompt = f"[Celebi][{current_project_name}][{current_path}]\n>>>> "

    def cmdloop(self, intro=None):
        """Keep tab completion and catch Ctrl-C during input"""
        while True:
            try:
                # Call the original cmdloop() to preserve readline & completion
                return super().cmdloop(intro)
            except KeyboardInterrupt:
                # This catches Ctrl-C during typing (inside readline)
                print("^C")
                # restart the loop (this re-enters cmdloop, preserving state)
                intro = None
                continue

    def parseline(self, line: str) -> tuple[str, str, str]:
        """Parse a command line input."""
        # Split the line to isolate the command name
        parts = line.strip().split(maxsplit=1)
        if not parts:
            return None, None, line

        command = parts[0].replace('-', '_')  # Replace only in command
        rest = parts[1] if len(parts) > 1 else ""

        # Recombine for superclass parsing
        command, arg, line = super().parseline(f"{command} {rest}".strip())
        return command, arg, line

    def completenames(self, text, *ignored):
        """Complete command names based on user input."""
        matches = []

        # Get all method names that start with 'do_'
        for name in self.get_names():
            if name.startswith("do_"):
                # Convert do_create_task to create-task
                command_name = name[3:].replace('_', '-')
                if command_name.startswith(text):
                    matches.append(command_name)

        return matches

    # pylint: disable=arguments-differ,too-many-nested-blocks
    def completedefault(self, text, _line, _begidx, endidx):
        """Default completion handler for commands that don't exist."""
        # Check if we're still typing the first word (no spaces)
        if ' ' not in _line.strip():
            # Get the full command being typed so far
            full_command = _line[:endidx].strip()

            # Get all matching commands
            all_matches = self.completenames(full_command)

            if all_matches:
                results = []
                for match in all_matches:
                    if match.startswith(full_command):
                        # Calculate the suffix after cursor position
                        text_start_pos = (
                            full_command.rfind(text) if text
                            else len(full_command)
                        )

                        if text_start_pos >= 0:
                            # Return the part of the match after the text
                            suffix = match[text_start_pos:]
                            if suffix:
                                results.append(suffix)
                        elif match == full_command:
                            # Exact match, add space
                            results.append(' ')
                return results

        return []

    def emptyline(self) -> None:
        """Handle empty line input."""

    def do_EOF(self, _: str) -> bool:  # pylint: disable=invalid-name
        """Handle EOF (Ctrl+D) to exit shell."""
        print("")
        print("Thank you for using Celebi")
        print(
            "Contact Mingrui Zhao (mingrui.zhao@mail.labz0.org) "
            "for any questions"
        )
        return True

    def get_completions(
        self, current_path: str, filepath: str, _line: str
    ) -> list:
        """Get command completions for file paths."""
        # Calculate the full path to look in
        full_search_path = os.path.join(current_path, filepath)

        # Separate the directory user typed from the file prefix
        user_dir = os.path.dirname(filepath)
        dirname = os.path.dirname(full_search_path)
        basename = os.path.basename(full_search_path)

        if os.path.exists(dirname):
            # Get all files in that directory
            candidates = [
                f for f in os.listdir(dirname) if not f.startswith('.chern')
            ]

            # Filter for matches
            matches = [f for f in candidates if f.startswith(basename)]

            # If the user typed a directory, prepend it to results
            if user_dir:
                return [os.path.join(user_dir, m) for m in matches]

            return matches

        return []

    def get_completions_out(self, abspath: str, line: str) -> list:
        """Get command completions for absolute paths."""
        if os.path.exists(abspath):
            listdir = os.listdir(abspath)
            if line.endswith("/"):
                return listdir
            return []

        basename = os.path.basename(abspath)
        dirname = os.path.dirname(abspath)
        if os.path.exists(dirname):
            listdir = os.listdir(dirname)
            completions = [f for f in listdir if f.startswith(basename)]
            return completions
        return []
