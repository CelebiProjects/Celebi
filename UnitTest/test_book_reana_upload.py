import inspect
from CelebiChrono.interface.shell_modules import reana_booking


def test_book_reana_has_upload_param_default_plots_logs():
    sig = inspect.signature(reana_booking.book_reana)
    assert "upload" in sig.parameters
    assert sig.parameters["upload"].default == "plots+logs"


def test_data_dict_includes_upload(monkeypatch):
    captured = {}

    def fake_sync(yuki_url, project_name, tar_buf, data, message):
        captured.update(data)
        return message

    monkeypatch.setattr(reana_booking, "_book_reana_sync", fake_sync)
    monkeypatch.setattr(reana_booking, "_pack_project_to_tar", lambda p: b"x")
    monkeypatch.setattr(reana_booking.os.path, "isdir", lambda p: True)
    monkeypatch.setattr(reana_booking.csys, "project_path", lambda: "/tmp/proj")
    monkeypatch.setattr(reana_booking, "_get_yuki_server_url", lambda: "http://h:1")
    reana_booking.book_reana(project_path="/tmp/proj", upload="plots", stream=False)
    assert captured.get("upload") == "plots"
