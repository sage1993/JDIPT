"""The single domain writer for canonical JDIPT proposition state."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
import os
from typing import Any

from scripts.legal_proposition import (
    EvidenceRef,
    LegalProposition,
    PropositionValidationError,
)
from scripts.proposition_rendering import PropositionRenderContract, build_render_contract
from scripts.synthesis_runtime_state import (
    RUNTIME_STATE_SCHEMA_VERSION,
    RuntimeStateError,
    RuntimeTurnState,
    load_runtime_state,
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
        status=fields.get("status"),
        materiality=_text_arg(fields, "materiality") or "material",
        subject=_text_arg(fields, "subject"),
        condition=_text_arg(fields, "condition"),
        procedure=_text_arg(fields, "procedure"),
        modality=_text_arg(fields, "modality"),
        legal_action=_text_arg(fields, "legal_action"),
        operative_verb_lexeme=_text_arg(fields, "operative_verb_lexeme"),
        legal_object=_text_arg(fields, "legal_object"),
        legal_effect=_text_arg(fields, "legal_effect"),
        polarity=_text_arg(fields, "polarity"),
        relation_type=_text_arg(fields, "relation_type"),
        base_proposition_id=_text_arg(fields, "base_proposition_id"),
        exception_proposition_id=_text_arg(fields, "exception_proposition_id"),
        evidence=_build_evidence(fields),
    )


def _merge_state(
    proposition: LegalProposition,
    session_id: str,
    turn_id: str,
    plugin_data: str | os.PathLike[str] | None,
) -> RuntimeTurnState:
    existing = load_runtime_state(session_id, turn_id, plugin_data)
    if existing is None:
        state = RuntimeTurnState(
            schema_version=RUNTIME_STATE_SCHEMA_VERSION,
            session_id=session_id,
            turn_id=turn_id,
            registry_active=True,
            repair_count=0,
            propositions=[proposition],
        )
    else:
        propositions = list(existing.propositions)
        for index, item in enumerate(propositions):
            if item.proposition_id == proposition.proposition_id:
                propositions[index] = proposition
                break
        else:
            propositions.append(proposition)
        state = replace(existing, registry_active=True, propositions=propositions)
    save_runtime_state(state, plugin_data)
    return state


def register_material_proposition(
    fields: Mapping[str, Any],
    plugin_data: str | os.PathLike[str] | None = None,
) -> RegistrationResult:
    """Parse, validate, persist, and render one canonical proposition."""

    if not isinstance(fields, Mapping):
        raise RuntimeStateError("registry input must be an object")
    unknown_fields = sorted(set(fields) - _REGISTRY_FIELDS)
    if unknown_fields:
        raise PropositionValidationError(
            "Unsupported registry arguments: " + ", ".join(unknown_fields)
        )
    session_id = fields.get("session_id")
    turn_id = fields.get("turn_id")
    if not isinstance(session_id, str) or not isinstance(turn_id, str):
        raise RuntimeStateError("session_id and turn_id are required")
    proposition = _build_proposition(fields)
    state = _merge_state(proposition, session_id, turn_id, plugin_data)
    return RegistrationResult(
        state=state,
        proposition=proposition,
        render_contract=build_render_contract(proposition),
    )
