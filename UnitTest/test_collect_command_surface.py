"""Test collect command surface."""
from unittest import mock
from CelebiChrono.interface.chern_shell import commands_basic


def test_do_collect_forwards_pattern():
    """Test do collect forwards pattern."""
    _cmd = commands_basic.__dict__  # module-level access to the shell class
    from CelebiChrono.interface.chern_shell.commands_basic import BasicCommands
    inst = BasicCommands.__new__(BasicCommands)
    with mock.patch(
        "CelebiChrono.interface.chern_shell.commands_basic.shell"
    ) as sh:
        sh.collect.return_value = mock.Mock(messages=[])
        inst.do_collect("*.root")
        sh.collect.assert_called_once_with("*.root")


def test_do_collect_forwards_allow_failed():
    """Interactive collect accepts the same failed-stageout opt-in."""
    from CelebiChrono.interface.chern_shell.commands_basic import BasicCommands
    inst = BasicCommands.__new__(BasicCommands)
    with mock.patch(
        "CelebiChrono.interface.chern_shell.commands_basic.shell"
    ) as sh:
        sh.collect.return_value = mock.Mock(messages=[])
        inst.do_collect("--allow-failed all")
        sh.collect.assert_called_once_with("all", allow_failed=True)
