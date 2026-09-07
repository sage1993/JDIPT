"""Typed material-obligation ledger and canonical registry closure gate."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum
import re
from typing import Any

from scripts.legal_proposition import (
    EvidenceRef,
    LegalProposition,
    Materiality,
    PropositionStatus,
)
from scripts.proposition_source_closure import (
    authority_satisfies,
    temporal_satisfies,
)


class ObligationSourceStatus(StrEnum):
    """Strict source-resolution states for one material obligation."""

    SOURCE_CONFIRMED = "SOURCE_CONFIRMED"
    SOURCE_UNRESOLVED = "SOURCE_UNRESOLVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


# These names are aliases for one canonical status type, not separate status
# hierarchies.  The explicit source-resolution name remains the primary API.
ObligationStatus = ObligationSourceStatus
SourceResolutionStatus = ObligationSourceStatus


class ObligationValidationError(ValueError):
    """Raised when a material-obligation ledger value is unsafe or malformed."""


@dataclass(frozen=True)
class MaterialObligation:
    """One independently supplied material legal issue to be closed."""

    obligation_id: str
    issue_type: str
    source_status: ObligationSourceStatus
    evidence_source_ids: tuple[str, ...] = ()
    proposition_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_identifier(self.obligation_id, "obligation_id")
        _validate_text(self.issue_type, "issue_type", required=True)
        if not isinstance(self.source_status, ObligationSourceStatus):
            raise ObligationValidationError(
                "source_status must be a canonical ObligationSourceStatus value"
            )
        _validate_identifier_tuple(self.evidence_source_ids, "evidence_source_ids")
        _validate_identifier_tuple(self.proposition_ids, "proposition_ids")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> MaterialObligation:
        if not isinstance(payload, Mapping):
            raise ObligationValidationError("material obligation must be an object")
        allowed = {
            "obligation_id",
            "issue_type",
            "source_status",
            "evidence_source_ids",
            "proposition_ids",
        }
        unknown = sorted(set(payload) - allowed)
        if unknown:
            raise ObligationValidationError(
                "unsupported material obligation fields: " + ", ".join(unknown)
            )
        raw_status = payload.get("source_status")
        if not isinstance(raw_status, str):
            raise ObligationValidationError(
                "source_status must be one of the supported typed values"
            )
        try:
            status = ObligationSourceStatus(raw_status)
        except ValueError as exc:
            raise ObligationValidationError(
                f"source_status has an unknown value: {raw_status!r}"
            ) from exc
        return cls(
            obligation_id=payload.get("obligation_id"),
            issue_type=payload.get("issue_type"),
            source_status=status,
            evidence_source_ids=_tuple_field(
                payload.get("evidence_source_ids", ()),
                "evidence_source_ids",
            ),
            proposition_ids=_tuple_field(
                payload.get("proposition_ids", ()),
                "proposition_ids",
            ),
        )


@dataclass(frozen=True)
class MaterialObligationLedger:
    """Required obligations plus the explicit verified evidence set."""

    obligations: tuple[MaterialObligation, ...]
    verified_source_evidence: tuple[EvidenceRef, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.obligations, tuple):
            raise ObligationValidationError("obligations must be a tuple")
        if not isinstance(self.verified_source_evidence, tuple):
            raise ObligationValidationError(
                "verified_source_evidence must be a tuple"
            )
        if any(not isinstance(item, MaterialObligation) for item in self.obligations):
            raise ObligationValidationError(
                "obligations must contain MaterialObligation instances"
            )
        if any(not isinstance(item, EvidenceRef) for item in self.verified_source_evidence):
            raise ObligationValidationError(
                "verified_source_evidence must contain EvidenceRef instances"
            )
        _reject_duplicate_ids(
            (item.obligation_id for item in self.obligations),
            "obligation_id",
        )
        _reject_duplicate_ids(
            (item.source_id for item in self.verified_source_evidence),
            "source_id",
        )

    @property
    def source_evidence(self) -> tuple[EvidenceRef, ...]:
        """Compatibility name for the same canonical verified evidence set."""

        return self.verified_source_evidence

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> MaterialObligationLedger:
        if not isinstance(payload, Mapping):
            raise ObligationValidationError("material obligation ledger must be an object")
        allowed = {"obligations", "verified_source_evidence"}
        unknown = sorted(set(payload) - allowed)
        if unknown:
            raise ObligationValidationError(
                "unsupported material obligation ledger fields: "
                + ", ".join(unknown)
            )
        missing = sorted(allowed - set(payload))
        if missing:
            raise ObligationValidationError(
                "material obligation ledger is missing required fields: "
                + ", ".join(missing)
            )
        raw_obligations = payload["obligations"]
        raw_evidence = payload["verified_source_evidence"]
        if not isinstance(raw_obligations, Sequence) or isinstance(
            raw_obligations, (str, bytes)
        ):
            raise ObligationValidationError("obligations must be an array")
        if not isinstance(raw_evidence, Sequence) or isinstance(
            raw_evidence, (str, bytes)
        ):
            raise ObligationValidationError(
                "verified_source_evidence must be an array"
            )
        obligations = tuple(
            item
            if isinstance(item, MaterialObligation)
            else MaterialObligation.from_mapping(item)
            for item in raw_obligations
        )
        try:
            evidence = tuple(
                item if isinstance(item, EvidenceRef) else EvidenceRef(**item)
                for item in raw_evidence
            )
        except (TypeError, ValueError, KeyError) as exc:
            raise ObligationValidationError(
                f"verified_source_evidence is malformed: {exc}"
            ) from exc
        return cls(obligations=obligations, verified_source_evidence=evidence)


@dataclass(frozen=True)
class RegistryClosureViolation:
    code: str
    obligation_id: str | None
    proposition_id: str | None
    source_id: str | None
    reason: str


@dataclass(frozen=True)
class RegistryClosureResult:
    registry_closure_passed: bool
    violations: tuple[RegistryClosureViolation, ...]


_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def _validate_text(value: object, field: str, *, required: bool = False) -> None:
    if not isinstance(value, str):
        raise ObligationValidationError(f"{field} must be a string")
    if required and not value.strip():
        raise ObligationValidationError(f"{field} is required")
    if len(value) > 2048:
        raise ObligationValidationError(f"{field} exceeds the runtime metadata limit")
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise ObligationValidationError(f"{field} contains an invalid Unicode surrogate")
    if any(ord(char) < 32 and char not in "\t\r\n" for char in value):
        raise ObligationValidationError(f"{field} contains a control character")


def _validate_identifier(value: object, field: str) -> None:
    _validate_text(value, field, required=True)
    if not _IDENTIFIER_PATTERN.fullmatch(value):
        raise ObligationValidationError(
            f"{field} must be a safe non-empty identifier"
        )


def _tuple_field(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ObligationValidationError(f"{field} must be an array")
    return tuple(value)


def _validate_identifier_tuple(value: object, field: str) -> None:
    if not isinstance(value, tuple):
        raise ObligationValidationError(f"{field} must be a tuple")
    for item in value:
        _validate_identifier(item, field[:-1] if field.endswith("s") else field)
    _reject_duplicate_ids(value, field)


def _reject_duplicate_ids(values: Sequence[str] | Any, field: str) -> None:
    items = tuple(values)
    if len(set(items)) != len(items):
        raise ObligationValidationError(f"duplicate {field} in material obligation ledger")


def _coerce_obligations(
    required_obligations: MaterialObligationLedger | Sequence[MaterialObligation],
) -> tuple[MaterialObligation, ...]:
    if isinstance(required_obligations, MaterialObligationLedger):
        return required_obligations.obligations
    if not isinstance(required_obligations, Sequence) or isinstance(
        required_obligations, (str, bytes)
    ):
        raise ObligationValidationError("required obligations must be an array")
    return tuple(
        item
        if isinstance(item, MaterialObligation)
        else MaterialObligation.from_mapping(item)
        for item in required_obligations
    )


def _coerce_evidence(
    resolved_source_evidence: Sequence[EvidenceRef] | Mapping[str, EvidenceRef],
) -> tuple[EvidenceRef, ...]:
    if isinstance(resolved_source_evidence, Mapping):
        if any(
            not isinstance(key, str) or key != value.source_id
            for key, value in resolved_source_evidence.items()
            if isinstance(value, EvidenceRef)
        ):
            raise ObligationValidationError(
                "resolved source evidence mapping keys must match source_id"
            )
        values = tuple(resolved_source_evidence.values())
    elif isinstance(resolved_source_evidence, Sequence) and not isinstance(
        resolved_source_evidence, (str, bytes)
    ):
        values = tuple(resolved_source_evidence)
    else:
        raise ObligationValidationError(
            "resolved source evidence must be an array or source-id mapping"
        )
    if any(not isinstance(item, EvidenceRef) for item in values):
        raise ObligationValidationError(
            "resolved source evidence must contain EvidenceRef instances"
        )
    _reject_duplicate_ids((item.source_id for item in values), "source_id")
    return values


def _violation(
    violations: list[RegistryClosureViolation],
    code: str,
    *,
    obligation_id: str | None = None,
    proposition_id: str | None = None,
    source_id: str | None = None,
    reason: str,
) -> None:
    violations.append(
        RegistryClosureViolation(
            code=code,
            obligation_id=obligation_id,
            proposition_id=proposition_id,
            source_id=source_id,
            reason=reason,
        )
    )


def _malformed_result(reason: str) -> RegistryClosureResult:
    return RegistryClosureResult(
        registry_closure_passed=False,
        violations=(
            RegistryClosureViolation(
                code="MALFORMED_REGISTRY_CLOSURE_INPUT",
                obligation_id=None,
                proposition_id=None,
                source_id=None,
                reason=reason,
            ),
        ),
    )


def evaluate_registry_closure(
    required_obligations: MaterialObligationLedger | Sequence[MaterialObligation],
    resolved_source_evidence: Sequence[EvidenceRef]
    | Mapping[str, EvidenceRef]
    | None,
    registered_propositions: Sequence[LegalProposition],
) -> RegistryClosureResult:
    """Compare required obligations, resolved evidence, and canonical propositions."""

    try:
        obligations = _coerce_obligations(required_obligations)
        if resolved_source_evidence is None:
            if not isinstance(required_obligations, MaterialObligationLedger):
                raise ObligationValidationError(
                    "resolved source evidence is required without a ledger"
                )
            evidence = required_obligations.verified_source_evidence
        else:
            evidence = _coerce_evidence(resolved_source_evidence)
        if not isinstance(registered_propositions, Sequence) or isinstance(
            registered_propositions, (str, bytes)
        ):
            raise ObligationValidationError("registered propositions must be an array")
        propositions = tuple(registered_propositions)
        if any(not isinstance(item, LegalProposition) for item in propositions):
            raise ObligationValidationError(
                "registered propositions must contain LegalProposition instances"
            )
        _reject_duplicate_ids(
            (item.obligation_id for item in obligations),
            "obligation_id",
        )
        _reject_duplicate_ids((item.proposition_id for item in propositions), "proposition_id")
    except (KeyError, TypeError, ValueError, ObligationValidationError) as exc:
        return _malformed_result(str(exc))

    violations: list[RegistryClosureViolation] = []
    by_source_id = {item.source_id: item for item in evidence}
    by_proposition_id = {item.proposition_id: item for item in propositions}

    for obligation_item in obligations:
        status = obligation_item.source_status
        if status is ObligationSourceStatus.NOT_APPLICABLE:
            if obligation_item.evidence_source_ids or obligation_item.proposition_ids:
                _violation(
                    violations,
                    "NOT_APPLICABLE_WITH_LINKAGE",
                    obligation_id=obligation_item.obligation_id,
                    reason=(
                        "NOT_APPLICABLE cannot carry source-evidence or proposition links"
                    ),
                )
            continue

        if status is ObligationSourceStatus.SOURCE_UNRESOLVED:
            if obligation_item.evidence_source_ids:
                _violation(
                    violations,
                    "UNRESOLVED_SOURCE_HAS_CONFIRMED_EVIDENCE",
                    obligation_id=obligation_item.obligation_id,
                    source_id=obligation_item.evidence_source_ids[0],
                    reason=(
                        "SOURCE_UNRESOLVED cannot claim an explicitly resolved evidence link"
                    ),
                )
            for proposition_id in obligation_item.proposition_ids:
                proposition = by_proposition_id.get(proposition_id)
                if proposition is None:
                    _violation(
                        violations,
                        "LINKED_PROPOSITION_MISSING",
                        obligation_id=obligation_item.obligation_id,
                        proposition_id=proposition_id,
                        reason="unresolved obligation points to an unregistered proposition",
                    )
                elif proposition.status is PropositionStatus.CLOSED:
                    _violation(
                        violations,
                        "UNRESOLVED_SOURCE_PROMOTED_TO_CLOSED",
                        obligation_id=obligation_item.obligation_id,
                        proposition_id=proposition_id,
                        reason=(
                            "SOURCE_UNRESOLVED cannot be linked to a CLOSED proposition"
                        ),
                    )
            continue

        if status is not ObligationSourceStatus.SOURCE_CONFIRMED:
            _violation(
                violations,
                "UNKNOWN_SOURCE_STATUS",
                obligation_id=obligation_item.obligation_id,
                reason=f"unsupported source status: {status!r}",
            )
            continue

        if not obligation_item.evidence_source_ids:
            _violation(
                violations,
                "CONFIRMED_OBLIGATION_WITHOUT_EVIDENCE",
                obligation_id=obligation_item.obligation_id,
                reason="SOURCE_CONFIRMED requires at least one resolved evidence link",
            )
        if not obligation_item.proposition_ids:
            _violation(
                violations,
                "CONFIRMED_OBLIGATION_WITHOUT_PROPOSITION",
                obligation_id=obligation_item.obligation_id,
                reason="SOURCE_CONFIRMED requires at least one canonical proposition link",
            )

        linked_evidence: list[EvidenceRef] = []
        for source_id in obligation_item.evidence_source_ids:
            source = by_source_id.get(source_id)
            if source is None:
                _violation(
                    violations,
                    "CONFIRMED_EVIDENCE_UNRESOLVED",
                    obligation_id=obligation_item.obligation_id,
                    source_id=source_id,
                    reason="obligation evidence source ID is absent from resolved evidence",
                )
            else:
                linked_evidence.append(source)

        for proposition_id in obligation_item.proposition_ids:
            proposition = by_proposition_id.get(proposition_id)
            if proposition is None:
                _violation(
                    violations,
                    "LINKED_PROPOSITION_MISSING",
                    obligation_id=obligation_item.obligation_id,
                    proposition_id=proposition_id,
                    reason="confirmed obligation points to an unregistered proposition",
                )
                continue
            _check_linked_proposition(
                violations,
                obligation_item,
                proposition,
                linked_evidence,
            )

    for proposition in propositions:
        if proposition.materiality is not Materiality.MATERIAL:
            continue
        if proposition.status is not PropositionStatus.CLOSED:
            continue
        proposition_evidence = proposition.evidence
        if proposition_evidence is None:
            _violation(
                violations,
                "PROPOSITION_WITHOUT_REQUIRED_EVIDENCE",
                proposition_id=proposition.proposition_id,
                reason="CLOSED material proposition has no evidence reference",
            )
            continue
        resolved = by_source_id.get(proposition_evidence.source_id)
        if resolved is None or resolved != proposition_evidence:
            _violation(
                violations,
                "PROPOSITION_WITHOUT_REQUIRED_EVIDENCE",
                proposition_id=proposition.proposition_id,
                source_id=proposition_evidence.source_id,
                reason=(
                    "CLOSED material proposition evidence is absent from the explicit "
                    "resolved source-evidence set"
                ),
            )
        _check_temporal_and_authority(
            violations,
            proposition,
            proposition_evidence,
        )

    unique: list[RegistryClosureViolation] = []
    seen: set[tuple[str, str | None, str | None, str | None]] = set()
    for item in violations:
        key = (item.code, item.obligation_id, item.proposition_id, item.source_id)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return RegistryClosureResult(
        registry_closure_passed=not unique,
        violations=tuple(unique),
    )


def _check_linked_proposition(
    violations: list[RegistryClosureViolation],
    obligation: MaterialObligation,
    proposition: LegalProposition,
    linked_evidence: Sequence[EvidenceRef],
) -> None:
    if proposition.materiality is not Materiality.MATERIAL:
        _violation(
            violations,
            "MATERIALITY_MISMATCH",
            obligation_id=obligation.obligation_id,
            proposition_id=proposition.proposition_id,
            reason="material obligation is linked to a non-material proposition",
        )
    if proposition.status is not PropositionStatus.CLOSED:
        _violation(
            violations,
            "CONFIRMED_OBLIGATION_NOT_CLOSED",
            obligation_id=obligation.obligation_id,
            proposition_id=proposition.proposition_id,
            reason="SOURCE_CONFIRMED requires a CLOSED canonical proposition",
        )
    if proposition.evidence is None or proposition.evidence not in linked_evidence:
        _violation(
            violations,
            "PROPOSITION_WITHOUT_REQUIRED_EVIDENCE",
            obligation_id=obligation.obligation_id,
            proposition_id=proposition.proposition_id,
            source_id=(
                proposition.evidence.source_id if proposition.evidence is not None else None
            ),
            reason=(
                "linked proposition does not carry an exact EvidenceRef from the "
                "confirmed obligation evidence set"
            ),
        )
        return
    _check_temporal_and_authority(violations, proposition, proposition.evidence)


def _check_temporal_and_authority(
    violations: list[RegistryClosureViolation],
    proposition: LegalProposition,
    evidence: EvidenceRef,
) -> None:
    if (
        proposition.required_source_type is not None
        and evidence.authority_kind != proposition.required_source_type
    ):
        _violation(
            violations,
            "INSUFFICIENT_AUTHORITY",
            proposition_id=proposition.proposition_id,
            source_id=evidence.source_id,
            reason=(
                "evidence source type does not satisfy the proposition source-type "
                "requirement"
            ),
        )
    elif not authority_satisfies(proposition, evidence.authority_kind):
        _violation(
            violations,
            "INSUFFICIENT_AUTHORITY",
            proposition_id=proposition.proposition_id,
            source_id=evidence.source_id,
            reason="evidence authority does not satisfy proposition authority requirements",
        )
    temporal_ok, _ = temporal_satisfies(proposition, evidence.temporal_status)
    if not temporal_ok:
        _violation(
            violations,
            "TEMPORAL_CONTRADICTION",
            proposition_id=proposition.proposition_id,
            source_id=evidence.source_id,
            reason=(
                "evidence temporal status does not satisfy the proposition temporal "
                "requirement"
            ),
        )


def validate_registry_closure(
    required_obligations: MaterialObligationLedger | Sequence[MaterialObligation],
    resolved_source_evidence: Sequence[EvidenceRef]
    | Mapping[str, EvidenceRef]
    | None,
    registered_propositions: Sequence[LegalProposition],
) -> RegistryClosureResult:
    """Canonical named validator for the registry closure gate."""

    return evaluate_registry_closure(
        required_obligations,
        resolved_source_evidence,
        registered_propositions,
    )


def material_obligation_ledger_to_dict(
    ledger: MaterialObligationLedger,
) -> dict[str, Any]:
    """Serialize the ledger without changing its canonical links."""

    if not isinstance(ledger, MaterialObligationLedger):
        raise ObligationValidationError("ledger must be a MaterialObligationLedger")
    return {
        "obligations": [
            {
                "obligation_id": item.obligation_id,
                "issue_type": item.issue_type,
                "source_status": item.source_status.value,
                "evidence_source_ids": list(item.evidence_source_ids),
                "proposition_ids": list(item.proposition_ids),
            }
            for item in ledger.obligations
        ],
        "verified_source_evidence": [asdict(item) for item in ledger.verified_source_evidence],
    }


def registry_closure_result_to_dict(
    result: RegistryClosureResult,
) -> dict[str, Any]:
    """Serialize closure evidence for the existing reconciliation snapshot."""

    if not isinstance(result, RegistryClosureResult):
        raise ObligationValidationError("result must be a RegistryClosureResult")
    payload = asdict(result)
    payload["violations"] = [asdict(item) for item in result.violations]
    return payload
