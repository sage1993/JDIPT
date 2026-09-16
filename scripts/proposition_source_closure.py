"""Deterministic source, authority, and temporal closure for propositions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum
import re
from typing import Any

from scripts.legal_proposition import (
    AuthorityRequirement,
    LegalProposition,
    Materiality,
    Modality,
    Polarity,
    PropositionStatus,
    TemporalRequirement,
)
from scripts.proposition_soundness import AnswerSpan, classify_answer_regions


@dataclass(frozen=True)
class SourceClosureStatus(StrEnum):
    """The bounded source-closure progression for one material proposition."""

    SOURCE_ABSENT = "SOURCE_ABSENT"
    SOURCE_PRESENT = "SOURCE_PRESENT"
    SOURCE_MATCHED = "SOURCE_MATCHED"
    SOURCE_SUPPORTING = "SOURCE_SUPPORTING"
    SOURCE_AUTHORITY_SATISFIED = "SOURCE_AUTHORITY_SATISFIED"
    SOURCE_TEMPORALLY_VALID = "SOURCE_TEMPORALLY_VALID"
    SOURCE_CLOSED = "SOURCE_CLOSED"


@dataclass(frozen=True)
class SourceClosureAssessment:
    proposition_id: str
    status: SourceClosureStatus
    source_id: str | None
    source_span: str
    matched_span: str
    required_authority: str | None
    actual_authority: str | None
    required_temporal_status: str | None
    actual_temporal_status: str | None
    reason: str


@dataclass(frozen=True)
class SourceClosureViolation:
    code: str
    proposition_id: str
    materiality: str
    modality: str | None
    polarity: str | None
    status: str
    required_source_type: str | None
    actual_source_type: str | None
    required_authority: str | None
    actual_authority: str | None
    source_id: str | None
    source_span: str
    matched_span: str
    required_condition: str | None
    matched_condition: str | None
    required_exception: str | None
    matched_exception: str | None
    required_procedure: str | None
    matched_procedure: str | None
    dependency_proposition_ids: tuple[str, ...]
    final_conclusion_span: str
    reason: str


@dataclass(frozen=True)
class SourceClosureResult:
    source_closure_passed: bool
    authority_closure_passed: bool
    temporal_source_closure_passed: bool
    violations: tuple[SourceClosureViolation, ...]
    assessments: tuple[SourceClosureAssessment, ...] = ()


_TOKEN_RE = re.compile(r"[a-z0-9]+|[가-힣]+", re.IGNORECASE)
_PRIMARY_AUTHORITY = frozenset({"statute", "regulation", "ordinance"})
_NEGATIVE_SOURCE_RE = re.compile(
    r"(?:하여서는\s*안|해서는\s*안|금지|불가|불가능|허용되지|하지\s*않아야)",
    re.IGNORECASE,
)
_MANDATORY_SOURCE_RE = re.compile(
    r"(?:하여야\s*한다|해야\s*한다|의무|반드시)",
    re.IGNORECASE,
)
_DISCRETIONARY_SOURCE_RE = re.compile(
    r"(?:할\s*수\s*있|가능|재량)",
    re.IGNORECASE,
)


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(_TOKEN_RE.findall(value.casefold()))


def _token_matches(expected: str, actual: str) -> bool:
    if expected == actual:
        return True
    if re.fullmatch(r"[가-힣]+", expected) and actual.startswith(expected):
        return len(actual) - len(expected) <= 4
    return False


def _phrase_present(phrase: str | None, text: str) -> bool:
    expected = _tokens(_text(phrase))
    actual = _tokens(text)
    if not expected:
        return True
    width = len(expected)
    return any(
        all(_token_matches(wanted, found) for wanted, found in zip(expected, actual[index : index + width], strict=True))
        for index in range(len(actual) - width + 1)
    )


def _enum_value(value: object) -> str | None:
    return None if value is None else str(getattr(value, "value", value))


def _final_conclusion_span(spans: Sequence[AnswerSpan]) -> str:
    return " ".join(
        span.text.strip()
        for span in spans
        if span.kind == "final_conclusion" and span.text.strip()
    ).strip()


def _adopted_text(spans: Sequence[AnswerSpan]) -> str:
    return " ".join(
        span.text.strip()
        for span in spans
        if span.adopted and span.text.strip()
    ).strip()


def _dependency_ids(proposition: LegalProposition) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            value
            for value in (
                proposition.base_proposition_id,
                proposition.exception_proposition_id,
            )
            if value
        )
    )


def _violation(
    proposition: LegalProposition,
    code: str,
    *,
    source_span: str = "",
    matched_span: str = "",
    matched_condition: str | None = None,
    matched_exception: str | None = None,
    matched_procedure: str | None = None,
    final_conclusion_span: str = "",
    reason: str,
) -> SourceClosureViolation:
    evidence = proposition.evidence
    return SourceClosureViolation(
        code=code,
        proposition_id=proposition.proposition_id,
        materiality=_enum_value(proposition.materiality) or "",
        modality=_enum_value(proposition.modality),
        polarity=_enum_value(proposition.polarity),
        status=_enum_value(proposition.status) or "",
        required_source_type=proposition.required_source_type,
        actual_source_type=evidence.authority_kind if evidence is not None else None,
        required_authority=_enum_value(proposition.required_authority),
        actual_authority=evidence.authority_kind if evidence is not None else None,
        source_id=evidence.source_id if evidence is not None else None,
        source_span=source_span,
        matched_span=matched_span,
        required_condition=proposition.condition,
        matched_condition=matched_condition,
        required_exception=proposition.exception_proposition_id,
        matched_exception=matched_exception,
        required_procedure=proposition.procedure,
        matched_procedure=matched_procedure,
        dependency_proposition_ids=_dependency_ids(proposition),
        final_conclusion_span=final_conclusion_span,
        reason=reason,
    )


def _authority_satisfied(
    proposition: LegalProposition,
    actual_source_type: str,
) -> bool:
    required = proposition.required_authority
    if required is AuthorityRequirement.ANY:
        return True
    if required is AuthorityRequirement.PRIMARY:
        return actual_source_type in _PRIMARY_AUTHORITY
    if required is AuthorityRequirement.PRECEDENT:
        return actual_source_type == "precedent"
    if required is AuthorityRequirement.INTERPRETATION:
        return actual_source_type == "interpretation"
    if required is AuthorityRequirement.GUIDANCE:
        return actual_source_type == "guidance"
    return False


def _temporal_satisfied(proposition: LegalProposition, actual_status: str) -> tuple[bool, str | None]:
    required = proposition.required_temporal_status
    if required is TemporalRequirement.ANY:
        return True, None
    if required is TemporalRequirement.CURRENT:
        if actual_status == "HISTORICAL_CONFIRMED":
            return False, "OUTDATED_SOURCE_USED"
        if actual_status == "CURRENT_UNRESOLVED":
            return False, "TEMPORAL_SOURCE_UNRESOLVED"
        return actual_status == "CURRENT_CONFIRMED", "TEMPORAL_SOURCE_UNRESOLVED"
    if required is TemporalRequirement.HISTORICAL:
        if actual_status == "CURRENT_UNRESOLVED":
            return False, "TEMPORAL_SOURCE_UNRESOLVED"
        return actual_status == "HISTORICAL_CONFIRMED", "OUTDATED_SOURCE_USED"
    return False, "TEMPORAL_SOURCE_UNRESOLVED"


def authority_satisfies(proposition: LegalProposition, actual_source_type: str) -> bool:
    """Expose the canonical authority semantics for other closure gates."""

    return _authority_satisfied(proposition, actual_source_type)


def temporal_satisfies(
    proposition: LegalProposition,
    actual_status: str,
) -> tuple[bool, str | None]:
    """Expose the canonical temporal semantics for other closure gates."""

    return _temporal_satisfied(proposition, actual_status)


def _support_fields(proposition: LegalProposition) -> tuple[tuple[str, str], ...]:
    return tuple(
        (name, value)
        for name, value in (
            ("subject", proposition.subject),
            (
                "legal_action",
                proposition.operative_verb_lexeme or proposition.legal_action,
            ),
            ("legal_object", proposition.legal_object),
            ("legal_effect", proposition.legal_effect),
            ("condition", proposition.condition),
            ("procedure", proposition.procedure),
        )
        if _text(value)
    )


def _source_anchor_present(proposition: LegalProposition, adopted_text: str) -> bool:
    evidence = proposition.evidence
    if evidence is None:
        return False
    return _phrase_present(evidence.source_locator, adopted_text) or (
        _phrase_present(evidence.source_id, adopted_text)
        and _phrase_present(evidence.source_title, adopted_text)
    )


def _source_semantics_match(proposition: LegalProposition, source_span: str) -> bool:
    negative = bool(_NEGATIVE_SOURCE_RE.search(source_span))
    if proposition.polarity is not None:
        if proposition.polarity is Polarity.POSITIVE and negative:
            return False
        if proposition.polarity is Polarity.NEGATIVE and not negative:
            return False
    if proposition.modality is not None:
        if proposition.modality is Modality.MUST and not _MANDATORY_SOURCE_RE.search(source_span):
            return False
        if proposition.modality in {Modality.MUST_NOT, Modality.MAY_NOT} and not negative:
            return False
        if proposition.modality is Modality.MAY and not _DISCRETIONARY_SOURCE_RE.search(source_span):
            return False
    return True


def source_relation_failure_code(proposition: LegalProposition) -> str | None:
    """Validate a bound evidence span before a proposition enters the registry."""

    if proposition.materiality is not Materiality.MATERIAL:
        return None
    if proposition.status is not PropositionStatus.CLOSED:
        return None
    evidence = proposition.evidence
    if evidence is None:
        return "SOURCE_REQUIRED_BUT_MISSING"
    matched_fields = [
        name
        for name, value in _support_fields(proposition)
        if _phrase_present(value, evidence.evidence_span)
    ]
    required_fields = [name for name, _ in _support_fields(proposition)]
    if not matched_fields:
        return "SOURCE_PRESENT_BUT_NOT_SUPPORTING"
    if len(matched_fields) != len(required_fields):
        return "SOURCE_PROPOSITION_MISMATCH"
    if not _source_semantics_match(proposition, evidence.evidence_span):
        return "SOURCE_PROPOSITION_MISMATCH"
    return None


def _assessment(
    proposition: LegalProposition,
    status: SourceClosureStatus,
    *,
    matched_span: str = "",
    reason: str,
) -> SourceClosureAssessment:
    evidence = proposition.evidence
    return SourceClosureAssessment(
        proposition_id=proposition.proposition_id,
        status=status,
        source_id=evidence.source_id if evidence is not None else None,
        source_span=evidence.evidence_span if evidence is not None else "",
        matched_span=matched_span,
        required_authority=_enum_value(proposition.required_authority),
        actual_authority=evidence.authority_kind if evidence is not None else None,
        required_temporal_status=_enum_value(proposition.required_temporal_status),
        actual_temporal_status=evidence.temporal_status if evidence is not None else None,
        reason=reason,
    )


def evaluate_source_closure(
    propositions: Sequence[LegalProposition],
    draft: str,
) -> SourceClosureResult:
    """Evaluate material source support independently of coverage/soundness."""

    if not isinstance(draft, str):
        raise TypeError("draft must be a string")
    spans = classify_answer_regions(draft)
    conclusion = _final_conclusion_span(spans)
    adopted = _adopted_text(spans)
    violations: list[SourceClosureViolation] = []
    authority_passed = True
    temporal_passed = True
    assessments: list[SourceClosureAssessment] = []

    for proposition in propositions:
        if proposition.materiality is not Materiality.MATERIAL:
            continue
        evidence = proposition.evidence
        dependencies = _dependency_ids(proposition)
        if evidence is None:
            assessments.append(
                _assessment(
                    proposition,
                    SourceClosureStatus.SOURCE_ABSENT,
                    reason="material proposition has no evidence reference",
                )
            )
            violations.append(
                _violation(
                    proposition,
                    "SOURCE_REQUIRED_BUT_MISSING",
                    final_conclusion_span=conclusion,
                    reason="material proposition has no evidence reference",
                )
            )
            authority_passed = False
            temporal_passed = False
            continue

        source_span = evidence.evidence_span
        matched_fields = [
            name
            for name, value in _support_fields(proposition)
            if _phrase_present(value, source_span)
        ]
        required_fields = [name for name, _ in _support_fields(proposition)]
        source_supporting = len(matched_fields) == len(required_fields) and _source_semantics_match(
            proposition,
            source_span,
        )
        if len(matched_fields) != len(required_fields):
            code = (
                "SOURCE_PRESENT_BUT_NOT_SUPPORTING"
                if not matched_fields
                else "SOURCE_PROPOSITION_MISMATCH"
            )
            violations.append(
                _violation(
                    proposition,
                    code,
                    source_span=source_span,
                    matched_span=" ".join(matched_fields),
                    final_conclusion_span=conclusion,
                    reason=(
                        "evidence span does not preserve the complete legal relation; "
                        f"matched={matched_fields}, required={required_fields}"
                    ),
                )
            )
        elif not source_supporting:
            violations.append(
                _violation(
                    proposition,
                    "SOURCE_PROPOSITION_MISMATCH",
                    source_span=source_span,
                    matched_span=";".join(matched_fields),
                    final_conclusion_span=conclusion,
                    reason="evidence span polarity or modality conflicts with the proposition",
                )
            )

        if not _source_anchor_present(proposition, adopted):
            violations.append(
                _violation(
                    proposition,
                    "MATERIAL_SOURCE_OMITTED",
                    source_span=source_span,
                    matched_span=adopted,
                    final_conclusion_span=conclusion,
                    reason="material source identifier or locator is absent from the final answer",
                )
            )

        actual_source_type = evidence.authority_kind
        authority_ok = True
        if (
            proposition.required_source_type is not None
            and actual_source_type != proposition.required_source_type
        ):
            authority_ok = False
            authority_passed = False
            violations.append(
                _violation(
                    proposition,
                    "INSUFFICIENT_AUTHORITY",
                    source_span=source_span,
                    final_conclusion_span=conclusion,
                    reason=(
                        "actual source type does not satisfy the required source type: "
                        f"{actual_source_type!r} != {proposition.required_source_type!r}"
                    ),
                )
            )
        elif not _authority_satisfied(proposition, actual_source_type):
            authority_ok = False
            authority_passed = False
            violations.append(
                _violation(
                    proposition,
                    "INSUFFICIENT_AUTHORITY",
                    source_span=source_span,
                    final_conclusion_span=conclusion,
                    reason=(
                        "actual authority cannot satisfy the required authority: "
                        f"{actual_source_type!r} for {_enum_value(proposition.required_authority)!r}"
                    ),
                )
            )

        temporal_ok, temporal_code = _temporal_satisfied(
            proposition,
            evidence.temporal_status,
        )
        if not temporal_ok:
            temporal_passed = False
            violations.append(
                _violation(
                    proposition,
                    temporal_code or "TEMPORAL_SOURCE_UNRESOLVED",
                    source_span=source_span,
                    final_conclusion_span=conclusion,
                    reason=(
                        "source temporal status does not satisfy the proposition requirement: "
                        f"{evidence.temporal_status!r} for "
                        f"{_enum_value(proposition.required_temporal_status)!r}"
                    ),
                )
            )

        if proposition.status is PropositionStatus.OPEN and proposition.materiality is Materiality.MATERIAL:
            violations.append(
                _violation(
                    proposition,
                    "SOURCE_PROPOSITION_MISMATCH",
                    source_span=source_span,
                    final_conclusion_span=conclusion,
                    reason="an OPEN material proposition cannot be source-closed",
                )
            )

        anchor_ok = _source_anchor_present(proposition, adopted)
        if not matched_fields:
            assessment_status = SourceClosureStatus.SOURCE_PRESENT
            assessment_reason = "source is present but no proposition relation field matched"
        elif not source_supporting:
            assessment_status = SourceClosureStatus.SOURCE_MATCHED
            assessment_reason = "source matches some relation fields but not the complete legal relation"
        elif not authority_ok:
            assessment_status = SourceClosureStatus.SOURCE_SUPPORTING
            assessment_reason = "source supports the relation but authority is insufficient"
        elif not temporal_ok:
            assessment_status = SourceClosureStatus.SOURCE_AUTHORITY_SATISFIED
            assessment_reason = "authority is sufficient but source temporal status is unresolved"
        elif not anchor_ok:
            assessment_status = SourceClosureStatus.SOURCE_TEMPORALLY_VALID
            assessment_reason = "source is valid but its identifier or locator is not adopted"
        elif proposition.status is PropositionStatus.OPEN:
            assessment_status = SourceClosureStatus.SOURCE_TEMPORALLY_VALID
            assessment_reason = "source is valid but the proposition remains OPEN"
        else:
            assessment_status = SourceClosureStatus.SOURCE_CLOSED
            assessment_reason = "source relation, authority, temporal status, and adopted anchor are closed"
        assessments.append(
            _assessment(
                proposition,
                assessment_status,
                matched_span=";".join(matched_fields),
                reason=assessment_reason,
            )
        )

    unique: list[SourceClosureViolation] = []
    seen: set[tuple[str, str]] = set()
    for item in violations:
        key = (item.proposition_id, item.code)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return SourceClosureResult(
        source_closure_passed=not unique,
        authority_closure_passed=authority_passed and not any(
            item.code == "SOURCE_REQUIRED_BUT_MISSING" for item in unique
        ),
        temporal_source_closure_passed=temporal_passed
        and not any(item.code == "SOURCE_REQUIRED_BUT_MISSING" for item in unique),
        violations=tuple(unique),
        assessments=tuple(assessments),
    )


def source_closure_result_to_dict(result: SourceClosureResult) -> dict[str, Any]:
    """Serialize source closure without losing forensic evidence."""

    payload = asdict(result)
    payload["violations"] = [asdict(item) for item in result.violations]
    payload["assessments"] = [asdict(item) for item in result.assessments]
    for item in payload["assessments"]:
        item["status"] = _enum_value(item["status"])
    for item in payload["violations"]:
        for key in ("materiality", "modality", "polarity", "status"):
            item[key] = _enum_value(item[key])
    return payload
