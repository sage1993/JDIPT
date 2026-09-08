"""Secret-safe boundary probe for Task 11R runtime identity evidence."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping


ENV_KEYS = ("PLUGIN_ROOT", "PLUGIN_DATA")
_PRESENCE_STATES = {"ABSENT", "PRESENT_EMPTY", "PRESENT_NONEMPTY"}


def presence_state(value: str | None) -> str:
    """Classify an environment value without collapsing empty and absent."""

    if value is None:
        return "ABSENT"
    if value == "":
        return "PRESENT_EMPTY"
    return "PRESENT_NONEMPTY"


def _safe_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return f"<{type(value).__name__}>"


def _parent_executable() -> str | None:
    """Return the Windows parent image when the platform exposes it."""

    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION,
            False,
            os.getppid(),
        )
        if not handle:
            return None
        try:
            buffer = ctypes.create_unicode_buffer(32768)
            size = wintypes.DWORD(len(buffer))
            if not kernel32.QueryFullProcessImageNameW(
                handle,
                0,
                buffer,
                ctypes.byref(size),
            ):
                return None
            return buffer.value
        finally:
            kernel32.CloseHandle(handle)
    except (AttributeError, OSError, TypeError, ValueError):
        return None


def _module_identity(module_name: str) -> dict[str, Any]:
    module = sys.modules.get(module_name)
    if module is None:
        return {"module": module_name, "status": "NOT_LOADED"}
    raw_path = getattr(module, "__file__", None)
    if not isinstance(raw_path, str) or not raw_path:
        return {"module": module_name, "status": "FILE_UNAVAILABLE"}
    path = Path(raw_path)
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, TypeError, ValueError):
        digest = None
    return {
        "module": module_name,
        "status": "LOADED",
        "path": str(path),
        "sha256": digest,
    }


def capture_context(
    stage: str,
    *,
    event: Mapping[str, Any] | None = None,
    wrapper_command: str | None = None,
    module_names: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Capture only the non-secret fields needed by the Task 11R contract."""

    event = event if isinstance(event, Mapping) else {}
    record: dict[str, Any] = {
        "stage": stage,
        "pid": os.getpid(),
        "ppid": os.getppid(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cwd": os.getcwd(),
        "process_executable": sys.executable,
        "parent_process_identity": _parent_executable(),
        "hook_command_argv": [str(value) for value in sys.argv],
        "wrapper_command": wrapper_command,
        "environment": {},
        "event": {},
        "module_identity": [_module_identity(name) for name in module_names],
    }
    for key in ENV_KEYS:
        value = os.environ.get(key)
        record["environment"][key] = {
            "state": presence_state(value),
            "value": value,
        }
    for key in ("hook_event_name", "tool_name"):
        value = event.get(key)
        record["event"][key] = {
            "state": presence_state(value if isinstance(value, str) else None),
            "value": _safe_value(value),
        }
    record["event"]["session_id"] = {
        "state": presence_state(
            event.get("session_id") if isinstance(event.get("session_id"), str) else None
        ),
        "value": _safe_value(event.get("session_id")),
    }
    record["event"]["turn_id"] = {
        "state": presence_state(
            event.get("turn_id") if isinstance(event.get("turn_id"), str) else None
        ),
        "value": _safe_value(event.get("turn_id")),
    }
    return record


def capture_stdin(
    stage: str,
    raw_input: bytes,
    *,
    wrapper_command: str | None = None,
) -> dict[str, Any]:
    """Capture input metadata and selected event fields without logging payloads."""

    parsed: Mapping[str, Any] | None = None
    parse_success = False
    try:
        value = json.loads(raw_input.decode("utf-8"))
        if isinstance(value, Mapping):
            parsed = value
            parse_success = True
    except (UnicodeError, json.JSONDecodeError):
        pass
    record = capture_context(
        stage,
        event=parsed,
        wrapper_command=wrapper_command,
    )
    record["stdin"] = {
        "received": bool(raw_input),
        "length": len(raw_input),
        "sha256": hashlib.sha256(raw_input).hexdigest(),
        "json_parse_success": parse_success,
        "top_level_keys": sorted(str(key) for key in parsed) if parsed else [],
    }
    return record


def main() -> int:
    raw_input = sys.stdin.buffer.read()
    event = capture_stdin(
        os.environ.get("TASK11R_PROBE_STAGE", "T3"),
        raw_input,
        wrapper_command=os.environ.get("TASK11R_WRAPPER_COMMAND"),
    )
    json.dump(event, sys.stdout, ensure_ascii=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
