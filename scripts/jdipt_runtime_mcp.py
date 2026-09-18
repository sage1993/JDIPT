"""Capability-only stdio MCP server for the JDIPT runtime transaction."""
from __future__ import annotations

from collections.abc import Mapping
import json
import os
from pathlib import Path
import sys
from typing import Any, get_args

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.runtime_root import RuntimeRootError, resolve_runtime_root
from scripts.legal_proposition import (
    AuthorityKind,
    AuthorityRequirement,
    CANONICAL_PROPOSITION_FIELDS,
    canonical_proposition_schema,
    Modality,
    Polarity,
    TemporalRequirement,
    TemporalStatus,
)
from scripts.runtime_transaction import (
    RuntimeStateError,
    begin_runtime_turn as _begin_runtime_turn,
    finalize_transaction,
    load_current_transaction,
    record_ledger,
    register_proposition,
)
from scripts.material_obligation_ledger import MaterialObligationLedger
from scripts.proposition_registry import RegistryService, validate_typed_proposition
from scripts.turn_anchor import TurnAnchorError


BEGIN_TOOL = "begin_runtime_turn"
LEDGER_TOOL = "submit_material_obligation_ledger"
PROPOSITION_TOOL = "register_material_proposition"
FINALIZE_TOOL = "finalize_runtime_turn"
COMMIT_PREPARED_TOOL = "commit_prepared_runtime_turn"
TOOL_NAMES = (BEGIN_TOOL, LEDGER_TOOL, PROPOSITION_TOOL, FINALIZE_TOOL)

PROPOSITION_FIELDS = CANONICAL_PROPOSITION_FIELDS
TOOL_ARGUMENT_FIELDS = {
    BEGIN_TOOL: frozenset(),
    LEDGER_TOOL: frozenset({"turn_capability", "ledger"}),
    PROPOSITION_TOOL: frozenset({"turn_capability", "proposition"}),
    FINALIZE_TOOL: frozenset({"turn_capability"}),
    COMMIT_PREPARED_TOOL: frozenset({"ledger", "propositions"}),
}
_AUTHORITY_KIND_VALUES = list(get_args(AuthorityKind))
_TEMPORAL_STATUS_VALUES = list(get_args(TemporalStatus))
_MODALITY_VALUES = [item.value for item in Modality]
_POLARITY_VALUES = [item.value for item in Polarity]
_AUTHORITY_REQUIREMENT_VALUES = [item.value for item in AuthorityRequirement]
_TEMPORAL_REQUIREMENT_VALUES = [item.value for item in TemporalRequirement]


