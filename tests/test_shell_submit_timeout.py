"""Regression tests for timeout options in the interactive submit command."""
from unittest.mock import patch

import pytest

from CelebiChrono.interface.chern_shell.commands_environment import EnvironmentCommands
from CelebiChrono.interface import shell


@pytest.mark.parametrize('args,runner,timeout', [
    ('--runner pkufarm212 --timeout 3000', 'pkufarm212', 3000),
    ('--timeout 3000 --runner pkufarm212', 'pkufarm212', 3000),
    ('--runner=pkufarm212 --timeout=3000', 'pkufarm212', 3000),
    ('--timeout 3000', 'local', 3000),
    ('--runner pkufarm212', 'pkufarm212', None),
    ('', 'local', None),
])
def test_current_object_submit(args, runner, timeout):
    with patch.object(shell, 'submit') as submit, \
         patch.object(shell, 'submit_objects') as batch:
        EnvironmentCommands().do_submit(args)
    submit.assert_called_once_with(runner, timeout=timeout)
    batch.assert_not_called()


def test_named_objects_submit():
    with patch.object(shell, 'submit') as submit, \
         patch.object(shell, 'submit_objects') as batch:
        EnvironmentCommands().do_submit('a --timeout 3000 "b c" --runner pkufarm212')
    submit.assert_not_called()
    batch.assert_called_once_with(['a', 'b c'], 'pkufarm212', timeout=3000)


@pytest.mark.parametrize('args', [
    '--timeout', '--timeout --runner farm', '--timeout=','--timeout 0',
    '--timeout -1', '--timeout nope', '--timeout 1.5', '--runner', '--typo 3000',
])
def test_invalid_options_do_not_resolve_objects(args, capsys):
    with patch.object(shell, 'submit') as submit, \
         patch.object(shell, 'submit_objects') as batch:
        EnvironmentCommands().do_submit(args)
    submit.assert_not_called()
    batch.assert_not_called()
    assert 'Error submitting:' in capsys.readouterr().out
