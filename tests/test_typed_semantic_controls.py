import pytest
import json

from scripts.legal_proposition import (
    AuthorityRequirement,
    EvidenceRef,
    LegalProposition,
    Materiality,
    Modality,
    Polarity,
    PropositionStatus,
    PropositionValidationError,
    TemporalRequirement,
)
from scripts.proposition_registry import register_material_proposition
from scripts.proposition_registry import RegistryService
from scripts.jdipt_runtime_mcp import tool_definitions
from scripts.proposition_rendering import build_render_contract
from scripts.synthesis_runtime_state import load_runtime_state, save_runtime_state


def _evidence() -> EvidenceRef:
    return EvidenceRef(
        source_id="law-001",
        authority_kind="statute",
        source_title="검증 법령",
        source_locator="법령 식별자/조문",
        evidence_span="확인된 원문",
        temporal_status="CURRENT_CONFIRMED",
        temporal_render_text="현행 기준에 따른다.",
    )


def _closed_proposition(**overrides) -> LegalProposition:
    values = {
        "proposition_id": "P1",
        "status": PropositionStatus.CLOSED,
        "materiality": Materiality.MATERIAL,
        "subject": "행정청",
        "condition": "요건",
        "procedure": "절차",
        "modality": Modality.MAY,
        "legal_action": "designate",
        "operative_verb_lexeme": "지정",
        "legal_object": "대상",
        "legal_effect": "법적 지위",
        "polarity": Polarity.POSITIVE,
        "relation_type": "base",
        "base_proposition_id": None,
        "exception_proposition_id": None,
        "evidence": _evidence(),
    }
    values.update(overrides)
    return LegalProposition(**values)


def _closed_fields(**overrides):
    values = {
        "session_id": "session-a",
        "turn_id": "turn-1",
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
        "relation_type": "base",
        "source_id": "law-001",
        "authority_kind": "statute",
        "source_title": "검증 법령",
        "source_locator": "법령 식별자/조문",
        "evidence_span": "확인된 원문",
        "temporal_status": "CURRENT_CONFIRMED",
        "temporal_render_text": "현행 기준에 따른다.",
    }
    values.update(overrides)
    return values


@pytest.fixture(autouse=True)
def _pending_registry_state(tmp_path):
    """Keep direct semantic-control tests on the canonical lifecycle boundary."""

    RegistryService(tmp_path).begin_pending("session-a", "turn-1")


@pytest.mark.parametrize("value", ["criticality", "critical", "important"])
def test_direct_domain_rejects_unknown_materiality(value):
    with pytest.raises(PropositionValidationError, match="materiality"):
        _closed_proposition(materiality=value)


@pytest.mark.parametrize("value", ["SHOULD", "REQUIRED", "PROHIBITED", "not required"])
def test_direct_domain_rejects_unknown_modality(value):
    with pytest.raises(PropositionValidationError, match="modality"):
        _closed_proposition(modality=value)


@pytest.mark.parametrize("value", ["NEUTRAL", "UNKNOWN", ""])
def test_direct_domain_rejects_unknown_polarity(value):
    with pytest.raises(PropositionValidationError, match="polarity"):
        _closed_proposition(polarity=value)


@pytest.mark.parametrize("value", ["PENDING", "DONE", ""])
def test_direct_domain_rejects_unknown_proposition_status(value):
    with pytest.raises(PropositionValidationError, match="status"):
        _closed_proposition(status=value)


@pytest.mark.parametrize("field", ["required_authority", "required_temporal_status"])
def test_direct_domain_rejects_unknown_source_closure_requirement(field):
    with pytest.raises(PropositionValidationError, match=field):
        _closed_proposition(**{field: "UNKNOWN"})


def test_registry_rejects_unknown_materiality_instead_of_downgrading(tmp_path):
    with pytest.raises(PropositionValidationError, match="materiality"):
        register_material_proposition(
            _closed_fields(materiality="criticality"),
            tmp_path,
        )


def test_registry_does_not_default_missing_materiality_to_non_material(tmp_path):
    fields = _closed_fields()
    fields.pop("materiality")

    with pytest.raises(PropositionValidationError, match="materiality"):
        register_material_proposition(fields, tmp_path)


@pytest.mark.parametrize("value", ["not required", "critical", "important"])
def test_registry_rejects_unapproved_semantic_aliases(tmp_path, value):
    with pytest.raises(PropositionValidationError):
        register_material_proposition(_closed_fields(materiality=value), tmp_path)


@pytest.mark.parametrize("value", ["SHOULD", "REQUIRED", "PROHIBITED", "not required"])
def test_registry_rejects_unknown_modality(tmp_path, value):
    with pytest.raises(PropositionValidationError, match="modality"):
        register_material_proposition(_closed_fields(modality=value), tmp_path)


@pytest.mark.parametrize("value", ["NEUTRAL", "UNKNOWN", ""])
def test_registry_rejects_unknown_polarity(tmp_path, value):
    with pytest.raises(PropositionValidationError, match="polarity"):
        register_material_proposition(_closed_fields(polarity=value), tmp_path)


