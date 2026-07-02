"""
Environment and Execution Command Handlers for Chern Shell.

This module contains command handlers for environment settings
and job execution management.
"""
# pylint: disable=broad-exception-caught
from ...interface import shell
from ...interface.ChernManager import get_manager


MANAGER = get_manager()


def _parse_update_runner_args(arg: str):
    """Parse update-runner shell argument into (name, kwargs).

    Returns (name, kwargs). Either may be None/empty to signal a user error.
    """
    parts = arg.split()
    kwargs = {}
    name = None
    i = 0
    while i < len(parts):
        if parts[i] == "--url" and i + 1 < len(parts):
            kwargs["url"] = parts[i + 1]
            i += 2
        elif parts[i] == "--token" and i + 1 < len(parts):
            kwargs["token"] = parts[i + 1]
            i += 2
        elif parts[i] == "--backend-type" and i + 1 < len(parts):
            kwargs["backend_type"] = parts[i + 1]
            i += 2
        elif parts[i] == "--use-kerberos":
            kwargs["use_kerberos"] = True
            i += 1
        elif parts[i] == "--no-use-kerberos":
            kwargs["use_kerberos"] = False
            i += 1
        elif parts[i] == "--eos-mount-point" and i + 1 < len(parts):
            kwargs["eos_mount_point"] = parts[i + 1]
            i += 2
        elif parts[i].startswith("--"):
            i += 1
        elif name is None:
            name = parts[i]
            i += 1
        else:
            i += 1
    return name, kwargs


def _parse_submit_args(arg: str):
    """Parse submit shell argument into (runner, object_names).

    Syntax:
        submit                     -> runner="local", object_names=[]
        submit --runner cern       -> runner="cern", object_names=[]
        submit --runner cern a b   -> runner="cern", object_names=["a", "b"]
        submit a b                 -> runner="local", object_names=["a", "b"]

    The --runner flag is optional. Any positional arguments after the
    runner (if provided) are treated as object names.
    """
    parts = arg.split()
    if "--runner" in parts:
        ridx = parts.index("--runner")
        runner = parts[ridx + 1] if ridx + 1 < len(parts) else "local"
        object_names = parts[:ridx] + parts[ridx + 2:]
        return runner, object_names
    return "local", parts


class EnvironmentCommands:
    """Mixin class providing environment and execution command handlers."""
    # pylint: disable=too-many-public-methods

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

    def do_set_descriptor(self, arg: str) -> None:
        """Set descriptor for current task or algorithm."""
        try:
            descriptor = arg.split()[0]
            result = shell.set_descriptor(descriptor)
            if result.messages:
                print(result.colored())
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a descriptor. {e}")
        except Exception as e:
            print(f"Error setting descriptor: {e}")

    def do_setdescriptor(self, arg: str) -> None:
        """Set descriptor for current task or algorithm (alias for set-descriptor)."""
        self.do_set_descriptor(arg)

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
        """Submit current object or named sub-objects.

        Usage:
            submit
            submit --runner cern
            submit --runner cern a b
            submit a b
        """
        try:
            runner, object_names = _parse_submit_args(arg)
            if not object_names:
                result = shell.submit(runner)
            else:
                result = shell.submit_objects(object_names, runner)
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

    def do_update_runner(self, arg: str) -> None:
        """Update settings for an existing runner.

        Usage: update-runner <name> [--url URL] [--token TOKEN]
               [--backend-type TYPE] [--use-kerberos] [--no-use-kerberos]
               [--eos-mount-point PATH]
        """
        usage = (
            "Usage: update-runner <name> [--url URL] [--token TOKEN] "
            "[--backend-type TYPE] [--use-kerberos] [--no-use-kerberos] "
            "[--eos-mount-point PATH]"
        )
        try:
            name, kwargs = _parse_update_runner_args(arg)

            if name is None:
                print("Error: Please provide a runner name.")
                print(usage)
                return
            if not kwargs:
                print("Error: No settings provided to update.")
                print(usage)
                return
            result = shell.update_runner(name, **kwargs)
            if result.messages:
                print(result.colored())
        except Exception as e:
            print(f"Error updating runner: {e}")

    def do_booking_server(self, _arg: str) -> None:
        """Check the registered booking server URL and status.

        Usage: booking-server
        """
        try:
            result = shell.check_booking_server()
            if result.messages:
                print(result.colored())
        except Exception as e:
            print(f"Error checking booking server: {e}")

    def do_register_booking_server(self, arg: str) -> None:
        """Register REANA server and token with Yuki.

        Usage: register-booking-server [--server URL] [--token TOKEN]
        """
        try:
            args = arg.split() if arg else []
            server_url = ""
            access_token = ""
            i = 0
            while i < len(args):
                if args[i] == "--server" and i + 1 < len(args):
                    server_url = args[i + 1]
                    i += 2
                elif args[i] == "--token" and i + 1 < len(args):
                    access_token = args[i + 1]
                    i += 2
                else:
                    i += 1
            result = shell.register_booking_server(server_url, access_token)
            if result.messages:
                print(result.colored())
        except Exception as e:
            print(f"Error registering booking server: {e}")

    def do_book_reana(self, arg: str) -> None:
        """Book current project to REANA.

        Usage: book-reana [--server URL] [--token TOKEN] [--insecure]
                          [--upload MODE] [--stageout] [--no-stream]
        """
        try:
            args = arg.split() if arg else []
            server_url = ""
            access_token = ""
            verify_ssl = True
            stageout = False
            upload = "plots+logs"
            stream = True
            i = 0
            while i < len(args):
                if args[i] == "--server" and i + 1 < len(args):
                    server_url = args[i + 1]
                    i += 2
                elif args[i] == "--token" and i + 1 < len(args):
                    access_token = args[i + 1]
                    i += 2
                elif args[i] == "--insecure":
                    verify_ssl = False
                    i += 1
                elif args[i] == "--upload" and i + 1 < len(args):
                    upload = args[i + 1]
                    i += 2
                elif args[i] == "--stageout":
                    stageout = True
                    i += 1
                elif args[i] == "--no-stream":
                    stream = False
                    i += 1
                else:
                    i += 1
            result = shell.book_reana(
                server_url, access_token, verify_ssl,
                stageout=stageout, upload=upload, stream=stream
            )
            # In streaming mode, messages were already printed live.
            if stream:
                pass
            elif result.messages:
                print(result.colored())
        except Exception as e:
            print(f"Error booking to REANA: {e}")

    def do_add_host(self, arg: str) -> None:
        """Add a host to the communicator."""
        try:
            args = arg.split()
            host = args[0]
            url = args[1]
            result = shell.add_host(host, url)
            if result.messages:
                print(result.colored())
        except (IndexError, ValueError) as e:
            print(f"Error: Please provide a host name and URL. {e}")
        except Exception as e:
            print(f"Error adding host: {e}")

    def do_hosts(self, _: str) -> None:
        """List all hosts and their status."""
        try:
            result = shell.hosts()
            if result.messages:
                print(result.colored())
        except Exception as e:
            print(f"Error listing hosts: {e}")
