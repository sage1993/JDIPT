"""Deterministic obligation and dependency closure for final answers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
import re
from typing import Any

from scripts.legal_proposition import (
    LegalProposition,
    Materiality,
    Modality,
    Polarity,
    PropositionStatus,
)
from scripts.proposition_reconciliation import normalize_rendered_text
from scripts.proposition_rendering import PropositionRenderContract
from scripts.proposition_soundness import AnswerSpan, classify_answer_regions

# Re-export the Task 8 domain boundary for callers that already consume the
# proposition-obligation module.  The implementation and state authority live
# in material_obligation_ledger.py.
from scripts.material_obligation_ledger import (
    MaterialObligation,
    MaterialObligationLedger,
    ObligationSourceStatus,
    ObligationStatus,
    RegistryClosureResult,
    SourceResolutionStatus,
    evaluate_registry_closure,
    validate_registry_closure,
)


@dataclass(frozen=True)
class ObligationClosureViolation:
    code: str
    proposition_id: str
    materiality: str
    modality: str | None
    polarity: str | None
    status: str
    required_condition: str | None
    matched_condition: str | None
    required_exception: str | None
    matched_exception: str | None
    required_procedure: str | None
    matched_procedure: str | None
    dependency_proposition_ids: tuple[str, ...]
    matched_region: str
    matched_span: str
    final_conclusion_span: str
    reason: str


@dataclass(frozen=True)
class ObligationClosureResult:
    obligation_closure_passed: bool
    dependency_closure_passed: bool
    final_conclusion_support_passed: bool
    violations: tuple[ObligationClosureViolation, ...]


_TOKEN_RE = re.compile(r"[a-z0-9]+|[가-힣]+", re.IGNORECASE)
_MAY_RE = re.compile(
    r"(?:할\s*수\s*있|가능|고려|권고|권장|추천|재량)",
    re.IGNORECASE,
)
_MUST_RE = re.compile(r"(?:하여야\s*한다|해야\s*한다|의무|반드시)", re.IGNORECASE)
_MUST_NOT_RE = re.compile(
    r"(?:하여서는\s*안|해서는\s*안|금지|하지\s*않아야|불허)",
    re.IGNORECASE,
)
_EXCEPTION_RE = re.compile(r"(?:예외|특례|다만|exception|special)", re.IGNORECASE)
_DEFINITIVE_RE = re.compile(
    r"(?:할\s*수\s*있|가능|허용|하여야\s*한다|해야\s*한다|금지|하여서는\s*안|불가|불가능)",
    re.IGNORECASE,
)


def _enum_value(value: object) -> str | None:
    return None if value is None else str(getattr(value, "value", value))


def _tokens(value: str | None) -> tuple[str, ...]:
    return tuple(_TOKEN_RE.findall((value or "").casefold()))


def _token_matches(expected: str, actual: str) -> bool:
    if expected == actual:
        return True
    if re.fullmatch(r"[가-힣]+", expected) and actual.startswith(expected):
        return len(actual) - len(expected) <= 4
    return False


def _phrase_present(phrase: str | None, text: str) -> bool:
    expected = _tokens(phrase)
    actual = _tokens(text)
    if not expected:
        return True
    width = len(expected)
    return any(
        all(_token_matches(wanted, found) for wanted, found in zip(expected, actual[index : index + width], strict=True))
        for index in range(len(actual) - width + 1)
    )


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


def _adopted_text(spans: Sequence[AnswerSpan]) -> str:
    return " ".join(
        span.text.strip()
        for span in spans
        if span.adopted and span.text.strip()
    ).strip()


def _final_conclusion(spans: Sequence[AnswerSpan]) -> str:
    return " ".join(
        span.text.strip()
        for span in spans
        if span.kind == "final_conclusion" and span.text.strip()
    ).strip()


def _slot_text(
    contract: PropositionRenderContract,
    kind: str,
) -> str:
    return next((slot.text for slot in contract.slots if slot.kind == kind), "")


def _exact_slot_adopted(
    contract: PropositionRenderContract,
    spans: Sequence[AnswerSpan],
    kind: str,
) -> tuple[bool, str, str]:
    expected = _slot_text(contract, kind)
    normalized_expected = normalize_rendered_text(expected)
    if not normalized_expected:
        return True, "", ""
    fallback: tuple[str, str] | None = None
    for span in spans:
        if normalized_expected in normalize_rendered_text(span.text):
            if span.adopted:
                return True, span.kind, span.text
            if fallback is None:
                fallback = (span.kind, span.text)
    if fallback is not None:
        return False, fallback[0], fallback[1]
    return False, "missing", ""


def _violation(
    proposition: LegalProposition,
    code: str,
    *,
    matched_region: str = "missing",
    matched_span: str = "",
    matched_condition: str | None = None,
    matched_exception: str | None = None,
    matched_procedure: str | None = None,
    final_conclusion_span: str = "",
    reason: str,
) -> ObligationClosureViolation:
    return ObligationClosureViolation(
        code=code,
        proposition_id=proposition.proposition_id,
        materiality=_enum_value(proposition.materiality) or "",
        modality=_enum_value(proposition.modality),
        polarity=_enum_value(proposition.polarity),
        status=_enum_value(proposition.status) or "",
        required_condition=proposition.condition,
        matched_condition=matched_condition,
        required_exception=proposition.exception_proposition_id,
        matched_exception=matched_exception,
        required_procedure=proposition.procedure,
        matched_procedure=matched_procedure,
        dependency_proposition_ids=_dependency_ids(proposition),
        matched_region=matched_region,
        matched_span=matched_span,
        final_conclusion_span=final_conclusion_span,
        reason=reason,
    )


def _relation_requires_exception(proposition: LegalProposition) -> bool:
    return bool(
        proposition.exception_rule
        or (
            proposition.relation_type
            and _EXCEPTION_RE.search(proposition.relation_type)
        )
    )


def _modality_preserved(proposition: LegalProposition, conclusion: str) -> tuple[bool, str | None]:
    modality = proposition.modality
    if modality is Modality.MUST:
        if _MUST_RE.search(conclusion):
            return True, None
        if _MAY_RE.search(conclusion):
            return False, "MUST_DEGRADED_TO_MAY"
        return False, "OBLIGATION_DROPPED"
    if modality in {Modality.MUST_NOT, Modality.MAY_NOT}:
        if _MUST_NOT_RE.search(conclusion):
            return True, None
        return False, "MUST_NOT_DEGRADED"
    if modality is Modality.MAY and _MAY_RE.search(conclusion):
        return True, None
    return False, "OBLIGATION_DROPPED"


def _final_relation_supported(proposition: LegalProposition, conclusion: str) -> tuple[set[str], set[str]]:
    required = {
        name
        for name, value in (
            ("condition", proposition.condition),
            ("procedure", proposition.procedure),
            ("legal_action", proposition.operative_verb_lexeme or proposition.legal_action),
            ("legal_object", proposition.legal_object),
            ("legal_effect", proposition.legal_effect),
        )
        if value
    }
    matched = {
        name
        for name, value in (
            ("condition", proposition.condition),
            ("procedure", proposition.procedure),
            ("legal_action", proposition.operative_verb_lexeme or proposition.legal_action),
            ("legal_object", proposition.legal_object),
            ("legal_effect", proposition.legal_effect),
        )
        if value and _phrase_present(value, conclusion)
    }
    return required, matched


def _polarity_supported(proposition: LegalProposition, conclusion: str) -> bool:
    if proposition.polarity is Polarity.NEGATIVE:
        return bool(_MUST_NOT_RE.search(conclusion))
    if proposition.polarity is Polarity.POSITIVE:
        return not bool(_MUST_NOT_RE.search(conclusion))
    return True


def evaluate_obligation_closure(
    propositions: Sequence[LegalProposition],
    contracts: Sequence[PropositionRenderContract],
    draft: str,
) -> ObligationClosureResult:
    """Ensure legal obligations and their material dependencies survive adoption."""

    if not isinstance(draft, str):
        raise TypeError("draft must be a string")
    by_id: Mapping[str, LegalProposition] = {
        item.proposition_id: item for item in propositions
    }
    contracts_by_id = {item.proposition_id: item for item in contracts}
    spans = classify_answer_regions(draft)
    adopted = _adopted_text(spans)
    conclusion = _final_conclusion(spans)
    violations: list[ObligationClosureViolation] = []
    dependency_passed = True
    final_support_passed = True

    for proposition in propositions:
        if proposition.materiality is not Materiality.MATERIAL:
            continue
        contract = contracts_by_id.get(proposition.proposition_id)
        if contract is None:
            final_support_passed = False
            violations.append(
                _violation(
                    proposition,
                    "OBLIGATION_DROPPED",
                    final_conclusion_span=conclusion,
                    reason="material proposition has no deterministic render contract",
                )
            )
            continue

        if proposition.status is PropositionStatus.OPEN:
            if _DEFINITIVE_RE.search(conclusion or adopted):
                violations.append(
                    _violation(
                        proposition,
                        "OPEN_PROMOTED_TO_CLOSED",
                        matched_region="final_conclusion",
                        matched_span=conclusion or adopted,
                        final_conclusion_span=conclusion,
                        reason="OPEN proposition is expressed as a definitive legal effect",
                    )
                )
            continue

        effect_adopted, effect_region, effect_span = _exact_slot_adopted(
            contract,
            spans,
            "effect",
        )
        if not effect_adopted:
            violations.append(
                _violation(
                    proposition,
                    "OBLIGATION_DROPPED",
                    matched_region=effect_region,
                    matched_span=effect_span,
                    final_conclusion_span=conclusion,
                    reason="material obligation is absent from an adopted answer region",
                )
            )

        modality_ok, modality_code = _modality_preserved(proposition, conclusion)
        if not modality_ok:
            violations.append(
                _violation(
                    proposition,
                    modality_code or "OBLIGATION_DROPPED",
                    matched_region="final_conclusion" if conclusion else "missing",
                    matched_span=conclusion,
                    final_conclusion_span=conclusion,
                    reason="final conclusion weakens or omits the proposition modality",
                )
            )

        required_fields, matched_fields = _final_relation_supported(
            proposition,
            conclusion,
        )
        if "condition" in required_fields and "condition" not in matched_fields:
            violations.append(
                _violation(
                    proposition,
                    "CONDITION_DROPPED",
                    matched_region="final_conclusion" if conclusion else "missing",
                    matched_span=conclusion,
                    final_conclusion_span=conclusion,
                    reason="required condition is absent from the final conclusion",
                )
            )
        if "procedure" in required_fields and "procedure" not in matched_fields:
            violations.append(
                _violation(
                    proposition,
                    "PROCEDURAL_PREREQUISITE_DROPPED",
                    matched_region="final_conclusion" if conclusion else "missing",
                    matched_span=conclusion,
                    final_conclusion_span=conclusion,
                    reason="mandatory procedure is absent from the final conclusion",
                )
            )
        if _relation_requires_exception(proposition) and not _EXCEPTION_RE.search(conclusion):
            violations.append(
                _violation(
                    proposition,
                    "EXCEPTION_DROPPED",
                    matched_region="final_conclusion" if conclusion else "missing",
                    matched_span=conclusion,
                    final_conclusion_span=conclusion,
                    reason="exception relation or exception condition is absent from the final conclusion",
                )
            )
        if not _polarity_supported(proposition, conclusion):
            violations.append(
                _violation(
                    proposition,
                    "FINAL_CONCLUSION_UNSUPPORTED",
                    matched_region="final_conclusion" if conclusion else "missing",
                    matched_span=conclusion,
                    final_conclusion_span=conclusion,
                    reason="final conclusion polarity contradicts the proposition",
                )
            )

        relation_required = {
            "legal_action",
            "legal_object",
            "legal_effect",
        }
        if not conclusion or not relation_required.issubset(matched_fields):
            final_support_passed = False
            violations.append(
                _violation(
                    proposition,
                    "FINAL_CONCLUSION_UNSUPPORTED",
                    matched_region="final_conclusion" if conclusion else "missing",
                    matched_span=conclusion,
                    final_conclusion_span=conclusion,
                    reason="final conclusion does not preserve the proposition legal relation",
                )
            )

        for dependency_id in _dependency_ids(proposition):
            dependency = by_id.get(dependency_id)
            if dependency is None:
                dependency_passed = False
                violations.append(
                    _violation(
                        proposition,
                        "DEPENDENCY_OMITTED",
                        matched_region="missing",
                        final_conclusion_span=conclusion,
                        reason=f"required dependency {dependency_id!r} is not registered",
                    )
                )
                continue
            if dependency.status is PropositionStatus.OPEN:
                dependency_passed = False
                violations.append(
                    _violation(
                        proposition,
                        "DEPENDENCY_OPEN",
                        matched_region="open",
                        matched_span=dependency_id,
                        final_conclusion_span=conclusion,
                        reason=f"required dependency {dependency_id!r} remains OPEN",
                    )
                )
                continue
            dependency_contract = contracts_by_id.get(dependency_id)
            if dependency_contract is None:
                dependency_passed = False
                violations.append(
                    _violation(
                        proposition,
                        "DEPENDENCY_OMITTED",
                        matched_region="missing",
                        final_conclusion_span=conclusion,
                        reason=f"required dependency {dependency_id!r} has no render contract",
                    )
                )
                continue
            dependency_adopted, dependency_region, dependency_span = _exact_slot_adopted(
                dependency_contract,
                spans,
                "effect",
            )
            if not dependency_adopted:
                dependency_passed = False
                violations.append(
                    _violation(
                        proposition,
                        "DEPENDENCY_OMITTED",
                        matched_region=dependency_region,
                        matched_span=dependency_span,
                        final_conclusion_span=conclusion,
                        reason=f"dependency {dependency_id!r} is not preserved in an adopted region",
                    )
                )

    unique: list[ObligationClosureViolation] = []
    seen: set[tuple[str, str]] = set()
    for item in violations:
        key = (item.proposition_id, item.code)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return ObligationClosureResult(
        obligation_closure_passed=not unique,
        dependency_closure_passed=dependency_passed,
        final_conclusion_support_passed=final_support_passed
        and not any(item.code == "FINAL_CONCLUSION_UNSUPPORTED" for item in unique),
        violations=tuple(unique),
    )


def obligation_closure_result_to_dict(result: ObligationClosureResult) -> dict[str, Any]:
    """Serialize obligation closure without dropping spans or dependency ids."""

    payload = asdict(result)
    payload["violations"] = [asdict(item) for item in result.violations]
    for item in payload["violations"]:
        for key in ("materiality", "modality", "polarity", "status"):
            item[key] = _enum_value(item[key])
    return payload
