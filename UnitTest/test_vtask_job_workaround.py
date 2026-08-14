"""Tests for JobManager workaround helpers that stage predecessor outputs.

These tests verify that nested output paths (e.g. ``subdir/file.root``) create
the required intermediate directories when predecessor impressions are exported
into the workaround ``stageout`` area.
"""
import os
import tempfile
from unittest import mock

from CelebiChrono.kernel.vtask_job import JobManager


# pylint: disable=protected-access
class FakeJobManager(JobManager):
    """Minimal JobManager stand-in that only implements the helpers under test."""

    def __init__(self, project_path, inputs=None):
        # pylint: disable=super-init-not-called
        """Init."""
        self._project_path = project_path
        self._inputs = inputs or []

    # Required abstract stubs
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

    def project_path(self):
        """Project path."""
        return self._project_path

    def inputs(self):
        """Inputs."""
        return self._inputs

    def path_to_alias(self, path):
        """Path to alias."""
        return os.path.basename(path.rstrip(os.sep))


def _make_predecessor(output_files, env="python:3.9", uuid="imp-uuid", path="/tasks/pre"):
    """Build a mocked predecessor task with the given output_files."""
    _ = output_files
    pre = mock.Mock()
    impression = mock.Mock(uuid=uuid)
    pre.impression.return_value = impression
    pre.environment.return_value = env
    pre.invariant_path.return_value = path
    return pre, impression


def _make_communicator(output_files):
    """Build a mocked ChernCommunicator that reports the given output_files."""
    cherncc = mock.Mock()
    cherncc.output_files.return_value = output_files
    return cherncc


def test_link_preceding_jobs_creates_nested_stageout_dirs():
    """_link_preceding_jobs must preserve subdirectory structure of outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pre, impression = _make_predecessor(["flat.root", "subdir/nested.root"])
        jm = FakeJobManager(tmpdir, inputs=[pre])
        cherncc = _make_communicator(["flat.root", "subdir/nested.root"])

        workspace = os.path.join(tmpdir, "workspace")
        os.makedirs(workspace)

        with mock.patch("CelebiChrono.kernel.vtask_job.csys.symlink") as mock_symlink, \
             mock.patch("CelebiChrono.kernel.vtask_job.csys.mkdir") as mock_mkdir:
            jm._link_preceding_jobs(cherncc, workspace)

        cherncc.output_files.assert_called_once_with(impression)
        assert cherncc.export.call_count == 2

        mkdir_calls = [call.args[0] for call in mock_mkdir.call_args_list]
        # Both calls should create the parent directory of the output path,
        # including the nested subdirectory for subdir/nested.root.
        assert any(os.path.basename(call) == "stageout" for call in mkdir_calls)
        assert any(os.path.basename(call) == "subdir" for call in mkdir_calls)

        # Symlink points from workspace alias to the impression temp dir.
        assert mock_symlink.call_count == 1


def test_prepare_mounting_preceding_jobs_creates_nested_stageout_dirs():
    """_prepare_mounting_preceding_jobs must preserve subdirectory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pre, impression = _make_predecessor(["a/b/deep.root"])
        jm = FakeJobManager(tmpdir, inputs=[pre])
        cherncc = _make_communicator(["a/b/deep.root"])

        mount_config = {"base_dir": tmpdir, "mounts": []}

        with mock.patch("CelebiChrono.kernel.vtask_job.csys.mkdir") as mock_mkdir:
            jm._prepare_mounting_preceding_jobs(cherncc, tmpdir, mount_config)

        cherncc.output_files.assert_called_once_with(impression)
        cherncc.export.assert_called_once()

        mkdir_calls = [call.args[0] for call in mock_mkdir.call_args_list]
        # The nested path a/b/deep.root requires stageout/a/b to be created.
        assert any(str(call).endswith(os.path.join("stageout", "a", "b")) for call in mkdir_calls)

        assert len(mount_config["mounts"]) == 1
        assert mount_config["mounts"][0]["target"] == "/workspace/pre"


def test_link_preceding_jobs_skips_existing_temp_dir():
    """_link_preceding_jobs should not re-export if the temp dir already exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pre, _ = _make_predecessor(["flat.root"])
        jm = FakeJobManager(tmpdir, inputs=[pre])
        cherncc = _make_communicator(["flat.root"])

        workspace = os.path.join(tmpdir, "workspace")
        os.makedirs(workspace)

        # Pre-create the impression temp dir so the export branch is skipped.
        os.makedirs(jm._workaround_dir(name="imp-uuid", prefix="chernimp_"))

        with mock.patch("CelebiChrono.kernel.vtask_job.csys.symlink"):
            jm._link_preceding_jobs(cherncc, workspace)

        cherncc.output_files.assert_not_called()
        cherncc.export.assert_not_called()
