"""Interactive submit completions for options and their values."""
from unittest.mock import Mock

import pytest

from CelebiChrono.interface.chern_shell.completions import ChernShellCompletions


@pytest.mark.parametrize('line,expected', [
    ('submit ', ['--runner', '--timeout']),
    ('submit --', ['--runner', '--timeout']),
    ('submit --r', ['--runner']),
    ('submit --t', ['--timeout']),
    ('submit --runner ', ['local', 'pkufarm212']),
    ('submit --runner p', ['pkufarm212']),
    ('submit --runner pkufarm212 ', ['--runner', '--timeout']),
    ('submit --runner pkufarm212 --t', ['--timeout']),
    ('submit --timeout ', []),
    ('submit --timeout 30', []),
    ('submit --timeout 3000 --r', ['--runner']),
    ('submit --timeout 3000 --runner p', ['pkufarm212']),
    ('submit task --t', ['--timeout']),
    ('submit --timeout=30', []),
    ('submit --runner=p', ['--runner=pkufarm212']),
    ('submit -- --t', []),
])
def test_submit_completions(line, expected):
    comp = ChernShellCompletions()
    comp.readline_file = Mock()
    comp.readline_file.read_variable.return_value = ['local', 'pkufarm212']
    begidx = line.rfind(' ') + 1
    assert comp.complete_submit(line[begidx:], line, begidx, len(line)) == expected


def test_cursor_before_end_of_line():
    comp = ChernShellCompletions()
    assert comp.complete_submit('--t', 'submit --t --runner local', 7, 10) == ['--timeout']


def test_readline_splits_on_equals():
    comp = ChernShellCompletions()
    comp.readline_file = Mock()
    comp.readline_file.read_variable.return_value = ['pkufarm212']
    line = 'submit --runner=p'
    assert comp.complete_submit('p', line, len(line) - 1, len(line)) == ['pkufarm212']
