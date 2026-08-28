"""Command execution module for Chern shell."""
from ..shell_modules.execution_management import test, ssh_test, engine_logs

class CommandsExecution:
    """Execution commands for Chern shell."""
    def do_test(self, arg):
        """
        Execute a test workflow.

        Usage:
            test docker <docker_image> <command>
            test ssh <runner>

        Examples:
            test docker ubuntu:latest ls -l
            test ssh mycluster
        """
        args = arg.split()
        if not args:
            print("Error: Missing arguments. "
                  "Usage: test docker <docker_image> <command> | "
                  "test ssh <runner>")
            return

        if args[0] == "ssh":
            if len(args) < 2:
                print("Error: Missing runner name. Usage: test ssh <runner>")
                return
            try:
                result = ssh_test(args[1])
                if result.messages:
                    print(result.colored())
            except Exception as e:
                print(f"Error running ssh test: {e}")
            return

        if args[0] == "docker":
            if len(args) < 3:
                print("Error: Missing arguments. "
                      "Usage: test docker <docker_image> <command>")
                return
            test()
            return

        print(f"Error: Unknown test mode '{args[0]}'. "
              "Usage: test docker <docker_image> <command> | "
              "test ssh <runner>")

    def do_engine_logs(self, arg):
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
            result = engine_logs(fetch="--fetch" in arg.split())
            if result.messages:
                print(result.colored())
        except Exception as e:
            print(f"Error fetching engine logs: {e}")
