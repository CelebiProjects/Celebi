"""Test vtask collect selector."""
from unittest import mock
from CelebiChrono.kernel.vtask_job import JobManager


class FakeJobManager(JobManager):
    """Fake Job Manager."""
    def algorithm(self):
        """Algorithm."""
        return mock.Mock()
    def auto_download(self):
        """Auto download."""
        return False
    def default_runner(self):
        """Default runner."""
        return "local"
    def environment(self):
        """Environment."""
        return "python:3.9"
    def get_task(self, path):
        """Get task."""
        return self
    def input_md5(self):
        """Input md5."""
        return "abc123"
    def inputs(self):
        """Inputs."""
        return []
    def memory_limit(self):
        """Memory limit."""
        return "2G"
    def output_files(self):
        """Output files."""
        return []
    def parameters(self):
        """Parameters."""
        return ([], {})
    def set_input_md5(self, path):
        """Set input md5."""
    def cache_on_runner(self):
        """Cache on runner."""
        return False
    def validated(self):
        """Validated."""
        return True


def _jm():
    """Jm."""
    jm = FakeJobManager.__new__(FakeJobManager)
    jm.impression = lambda: mock.Mock(uuid="abc")
    return jm


def _patch_cc():
    """Patch cc."""
    cc = mock.Mock()
    return mock.patch(
        "CelebiChrono.kernel.vtask_job.ChernCommunicator.instance",
        return_value=cc), cc


def test_default_calls_light_collect():
    """Test default calls light collect."""
    jm = _jm()
    p, cc = _patch_cc()
    with p:
        jm.collect("")
    cc.collect.assert_called_once()


def test_all_calls_outputs_and_logs():
    """Test all calls outputs and logs."""
    jm = _jm()
    p, cc = _patch_cc()
    with p:
        jm.collect("all")
    cc.collect_outputs.assert_called_once()
    cc.collect_logs.assert_called_once()


def test_plots_keyword():
    """Test plots keyword."""
    jm = _jm()
    p, cc = _patch_cc()
    with p:
        jm.collect("plots")
    assert cc.collect_files.call_args.kwargs["spec_type"] == "plots"


def test_glob_pattern():
    """Test glob pattern."""
    jm = _jm()
    p, cc = _patch_cc()
    with p:
        jm.collect("*.root")
    assert cc.collect_files.call_args.kwargs["pattern"] == "*.root"


def test_data_keyword():
    """Test data keyword."""
    jm = _jm()
    p, cc = _patch_cc()
    with p:
        jm.collect("data")
    assert cc.collect_files.call_args.kwargs["spec_type"] == "data"


def test_logs_keyword():
    """Test logs keyword."""
    jm = _jm()
    p, cc = _patch_cc()
    with p:
        jm.collect("logs")
    cc.collect_logs.assert_called_once()


def test_literal_name_routes_to_names():
    """Test literal name routes to names."""
    jm = _jm()
    p, cc = _patch_cc()
    with p:
        jm.collect("mass.png")
    assert cc.collect_files.call_args.kwargs["names"] == ["mass.png"]


def test_outputs_alias_collects_full_stageout():
    """Test outputs alias collects full stageout."""
    jm = _jm()
    p, cc = _patch_cc()
    with p:
        jm.collect("outputs")
    cc.collect_outputs.assert_called_once()


def test_check_preceding_jobs_collects_full_stageout():
    """Test check preceding jobs collects full stageout."""
    jm = FakeJobManager.__new__(FakeJobManager)
    pre = mock.Mock()
    pre.is_impressed_fast.return_value = True
    pre.run_status.return_value = "finished"
    pre.impression.return_value = mock.Mock(uuid="pre")
    jm.inputs = lambda: [pre]
    cc = mock.Mock()
    ok, _msg = jm._check_preceding_jobs(cc)  # pylint: disable=protected-access
    assert ok is True
    cc.collect_outputs.assert_called_once_with(pre.impression())
    cc.collect.assert_not_called()


