"""Test cherncommunicator select."""
from unittest import mock
from CelebiChrono.kernel.chern_communicator import ChernCommunicator
from CelebiChrono.kernel.chern_cache import ChernCache


def _cc():
    """Cc."""
    cc = ChernCommunicator.__new__(ChernCommunicator)
    cc.project_uuid = "proj"
    cc.timeout = 1
    cc.serverurl = lambda: "host:1"
    cc.file_status_timeout = 40
    cc.transfer_timeout = 600
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
    ChernCache.instance().file_status_cache.clear()
    with mock.patch("CelebiChrono.kernel.chern_communicator.requests.get") as rq_get:
        rq_get.return_value.json.return_value = [{"name": "mass.png"}]
        out = cc.file_status(imp, "runner", "stageout")
    assert out[0]["name"] == "mass.png"


def test_file_status_detailed_caches_within_status_window():
    """Test file status detailed reuses cache within 1s, then refreshes.

    The fake clock advances during the request so the age of the cache
    entry is measured from the fetch completion, not the request start.
    """
    cc = _cc()
    imp = mock.Mock(uuid="abc")
    ChernCache.instance().file_status_cache.clear()
    payload = {"files": [{"name": "mass.png"}], "notes": []}
    clock = [100.0]
    fake_time = mock.Mock(time=mock.Mock(side_effect=lambda: clock[0]))
    response = mock.Mock()
    response.json.return_value = payload
    with mock.patch("CelebiChrono.kernel.chern_communicator.requests.get") as rq_get, \
            mock.patch("CelebiChrono.kernel.chern_communicator.time", fake_time):
        def slow_get(*args, **kwargs):
            """0.9s server round-trip."""
            clock[0] += 0.9
            return response
        rq_get.side_effect = slow_get
        out1 = cc.file_status_detailed(imp, "runner", "stageout")
        # Fetch finished at 100.9; the next call is inside the 1s window.
        out2 = cc.file_status_detailed(imp, "runner", "stageout")
        assert rq_get.call_count == 1
        assert out2 == out1
        # More than 1s after the fetch completed: refresh.
        clock[0] = 102.0
        cc.file_status_detailed(imp, "runner", "stageout")
        assert rq_get.call_count == 2


def test_file_status_detailed_does_not_cache_errors():
    """Test failed requests are not cached and retried on the next call."""
    cc = _cc()
    imp = mock.Mock(uuid="abc")
    ChernCache.instance().file_status_cache.clear()
    fake_time = mock.Mock(time=mock.Mock(return_value=100.0))
    with mock.patch("CelebiChrono.kernel.chern_communicator.requests.get") as rq_get, \
            mock.patch("CelebiChrono.kernel.chern_communicator.time", fake_time):
        rq_get.side_effect = Exception("boom")
        out1 = cc.file_status_detailed(imp, "runner", "stageout")
        out2 = cc.file_status_detailed(imp, "runner", "stageout")
        assert "cannot reach Yuki server" in out1["notes"][0]["message"]
        assert rq_get.call_count == 2
        assert out2 == out1
