"""Hardened registry writer for JDIPT runtime proposition state."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
import os
from typing import Any

from scripts.synthesis_runtime_state import (
    MaterialProposition,
    RuntimeStateError,
    RuntimeTurnState,
    load_runtime_state,
    save_runtime_state,
)

MAX_TEXT_LENGTH = 2048


def _validate_text(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise RuntimeStateError(f"{field} must be a string")
    if len(value) > MAX_TEXT_LENGTH:
        raise RuntimeStateError(f"{field} exceeds the runtime metadata limit")
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise RuntimeStateError(f"{field} contains an invalid Unicode surrogate")
    if any(ord(char) < 32 and char not in "\t\r\n" for char in value):
        raise RuntimeStateError(f"{field} contains a control character")
    return value


def _text_arg(fields: Mapping[str, Any], *names: str) -> str | None:
    for name in names:
        if name in fields and fields[name] is not None:
            value = fields[name]
            if not isinstance(value, str):
                raise RuntimeStateError(f"{name} must be a string")
            value = value.strip()
            _validate_text(value, name)
            return value
    return None


def _modality_kind(proposition: MaterialProposition) -> str:
    modality = (proposition.modality or "").strip().lower()
    polarity = (proposition.polarity or "").strip().lower()
    action = (proposition.operative_verb_lexeme or proposition.legal_action or "").strip().lower()
    prohibited_tokens = (
        "prohibited", "forbidden", "must not", "shall not", "may not", "금지", "하여서는 안"
    )
    mandatory_tokens = ("mandatory", "must", "shall", "required", "의무", "하여야")
    if polarity in {"negative", "prohibited", "forbidden"}:
        return "prohibited"
    if any(token in modality or token in action for token in prohibited_tokens):
        return "prohibited"
    if any(token in modality or token in action for token in mandatory_tokens):
        return "mandatory"
    return "discretionary"


def build_mandatory_render_clause(proposition: MaterialProposition) -> str:
    """Build a deterministic clause without weakening source modality."""
    condition = proposition.condition or "관련 요건"
    procedure = proposition.procedure or "필요한 절차"
    subject = proposition.subject or "권한 있는 주체"
    legal_object = proposition.legal_object or "해당 대상"
    legal_effect = proposition.legal_effect or "정해진 법적 상태"
    action = proposition.operative_verb_lexeme or proposition.legal_action or "법적 조치"
    relation = (proposition.relation_type or "").lower()
    prefix = ""
    if relation in {"exception", "special", "예외", "특례"}:
        prefix = "다만, 예외로 "
    elif relation in {"base", "기본", "본칙"}:
        prefix = "기본 기준으로 "

    if proposition.status == "OPEN":
        return (
            f"확인 필요: {prefix}{condition} 및 {procedure}의 충족 여부에 따라 "
            f"{subject}의 {legal_object}에 대한 원문상 `{action}` 법적 행위와 "
            f"{legal_effect}의 적용 여부는 현재 확정할 수 없다."
        )

    kind = _modality_kind(proposition)
    if kind == "mandatory":
        return (
            f"{prefix}{condition}을 충족하고 {procedure}를 거치면 {subject}는 "
            f"{legal_object}에 대하여 원문상 `{action}`라는 의무적 법적 행위를 하여야 하고, "
            f"그 법적 효과는 {legal_effect}이다."
        )
    if kind == "prohibited":
        return (
            f"{prefix}{condition}에서 {procedure}를 전제로 {subject}는 {legal_object}에 대하여 "
            f"원문상 `{action}` 법적 행위를 하여서는 안 되며, 그 법적 효과는 {legal_effect}이다."
        )
    return (
        f"{prefix}{condition}을 충족하고 {procedure}를 거치면 {subject}는 "
        f"{legal_object}를 {legal_effect}로 {action}할 수 있다."
    )


def register_material_proposition(
    fields: Mapping[str, Any],
    plugin_data: str | os.PathLike[str] | None = None,
) -> RuntimeTurnState:
    """Register or replace one proposition after hardened boundary validation."""
    if not isinstance(fields, Mapping):
        raise RuntimeStateError("registry input must be an object")
    session_id = fields.get("session_id")
    turn_id = fields.get("turn_id")
    status = fields.get("status")
    if not isinstance(session_id, str) or not isinstance(turn_id, str):
        raise RuntimeStateError("session_id and turn_id are required")
    if status not in {"OPEN", "CLOSED"}:
        raise RuntimeStateError("status must be OPEN or CLOSED")
    proposition_id = fields.get("proposition_id")
    if not isinstance(proposition_id, str) or not proposition_id:
        raise RuntimeStateError("proposition_id is required")

    proposition = MaterialProposition(
        proposition_id=proposition_id,
        status=status,
        subject=_text_arg(fields, "subject", "legal_actor"),
        condition=_text_arg(fields, "condition"),
        procedure=_text_arg(fields, "procedure"),
        operative_verb_lexeme=_text_arg(fields, "operative_verb_lexeme"),
        legal_object=_text_arg(fields, "legal_object"),
        legal_effect=_text_arg(fields, "legal_effect", "resulting_status_or_effect"),
        source_clause=_text_arg(fields, "source_clause", "source_proposition", "evidence_span"),
        mandatory_render_clause=None,
        relation_type=_text_arg(fields, "relation_type", "relation_to_base_or_exception"),
        base_proposition_id=_text_arg(fields, "base_proposition_id"),
        exception_proposition_id=_text_arg(fields, "exception_proposition_id"),
        current_status=_text_arg(fields, "current_status", "temporal_status"),
        modality=_text_arg(fields, "modality") or "may",
        legal_action=_text_arg(fields, "legal_action"),
        polarity=_text_arg(fields, "polarity") or "positive",
        materiality=_text_arg(fields, "materiality") or "material",
    )
    proposition = replace(
        proposition,
        mandatory_render_clause=build_mandatory_render_clause(proposition),
    )
    existing = load_runtime_state(session_id, turn_id, plugin_data)
    if existing is None:
        state = RuntimeTurnState(
            session_id=session_id,
            turn_id=turn_id,
            jdipt_active=True,
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
        state = replace(existing, jdipt_active=True, propositions=propositions)
    save_runtime_state(state, plugin_data)
    return state
