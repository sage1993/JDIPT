"""Trusted runtime-root resolution for the JDIPT server-side state."""
from __future__ import annotations

from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile
import time
import uuid
from typing import Any, Iterator


PLUGIN_ID = "jdipt@sage1993"
SCHEMA_VERSION = 1
RUNTIME_MARKER_FILENAME = "runtime-root.json"


class RuntimeRootError(ValueError):
    """Raised when the server cannot establish a trusted runtime root."""


@dataclass(frozen=True)
class RuntimeRootMarker:
    plugin_id: str
    schema_version: int
    runtime_root_id: str


@dataclass(frozen=True)
class RuntimeRootResolution:
    root: Path
    source: str


def _plugin_cache_runtime_root() -> Path | None:
    """Derive the data root from Codex's host-selected plugin cache cwd."""

    try:
        candidate = _canonical(Path.cwd())
    except (OSError, RuntimeRootError):
        return None

    # Codex resolves .mcp.json's relative cwd to the installed plugin root:
    # <codex>\\plugins\\cache\\sage1993\\jdipt\\<version>. This is a
    # host-selected process boundary, not a model-supplied tool argument.
    plugin_root = candidate
    if plugin_root.parent.name.casefold() != "jdipt":
        return None
    if plugin_root.parent.parent.name.casefold() != "sage1993":
        return None
    if plugin_root.parent.parent.parent.name.casefold() != "cache":
        return None
    if plugin_root.parent.parent.parent.parent.name.casefold() != "plugins":
        return None
    codex_root = plugin_root.parents[4]
    if codex_root.name.casefold() != ".codex":
        return None
    return codex_root / "plugins" / "data" / "jdipt-sage1993"


def _canonical(path: str | os.PathLike[str]) -> Path:
    try:
        candidate = Path(path).expanduser()
    except (TypeError, ValueError) as exc:
        raise RuntimeRootError("RUNTIME_ROOT_INVALID: runtime root is invalid") from exc
    if not candidate.is_absolute():
        raise RuntimeRootError("RUNTIME_ROOT_INVALID: runtime root must be absolute")
    try:
        resolved = candidate.resolve(strict=False)
    except OSError as exc:
        raise RuntimeRootError("RUNTIME_ROOT_INVALID: runtime root cannot be resolved") from exc
    if resolved.name in {"", ".", ".."}:
        raise RuntimeRootError("RUNTIME_ROOT_INVALID: runtime root must be concrete")
    if candidate.is_symlink() or resolved != candidate.absolute():
        raise RuntimeRootError("RUNTIME_ROOT_MISMATCH: runtime root is a reparse or symlink path")
    return resolved


def runtime_root_source(
    plugin_data: str | os.PathLike[str] | None = None,
) -> str:
    """Return the precedence source selected for runtime-root resolution."""

    if plugin_data is not None:
        return "EXPLICIT"
    if os.environ.get("JDIPT_RUNTIME_ROOT") is not None:
        return "JDIPT_RUNTIME_ROOT"
    if os.environ.get("CLAUDE_PLUGIN_DATA") is not None:
        return "CLAUDE_PLUGIN_DATA"
    if os.environ.get("PLUGIN_DATA") is not None:
        return "PLUGIN_DATA"
    if _plugin_cache_runtime_root() is not None:
        return "PLUGIN_CWD"
    return "CODEX_HOME"


def resolve_runtime_root_with_source(
    plugin_data: str | os.PathLike[str] | None = None,
) -> RuntimeRootResolution:
    """Resolve the trusted root without accepting a model-supplied path.

    ``plugin_data`` is an in-process/test override.  The MCP layer never reads
    it from tool arguments; production calls use ``JDIPT_RUNTIME_ROOT``, the
    compatibility ``PLUGIN_DATA`` variable, or the canonical ``CODEX_HOME``
    location.
    """

    explicit = plugin_data is not None
    source = runtime_root_source(plugin_data)
    value: str | os.PathLike[str] | None = plugin_data
    if value is None:
        value = os.environ.get("JDIPT_RUNTIME_ROOT")
    if value is None:
        value = os.environ.get("CLAUDE_PLUGIN_DATA")
    if value is None:
        value = os.environ.get("PLUGIN_DATA")
    if value is None:
        value = _plugin_cache_runtime_root()
    if value is None:
        codex_home = os.environ.get("CODEX_HOME")
        if not codex_home:
            raise RuntimeRootError("RUNTIME_ROOT_REQUIRED: trusted runtime root is unavailable")
        value = Path(codex_home) / "plugins" / "data" / "jdipt-sage1993"
    root = _canonical(value)
    if (
        not explicit
        and os.environ.get("CODEX_HOME")
        and "CLAUDE_PLUGIN_DATA" not in os.environ
        and "PLUGIN_DATA" not in os.environ
    ):
        expected = _canonical(Path(os.environ["CODEX_HOME"]) / "plugins" / "data" / "jdipt-sage1993")
        if root != expected:
            raise RuntimeRootError("RUNTIME_ROOT_MISMATCH: runtime root is outside CODEX_HOME")
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeRootError(f"RUNTIME_ROOT_UNAVAILABLE: {exc}") from exc
    return RuntimeRootResolution(root=root, source=source)


