"""Import local credentials into Yuki's private store."""
import click


@click.command(name="add-secret")
@click.argument("name")
@click.option("--file", "filename", required=True,
              type=click.Path(exists=True, dir_okay=False, readable=True))
@click.option("--type", "kind", required=True, type=click.Choice(["kerberos"]))
@click.option("--principal", required=True, help="Kerberos identity, e.g. USER@CERN.CH")
def add_secret_command(name, filename, kind, principal):
    """Import a keytab into Yuki under NAME, without adding it to the project.

    Existing names are never overwritten. Bind it with update-runner --secret NAME.
    Use HTTPS or a local SSH tunnel to reach Yuki.
    """
    from CelebiChrono.kernel.chern_communicator import ChernCommunicator
    try:
        result = ChernCommunicator.instance().add_secret(name, filename, kind, principal)
    except (OSError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Secret '{result['name']}' imported into Yuki ({result['type']}).")
