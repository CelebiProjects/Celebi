"""Discover the endpoint recorded by a local Yuki service."""

import os
from pathlib import Path
from typing import Optional


DEFAULT_YUKI_ENDPOINT = "127.0.0.1:3315"


def local_yuki_endpoint() -> Optional[str]:
    """Return the current loopback endpoint, if Yuki published one."""
    root = Path(os.environ.get("YUKIDIR") or "~/.Yuki").expanduser() / "run"
    try:
        port = (root / "yuki.port").read_text(encoding="ascii").strip()
        if not port.isdecimal() or len(port) > 5 or not 1 <= int(port) <= 65535:
            return None
    except (OSError, UnicodeError):
        return None

    try:
        pid = (root / "yuki.pid").read_text(encoding="ascii").strip()
        if not pid.isdecimal() or len(pid) > 10 or not 1 <= int(pid) <= 2**31 - 1:
            return None
        os.kill(int(pid), 0)
    except FileNotFoundError:
        # Direct launches can publish a port without the service wrapper's PID file.
        pass
    except (OSError, UnicodeError):
        return None

    return f"127.0.0.1:{int(port)}"
