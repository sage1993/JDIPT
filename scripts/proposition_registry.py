"""Canonical legal-state writer for the capability runtime.

The capability transaction is deliberately not a legal-state store.  This
service owns the typed Task 8 ledger, canonical propositions, and the bounded
semantic evidence used by finalization and Stop.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
import os
from pathlib import Path
import uuid
from typing import Any

from scripts.legal_proposition import (
    CANONICAL_PROPOSITION_FIELDS,
    EvidenceRef,
    LegalProposition,
    Materiality,
    PropositionStatus,
    PropositionValidationError,
    normalize_authority_requirement,
    normalize_materiality,
    normalize_modality,
    normalize_polarity,
    normalize_status,
    normalize_temporal_requirement,
)
from scripts.material_obligation_ledger import (
    MaterialObligationLedger,
    ObligationValidationError,
    canonical_material_obligation_ledger_digest,
    material_obligation_ledger_to_dict,
    validate_registry_closure,
)
from scripts.runtime_root import (
    RuntimeRootError,
    atomic_write_json,
    exclusive_lock,
    read_json,
    resolve_runtime_root,
)
from scripts.synthesis_runtime_state import (
    MaterialProposition as LegacyProposition,
    RuntimeStateError,
)


REGISTRY_RELATIVE_PATH = Path("synthesis-runtime") / "canonical-registry.json"
REGISTRY_SCHEMA_VERSION = 1
WRITER_NAME = "RegistryService"
LEDGER_WRITER_NAME = "RegistryService.record_material_obligation_ledger"

_EVIDENCE_FIELDS = (
    "source_id",
    "authority_kind",
    "source_title",
    "source_locator",
    "evidence_span",
    "temporal_status",
    "temporal_render_text",
)
_LEGACY_FIELDS = {
    "proposition_id",
    "status",
    "subject",
    "legal_actor",
    "condition",
    "procedure",
    "operative_verb_lexeme",
    "legal_action",
    "legal_object",
    "legal_effect",
    "source_clause",
    "source_proposition",
    "evidence_span",
    "mandatory_render_clause",
    "relation_type",
    "relation_to_base_or_exception",
    "base_proposition_id",
    "exception_proposition_id",
    "current_status",
    "temporal_status",
    "modality",
    "polarity",
    "materiality",
    "base_rule",
    "exception_rule",
}
# Keep the validator and the public MCP surface on the same typed contract.
# Legacy aliases remain available only through `_build_legacy_proposition`.
_TYPED_FIELDS = CANONICAL_PROPOSITION_FIELDS


@dataclass(frozen=True)
class CanonicalRegistry:
    registry_id: str
    transaction_id: str
    registry_state: str
    created_at: str
    updated_at: str
    ledger: MaterialObligationLedger | None
    propositions: tuple[LegalProposition | LegacyProposition, ...]
    writer: str = WRITER_NAME
    ledger_compatibility: bool = False
    reconciliation: dict[str, Any] | None = None

    @property
    def state(self) -> str:
        return self.registry_state


def registry_path(root: Path) -> Path:
    return root / REGISTRY_RELATIVE_PATH


def _lock_path(root: Path) -> Path:
    return registry_path(root).with_name("canonical-registry.lock")


def _json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


def _proposition_to_json(proposition: LegalProposition | LegacyProposition) -> dict[str, Any]:
    if isinstance(proposition, LegalProposition):
        return {
            "kind": "typed",
            "fields": _json_value(asdict(proposition)),
        }
    if isinstance(proposition, LegacyProposition):
        return {
            "kind": "legacy-compatibility",
            "fields": _json_value(asdict(proposition)),
        }
    raise RuntimeStateError("canonical registry contains an unsupported proposition type")


def _evidence_from_json(value: Any) -> EvidenceRef | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise RuntimeStateError("canonical registry evidence must be an object")
    try:
        return EvidenceRef(**{name: value.get(name) for name in _EVIDENCE_FIELDS})
    except (KeyError, TypeError, ValueError, PropositionValidationError) as exc:
        raise RuntimeStateError(f"invalid canonical proposition evidence: {exc}") from exc


def _proposition_from_json(value: Any) -> LegalProposition | LegacyProposition:
    if not isinstance(value, Mapping):
        raise RuntimeStateError("canonical registry proposition must be an object")
    kind = value.get("kind")
    fields = value.get("fields")
    if not isinstance(fields, Mapping):
        raise RuntimeStateError("canonical registry proposition fields are invalid")
    if kind == "typed":
        payload = dict(fields)
        payload["status"] = normalize_status(payload.get("status"), required=True)
        payload["materiality"] = normalize_materiality(
            payload.get("materiality"), required=True
        )
        payload["modality"] = normalize_modality(payload.get("modality"))
        payload["polarity"] = normalize_polarity(payload.get("polarity"))
        payload["required_authority"] = normalize_authority_requirement(
            payload.get("required_authority", "PRIMARY"), required=True
        )
        payload["required_temporal_status"] = normalize_temporal_requirement(
            payload.get("required_temporal_status", "CURRENT"), required=True
        )
        payload["evidence"] = _evidence_from_json(payload.get("evidence"))
        try:
            return LegalProposition(**payload)
        except (TypeError, ValueError, PropositionValidationError) as exc:
            raise RuntimeStateError(f"invalid canonical proposition: {exc}") from exc
    if kind == "legacy-compatibility":
        try:
            return LegacyProposition(**dict(fields))
        except (TypeError, ValueError, RuntimeStateError) as exc:
            raise RuntimeStateError(f"invalid compatibility proposition: {exc}") from exc
    raise RuntimeStateError("canonical registry proposition kind is invalid")


def _as_json(registry: CanonicalRegistry) -> dict[str, Any]:
    return {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "registry_id": registry.registry_id,
        "transaction_id": registry.transaction_id,
        "registry_state": registry.registry_state,
        "created_at": registry.created_at,
        "updated_at": registry.updated_at,
        "writer": registry.writer,
        "ledger_compatibility": registry.ledger_compatibility,
        "ledger": (
            material_obligation_ledger_to_dict(registry.ledger)
            if registry.ledger is not None
            else None
        ),
        "propositions": [
            _proposition_to_json(item) for item in registry.propositions
        ],
        "reconciliation": registry.reconciliation,
    }


def _from_json(payload: Any) -> CanonicalRegistry:
    if not isinstance(payload, Mapping):
        raise RuntimeStateError("canonical registry must be an object")
    if payload.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        raise RuntimeStateError("canonical registry schema is invalid")
    registry_id = payload.get("registry_id")
    transaction_id = payload.get("transaction_id")
    if not isinstance(registry_id, str) or not registry_id:
        raise RuntimeStateError("canonical registry id is missing")
    if not isinstance(transaction_id, str) or not transaction_id:
        raise RuntimeStateError("canonical registry transaction id is missing")
    try:
        ledger_payload = payload.get("ledger")
        ledger = (
            None
            if ledger_payload is None
            else MaterialObligationLedger.from_mapping(ledger_payload)
        )
        raw_propositions = payload.get("propositions", [])
        if not isinstance(raw_propositions, list):
            raise RuntimeStateError("canonical registry propositions must be a list")
        propositions = tuple(_proposition_from_json(item) for item in raw_propositions)
    except (ObligationValidationError, RuntimeStateError, TypeError, ValueError) as exc:
        if isinstance(exc, RuntimeStateError):
            raise
        raise RuntimeStateError(f"invalid canonical registry contents: {exc}") from exc
    state = payload.get("registry_state")
    if state not in {"PENDING", "REGISTERING", "ACTIVE", "RECONCILING", "CLOSED", "FAILED"}:
        raise RuntimeStateError("canonical registry state is invalid")
    if not isinstance(payload.get("created_at"), str) or not isinstance(
        payload.get("updated_at"), str
    ):
        raise RuntimeStateError("canonical registry timestamps are invalid")
    writer = payload.get("writer", WRITER_NAME)
    if writer not in {WRITER_NAME, LEDGER_WRITER_NAME}:
        raise RuntimeStateError("canonical registry writer is invalid")
    reconciliation = payload.get("reconciliation")
    if reconciliation is not None and not isinstance(reconciliation, dict):
        raise RuntimeStateError("canonical registry reconciliation is invalid")
    return CanonicalRegistry(
        registry_id=registry_id,
        transaction_id=transaction_id,
        registry_state=state,
        created_at=payload["created_at"],
        updated_at=payload["updated_at"],
        ledger=ledger,
        propositions=propositions,
        writer=writer,
        ledger_compatibility=bool(payload.get("ledger_compatibility", False)),
        reconciliation=reconciliation,
    )


def _text_arg(fields: Mapping[str, Any], name: str) -> str | None:
    if name not in fields or fields[name] is None:
        return None
    value = fields[name]
    if not isinstance(value, str):
        raise RuntimeStateError(f"{name} must be a string")
    return value.strip()


def _build_evidence(fields: Mapping[str, Any]) -> EvidenceRef | None:
    present = {name for name in _EVIDENCE_FIELDS if fields.get(name) is not None}
    if not present:
        return None
    required = set(_EVIDENCE_FIELDS) - {"temporal_render_text"}
    missing = sorted(required - present)
    if missing:
        raise PropositionValidationError(
            "evidence fields must be complete; missing: " + ", ".join(missing)
        )
    try:
        return EvidenceRef(
            source_id=_text_arg(fields, "source_id"),
            authority_kind=_text_arg(fields, "authority_kind"),
            source_title=_text_arg(fields, "source_title"),
            source_locator=_text_arg(fields, "source_locator"),
            evidence_span=_text_arg(fields, "evidence_span"),
            temporal_status=_text_arg(fields, "temporal_status"),
            temporal_render_text=_text_arg(fields, "temporal_render_text"),
        )
    except (TypeError, ValueError, PropositionValidationError) as exc:
        raise RuntimeStateError(f"invalid proposition evidence: {exc}") from exc


def _build_typed_proposition(fields: Mapping[str, Any]) -> LegalProposition:
    unknown = sorted(set(fields) - _TYPED_FIELDS)
    if unknown:
        raise RuntimeStateError("unsupported proposition fields: " + ", ".join(unknown))
    try:
        return LegalProposition(
            proposition_id=fields.get("proposition_id"),
            status=normalize_status(fields.get("status"), required=True),
            materiality=normalize_materiality(fields.get("materiality"), required=True),
            subject=_text_arg(fields, "subject") or _text_arg(fields, "legal_actor"),
            condition=_text_arg(fields, "condition"),
            procedure=_text_arg(fields, "procedure"),
            modality=normalize_modality(fields.get("modality")),
            legal_action=_text_arg(fields, "legal_action"),
            operative_verb_lexeme=_text_arg(fields, "operative_verb_lexeme"),
            legal_object=_text_arg(fields, "legal_object"),
            legal_effect=_text_arg(fields, "legal_effect"),
            polarity=normalize_polarity(fields.get("polarity")),
            relation_type=_text_arg(fields, "relation_type"),
            base_proposition_id=_text_arg(fields, "base_proposition_id"),
            exception_proposition_id=_text_arg(fields, "exception_proposition_id"),
            evidence=_build_evidence(fields),
            base_rule=_text_arg(fields, "base_rule"),
            exception_rule=_text_arg(fields, "exception_rule"),
            required_authority=normalize_authority_requirement(
                fields.get("required_authority")
            )
            or normalize_authority_requirement("PRIMARY", required=True),
            required_temporal_status=normalize_temporal_requirement(
                fields.get("required_temporal_status")
            )
            or normalize_temporal_requirement("CURRENT", required=True),
            required_source_type=_text_arg(fields, "required_source_type"),
        )
    except (TypeError, ValueError, PropositionValidationError) as exc:
        message = str(exc)
        if message.startswith("CLOSED proposition is missing"):
            raise RuntimeStateError(
                "CLOSED_PROPOSITION_RELATION_INCOMPLETE: " + message
            ) from exc
        raise RuntimeStateError(f"invalid typed proposition: {exc}") from exc


def _build_legacy_proposition(fields: Mapping[str, Any]) -> LegacyProposition:
    unknown = sorted(set(fields) - _LEGACY_FIELDS)
    if unknown:
        raise RuntimeStateError("unsupported proposition fields: " + ", ".join(unknown))
    proposition = LegacyProposition(
        proposition_id=fields.get("proposition_id"),
        status=fields.get("status"),
        subject=_text_arg(fields, "subject") or _text_arg(fields, "legal_actor"),
        condition=_text_arg(fields, "condition"),
        procedure=_text_arg(fields, "procedure"),
        operative_verb_lexeme=_text_arg(fields, "operative_verb_lexeme"),
        legal_object=_text_arg(fields, "legal_object"),
        legal_effect=_text_arg(fields, "legal_effect"),
        source_clause=_text_arg(fields, "source_clause")
        or _text_arg(fields, "source_proposition")
        or _text_arg(fields, "evidence_span"),
        mandatory_render_clause=None,
        relation_type=_text_arg(fields, "relation_type")
        or _text_arg(fields, "relation_to_base_or_exception"),
        base_proposition_id=_text_arg(fields, "base_proposition_id"),
        exception_proposition_id=_text_arg(fields, "exception_proposition_id"),
        current_status=_text_arg(fields, "current_status")
        or _text_arg(fields, "temporal_status"),
        modality=_text_arg(fields, "modality") or "may",
        legal_action=_text_arg(fields, "legal_action"),
        polarity=_text_arg(fields, "polarity") or "positive",
        materiality=_text_arg(fields, "materiality") or "material",
        base_rule=_text_arg(fields, "base_rule"),
        exception_rule=_text_arg(fields, "exception_rule"),
    )
    # Keep the existing modality-preserving renderer for the compatibility
    # shape.  The RegistryService remains the writer; this helper only builds
    # the deterministic response clause.
    from scripts.runtime_registry_state import build_mandatory_render_clause

    return LegacyProposition(
        **{
            **asdict(proposition),
            "mandatory_render_clause": build_mandatory_render_clause(proposition),
        }
    )


def _build_proposition(fields: Mapping[str, Any]) -> LegalProposition | LegacyProposition:
    if not isinstance(fields, Mapping):
        raise RuntimeStateError("proposition must be an object")
    if "materiality" in fields or any(name in fields for name in _EVIDENCE_FIELDS):
        return _build_typed_proposition(fields)
    return _build_legacy_proposition(fields)


def validate_typed_proposition(fields: Mapping[str, Any]) -> LegalProposition:
    """Parse a typed proposition without mutating the canonical registry."""

    proposition = _build_proposition(fields)
    if not isinstance(proposition, LegalProposition):
        raise RuntimeStateError("TYPED_PROPOSITION_REQUIRED: typed proposition is required")
    return proposition


def _transaction_id(expected: object) -> str:
    if isinstance(expected, str) and expected:
        return expected
    value = getattr(expected, "transaction_id", None)
    if isinstance(value, str) and value:
        return value
    raise RuntimeStateError("canonical registry transaction id is required")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RegistryService:
    """The sole mutable writer for the capability runtime's legal state."""

    def __init__(self, plugin_data: str | os.PathLike[str] | None = None):
        try:
            self.root = resolve_runtime_root(plugin_data)
        except (RuntimeRootError, OSError, TypeError, ValueError) as exc:
            raise RuntimeStateError(str(exc)) from exc

    def _load_unlocked(self) -> CanonicalRegistry | None:
        path = registry_path(self.root)
        if not path.exists():
            return None
        try:
            return _from_json(read_json(path))
        except RuntimeRootError as exc:
            raise RuntimeStateError(str(exc)) from exc

    def _save_unlocked(self, registry: CanonicalRegistry) -> CanonicalRegistry:
        atomic_write_json(registry_path(self.root), _as_json(registry))
        return registry

    def create(self, transaction_id: str) -> CanonicalRegistry:
        if not isinstance(transaction_id, str) or not transaction_id:
            raise RuntimeStateError("canonical registry transaction id is required")
        with exclusive_lock(_lock_path(self.root)):
            existing = self._load_unlocked()
            if existing is not None and existing.transaction_id == transaction_id:
                return existing
            if existing is not None and existing.registry_state not in {"CLOSED", "FAILED"}:
                raise RuntimeStateError("CANONICAL_REGISTRY_ALREADY_ACTIVE: registry is already active")
            timestamp = _now()
            return self._save_unlocked(
                CanonicalRegistry(
                    registry_id=str(uuid.uuid4()),
                    transaction_id=transaction_id,
                    registry_state="PENDING",
                    created_at=timestamp,
                    updated_at=timestamp,
                    ledger=None,
                    propositions=(),
                )
            )

    def read_canonical_registry(self, registry_id: str | None = None) -> CanonicalRegistry | None:
        registry = self._load_unlocked()
        if registry_id is not None and registry is not None and registry.registry_id != registry_id:
            raise RuntimeStateError("CANONICAL_REGISTRY_MISMATCH: registry id does not match")
        return registry

    def record_material_obligation_ledger(
        self,
        expected: object,
        ledger: MaterialObligationLedger,
    ) -> CanonicalRegistry:
        if not isinstance(ledger, MaterialObligationLedger):
            raise RuntimeStateError(
                "material obligation ledger must be a MaterialObligationLedger"
            )
        if not ledger.obligations:
            raise RuntimeStateError("material-obligation ledger requires at least one obligation")
        transaction_id = _transaction_id(expected)
        with exclusive_lock(_lock_path(self.root)):
            current = self._load_unlocked()
            if current is None or current.transaction_id != transaction_id:
                raise RuntimeStateError("CANONICAL_REGISTRY_MISSING: transaction registry is missing")
            if current.registry_state not in {"PENDING", "REGISTERING"}:
                raise RuntimeStateError("LEDGER_AFTER_REGISTRY_COMPLETION: ledger is not mutable")
            digest = canonical_material_obligation_ledger_digest(ledger)
            if current.ledger is not None:
                if canonical_material_obligation_ledger_digest(current.ledger) != digest:
                    raise RuntimeStateError("LEDGER_MUTATION: ledger digest changed")
                return current
            updated = CanonicalRegistry(
                **{
                    **current.__dict__,
                    "registry_state": "REGISTERING",
                    "updated_at": _now(),
                    "ledger": ledger,
                    "writer": LEDGER_WRITER_NAME,
                    "ledger_compatibility": any(
                        item.issue_type == "LEGACY_RUNTIME"
                        for item in ledger.obligations
                    ),
                }
            )
            return self._save_unlocked(updated)

    def register(
        self,
        fields: Mapping[str, Any],
        *,
        transaction_id: str | None = None,
        session_id: str | None = None,
        turn_id: str | None = None,
    ) -> CanonicalRegistry:
        if not isinstance(fields, Mapping):
            raise RuntimeStateError("registry input must be an object")
        if transaction_id is None:
            transaction_id = fields.get("transaction_id")
        proposition = _build_proposition(fields)
        if not transaction_id:
            if session_id and turn_id:
                transaction_id = f"legacy:{session_id}:{turn_id}"
            else:
                raise RuntimeStateError("canonical registry transaction id is required")
        with exclusive_lock(_lock_path(self.root)):
            current = self._load_unlocked()
            if current is None or current.transaction_id != transaction_id:
                raise RuntimeStateError("CANONICAL_REGISTRY_MISSING: transaction registry is missing")
            if current.ledger is None:
                raise RuntimeStateError("LEDGER_REQUIRED: record the material obligation ledger first")
            if not current.ledger_compatibility and not isinstance(proposition, LegalProposition):
                raise RuntimeStateError(
                    "TYPED_PROPOSITION_REQUIRED: typed ledger requires typed propositions"
                )
            if current.registry_state in {"ACTIVE", "CLOSED", "FAILED"}:
                raise RuntimeStateError("TRANSACTION_ACTIVE: canonical registry is immutable")
            if any(item.proposition_id == proposition.proposition_id for item in current.propositions):
                raise RuntimeStateError("PROPOSITION_DUPLICATE: proposition id is already registered")
            propositions = (*current.propositions, proposition)
            required = {
                proposition_id
                for obligation in current.ledger.obligations
                for proposition_id in obligation.proposition_ids
            }
            registered = {item.proposition_id for item in propositions}
            # A proposition is ACTIVE only when the Task 8 ledger explicitly
            # identifies the obligation set it is closing.  An unrelated
            # proposition must never make an unlinked ledger look complete.
            complete = bool(propositions) and bool(required) and required.issubset(registered)
            return self._save_unlocked(
                CanonicalRegistry(
                    **{
                        **current.__dict__,
                        "registry_state": "ACTIVE" if complete else "REGISTERING",
                        "updated_at": _now(),
                        "propositions": propositions,
                        "writer": WRITER_NAME,
                    }
                )
            )

    def set_state(
        self,
        expected: object,
        state: str,
        *,
        reconciliation: dict[str, Any] | None = None,
    ) -> CanonicalRegistry:
        if state not in {"RECONCILING", "CLOSED", "FAILED"}:
            raise RuntimeStateError("canonical registry terminal state is invalid")
        transaction_id = _transaction_id(expected)
        with exclusive_lock(_lock_path(self.root)):
            current = self._load_unlocked()
            if current is None or current.transaction_id != transaction_id:
                raise RuntimeStateError("CANONICAL_REGISTRY_MISSING: transaction registry is missing")
            return self._save_unlocked(
                CanonicalRegistry(
                    **{
                        **current.__dict__,
                        "registry_state": state,
                        "updated_at": _now(),
                        "reconciliation": reconciliation or current.reconciliation,
                        "writer": WRITER_NAME,
                    }
                )
            )

    @staticmethod
    def _to_integrity_proposition(
        proposition: LegalProposition | LegacyProposition,
    ):
        if isinstance(proposition, LegacyProposition):
            return proposition.to_integrity_proposition()
        from scripts.synthesis_integrity import MaterialProposition as IntegrityProposition

        return IntegrityProposition(
            proposition_id=proposition.proposition_id,
            materiality=proposition.materiality.value,
            legal_actor=proposition.subject or "",
            condition=proposition.condition or "",
            procedure=proposition.procedure or "",
            modality=(proposition.modality.value.lower() if proposition.modality else "may"),
            legal_action=proposition.legal_action or "",
            legal_object=proposition.legal_object or "",
            resulting_status_or_effect=proposition.legal_effect or "",
            polarity=(proposition.polarity.value.lower() if proposition.polarity else "positive"),
            relation_to_base_or_exception=proposition.relation_type or "",
            source_proposition=(
                proposition.evidence.evidence_span if proposition.evidence else ""
            ),
            evidence_span=(
                proposition.evidence.evidence_span if proposition.evidence else ""
            ),
            closure_status=proposition.status.value,
            operative_verb_lexeme=proposition.operative_verb_lexeme or "",
            mandatory_render_clause="",
            direct_source=(
                proposition.evidence.source_locator if proposition.evidence else ""
            ),
            temporal_status=(
                proposition.evidence.temporal_status if proposition.evidence else ""
            ),
            base_rule=proposition.base_rule or "",
            exception_rule=proposition.exception_rule or "",
            base_proposition_id=proposition.base_proposition_id or "",
            exception_proposition_id=proposition.exception_proposition_id or "",
        )

    def reconcile(
        self,
        expected: object,
        *,
        draft: str | None = None,
    ) -> dict[str, Any]:
        transaction_id = _transaction_id(expected)
        registry = self.read_canonical_registry()
        if registry is None or registry.transaction_id != transaction_id:
            raise RuntimeStateError("CANONICAL_REGISTRY_MISSING: transaction registry is missing")
        if registry.ledger is None or not registry.propositions:
            raise RuntimeStateError("PROPOSITION_INCOMPLETE: canonical registry is incomplete")
        typed_props = tuple(
            item for item in registry.propositions if isinstance(item, LegalProposition)
        )
        if len(typed_props) == len(registry.propositions):
            return self._reconcile_typed_registry(registry, typed_props, draft=draft)

        integrity_props = tuple(
            self._to_integrity_proposition(item) for item in registry.propositions
        )
        from scripts.synthesis_integrity import (
            reconcile_draft,
            render_mandatory_slots,
        )

        rendered = draft
        if rendered is None:
            rendered = "\n\n".join(render_mandatory_slots(integrity_props))
        semantic = reconcile_draft(integrity_props, rendered)
        registry_closure_passed = True
        closure_violations = []
        return {
            "stage": "RECONCILING",
            "covered": bool(semantic.covered),
            "semantic_passed": bool(semantic.covered),
            "registry_closure_passed": registry_closure_passed,
            "closure_violations": closure_violations,
            "failures": list(semantic.failures),
            "proposition_ids": [item.proposition_id for item in registry.propositions],
        }

    @staticmethod
    def _deterministic_typed_draft(
        propositions: Sequence[LegalProposition],
        contracts: Sequence[Any],
    ) -> str:
        """Build an internal render candidate when finalize has no draft input."""

        lines = ["# 2. 검토결론"]
        for contract in contracts:
            lines.extend(slot.text for slot in contract.slots)
        for proposition in propositions:
            if proposition.evidence is None:
                continue
            evidence = proposition.evidence
            lines.append(
                "근거: "
                f"{evidence.source_id} {evidence.source_title} "
                f"{evidence.source_locator}"
            )
        return "\n".join(lines)

    @staticmethod
    def _reconcile_typed_registry(
        registry: CanonicalRegistry,
        propositions: Sequence[LegalProposition],
        *,
        draft: str | None,
    ) -> dict[str, Any]:
        """Run the Task 9/10 semantic pipeline before a typed turn can close."""

        from dataclasses import asdict as dataclass_asdict

        from scripts.material_obligation_ledger import (
            evaluate_registry_closure,
            registry_closure_result_to_dict,
        )
        from scripts.proposition_obligation_closure import (
            evaluate_obligation_closure,
            obligation_closure_result_to_dict,
        )
        from scripts.proposition_reconciliation import (
            reconcile_render_contracts,
        )
        from scripts.proposition_relations import reconcile_range_exception_relation
        from scripts.proposition_render_coverage import (
            evaluate_render_coverage,
            render_coverage_result_to_dict,
        )
        from scripts.proposition_rendering import build_render_contract
        from scripts.proposition_soundness import (
            evaluate_soundness,
            soundness_result_to_dict,
        )
        from scripts.proposition_source_closure import (
            evaluate_source_closure,
            source_closure_result_to_dict,
        )

        contracts = tuple(build_render_contract(item) for item in propositions)
        rendered = draft if draft is not None else RegistryService._deterministic_typed_draft(
            propositions,
            contracts,
        )
        render_result = reconcile_render_contracts(contracts, rendered)
        relation_result = reconcile_range_exception_relation(propositions, rendered)
        soundness_result = evaluate_soundness(propositions, contracts, rendered)
        source_closure_result = evaluate_source_closure(propositions, rendered)
        obligation_closure_result = evaluate_obligation_closure(
            propositions,
            contracts,
            rendered,
        )
        registry_closure_result = evaluate_registry_closure(
            registry.ledger,
            registry.ledger.verified_source_evidence,
            propositions,
        )
        render_coverage_result = evaluate_render_coverage(
            registry.ledger,
            registry_closure_result,
            propositions,
            rendered,
        )

        overall_render = render_result.covered and (
            relation_result is None or relation_result.covered
        ) and render_coverage_result.coverage_passed
        overall_source = (
            source_closure_result.source_closure_passed
            and source_closure_result.authority_closure_passed
            and source_closure_result.temporal_source_closure_passed
        )
        overall_obligation = (
            obligation_closure_result.obligation_closure_passed
            and obligation_closure_result.dependency_closure_passed
            and obligation_closure_result.final_conclusion_support_passed
        )
        overall_semantic = (
            overall_render
            and soundness_result.soundness_passed
            and overall_source
            and overall_obligation
        )
        overall = overall_semantic and registry_closure_result.registry_closure_passed

        failures: list[str] = []

        def add_failures(label: str, result: Any, passed: bool, *, attr: str = "violations") -> None:
            if passed:
                return
            values = getattr(result, attr, ())
            codes = [getattr(item, "code", "") for item in values]
            codes = [code for code in codes if code]
            failures.append(f"{label}: {', '.join(dict.fromkeys(codes)) or 'failed'}")

        add_failures("render_reconciliation", render_result, render_result.covered)
        if relation_result is not None and not relation_result.covered:
            failures.append(
                "range_exception_relation: "
                + ", ".join(relation_result.missing_fields or ("failed",))
            )
        add_failures("semantic_soundness", soundness_result, soundness_result.soundness_passed)
        add_failures("source_closure", source_closure_result, overall_source)
        add_failures("obligation_closure", obligation_closure_result, overall_obligation)
        add_failures(
            "registry_closure",
            registry_closure_result,
            registry_closure_result.registry_closure_passed,
        )
        if not render_coverage_result.coverage_passed:
            failures.append(
                "render_coverage: "
                + (render_coverage_result.failure_reason or "failed")
            )

        return _json_value(
            {
                "stage": "RECONCILING",
                "covered": overall,
                "semantic_passed": overall_semantic,
                "render_reconciliation": dataclass_asdict(render_result),
                "range_exception_relation": (
                    dataclass_asdict(relation_result)
                    if relation_result is not None
                    else None
                ),
                "soundness": soundness_result_to_dict(soundness_result),
                "source_closure": source_closure_result_to_dict(source_closure_result),
                "obligation_closure": obligation_closure_result_to_dict(
                    obligation_closure_result
                ),
                "registry_closure": registry_closure_result_to_dict(
                    registry_closure_result
                ),
                "registry_closure_passed": registry_closure_result.registry_closure_passed,
                "closure_violations": [
                    item.code for item in registry_closure_result.violations
                ],
                "render_coverage": render_coverage_result_to_dict(
                    render_coverage_result
                ),
                "failures": failures,
                "proposition_ids": [item.proposition_id for item in propositions],
            }
        )

    @staticmethod
    def preflight_typed_turn(
        ledger: MaterialObligationLedger,
        propositions: Sequence[LegalProposition],
    ) -> dict[str, Any]:
        """Run the exact typed semantic gates on prepared data before a begin call."""

        if not isinstance(ledger, MaterialObligationLedger):
            raise RuntimeStateError("material-obligation ledger must be typed")
        if not propositions or any(
            not isinstance(item, LegalProposition) for item in propositions
        ):
            raise RuntimeStateError("typed propositions are required for preflight")
        candidate = CanonicalRegistry(
            registry_id="preflight",
            transaction_id="preflight",
            registry_state="ACTIVE",
            created_at="",
            updated_at="",
            ledger=ledger,
            propositions=tuple(propositions),
        )
        return RegistryService._reconcile_typed_registry(
            candidate,
            propositions,
            draft=None,
        )
