from unittest import mock
from CelebiChrono.kernel.vtask_job import JobManager


class FakeJobManager(JobManager):
    def algorithm(self): return mock.Mock()
    def auto_download(self): return False
    def default_runner(self): return "local"
    def environment(self): return "python:3.9"
    def get_task(self, path): return self
    def input_md5(self): return "abc123"
    def inputs(self): return []
    def memory_limit(self): return "2G"
    def output_files(self): return []
    def parameters(self): return ([], {})
    def set_input_md5(self, path): pass
    def use_eos(self): return False
    def validated(self): return True


def _jm():
    jm = FakeJobManager.__new__(FakeJobManager)
    jm.impression = lambda: mock.Mock(uuid="abc")
    return jm


def _patch_cc():
    cc = mock.Mock()
    return mock.patch(
        "CelebiChrono.kernel.vtask_job.ChernCommunicator.instance",
        return_value=cc), cc


def test_default_calls_light_collect():
    jm = _jm(); p, cc = _patch_cc()
    with p:
        jm.collect("")
    cc.collect.assert_called_once()


def test_all_calls_outputs_and_logs():
    jm = _jm(); p, cc = _patch_cc()
    with p:
        jm.collect("all")
    cc.collect_outputs.assert_called_once()
    cc.collect_logs.assert_called_once()


def test_plots_keyword():
    jm = _jm(); p, cc = _patch_cc()
    with p:
        jm.collect("plots")
    assert cc.collect_files.call_args.kwargs["spec_type"] == "plots"


def test_glob_pattern():
    jm = _jm(); p, cc = _patch_cc()
    with p:
        jm.collect("*.root")
    assert cc.collect_files.call_args.kwargs["pattern"] == "*.root"


def test_data_keyword():
    jm = _jm(); p, cc = _patch_cc()
    with p:
        jm.collect("data")
    assert cc.collect_files.call_args.kwargs["spec_type"] == "data"


def test_logs_keyword():
    jm = _jm(); p, cc = _patch_cc()
    with p:
        jm.collect("logs")
    cc.collect_logs.assert_called_once()


def test_literal_name_routes_to_names():
    jm = _jm(); p, cc = _patch_cc()
    with p:
        jm.collect("mass.png")
    assert cc.collect_files.call_args.kwargs["names"] == ["mass.png"]


def test_outputs_alias_collects_full_stageout():
    jm = _jm(); p, cc = _patch_cc()
    with p:
        jm.collect("outputs")
    cc.collect_outputs.assert_called_once()


def test_check_preceding_jobs_collects_full_stageout():
    jm = FakeJobManager.__new__(FakeJobManager)
    pre = mock.Mock()
    pre.is_impressed_fast.return_value = True
    pre.run_status.return_value = "finished"
    pre.impression.return_value = mock.Mock(uuid="pre")
    jm.inputs = lambda: [pre]
    cc = mock.Mock()
    ok, _msg = jm._check_preceding_jobs(cc)
    assert ok is True
    cc.collect_outputs.assert_called_once_with(pre.impression())
    cc.collect.assert_not_called()
