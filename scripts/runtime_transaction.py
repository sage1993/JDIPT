"""Canonical single-writer transaction registry for the capability runtime."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections.abc import Mapping
from pathlib import Path
import uuid
from typing import Any

from scripts.runtime_root import (
    RuntimeRootError,
    atomic_write_json,
    ensure_runtime_marker,
    exclusive_lock,
    read_json,
    resolve_runtime_root,
)
from scripts.synthesis_runtime_state import RuntimeStateError
from scripts.material_obligation_ingress import record_material_obligation_ledger
from scripts.material_obligation_ledger import (
    MaterialObligationLedger,
    canonical_material_obligation_ledger_digest,
)
from scripts.proposition_registry import (
    RegistryService,
    registry_path,
    validate_typed_proposition,
)
from scripts.proposition_source_closure import source_relation_failure_code
from scripts.turn_anchor import (
    TurnAnchor,
    TurnAnchorError,
    claim_current_turn_anchor,
    load_current_turn_anchor,
    recover_claimed_turn_anchor,
)
from scripts.turn_capability import capability_digest, issue_capability, verify_capability


TRANSACTION_RELATIVE_PATH = Path("synthesis-runtime") / "runtime-transaction.json"
NON_CLOSED_STATES = frozenset(
    {"PENDING", "LEDGER_RECORDED", "REGISTERING", "ACTIVE", "RECONCILING"}
)
TERMINAL_STATES = frozenset({"CLOSED", "FAILED", "ABORTED_BY_NEW_EPOCH"})
MAX_SEMANTIC_ATTEMPTS = 2
INVALID_CLOSED_STATE_QUARANTINE_ROOT = (
    Path("synthesis-runtime") / "recovery-quarantine"
)


@dataclass
class RuntimeTransaction:
    transaction_id: str
    epoch: int
    anchor_id: str
    capability_digest: str
    runtime_root_id: str
    transaction_state: str
    created_at: str
    ledger_required: bool = True
    ledger_digest: str | None = None
    ledger_count: int = 0
    propositions_registered: bool = False
    registry_completed: bool = False
    finalized: bool = False
    required_proposition_ids: tuple[str, ...] = ()
    canonical_registry_id: str | None = None
    registered_proposition_ids: tuple[str, ...] = ()
    semantic_reconciliation: dict[str, Any] | None = None
    semantic_attempt_count: int = 0
    # This is a response-only compatibility snapshot.  It is deliberately
    # omitted from _as_json and is never used as authoritative legal state.
    propositions: list[dict[str, Any]] = field(default_factory=list, repr=False)
    turn_capability: str | None = field(default=None, repr=False, compare=False)

    @property
    def state(self) -> str:
        """Compatibility alias for the transaction-record state field."""

        return self.transaction_state


def transaction_path(root: Path) -> Path:
    return root / TRANSACTION_RELATIVE_PATH


def _as_json(transaction: RuntimeTransaction) -> dict[str, Any]:
    return {
        "transaction_id": transaction.transaction_id,
        "epoch": transaction.epoch,
        "anchor_id": transaction.anchor_id,
        "capability_digest": transaction.capability_digest,
        "runtime_root_id": transaction.runtime_root_id,
        "transaction_state": transaction.transaction_state,
        "state": transaction.transaction_state,
        "created_at": transaction.created_at,
        "ledger_required": transaction.ledger_required,
        "ledger_digest": transaction.ledger_digest,
        "ledger_count": transaction.ledger_count,
        "propositions_registered": transaction.propositions_registered,
        "registry_completed": transaction.registry_completed,
        "finalized": transaction.finalized,
        "required_proposition_ids": list(transaction.required_proposition_ids),
        "canonical_registry_id": transaction.canonical_registry_id,
        "registered_proposition_ids": list(transaction.registered_proposition_ids),
        "semantic_reconciliation": transaction.semantic_reconciliation,
        "semantic_attempt_count": transaction.semantic_attempt_count,
    }


def _from_json(payload: Any) -> RuntimeTransaction:
    if not isinstance(payload, dict):
        raise RuntimeStateError("runtime transaction must be an object")
    try:
        transaction = RuntimeTransaction(
            transaction_id=payload["transaction_id"],
            epoch=payload["epoch"],
            anchor_id=payload["anchor_id"],
            capability_digest=payload["capability_digest"],
            runtime_root_id=payload["runtime_root_id"],
            transaction_state=payload.get("transaction_state", payload.get("state")),
            created_at=payload["created_at"],
            ledger_required=payload.get("ledger_required", True),
            ledger_digest=payload.get("ledger_digest"),
            ledger_count=payload.get("ledger_count", 0),
            propositions_registered=payload.get("propositions_registered", False),
            registry_completed=payload.get("registry_completed", False),
            finalized=payload.get("finalized", False),
            required_proposition_ids=tuple(payload.get("required_proposition_ids", [])),
            canonical_registry_id=payload.get("canonical_registry_id"),
            registered_proposition_ids=tuple(payload.get("registered_proposition_ids", [])),
            semantic_reconciliation=payload.get("semantic_reconciliation"),
            semantic_attempt_count=payload.get("semantic_attempt_count", 0),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeStateError(f"invalid runtime transaction: {exc}") from exc
    if "state" in payload and payload.get("state") != transaction.transaction_state:
        raise RuntimeStateError("invalid runtime transaction: state fields disagree")
    if not transaction.transaction_id or not transaction.anchor_id or not transaction.runtime_root_id:
        raise RuntimeStateError("invalid runtime transaction identifiers")
    if transaction.transaction_state not in NON_CLOSED_STATES | TERMINAL_STATES:
        raise RuntimeStateError("invalid runtime transaction state")
    if not isinstance(transaction.registered_proposition_ids, tuple):
        raise RuntimeStateError("runtime transaction proposition evidence is invalid")
    if not isinstance(transaction.epoch, int) or transaction.epoch < 1:
        raise RuntimeStateError("invalid runtime transaction epoch")
    if not isinstance(transaction.propositions_registered, bool):
        raise RuntimeStateError("runtime transaction proposition completion is invalid")
    if not isinstance(transaction.registry_completed, bool):
        raise RuntimeStateError("runtime transaction registry completion is invalid")
    if not isinstance(transaction.finalized, bool):
        raise RuntimeStateError("runtime transaction finalization flag is invalid")
    if transaction.semantic_attempt_count not in range(MAX_SEMANTIC_ATTEMPTS + 1):
        raise RuntimeStateError("runtime transaction semantic attempt budget is invalid")
    if transaction.transaction_state == "CLOSED":
        missing = []
        if not transaction.finalized:
            missing.append("finalized")
        if not transaction.registry_completed:
            missing.append("registry_completed")
        if not transaction.propositions_registered:
            missing.append("propositions_registered")
        if not transaction.ledger_required:
            missing.append("ledger_required")
        if not transaction.ledger_digest:
            missing.append("ledger_digest")
        if transaction.ledger_count < 1:
            missing.append("ledger_count")
        if not transaction.canonical_registry_id:
            missing.append("canonical_registry_id")
        if not transaction.registered_proposition_ids:
            missing.append("registered_proposition_ids")
        if missing:
            raise RuntimeStateError(
                "CLOSED_STATE_INVARIANT_VIOLATION: missing " + ", ".join(missing)
            )
    if transaction.semantic_reconciliation is not None and not isinstance(
        transaction.semantic_reconciliation, dict
    ):
        raise RuntimeStateError("runtime transaction reconciliation evidence is invalid")
    return transaction


def save_transaction(transaction: RuntimeTransaction, root: Path) -> RuntimeTransaction:
    path = transaction_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with exclusive_lock(_transaction_lock_path(root)):
        _save_transaction_unlocked(transaction, root)
    return transaction


def _transaction_lock_path(root: Path) -> Path:
    return transaction_path(root).with_name("runtime-transaction.lock")


def _invalid_closed_state_payload(root: Path) -> dict[str, Any] | None:
    """Return a persisted CLOSED payload that cannot satisfy the new contract."""

    path = transaction_path(root)
    try:
        payload = read_json(path)
    except RuntimeRootError as exc:
        raise RuntimeStateError(str(exc)) from exc
    if not isinstance(payload, dict):
        return None
    state = payload.get("transaction_state", payload.get("state"))
    legacy_state = payload.get("state", state)
    if state != "CLOSED" or legacy_state != "CLOSED":
        return None
    try:
        _from_json(payload)
    except RuntimeStateError:
        return payload
    return None


def _quarantine_invalid_closed_state(
    root: Path,
    anchor: TurnAnchor,
    validation_error: RuntimeStateError,
) -> None:
    """Retire an invalid legacy CLOSED snapshot before starting a new epoch.

    A malformed terminal snapshot is never repaired into CLOSED.  Its compact
    transaction and matching canonical-registry records are moved together to
    a recovery quarantine so the next authoritative transaction can start
    without discarding forensic evidence or treating test state as live state.
    """

    payload = _invalid_closed_state_payload(root)
    if payload is None:
        raise validation_error
    transaction_id = payload.get("transaction_id")
    registry = registry_path(root)
    if registry.exists():
        try:
            registry_payload = read_json(registry)
        except RuntimeRootError as exc:
            raise RuntimeStateError(
                "INVALID_CLOSED_STATE_RECOVERY_FAILED: canonical registry cannot be read"
            ) from exc
        if isinstance(registry_payload, dict) and registry_payload.get("transaction_id") not in {
            None,
            transaction_id,
        }:
            raise RuntimeStateError(
                "INVALID_CLOSED_STATE_RECOVERY_FAILED: canonical registry transaction mismatch"
            )

    token = uuid.uuid4().hex
    quarantine = root / INVALID_CLOSED_STATE_QUARANTINE_ROOT / (
        f"invalid-closed-state-{token}"
    )
    try:
        quarantine.mkdir(parents=True, exist_ok=False)
        transaction_path(root).replace(quarantine / "runtime-transaction.json")
        if registry.exists():
            registry.replace(quarantine / "canonical-registry.json")
        atomic_write_json(
            quarantine / "recovery.json",
            {
                "reason_code": "INVALID_CLOSED_STATE_QUARANTINED",
                "validation_error": str(validation_error),
                "source_transaction_id": transaction_id,
                "source_epoch": payload.get("epoch"),
                "replacement_epoch": anchor.epoch,
            },
        )
    except (OSError, RuntimeRootError, TypeError, ValueError) as exc:
        raise RuntimeStateError(
            f"INVALID_CLOSED_STATE_RECOVERY_FAILED: {exc}"
        ) from exc


def _save_transaction_unlocked(
    transaction: RuntimeTransaction,
    root: Path,
) -> RuntimeTransaction:
    path = transaction_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, _as_json(transaction))
    return transaction


def _abort_transaction_for_new_epoch(
    transaction: RuntimeTransaction,
    root: Path,
) -> RuntimeTransaction:
    """Retire transaction and canonical registry as one epoch transition."""

    updated = RuntimeTransaction(
        **{
            **transaction.__dict__,
            "transaction_state": "ABORTED_BY_NEW_EPOCH",
            "turn_capability": None,
        }
    )
    _save_transaction_unlocked(updated, root)
    if updated.canonical_registry_id:
        RegistryService(root).set_state(
            updated,
            "FAILED",
            reconciliation={
                "stage": "ABORTED_BY_NEW_EPOCH",
                "transaction_id": updated.transaction_id,
                "epoch": updated.epoch,
            },
        )
    return updated


def load_current_transaction(
    root: Path,
    *,
    include_registry_snapshot: bool = True,
) -> RuntimeTransaction | None:
    """Load the current transaction, optionally without reading its registry.

    Stop forensic validation uses the transaction record and canonical registry
    as separate evidence sources so a registry read failure is distinguishable
    from a transaction read failure.  Existing callers retain the enriched
    snapshot behavior by default.
    """

    path = transaction_path(root)
    if not path.exists():
        return None
    try:
        transaction = _from_json(read_json(path))
        # Backward-compatible callers may inspect this in-memory snapshot,
        # but the canonical source remains RegistryService's registry file.
        if include_registry_snapshot and transaction.canonical_registry_id:
            registry = RegistryService(root).read_canonical_registry(
                transaction.canonical_registry_id
            )
            if registry is not None:
                transaction = RuntimeTransaction(
                    **{
                        **transaction.__dict__,
                        "propositions": [
                            {
                                "proposition_id": item.proposition_id,
                                "status": getattr(item.status, "value", item.status),
                            }
                            for item in registry.propositions
                        ],
                    }
                )
        return transaction
    except RuntimeRootError as exc:
        raise RuntimeStateError(str(exc)) from exc


def begin_transaction(
    root: Path,
    anchor: TurnAnchor,
    runtime_root_id: str,
) -> RuntimeTransaction:
    path = transaction_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with exclusive_lock(_transaction_lock_path(root)):
        try:
            existing = load_current_transaction(root, include_registry_snapshot=False)
        except RuntimeStateError as exc:
            _quarantine_invalid_closed_state(root, anchor, exc)
            existing = None
        if existing is not None and existing.transaction_state in NON_CLOSED_STATES:
            if existing.epoch == anchor.epoch:
                raise RuntimeStateError("TURN_ALREADY_ACTIVE: current epoch already has a transaction")
            existing = _abort_transaction_for_new_epoch(existing, root)
        capability = issue_capability()
        transaction = RuntimeTransaction(
            transaction_id=str(uuid.uuid4()),
            epoch=anchor.epoch,
            anchor_id=anchor.anchor_id,
            capability_digest=capability_digest(capability),
            runtime_root_id=runtime_root_id,
            transaction_state="PENDING",
            created_at=datetime.now(timezone.utc).isoformat(),
            turn_capability=capability,
        )
        _save_transaction_unlocked(transaction, root)
        try:
            registry = RegistryService(root).create(transaction.transaction_id)
        except Exception as exc:
            failed = RuntimeTransaction(
                **{
                    **transaction.__dict__,
                    "transaction_state": "FAILED",
                    "finalized": False,
                    "turn_capability": None,
                }
            )
            _save_transaction_unlocked(failed, root)
            raise RuntimeStateError(
                f"CANONICAL_REGISTRY_CREATE_FAILED: {exc}"
            ) from exc
        transaction = RuntimeTransaction(
            **{
                **transaction.__dict__,
                "canonical_registry_id": registry.registry_id,
            }
        )
        _save_transaction_unlocked(transaction, root)
        return transaction


def begin_runtime_turn(root: Path | str) -> RuntimeTransaction:
    root = resolve_runtime_root(root)
    marker = ensure_runtime_marker(root)
    try:
        anchor = claim_current_turn_anchor(root)
    except TurnAnchorError as exc:
        if "ANCHOR_ALREADY_CLAIMED" not in str(exc):
            raise
        recovered = recover_claimed_turn_anchor(root)
        if recovered.state != "AVAILABLE":
            raise
        anchor = claim_current_turn_anchor(root)
    try:
        return begin_transaction(root, anchor, marker.runtime_root_id)
    except Exception:
        try:
            recover_claimed_turn_anchor(root, anchor.anchor_id)
        except Exception:
            # Preserve the original begin failure.  Recovery is itself
            # fail-closed and is retried explicitly by the next begin call.
            pass
        raise


def abort_previous_transaction(root: Path, current_epoch: int) -> RuntimeTransaction | None:
    transaction_path(root).parent.mkdir(parents=True, exist_ok=True)
    with exclusive_lock(_transaction_lock_path(root)):
        transaction = load_current_transaction(root)
        if transaction is None or transaction.transaction_state not in NON_CLOSED_STATES:
            return None
        if transaction.epoch >= current_epoch:
            return transaction
        return _abort_transaction_for_new_epoch(transaction, root)


def assert_current_capability(
    capability: str,
    root: Path,
    allowed_states: set[str] | frozenset[str] | None = None,
) -> RuntimeTransaction:
    if not isinstance(capability, str) or not capability:
        raise RuntimeStateError("CAPABILITY_REQUIRED: turn capability is required")
    marker = ensure_runtime_marker(root)
    transaction = load_current_transaction(root)
    if transaction is None:
        raise RuntimeStateError("UNKNOWN_CAPABILITY: transaction is missing")
    if transaction.runtime_root_id != marker.runtime_root_id:
        raise RuntimeStateError("RUNTIME_ROOT_MISMATCH: transaction belongs to another runtime root")
    if not verify_capability(capability, transaction.capability_digest):
        raise RuntimeStateError("UNKNOWN_CAPABILITY: capability digest does not match")
    anchor = load_current_turn_anchor(root)
    if transaction.epoch != anchor.epoch or transaction.anchor_id != anchor.anchor_id:
        raise RuntimeStateError("STALE_TURN_CAPABILITY: transaction is from a stale epoch")
    if transaction.transaction_state == "ABORTED_BY_NEW_EPOCH":
        raise RuntimeStateError("STALE_TURN_CAPABILITY: transaction was aborted by a new epoch")
    if transaction.transaction_state == "CLOSED":
        raise RuntimeStateError("TRANSACTION_CLOSED: transaction is already closed")
    if transaction.transaction_state == "FAILED":
        raise RuntimeStateError("TRANSACTION_FAILED: transaction is failed")
    if allowed_states is not None and transaction.transaction_state not in allowed_states:
        raise RuntimeStateError(
            f"INVALID_TRANSACTION_STATE: expected {sorted(allowed_states)}, got {transaction.transaction_state}"
        )
    return transaction


def _legacy_ledger_adapter(ledger: Mapping[str, Any]) -> dict[str, Any] | None:
    """Normalize the pre-Task-8 test fixture without creating a second digest."""

    obligations = ledger.get("obligations")
    if not isinstance(obligations, list) or not obligations:
        return None
    normalized: list[dict[str, Any]] = []
    for item in obligations:
        if not isinstance(item, Mapping) or not isinstance(item.get("id"), str):
            return None
        normalized.append(
            {
                "obligation_id": item["id"],
                "issue_type": "LEGACY_RUNTIME",
                "source_status": "SOURCE_UNRESOLVED",
                "evidence_source_ids": [],
                "proposition_ids": [item["id"]],
            }
        )
    return {
        "obligations": normalized,
        "verified_source_evidence": [],
    }


def record_ledger(
    capability: str,
    ledger: Mapping[str, Any] | None,
    root: Path,
) -> RuntimeTransaction:
    if ledger is None:
        raise RuntimeStateError("LEDGER_REQUIRED: material obligation ledger is required")
    if not isinstance(ledger, Mapping):
        raise RuntimeStateError("MALFORMED_LEDGER: ledger must be an object")
    with exclusive_lock(_transaction_lock_path(root)):
        transaction = assert_current_capability(capability, root, {"PENDING", "LEDGER_RECORDED"})
        raw_ledger: Mapping[str, Any] = ledger
        try:
            typed_ledger = MaterialObligationLedger.from_mapping(raw_ledger)
        except (TypeError, ValueError) as exc:
            compatibility = _legacy_ledger_adapter(ledger)
            if compatibility is None:
                raise RuntimeStateError(f"MALFORMED_LEDGER: {exc}") from exc
            raw_ledger = compatibility
            try:
                typed_ledger = MaterialObligationLedger.from_mapping(raw_ledger)
            except (TypeError, ValueError) as typed_exc:
                raise RuntimeStateError(f"MALFORMED_LEDGER: {typed_exc}") from typed_exc
        digest = canonical_material_obligation_ledger_digest(typed_ledger)
        if transaction.ledger_digest is not None:
            if transaction.ledger_digest != digest:
                raise RuntimeStateError("LEDGER_MUTATION: ledger digest changed")
            return transaction
        registry = record_material_obligation_ledger(
            {
                "transaction_id": transaction.transaction_id,
                "material_obligation_ledger": raw_ledger,
            },
            root,
        )
        updated = RuntimeTransaction(
            **{
                **transaction.__dict__,
                "transaction_state": "LEDGER_RECORDED",
                "ledger_digest": digest,
                "ledger_count": len(typed_ledger.obligations),
                "required_proposition_ids": tuple(
                    proposition_id
                    for obligation in typed_ledger.obligations
                    for proposition_id in obligation.proposition_ids
                ),
                "canonical_registry_id": registry.registry_id,
                "turn_capability": None,
            }
        )
        return _save_transaction_unlocked(updated, root)


def register_proposition(
    capability: str,
    fields: Mapping[str, Any],
    root: Path,
) -> RuntimeTransaction:
    with exclusive_lock(_transaction_lock_path(root)):
        transaction = assert_current_capability(capability, root)
        if transaction.transaction_state == "PENDING":
            raise RuntimeStateError("LEDGER_REQUIRED: record the material obligation ledger first")
        if transaction.transaction_state == "ACTIVE":
            raise RuntimeStateError("TRANSACTION_ACTIVE: ACTIVE transactions are immutable")
        if transaction.transaction_state not in {"LEDGER_RECORDED", "REGISTERING"}:
            raise RuntimeStateError(
                f"INVALID_TRANSACTION_STATE: expected ['LEDGER_RECORDED', 'REGISTERING'], got {transaction.transaction_state}"
            )
        if transaction.semantic_attempt_count >= MAX_SEMANTIC_ATTEMPTS:
            raise RuntimeStateError(
                "COMMIT_RETRY_EXHAUSTED: semantic validation retry budget is exhausted"
            )
        registry = RegistryService(root).read_canonical_registry(
            transaction.canonical_registry_id
        )
        if registry is None or registry.transaction_id != transaction.transaction_id:
            raise RuntimeStateError("CANONICAL_REGISTRY_MISSING: canonical registry is missing")

        try:
            typed_proposition = None
            if not registry.ledger_compatibility:
                typed_proposition = validate_typed_proposition(fields)
                if typed_proposition.status.value == "CLOSED" and typed_proposition.materiality.value == "MATERIAL":
                    if typed_proposition.evidence not in set(registry.ledger.verified_source_evidence):
                        raise RuntimeStateError(
                            "EVIDENCE_REF_MISMATCH: proposition evidence does not exactly match the submitted ledger"
                        )
                    source_failure = source_relation_failure_code(typed_proposition)
                    if source_failure is not None:
                        raise RuntimeStateError(
                            f"{source_failure}: bound source does not support the declared legal relation"
                        )
            registry = RegistryService(root).register(
                fields,
                transaction_id=transaction.transaction_id,
            )
        except (RuntimeStateError, TypeError, ValueError) as exc:
            next_attempt = transaction.semantic_attempt_count + 1
            exhausted = next_attempt >= MAX_SEMANTIC_ATTEMPTS
            failed = RuntimeTransaction(
                **{
                    **transaction.__dict__,
                    "semantic_attempt_count": next_attempt,
                    "transaction_state": "FAILED" if exhausted else transaction.transaction_state,
                    "turn_capability": None if exhausted else transaction.turn_capability,
                }
            )
            _save_transaction_unlocked(failed, root)
            if exhausted:
                raise RuntimeStateError(
                    "COMMIT_RETRY_EXHAUSTED: semantic validation retry budget is exhausted"
                ) from exc
            raise
        registered_ids = tuple(item.proposition_id for item in registry.propositions)
        complete = registry.registry_state == "ACTIVE"
        proposition = next(
            item for item in registry.propositions
            if item.proposition_id == fields.get("proposition_id")
        )
        updated = RuntimeTransaction(
            **{
                **transaction.__dict__,
                "transaction_state": "ACTIVE" if complete else "REGISTERING",
                "registry_completed": complete,
                "propositions_registered": complete,
                "canonical_registry_id": registry.registry_id,
                "registered_proposition_ids": registered_ids,
                "propositions": [
                    {"proposition_id": item.proposition_id, "status": str(item.status)}
                    for item in registry.propositions
                ],
                "turn_capability": None,
            }
        )
        return _save_transaction_unlocked(updated, root)


def finalize_transaction(capability: str, root: Path) -> RuntimeTransaction:
    with exclusive_lock(_transaction_lock_path(root)):
        transaction = assert_current_capability(capability, root)
        if transaction.ledger_digest is None:
            raise RuntimeStateError("PREREQUISITES_INCOMPLETE: ledger has not been recorded")
        registry = RegistryService(root).read_canonical_registry(transaction.canonical_registry_id)
        if registry is None or registry.transaction_id != transaction.transaction_id:
            raise RuntimeStateError("CANONICAL_REGISTRY_MISSING: canonical registry is missing")
        registered_ids = {item.proposition_id for item in registry.propositions}
        required = set(transaction.required_proposition_ids)
        if not registry.propositions or (required and not required.issubset(registered_ids)):
            raise RuntimeStateError("PROPOSITION_INCOMPLETE: required propositions are not complete")
        if transaction.transaction_state != "ACTIVE":
            raise RuntimeStateError("PREREQUISITES_INCOMPLETE: transaction is not ACTIVE")
        reconciling = RuntimeTransaction(
            **{
                **transaction.__dict__,
                "transaction_state": "RECONCILING",
                "turn_capability": None,
            }
        )
        _save_transaction_unlocked(reconciling, root)
        RegistryService(root).set_state(transaction, "RECONCILING")
        try:
            evidence = RegistryService(root).reconcile(transaction)
        except (OSError, RuntimeError, RuntimeStateError, TypeError, ValueError) as exc:
            evidence = {
                "stage": "RECONCILING",
                "covered": False,
                "semantic_passed": False,
                "registry_closure_passed": False,
                "closure_violations": [],
                "failures": [str(exc)],
                "proposition_ids": list(transaction.registered_proposition_ids),
            }
        if not evidence.get("covered") or not evidence.get("registry_closure_passed"):
            failed = RuntimeTransaction(
                **{
                    **reconciling.__dict__,
                    "transaction_state": "FAILED",
                    "semantic_reconciliation": evidence,
                    "turn_capability": None,
                }
            )
            _save_transaction_unlocked(failed, root)
            RegistryService(root).set_state(transaction, "FAILED", reconciliation=evidence)
            raise RuntimeStateError(
                "SEMANTIC_RECONCILIATION_FAILED: canonical semantic gates did not pass"
            )
        RegistryService(root).set_state(transaction, "CLOSED", reconciliation=evidence)
        closed = RuntimeTransaction(
            **{
                **reconciling.__dict__,
                "transaction_state": "CLOSED",
                "registry_completed": True,
                "finalized": True,
                "semantic_reconciliation": evidence,
                "turn_capability": None,
            }
        )
        return _save_transaction_unlocked(closed, root)
