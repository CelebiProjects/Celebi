"""Exercise timeout options from both command interfaces through HTTP requests."""
from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from CelebiChrono.celebi_cli.commands.object_creation import (
    register_ssh_data_command, verify_data_command,
)
from CelebiChrono.celebi_cli.commands.file_operations import transfer_command
from CelebiChrono.interface.chern_shell.commands_task import TaskCommands
from CelebiChrono.interface.chern_shell.commands_file import FileCommands
from CelebiChrono.interface.shell_modules import object_creation, file_operations
from CelebiChrono.kernel.chern_communicator import ChernCommunicator
from CelebiChrono.utils.message import Message


COMMANDS = [
    (register_ssh_data_command, TaskCommands().do_register_ssh_data,
     ["cluster", "/remote/data"], 10),
    (transfer_command, FileCommands().do_transfer, ["yuki", "runner:cluster"], 10),
    (verify_data_command, TaskCommands().do_verify_data, [], 3600),
]


@pytest.mark.parametrize("command,handler,args,default", COMMANDS)
@pytest.mark.parametrize("interface", ["cli", "shell"])
@pytest.mark.parametrize("timeout", [None, 120])
def test_timeout_reaches_http_without_changing_defaults(
        command, handler, args, default, interface, timeout):
    current = MagicMock()
    current.object_type.return_value = "task" if not args else "project"
    current.environment.return_value = "rawdata"
    current.project_uuid.return_value = "project"
    current.impression.return_value.uuid = "impression"
    cc = ChernCommunicator()
    cc.serverurl = MagicMock(return_value="localhost:3315")
    cc.timeout = 10
    response = MagicMock(status_code=200)
    response.json.return_value = {
        "status": "done", "job_id": "job", "match": True,
        "expected": "md5", "location": "cluster",
        "result": {"uuid": "md5", "impression_uuid": "impression", "descriptor": "data"},
        "report": {"transferred": [], "skipped": [], "failed": []},
    }
    with ExitStack() as stack:
        for module in (object_creation, file_operations):
            manager = stack.enter_context(patch.object(module, "MANAGER"))
            manager.current_object.return_value = current
            stack.enter_context(patch.object(module, "tqdm"))
        stack.enter_context(patch.object(ChernCommunicator, "instance", return_value=cc))
        stack.enter_context(patch.object(object_creation, "_fill_registered_data",
                                        return_value=Message()))
        get = stack.enter_context(patch(
            "CelebiChrono.kernel.chern_communicator.requests.get", return_value=response))
        post_response = MagicMock(status_code=200)
        post_response.json.return_value = {"job_id": "job"}
        post = stack.enter_context(patch(
            "CelebiChrono.kernel.chern_communicator.requests.post", return_value=post_response))
        arguments = args + (["--timeout", str(timeout)] if timeout is not None else [])
        if interface == "cli":
            result = CliRunner().invoke(command, arguments)
            assert result.exit_code == 0, result.output
        else:
            handler(" ".join(arguments))
        get.assert_called_once()
        assert get.call_args.kwargs["timeout"] == (default if timeout is None else timeout)
        if args:
            post.assert_called_once()
            assert post.call_args.kwargs["timeout"] == (default if timeout is None else timeout)
        assert cc.timeout == 10


@pytest.mark.parametrize("command,handler,args,default", COMMANDS)
@pytest.mark.parametrize("value", ["0", "-1", "abc", ""])
def test_invalid_timeout_rejected(command, handler, args, default, value, capsys):
    arguments = args + ["--timeout"] + ([value] if value else [])
    with patch.object(ChernCommunicator, "instance") as instance:
        result = CliRunner().invoke(command, arguments)
        assert result.exit_code != 0
        assert "--timeout" in result.output
        handler(" ".join(arguments))
        assert "--timeout requires a positive integer" in capsys.readouterr().out
        instance.assert_not_called()


def test_shell_timeout_before_quoted_path():
    with patch("CelebiChrono.interface.shell.register_ssh_data", return_value=Message()) as call:
        TaskCommands().do_register_ssh_data('--timeout=120 cluster "/data/with spaces"')
    call.assert_called_once_with("cluster", "/data/with spaces", "", timeout=120)
