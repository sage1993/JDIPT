"""Deterministic guards for source-specific legal-effect synthesis.

The Skill is the user-facing generation path.  This module provides the
small, executable boundary used by regression tests and by any future
orchestration that needs to construct or check that path:

    ledger -> mandatory legal-effect sentences -> explanation -> reconcile
    -> bounded repair

It deliberately does not know any case-specific facts or numbers.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import re


_ACTION_LEXEMES: dict[str, tuple[str, ...]] = {
    "designate": ("지정", "designate"),
    "approve": ("승인", "approve"),
    "recognize": ("인정", "recognize"),
    "permit": ("허가", "허용", "permit"),
    "exclude": ("제외", "exclude"),
    "count": ("산입", "계상", "count"),
    "non-application": ("적용하지 아니", "적용하지 않", "미적용", "non-application"),
    "apply": ("적용", "apply"),
    "register": ("등록", "register"),
    "cancel": ("취소", "cancel"),
    "change": ("변경", "change"),
}

_GENERIC_DEGRADATION_TERMS = ("완화", "혜택", "benefit", "relaxation")
_NEUTRAL_TERMS = (
    "확인 필요",
    "확인되지",
    "미확인",
    "검토 필요",
    "판단할 수 없",
    "undetermined",
    "unresolved",
)


@dataclass(frozen=True)
class MaterialProposition:
    """A material proposition carried from evidence into synthesis."""

    proposition_id: str
    materiality: str
    legal_actor: str
    condition: str
    procedure: str
    modality: str
    legal_action: str
    legal_object: str
    resulting_status_or_effect: str
    polarity: str
    relation_to_base_or_exception: str
    source_proposition: str
    evidence_span: str
    closure_status: str
    operative_verb_lexeme: str = ""
    mandatory_render_clause: str = ""
    direct_source: str = ""
    temporal_status: str = ""

    def __post_init__(self) -> None:
        if self.closure_status not in {"OPEN", "CLOSED"}:
            raise ValueError("closure_status must be OPEN or CLOSED")


@dataclass(frozen=True)
class ReconciliationResult:
    covered: bool
    missing_fields: tuple[str, ...] = ()
    failures: tuple[str, ...] = ()


@dataclass(frozen=True)
class DraftReconciliationResult:
    covered: bool
    failures: tuple[str, ...] = ()
    proposition_results: tuple[ReconciliationResult, ...] = ()


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _contains(draft: str, value: str) -> bool:
    token = _normalize(value)
    return bool(token) and token in _normalize(draft)


def _is_material(proposition: MaterialProposition) -> bool:
    return _normalize(proposition.materiality) in {"material", "중요", "material proposition"}


def _action_terms(proposition: MaterialProposition) -> tuple[str, ...]:
    if proposition.operative_verb_lexeme:
        return (proposition.operative_verb_lexeme,)
    return _ACTION_LEXEMES.get(
        _normalize(proposition.legal_action),
        (proposition.legal_action,),
    )


def _modality_terms(modality: str) -> tuple[str, ...]:
    normalized = _normalize(modality)
    if normalized in {"may", "can", "재량", "가능"}:
        return ("할 수", "가능", "may", "can", "허용")
    if normalized in {"must", "required", "의무"}:
        return ("해야", "하여야", "한다", "필수", "must", "required")
    if normalized in {"must not", "prohibited", "금지"}:
        return ("할 수 없", "해서는 안", "금지", "must not", "prohibited")
    if normalized in {"may not", "불허"}:
        return ("할 수 없", "불가", "허용되지", "may not")
    return (modality,)


def _relation_is_present(proposition: MaterialProposition, draft: str) -> bool:
    relation = _normalize(proposition.relation_to_base_or_exception)
    if not relation:
        return True
    if any(term in relation for term in ("exception", "예외", "special", "특례")):
        return any(_contains(draft, term) for term in ("예외", "특례", "exception", "special"))
    if any(term in relation for term in ("base", "본칙", "기본")):
        return any(_contains(draft, term) for term in ("본칙", "기본", "base"))
    return _contains(draft, proposition.relation_to_base_or_exception)


def _positive_polarity_is_preserved(proposition: MaterialProposition, draft: str) -> bool:
    polarity = _normalize(proposition.polarity)
    if polarity not in {"positive", "affirmative", "적극"}:
        return True
    if _normalize(proposition.legal_action) == "non-application":
        return True
    return not re.search(
        r"(?:할|하여|하는|를|을)\s*수\s*없|하지\s*아니|하지\s*않|불가|금지|아니다|없다",
        _normalize(draft),
    )


def reconcile_proposition(
    proposition: MaterialProposition,
    draft: str,
) -> ReconciliationResult:
    """Check whether ``draft`` preserves one proposition's legal relation."""

    if not _is_material(proposition):
        return ReconciliationResult(covered=True)
    if proposition.closure_status != "CLOSED":
        return ReconciliationResult(covered=False, failures=("OPEN",))

    missing: list[str] = []
    required_values = (
        ("subject / legal actor", proposition.legal_actor),
        ("condition", proposition.condition),
        ("procedure", proposition.procedure),
        ("legal_object", proposition.legal_object),
        ("resulting_status_or_effect", proposition.resulting_status_or_effect),
    )
    for field, value in required_values:
        if value and value not in {"항상", "없음", "none", "N/A"} and not _contains(draft, value):
            missing.append(field)

    if not any(_contains(draft, term) for term in _modality_terms(proposition.modality)):
        missing.append("modality")
    if not any(_contains(draft, term) for term in _action_terms(proposition)):
        missing.append("legal_action")
    if not _relation_is_present(proposition, draft):
        missing.append("relation_to_base_or_exception")
    if not _positive_polarity_is_preserved(proposition, draft):
        missing.append("polarity")

    # A generic range/benefit statement cannot satisfy a missing source action.
    # Keep this as a diagnostic aid; the missing fields remain the actual gate.
    if any(_contains(draft, term) for term in _GENERIC_DEGRADATION_TERMS) and "legal_action" in missing:
        missing.append("specific_legal_effect")

    deduplicated = tuple(dict.fromkeys(missing))
    return ReconciliationResult(covered=not deduplicated, missing_fields=deduplicated)


