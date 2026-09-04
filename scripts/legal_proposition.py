"""Canonical legal proposition and evidence metadata models."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal


PropositionStatus = Literal["OPEN", "CLOSED"]
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


class PropositionValidationError(ValueError):
    """Raised when proposition or evidence metadata is unsafe or incomplete."""


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
    materiality: str

    subject: str | None
    condition: str | None
    procedure: str | None
    modality: str | None
    legal_action: str | None
    operative_verb_lexeme: str | None
    legal_object: str | None
    legal_effect: str | None
    polarity: str | None

    relation_type: str | None
    base_proposition_id: str | None
    exception_proposition_id: str | None

    evidence: EvidenceRef | None

    def __post_init__(self) -> None:
        _validate_identifier(self.proposition_id, "proposition_id")
        if self.status not in {"OPEN", "CLOSED"}:
            raise PropositionValidationError("status must be OPEN or CLOSED")
        _validate_text(self.materiality, "materiality", required=True)

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
        ):
            value = getattr(self, name)
            if value is not None:
                _validate_text(value, name)

        if self.evidence is not None and not isinstance(self.evidence, EvidenceRef):
            raise PropositionValidationError("evidence must be an EvidenceRef")

        if self.status != "CLOSED":
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
