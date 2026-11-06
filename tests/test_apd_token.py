"""APD tokens can be attached to ordinary execution tasks."""

from unittest import mock

from CelebiChrono.interface.shell_modules import task_configuration
from CelebiChrono.utils import metadata


def test_add_apd_token_accepts_ordinary_task(tmp_path):
    """An lb-conda task stores its token only in git-excluded local config."""
    task = mock.Mock()
    task.object_type.return_value = "task"
    task.path = str(tmp_path)
    metadata.YamlFile(str(tmp_path / "celebi.yaml")).write_variable(
        "environment", "lb-conda/pidcalib/2026-10-15")

    with mock.patch.object(task_configuration.MANAGER, "current_object",
                           return_value=task):
        result = task_configuration.add_apd_token("lbapi:user:secret")

    assert result.success
    local = metadata.ConfigFile(str(tmp_path / ".celebi/config.local.json"))
    assert local.read_variable("apd_token", "") == "lbapi:user:secret"
    yaml_file = metadata.YamlFile(str(tmp_path / "celebi.yaml"))
    assert yaml_file.read_variable("apd_token", None) is None


def test_add_apd_token_still_rejects_non_task(tmp_path):
    """Secrets cannot be attached to directories or algorithms."""
    current = mock.Mock()
    current.object_type.return_value = "algorithm"
    current.path = str(tmp_path)

    with mock.patch.object(task_configuration.MANAGER, "current_object",
                           return_value=current):
        result = task_configuration.add_apd_token("lbapi:user:secret")

    assert not result.success
    assert not (tmp_path / ".celebi/config.local.json").exists()


def test_add_apd_token_rejects_empty_secret(tmp_path):
    """An empty prompt result cannot enable a misleading token state."""
    task = mock.Mock()
    task.object_type.return_value = "task"
    task.path = str(tmp_path)

    with mock.patch.object(task_configuration.MANAGER, "current_object",
                           return_value=task):
        result = task_configuration.add_apd_token("   ")

    assert not result.success
    assert not (tmp_path / ".celebi/config.local.json").exists()
