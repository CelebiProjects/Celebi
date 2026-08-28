"""Regression tests for three defects found alongside the settings work."""
import os
import tempfile
import unittest
from unittest import mock

from CelebiChrono.interface import merge_resolver
from CelebiChrono.kernel import chern_communicator
from CelebiChrono.utils import container_manager


class TestDockerSocket(unittest.TestCase):

    """The Docker client must not point at one developer's home directory."""

    def test_uses_environment_based_client(self):
        """Docker connection comes from the environment, not a fixed path."""
        with mock.patch.object(container_manager, "docker") as docker_mod:
            container_manager.ContainerManager("img", {})
        docker_mod.DockerClient.assert_not_called()
        docker_mod.from_env.assert_called_once_with()

    def test_no_hardcoded_home_path_in_source(self):
        """No absolute /Users/<someone> path may remain in the module."""
        with open(
            container_manager.__file__, encoding="utf-8"
        ) as f:
            source = f.read()
        self.assertNotIn("/Users/", source)


class TestMergeResolverEditor(unittest.TestCase):

    """The merge resolver must honour the `editor` user setting."""

    def setUp(self):
        """Isolate HOME and configure a distinctive editor."""
        # pylint: disable=consider-using-with
        self.home = tempfile.TemporaryDirectory()
        self.addCleanup(self.home.cleanup)
        home_path = os.path.realpath(self.home.name)
        patcher = mock.patch.dict(
            os.environ, {"HOME": home_path, "EDITOR": "should-be-ignored"}
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        celebi_dir = os.path.join(home_path, ".celebi")
        os.makedirs(celebi_dir, exist_ok=True)
        with open(
            os.path.join(celebi_dir, "config.yaml"), "w", encoding="utf-8"
        ) as f:
            f.write("editor: myeditor\n")

    def test_uses_configured_editor_over_environment(self):
        """`editor` in config.yaml wins over the EDITOR variable."""
        resolver = merge_resolver.MergeResolver.__new__(
            merge_resolver.MergeResolver)
        with mock.patch.object(merge_resolver.subprocess, "run") as run:
            run.return_value.returncode = 0
            resolver._edit_file_manually("/tmp/f.txt")  # pylint: disable=protected-access
        self.assertEqual(run.call_args[0][0][0], "myeditor")


class TestTransferTimeout(unittest.TestCase):

    """The `* 1000` multiplier made these requests effectively un-timeouted."""

    def setUp(self):
        """Build a communicator without running __init__."""
        self.comm = chern_communicator.ChernCommunicator.__new__(
            chern_communicator.ChernCommunicator)
        self.comm.timeout = 10
        self.comm.transfer_timeout = 600
        self.comm.project_uuid = "p"

    def test_transfer_timeout_is_declared(self):
        """A real communicator carries a named transfer timeout."""
        with mock.patch.object(
            chern_communicator.csys, "project_path", return_value="/tmp"
        ), mock.patch.object(chern_communicator.metadata, "ConfigFile"):
            comm = chern_communicator.ChernCommunicator()
        self.assertEqual(comm.transfer_timeout, 600)

    def test_export_uses_transfer_timeout(self):
        """export() no longer multiplies the base timeout by 1000."""
        impression = mock.MagicMock()
        impression.uuid = "i"
        target = os.path.join(tempfile.mkdtemp(), "out.bin")
        with mock.patch.object(self.comm, "serverurl", return_value="h:1"), \
                mock.patch.object(
                    chern_communicator.requests, "get") as get:
            get.return_value.content = b"x"
            self.comm.export(impression, "f.png", target)
        self.assertEqual(get.call_args.kwargs["timeout"], 600)

    def test_watermark_uses_transfer_timeout(self):
        """watermark() uses the named transfer timeout."""
        impression = mock.MagicMock()
        impression.uuid = "i"
        with mock.patch.object(self.comm, "serverurl", return_value="h:1"), \
                mock.patch.object(
                    chern_communicator.requests, "get") as get:
            self.comm.watermark(impression)
        self.assertEqual(get.call_args.kwargs["timeout"], 600)

    def test_no_thousand_multiplier_remains(self):
        """The magic `* 1000` scale factor is gone from the source."""
        with open(
            chern_communicator.__file__, encoding="utf-8"
        ) as f:
            self.assertNotIn("timeout * 1000", f.read())


if __name__ == "__main__":
    unittest.main()
