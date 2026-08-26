"""Tests for shell error_log offset forwarding."""
from unittest import mock

from CelebiChrono.interface.shell_modules import utilities


def test_error_log_forwards_offset_to_current_object():
    """error_log forwards the offset argument to the current object."""
    obj = mock.MagicMock()
    obj.error_log.return_value = "log-result"

    with mock.patch.object(utilities, "MANAGER") as manager:
        manager.current_object.return_value = obj
        result = utilities.error_log(3, offset=42)

    obj.error_log.assert_called_once_with(3, offset=42)
    assert result == "log-result"


def test_error_log_defaults_offset_to_zero():
    """error_log defaults the offset to 0."""
    obj = mock.MagicMock()
    obj.error_log.return_value = "log-result"

    with mock.patch.object(utilities, "MANAGER") as manager:
        manager.current_object.return_value = obj
        result = utilities.error_log(0)

    obj.error_log.assert_called_once_with(0, offset=0)
    assert result == "log-result"
