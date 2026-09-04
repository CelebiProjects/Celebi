"""Test natural sort key used for subobject listing."""
# pylint: disable=too-few-public-methods
from CelebiChrono.kernel.vobj_file_display import _natural_sort_key


class _StubObject:
    """Minimal stand-in providing the two attributes _natural_sort_key reads."""

    def __init__(self, path, obj_type):
        self.path = path
        self._obj_type = obj_type

    def object_type(self):
        """Return the stub's object type."""
        return self._obj_type


def test_mixed_numeric_and_word_suffixes_do_not_raise():
    """Sorting GenTask_1 next to GenTask_ssh must not raise TypeError."""
    objs = [
        _StubObject("/p/GenTask_ssh", "task"),
        _StubObject("/p/GenTask_1", "task"),
        _StubObject("/p/GenTask", "task"),
    ]
    sorted_objs = sorted(objs, key=_natural_sort_key)
    assert [o.path for o in sorted_objs] == [
        "/p/GenTask",
        "/p/GenTask_1",
        "/p/GenTask_ssh",
    ]


def test_numeric_suffixes_sort_naturally():
    """eff_2 must come before eff_10."""
    objs = [_StubObject(f"/p/eff_{i}", "task") for i in (10, 2)]
    sorted_objs = sorted(objs, key=_natural_sort_key)
    assert [o.path for o in sorted_objs] == ["/p/eff_2", "/p/eff_10"]


def test_directory_sorts_before_task():
    """Type priority dominates basename ordering."""
    objs = [
        _StubObject("/p/zeta_task", "task"),
        _StubObject("/p/aaa_dir", "directory"),
    ]
    sorted_objs = sorted(objs, key=_natural_sort_key)
    assert [o.path for o in sorted_objs] == ["/p/aaa_dir", "/p/zeta_task"]
