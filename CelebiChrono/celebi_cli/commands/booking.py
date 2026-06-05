"""Booking commands for celebi-cli."""
import click

from CelebiChrono.interface.shell_modules.reana_booking import (
    register_booking_server,
    book_reana,
    check_booking_server,
)


@click.command(name="booking-server")
def booking_server_command():
    """Check the registered booking server URL and status."""
    try:
        result = check_booking_server()
        if result.messages:
            print(result.colored())
    except Exception as e:
        print(f"Error: {e}")


@click.command(name="register-booking-server")
@click.option("--server", "server_url", default="",
              help="REANA server URL (or set REANA_SERVER_URL env var)")
@click.option("--token", "access_token", default="",
              help="REANA access token (or set REANA_ACCESS_TOKEN env var)")
def register_booking_server_command(server_url, access_token):
    """Register REANA server and token with Yuki for booking.

    Stores the credentials in Yuki's config so that 'book-reana'
    can be run without specifying --server and --token.
    """
    try:
        result = register_booking_server(
            server_url=server_url,
            access_token=access_token,
        )
        if result.messages:
            print(result.colored())
    except Exception as e:
        print(f"Error: {e}")


@click.command(name="book-reana")
@click.option("--server", "server_url", default="",
              help="REANA server URL (overrides stored credentials)")
@click.option("--token", "access_token", default="",
              help="REANA access token (overrides stored credentials)")
@click.option("--path", "project_path", default="",
              help="Path to Celebi project (default: current directory)")
@click.option("--insecure", is_flag=True, default=False,
              help="Disable SSL certificate verification")
@click.option("--stageout", is_flag=True, default=False,
              help="Also upload stageout files from Yuki storage")
@click.option("--no-stream", is_flag=True, default=False,
              help="Disable live streaming; wait for all output before printing")
def book_reana_command(server_url, access_token, project_path, insecure, stageout, no_stream):
    """Book the current project to REANA as a file catalog via Yuki.

    If --server and --token are not provided, Yuki will use credentials
    previously registered via 'register-booking-server'.
    """
    try:
        result = book_reana(
            server_url=server_url,
            access_token=access_token,
            verify_ssl=not insecure,
            project_path=project_path,
            stageout=stageout,
            stream=not no_stream,
        )
        # In streaming mode, messages were already printed live.
        if not no_stream:
            pass
        elif result.messages:
            print(result.colored())
    except Exception as e:
        print(f"Error: {e}")
