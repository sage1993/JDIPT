"""The single domain writer for canonical JDIPT proposition state."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
import os
from typing import Any

from scripts.legal_proposition import (
    EvidenceRef,
    LegalProposition,
    normalize_materiality,
    normalize_modality,
    normalize_polarity,
    normalize_authority_requirement,
    normalize_temporal_requirement,
    normalize_status,
    PropositionValidationError,
)
from scripts.proposition_rendering import PropositionRenderContract, build_render_contract
from scripts.synthesis_runtime_state import (
    RUNTIME_STATE_SCHEMA_VERSION,
    RuntimeStateError,
    RuntimeTurnState,
    load_runtime_state,
    runtime_state_fingerprint,
    runtime_state_transition_lock,
    save_runtime_state,
)


_EVIDENCE_FIELDS = (
    "source_id",
    "authority_kind",
    "source_title",
    "source_locator",
    "evidence_span",
    "temporal_status",
    "temporal_render_text",
)
_REGISTRY_FIELDS = frozenset(
    {
        "session_id",
        "turn_id",
        "proposition_id",
        "status",
        "materiality",
        "subject",
        "condition",
        "procedure",
        "modality",
        "legal_action",
        "operative_verb_lexeme",
        "legal_object",
        "legal_effect",
        "polarity",
        "relation_type",
        "base_proposition_id",
        "exception_proposition_id",
        "base_rule",
        "exception_rule",
        "required_authority",
        "required_temporal_status",
        "required_source_type",
        *_EVIDENCE_FIELDS,
    }
)


@dataclass(frozen=True)
class RegistrationResult:
    state: RuntimeTurnState
    proposition: LegalProposition
    render_contract: PropositionRenderContract


def _text_arg(fields: Mapping[str, Any], name: str) -> str | None:
    if name not in fields or fields[name] is None:
        return None
    value = fields[name]
    if not isinstance(value, str):
        raise PropositionValidationError(f"{name} must be a string")
    return value.strip()


def _build_evidence(fields: Mapping[str, Any]) -> EvidenceRef | None:
    present = {
        name for name in _EVIDENCE_FIELDS
        if name in fields and fields[name] is not None
    }
    if not present:
        return None
    required = set(_EVIDENCE_FIELDS) - {"temporal_render_text"}
    if not required.issubset(present):
        missing = sorted(required - present)
        raise PropositionValidationError(
            "evidence fields must be complete; missing: " + ", ".join(missing)
        )
    return EvidenceRef(
        source_id=_text_arg(fields, "source_id"),
        authority_kind=_text_arg(fields, "authority_kind"),
        source_title=_text_arg(fields, "source_title"),
        source_locator=_text_arg(fields, "source_locator"),
        evidence_span=_text_arg(fields, "evidence_span"),
        temporal_status=_text_arg(fields, "temporal_status"),
        temporal_render_text=_text_arg(fields, "temporal_render_text"),
    )


def _build_proposition(fields: Mapping[str, Any]) -> LegalProposition:
    return LegalProposition(
        proposition_id=fields.get("proposition_id"),
        status=normalize_status(fields.get("status"), required=True),
        materiality=normalize_materiality(fields.get("materiality"), required=True),
        subject=_text_arg(fields, "subject"),
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
        base_rule=_text_arg(fields, "base_rule"),
        exception_rule=_text_arg(fields, "exception_rule"),
        required_authority=normalize_authority_requirement(
            fields.get("required_authority"),
        ) or normalize_authority_requirement("PRIMARY", required=True),
        required_temporal_status=normalize_temporal_requirement(
            fields.get("required_temporal_status"),
        ) or normalize_temporal_requirement("CURRENT", required=True),
        required_source_type=_text_arg(fields, "required_source_type"),
        evidence=_build_evidence(fields),
    )


class RegistryService:
    """The sole owner of registry lifecycle and proposition write transitions."""

    def __init__(self, plugin_data: str | os.PathLike[str] | None = None):
        self.plugin_data = plugin_data

    def begin_pending(self, session_id: str, turn_id: str) -> RuntimeTurnState:
        """Persist PENDING exactly once for an explicit exact-turn invocation."""

        with runtime_state_transition_lock(
            session_id,
            turn_id,
            self.plugin_data,
        ):
            existing = load_runtime_state(session_id, turn_id, self.plugin_data)
            if existing is not None and existing.registry_required and existing.registry_completed:
                return existing
            if existing is not None and existing.activation_state == "PENDING":
                return existing
            if existing is not None and existing.activation_state == "ACTIVE":
                raise RuntimeStateError(
                    "active registry state cannot be downgraded to PENDING"
                )
            if existing is not None:
                pending = replace(
                    existing,
                    registry_active=False,
                    activation_state="PENDING",
                    registry_required=True,
                    registry_completed=False,
                    registry_required_operations=("register_material_proposition",),
                    registry_enforcement_count=0,
                    stop_disposition=None,
                )
            else:
                pending = RuntimeTurnState(
                    schema_version=RUNTIME_STATE_SCHEMA_VERSION,
                    session_id=session_id,
                    turn_id=turn_id,
                    registry_active=False,
                    repair_count=0,
                    propositions=[],
                    activation_state="PENDING",
                    registry_required=True,
                    registry_completed=False,
                    registry_required_operations=("register_material_proposition",),
                    registry_invocation_count=0,
                    registry_enforcement_count=0,
                )
            save_runtime_state(pending, self.plugin_data)
            return pending

    def register(
        self,
        fields: Mapping[str, Any],
        session_id: str | None = None,
        turn_id: str | None = None,
    ) -> RegistrationResult:
        """Validate, merge, and atomically activate one exact-turn proposition."""

        if not isinstance(fields, Mapping):
            raise RuntimeStateError("registry input must be an object")
        unknown_fields = sorted(set(fields) - _REGISTRY_FIELDS)
        if unknown_fields:
            raise PropositionValidationError(
                "Unsupported registry arguments: " + ", ".join(unknown_fields)
            )
        actual_session_id = fields.get("session_id")
        actual_turn_id = fields.get("turn_id")
        if not isinstance(actual_session_id, str) or not isinstance(actual_turn_id, str):
            raise RuntimeStateError("session_id and turn_id are required")
        if session_id is not None and actual_session_id != session_id:
            raise RuntimeStateError("registry session_id does not match authoritative turn")
        if turn_id is not None and actual_turn_id != turn_id:
            raise RuntimeStateError("registry turn_id does not match authoritative turn")

        proposition = _build_proposition(fields)
        with runtime_state_transition_lock(
            actual_session_id,
            actual_turn_id,
            self.plugin_data,
        ):
            existing = load_runtime_state(
                actual_session_id,
                actual_turn_id,
                self.plugin_data,
            )
            if existing is None:
                propositions = [proposition]
                invocation_count = 1
                repair_count = 0
                enforcement_count = 0
                first_reconciliation = None
                second_reconciliation = None
                stop_disposition = None
            else:
                propositions = list(existing.propositions)
                for index, item in enumerate(propositions):
                    if item.proposition_id == proposition.proposition_id:
                        propositions[index] = proposition
                        break
                else:
                    propositions.append(proposition)
                invocation_count = existing.registry_invocation_count + 1
                repair_count = existing.repair_count
                enforcement_count = existing.registry_enforcement_count
                first_reconciliation = existing.first_reconciliation
                second_reconciliation = existing.second_reconciliation
                stop_disposition = existing.stop_disposition

            state = RuntimeTurnState(
                schema_version=RUNTIME_STATE_SCHEMA_VERSION,
                session_id=actual_session_id,
                turn_id=actual_turn_id,
                registry_active=True,
                repair_count=repair_count,
                propositions=propositions,
                activation_state="ACTIVE",
                registry_required=True,
                registry_completed=True,
                registry_required_operations=("register_material_proposition",),
                registry_invocation_count=invocation_count,
                registry_enforcement_count=enforcement_count,
                first_reconciliation=first_reconciliation,
                second_reconciliation=second_reconciliation,
                stop_disposition=stop_disposition,
            )
            save_runtime_state(state, self.plugin_data)

        return RegistrationResult(
            state=state,
            proposition=proposition,
            render_contract=build_render_contract(proposition),
        )

    def _load_expected(self, expected: RuntimeTurnState) -> RuntimeTurnState:
        current = load_runtime_state(
            expected.session_id,
            expected.turn_id,
            self.plugin_data,
        )
        if current is None or runtime_state_fingerprint(current) != runtime_state_fingerprint(expected):
            raise RuntimeStateError(
                "registry transition expected state is stale or belongs to another turn"
            )
        return current

    def mark_enforcement(
        self,
        expected: RuntimeTurnState,
        disposition: str,
    ) -> RuntimeTurnState:
        """Atomically persist the bounded registry-enforcement transition."""

        if not isinstance(disposition, str) or not disposition:
            raise RuntimeStateError("registry disposition must be a non-empty string")
        with runtime_state_transition_lock(
            expected.session_id,
            expected.turn_id,
            self.plugin_data,
        ):
            current = self._load_expected(expected)
            if (
                not current.registry_required
                or current.registry_completed
                or current.registry_enforcement_count != 0
            ):
                raise RuntimeStateError(
                    "registry enforcement can only transition from 0 to 1 before completion"
                )
            updated = replace(
                current,
                registry_enforcement_count=1,
                stop_disposition=disposition,
            )
            save_runtime_state(updated, self.plugin_data)
            return updated

    def record_disposition(
        self,
        expected: RuntimeTurnState,
        disposition: str,
    ) -> RuntimeTurnState:
        """Persist a disposition only after exact-turn state revalidation."""

        if not isinstance(disposition, str) or not disposition:
            raise RuntimeStateError("registry disposition must be a non-empty string")
        with runtime_state_transition_lock(
            expected.session_id,
            expected.turn_id,
            self.plugin_data,
        ):
            current = self._load_expected(expected)
            updated = replace(current, stop_disposition=disposition)
            save_runtime_state(updated, self.plugin_data)
            return updated


def register_material_proposition(
    fields: Mapping[str, Any],
    plugin_data: str | os.PathLike[str] | None = None,
) -> RegistrationResult:
    """Compatibility boundary delegating the write to the single service."""

    return RegistryService(plugin_data).register(fields)
