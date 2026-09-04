"""Deterministic render contracts for canonical legal propositions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from scripts.legal_proposition import LegalProposition


RenderSlotKind = Literal["effect", "temporal", "open"]


@dataclass(frozen=True)
class RenderSlot:
    slot_id: str
    proposition_id: str
    kind: RenderSlotKind
    text: str


@dataclass(frozen=True)
class PropositionRenderContract:
    proposition_id: str
    slots: tuple[RenderSlot, ...]


def _is_material(proposition: LegalProposition) -> bool:
    return proposition.materiality.strip().lower() in {
        "material",
        "중요",
        "material proposition",
    }


def _relation_prefix(proposition: LegalProposition) -> str:
    relation = (proposition.relation_type or "").strip().lower()
    if any(term in relation for term in ("exception", "special", "예외", "특례")):
        return "다만, 예외로 "
    if any(term in relation for term in ("base", "본칙", "기본")):
        return "기본 기준으로 "
    return ""


def _modality_kind(proposition: LegalProposition) -> str:
    modality = (proposition.modality or "").strip().lower()
    polarity = (proposition.polarity or "").strip().lower()
    action = (
        proposition.operative_verb_lexeme or proposition.legal_action or ""
    ).strip().lower()
    prohibited_tokens = (
        "prohibited",
        "forbidden",
        "must not",
        "shall not",
        "may not",
        "금지",
        "하여서는 안",
        "불허",
    )
    mandatory_tokens = (
        "mandatory",
        "must",
        "shall",
        "required",
        "의무",
        "하여야",
        "해야",
    )
    if polarity in {"negative", "prohibited", "forbidden"}:
        return "prohibited"
    if any(token in modality or token in action for token in prohibited_tokens):
        return "prohibited"
    if any(token in modality or token in action for token in mandatory_tokens):
        return "mandatory"
    return "discretionary"


def _effect_text(proposition: LegalProposition) -> str:
    condition = proposition.condition or "관련 요건"
    procedure = proposition.procedure or "필요한 절차"
    subject = proposition.subject or "권한 있는 주체"
    legal_object = proposition.legal_object or "해당 대상"
    legal_effect = proposition.legal_effect or "정해진 법적 상태"
    action = proposition.operative_verb_lexeme or proposition.legal_action or "법적 조치"
    prefix = _relation_prefix(proposition)
    kind = _modality_kind(proposition)

    if kind == "mandatory":
        return (
            f"{prefix}{condition}을 충족하고 {procedure}를 거치면 {subject}는 "
            f"{legal_object}에 대하여 원문상 `{action}`라는 의무적 법적 행위를 "
            f"하여야 하고, 그 법적 효과는 {legal_effect}이다."
        )
    if kind == "prohibited":
        return (
            f"{prefix}{condition}에서 {procedure}를 전제로 {subject}는 "
            f"{legal_object}에 대하여 원문상 `{action}` 법적 행위를 하여서는 안 되며, "
            f"그 법적 효과는 {legal_effect}이다."
        )
    return (
        f"{prefix}{condition}을 충족하고 {procedure}를 거치면 {subject}는 "
        f"{legal_object}를 {legal_effect}로 {action}할 수 있다."
    )


def _open_context(proposition: LegalProposition) -> str:
    for value in (
        proposition.condition,
        proposition.procedure,
        proposition.legal_action,
        proposition.operative_verb_lexeme,
        proposition.legal_object,
        proposition.legal_effect,
        proposition.relation_type,
    ):
        if value and value.strip():
            return value.strip()
    return "관련 법적 요건"


def _open_text(proposition: LegalProposition) -> str:
    context = _open_context(proposition)
    return (
        f"확인 필요: {context}에 관한 근거와 적용 여부는 "
        "현재 확정할 수 없다."
    )


def _temporal_text(proposition: LegalProposition) -> str:
    assert proposition.evidence is not None
    if proposition.evidence.temporal_render_text:
        return proposition.evidence.temporal_render_text.strip()
    fallback = {
        "CURRENT_CONFIRMED": "현행 기준에 따른다.",
        "HISTORICAL_CONFIRMED": "당시 시행 기준에 따른다.",
        "CURRENT_UNRESOLVED": "현재 적용 여부는 확인 필요하다.",
    }
    return fallback[proposition.evidence.temporal_status]


def build_render_contract(
    proposition: LegalProposition,
) -> PropositionRenderContract:
    """Build the exact deterministic slots required for one proposition."""

    if not _is_material(proposition):
        return PropositionRenderContract(proposition.proposition_id, ())

    if proposition.status == "OPEN":
        slot = RenderSlot(
            slot_id=f"{proposition.proposition_id}:open",
            proposition_id=proposition.proposition_id,
            kind="open",
            text=_open_text(proposition),
        )
        return PropositionRenderContract(proposition.proposition_id, (slot,))

    effect = RenderSlot(
        slot_id=f"{proposition.proposition_id}:effect",
        proposition_id=proposition.proposition_id,
        kind="effect",
        text=_effect_text(proposition),
    )
    temporal = RenderSlot(
        slot_id=f"{proposition.proposition_id}:temporal",
        proposition_id=proposition.proposition_id,
        kind="temporal",
        text=_temporal_text(proposition),
    )
    return PropositionRenderContract(
        proposition.proposition_id,
        (effect, temporal),
    )
