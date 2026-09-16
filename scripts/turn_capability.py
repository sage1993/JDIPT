"""Opaque server-issued Turn Capability helpers."""
from __future__ import annotations

import hashlib
import hmac
import secrets


CAPABILITY_PREFIX = "jtc_"
CAPABILITY_BYTES = 32


def issue_capability() -> str:
    return CAPABILITY_PREFIX + secrets.token_urlsafe(CAPABILITY_BYTES)


def capability_digest(capability: str) -> str:
    if not isinstance(capability, str) or not capability.startswith(CAPABILITY_PREFIX):
        raise ValueError("UNKNOWN_CAPABILITY: capability format is invalid")
    return hashlib.sha256(capability.encode("utf-8")).hexdigest()


def verify_capability(capability: str, digest: str) -> bool:
    try:
        computed = capability_digest(capability)
    except (TypeError, UnicodeError, ValueError):
        return False
    return isinstance(digest, str) and hmac.compare_digest(computed, digest)
