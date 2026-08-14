"""Test cherncommunicator select."""
from unittest import mock
from CelebiChrono.kernel.chern_communicator import ChernCommunicator


def _cc():
    """Cc."""
    cc = ChernCommunicator.__new__(ChernCommunicator)
    cc.project_uuid = "proj"
    cc.timeout = 1
    cc.serverurl = lambda: "host:1"
    return cc


def test_collect_files_builds_type_query():
    """Test collect files builds type query."""
    cc = _cc()
    imp = mock.Mock(uuid="abc")
    with mock.patch("CelebiChrono.kernel.chern_communicator.requests") as rq:
        rq.get.return_value.text = "ok"
        cc.collect_files(imp, kind="stageout", spec_type="plots")
        url = rq.get.call_args.args[0]
    assert "/collect-files/proj/abc" in url and "type=plots" in url and "kind=stageout" in url


def test_file_status_parses_json():
    """Test file status parses json."""
    cc = _cc()
    imp = mock.Mock(uuid="abc")
    with mock.patch("CelebiChrono.kernel.chern_communicator.requests") as rq:
        rq.get.return_value.json.return_value = [{"name": "mass.png"}]
        out = cc.file_status(imp, "runner", "stageout")
    assert out[0]["name"] == "mass.png"
