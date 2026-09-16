from dataclasses import replace

import pytest

from scripts.synthesis_integrity import (
    MaterialProposition,
    reconcile_draft,
    reconcile_proposition,
    render_mandatory_proposition_sentence,
    render_mandatory_slots,
    render_synthesis,
    repair_draft,
)


def designation_fixture() -> MaterialProposition:
    return MaterialProposition(
        proposition_id="EXCEPTION_X",
        materiality="material",
        legal_actor="A",
        condition="C",
        procedure="P",
        modality="may",
        legal_action="designate",
        legal_object="O",
        resulting_status_or_effect="Z",
        polarity="positive",
        relation_to_base_or_exception="exception to BASE_X",
        source_proposition="C를 충족하고 P를 거치면 O를 Z로 지정할 수 있다.",
        evidence_span="C를 충족하고 P를 거치면 O를 Z로 지정할 수 있다.",
        closure_status="CLOSED",
        operative_verb_lexeme="지정",
    )


def test_closed_designation_is_rendered_as_a_mandatory_legal_effect_sentence():
    proposition = designation_fixture()

    sentence = render_mandatory_proposition_sentence(proposition)
    result = reconcile_proposition(proposition, sentence)

    assert result.covered
    assert "C" in sentence and "P" in sentence and "O" in sentence
    assert "지정" in sentence and "Z" in sentence


@pytest.mark.parametrize(
    ("legal_action", "operative_verb_lexeme", "source_action"),
    [
        ("designate", "지정", "지정"),
        ("approve", "승인", "승인"),
        ("exclude", "제외", "제외"),
    ],
)
def test_source_specific_legal_actions_survive_mandatory_rendering(
    legal_action: str,
    operative_verb_lexeme: str,
    source_action: str,
):
    proposition = replace(
        designation_fixture(),
        legal_action=legal_action,
        operative_verb_lexeme=operative_verb_lexeme,
        source_proposition=f"C를 충족하고 P를 거치면 O를 Z로 {source_action}할 수 있다.",
        evidence_span=f"C를 충족하고 P를 거치면 O를 Z로 {source_action}할 수 있다.",
    )

    sentence = render_mandatory_proposition_sentence(proposition)

    assert source_action in sentence
    assert reconcile_proposition(proposition, sentence).covered


@pytest.mark.parametrize(
    ("draft", "missing"),
    [
        (
            "C를 충족하면 기준이 완화될 수 있다.",
            {"procedure", "legal_action", "legal_object", "resulting_status_or_effect"},
        ),
        ("C를 충족하면 O를 Z로 지정할 수 있다.", {"procedure"}),
        (
            "C를 충족하고 P를 거치면 O에 혜택을 적용할 수 있다.",
            {"legal_action", "resulting_status_or_effect"},
        ),
        (
            "P를 거치면 기준이 어느 범위까지 완화된다.",
            {"condition", "legal_action", "legal_object", "resulting_status_or_effect"},
        ),
    ],
)
def test_reconciliation_rejects_degraded_closed_relation(draft: str, missing: set[str]):
    result = reconcile_proposition(designation_fixture(), draft)

    assert not result.covered
    assert missing <= set(result.missing_fields)


def test_base_and_exception_get_independent_mandatory_slots():
    base = MaterialProposition(
        proposition_id="BASE_X",
        materiality="material",
        legal_actor="A",
        condition="항상",
        procedure="기본 절차",
        modality="must",
        legal_action="apply",
        legal_object="O",
        resulting_status_or_effect="B",
        polarity="positive",
        relation_to_base_or_exception="base",
        source_proposition="기본 절차에 따라 O에 B를 적용한다.",
        evidence_span="기본 절차에 따라 O에 B를 적용한다.",
        closure_status="CLOSED",
        operative_verb_lexeme="적용",
    )
    exception = designation_fixture()

    slots = render_mandatory_slots([base, exception])

    assert len(slots) == 2
    assert "B" in slots[0] and "적용" in slots[0]
    assert "C" in slots[1] and "P" in slots[1] and "지정" in slots[1]


def test_mandatory_legal_effect_precedes_explanatory_range_text():
    output = render_synthesis(
        [designation_fixture()],
        explanatory_synthesis="실무상 범위가 확대될 수 있는지는 별도 검토한다.",
    )

    assert output.index("지정") < output.index("범위가 확대")


def test_repair_restores_source_effect_instead_of_free_paraphrase():
    draft = "C를 충족하면 기준이 완화될 수 있다."

    repaired = repair_draft(draft, [designation_fixture()])

    assert "P" in repaired and "O" in repaired and "Z" in repaired and "지정" in repaired
    assert reconcile_draft([designation_fixture()], repaired).covered


def test_open_proposition_cannot_be_promoted_to_confirmed_effect():
    proposition = replace(designation_fixture(), closure_status="OPEN")

    confirmed = reconcile_draft(
        [proposition],
        "C를 충족하고 P를 거치면 O를 Z로 지정할 수 있다.",
    )
    neutral = reconcile_draft(
        [proposition],
        "C와 P가 확인되면 O를 Z로 지정할 수 있는지는 확인 필요하다.",
    )

    assert not confirmed.covered
    assert "OPEN" in confirmed.failures
    assert neutral.covered
