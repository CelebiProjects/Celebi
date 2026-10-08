"""Tests for exporting a task into a notebook-based VRE directory."""
import json
from datetime import datetime
from unittest import mock

from CelebiChrono.kernel.vtask_job import JobManager


def test_workaround_vre_exports_results_and_creates_notebook(tmp_path):
    impression = mock.Mock()
    impression.uuid = "abcdef0123456789abcdef0123456789"
    impression.short_uuid.return_value = "abcdef0"

    class FakeTask:
        export = JobManager.export
        workaround_vre = JobManager.workaround_vre

    task = FakeTask()
    task.impression = mock.Mock(return_value=impression)
    task.project_path = mock.Mock(return_value=str(tmp_path))

    communicator = mock.Mock()
    communicator.output_files.return_value = ["plots/result.png", "notes.txt"]

    fixed_time = datetime(2026, 10, 8, 14, 5, 6)
    with mock.patch(
        "CelebiChrono.kernel.vtask_job.ChernCommunicator.instance",
        return_value=communicator,
    ), mock.patch("CelebiChrono.kernel.vtask_job.datetime") as datetime_mock:
        datetime_mock.now.return_value = fixed_time
        notebook_path = JobManager.workaround_vre(task, "*")

    export_dir = (
        tmp_path / "_celebi_workaround" / "20261008-140506-abcdef0"
    )
    assert notebook_path == str(export_dir / "view_results.ipynb")
    assert communicator.export.call_count == 2

    notebook = json.loads((export_dir / "view_results.ipynb").read_text())
    assert notebook["nbformat"] == 4
    assert len(notebook["cells"]) == 3
    sources = "\n".join(cell["source"] for cell in notebook["cells"])
    assert impression.uuid in sources
    assert "IPython.display" in sources
    assert "uproot.open" in sources
    assert str(export_dir) in sources