def _schema(properties: Mapping[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": dict(properties),
    }


def _prepared_proposition_schema() -> dict[str, Any]:
    return canonical_proposition_schema()


def _prepared_ledger_schema() -> dict[str, Any]:
    return _schema(
        {
            "obligations": {
                "type": "array",
                "items": _schema(
                    {
                        "obligation_id": {"type": "string"},
                        "issue_type": {"type": "string"},
                        "source_status": {
                            "type": "string",
                            "enum": [
                                "SOURCE_CONFIRMED",
                                "SOURCE_UNRESOLVED",
                                "NOT_APPLICABLE",
                            ],
                        },
                        "evidence_source_ids": {
                            "type": "array",
                            "description": (
                                "Unique source IDs referenced by this obligation. Include each ID once, "
                                "even when verified_source_evidence contains multiple distinct spans "
                                "for that same source_id."
                            ),
                            "items": {"type": "string"},
                            "uniqueItems": True,
                        },
                        "proposition_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    ["obligation_id", "issue_type", "source_status"],
                ),
            },
            "verified_source_evidence": {
                "type": "array",
                "description": (
                    "Include one verified reference for each distinct source clause/span. "
                    "Every CLOSED proposition must match one item exactly."
                ),
                "items": _schema(
                    {
                        "source_id": {"type": "string"},
                        "authority_kind": {
                            "type": "string",
                            "enum": _AUTHORITY_KIND_VALUES,
                        },
                        "source_title": {"type": "string"},
                        "source_locator": {"type": "string"},
                        "evidence_span": {"type": "string"},
                        "temporal_status": {
                            "type": "string",
                            "enum": _TEMPORAL_STATUS_VALUES,
                        },
                        "temporal_render_text": {"type": "string"},
                    },
                    [
                        "source_id",
                        "authority_kind",
                        "source_title",
                        "source_locator",
                        "evidence_span",
                        "temporal_status",
                    ],
                ),
            },
        },
        ["obligations", "verified_source_evidence"],
    )


def _preflight_prepared_turn(
    ledger: Mapping[str, Any] | None,
    propositions: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    """Validate the full prepared bundle before claiming an epoch anchor."""

    if not isinstance(ledger, Mapping):
        raise RuntimeStateError("PREPARED_TURN_INVALID: ledger must be an object")
    raw_evidence = ledger.get("verified_source_evidence")
    if not isinstance(raw_evidence, list):
        raise RuntimeStateError(
            "PREPARED_TURN_INVALID: verified_source_evidence must be an array"
        )
    normalized_ledger = dict(ledger)
    normalized_ledger["verified_source_evidence"] = [
        {**item, "temporal_render_text": item.get("temporal_render_text")}
        if isinstance(item, Mapping)
        else item
        for item in raw_evidence
    ]
    try:
        typed_ledger = MaterialObligationLedger.from_mapping(normalized_ledger)
    except (TypeError, ValueError) as exc:
        raise RuntimeStateError(f"PREPARED_TURN_INVALID: ledger: {exc}") from exc
    if not typed_ledger.obligations:
        raise RuntimeStateError("PREPARED_TURN_INVALID: ledger requires at least one obligation")
    if not isinstance(propositions, list) or not propositions:
        raise RuntimeStateError("PREPARED_TURN_INVALID: propositions must be a non-empty array")

    typed_propositions = []
    try:
        typed_propositions = [validate_typed_proposition(item) for item in propositions]
    except (RuntimeStateError, TypeError, ValueError) as exc:
        raise RuntimeStateError(f"PREPARED_TURN_INVALID: proposition: {exc}") from exc

    proposition_ids = [item.proposition_id for item in typed_propositions]
    required_ids = {
        proposition_id
        for obligation in typed_ledger.obligations
        for proposition_id in obligation.proposition_ids
    }
    if not required_ids or len(proposition_ids) != len(set(proposition_ids)) or set(proposition_ids) != required_ids:
        raise RuntimeStateError(
            "PROPOSITION_SET_MISMATCH: prepared propositions must exactly match the ledger obligation set"
        )

    verified_evidence = set(typed_ledger.verified_source_evidence)
    for proposition in typed_propositions:
        if proposition.status.value == "CLOSED" and proposition.evidence not in verified_evidence:
            raise RuntimeStateError(
                f"CLOSED_PROPOSITION_EVIDENCE_MISMATCH: {proposition.proposition_id}"
            )
    semantic_preflight = RegistryService.preflight_typed_turn(
        typed_ledger,
        typed_propositions,
    )
    if not semantic_preflight.get("covered") or not semantic_preflight.get(
        "registry_closure_passed"
    ):
        failures = ",".join(semantic_preflight.get("failures", []))
        raise RuntimeStateError(f"SEMANTIC_PREFLIGHT_FAILED: {failures or 'semantic gate failed'}")
    return (
        normalized_ledger,
        [dict(item) for item in propositions],
        {"passed": True, "proposition_count": len(typed_propositions)},
    )


def tool_definitions() -> list[dict[str, Any]]:
    ledger_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["obligations", "verified_source_evidence"],
        "properties": {
            "obligations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["obligation_id", "issue_type", "source_status"],
                    "properties": {
                        "obligation_id": {"type": "string"},
                        "issue_type": {"type": "string"},
                        "source_status": {
                            "type": "string",
                            "enum": [
                                "SOURCE_CONFIRMED",
                                "SOURCE_UNRESOLVED",
                                "NOT_APPLICABLE",
                            ],
                        },
                        "evidence_source_ids": {
                            "type": "array",
                            "description": (
                                "Unique source IDs referenced by this obligation. Include each ID once, "
                                "even when verified_source_evidence contains multiple distinct spans "
                                "for that same source_id."
                            ),
                            "items": {"type": "string"},
                            "uniqueItems": True,
                        },
                        "proposition_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
            },
            "verified_source_evidence": {
                "type": "array",
                "description": (
                    "Include one verified reference for each distinct source clause/span. "
                    "Distinct references may share a source_id. Every CLOSED proposition "
                    "must use an evidence reference whose fields exactly match one array item."
                ),
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "source_id",
                        "authority_kind",
                        "source_title",
                        "source_locator",
                        "evidence_span",
                        "temporal_status",
                    ],
                    "properties": {
                        "source_id": {"type": "string"},
                        "authority_kind": {
                            "type": "string",
                            "enum": _AUTHORITY_KIND_VALUES,
                            "description": "Source kind; use one of the listed lowercase values.",
                        },
                        "source_title": {"type": "string"},
                        "source_locator": {"type": "string"},
                        "evidence_span": {"type": "string"},
                        "temporal_status": {
                            "type": "string",
                            "enum": _TEMPORAL_STATUS_VALUES,
                            "description": (
                                "Verification status of this evidence, not the proposition's "
                                "required_temporal_status."
                            ),
                        },
                        "temporal_render_text": {"type": "string"},
                    },
                },
            },
        },
    }
    definitions = [
        {
            "name": BEGIN_TOOL,
            "description": "Claim the current authoritative JDIPT turn boundary.",
            "inputSchema": _schema({}, []),
        },
        {
            "name": LEDGER_TOOL,
            "description": "Record the material obligation ledger for the claimed turn.",
            "inputSchema": _schema(
                {
                    "turn_capability": {"type": "string"},
                    "ledger": ledger_schema,
                },
                ["turn_capability", "ledger"],
            ),
        },
        {
            "name": PROPOSITION_TOOL,
            "description": "Register one structured material legal proposition for the claimed turn.",
            "inputSchema": _schema(
                {
                    "turn_capability": {"type": "string"},
                    "proposition": canonical_proposition_schema(),
                },
                ["turn_capability", "proposition"],
            ),
        },
        {
            "name": FINALIZE_TOOL,
            "description": "Reconcile and close the claimed JDIPT turn.",
            "inputSchema": _schema(
                {"turn_capability": {"type": "string"}},
                ["turn_capability"],
            ),
        },
        {
            "name": COMMIT_PREPARED_TOOL,
            "description": (
                "Commit a fully prepared typed ledger and proposition set in one call. "
                "The server validates the bundle before claiming the epoch and keeps the "
                "turn capability internal while it records the ledger, registers every "
                "proposition, and finalizes the transaction."
            ),
            "inputSchema": _schema(
                {
                    "ledger": _prepared_ledger_schema(),
                    "propositions": {
                        "type": "array",
                        "minItems": 1,
                        "items": _prepared_proposition_schema(),
                    },
                },
                ["ledger", "propositions"],
            ),
        },
    ]
    # The prepared bundle helper remains private for compatibility diagnostics,
    # but it is intentionally not a model-facing MCP operation.  There is one
    # authoritative protocol: begin, ledger, proposition, finalize.
    return [item for item in definitions if item["name"] in TOOL_NAMES]


