"""Command execution module for Chern shell."""
from ..shell_modules.execution_management import test

class CommandsExecution:  # pylint: disable=too-few-public-methods
    """Execution commands for Chern shell."""
    def do_test(self, arg):
        """
        Execute a test workflow.

        Usage:
            test <docker_image> <command>

        Examples:
            test ubuntu:latest ls -l
        """
        args = arg.split(maxsplit=1)
        if len(args) < 2:
            print("Error: Missing arguments. Usage: test <docker_image> <command>")
            return

        _docker_image, _command = args
        test()