def _relation_prefix(proposition: MaterialProposition, clause: str) -> str:
    relation = _normalize(proposition.relation_to_base_or_exception)
    if any(term in relation for term in ("exception", "예외", "special", "특례")):
        if not any(_contains(clause, term) for term in ("예외", "특례", "exception", "special")):
            return "다만, 예외로 "
    if any(term in relation for term in ("base", "본칙", "기본")):
        if not any(_contains(clause, term) for term in ("본칙", "기본", "base")):
            return "기본 기준으로 "
    return ""


def _actor_prefix(proposition: MaterialProposition, clause: str) -> str:
    if proposition.legal_actor and not _contains(clause, proposition.legal_actor):
        return f"{proposition.legal_actor}는 "
    return ""


def _action_surface(proposition: MaterialProposition) -> str:
    if proposition.operative_verb_lexeme:
        return proposition.operative_verb_lexeme
    terms = _action_terms(proposition)
    return terms[0]


def _structured_relation_sentence(proposition: MaterialProposition) -> str:
    condition = proposition.condition or "해당 요건"
    procedure = proposition.procedure or "필요한 절차"
    actor = proposition.legal_actor or "권한 있는 주체"
    object_ = proposition.legal_object or "해당 대상"
    effect = proposition.resulting_status_or_effect or "정해진 법적 상태"
    action = _action_surface(proposition)
    modality = _normalize(proposition.modality)
    if modality in {"must", "required", "의무"}:
        ending = f"{action}하여야 한다."
    elif modality in {"must not", "prohibited", "금지", "may not", "불허"}:
        ending = f"{action}할 수 없다."
    else:
        ending = f"{action}할 수 있다."
    return f"{condition}을 충족하고 {procedure}를 거치면 {actor}는 {object_}를 {effect}로 {ending}"


def _open_sentence(proposition: MaterialProposition) -> str:
    condition = proposition.condition or "관련 요건"
    procedure = proposition.procedure or "필요 절차"
    object_ = proposition.legal_object or "해당 대상"
    effect = proposition.resulting_status_or_effect or "해당 법적 상태"
    action = _action_surface(proposition)
    return (
        f"확인 필요: {condition} 및 {procedure}의 충족 여부에 따라 "
        f"{object_}를 {effect}로 {action}할 수 있는지는 현재 확정할 수 없다."
    )


