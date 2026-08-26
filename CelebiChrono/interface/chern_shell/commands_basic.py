"""
Basic Operations Command Handlers for Chern Shell.

This module contains command handlers for basic object operations.
"""
# pylint: disable=broad-exception-caught
from ...interface import shell
from ...interface.ChernManager import get_manager


MANAGER = get_manager()


def _parse_log_args(arg: str):
    """Parse `log` command arguments into (index, follow, poll_interval).

    Returns (None, follow, poll_interval) after printing an error when the
    first token is present but not a valid index.
    """
    tokens = arg.split()
    follow = "--follow" in tokens or "-f" in tokens
    poll_interval = 2.0
    if "-i" in tokens:
        pos = tokens.index("-i")
        if pos + 1 < len(tokens):
            poll_interval = float(tokens[pos + 1])
    elif "--poll-interval" in tokens:
        pos = tokens.index("--poll-interval")
        if pos + 1 < len(tokens):
            poll_interval = float(tokens[pos + 1])

    if tokens and tokens[0].isdigit():
        return int(tokens[0]), follow, poll_interval
    if tokens and not tokens[0].startswith("-"):
        print(f"Error: Please provide a valid log index. {tokens[0]}")
        return None, follow, poll_interval
    return 0, follow, poll_interval


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

    def do_successors(self, _: str) -> None:
        """List successors of current object."""
        try:
            message = shell.successors()
            print(message.colored())
        except Exception as e:
            print(f"Error listing successors: {e}")

    def do_predecessors(self, _: str) -> None:
        """List predecessors of current object."""
        try:
            message = shell.predecessors()
            print(message.colored())
        except Exception as e:
            print(f"Error listing predecessors: {e}")

    def do_collect(self, arg: str) -> None:
        """Collect results. Usage: collect [all|plots|data|logs|<glob>|<name>]"""
        try:
            result = shell.collect(arg.strip())
            if result.messages:
                print(result.colored())
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

    def do_imgcat(self, arg: str) -> None:
        """Display an image file inline in terminal."""
        try:
            filename = arg.strip() if arg else None
            result = shell.imgcat(filename)
            if result.messages:
                print(result.colored())
        except Exception as e:
            print(f"Error displaying image: {e}")

    def do_cat(self, arg: str) -> None:
        """Display file contents."""
        try:
            MANAGER.current_object().cat(arg)
        except Exception as e:
            print(f"Error displaying file: {e}")

    def do_tree(self, _arg: str) ->None:
        """Display directory tree structure."""
        print(shell.tree().colored())

    def do_short_ls(self, _: str) -> None:
        """Show short listing of current object."""
        try:
            result = shell.short_ls("")
            if result.messages:
                print(result.colored())
        except Exception as e:
            print(f"Error showing short listing: {e}")

    def do_jobs(self, _: str) -> None:
        """Show jobs for current algorithm or task."""
        try:
            result = shell.jobs("")
            if result.messages:
                print(result.colored())
        except Exception as e:
            print(f"Error showing jobs: {e}")

    def do_log(self, arg: str) -> None:
        """Show log for current object. Usage: log [index] [--follow] [-i SECONDS]

        With --follow, prints the current log and then polls for new content
        every interval (default 2s) until Ctrl-C.
        """
        try:
            index, follow, poll_interval = _parse_log_args(arg)
            if index is None:
                return
            if not follow:
                result = shell.error_log(index)
                output = result.colored()
                if output:
                    print(output, end="")
                else:
                    print("No log content found")
                return

            import time

            offset = 0
            while True:
                result = shell.error_log(index, offset=offset)
                output = result.colored()
                if output:
                    print(output, end="")
                    offset += len("".join(
                        text for text, _ in result.messages).encode("utf-8"))
                time.sleep(poll_interval)
        except Exception as e:
            print(f"Error showing error log: {e}")
