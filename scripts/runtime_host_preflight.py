"""Host checks required before a native JDIPT acceptance campaign may start."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import os
from pathlib import Path
import uuid
from typing import Any


PASS = "PASS"
FAIL = "FAIL"
NOT_VERIFIED = "NOT_VERIFIED"


class HostPreflightError(RuntimeError):
    """Raised when a native campaign is attempted without a passing preflight."""


def _probe_writable_path(
    path: str | os.PathLike[str] | None,
    *,
    create_directory: bool,
) -> str:
    if path is None:
        return NOT_VERIFIED
    candidate = Path(path)
    try:
        if create_directory:
            candidate.mkdir(parents=True, exist_ok=True)
            parent = candidate
        else:
            parent = candidate.parent
            if not parent.is_dir():
                return FAIL
        probe = parent / f".jdipt-host-preflight-{uuid.uuid4().hex}.tmp"
        probe.write_text("jdipt host preflight\n", encoding="utf-8", newline="\n")
        if probe.read_text(encoding="utf-8") != "jdipt host preflight\n":
            return FAIL
        probe.unlink()
    except (OSError, UnicodeError, TypeError, ValueError):
        return FAIL
    return PASS


def _probe_callback(callback: Callable[[], Any] | None) -> str:
    if callback is None:
        return NOT_VERIFIED
    try:
        return PASS if callback() is True else FAIL
    except Exception:
        return FAIL


def run_host_preflight(
    *,
    app_server_db: str | os.PathLike[str] | None = None,
    sandbox_probe: Callable[[], Any] | None = None,
    temp_path: str | os.PathLike[str] | None = None,
    plugin_runtime_root: str | os.PathLike[str] | None = None,
    native_smoke_probe: Callable[[], Any] | None = None,
) -> dict[str, Any]:
    """Return independent host statuses and whether campaign entry is allowed.

    Missing probes are deliberately ``NOT_VERIFIED``.  No ACL, sandbox, or
    app-server state is changed by this function.
    """

    checks = {
        "APP_SERVER_DB_WRITABLE": _probe_writable_path(
            app_server_db,
            create_directory=False,
        ),
        "SANDBOX_INIT": _probe_callback(sandbox_probe),
        "TEMP_PATH_USABLE": _probe_writable_path(
            temp_path,
            create_directory=True,
        ),
        "PLUGIN_RUNTIME_ROOT_WRITABLE": _probe_writable_path(
            plugin_runtime_root,
            create_directory=True,
        ),
        "CODEX_NATIVE_EXEC_SMOKE": _probe_callback(native_smoke_probe),
    }
    passed = all(status == PASS for status in checks.values())
    return {
        "HOST_PREFLIGHT": PASS if passed else "HOST_PREFLIGHT_FAIL",
        "CAMPAIGN_STATUS": "READY" if passed else "CAMPAIGN_NOT_STARTED",
        "checks": checks,
        "failed_checks": [name for name, status in checks.items() if status != PASS],
    }


def assert_campaign_entry_allowed(result: Mapping[str, Any]) -> None:
    """Enforce the host gate at the native campaign boundary."""

    if not isinstance(result, Mapping) or result.get("CAMPAIGN_STATUS") != "READY":
        failed = (
            ", ".join(result.get("failed_checks", []))
            if isinstance(result, Mapping)
            else "preflight result is invalid"
        )
        raise HostPreflightError(
            "CAMPAIGN_NOT_STARTED: HOST_PREFLIGHT_FAIL" + (f": {failed}" if failed else "")
        )
