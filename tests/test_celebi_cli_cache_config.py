from click.testing import CliRunner
import os

from CelebiChrono.celebi_cli.cli import cli
from CelebiChrono.kernel import vproject
from CelebiChrono.utils import metadata


def test_config_cache_invalidation_mode_registered():
    assert "config-cache-invalidation-mode" in cli.commands


def test_config_cache_invalidation_mode_show_and_set():
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir(".celebi")
        vproject.create_readme(".")
        vproject.create_configfile(".", "test-project-uuid")

        result = runner.invoke(cli, ["config-cache-invalidation-mode"])
        assert result.exit_code == 0
        assert "cache_invalidation_mode=auto" in result.output

        result = runner.invoke(cli, ["config-cache-invalidation-mode", "off"])
        assert result.exit_code == 0
        assert "cache_invalidation_mode=off" in result.output
        assert "resolved_method=off" in result.output

        local_config = metadata.ConfigFile("./.celebi/config.local.json")
        assert local_config.read_variable("cache_invalidation_mode") == "off"
