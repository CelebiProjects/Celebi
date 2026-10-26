"""The Celebi-side ``lb_run`` schema includes optional nightly slots."""
import pytest

from CelebiChrono.utils.lb_run import lb_run_spec


def test_release_spec_defaults_optional_fields():
    assert lb_run_spec({"project": "Gauss", "version": "v62r0"}) == {
        "project": "Gauss",
        "version": "v62r0",
        "platform": "",
        "nightly": "",
    }


def test_nightly_spec_substitutes_task_parameters():
    values = {
        "version": "run5_stackglue_June2026",
        "slot": "lhcb-sim11-run5-gluing/74",
    }

    def substitute(value):
        for key, replacement in values.items():
            value = value.replace("${" + key + "}", replacement)
        return value

    assert lb_run_spec({
        "project": "Gauss",
        "version": "${version}",
        "platform": "x86_64_v3-el9-gcc15-opt",
        "nightly": "${slot}",
    }, substitute)["nightly"] == "lhcb-sim11-run5-gluing/74"


@pytest.mark.parametrize("field", ["project", "version", "platform", "nightly"])
def test_fields_must_be_strings(field):
    config = {"project": "Gauss", "version": "master", field: 74}
    with pytest.raises(ValueError, match=rf"lb_run\.{field} must be a string"):
        lb_run_spec(config)


def test_unknown_fields_are_rejected():
    with pytest.raises(ValueError, match="unsupported lb_run field.*slot"):
        lb_run_spec({"project": "Gauss", "version": "master", "slot": "74"})


def test_nightly_may_contain_a_slash_but_project_and_version_may_not():
    assert lb_run_spec({
        "project": "Gauss",
        "version": "master",
        "nightly": "lhcb-sim11/latest",
    })["nightly"] == "lhcb-sim11/latest"
    with pytest.raises(ValueError, match="version must not contain"):
        lb_run_spec({"project": "Gauss", "version": "Gauss/master"})
