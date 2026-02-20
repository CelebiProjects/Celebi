"""
Environment and Execution Command Handlers for Chern Shell.

This module contains command handlers for environment settings
and job execution management.
"""
# pylint: disable=broad-exception-caught
from ...interface import shell
from ...interface.ChernManager import get_manager


MANAGER = get_manager()


class EnvironmentCommands:
    """Mixin class providing environment and execution command handlers."""

    def do_set_environment(self, arg: str) -> None:
        """Set environment for current object."""
        try:
            environment = arg.split()[0]
            result = shell.set_environment(environment)
            if result.messages:
                print(result.colored())
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide an environment name. {e}")
        except Exception as e:
            print(f"Error setting environment: {e}")

    def do_setenv(self, arg: str) -> None:
        """Set environment for current object (alias for set-environment)."""
        try:
            environment = arg.split()[0]
            result = shell.set_environment(environment)
            if result.messages:
                print(result.colored())
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide an environment name. {e}")
        except Exception as e:
            print(f"Error setting environment: {e}")

    def do_set_memory_limit(self, arg: str) -> None:
        """Set memory limit for current object."""
        try:
            memory_limit = arg.split()[0]
            result = shell.set_memory_limit(memory_limit)
            if result.messages:
                print(result.colored())
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a memory limit. {e}")
        except Exception as e:
            print(f"Error setting memory limit: {e}")

    def do_auto_download(self, arg: str) -> None:
        """Enable or disable auto download."""
        try:
            auto_download = arg.split()[0]
            if auto_download == "on":
                MANAGER.current_object().set_auto_download(True)
            elif auto_download == "off":
                MANAGER.current_object().set_auto_download(False)
            else:
                print("please input on or off")
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide 'on' or 'off'. {e}")
        except Exception as e:
            print(f"Error setting auto download: {e}")

    def do_use_eos(self,  arg: str) -> None:
        """Enable or disable EOS usage."""
        try:
            use_eos = arg.split()[0]
            if use_eos == "on":
                MANAGER.current_object().set_use_eos(True)
            elif use_eos == "off":
                MANAGER.current_object().set_use_eos(False)
            else:
                print("please input on or off")
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide 'on' or 'off'. {e}")
        except Exception as e:
            print(f"Error setting EOS usage: {e}")

    def do_request_runner(self, arg: str) -> None:
        """Request a runner for current object."""
        try:
            runner = arg.split()[0]
            result = shell.request_runner(runner)
            if result.messages:
                print(result.colored())
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a runner name. {e}")
        except Exception as e:
            print(f"Error requesting runner: {e}")

    def do_config(self, _: str) -> None:
        """Edit configuration."""
        try:
            result = shell.config()
            if result.messages:
                print(result.colored())
        except Exception as e:
            print(f"Error accessing config: {e}")

    def do_submit(self, arg: str) -> None:
        """Submit current object."""
        try:
            if not arg:
                result = shell.submit()
            else:
                obj = arg.split()[0]
                result = shell.submit(obj)
            if result.messages:
                print(result.colored())
        except Exception as e:
            print(f"Error submitting: {e}")

    def do_purge_impressions(self, _: str) -> None:
        """Purge impressions current object."""
        try:
            # Ask for confirmation
            answer = input("Are you sure you want to purge impressions? This action cannot be undone. (N/y): ") # pylint: disable=line-too-long
            if answer.lower() != 'y':
                print("Purge impressions cancelled.")
                return
            result = shell.purge()
            if result.messages:
                print(result.colored())
        except Exception as e:
            print(f"Error purge: {e}")

    def do_purge_old_impressions(self, _: str) -> None:
        """Purge old impressions of current object."""
        try:
            # Ask for confirmation
            answer = input("Are you sure you want to purge old impressions? This action cannot be undone. (N/y): ") # pylint: disable=line-too-long
            if answer.lower() != 'y':
                print("Purge old impressions cancelled.")
                return
            result = shell.purge_old_impressions()
            if result.messages:
                print(result.colored())
        except Exception as e:
            print(f"Error purging old impressions: {e}")



    def do_kill(self, _: str) -> None:
        """Kill current object process."""
        try:
            MANAGER.current_object().kill()
        except Exception as e:
            print(f"Error killing process: {e}")

    def do_runners(self, _: str) -> None:
        """Show available runners."""
        try:
            print(shell.runners().colored())
        except Exception as e:
            print(f"Error showing runners: {e}")

    def do_register_runner(self, _: str) -> None:
        """Register a runner with default values if input is empty."""

        # Define your defaults here
        defaults = {
            "runner": "default-runner",
            "url": "http://localhost:8080",
            "secret": "fallback-secret-123",
            "backend_type": "reana"
        }

        try:
            # Prompt user: if they press Enter without typing, it uses the default
            runner = input(f"Enter runner name [{defaults['runner']}]: ").strip() \
                        or defaults['runner']
            url = input(f"Enter URL [{defaults['url']}]: ").strip() \
                    or defaults['url']
            secret = input(f"Enter secret [{defaults['secret']}]: ").strip() \
                    or defaults['secret']
            backend_type = input("Enter backend type [optional]: ").strip() \
                    or defaults['backend_type']

            result = shell.register_runner(runner, url, secret, backend_type)
            if result.messages:
                print(result.colored())

        except EOFError:
            print("\nOperation cancelled.")
        except Exception as e:
            print(f"Error: {e}")

    def do_remove_runner(self, arg: str) -> None:
        """Remove a runner."""
        try:
            obj = arg.split()[0]
            result = shell.remove_runner(obj)
            if result.messages:
                print(result.colored())
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a runner name. {e}")
        except Exception as e:
            print(f"Error removing runner: {e}")
