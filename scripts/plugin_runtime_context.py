"""Fail-closed resolution of the host plugin environment contract."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_plugin_data(
    explicit: str | os.PathLike[str] | None = None,
) -> str | os.PathLike[str] | None:
    """Resolve plugin data without inventing a location.

    An explicit value is used by tests and direct callers. For hook execution,
    the reserved host variable wins whenever it is present, including when it
    is empty. The legacy variable is only a compatibility fallback when the
    reserved key is absent.
    """

    if explicit is not None:
        return explicit
    if "CLAUDE_PLUGIN_DATA" in os.environ:
        return os.environ["CLAUDE_PLUGIN_DATA"]
    return os.environ.get("PLUGIN_DATA")


def is_valid_plugin_data_path(
    value: str | os.PathLike[str] | None,
    *,
    require_existing: bool = True,
) -> bool:
    """Accept only a concrete absolute path, optionally requiring a directory."""

    if value is None:
        return False
    try:
        text = os.fspath(value)
    except TypeError:
        return False
    if not isinstance(text, str) or not text:
        return False
    try:
        path = Path(text)
    except (OSError, RuntimeError, TypeError, ValueError):
        return False
    if not path.is_absolute() or path.name in {"", ".", ".."}:
        return False
    if not require_existing:
        return True
    try:
        return path.is_dir()
    except OSError:
        return False
