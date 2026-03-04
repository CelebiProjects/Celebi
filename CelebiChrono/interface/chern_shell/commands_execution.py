"""Command execution module for Chern shell."""
from ..shell_modules.execution_management import test, engine_logs

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

    def do_engine_logs(self, _arg):
        """
        Fetch and display engine logs for the current task.

        Retrieves documented engine logs from the DITE server for the current
        task's impression. Engine logs provide detailed information about the
        execution environment, workflow engine operations, and runtime events.

        Usage:
            engine-logs

        Examples:
            engine-logs    # Display engine logs for current task

        Note:
            - Must be used within a task context
            - Requires connection to DITE server
            - Useful for debugging execution issues
        """
        try:
            result = engine_logs()
            if result.messages:
                print(result.colored())
        except Exception as e:
            print(f"Error fetching engine logs: {e}")
