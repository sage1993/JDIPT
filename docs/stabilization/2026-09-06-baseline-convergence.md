# JDIPT Baseline Convergence

**Date:** 2026-09-06  
**Scope:** Task 1 documentation/evidence only; no production files changed.  
**Canonical baseline:** R2 `refactor/legal-proposition-core-working2` at `afa4003ca700f15794dc346e8239c6dda79492e2`.  
**Legacy comparison:** R1 `fix/ansim-structural-behavior-stability` at `69dda97106cf094d93d7abb26753a76ed33ea773`.  
**Dirty comparison:** L1 is the user's existing `F:/2026-PJ/JDIPT` checkout, preserved read-only.

## Evidence and preservation

- The isolated worktree is `C:/Users/KSH/.codex/visualizations/2026/09/06/01a0769a-1b77-7a83-990e-e8f32ba44634/jdipt-correctness-stabilization`, on branch `codex-jdipt-correctness-stabilization`.
- The complete read-only command output is recorded in [`2026-09-06-baseline-git-state.txt`](2026-09-06-baseline-git-state.txt).
- The exact SHA-256/size manifest produced from the Task 1 digest procedure contains 601 entries and is recorded in [`2026-09-06-dirty-tree-manifest.json`](2026-09-06-dirty-tree-manifest.json).
- The baseline command results were successful: top-level path, branch, `HEAD`, `origin/main`, status, unstaged names, staged names, and untracked names each exited 0. Git emitted only existing permission/LF-normalization warnings while reading the dirty tree.
- The baseline `HEAD` is exactly R1 `69dda97106cf094d93d7abb26753a76ed33ea773`; `origin/main` resolved to `5e4a79feee3514bc314a19f8987b441acb4470b9`.
- The approved design and implementation-plan documents were verified byte-for-byte in place before this document was authored; their SHA-256 values are recorded in the Task 1 report. Their contents were not altered.

## Decision legend

`KEEP` means the R2 implementation owns the capability. `PORT_TO_R2` means the L1 behavior is a candidate invariant to port after review, without copying L1 files wholesale. `DELETE_AFTER_PARITY` means the R1/L1 duplicate remains only until canonical parity is proven in a later task. `UNKNOWN` is reserved for unresolved ownership that blocks registry/state/Stop work.

## Required convergence matrix

| Capability | R1 | R2 | L1 | Decision | Evidence |
|---|---|---|---|---|---|
| canonical proposition | duplicate schemas: `scripts/runtime_registry_state.py:register_material_proposition`, `scripts/synthesis_integrity.py:MaterialProposition` | `scripts/legal_proposition.py:LegalProposition` | `scripts/synthesis_runtime_state.py:MaterialProposition` plus both legacy modules | KEEP R2 | `LegalProposition`, `EvidenceRef`, and R2 proposition tests |
| evidence metadata | `MaterialProposition.source_clause`, `current_status`, and related legacy fields | `legal_proposition.py:EvidenceRef` with authority, locator, span, and temporal status | legacy `MaterialProposition` fields and `synthesis_runtime_state.MaterialProposition` | KEEP R2 | `EvidenceRef.__post_init__`, `LegalProposition.__post_init__` |
| registry writer | `runtime_registry_state.py:register_material_proposition` | `proposition_registry.py:register_material_proposition` | `synthesis_runtime_state.py:register_material_proposition` and legacy writer; MCP dispatch delegates to the legacy writer | KEEP R2 / PORT invariant | `proposition_registry._merge_state`, `proposition_registry.register_material_proposition`, L1 diff |
| exact-turn state | `synthesis_runtime_state.RuntimeTurnState` with `session_id`/`turn_id` | same exact identity in `RuntimeTurnState`, `runtime_state_path`, `load_runtime_state` | same identity plus pending/active state and registry counters | KEEP + verify | `synthesis_runtime_state.py:runtime_state_path`, `load_runtime_state`; exact-turn tests |
| registry_required | absent | absent | `RuntimeTurnState.registry_required`, `create_pending_runtime_state`, and `register_material_proposition` | PORT_TO_R2 if verified | L1 `synthesis_runtime_state.py` symbols and `validate_repo.py` markers |
| registry_completed | absent | absent | `RuntimeTurnState.registry_completed`; set during L1 registry completion | PORT_TO_R2 if verified | L1 `register_material_proposition`, `_registry_enforcement_response` |
| enforcement_count | absent | absent | `registry_enforcement_count`, `update_registry_enforcement_count`, and `stop_synthesis_gate._registry_enforcement_response` | PORT_TO_R2 if verified | L1 bounded 0-to-1 transition and Stop response |
| relation model | `synthesis_integrity.RangeExceptionRelation`, `build_range_exception_relation`, and `reconcile_range_exception_relation` | exact render slots: `RenderSlot`, `PropositionRenderContract`, `reconcile_render_contracts` | both legacy relation functions and compact relation fields in `synthesis_runtime_state.MaterialProposition` | compare semantics | R2 `proposition_rendering.py`/`proposition_reconciliation.py`; L1 relation tests |
| CI | absent | `.github/workflows/ci.yml` present | L1 dirty tree contains no R2 CI replacement | KEEP R2 | `.github/workflows/ci.yml`, `tests/test_ci_workflow.py` |
| legacy runtime_registry_state | present | removed | present and modified | DELETE_AFTER_PARITY | R2 file tree; L1 `scripts/runtime_registry_state.py` |
| legacy synthesis_integrity | present | removed | present and modified | DELETE_AFTER_PARITY | R2 file tree; L1 `scripts/synthesis_integrity.py` |

