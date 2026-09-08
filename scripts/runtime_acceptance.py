"""Fail-closed runtime acceptance and release-authority primitives."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.plugin_integrity import build_runtime_manifest


LIFECYCLE_STAGES = (
    "NO_STATE",
    "PENDING",
    "ACTIVE",
    "SYNTHESIS/ENFORCEMENT",
    "STOP RECONCILIATION",
    "FINALIZED/CLOSED",
)

REQUIRED_RELEASE_EVIDENCE = (
    "static_validation",
    "regression",
    "active_runtime_identity",
    "turn_continuity",
    "ash06_3run",
    "ash06_10run",
    "semantic_soundness",
    "plugin_integrity_classification",
    "mcp_runtime",
)

ACTIVE_RUNTIME_LOGICAL_FILES = frozenset(
    {
        "SKILL.md",
        "references/legal-issue-mapping.md",
        "references/source-policy.md",
        "plugin/hooks/hooks.json",
        "plugin/.mcp.json",
        "plugin/scripts/jdipt_activation.py",
        "plugin/scripts/inject_registry_runtime.py",
        "plugin/scripts/jdipt_runtime_mcp.py",
        "plugin/scripts/legal_proposition.py",
        "plugin/scripts/material_obligation_ingress.py",
        "plugin/scripts/material_obligation_ledger.py",
        "plugin/scripts/proposition_obligation_closure.py",
        "plugin/scripts/proposition_registry.py",
        "plugin/scripts/proposition_relations.py",
        "plugin/scripts/proposition_render_coverage.py",
        "plugin/scripts/proposition_rendering.py",
        "plugin/scripts/proposition_source_closure.py",
        "plugin/scripts/proposition_soundness.py",
        "plugin/scripts/synthesis_runtime_state.py",
        "plugin/scripts/stop_synthesis_gate.py",
    }
)

PLUGIN_MISMATCH_CLASSIFICATIONS = frozenset(
    {
        "EXPECTED_STALE_INSTALL",
        "ACTIVE_RUNTIME_RELEVANT",
        "ACTIVE_RUNTIME_IRRELEVANT",
        "UNKNOWN",
    }
)


def _append_once(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def validate_exact_turn_lifecycle(
    events: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate one observed hook/state lifecycle without repairing evidence."""

    violations: list[str] = []
    if not isinstance(events, Sequence) or isinstance(events, (str, bytes)) or not events:
        return {
            "status": "FAIL_CLOSED",
            "violations": ["MISSING_LIFECYCLE_EVIDENCE"],
            "same_state_stop": False,
        }

    observed_stages = [event.get("stage") for event in events if isinstance(event, Mapping)]
    if tuple(observed_stages) != LIFECYCLE_STAGES:
        _append_once(violations, "INVALID_LIFECYCLE_ORDER")

    authoritative_identity: tuple[Any, Any] | None = None
    active_state: Any = None
    state_by_turn: dict[tuple[Any, Any], Any] = {}
    same_state_stop = False

    for event in events:
        if not isinstance(event, Mapping):
            _append_once(violations, "MALFORMED_LIFECYCLE_EVENT")
            continue
        stage = event.get("stage")
        session_id = event.get("session_id")
        turn_id = event.get("turn_id")
        state_identity = event.get("state_identity")

        if stage != "NO_STATE" and not isinstance(session_id, str):
            _append_once(violations, "MISSING_SESSION_IDENTITY")
        if stage != "NO_STATE" and not isinstance(turn_id, str):
            _append_once(violations, "MISSING_TURN_IDENTITY")
        if stage not in {"NO_STATE"} and not state_identity:
            _append_once(violations, "MISSING_AUTHORITATIVE_STATE")

        if stage != "NO_STATE" and isinstance(session_id, str) and isinstance(turn_id, str):
            identity = (session_id, turn_id)
            if authoritative_identity is None:
                authoritative_identity = identity
            elif identity != authoritative_identity:
                _append_once(violations, "CROSS_TURN_IDENTITY")
            if state_identity:
                prior = state_by_turn.setdefault(identity, state_identity)
                if prior != state_identity:
                    _append_once(violations, "CROSS_TURN_STATE_REUSE")

        if event.get("activation_state") == "PENDING" and event.get("jdipt_active") is True:
            _append_once(violations, "NON_ATOMIC_ACTIVATION")

        if stage == "ACTIVE":
            active_state = state_identity
        if stage == "STOP RECONCILIATION":
            same_state_stop = bool(active_state and state_identity == active_state)
            if not same_state_stop:
                _append_once(violations, "STOP_STATE_MISMATCH")

    return {
        "status": "PASS" if not violations else "FAIL_CLOSED",
        "violations": violations,
        "same_state_stop": same_state_stop,
    }