def render_mandatory_proposition_sentence(proposition: MaterialProposition) -> str:
    """Render the non-optional legal-effect sentence for one proposition."""

    if not _is_material(proposition):
        return proposition.source_proposition or proposition.evidence_span
    if proposition.closure_status != "CLOSED":
        return _open_sentence(proposition)

    clause = (
        proposition.mandatory_render_clause
        or proposition.source_proposition
        or proposition.evidence_span
        or _structured_relation_sentence(proposition)
    ).strip()
    clause = f"{_relation_prefix(proposition, clause)}{_actor_prefix(proposition, clause)}{clause}"
    return clause


def _slot_sort_key(item: tuple[int, MaterialProposition]) -> tuple[int, int]:
    index, proposition = item
    relation = _normalize(proposition.relation_to_base_or_exception)
    if "base" in relation or "본칙" in relation or "기본" in relation:
        return (0, index)
    if "exception" in relation or "예외" in relation or "special" in relation or "특례" in relation:
        return (1, index)
    return (2, index)


def render_mandatory_slots(
    propositions: Sequence[MaterialProposition],
) -> tuple[str, ...]:
    """Return one independent mandatory slot for every material proposition."""

    ordered = sorted(enumerate(propositions), key=_slot_sort_key)
    return tuple(
        render_mandatory_proposition_sentence(proposition)
        for _, proposition in ordered
        if _is_material(proposition)
    )


def _has_neutral_status(draft: str) -> bool:
    return any(_contains(draft, term) for term in _NEUTRAL_TERMS)


def reconcile_draft(
    propositions: Sequence[MaterialProposition],
    draft: str,
) -> DraftReconciliationResult:
    """Reconcile all material propositions and reject OPEN promotion."""

    results: list[ReconciliationResult] = []
    failures: list[str] = []
    for proposition in propositions:
        if not _is_material(proposition):
            continue
        if proposition.closure_status == "OPEN":
            result = ReconciliationResult(
                covered=_has_neutral_status(draft),
                failures=() if _has_neutral_status(draft) else ("OPEN",),
            )
        else:
            result = reconcile_proposition(proposition, draft)
        results.append(result)
        failures.extend(result.failures)
        if not result.covered and proposition.closure_status == "CLOSED":
            failures.append(f"{proposition.proposition_id}: material mismatch")

    deduplicated = tuple(dict.fromkeys(failures))
    return DraftReconciliationResult(
        covered=not deduplicated,
        failures=deduplicated,
        proposition_results=tuple(results),
    )


def repair_draft(
    draft: str,
    propositions: Sequence[MaterialProposition],
) -> str:
    """Perform one bounded repair using source/effect-first sentences only."""

    repaired = draft.strip()
    for proposition in propositions:
        if not _is_material(proposition):
            continue
        if proposition.closure_status == "OPEN":
            if not _has_neutral_status(repaired):
                repaired = "\n\n".join(part for part in (repaired, _open_sentence(proposition)) if part)
            continue
        if not reconcile_proposition(proposition, repaired).covered:
            sentence = render_mandatory_proposition_sentence(proposition)
            repaired = "\n\n".join(part for part in (repaired, sentence) if part)
    return repaired


def render_synthesis(
    propositions: Sequence[MaterialProposition],
    *,
    explanatory_synthesis: str = "",
) -> str:
    """Compose mandatory legal effects before optional explanatory synthesis."""

    parts = [*render_mandatory_slots(propositions)]
    if explanatory_synthesis.strip():
        parts.append(explanatory_synthesis.strip())
    draft = "\n\n".join(parts)
    reconciled = reconcile_draft(propositions, draft)
    if not reconciled.covered:
        draft = repair_draft(draft, propositions)
        reconciled = reconcile_draft(propositions, draft)
    if not reconciled.covered:
        raise ValueError(f"unresolved synthesis integrity mismatch: {reconciled.failures}")
    return draft
