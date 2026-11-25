"""Runner authentication options are forwarded without keytab upload."""
from unittest.mock import patch
from click.testing import CliRunner
from CelebiChrono.celebi_cli.commands.execution_management import update_runner_command


def test_ssh_kerberos_options():
    with patch('CelebiChrono.interface.shell.update_runner', return_value='ok') as update:
        result = CliRunner().invoke(update_runner_command, [
            'farm', '--use-kerberos', '--kerberos-keytab', '~/.keytab',
            '--kerberos-principal', 'analyst@CERN.CH', '--kerberos-renew-interval', '1800'])
    assert result.exit_code == 0, result.output
    update.assert_called_once_with('farm', use_kerberos=True, kerberos_keytab='~/.keytab',
                                   kerberos_principal='analyst@CERN.CH',
                                   kerberos_renew_interval=1800)


def test_invalid_refresh_interval():
    result = CliRunner().invoke(update_runner_command,
                               ['farm', '--kerberos-renew-interval', '0'])
    assert result.exit_code != 0