## L1 production-file ownership ledger

The following is the file-by-file classification of every L1 production/runtime file observed in the dirty tracked or untracked set. Symbols are exact top-level definitions (class methods are shown with their class-qualified name). R2 behavior is stated explicitly so later tasks can port invariants rather than replace the canonical core.

| L1 file | Exact L1 symbols | R2 behavior / comparison | Decision |
|---|---|---|---|
| `hooks/hooks.json` | `UserPromptSubmit`, `PreToolUse`, `Stop`; L1 activation and Windows command entries | R2 has the canonical hook chain and Windows-compatible runtime commands; L1 adds activation-forensic wiring and command quoting | PORT_TO_R2 |
| `scripts/activation_forensics.py` | `_append`, `_destination`, `ActivationForensicTrace.__init__`, `.emit`, `.stage`, `.failure`, `.entered` | No R2 counterpart; diagnostic trace only, not proposition/state authority | PORT_TO_R2 |
| `scripts/ansim_housing_oracle.py` | `load_ansim_oracle`, `detect_ansim_markers`, `evaluate_ansim_case`, `_validate_ansim_oracle`, `build_ansim_summary` | R2 has the same oracle symbols; L1 adds `FINAL_ACCEPTANCE` runtime pass/bypass/enforcement counters | PORT_TO_R2 |
| `scripts/hook_forensics.py` | `is_present`, `safe_trace_text`, `_append_text`, `_record_write_failure`, `_configured_destination`, `_field_evidence`, `StopForensicTrace.__init__`, `._write`, `.emit`, `.stage`, `.failure`, `.entered`, `.payload`, `capture_raw_stop_input` | No R2 counterpart; diagnostic Stop trace only | PORT_TO_R2 |
| `scripts/inject_registry_runtime.py` | `_trace_destination`, `_trace_value`, `_is_present`, `_write_trace`, `_trace_event`, `_trace_updated_input`, `_deny`, `handle_pre_tool_use`, `_configure_stdio`, `_main` | R2 owns `_deny`, `handle_pre_tool_use`, `_configure_stdio`, `_main`; L1 adds tracing around the same bridge | KEEP core; PORT trace invariant |
| `scripts/jdipt_activation.py` | `_fail_closed`, `_prompt_value`, `is_explicit_jdipt_prompt`, `handle_user_prompt_submit`, `_main` | No R2 counterpart; explicit prompt activation is an L1 runtime entry | PORT_TO_R2 |
| `scripts/jdipt_activation_forensic_entry.py` | `_prompt_value`, `_run`, `_main` | No R2 counterpart; entrypoint/forensic wrapper only | PORT_TO_R2 |
| `scripts/jdipt_runtime_mcp.py` | `tool_definitions`, `register_material_proposition`, `_error`, `dispatch_json_rpc`, `_configure_stdio`, `serve` | R2 owns the same transport symbols and delegates to `proposition_registry.register_material_proposition`; L1 delegates to the legacy writer and changes the response contract | KEEP R2; PORT verified invariant |
| `scripts/plugin_integrity.py` | `_skill_root`, `_plugin_root`, `_runtime_entries`, `build_runtime_manifest`, `compare_runtime_manifests`, `_cache_skill_candidates`, `resolve_installed_skill_root`, `main` | R2 owns the same manifest/parity symbols and canonical runtime entries; L1 adds legacy/forensic entries | KEEP R2; PORT verified parity invariant |
| `scripts/run_eval_suite.py` | `load_catalog`, `load_ansim_catalog`, `ansim_attempt_plan`, `execute_ansim_attempts`, `select_case_ids`, `_promote_answer_environment_error`, `_run_ansim_cli`, `main` | R2 owns the same suite runner symbols; L1 adds runtime-ledger capture/reporting and selected-case execution | PORT_TO_R2 |
| `scripts/runtime_acceptance.py` | `_candidate_state_files`, `_ledger_from_state`, `_latest_stop_trace`, `capture_runtime_ledger`, `_repair_result`, `classify_runtime_acceptance`, `runtime_report_from_ledger` | No R2 counterpart; acceptance evidence adapter, not runtime authority | PORT_TO_R2 |
| `scripts/runtime_registry_state.py` | `_validate_text`, `_text_arg`, `_modality_kind`, `build_mandatory_render_clause`, `register_material_proposition` | R2 replaces this writer with `proposition_registry.register_material_proposition` over `LegalProposition` and `EvidenceRef` | DELETE_AFTER_PARITY |
| `scripts/stop_synthesis_gate.py` | `_fail_closed`, `_block`, `_failure_reason`, `_draft_from_event`, `_write_stop_trace`, `_looks_like_jdipt_answer`, `_jdipt_turn_evidence`, `_repair_payload`, `_registry_enforcement_response`, `_handle_stop_event`, `_response_disposition`, `_instrument_stop_event`, `handle_stop_event`, `_main` | R2 owns the canonical `handle_stop_event` exact-turn render-coverage gate and bounded repair; L1 adds registry enforcement, soundness/relation handling, and forensic trace | PORT_TO_R2 |
| `scripts/synthesis_integrity.py` | `MaterialProposition`, `ReconciliationResult`, `DraftReconciliationResult`, `RangeExceptionRelation`, `RelationReconciliationResult`, `build_range_exception_relation`, `reconcile_range_exception_relation`, `reconcile_proposition`, `render_mandatory_proposition_sentence`, `render_mandatory_slots`, `reconcile_draft`, `repair_draft`, `render_synthesis`, plus their private helpers | R2 separates the canonical proposition model, render contracts, and reconciliation into `legal_proposition.py`, `proposition_rendering.py`, and `proposition_reconciliation.py` | DELETE_AFTER_PARITY |
| `scripts/synthesis_runtime_state.py` | `RuntimeStateError`, `MaterialProposition.__post_init__`, `.to_integrity_proposition`, `RuntimeTurnState.__post_init__`, `_validate_identifier`, `_validate_text`, `_validate_evidence`, `_plugin_data_root`, `runtime_state_path`, `_as_json`, `_from_json`, `save_runtime_state`, `load_runtime_state`, `update_repair_count`, `update_registry_enforcement_count`, `create_pending_runtime_state`, `_reconciliation_summary`, `record_reconciliation`, `record_stop_disposition`, `_text_arg`, `_action_name`, `build_mandatory_render_clause`, `register_material_proposition` | R2 owns `RuntimeStateError`, `RuntimeTurnState`, exact state path/load/save, and `update_repair_count`; L1 adds compact legacy proposition data and registry/enforcement/forensic writers | KEEP R2; PORT verified invariants |
| `scripts/validate_repo.py` | `fail`, `require_markers`, `reject_legacy_default_headings`, `read_tracked_files`, `is_placeholder`, `validate_tracked_secrets`, `main` | R2 additionally owns `_definitions` and `runtime_architecture_violations`; L1 changes architecture markers toward forensic activation and legacy runtime names | KEEP R2; PORT verified markers |

