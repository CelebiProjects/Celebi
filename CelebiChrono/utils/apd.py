"""Validation shared by APD task configuration and execution."""
import re


def apd_lb_conda_environment(ap_config):
    """Return the SSH LbConda environment, optionally pinned to a release."""
    if not isinstance(ap_config, dict):
        raise ValueError("ap_config must be a mapping")
    value = ap_config.get("lb_conda", "default")
    pattern = r"[A-Za-z0-9][A-Za-z0-9._-]*(?:/\d{4}-\d{2}-\d{2}(?:_\d{2}-\d{2})?)?"
    if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
        raise ValueError("ap_config.lb_conda must be PACKAGE or PACKAGE/YYYY-MM-DD")
    return value
