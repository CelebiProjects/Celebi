"""
Completion Handlers Module for Chern Shell.

This module contains all command completion methods (complete_* methods)
for tab-completion functionality in the Chern Shell.

Note: This is a mixin class. Methods reference `self.get_completions`,
`self.get_completions_out`, and `self.readline_file` which are provided
by ChernShellBase when this mixin is combined with it in ChernShell.
"""
# pylint: disable=broad-exception-caught,no-member
from ..interface.ChernManager import get_manager
from ..utils import csys


MANAGER = get_manager()


# pylint: disable=too-many-public-methods
class ChernShellCompletions:
    """Mixin class providing all completion handlers for Chern Shell."""

    def complete_cd(
        self, _: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete cd command with available paths."""
        current_path = MANAGER.c.path
        filepath = csys.strip_path_string(line[3:])
        return self.get_completions(current_path, filepath, line)

    def complete_mv(
        self, _: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete mv command with available paths."""
        current_path = MANAGER.c.path
        filepath = csys.strip_path_string(line[3:])
        return self.get_completions(current_path, filepath, line)

    def complete_cp(
        self, _: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete cp command with available paths."""
        current_path = MANAGER.c.path
        filepath = csys.strip_path_string(line[3:])
        return self.get_completions(current_path, filepath, line)

    def complete_setenv(
        self, text: str, _line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete set_environment command with available environments."""
        # Get the list
        environments = self.readline_file.read_variable("environments", [])

        # Filter using 'text' (which contains the word currently being typed)
        matches = [env for env in environments if env.startswith(text)]

        return matches

    def complete_add_algorithm(
        self, text: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete add_algorithm command with available paths."""
        current_path = MANAGER.c.path
        # Use 'text' instead of slicing 'line'
        return self.get_completions(current_path, text, line)

    def complete_add_input(
        self, text: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete add_input command with available paths."""
        current_path = MANAGER.c.path
        # Use 'text' instead of slicing 'line'
        return self.get_completions(current_path, text, line)

    def complete_add_multi_inputs(
        self, _: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete add_input command with available paths."""
        current_path = MANAGER.c.path
        filepath = csys.strip_path_string(line[16:])
        return self.get_completions(current_path, filepath, line)

    def complete_remove_input(
        self, text: str, _line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete remove_input command with available aliases."""
        if not MANAGER.c.is_task_or_algorithm():
            return []
        alias = MANAGER.c.get_alias_list()
        if text == "":
            return list(alias)
        return [f for f in alias if f.startswith(text)]

    def complete_submit(
        self, _: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete submit command with readline file"""
        runners = self.readline_file.read_variable("runners", [])
        if line.strip() == "submit":
            return runners
        matches = []
        for runner in runners:
            if runner.startswith(line.strip().split()[-1]):
                matches.append(runner)
        return matches

    def complete_import_file(
        self, _: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete import_file command with available paths."""
        filepath = csys.strip_path_string(line[12:])
        return self.get_completions_out(filepath, line)

    def complete_view(
        self, _: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete view command with [browsers] option"""
        options = ["firefox", "chrome", "safari", "edge", "browsers"]
        if line.strip() == "view":
            return options
        for option in options:
            if option.startswith(line.strip().split()[-1]):
                return [option]
        return []

    # ====================================================================
    # File and Directory Completions
    # ====================================================================

    def complete_mkdir(
        self, _: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete mkdir command with available paths."""
        current_path = MANAGER.c.path
        filepath = csys.strip_path_string(line[6:])
        return self.get_completions(current_path, filepath, line)

    def complete_rm(
        self, _: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete rm command with available paths."""
        current_path = MANAGER.c.path
        filepath = csys.strip_path_string(line[3:])
        return self.get_completions(current_path, filepath, line)

    def complete_import(
        self, _: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete import command with available paths."""
        filepath = csys.strip_path_string(line[7:])
        return self.get_completions_out(filepath, line)

    def complete_rm_file(
        self, _: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete rm_file command with files in current object."""
        current_path = MANAGER.c.path
        filepath = csys.strip_path_string(line[8:])
        return self.get_completions(current_path, filepath, line)

    def complete_mv_file(
        self, _: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete mv_file command with files in current object."""
        current_path = MANAGER.c.path
        filepath = csys.strip_path_string(line[8:])
        return self.get_completions(current_path, filepath, line)

    def complete_export(
        self, _: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete export command with files in current object."""
        current_path = MANAGER.c.path
        filepath = csys.strip_path_string(line[7:])
        return self.get_completions(current_path, filepath, line)

    def complete_display(
        self, _: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete display command with files in current object."""
        current_path = MANAGER.c.path
        filepath = csys.strip_path_string(line[8:])
        return self.get_completions(current_path, filepath, line)

    def complete_cat(
        self, _: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete cat command with files in current object."""
        current_path = MANAGER.c.path
        filepath = csys.strip_path_string(line[4:])
        return self.get_completions(current_path, filepath, line)

    # ====================================================================
    # Task and Object Completions
    # ====================================================================

    def complete_create_task(
        self, _: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete create_task command with available paths."""
        current_path = MANAGER.c.path
        filepath = csys.strip_path_string(line[12:])
        return self.get_completions(current_path, filepath, line)

    def complete_create_algorithm(
        self, _: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete create_algorithm command with available paths."""
        current_path = MANAGER.c.path
        filepath = csys.strip_path_string(line[17:])
        return self.get_completions(current_path, filepath, line)

    def complete_create_data(
        self, _: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete create_data command with available paths."""
        current_path = MANAGER.c.path
        filepath = csys.strip_path_string(line[12:])
        return self.get_completions(current_path, filepath, line)

    def complete_input(
        self, text: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete input command with available paths."""
        current_path = MANAGER.c.path
        return self.get_completions(current_path, text, line)

    def complete_send(
        self, _: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete send command with available paths."""
        current_path = MANAGER.c.path
        filepath = csys.strip_path_string(line[5:])
        return self.get_completions(current_path, filepath, line)

    # ====================================================================
    # Environment Completions
    # ====================================================================

    def complete_set_environment(
        self, text: str, _line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete set_environment command with available environments."""
        environments = self.readline_file.read_variable("environments", [])
        matches = [env for env in environments if env.startswith(text)]
        return matches

    def complete_auto_download(
        self, text: str, _line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete auto_download command with on/off options."""
        options = ["on", "off"]
        return [opt for opt in options if opt.startswith(text)]

    def complete_register_runner(
        self, text: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete register_runner command with existing runners."""
        runners = self.readline_file.read_variable("runners", [])
        parts = line.split()
        if len(parts) == 1 or (len(parts) == 2 and not line.endswith(" ")):
            # Completing runner name
            return [r for r in runners if r.startswith(text)]
        return []

    def complete_remove_runner(
        self, text: str, _line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete remove_runner command with existing runners."""
        runners = self.readline_file.read_variable("runners", [])
        return [r for r in runners if r.startswith(text)]

    # ====================================================================
    # Script and Documentation Completions
    # ====================================================================

    def complete_edit_script(
        self, _: str, line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete edit_script command with script files."""
        current_path = MANAGER.c.path
        filepath = csys.strip_path_string(line[12:])
        return self.get_completions(current_path, filepath, line)

    def complete_remove_parameter(
        self, text: str, _line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete remove_parameter with existing parameters."""
        if not MANAGER.c.is_task_or_algorithm():
            return []
        try:
            params = MANAGER.c.get_parameter_list()
            return [p for p in params if p.startswith(text)]
        except Exception:
            return []

    # ====================================================================
    # Workaround Completions
    # ====================================================================

    def complete_workaround(
        self, text: str, _line: str, _begidx: int, _endidx: int
    ) -> list:
        """Complete workaround command with docker option."""
        options = ["docker"]
        return [opt for opt in options if opt.startswith(text)]