@pytest.mark.parametrize("value", ["PENDING", "DONE", ""])
def test_registry_rejects_unknown_status(tmp_path, value):
    with pytest.raises(PropositionValidationError, match="status"):
        register_material_proposition(_closed_fields(status=value), tmp_path)


@pytest.mark.parametrize(
    ("materiality", "expected"),
    [
        ("MATERIAL", Materiality.MATERIAL),
        ("material", Materiality.MATERIAL),
        ("NON_MATERIAL", Materiality.NON_MATERIAL),
        ("non_material", Materiality.NON_MATERIAL),
        ("non-material", Materiality.NON_MATERIAL),
    ],
)
def test_registry_materiality_aliases_are_explicit_and_typed(
    tmp_path,
    materiality,
    expected,
):
    result = register_material_proposition(
        _closed_fields(materiality=materiality),
        tmp_path,
    )

    assert result.proposition.materiality is expected
    assert isinstance(result.proposition.materiality, Materiality)


@pytest.mark.parametrize(
    ("modality", "expected"),
    [
        ("MAY", Modality.MAY),
        ("may", Modality.MAY),
        ("MUST", Modality.MUST),
        ("must", Modality.MUST),
        ("mandatory", Modality.MUST),
        ("must not", Modality.MUST_NOT),
        ("may not", Modality.MAY_NOT),
    ],
)
def test_registry_modality_aliases_preserve_canonical_distinctions(
    tmp_path,
    modality,
    expected,
):
    result = register_material_proposition(
        _closed_fields(modality=modality),
        tmp_path,
    )

    assert result.proposition.modality is expected


def test_registry_does_not_derive_polarity_from_negative_modality(tmp_path):
    result = register_material_proposition(
        _closed_fields(modality="MUST_NOT", polarity="POSITIVE"),
        tmp_path,
    )

    assert result.proposition.modality is Modality.MUST_NOT
    assert result.proposition.polarity is Polarity.POSITIVE


@pytest.mark.parametrize("field", ["required_authority", "required_temporal_status"])
def test_registry_rejects_unknown_source_closure_requirement(tmp_path, field):
    with pytest.raises(PropositionValidationError, match=field):
        register_material_proposition(
            _closed_fields(**{field: "UNKNOWN"}),
            tmp_path,
        )


def test_registry_source_closure_requirements_are_typed_and_persisted(tmp_path):
    result = register_material_proposition(
        _closed_fields(
            required_authority="INTERPRETATION",
            required_temporal_status="HISTORICAL",
        ),
        tmp_path,
    )

    assert result.proposition.required_authority is AuthorityRequirement.INTERPRETATION
    assert result.proposition.required_temporal_status is TemporalRequirement.HISTORICAL
    loaded = load_runtime_state("session-a", "turn-1", tmp_path)
    assert loaded.propositions[0].required_authority is AuthorityRequirement.INTERPRETATION
    assert loaded.propositions[0].required_temporal_status is TemporalRequirement.HISTORICAL


def test_serialization_round_trip_writes_and_restores_canonical_values(tmp_path):
    result = register_material_proposition(
        _closed_fields(
            materiality="material",
            modality="must not",
            polarity="negative",
        ),
        tmp_path,
    )

    path = save_runtime_state(result.state, tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    persisted = payload["propositions"][0]

    assert persisted["materiality"] == "MATERIAL"
    assert persisted["modality"] == "MUST_NOT"
    assert persisted["polarity"] == "NEGATIVE"
    assert persisted["status"] == "CLOSED"

    loaded = load_runtime_state("session-a", "turn-1", tmp_path)
    proposition = loaded.propositions[0]
    assert loaded == result.state
    assert proposition.materiality is Materiality.MATERIAL
    assert proposition.modality is Modality.MUST_NOT
    assert proposition.polarity is Polarity.NEGATIVE
    assert proposition.status is PropositionStatus.CLOSED


def test_renderer_uses_typed_modality_without_substring_inference(tmp_path):
    result = register_material_proposition(
        _closed_fields(modality="MAY_NOT"),
        tmp_path,
    )

    text = build_render_contract(result.proposition).slots[0].text

    assert "하여서는 안" in text
    assert "할 수 있다" not in text


def test_mcp_schema_restricts_semantic_properties_to_explicit_values():
    properties = tool_definitions()[0]["inputSchema"]["properties"]

    assert properties["materiality"]["enum"][:2] == ["MATERIAL", "NON_MATERIAL"]
    assert properties["modality"]["enum"][:4] == [
        "MAY",
        "MUST",
        "MUST_NOT",
        "MAY_NOT",
    ]
    assert properties["polarity"]["enum"][:2] == ["POSITIVE", "NEGATIVE"]
    assert properties["required_authority"]["enum"][:5] == [
        "PRIMARY",
        "PRECEDENT",
        "INTERPRETATION",
        "GUIDANCE",
        "ANY",
    ]
    assert properties["required_temporal_status"]["enum"][:3] == [
        "CURRENT",
        "HISTORICAL",
        "ANY",
    ]
