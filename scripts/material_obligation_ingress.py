"""Trusted issue-mapping ingress for the canonical material-obligation ledger."""

from __future__ import annotations

from collections.abc import Mapping
import os
from pathlib import Path
from typing import Any

from scripts.material_obligation_ledger import (
    MaterialObligationLedger,
    ObligationValidationError,
)
from scripts.proposition_registry import RegistryService
from scripts.synthesis_runtime_state import RuntimeStateError


_INGRESS_FIELDS = frozenset(
    {"transaction_id", "material_obligation_ledger"}
)


def record_material_obligation_ledger(
    event: Mapping[str, Any],
    plugin_data: str | os.PathLike[str] | None = None,
) -> Any:
    """Persist one ledger against the transaction-owned canonical registry."""

    if not isinstance(event, Mapping):
        raise RuntimeStateError("material-obligation ingress input must be an object")
    unknown = sorted(set(event) - _INGRESS_FIELDS)
    if unknown:
        raise RuntimeStateError(
            "unsupported material-obligation ingress fields: " + ", ".join(unknown)
        )
    transaction_id = event.get("transaction_id")
    if not isinstance(transaction_id, str) or not transaction_id:
        raise RuntimeStateError("material-obligation ingress transaction_id is required")
    raw_ledger = event.get("material_obligation_ledger")
    try:
        ledger = (
            raw_ledger
            if isinstance(raw_ledger, MaterialObligationLedger)
            else MaterialObligationLedger.from_mapping(raw_ledger)
        )
    except (TypeError, ValueError, ObligationValidationError) as exc:
        raise RuntimeStateError(
            f"material-obligation ingress ledger is invalid: {exc}"
        ) from exc

    service = RegistryService(plugin_data)
    return service.record_material_obligation_ledger(transaction_id, ledger)
