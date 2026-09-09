"""Numeric shell navigation must follow the indices printed by ls."""
import os
from unittest import mock

import pytest

from CelebiChrono.interface.shell_modules import navigation
from CelebiChrono.kernel.vobj_file_display import FileManagementDisplay, LsParameters


@pytest.mark.parametrize("entries, expected", [
    (
        [("algorithm", "prepare_tmva"), ("directory", "D02pipi"),
         ("directory", "D02Kpi"), ("directory", "D02KK"),
         ("directory", "D02K3pi")],
        ["D02K3pi", "D02KK", "D02Kpi", "D02pipi", "prepare_tmva"],
    ),
    (
        [("task", "eff_10"), ("task", "eff_2"), ("task", "eff_all"),
         ("algorithm", "prepare"), ("directory", "inputs")],
        ["inputs", "prepare", "eff_2", "eff_10", "eff_all"],
    ),
])
def test_numeric_cd_matches_displayed_subobject_indices(entries, expected):
    """Mixed types and numeric suffixes use the same order in ls and cd."""
    objects = []
    for object_type, name in entries:
        obj = mock.Mock(path=f"/project/{name}")
        obj.object_type.return_value = object_type
        objects.append(obj)

    current = mock.Mock()
    # Return fresh lists so ls's in-place sort cannot mask navigation bugs.
    current.sub_objects.side_effect = lambda: list(objects)
    current.predecessors.return_value = []
    current.successors.return_value = []
    current.relative_path.side_effect = os.path.basename

    message = FileManagementDisplay.show_sub_objects(
        current, current.sub_objects(), LsParameters()
    )
    lines = "".join(text for text, _ in message.messages).splitlines()[1:]
    assert [line.split()[-1] for line in lines] == expected

    with mock.patch.object(navigation, "MANAGER") as manager, \
            mock.patch.object(navigation, "_cd_by_path") as cd_by_path:
        manager.current_object.return_value = current
        for index, name in enumerate(expected):
            assert lines[index].split()[0] == f"[{index}]"
            navigation.cd(str(index))
            cd_by_path.assert_called_with(name)
