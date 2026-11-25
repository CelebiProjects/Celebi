"""SSH APD environment defaults and validation."""
from types import SimpleNamespace

import pytest

from CelebiChrono.kernel.vtask_setting import SettingManager
from CelebiChrono.utils import metadata
from CelebiChrono.utils.apd import apd_lb_conda_environment


@pytest.mark.parametrize("value", ["default", "default/2026-09-17",
                                    "default/2026-04-10_06-22"])
def test_valid_lb_conda(value):
    assert apd_lb_conda_environment({"lb_conda": value}) == value


def test_existing_apd_config_defaults_to_default():
    assert apd_lb_conda_environment({"datasets": {}}) == "default"


@pytest.mark.parametrize("value", [None, 1, "", "default;echo bad", "../default",
                                    "default/20260917", "default/2026-09-17/extra"])
def test_invalid_lb_conda(value):
    with pytest.raises(ValueError, match="ap_config.lb_conda"):
        apd_lb_conda_environment({"lb_conda": value})


def test_task_rejects_invalid_apd_runtime(tmp_path):
    config = metadata.YamlFile(str(tmp_path / "celebi.yaml"))
    task = SimpleNamespace(path=str(tmp_path), environment=lambda: "lhcb_ap_datalist")
    config.write_variable("ap_config", {"lb_conda": "default;bad"})
    assert not SettingManager.env_validated(task)
    config.write_variable("ap_config", {"lb_conda": "default/2026-09-17"})
    assert SettingManager.env_validated(task)
