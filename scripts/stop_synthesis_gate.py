"""Codex Stop-hook adapter for bounded deterministic render-slot enforcement."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
import re
import sys
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.proposition_reconciliation import reconcile_render_contracts
from scripts.proposition_rendering import build_render_contract
from scripts.proposition_relations import (
    reconcile_range_exception_relation,
)
from scripts.proposition_obligation_closure import evaluate_obligation_closure
from scripts.proposition_render_coverage import evaluate_render_coverage
from scripts.material_obligation_ledger import (
    RegistryClosureResult,
    RegistryClosureViolation,
    evaluate_registry_closure,
)
from scripts.proposition_soundness import evaluate_soundness
from scripts.proposition_source_closure import evaluate_source_closure
from scripts.proposition_registry import RegistryService
from scripts.runtime_root import RuntimeRootError, resolve_runtime_root
from scripts.runtime_transaction import load_current_transaction
from scripts.synthesis_runtime_state import (
    RuntimeStateError,
    record_reconciliation,
    update_repair_count,
)
from scripts.turn_anchor import load_current_turn_anchor


def _fail_closed(system_message: str) -> dict[str, str | bool]:
    return {
        "continue": False,
        "stopReason": "JDIPT synthesis render-slot validation failed",
        "systemMessage": system_message,
    }


def _block(reason: str) -> dict[str, str]:
    return {"decision": "block", "reason": reason}


def _failure_reason(
    result,
    relation_result=None,
    soundness_result=None,
    source_closure_result=None,
    obligation_closure_result=None,
    registry_closure_result=None,
    render_coverage_result=None,
) -> str:
    grouped: dict[str, list[str]] = {}
    for slot in result.missing_slots:
        grouped.setdefault(slot.proposition_id, []).append(slot.expected_text.strip())
    details = " | ".join(
        f"{proposition_id}: " + " ; ".join(texts)
        for proposition_id, texts in grouped.items()
    )
    if relation_result is not None and not relation_result.covered:
        relation_details = ", ".join(relation_result.missing_fields)
        details = (
            f"range_exception_relation: {relation_details}"
            if relation_details
            else "range_exception_relation"
        ) + (f" | {details}" if details else "")
    if soundness_result is not None and not soundness_result.soundness_passed:
        soundness_codes = ", ".join(
            dict.fromkeys(item.code for item in soundness_result.violations)
        )
        details = (
            f"semantic_soundness: {soundness_codes}"
            if soundness_codes
            else "semantic_soundness"
        ) + (f" | {details}" if details else "")
    for label, closure_result in (
        ("source_closure", source_closure_result),
        ("obligation_closure", obligation_closure_result),
        ("registry_closure", registry_closure_result),
    ):
        if closure_result is not None:
            passed = getattr(
                closure_result,
                "source_closure_passed"
                if label == "source_closure"
                else (
                    "obligation_closure_passed"
                    if label == "obligation_closure"
                    else "registry_closure_passed"
                ),
            )
            if not passed:
                codes = ", ".join(
                    dict.fromkeys(item.code for item in closure_result.violations)
                )
                details = (
                    f"{label}: {codes}"
                    if codes
                    else label
                ) + (f" | {details}" if details else "")
    if render_coverage_result is not None and not render_coverage_result.coverage_passed:
        missing_ids = ", ".join(render_coverage_result.missing_proposition_ids)
        coverage_details = render_coverage_result.failure_reason or "coverage failed"
        if missing_ids:
            coverage_details = f"{coverage_details} ({missing_ids})"
        details = (
            f"render_coverage: {coverage_details}"
            + (f" | {details}" if details else "")
        )
    if not details:
        details = "material proposition render slots are missing"
    return (
        "JDIPT synthesis mismatch. Insert the missing mandatory legal proposition "
        "render slots without weakening their legal action, modality, temporal "
        "status, or uncertainty. "
        + details
    )


def _looks_like_jdipt_answer(draft: str) -> bool:
    if not isinstance(draft, str):
        return False
    return all(
        re.search(rf"(?m)^\s*#\s*{number}\.\s*", draft) is not None
        for number in range(1, 5)
    )


def _registry_enforcement_response(
    state,
    event: Mapping[str, Any],
    service: RegistryService,
) -> dict[str, Any] | None:
    if not state.registry_required or state.registry_completed:
        return None
    if (
        state.registry_enforcement_count == 0
        and event.get("stop_hook_active") is not True
    ):
        try:
            service.mark_enforcement(
                state,
                "REGISTRY_ENFORCEMENT",
            )
        except (OSError, RuntimeStateError, ValueError):
            return _fail_closed(
                "JDIPT synthesis validation failed-closed; registry enforcement "
                "state could not be persisted."
            )
        return _block(
            "REGISTRY_ENFORCEMENT: complete the required exact-turn "
            "register_material_proposition contract before final synthesis."
        )
    try:
        service.record_disposition(
            state,
            "REGISTRY_ENFORCEMENT_EXHAUSTED",
        )
    except (OSError, RuntimeStateError, ValueError):
        return _fail_closed(
            "JDIPT synthesis validation failed-closed; registry enforcement "
            "exhaustion could not be persisted."
        )
    return _fail_closed(
        "REGISTRY_ENFORCEMENT_EXHAUSTED: the required exact-turn registry "
        "completion was not proven after one bounded continuation."
    )


def _canonical_stop_event(
    event: Mapping[str, Any],
    plugin_data: str | None,
) -> dict[str, Any]:
    """Validate Stop against the current capability transaction only."""

    draft = event.get("last_assistant_message")
    draft = draft if isinstance(draft, str) else ""
    jdipt_output = _looks_like_jdipt_answer(draft)
    try:
        root = resolve_runtime_root(plugin_data)
        transaction = load_current_transaction(root, include_registry_snapshot=False)
    except (OSError, RuntimeRootError, RuntimeStateError, TypeError, ValueError) as exc:
        if jdipt_output:
            return _fail_closed(
                "STOP_RUNTIME_UNAVAILABLE: canonical runtime transaction could not "
                f"be read: {exc}"
            )
        return {}

    if transaction is None:
        if jdipt_output:
            return _fail_closed(
                "STOP_TRANSACTION_MISSING: no canonical transaction exists for "
                "this JDIPT output."
            )
        return {}

    try:
        anchor = load_current_turn_anchor(root)
        registry = RegistryService(root).read_canonical_registry(
            transaction.canonical_registry_id
        )
    except (OSError, RuntimeStateError, TypeError, ValueError) as exc:
        return _fail_closed(
            "STOP_CANONICAL_STATE_INVALID: transaction/registry evidence could not "
            f"be read: {exc}"
        )

    same_epoch = (
        transaction.epoch == anchor.epoch
        and transaction.anchor_id == anchor.anchor_id
    )
    same_registry = bool(
        registry is not None
        and registry.transaction_id == transaction.transaction_id
        and registry.registry_state == "CLOSED"
    )
    if (
        same_epoch
        and same_registry
        and transaction.transaction_state == "CLOSED"
        and transaction.finalized
        and transaction.registry_completed
    ):
        return {}

    return _fail_closed(
        "STOP_TRANSACTION_NOT_FINALIZED: current epoch requires a canonical "
        "transaction with finalized=true, registry_completed=true, and CLOSED "
        "transaction/registry state."
    )


def handle_stop_event(
    event: Mapping[str, Any],
    plugin_data: str | None = None,
) -> dict[str, Any]:
    """Return the documented Stop-hook response for one Codex event."""

    if not isinstance(event, Mapping):
        return _fail_closed(
            "JDIPT synthesis validation failed closed; invalid Stop input."
        )

    return _canonical_stop_event(event, plugin_data)

    session_id = event.get("session_id")
    turn_id = event.get("turn_id")
    draft = event.get("last_assistant_message")
    if not isinstance(draft, str):
        draft = ""
    if not isinstance(session_id, str) or not isinstance(turn_id, str):
        if _looks_like_jdipt_answer(draft):
            return _fail_closed(
                "ACTIVATION_BYPASS: JDIPT-shaped output has no exact session/turn "
                "identity for registry validation."
            )
        return {}

    service = RegistryService(plugin_data)
    try:
        state = service.read_state(session_id, turn_id)
    except (OSError, RuntimeStateError, ValueError):
        return _fail_closed(
            "JDIPT synthesis validation failed closed; runtime state was invalid."
        )
    if state is None:
        if not _looks_like_jdipt_answer(draft):
            return {}
        try:
            state = service.begin_pending(session_id, turn_id)
            service.record_disposition(state, "ACTIVATION_BYPASS")
        except (OSError, RuntimeStateError, ValueError):
            return _fail_closed(
                "JDIPT synthesis validation failed closed; pending activation "
                "state could not be persisted."
            )
        return _fail_closed(
            "ACTIVATION_BYPASS: JDIPT-shaped output was observed without an "
            "explicit activation/registry completion for this exact turn."
        )

    enforcement_response = _registry_enforcement_response(
        state,
        event,
        service,
    )
    if enforcement_response is not None:
        return enforcement_response
    if not state.registry_active:
        return {}

    contracts = [
        contract
        for proposition in state.propositions
        if (contract := build_render_contract(proposition)).slots
    ]
    result = reconcile_render_contracts(contracts, draft)
    relation_result = reconcile_range_exception_relation(state.propositions, draft)
    try:
        soundness_result = evaluate_soundness(state.propositions, contracts, draft)
        source_closure_result = evaluate_source_closure(state.propositions, draft)
        obligation_closure_result = evaluate_obligation_closure(
            state.propositions,
            contracts,
            draft,
        )
        if state.material_obligation_ledger_required and state.material_obligation_ledger is None:
            registry_closure_result = RegistryClosureResult(
                registry_closure_passed=False,
                violations=(
                    RegistryClosureViolation(
                        code="MATERIAL_OBLIGATION_LEDGER_MISSING",
                        obligation_id=None,
                        proposition_id=None,
                        source_id=None,
                        reason="Task 8 state requires an independently supplied obligation ledger",
                    ),
                ),
            )
        elif state.material_obligation_ledger is None:
            registry_closure_result = None
        else:
            registry_closure_result = evaluate_registry_closure(
                state.material_obligation_ledger,
                state.material_obligation_ledger.verified_source_evidence,
                state.propositions,
            )
        render_coverage_result = None
        if state.material_obligation_ledger_required:
            render_coverage_result = evaluate_render_coverage(
                state.material_obligation_ledger,
                registry_closure_result,
                state.propositions,
                draft,
            )
    except (TypeError, UnicodeError, ValueError):
        return _fail_closed(
            "JDIPT synthesis validation failed-closed; semantic/source/obligation "
            "closure could not be evaluated safely."
        )
    overall_covered = result.covered and (
        relation_result is None or relation_result.covered
    ) and (
        render_coverage_result is None
        or render_coverage_result.coverage_passed
    )
    overall_sound = soundness_result.soundness_passed
    overall_source = (
        source_closure_result.source_closure_passed
        and source_closure_result.authority_closure_passed
        and source_closure_result.temporal_source_closure_passed
    )
    overall_obligation = (
        obligation_closure_result.obligation_closure_passed
        and obligation_closure_result.dependency_closure_passed
        and obligation_closure_result.final_conclusion_support_passed
    )
    overall_registry = (
        registry_closure_result is None
        or registry_closure_result.registry_closure_passed
    )
    phase = "second" if state.repair_count else "first"
    if (
        overall_covered
        and overall_sound
        and overall_source
        and overall_obligation
        and overall_registry
    ):
        try:
            updated = record_reconciliation(
                state,
                phase,
                result,
                plugin_data,
                relation_result=relation_result,
                soundness_result=soundness_result,
                source_closure_result=source_closure_result,
                obligation_closure_result=obligation_closure_result,
                registry_closure_result=registry_closure_result,
                render_coverage_result=render_coverage_result,
            )
            service.record_disposition(updated, "COMPLETED")
        except (OSError, RuntimeStateError, ValueError):
            return _fail_closed(
                "JDIPT synthesis validation failed-closed; reconciliation "
                "evidence could not be persisted."
            )
        return {}

    if state.repair_count != 0 or event.get("stop_hook_active") is True:
        try:
            updated = record_reconciliation(
                state,
                "second",
                result,
                plugin_data,
                relation_result=relation_result,
                soundness_result=soundness_result,
                source_closure_result=source_closure_result,
                obligation_closure_result=obligation_closure_result,
                registry_closure_result=registry_closure_result,
                render_coverage_result=render_coverage_result,
            )
            service.record_disposition(
                updated,
                "REPAIR_EXHAUSTED",
            )
        except (OSError, RuntimeStateError, ValueError):
            return _fail_closed(
                "JDIPT synthesis validation failed-closed; final reconciliation "
                "evidence could not be persisted."
            )
        return _fail_closed(
            "JDIPT synthesis validation failed-closed; the bounded repair did not "
            "produce an acceptable final answer."
        )

    try:
        updated = update_repair_count(state, 1, plugin_data)
        updated = record_reconciliation(
            updated,
            "first",
            result,
            plugin_data,
            relation_result=relation_result,
            soundness_result=soundness_result,
            source_closure_result=source_closure_result,
            obligation_closure_result=obligation_closure_result,
            registry_closure_result=registry_closure_result,
            render_coverage_result=render_coverage_result,
        )
        service.record_disposition(updated, "REPAIR_REQUESTED")
    except (OSError, RuntimeStateError, ValueError):
        return _fail_closed(
            "JDIPT synthesis validation failed-closed; repair state could not be persisted."
        )
    return _block(
        _failure_reason(
            result,
            relation_result,
            soundness_result,
            source_closure_result,
            obligation_closure_result,
            registry_closure_result,
            render_coverage_result,
        )
    )


def _main() -> int:
    try:
        event = json.load(sys.stdin)
        response = handle_stop_event(event)
    except (OSError, UnicodeError, json.JSONDecodeError, RuntimeStateError):
        response = _fail_closed(
            "JDIPT synthesis validation failed closed; Stop input was invalid."
        )
    json.dump(response, sys.stdout, ensure_ascii=False, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
