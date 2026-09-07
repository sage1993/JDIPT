from dataclasses import replace
import importlib

import pytest

from scripts.legal_proposition import (
    EvidenceRef,
    LegalProposition,
    Materiality,
    Modality,
    Polarity,
    PropositionStatus,
)
from scripts.material_obligation_ledger import (
    MaterialObligation,
    MaterialObligationLedger,
    ObligationSourceStatus,
    RegistryClosureViolation,
    RegistryClosureResult,
    evaluate_registry_closure,
)
from scripts.proposition_rendering import build_render_contract
from scripts.proposition_soundness import evaluate_soundness


def _coverage_api():
    try:
        return importlib.import_module("scripts.proposition_render_coverage")
    except ModuleNotFoundError as exc:
        pytest.fail(f"Task 9 coverage API is missing: {exc}")


def _evidence(source_id: str) -> EvidenceRef:
    return EvidenceRef(
        source_id=source_id,
        authority_kind="statute",
        source_title=f"Verified source {source_id}",
        source_locator=f"https://example.test/{source_id}",
        evidence_span=f"A rule for {source_id} has a verified legal effect.",
        temporal_status="CURRENT_CONFIRMED",
        temporal_render_text=f"The current verified standard for {source_id} applies.",
    )


def _proposition(
    proposition_id: str,
    source_id: str,
    *,
    relation_type: str = "base",
) -> LegalProposition:
    source = _evidence(source_id)
    return LegalProposition(
        proposition_id=proposition_id,
        status=PropositionStatus.CLOSED,
        materiality=Materiality.MATERIAL,
        subject="the authority",
        condition=f"the required condition for {proposition_id}",
        procedure=f"the required procedure for {proposition_id}",
        modality=Modality.MAY,
        legal_action="apply",
        operative_verb_lexeme="apply",
        legal_object=f"the subject {proposition_id}",
        legal_effect=f"the legal effect for {proposition_id}",
        polarity=Polarity.POSITIVE,
        relation_type=relation_type,
        base_proposition_id=None,
        exception_proposition_id=None,
        evidence=source,
    )


def _ledger(*propositions: LegalProposition) -> MaterialObligationLedger:
    obligations = tuple(
        MaterialObligation(
            obligation_id=f"O_{proposition.proposition_id}",
            issue_type=(
                "EXCEPTION_RULE"
                if proposition.relation_type == "exception"
                else "BASE_RULE"
            ),
            source_status=ObligationSourceStatus.SOURCE_CONFIRMED,
            evidence_source_ids=(proposition.evidence.source_id,),
            proposition_ids=(proposition.proposition_id,),
        )
        for proposition in propositions
    )
    return MaterialObligationLedger(
        obligations=obligations,
        verified_source_evidence=tuple(
            proposition.evidence for proposition in propositions
        ),
    )


def _closed_authority(propositions, ledger):
    return evaluate_registry_closure(
        ledger,
        ledger.verified_source_evidence,
        tuple(propositions),
    )


def _evaluate(ledger, closure, propositions, draft):
    api = _coverage_api()
    return api.evaluate_render_coverage(
        ledger,
        closure,
        tuple(propositions),
        draft,
    )


def test_complete_render_has_deterministic_coverage():
    proposition = _proposition("P1", "S1")
    ledger = _ledger(proposition)
    closure = _closed_authority((proposition,), ledger)
    draft = " ".join(slot.text for slot in build_render_contract(proposition).slots)

    result = _evaluate(ledger, closure, (proposition,), draft)

    assert result.coverage_passed is True
    assert result.required_proposition_ids == ("P1",)
    assert result.covered_proposition_ids == ("P1",)
    assert result.missing_proposition_ids == ()


def test_one_required_proposition_missing_fails_closed():
    first = _proposition("P1", "S1")
    second = _proposition("P2", "S2")
    third = _proposition("P3", "S3")
    propositions = (first, second, third)
    ledger = _ledger(*propositions)
    closure = _closed_authority(propositions, ledger)
    draft = " ".join(
        slot.text
        for proposition in (first, second)
        for slot in build_render_contract(proposition).slots
    )

    result = _evaluate(ledger, closure, propositions, draft)

    assert result.coverage_passed is False
    assert result.missing_proposition_ids == ("P3",)


def test_required_exception_is_not_satisfied_by_base_rule_only():
    base = _proposition("P_BASE", "S_BASE")
    exception = _proposition("P_EXCEPTION", "S_EXCEPTION", relation_type="exception")
    propositions = (base, exception)
    ledger = _ledger(*propositions)
    closure = _closed_authority(propositions, ledger)
    draft = " ".join(
        slot.text for slot in build_render_contract(base).slots
    )

    result = _evaluate(ledger, closure, propositions, draft)

    assert result.coverage_passed is False
    assert result.missing_proposition_ids == ("P_EXCEPTION",)


