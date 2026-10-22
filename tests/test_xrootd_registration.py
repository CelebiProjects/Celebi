"""XRootD registration freezes a remote manifest into a datalist task."""
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from CelebiChrono.celebi_cli.commands.object_creation import (
    register_xrootd_data_command,
)
from CelebiChrono.interface.shell_modules import object_creation
from CelebiChrono.kernel.vtask import create_xrootd_data_list_task
from CelebiChrono.utils.metadata import ConfigFile, YamlFile
from CelebiChrono.utils.message import Message


def test_create_xrootd_datalist_task(tmp_path):
    """Canonical XRootD tasks contain a frozen datalist and manifest."""
    ConfigFile(str(tmp_path / ".celebi" / "config.json")).write_variable(
        "object_type", "project")
    target = tmp_path / "sample"
    source = {"type": "xrootd", "url": "root://host//sample", "runner": "cluster"}
    manifest = {"digest": "sha256:abc", "file_count": 2}
    files = ["root://host//sample/a.root", "root://host//sample/b.root"]

    create_xrootd_data_list_task(
        str(target), "sample", source, files, manifest)

    yaml = YamlFile(str(target / "celebi.yaml"))
    assert yaml.read_variable("environment") == "datalist"
    assert yaml.read_variable("datalist") == files
    assert yaml.read_variable("data_source") == source
    assert yaml.read_variable("manifest") == manifest


def test_register_xrootd_data_immediate_result():
    """An immediate server result is attached to the current project."""
    current = MagicMock()
    current.object_type.return_value = "project"
    current.project_path.return_value = "/project"
    current.project_uuid.return_value = "project-id"
    result = {
        "descriptor": "sample",
        "impression_uuid": "impression-id",
        "file_count": 1,
        "files": ["root://host//sample/a.root"],
        "source": {"type": "xrootd"},
        "manifest": {"digest": "sha256:abc"},
    }
    communicator = MagicMock()
    communicator.register_xrootd_data.return_value = {"result": result}

    with patch.object(object_creation, "MANAGER") as manager, \
            patch.object(object_creation, "ChernCommunicator") as cc, \
            patch.object(object_creation, "_fill_registered_xrootd_data",
                         return_value=Message()) as fill:
        manager.current_object.return_value = current
        cc.instance.return_value = communicator
        message = object_creation.register_xrootd_data(
            "cluster", "root://host//sample", checksum="required")

    assert message.success
    communicator.register_xrootd_data.assert_called_once_with(
        "cluster", "root://host//sample", "project-id", None,
        checksum="required")
    fill.assert_called_once_with(
        "/project", current, result, "", "cluster")


def test_register_xrootd_cli_forwards_options():
    """The Click command forwards checksum and timeout options."""
    with patch("CelebiChrono.interface.shell.register_xrootd_data",
               return_value=Message()) as register:
        response = CliRunner().invoke(register_xrootd_data_command, [
            "cluster", "root://host//sample", "--descriptor", "my-sample",
            "--checksum", "none", "--timeout", "120",
        ])

    assert not response.exit_code, response.output
    register.assert_called_once_with(
        "cluster", "root://host//sample", "my-sample", "none", timeout=120)
