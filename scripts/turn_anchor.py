"""Authoritative UserPromptSubmit epoch and Turn Anchor storage."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import uuid
from typing import Any

from scripts.runtime_root import atomic_write_json, exclusive_lock, read_json


ANCHOR_FILENAME = "current-turn-anchor.json"
ANCHOR_STATES = frozenset({"AVAILABLE", "CLAIMED"})


class TurnAnchorError(ValueError):
    """Raised when an authoritative Turn Anchor is unavailable or invalid."""


@dataclass(frozen=True)
class TurnAnchor:
    schema_version: int
    epoch: int
    anchor_id: str
    created_at: str
    state: str


def _path(root: Path) -> Path:
    return root / ANCHOR_FILENAME


def _validate(payload: Any) -> TurnAnchor:
    if not isinstance(payload, dict):
        raise TurnAnchorError("ANCHOR_INVALID: anchor must be an object")
    anchor = TurnAnchor(
        schema_version=payload.get("schema_version"),
        epoch=payload.get("epoch"),
        anchor_id=payload.get("anchor_id"),
        created_at=payload.get("created_at"),
        state=payload.get("state"),
    )
    if anchor.schema_version != 1 or not isinstance(anchor.epoch, int) or anchor.epoch < 1:
        raise TurnAnchorError("ANCHOR_INVALID: anchor epoch/schema is invalid")
    try:
        uuid.UUID(anchor.anchor_id)
    except (AttributeError, ValueError, TypeError) as exc:
        raise TurnAnchorError("ANCHOR_INVALID: anchor id is invalid") from exc
    if not isinstance(anchor.created_at, str) or not anchor.created_at:
        raise TurnAnchorError("ANCHOR_INVALID: created_at is invalid")
    if anchor.state not in ANCHOR_STATES:
        raise TurnAnchorError("ANCHOR_INVALID: anchor state is invalid")
    return anchor


def load_current_turn_anchor(root: Path) -> TurnAnchor:
    path = _path(root)
    if not path.is_file():
        raise TurnAnchorError("ANCHOR_REQUIRED: current Turn Anchor is missing")
    try:
        return _validate(read_json(path))
    except TurnAnchorError:
        raise
    except ValueError as exc:
        raise TurnAnchorError(str(exc)) from exc


def create_turn_anchor(root: Path, now: datetime | None = None) -> TurnAnchor:
    path = _path(root)
    lock = path.with_name(path.name + ".lock")
    with exclusive_lock(lock):
        previous_epoch = 0
        if path.exists():
            previous_epoch = _validate(read_json(path)).epoch
        anchor = TurnAnchor(
            schema_version=1,
            epoch=previous_epoch + 1,
            anchor_id=str(uuid.uuid4()),
            created_at=(now or datetime.now(timezone.utc)).isoformat(),
            state="AVAILABLE",
        )
        atomic_write_json(path, asdict(anchor))
        return anchor


def claim_current_turn_anchor(root: Path) -> TurnAnchor:
    path = _path(root)
    lock = path.with_name(path.name + ".lock")
    with exclusive_lock(lock):
        anchor = load_current_turn_anchor(root)
        if anchor.state != "AVAILABLE":
            raise TurnAnchorError("ANCHOR_ALREADY_CLAIMED: anchor already claimed")
        claimed = TurnAnchor(
            schema_version=anchor.schema_version,
            epoch=anchor.epoch,
            anchor_id=anchor.anchor_id,
            created_at=anchor.created_at,
            state="CLAIMED",
        )
        atomic_write_json(path, asdict(claimed))
        return claimed


def recover_claimed_turn_anchor(
    root: Path,
    expected_anchor_id: str | None = None,
) -> TurnAnchor:
    """Recover a claim left without a durable matching transaction.

    A claimed anchor is retained when the transaction and canonical registry
    both exist for the same epoch.  Otherwise the claim is safely returned to
    AVAILABLE so a failed begin can be retried in the same prompt epoch.
    """

    path = _path(root)
    lock = path.with_name(path.name + ".lock")
    with exclusive_lock(lock):
        anchor = load_current_turn_anchor(root)
        if anchor.state != "CLAIMED":
            return anchor
        if expected_anchor_id is not None and anchor.anchor_id != expected_anchor_id:
            raise TurnAnchorError("ANCHOR_MISMATCH: recovery target is not current")
        valid_transaction = False
        try:
            from scripts.runtime_transaction import load_current_transaction
            from scripts.proposition_registry import RegistryService

            transaction = load_current_transaction(root)
            registry = (
                RegistryService(root).read_canonical_registry(
                    transaction.canonical_registry_id
                )
                if transaction is not None and transaction.canonical_registry_id
                else None
            )
            valid_transaction = bool(
                transaction is not None
                and transaction.epoch == anchor.epoch
                and transaction.anchor_id == anchor.anchor_id
                and transaction.transaction_state in {
                    "PENDING",
                    "LEDGER_RECORDED",
                    "REGISTERING",
                    "ACTIVE",
                    "RECONCILING",
                }
                and registry is not None
                and registry.transaction_id == transaction.transaction_id
            )
        except (OSError, TypeError, ValueError):
            valid_transaction = False
        if valid_transaction:
            return anchor
        recovered = TurnAnchor(
            schema_version=anchor.schema_version,
            epoch=anchor.epoch,
            anchor_id=anchor.anchor_id,
            created_at=anchor.created_at,
            state="AVAILABLE",
        )
        atomic_write_json(path, asdict(recovered))
        return recovered