def test_extra_non_required_text_does_not_fail_coverage():
    proposition = _proposition("P1", "S1")
    ledger = _ledger(proposition)
    closure = _closed_authority((proposition,), ledger)
    rendered = " ".join(
        slot.text for slot in build_render_contract(proposition).slots
    )

    result = _evaluate(
        ledger,
        closure,
        (proposition,),
        f"Additional explanation. {rendered} Additional explanation.",
    )

    assert result.coverage_passed is True


def test_duplicate_render_is_covered_once_for_presence_purposes():
    proposition = _proposition("P1", "S1")
    ledger = _ledger(proposition)
    closure = _closed_authority((proposition,), ledger)
    rendered = " ".join(
        slot.text for slot in build_render_contract(proposition).slots
    )

    result = _evaluate(ledger, closure, (proposition,), f"{rendered} {rendered}")

    assert result.coverage_passed is True
    assert result.covered_proposition_ids == ("P1",)


def test_registry_only_presence_does_not_cover_final_answer():
    proposition = _proposition("P1", "S1")
    ledger = _ledger(proposition)
    closure = _closed_authority((proposition,), ledger)

    result = _evaluate(ledger, closure, (proposition,), "registry contains P1")

    assert result.coverage_passed is False
    assert result.missing_proposition_ids == ("P1",)


def test_keyword_only_presence_does_not_cover_canonical_slots():
    proposition = _proposition("P1", "S1")
    ledger = _ledger(proposition)
    closure = _closed_authority((proposition,), ledger)

    result = _evaluate(
        ledger,
        closure,
        (proposition,),
        "The required condition and required procedure concern the subject and legal effect.",
    )

    assert result.coverage_passed is False
    assert result.missing_proposition_ids == ("P1",)


def test_malformed_required_identity_fails_closed():
    proposition = _proposition("P1", "S1")
    malformed_obligation = object.__new__(MaterialObligation)
    object.__setattr__(malformed_obligation, "obligation_id", "O1")
    object.__setattr__(malformed_obligation, "issue_type", "BASE_RULE")
    object.__setattr__(
        malformed_obligation,
        "source_status",
        ObligationSourceStatus.SOURCE_CONFIRMED,
    )
    object.__setattr__(malformed_obligation, "evidence_source_ids", ("S1",))
    object.__setattr__(malformed_obligation, "proposition_ids", ("bad identity",))
    malformed_ledger = object.__new__(MaterialObligationLedger)
    object.__setattr__(malformed_ledger, "obligations", (malformed_obligation,))
    object.__setattr__(malformed_ledger, "verified_source_evidence", (_evidence("S1"),))
    closure = RegistryClosureResult(
        registry_closure_passed=True,
        violations=(),
    )

    result = _evaluate(malformed_ledger, closure, (proposition,), "")

    assert result.coverage_passed is False
    assert "proposition_id" in result.failure_reason.casefold()


def test_normal_empty_required_set_is_allowed():
    ledger = MaterialObligationLedger(obligations=(), verified_source_evidence=())
    closure = _closed_authority((), ledger)

    result = _evaluate(ledger, closure, (), "There is no confirmed material obligation.")

    assert result.coverage_passed is True
    assert result.required_proposition_ids == ()
    assert result.missing_proposition_ids == ()


def test_authority_failure_that_looks_empty_fails_closed():
    result = _evaluate(
        None,
        None,
        (),
        "There is no confirmed material obligation.",
    )

    assert result.coverage_passed is False
    assert "authority" in result.failure_reason.casefold()


def test_registry_ledger_authority_mismatch_fails_closed():
    proposition = _proposition("P1", "S1")
    ledger = _ledger(proposition)
    forged_closure = RegistryClosureResult(
        registry_closure_passed=True,
        violations=(
            RegistryClosureViolation(
                code="FORGED_AUTHORITY",
                obligation_id=None,
                proposition_id=None,
                source_id=None,
                reason="not produced by canonical closure",
            ),
        ),
    )

    result = _evaluate(
        ledger,
        forged_closure,
        (proposition,),
        "",
    )

    assert result.coverage_passed is False
    assert "does not match" in result.failure_reason.casefold()


def test_non_string_final_render_fails_closed():
    proposition = _proposition("P1", "S1")
    ledger = _ledger(proposition)
    closure = _closed_authority((proposition,), ledger)

    result = _evaluate(ledger, closure, (proposition,), None)

    assert result.coverage_passed is False
    assert "final rendered answer" in result.failure_reason.casefold()


def test_coverage_presence_does_not_claim_semantic_soundness():
    proposition = _proposition("P1", "S1")
    ledger = _ledger(proposition)
    closure = _closed_authority((proposition,), ledger)
    rendered = " ".join(
        slot.text for slot in build_render_contract(proposition).slots
    )
    draft = f"Review example only: '{rendered}'"

    coverage = _evaluate(ledger, closure, (proposition,), draft)
    soundness = evaluate_soundness(
        (proposition,),
        (build_render_contract(proposition),),
        draft,
    )

    assert coverage.coverage_passed is True
    assert soundness.soundness_passed is False