def test_collect_shows_start_message():
    """Test collect shows start message."""
    jm = _jm()
    p, cc = _patch_cc()
    cc.collect.return_value = {"success": True, "message": "ok"}
    cc.file_status.return_value = []
    with p:
        msg = jm.collect("")
    assert any("Collecting" in text and "plots+logs" in text
               for text, _ in msg.messages)


def test_collect_reports_error_on_failure():
    """Test collect reports error on failure."""
    jm = _jm()
    p, cc = _patch_cc()
    cc.collect.return_value = {"success": False, "message": "connection refused"}
    with p:
        msg = jm.collect("")
    assert any("Failed to collect" in text for text, _ in msg.messages)
    assert any("connection refused" in text for text, _ in msg.messages)


def test_collect_warns_when_no_files_in_yuki():
    """Test collect warns when no files in yuki."""
    jm = _jm()
    p, cc = _patch_cc()
    cc.collect.return_value = {"success": True, "message": "ok"}
    cc.file_status.return_value = []
    with p:
        msg = jm.collect("")
    assert any("No files are currently collected" in text
               for text, _ in msg.messages)


def test_collect_reports_file_count():
    """Test collect reports file count."""
    jm = _jm()
    p, cc = _patch_cc()
    cc.collect.return_value = {"success": True, "message": "ok"}
    cc.file_status.side_effect = [
        [{"name": "plot.png", "size": 100, "in_yuki": True}],
        [{"name": "log.txt", "size": 50, "in_yuki": True}],
    ]
    with p:
        msg = jm.collect("")
    assert any("2 file(s) now in Yuki" in text for text, _ in msg.messages)


def test_collect_all_reports_partial_failure():
    """Test collect all reports partial failure."""
    jm = _jm()
    p, cc = _patch_cc()
    cc.collect_outputs.return_value = {"success": False, "message": "outputs failed"}
    cc.collect_logs.return_value = {"success": True, "message": "ok"}
    with p:
        msg = jm.collect("all")
    assert any("outputs failed" in text for text, _ in msg.messages)
    assert not any("now in Yuki" in text for text, _ in msg.messages)


def test_collect_reports_skipped_files():
    """Test collect reports skipped files."""
    jm = _jm()
    p, cc = _patch_cc()
    cc.collect.return_value = {
        "success": True,
        "message": {
            "local": {
                "collected": ["plot.png"],
                "skipped": [{"file": "old.png", "reason": "already in Yuki"}],
                "failed": [],
            }
        },
    }
    cc.file_status.return_value = [
        {"name": "plot.png", "size": 100, "in_yuki": True}
    ]
    with p:
        msg = jm.collect("")
    assert any("Skipped 1 file(s)" in text for text, _ in msg.messages)
    assert any("[local] old.png: already in Yuki" in text for text, _ in msg.messages)


def test_collect_reports_failed_files():
    """Test collect reports failed files."""
    jm = _jm()
    p, cc = _patch_cc()
    cc.collect.return_value = {
        "success": True,
        "message": {
            "local": {
                "collected": [],
                "skipped": [],
                "failed": [{"file": "big.root", "reason": "Connection reset"}],
            }
        },
    }
    cc.file_status.return_value = []
    with p:
        msg = jm.collect("")
    assert any("Failed 1 file(s)" in text for text, _ in msg.messages)
    assert any("[local] big.root: Connection reset" in text for text, _ in msg.messages)


def test_collect_files_nested_report():
    """Test collect files nested report."""
    jm = _jm()
    p, cc = _patch_cc()
    cc.collect_files.return_value = {
        "success": True,
        "message": {
            "*.root": {
                "local": {
                    "collected": ["data.root"],
                    "skipped": [{"file": "plot.png", "reason": "does not match selector"}],
                    "failed": [],
                }
            }
        },
    }
    cc.file_status.return_value = [
        {"name": "data.root", "size": 100, "in_yuki": True}
    ]
    with p:
        msg = jm.collect("*.root")
    assert any("Skipped 1 file(s)" in text for text, _ in msg.messages)
    assert any("[local] plot.png: does not match selector" in text for text, _ in msg.messages)
