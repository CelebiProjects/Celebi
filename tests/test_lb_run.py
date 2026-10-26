"""The Celebi-side ``lb_run`` schema includes optional nightly slots."""
import pytest

from CelebiChrono.utils.lb_run import lb_run_spec, validated_lb_run_spec


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


def test_algorithm_lb_run_requires_task_and_algorithm_environment():
    raw = {"project": "Gauss", "version": "master"}
    assert validated_lb_run_spec("lb-run", "lb-run", raw)["project"] == "Gauss"
    with pytest.raises(ValueError, match="task environment 'lb-run'"):
        validated_lb_run_spec("script", "lb-run", raw)
    with pytest.raises(ValueError, match="command source environment 'lb-run'"):
        validated_lb_run_spec("lb-run", "script", raw)


def test_inline_task_can_be_its_own_lb_run_command_source():
    raw = {"project": "Moore", "version": "v55r12"}
    assert validated_lb_run_spec("lb-run", "lb-run", raw)["version"] == "v55r12"


def test_lb_run_environment_requires_a_declaration():
    with pytest.raises(ValueError, match="requires an lb_run declaration"):
        validated_lb_run_spec("lb-run", "lb-run", None)
