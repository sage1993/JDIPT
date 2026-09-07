"""Deterministic final-answer coverage for Task 8 canonical propositions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Any

from scripts.legal_proposition import LegalProposition, Materiality
from scripts.material_obligation_ledger import (
    MaterialObligationLedger,
    ObligationSourceStatus,
    RegistryClosureResult,
    evaluate_registry_closure,
)
from scripts.proposition_reconciliation import reconcile_render_contracts
from scripts.proposition_rendering import build_render_contract


@dataclass(frozen=True)
class RenderCoverageResult:
    """Auditable presence result for the authoritative required set."""

    coverage_passed: bool
    required_proposition_ids: tuple[str, ...]
    covered_proposition_ids: tuple[str, ...]
    missing_proposition_ids: tuple[str, ...]
    failure_reason: str


def _failure(reason: str) -> RenderCoverageResult:
    return RenderCoverageResult(
        coverage_passed=False,
        required_proposition_ids=(),
        covered_proposition_ids=(),
        missing_proposition_ids=(),
        failure_reason=reason,
    )


def _validate_propositions(
    propositions: Sequence[LegalProposition],
) -> tuple[LegalProposition, ...]:
    if not isinstance(propositions, Sequence) or isinstance(
        propositions,
        (str, bytes),
    ):
        raise ValueError("canonical propositions must be an array")
    values = tuple(propositions)
    if any(not isinstance(item, LegalProposition) for item in values):
        raise ValueError("canonical propositions must contain LegalProposition values")
    for item in values:
        item.__post_init__()
    ids = tuple(item.proposition_id for item in values)
    if len(set(ids)) != len(ids):
        raise ValueError("canonical propositions contain ambiguous duplicate identities")
    return values


def _validate_ledger(ledger: MaterialObligationLedger) -> None:
    if not isinstance(ledger, MaterialObligationLedger):
        raise ValueError("required-set authority ledger is unavailable")
    for item in ledger.obligations:
        if not hasattr(item, "__post_init__"):
            raise ValueError("material obligation identity is malformed")
        item.__post_init__()
    for item in ledger.verified_source_evidence:
        item.__post_init__()
    ledger.__post_init__()


def _closure_reason(result: RegistryClosureResult) -> str:
    codes = tuple(dict.fromkeys(item.code for item in result.violations))
    suffix = ", ".join(codes) if codes else "closure did not pass"
    return f"Task 8 registry closure authority is unavailable: {suffix}"


def _required_propositions(
    ledger: MaterialObligationLedger,
    registry_closure: RegistryClosureResult,
    propositions: tuple[LegalProposition, ...],
) -> tuple[LegalProposition, ...]:
    if not isinstance(registry_closure, RegistryClosureResult):
        raise ValueError("Task 8 registry closure authority is unavailable")
    if registry_closure.registry_closure_passed is not True:
        raise ValueError(_closure_reason(registry_closure))

    canonical_closure = evaluate_registry_closure(
        ledger,
        ledger.verified_source_evidence,
        propositions,
    )
    if canonical_closure != registry_closure:
        raise ValueError(
            "Task 8 registry closure authority does not match canonical state"
        )
    if canonical_closure.registry_closure_passed is not True:
        raise ValueError(_closure_reason(canonical_closure))

    by_id = {item.proposition_id: item for item in propositions}
    required: list[LegalProposition] = []
    seen: set[str] = set()
    for obligation in ledger.obligations:
        if obligation.source_status is not ObligationSourceStatus.SOURCE_CONFIRMED:
            continue
        for proposition_id in obligation.proposition_ids:
            proposition = by_id.get(proposition_id)
            if proposition is None:
                raise ValueError(
                    "required proposition identity is not linked to canonical state"
                )
            if proposition.materiality is not Materiality.MATERIAL:
                raise ValueError(
                    "required proposition identity is linked to a non-material proposition"
                )
            if proposition_id in seen:
                continue
            seen.add(proposition_id)
            required.append(proposition)
    return tuple(required)


def evaluate_render_coverage(
    ledger: MaterialObligationLedger | None,
    registry_closure: RegistryClosureResult | None,
    propositions: Sequence[LegalProposition],
    draft: str,
) -> RenderCoverageResult:
    """Compare the final draft with the required set proven by Task 8 closure."""

    try:
        if not isinstance(draft, str):
            raise ValueError("final rendered answer must be a string")
        if ledger is None or registry_closure is None:
            raise ValueError("required-set authority is unavailable")
        _validate_ledger(ledger)
        canonical_propositions = _validate_propositions(propositions)
        required = _required_propositions(
            ledger,
            registry_closure,
            canonical_propositions,
        )
        required_ids = tuple(item.proposition_id for item in required)
        contracts = tuple(build_render_contract(item) for item in required)
        reconciliation = reconcile_render_contracts(contracts, draft)
    except (TypeError, UnicodeError, ValueError, KeyError) as exc:
        return _failure(str(exc))

    missing = tuple(
        dict.fromkeys(item.proposition_id for item in reconciliation.missing_slots)
    )
    covered = tuple(
        proposition_id
        for proposition_id in required_ids
        if proposition_id not in missing
    )
    if missing:
        return RenderCoverageResult(
            coverage_passed=False,
            required_proposition_ids=required_ids,
            covered_proposition_ids=covered,
            missing_proposition_ids=missing,
            failure_reason=(
                "required proposition is missing from the final rendered answer: "
                + ", ".join(missing)
            ),
        )
    return RenderCoverageResult(
        coverage_passed=True,
        required_proposition_ids=required_ids,
        covered_proposition_ids=covered,
        missing_proposition_ids=(),
        failure_reason="",
    )


def render_coverage_result_to_dict(result: RenderCoverageResult) -> dict[str, Any]:
    """Serialize coverage evidence without retaining the final answer."""

    if not isinstance(result, RenderCoverageResult):
        raise ValueError("result must be a RenderCoverageResult")
    return asdict(result)