The modified L1 Skill and reference documents are policy/runtime-contract inputs, not runtime ownership authorities. They are retained in the dirty-tree manifest for preservation and require a later content review before any policy port.

## L1-only invariant rulings

| Invariant | L1 evidence | R2 status | Ruling |
|---|---|---|---|
| registry required before completion | `RuntimeTurnState.registry_required`; `create_pending_runtime_state`; `_registry_enforcement_response` | Not represented | PORT_TO_R2 after contract tests |
| registry completion is exact-turn and atomic | `register_material_proposition`; `registry_completed`; state reload/write path | R2 has exact-turn writer but no completion bit | PORT_TO_R2 after writer/concurrency review |
| one bounded registry enforcement | `update_registry_enforcement_count`; `registry_enforcement_count in {0, 1}`; Stop response | R2 bounds `repair_count`, not registry enforcement | PORT_TO_R2 |
| exact session/turn identity | `RuntimeTurnState.session_id`, `turn_id`, `runtime_state_path` | Already present in R2 | KEEP + verify |
| second reconciliation / bounded repair | L1 `record_reconciliation`, `record_stop_disposition`, and second-phase Stop path | R2 has `repair_count` and a second exact-turn Stop reconciliation | KEEP + verify parity |
| deterministic range-exception relation | `RangeExceptionRelation`, `build_range_exception_relation`, `reconcile_range_exception_relation` | R2 has generic exact render slots, not this relation model | PORT_TO_R2 after semantic comparison |
| activation and Stop forensic evidence | `ActivationForensicTrace`, `StopForensicTrace`, `capture_raw_stop_input`, `_write_stop_trace` | Not represented | PORT_TO_R2 as evidence tooling only |
| runtime/install acceptance parity | `runtime_acceptance.py`, `capture_runtime_ledger`, `runtime_report_from_ledger`, L1 oracle counters | R2 has repository/installed manifest comparison but no runtime ledger adapter | PORT_TO_R2 |
| legacy-module removal | L1 still contains both legacy modules; R2 removed them from the runtime tree | No active R2 production import found | DELETE_AFTER_PARITY; do not delete in Task 1 |

## Legacy import proof

The required isolated-worktree search was run as:

```powershell
rg -n "runtime_registry_state|synthesis_integrity" .
```

It found only historical plans/specifications and structural tests that explicitly document or assert the legacy modules' absence. No active plugin, MCP, or Stop-path import in R2 was found. Therefore no state/registry/Stop capability is `UNKNOWN`, and the Task 1 gate is not blocked.

## Task 1 boundary

This document records ownership and evidence only. It does not port L1 code, delete legacy modules, modify hooks, or change production behavior. The proposed commit boundary is:

```text
docs: define JDIPT correctness stabilization baseline
```