def resolve_runtime_root(
    plugin_data: str | os.PathLike[str] | None = None,
) -> Path:
    """Resolve the trusted root while preserving the legacy Path API."""

    return resolve_runtime_root_with_source(plugin_data).root


def assert_test_runtime_root_isolated(
    root: Path | str,
    production_root: Path | str | None = None,
) -> Path:
    """Reject a test fixture root that resolves to the production root.

    Acceptance fixtures must be explicitly isolated.  This guard is scoped to
    test/acceptance callers; normal native runtime resolution continues to use
    the trusted host-selected root.
    """

    candidate = _canonical(root)
    configured = production_root
    if configured is None:
        configured = os.environ.get("JDIPT_RUNTIME_ROOT")
        if configured is None:
            configured = os.environ.get("CLAUDE_PLUGIN_DATA")
        if configured is None:
            configured = os.environ.get("PLUGIN_DATA")
        if configured is None:
            configured = _plugin_cache_runtime_root()
        if configured is None:
            codex_home = os.environ.get("CODEX_HOME")
            if codex_home:
                configured = Path(codex_home) / "plugins" / "data" / "jdipt-sage1993"
    if configured is not None and candidate == _canonical(configured):
        raise RuntimeRootError(
            "RUNTIME_STATE_CONTAMINATION: test runtime root is the production runtime root"
        )
    return candidate


def _marker_path(root: Path) -> Path:
    return root / RUNTIME_MARKER_FILENAME


def _validate_marker(payload: Any, root: Path) -> RuntimeRootMarker:
    if not isinstance(payload, Mapping):
        raise RuntimeRootError("RUNTIME_ROOT_MISMATCH: runtime marker is not an object")
    marker = RuntimeRootMarker(
        plugin_id=payload.get("plugin_id"),
        schema_version=payload.get("schema_version"),
        runtime_root_id=payload.get("runtime_root_id"),
    )
    if marker.plugin_id != PLUGIN_ID or marker.schema_version != SCHEMA_VERSION:
        raise RuntimeRootError("RUNTIME_ROOT_MISMATCH: runtime marker identity is invalid")
    try:
        uuid.UUID(marker.runtime_root_id)
    except (AttributeError, ValueError, TypeError) as exc:
        raise RuntimeRootError("RUNTIME_ROOT_MISMATCH: runtime root id is invalid") from exc
    if _canonical(root) != root:
        raise RuntimeRootError("RUNTIME_ROOT_MISMATCH: runtime root changed during validation")
    return marker


def ensure_runtime_marker(root: Path) -> RuntimeRootMarker:
    """Create the marker once, then require exact identity on every read."""

    root = _canonical(root)
    path = _marker_path(root)
    lock = path.with_name(path.name + ".lock")
    with exclusive_lock(lock):
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise RuntimeRootError("RUNTIME_ROOT_MISMATCH: runtime marker cannot be read") from exc
            return _validate_marker(payload, root)
        marker = RuntimeRootMarker(
            plugin_id=PLUGIN_ID,
            schema_version=SCHEMA_VERSION,
            runtime_root_id=str(uuid.uuid4()),
        )
        atomic_write_json(path, {
            "plugin_id": marker.plugin_id,
            "schema_version": marker.schema_version,
            "runtime_root_id": marker.runtime_root_id,
        })
        return marker


def load_runtime_marker(root: Path) -> RuntimeRootMarker:
    """Read and validate an existing runtime marker without creating one."""

    root = _canonical(root)
    path = _marker_path(root)
    if not path.is_file():
        raise RuntimeRootError("RUNTIME_ROOT_MISSING: runtime marker is missing")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeRootError("RUNTIME_ROOT_MISMATCH: runtime marker cannot be read") from exc
    return _validate_marker(payload, root)


@contextmanager
def exclusive_lock(lock_path: Path, *, timeout: float = 5.0) -> Iterator[None]:
    """Acquire a small cross-process lock using atomic file creation."""

    started = time.monotonic()
    descriptor: int | None = None
    while descriptor is None:
        try:
            descriptor = os.open(
                lock_path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            )
            os.write(descriptor, str(os.getpid()).encode("ascii", "replace"))
        except FileExistsError:
            if time.monotonic() - started >= timeout:
                raise RuntimeRootError("RUNTIME_LOCK_TIMEOUT: authoritative state is busy")
            time.sleep(0.005)
        except OSError as exc:
            raise RuntimeRootError(f"RUNTIME_LOCK_FAILED: {exc}") from exc
    try:
        yield
    finally:
        try:
            os.close(descriptor)
        except OSError:
            pass
        try:
            lock_path.unlink()
        except OSError:
            pass


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write JSON with flush/fsync/atomic replace."""

    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise RuntimeRootError(f"RUNTIME_WRITE_FAILED: {exc}") from exc


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeRootError(f"RUNTIME_STATE_INVALID: {exc}") from exc