def evaluate_release_authority(evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Consume every Task 11 evidence category; no partial PASS can override HOLD."""

    reasons: list[str] = []
    if not isinstance(evidence, Mapping):
        return {
            "verdict": "HOLD",
            "release_ready": False,
            "reasons": ["MALFORMED_RELEASE_EVIDENCE"],
        }

    for name in REQUIRED_RELEASE_EVIDENCE:
        section = evidence.get(name)
        if not isinstance(section, Mapping):
            _append_once(reasons, f"MISSING_{name.upper()}")
            continue
        if section.get("stale") is True or section.get("fresh") is False:
            _append_once(reasons, f"STALE_{name.upper()}")
        if section.get("ambiguous") is True:
            _append_once(reasons, f"AMBIGUOUS_{name.upper()}")
        if section.get("malformed") is True:
            _append_once(reasons, f"MALFORMED_{name.upper()}")

    if evidence.get("unresolved_root_cause_with_patch") is True:
        _append_once(reasons, "UNRESOLVED_ROOT_CAUSE_WITH_PATCH")

    for name in ("static_validation", "regression", "mcp_runtime"):
        section = evidence.get(name)
        if isinstance(section, Mapping) and section.get("status") != "PASS":
            _append_once(reasons, f"{name.upper()}_NOT_PASS")

    active = evidence.get("active_runtime_identity")
    if isinstance(active, Mapping):
        if active.get("status") != "PROVEN":
            _append_once(reasons, "ACTIVE_RUNTIME_IDENTITY_NOT_PROVEN")
        if active.get("source_relation") != "SOURCE_MATCH":
            _append_once(reasons, "ACTIVE_RUNTIME_SOURCE_MISMATCH")

    continuity = evidence.get("turn_continuity")
    if isinstance(continuity, Mapping):
        if continuity.get("status") != "PASS":
            _append_once(reasons, "TURN_CONTINUITY_NOT_PASS")
        if continuity.get("cross_turn_state_reuse") != 0:
            _append_once(reasons, "CROSS_TURN_STATE_REUSE")

    for name, expected_count in (("ash06_3run", 3), ("ash06_10run", 10)):
        section = evidence.get(name)
        if not isinstance(section, Mapping):
            continue
        runs = section.get("runs")
        if not isinstance(runs, list) or len(runs) != expected_count or any(run != "PASS" for run in runs):
            _append_once(reasons, f"ASH06_{expected_count}RUN_NOT_{expected_count}_OF_{expected_count}")
        if section.get("status") != "PASS":
            _append_once(reasons, f"ASH06_{expected_count}RUN_NOT_PASS")

    semantic = evidence.get("semantic_soundness")
    if isinstance(semantic, Mapping):
        if semantic.get("coverage") is not True or semantic.get("sound") is not True:
            _append_once(reasons, "SEMANTIC_SOUNDNESS_NOT_PASS")
        if semantic.get("false_green") != 0:
            _append_once(reasons, "SEMANTIC_FALSE_GREEN")
        if semantic.get("critical_missing") != 0:
            _append_once(reasons, "CRITICAL_PROPOSITION_MISSING")
        if semantic.get("invalid_promotion") != 0:
            _append_once(reasons, "INVALID_SEMANTIC_PROMOTION")

    plugin = evidence.get("plugin_integrity_classification")
    if isinstance(plugin, Mapping):
        introduced = plugin.get("introduced_mismatches")
        if not isinstance(introduced, int) or isinstance(introduced, bool):
            _append_once(reasons, "MALFORMED_PLUGIN_INTEGRITY_CLASSIFICATION")
        elif introduced != 0:
            _append_once(reasons, "TASK11_INTRODUCED_PLUGIN_MISMATCH")
        mismatches = plugin.get("mismatches")
        if not isinstance(mismatches, list):
            _append_once(reasons, "MALFORMED_PLUGIN_INTEGRITY_CLASSIFICATION")
        elif any(
            not isinstance(item, Mapping)
            or item.get("classification") not in PLUGIN_MISMATCH_CLASSIFICATIONS
            for item in mismatches
        ):
            _append_once(reasons, "MALFORMED_PLUGIN_INTEGRITY_CLASSIFICATION")

    return {
        "verdict": "PASS" if not reasons else "HOLD",
        "release_ready": not reasons,
        "reasons": reasons,
    }


def sha256_file(path: Path) -> str:
    """Hash one observed file without accepting a missing path as evidence."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _resolved(path: Path | None) -> Path | None:
    if path is None:
        return None
    try:
        return path.expanduser().resolve(strict=False)
    except (OSError, RuntimeError, TypeError):
        return None


def _plugin_metadata(root: Path | None) -> dict[str, Any]:
    if root is None:
        return {}
    path = root / ".codex-plugin" / "plugin.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def build_runtime_identity(
    *,
    executable_path: Path | None,
    codex_version: str | None,
    candidate_root: Path | None,
    active_root: Path | None,
    plugin_data: Path | None,
    hook_path: Path | None,
    registry_path: Path | None,
    runtime_state_path: Path | None,
    loaded_module_paths: Sequence[Path] = (),
) -> dict[str, Any]:
    """Build identity evidence; absence is represented, never inferred away."""

    candidate = _resolved(candidate_root)
    active = _resolved(active_root)
    executable = _resolved(executable_path)
    data = _resolved(plugin_data)
    hook = _resolved(hook_path)
    registry = _resolved(registry_path)
    runtime_state = _resolved(runtime_state_path)
    modules = [_resolved(path) for path in loaded_module_paths]

    candidate_manifest = build_runtime_manifest(candidate) if candidate is not None and candidate.is_dir() else {}
    active_manifest = build_runtime_manifest(active) if active is not None and active.is_dir() else {}
    candidate_digest = hashlib.sha256(canonical_json(candidate_manifest).encode("utf-8")).hexdigest() if candidate_manifest else None
    active_digest = hashlib.sha256(canonical_json(active_manifest).encode("utf-8")).hexdigest() if active_manifest else None

    if candidate is not None and active is not None and candidate_digest == active_digest and candidate == active:
        source_relation = "SOURCE_MATCH"
    elif candidate is not None and active is not None:
        source_relation = "SOURCE_MISMATCH"
    else:
        source_relation = "IDENTITY_UNRESOLVED"

    module_records = []
    loaded_modules_observed = bool(modules) and all(path is not None and path.is_file() for path in modules)
    for path in modules:
        module_records.append(
            {
                "path": str(path) if path is not None else None,
                "sha256": sha256_file(path) if path is not None and path.is_file() else None,
            }
        )

    required_observed = all(
        (
            executable is not None and executable.is_file(),
            isinstance(codex_version, str) and bool(codex_version.strip()),
            active is not None and (active / ".codex-plugin" / "plugin.json").is_file(),
            data is not None and data.is_dir(),
            hook is not None and hook.is_file(),
            registry is not None and registry.exists(),
            runtime_state is not None and runtime_state.exists(),
            loaded_modules_observed,
        )
    )
    identity_status = "PROVEN" if required_observed else "IDENTITY_UNRESOLVED"
    active_metadata = _plugin_metadata(active)
    return {
        "identity_status": identity_status,
        "source_relation": source_relation,
        "executable": {
            "path": str(executable) if executable is not None else None,
            "version": codex_version,
        },
        "plugin": {
            "id": active_metadata.get("name"),
            "version": active_metadata.get("version"),
            "active_root": str(active) if active is not None else None,
            "candidate_root": str(candidate) if candidate is not None else None,
            "candidate_manifest_sha256": candidate_digest,
            "active_manifest_sha256": active_digest,
        },
        "hooks": {"path": str(hook) if hook is not None else None},
        "plugin_data": str(data) if data is not None else None,
        "registry_path": str(registry) if registry is not None else None,
        "runtime_state_path": str(runtime_state) if runtime_state is not None else None,
        "loaded_modules": module_records,
    }


def classify_plugin_mismatches(
    mismatches: Sequence[str],
    *,
    installed_root: Path | None,
    active_root: Path | None,
) -> list[dict[str, Any]]:
    """Classify inherited integrity mismatches without dropping any item."""

    installed = _resolved(installed_root)
    active = _resolved(active_root)
    active_is_installed = installed is not None and active is not None and installed == active
    classified: list[dict[str, Any]] = []
    for mismatch in mismatches:
        logical = mismatch.split(": ", 1)[-1] if ": " in mismatch else ""
        relevant = logical in ACTIVE_RUNTIME_LOGICAL_FILES
        if active is None or installed is None:
            classification = "UNKNOWN"
            active_relevant = False
        elif not active_is_installed:
            classification = "EXPECTED_STALE_INSTALL"
            active_relevant = False
        elif relevant:
            classification = "ACTIVE_RUNTIME_RELEVANT"
            active_relevant = True
        else:
            classification = "ACTIVE_RUNTIME_IRRELEVANT"
            active_relevant = False
        classified.append(
            {
                "mismatch": mismatch,
                "classification": classification,
                "active_runtime_relevant": active_relevant,
            }
        )
    return classified
