"""Configuration contract for repeated executions of a single task."""


def read_subtask_count(yaml_file):
    """Read the optional declaration without treating explicit null as absent."""
    sentinel = object()
    count = yaml_file.read_variable("subtasks", sentinel)
    if count is sentinel:
        return None
    config = {key: yaml_file.read_variable(key, None) for key in (
        "environment", "parameters", "compute_backend")}
    return subtask_count(dict(config, subtasks=count))


def subtask_count(config):
    """Return None for an ordinary task, otherwise a validated repeat count.

    ``index`` remains available to ordinary tasks for backwards compatibility.
    Repeated tasks reserve it for the execution engine.
    """
    if "subtasks" not in config:
        return None
    count = config["subtasks"]
    if type(count) is not int or count <= 0:
        raise ValueError("subtasks must be a positive integer")
    parameters = config.get("parameters") or {}
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be a mapping")
    if "index" in parameters:
        raise ValueError("index is reserved when subtasks is configured")
    if config.get("environment") in (
            "rawdata", "datalist", "lhcb_ap_datalist"):
        raise ValueError("subtasks is only supported for executable tasks")
    if config.get("compute_backend") == "htcondorcern":
        raise ValueError("subtasks is not supported with htcondorcern")
    return count
