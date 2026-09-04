"""Exact render-slot reconciliation for final legal-proposition synthesis."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import re

from scripts.proposition_rendering import PropositionRenderContract


@dataclass(frozen=True)
class MissingRenderSlot:
    proposition_id: str
    slot_id: str
    kind: str
    expected_text: str


@dataclass(frozen=True)
class DraftReconciliationResult:
    covered: bool
    missing_slots: tuple[MissingRenderSlot, ...]


def normalize_rendered_text(value: str) -> str:
    """Normalize presentation-only Markdown and whitespace differences."""

    if not isinstance(value, str):
        raise TypeError("rendered text must be a string")
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(
        r"(?m)^\s*(?:[-+*]|\d+[.)])\s+",
        "",
        normalized,
    )
    normalized = re.sub(r"[*_`]", "", normalized)
    return re.sub(r"\s+", " ", normalized).strip().casefold()


def reconcile_render_contracts(
    contracts: Sequence[PropositionRenderContract],
    draft: str,
) -> DraftReconciliationResult:
    """Require every expected slot as one contiguous normalized span."""

    normalized_draft = normalize_rendered_text(draft)
    missing: list[MissingRenderSlot] = []
    for contract in contracts:
        for slot in contract.slots:
            expected = normalize_rendered_text(slot.text)
            if not expected or expected not in normalized_draft:
                missing.append(
                    MissingRenderSlot(
                        proposition_id=slot.proposition_id,
                        slot_id=slot.slot_id,
                        kind=slot.kind,
                        expected_text=slot.text,
                    )
                )
    return DraftReconciliationResult(
        covered=not missing,
        missing_slots=tuple(missing),
    )
