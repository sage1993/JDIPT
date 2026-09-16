"""Canonical legal proposition and evidence metadata models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re
from typing import Literal


class Materiality(StrEnum):
    MATERIAL = "MATERIAL"
    NON_MATERIAL = "NON_MATERIAL"


class Modality(StrEnum):
    MAY = "MAY"
    MUST = "MUST"
    MUST_NOT = "MUST_NOT"
    MAY_NOT = "MAY_NOT"


class AuthorityRequirement(StrEnum):
    PRIMARY = "PRIMARY"
    PRECEDENT = "PRECEDENT"
    INTERPRETATION = "INTERPRETATION"
    GUIDANCE = "GUIDANCE"
    ANY = "ANY"


class TemporalRequirement(StrEnum):
    CURRENT = "CURRENT"
    HISTORICAL = "HISTORICAL"
    ANY = "ANY"


class Polarity(StrEnum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"


class PropositionStatus(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


TemporalStatus = Literal[
    "CURRENT_CONFIRMED",
    "HISTORICAL_CONFIRMED",
    "CURRENT_UNRESOLVED",
]
AuthorityKind = Literal[
    "statute",
    "regulation",
    "ordinance",
    "precedent",
    "interpretation",
    "guidance",
    "other",
]

MAX_TEXT_LENGTH = 2048
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
_TEMPORAL_STATUSES = {
    "CURRENT_CONFIRMED",
    "HISTORICAL_CONFIRMED",
    "CURRENT_UNRESOLVED",
}
_AUTHORITY_KINDS = {
    "statute",
    "regulation",
    "ordinance",
    "precedent",
    "interpretation",
    "guidance",
    "other",
}

# This is the single flattened, model-facing contract for a canonical
# LegalProposition.  EvidenceRef is intentionally flattened because MCP
# arguments are JSON objects, while the registry stores it as a typed value.
# `source_clause` and `current_status` remain compatibility inputs for the
# legacy ledger bridge; new Native calls must use evidence_span and
# temporal_status instead.  Generated/internal fields and legacy semantic
# renames are deliberately absent.
CANONICAL_PROPOSITION_FIELDS = frozenset(
    {
        "proposition_id",
        "status",
        "subject",
        "condition",
        "procedure",
        "operative_verb_lexeme",
        "legal_action",
        "legal_object",
        "legal_effect",
        "modality",
        "polarity",
        "materiality",
        "relation_type",
        "base_proposition_id",
        "exception_proposition_id",
        "source_clause",
        "current_status",
        "base_rule",
        "exception_rule",
        "required_authority",
        "required_temporal_status",
        "required_source_type",
        "source_id",
        "authority_kind",
        "source_title",
        "source_locator",
        "evidence_span",
        "temporal_status",
        "temporal_render_text",
    }
)
CANONICAL_PROPOSITION_REQUIRED_FIELDS = (
    "proposition_id",
    "status",
    "materiality",
)


def canonical_proposition_schema() -> dict[str, object]:
    """Return the JSON schema for the canonical flattened proposition input."""

    properties: dict[str, object] = {
        name: {"type": "string"}
        for name in sorted(CANONICAL_PROPOSITION_FIELDS)
        if name not in {"status", "materiality", "modality", "polarity", "authority_kind", "temporal_status", "required_authority", "required_temporal_status", "required_source_type"}
    }
    properties.update(
        {
            "status": {"type": "string", "enum": ["OPEN", "CLOSED"]},
            "materiality": {
                "type": "string",
                "enum": ["MATERIAL", "NON_MATERIAL", "material", "non_material", "non-material"],
            },
            "modality": {
                "type": "string",
                "enum": [item.value for item in Modality],
            },
            "polarity": {
                "type": "string",
                "enum": [item.value for item in Polarity],
            },
            "authority_kind": {"type": "string", "enum": sorted(_AUTHORITY_KINDS)},
            "temporal_status": {"type": "string", "enum": sorted(_TEMPORAL_STATUSES)},
            "required_authority": {
                "type": "string",
                "enum": [item.value for item in AuthorityRequirement],
            },
            "required_temporal_status": {
                "type": "string",
                "enum": [item.value for item in TemporalRequirement],
            },
            "required_source_type": {"type": "string", "enum": sorted(_AUTHORITY_KINDS)},
        }
    )
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(CANONICAL_PROPOSITION_REQUIRED_FIELDS),
        "properties": properties,
        "allOf": [
            {
                "if": {"properties": {"status": {"const": "CLOSED"}}},
                "then": {
                    "required": [
                        "subject",
                        "condition",
                        "procedure",
                        "modality",
                        "legal_object",
                        "legal_effect",
                        "source_id",
                        "authority_kind",
                        "source_title",
                        "source_locator",
                        "evidence_span",
                        "temporal_status",
                    ],
                    "anyOf": [
                        {"required": ["legal_action"]},
                        {"required": ["operative_verb_lexeme"]},
                    ],
                },
            }
        ],
    }


class PropositionValidationError(ValueError):
    """Raised when proposition or evidence metadata is unsafe or incomplete."""


_MATERIALITY_ALIASES = {
    "MATERIAL": Materiality.MATERIAL,
    "material": Materiality.MATERIAL,
    "NON_MATERIAL": Materiality.NON_MATERIAL,
    "non_material": Materiality.NON_MATERIAL,
    "non-material": Materiality.NON_MATERIAL,
}
_MODALITY_ALIASES = {
    "MAY": Modality.MAY,
    "may": Modality.MAY,
    "MUST": Modality.MUST,
    "must": Modality.MUST,
    "mandatory": Modality.MUST,
    "MUST_NOT": Modality.MUST_NOT,
    "must not": Modality.MUST_NOT,
    "MAY_NOT": Modality.MAY_NOT,
    "may not": Modality.MAY_NOT,
}
_AUTHORITY_REQUIREMENT_ALIASES = {
    "PRIMARY": AuthorityRequirement.PRIMARY,
    "primary": AuthorityRequirement.PRIMARY,
    "PRECEDENT": AuthorityRequirement.PRECEDENT,
    "precedent": AuthorityRequirement.PRECEDENT,
    "INTERPRETATION": AuthorityRequirement.INTERPRETATION,
    "interpretation": AuthorityRequirement.INTERPRETATION,
    "GUIDANCE": AuthorityRequirement.GUIDANCE,
    "guidance": AuthorityRequirement.GUIDANCE,
    "ANY": AuthorityRequirement.ANY,
    "any": AuthorityRequirement.ANY,
}
_TEMPORAL_REQUIREMENT_ALIASES = {
    "CURRENT": TemporalRequirement.CURRENT,
    "current": TemporalRequirement.CURRENT,
    "HISTORICAL": TemporalRequirement.HISTORICAL,
    "historical": TemporalRequirement.HISTORICAL,
    "ANY": TemporalRequirement.ANY,
    "any": TemporalRequirement.ANY,
}
_POLARITY_ALIASES = {
    "POSITIVE": Polarity.POSITIVE,
    "positive": Polarity.POSITIVE,
    "NEGATIVE": Polarity.NEGATIVE,
    "negative": Polarity.NEGATIVE,
}
_STATUS_ALIASES = {
    "OPEN": PropositionStatus.OPEN,
    "CLOSED": PropositionStatus.CLOSED,
}


def _normalize_control(
    raw: object,
    field: str,
    aliases: dict[str, StrEnum],
    enum_type: type[StrEnum],
    *,
    required: bool,
) -> StrEnum | None:
    if raw is None:
        if required:
            raise PropositionValidationError(f"{field} is required")
        return None
    if isinstance(raw, enum_type):
        return raw
    if not isinstance(raw, str):
        raise PropositionValidationError(f"{field} must be a canonical semantic value")
    try:
        return aliases[raw]
    except KeyError as exc:
        raise PropositionValidationError(
            f"{field} has an unknown semantic value: {raw!r}"
        ) from exc


def normalize_materiality(raw: object, *, required: bool = True) -> Materiality | None:
    return _normalize_control(
        raw,
        "materiality",
        _MATERIALITY_ALIASES,
        Materiality,
        required=required,
    )


def normalize_modality(raw: object, *, required: bool = False) -> Modality | None:
    return _normalize_control(
        raw,
        "modality",
        _MODALITY_ALIASES,
        Modality,
        required=required,
    )


def normalize_authority_requirement(
    raw: object,
    *,
    required: bool = False,
) -> AuthorityRequirement | None:
    return _normalize_control(
        raw,
        "required_authority",
        _AUTHORITY_REQUIREMENT_ALIASES,
        AuthorityRequirement,
        required=required,
    )


def normalize_temporal_requirement(
    raw: object,
    *,
    required: bool = False,
) -> TemporalRequirement | None:
    return _normalize_control(
        raw,
        "required_temporal_status",
        _TEMPORAL_REQUIREMENT_ALIASES,
        TemporalRequirement,
        required=required,
    )


def normalize_polarity(raw: object, *, required: bool = False) -> Polarity | None:
    return _normalize_control(
        raw,
        "polarity",
        _POLARITY_ALIASES,
        Polarity,
        required=required,
    )


def normalize_status(raw: object, *, required: bool = True) -> PropositionStatus | None:
    return _normalize_control(
        raw,
        "status",
        _STATUS_ALIASES,
        PropositionStatus,
        required=required,
    )


def _validate_text(value: str, field: str, *, required: bool = False) -> None:
    if not isinstance(value, str):
        raise PropositionValidationError(f"{field} must be a string")
    if required and not value.strip():
        raise PropositionValidationError(f"{field} is required")
    if len(value) > MAX_TEXT_LENGTH:
        raise PropositionValidationError(
            f"{field} exceeds the runtime metadata limit"
        )
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise PropositionValidationError(
            f"{field} contains an invalid Unicode surrogate"
        )
    if any(ord(char) < 32 and char not in "\t\r\n" for char in value):
        raise PropositionValidationError(f"{field} contains a control character")


def _validate_identifier(value: str, field: str) -> None:
    _validate_text(value, field, required=True)
    if not _IDENTIFIER_PATTERN.fullmatch(value):
        raise PropositionValidationError(
            f"{field} must be a safe non-empty identifier"
        )


@dataclass(frozen=True)
class EvidenceRef:
    source_id: str
    authority_kind: AuthorityKind
    source_title: str
    source_locator: str
    evidence_span: str
    temporal_status: TemporalStatus
    temporal_render_text: str | None

    def __post_init__(self) -> None:
        _validate_identifier(self.source_id, "source_id")
        if self.authority_kind not in _AUTHORITY_KINDS:
            raise PropositionValidationError(
                "authority_kind must be a supported authority kind"
            )
        for name in (
            "source_title",
            "source_locator",
            "evidence_span",
        ):
            _validate_text(getattr(self, name), name, required=True)
        if self.temporal_status not in _TEMPORAL_STATUSES:
            raise PropositionValidationError(
                "temporal_status must be a supported temporal status"
            )
        if self.temporal_render_text is not None:
            _validate_text(self.temporal_render_text, "temporal_render_text")


@dataclass(frozen=True)
class LegalProposition:
    proposition_id: str
    status: PropositionStatus
    materiality: Materiality

    subject: str | None
    condition: str | None
    procedure: str | None
    modality: Modality | None
    legal_action: str | None
    operative_verb_lexeme: str | None
    legal_object: str | None
    legal_effect: str | None
    polarity: Polarity | None

    relation_type: str | None
    base_proposition_id: str | None
    exception_proposition_id: str | None

    evidence: EvidenceRef | None
    base_rule: str | None = None
    exception_rule: str | None = None
    required_authority: AuthorityRequirement = AuthorityRequirement.PRIMARY
    required_temporal_status: TemporalRequirement = TemporalRequirement.CURRENT
    required_source_type: AuthorityKind | None = None

    def __post_init__(self) -> None:
        _validate_identifier(self.proposition_id, "proposition_id")
        if not isinstance(self.status, PropositionStatus):
            raise PropositionValidationError(
                "status must be a canonical PropositionStatus value"
            )
        if not isinstance(self.materiality, Materiality):
            raise PropositionValidationError(
                "materiality must be a canonical Materiality value"
            )
        if self.modality is not None and not isinstance(self.modality, Modality):
            raise PropositionValidationError(
                "modality must be a canonical Modality value"
            )
        if self.polarity is not None and not isinstance(self.polarity, Polarity):
            raise PropositionValidationError(
                "polarity must be a canonical Polarity value"
            )
        if not isinstance(self.required_authority, AuthorityRequirement):
            raise PropositionValidationError(
                "required_authority must be a canonical AuthorityRequirement value"
            )
        if not isinstance(self.required_temporal_status, TemporalRequirement):
            raise PropositionValidationError(
                "required_temporal_status must be a canonical TemporalRequirement value"
            )
        if (
            self.required_source_type is not None
            and self.required_source_type not in _AUTHORITY_KINDS
        ):
            raise PropositionValidationError(
                "required_source_type must be a supported authority kind"
            )

        for name in (
            "subject",
            "condition",
            "procedure",
            "modality",
            "legal_action",
            "operative_verb_lexeme",
            "legal_object",
            "legal_effect",
            "polarity",
            "relation_type",
            "base_proposition_id",
            "exception_proposition_id",
            "base_rule",
            "exception_rule",
            "required_authority",
            "required_temporal_status",
            "required_source_type",
        ):
            value = getattr(self, name)
            if value is not None:
                _validate_text(value, name)

        if self.evidence is not None and not isinstance(self.evidence, EvidenceRef):
            raise PropositionValidationError("evidence must be an EvidenceRef")

        if self.status is not PropositionStatus.CLOSED:
            return

        required_relation = {
            "subject": self.subject,
            "condition": self.condition,
            "procedure": self.procedure,
            "modality": self.modality,
            "legal action": self.legal_action or self.operative_verb_lexeme,
            "legal_object": self.legal_object,
            "legal_effect": self.legal_effect,
        }
        missing_relation = [
            field for field, value in required_relation.items()
            if value is None or not value.strip()
        ]
        if missing_relation:
            raise PropositionValidationError(
                "CLOSED proposition is missing required legal relation fields: "
                + ", ".join(missing_relation)
            )

        if self.evidence is None:
            raise PropositionValidationError(
                "CLOSED proposition requires an evidence reference"
            )
        required_evidence = {
            "source_id": self.evidence.source_id,
            "source_locator": self.evidence.source_locator,
            "evidence_span": self.evidence.evidence_span,
            "authority_kind": self.evidence.authority_kind,
            "temporal_status": self.evidence.temporal_status,
        }
        missing_evidence = [
            field for field, value in required_evidence.items()
            if value is None or not str(value).strip()
        ]
        if missing_evidence:
            raise PropositionValidationError(
                "CLOSED proposition is missing required evidence fields: "
                + ", ".join(missing_evidence)
            )
