from dataclasses import replace

import pytest

from scripts.legal_proposition import (
    EvidenceRef,
    LegalProposition,
    PropositionValidationError,
)


def _evidence():
    return EvidenceRef(
        source_id="law-001",
        authority_kind="statute",
        source_title="검증 법령",
        source_locator="법령 식별자/조문",
        evidence_span="확인된 원문",
        temporal_status="CURRENT_CONFIRMED",
        temporal_render_text="2026-09-04 현재 시행 중인 기준이다.",
    )


def _closed_proposition(**overrides):
    values = {
        "proposition_id": "P1",
        "status": "CLOSED",
        "materiality": "material",
        "subject": "행정청",
        "condition": "요건",
        "procedure": "절차",
        "modality": "may",
        "legal_action": "designate",
        "operative_verb_lexeme": "지정",
        "legal_object": "대상",
        "legal_effect": "법적 지위",
        "polarity": "positive",
        "relation_type": "exception",
        "base_proposition_id": None,
        "exception_proposition_id": None,
        "evidence": _evidence(),
    }
    values.update(overrides)
    return LegalProposition(**values)


def test_closed_proposition_requires_complete_legal_relation_and_evidence():
    with pytest.raises(PropositionValidationError):
        _closed_proposition(legal_effect=None)


def test_closed_proposition_requires_evidence_reference():
    with pytest.raises(PropositionValidationError):
        _closed_proposition(evidence=None)


def test_open_proposition_may_keep_partial_fields():
    proposition = LegalProposition(
        proposition_id="P1",
        status="OPEN",
        materiality="material",
        subject=None,
        condition="예외요건 확인",
        procedure=None,
        modality=None,
        legal_action=None,
        operative_verb_lexeme=None,
        legal_object="대상",
        legal_effect=None,
        polarity=None,
        relation_type="exception",
        base_proposition_id=None,
        exception_proposition_id=None,
        evidence=None,
    )

    assert proposition.status == "OPEN"


def test_proposition_rejects_path_injection_identifier():
    with pytest.raises(PropositionValidationError):
        _closed_proposition(proposition_id="../outside")


def test_evidence_rejects_control_character():
    with pytest.raises(PropositionValidationError):
        _closed_proposition(
            evidence=replace(_evidence(), source_title="bad\x00title")
        )


def test_proposition_rejects_unicode_surrogate_before_serialization():
    with pytest.raises(PropositionValidationError):
        _closed_proposition(condition="bad\ud800text")
