"""Canonical structured range-exception relation reconstruction and checking."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import re

from scripts.legal_proposition import (
    LegalProposition,
    Materiality,
    Modality,
    Polarity,
    PropositionStatus,
)


@dataclass(frozen=True)
class RangeExceptionRelation:
    """One source-linked base → range → exception proposition graph."""

    relation_id: str
    relation_type: str
    base_proposition_id: str
    exception_proposition_id: str
    base_rule: str
    exception_rule: str
    base_value: str
    exception_value: str
    condition: str
    procedure: str
    legal_actor: str
    legal_action: str
    operative_verb_lexeme: str
    legal_object: str
    legal_effect: str
    modality: Modality
    polarity: Polarity
    source_id: str
    source_locator: str
    evidence_span: str


@dataclass(frozen=True)
class RelationReconciliationResult:
    relation_id: str
    relation_type: str
    covered: bool
    missing_fields: tuple[str, ...] = ()
    source_proposition_ids: tuple[str, ...] = ()
    source_id: str = ""
    failure_reason: str = ""


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _contains(span: str, value: str) -> bool:
    token = _normalize(value)
    return bool(token) and token in _normalize(span)


def _distance_values(value: str | None) -> tuple[str, ...]:
    if not isinstance(value, str):
        return ()
    return tuple(
        match.group(0).replace(" ", "")
        for match in re.finditer(
            r"\d+(?:\.\d+)?\s*(?:m|미터)", value, re.IGNORECASE
        )
    )


def _is_material(proposition: LegalProposition) -> bool:
    return proposition.materiality is Materiality.MATERIAL


def _is_exception(proposition: LegalProposition) -> bool:
    relation = _normalize(proposition.relation_type or "")
    return any(term in relation for term in ("exception", "special", "예외", "특례"))


def _is_base(proposition: LegalProposition) -> bool:
    relation = _normalize(proposition.relation_type or "")
    return any(term in relation for term in ("base", "main", "본칙", "기본"))


def _base_for(
    exception: LegalProposition,
    propositions: Sequence[LegalProposition],
) -> LegalProposition | None:
    by_id = {item.proposition_id: item for item in propositions}
    if exception.base_proposition_id:
        candidate = by_id.get(exception.base_proposition_id)
        if candidate is not None:
            return candidate
    return next(
        (
            item
            for item in propositions
            if item.exception_proposition_id == exception.proposition_id
            and _is_base(item)
        ),
        None,
    )


def build_range_exception_relation(
    propositions: Sequence[LegalProposition],
) -> RangeExceptionRelation | None:
    """Build a relation only from explicit source-linked proposition fields."""

    candidates = [
        item
        for item in propositions
        if _is_material(item)
        and item.status is PropositionStatus.CLOSED
        and _is_exception(item)
        and item.evidence is not None
    ]
    for exception in candidates:
        base = _base_for(exception, propositions)
        base_rule = exception.base_rule or (base.base_rule if base else None)
        exception_rule = exception.exception_rule
        base_values = _distance_values(base_rule)
        exception_values = _distance_values(exception_rule)
        if not base_rule or not exception_rule or not base_values or not exception_values:
            continue
        base_value = base_values[0]
        exception_value = next(
            (value for value in exception_values if value != base_value),
            "",
        )
        if not exception_value:
            continue
        evidence = exception.evidence
        assert evidence is not None
        return RangeExceptionRelation(
            relation_id="range_exception_relation",
            relation_type="range_exception_relation",
            base_proposition_id=(
                exception.base_proposition_id
                or (base.proposition_id if base else "")
            ),
            exception_proposition_id=exception.proposition_id,
            base_rule=base_rule,
            exception_rule=exception_rule,
            base_value=base_value,
            exception_value=exception_value,
            condition=exception.condition or "",
            procedure=exception.procedure or "",
            legal_actor=exception.subject or "",
            legal_action=exception.legal_action or exception.operative_verb_lexeme or "",
            operative_verb_lexeme=exception.operative_verb_lexeme or "",
            legal_object=exception.legal_object or "",
            legal_effect=exception.legal_effect or "",
            modality=exception.modality or "",
            polarity=exception.polarity or "",
            source_id=evidence.source_id,
            source_locator=evidence.source_locator,
            evidence_span=evidence.evidence_span,
        )
    return None


def _sentence_spans(draft: str) -> tuple[str, ...]:
    normalized = re.sub(r"\s+", " ", draft).strip()
    if not normalized:
        return ()
    return tuple(
        span.strip()
        for span in re.split(r"(?<=[.!?。！？])\s+|\n+", normalized)
        if span.strip()
    )


def _ordered_range_and_labels(
    span: str,
    relation: RangeExceptionRelation,
) -> bool:
    normalized = _normalize(span)
    base_match = re.search(re.escape(_normalize(relation.base_value)), normalized)
    exception_match = re.search(
        re.escape(_normalize(relation.exception_value)), normalized
    )
    if base_match is None or exception_match is None:
        return False
    if base_match.start() >= exception_match.start():
        return False
    base_context = normalized[max(0, base_match.start() - 48) : base_match.end()]
    exception_context = normalized[
        max(base_match.end(), exception_match.start() - 48) : exception_match.end()
    ]
    return (
        any(label in base_context for label in ("기본", "본칙", "base"))
        and any(label in exception_context for label in ("예외", "특례", "exception", "special"))
    )


def _positive_polarity_preserved(span: str, relation: RangeExceptionRelation) -> bool:
    if relation.polarity is Polarity.NEGATIVE:
        return True
    return re.search(
        r"(?:할|하여|하는|를|을)\s*수\s*없|하지\s*아니|하지\s*않|불가|금지|아니다|없다",
        _normalize(span),
    ) is None


def _required_fields(relation: RangeExceptionRelation) -> tuple[tuple[str, str], ...]:
    return (
        ("condition", relation.condition),
        ("procedure", relation.procedure),
        (
            "legal_act",
            relation.operative_verb_lexeme or relation.legal_action,
        ),
        ("legal_object", relation.legal_object),
        ("legal_effect", relation.legal_effect),
    )


def reconcile_range_exception_relation(
    propositions: Sequence[LegalProposition],
    draft: str,
) -> RelationReconciliationResult | None:
    relation = build_range_exception_relation(propositions)
    if relation is None:
        return None
    spans = _sentence_spans(draft)
    for span in spans:
        if not _ordered_range_and_labels(span, relation):
            continue
        if not _positive_polarity_preserved(span, relation):
            continue
        if all(_contains(span, value) for _, value in _required_fields(relation)):
            return RelationReconciliationResult(
                relation_id=relation.relation_id,
                relation_type=relation.relation_type,
                covered=True,
                source_proposition_ids=tuple(
                    item
                    for item in (
                        relation.base_proposition_id,
                        relation.exception_proposition_id,
                    )
                    if item
                ),
                source_id=relation.source_id,
            )

    missing: list[str] = []
    if not any(_ordered_range_and_labels(span, relation) for span in spans):
        missing.extend(("base_rule", "exception_rule"))
    for field, value in _required_fields(relation):
        if not value or not any(_contains(span, value) for span in spans):
            missing.append(field)
    if not any(
        _ordered_range_and_labels(span, relation)
        and all(_contains(span, value) for _, value in _required_fields(relation))
        and _positive_polarity_preserved(span, relation)
        for span in spans
    ):
        missing.append("relation_span")
    return RelationReconciliationResult(
        relation_id=relation.relation_id,
        relation_type=relation.relation_type,
        covered=False,
        missing_fields=tuple(dict.fromkeys(missing)),
        source_proposition_ids=tuple(
            item
            for item in (relation.base_proposition_id, relation.exception_proposition_id)
            if item
        ),
        source_id=relation.source_id,
        failure_reason=(
            "base/exception rule, condition, procedure, legal act, legal object, "
            "and legal effect must remain in one source-linked relation span"
        ),
    )


def render_range_exception_relation(relation: RangeExceptionRelation) -> str:
    """Render the canonical relation for deterministic staged evidence."""

    action = relation.operative_verb_lexeme or relation.legal_action
    return (
        f"기본 기준은 {relation.base_rule}이고 예외 기준은 {relation.exception_rule}인 경우, "
        f"{relation.condition} {relation.procedure} {relation.legal_actor}는 "
        f"{relation.legal_object}를 {relation.legal_effect}로 "
        f"{action}할 수 있다."
    )
