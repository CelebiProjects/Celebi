from unittest import mock
from CelebiChrono.kernel.vtask import VTask


def test_status_table_lists_runner_and_downloaded():
    t = VTask.__new__(VTask)
    t.impression = lambda: mock.Mock(uuid="abc")
    rows = [
        {"name": "mass.png", "size": 240, "type": "plot", "in_runner": True, "in_yuki": True},
        {"name": "ntuple.root", "size": 3221225472, "type": "data",
         "in_runner": True, "in_yuki": False},
    ]
    cc = mock.Mock(); cc.file_status.return_value = rows
    msg = t._stageout_table(cc, "runner")     # helper under test
    text = "".join(m[0] for m in msg.messages)
    assert "mass.png" in text and "ntuple.root" in text
    assert "ROOT" not in text  # sanity: not echoing junk
    assert "✓" in text or "yes" in text.lower()   # downloaded marker shown
