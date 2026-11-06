"""Submission refreshes APD secrets for existing immutable impressions."""

from unittest import mock

from CelebiChrono.kernel import vobj_execution
from CelebiChrono.utils import metadata


class _ExistingTask:
    deposit_with_dependencies = vobj_execution.ExecutionManagement.deposit_with_dependencies

    def __init__(self, path, impression):
        self.path = str(path)
        self._impression = impression

    def is_deposited(self):
        return True

    def impression(self):
        return self._impression


def test_existing_impression_is_redeposited_when_apd_token_was_added(tmp_path):
    """A local secret added after the first run reaches Yuki on resubmit."""
    impression = mock.Mock(uuid="a" * 32)
    task = _ExistingTask(tmp_path, impression)
    local = metadata.ConfigFile(str(tmp_path / ".celebi/config.local.json"))
    local.write_variable("apd_token", "lbapi:user:secret")
    communicator = mock.Mock()
    vobj_execution.CHERN_CACHE.deposit_consult_table.pop(task.path, None)

    with mock.patch.object(vobj_execution.ChernCommunicator, "instance",
                           return_value=communicator):
        task.deposit_with_dependencies(123.0)

    communicator.deposit.assert_called_once_with(impression, task.path)


def test_existing_impression_without_apd_token_is_not_redeposited(tmp_path):
    """Ordinary immutable deposits retain the existing fast path."""
    impression = mock.Mock(uuid="b" * 32)
    task = _ExistingTask(tmp_path, impression)
    communicator = mock.Mock()
    vobj_execution.CHERN_CACHE.deposit_consult_table.pop(task.path, None)

    with mock.patch.object(vobj_execution.ChernCommunicator, "instance",
                           return_value=communicator):
        task.deposit_with_dependencies(124.0)

    communicator.deposit.assert_not_called()
