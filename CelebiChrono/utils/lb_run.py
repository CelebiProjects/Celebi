"""Shared configuration contract for LHCb ``lb-run`` execution."""


LB_RUN_FIELDS = ("project", "version", "platform", "nightly")


def lb_run_spec(raw, substitute=None):
    """Validate and resolve an optional ``lb_run`` mapping.

    ``substitute`` resolves task parameters in string values. The nightly slot
    intentionally permits ``/`` (for example ``lhcb-sim11/latest``), while the
    project and version remain the two components of ``PROJECT/VERSION``.
    """
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("lb_run must be a mapping")
    unknown = sorted(set(raw) - set(LB_RUN_FIELDS))
    if unknown:
        raise ValueError(
            "unsupported lb_run field(s): " + ", ".join(unknown))

    resolve = substitute or (lambda value: value)
    spec = {}
    for field in LB_RUN_FIELDS:
        value = raw.get(field, "")
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise ValueError(f"lb_run.{field} must be a string")
        value = resolve(value).strip()
        if "${" in value:
            raise ValueError(
                f"lb_run.{field} contains an unresolved parameter: {value}")
        spec[field] = value

    for field in ("project", "version"):
        if not spec[field]:
            raise ValueError(f"lb_run.{field} is required")
        if "/" in spec[field]:
            raise ValueError(
                f"lb_run.{field} must not contain '/': {spec[field]}")
    return spec


def read_lb_run_spec(yaml_file, substitute=None):
    """Read and validate ``lb_run`` from a Celebi YAML configuration."""
    return lb_run_spec(yaml_file.read_variable("lb_run", None), substitute)