def _payload(transaction: Any, **extra: Any) -> dict[str, Any]:
    result = {
        "transaction_id": transaction.transaction_id,
        "epoch": transaction.epoch,
        "state": transaction.transaction_state,
        "canonical_registry_id": transaction.canonical_registry_id,
        "registered_proposition_ids": list(transaction.registered_proposition_ids),
    }
    result.update(extra)
    return result


def begin_runtime_turn(plugin_data: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    root = resolve_runtime_root(plugin_data)
    transaction = _begin_runtime_turn(root)
    return _payload(
        transaction,
        turn_capability=transaction.turn_capability,
    )


def submit_material_obligation_ledger(
    turn_capability: str,
    ledger: Mapping[str, Any],
    plugin_data: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    root = resolve_runtime_root(plugin_data)
    transaction = record_ledger(turn_capability, ledger, root)
    return _payload(
        transaction,
        ledger_digest=transaction.ledger_digest,
        ledger_count=transaction.ledger_count,
    )


def register_material_proposition(
    turn_capability: str,
    proposition: Mapping[str, Any],
    plugin_data: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    root = resolve_runtime_root(plugin_data)
    transaction = register_proposition(turn_capability, proposition, root)
    registry = RegistryService(root).read_canonical_registry(transaction.canonical_registry_id)
    if registry is None:
        raise RuntimeStateError("CANONICAL_REGISTRY_MISSING: canonical registry is missing")
    registered = next(
        item
        for item in registry.propositions
        if item.proposition_id == proposition.get("proposition_id")
    )
    status = getattr(registered.status, "value", registered.status)
    if hasattr(registered, "mandatory_render_clause"):
        mandatory_clause = registered.mandatory_render_clause
    else:
        from scripts.proposition_registry import RegistryService as _RegistryService

        integrity = _RegistryService._to_integrity_proposition(registered)
        from scripts.synthesis_integrity import render_mandatory_proposition_sentence

        mandatory_clause = render_mandatory_proposition_sentence(integrity)
    return _payload(
        transaction,
        proposition_id=registered.proposition_id,
        status=status,
        mandatory_render_clause=mandatory_clause,
    )


def finalize_runtime_turn(
    turn_capability: str,
    plugin_data: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    root = resolve_runtime_root(plugin_data)
    transaction = finalize_transaction(turn_capability, root)
    return _payload(transaction, finalized=transaction.finalized)


def commit_prepared_runtime_turn(
    ledger: Mapping[str, Any] | None,
    propositions: Any,
    plugin_data: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Run the capability lifecycle without returning custody to the caller."""

    normalized_ledger, prepared_propositions, preflight = _preflight_prepared_turn(
        ledger,
        propositions,
    )
    root = resolve_runtime_root(plugin_data)
    transaction = _begin_runtime_turn(root)
    capability = transaction.turn_capability
    if not capability:
        raise RuntimeStateError("CAPABILITY_REQUIRED: server did not retain the issued capability")

    stage = "LEDGER"
    try:
        transaction = record_ledger(capability, normalized_ledger, root)
        stage = "PROPOSITIONS"
        for proposition in prepared_propositions:
            transaction = register_proposition(capability, proposition, root)
        stage = "FINALIZE"
        transaction = finalize_transaction(capability, root)
    except Exception as exc:
        latest = load_current_transaction(root)
        state = latest.transaction_state if latest is not None else "UNKNOWN"
        transaction_id = latest.transaction_id if latest is not None else "UNKNOWN"
        epoch = latest.epoch if latest is not None else "UNKNOWN"
        failures = (
            latest.semantic_reconciliation.get("failures", [])
            if latest is not None and latest.semantic_reconciliation
            else []
        )
        failure_detail = ",".join(str(item) for item in failures)
        raise RuntimeStateError(
            f"PREPARED_TURN_FAILED: stage={stage}; state={state}; "
            f"transaction_id={transaction_id}; epoch={epoch}; "
            f"failures={failure_detail}; cause={exc}"
        ) from exc

    return _payload(
        transaction,
        finalized=transaction.finalized,
        completed_stages=["BEGIN", "LEDGER", "PROPOSITIONS", "FINALIZE"],
        semantic_preflight=preflight,
    )


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def dispatch_json_rpc(
    request: Mapping[str, Any],
    plugin_data: str | os.PathLike[str] | None = None,
) -> dict[str, Any] | None:
    if not isinstance(request, Mapping):
        return _error(None, -32600, "Invalid Request")
    request_id = request.get("id")
    method = request.get("method")
    if not isinstance(method, str):
        return _error(request_id, -32600, "Invalid Request")
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "jdipt-runtime", "version": "0.2.7"},
            },
        }
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": tool_definitions()},
        }
    if method != "tools/call":
        return _error(request_id, -32601, "Method not found")

    params = request.get("params")
    if not isinstance(params, Mapping) or params.get("name") not in TOOL_NAMES:
        return _error(request_id, -32601, "Tool not found")
    name = params["name"]
    arguments = params.get("arguments", {})
    if not isinstance(arguments, Mapping):
        return _error(request_id, -32602, "Tool arguments must be an object")
    unknown_fields = sorted(set(arguments) - TOOL_ARGUMENT_FIELDS[name])
    if unknown_fields:
        return _error(
            request_id,
            -32602,
            "Unsupported tool arguments: " + ", ".join(unknown_fields),
        )
    try:
        if name == BEGIN_TOOL:
            result = begin_runtime_turn(plugin_data)
        elif name == LEDGER_TOOL:
            result = submit_material_obligation_ledger(
                arguments.get("turn_capability"),
                arguments.get("ledger"),
                plugin_data,
            )
        elif name == PROPOSITION_TOOL:
            proposition = arguments.get("proposition")
            if not isinstance(proposition, Mapping):
                raise RuntimeStateError("PROPOSITION_REQUIRED: proposition must be an object")
            unknown_proposition = sorted(set(proposition) - PROPOSITION_FIELDS)
            if unknown_proposition:
                raise RuntimeStateError(
                    "Unsupported proposition fields: " + ", ".join(unknown_proposition)
                )
            result = register_material_proposition(
                arguments.get("turn_capability"),
                proposition,
                plugin_data,
            )
        else:
            result = finalize_runtime_turn(arguments.get("turn_capability"), plugin_data)
    except (RuntimeRootError, RuntimeStateError, TurnAnchorError, OSError, TypeError, ValueError) as exc:
        return _error(request_id, -32602, f"Invalid tool arguments: {exc}")
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "content": [
                {"type": "text", "text": json.dumps(result, ensure_ascii=False)}
            ]
        },
    }


def _configure_stdio() -> None:
    for stream in (sys.stdin, sys.stdout):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="strict")


def serve() -> None:
    _configure_stdio()
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            response = dispatch_json_rpc(request)
        except (UnicodeError, json.JSONDecodeError):
            response = _error(None, -32700, "Parse error")
        if response is not None:
            json.dump(response, sys.stdout, ensure_ascii=True, separators=(",", ":"))
            sys.stdout.write("\n")
            sys.stdout.flush()


if __name__ == "__main__":
    serve()
