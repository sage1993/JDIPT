# Task 11R-2 Hook Contract / Runtime Identity Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to execute this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct the Windows hook environment contract at the authoritative JDIPT package boundary, install it through the official plugin mechanism, and prove active module identity, PLUGIN_DATA propagation, exact-turn lifecycle, and unchanged semantic oracle across fresh acceptance runs.

**Architecture:** Keep semantic code and the ASH-06 oracle immutable. Use the candidate worktree as the authoritative package only after comparing it with the configured source and active cache. Resolve reserved `CLAUDE_PLUGIN_ROOT`/`CLAUDE_PLUGIN_DATA` at the hook boundary, retain deterministic `PLUGIN_*` compatibility only when reserved variables are absent, and fail closed for missing, empty, malformed, or invalid data. Capture every source/install/runtime boundary with SHA-256 and secret-safe JSON/JSONL evidence.

**Tech Stack:** Windows PowerShell, Codex plugin CLI, Python 3, JSON/JSONL, SHA-256, pytest, repository validators, npm/korean-law-mcp.

**Spec:** User-provided `Task 11R-2 — Hook Contract Remediation / Active Runtime Identity Closure` brief in this task.

## Global Constraints

- Preserve existing root dirty changes and work only in `F:\2026-PJ\JDIPT\.worktrees\task11-runtime-acceptance-closure`.
- Never edit or copy into `C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4`; use only the official `codex plugin marketplace`/`codex plugin add` mechanism for installation.
- Do not change LegalProposition semantics, obligation/source/render gates, Task 9/10 contracts, or the ASH-06 semantic oracle.
- Do not infer root/data from cwd, repository-relative paths, home directories, cache search, or synthetic defaults.
- Preserve fail-closed behavior for absent, empty, malformed, invalid, stale, or mismatched runtime data.
- Do not push, create a PR, merge, delete branches, or directly mutate cache/binding outside the formal install/update operation.

### Task 1: Freeze baseline and resolve source authority

**Files:**
- Create: `docs/task11-evidence/task11r2-phase-a-baseline.md`
- Create: `docs/task11-evidence/task11r2-phase-b-authoritative-source.md`

- [ ] Record repository/worktree status, branch, HEAD, top-level path, diff check, root-dirty preservation, candidate/configured/cache hashes, active binding, plugin CLI version, and current 18-mismatch set.
- [ ] Compare the candidate worktree, configured `sage1993` source, and active cache by commit ancestry and complete runtime manifest; document why the candidate is or is not authoritative.
- [ ] Stop with HOLD evidence if authority is unresolved; otherwise record the exact source path and no production mutation yet.

### Task 2: Add the failing contract tests

**Files:**
- Create: `tests/test_task11r2_hook_contract.py`
- Modify: `tests/test_registry_runtime_bridge.py` only for reserved-variable regression coverage if needed.

- [ ] Add red tests for D-01 through D-12: reserved-only mapping, deterministic bare-variable compatibility, precedence/conflict handling, absent/empty/invalid data denial, valid injection, and MCP rejection of malformed or missing `_runtime_plugin_data`.
- [ ] Add a structural test requiring all Windows hook commands to reference `CLAUDE_PLUGIN_ROOT` and forbidding unresolved `%PLUGIN_ROOT%` in production Windows commands.
- [ ] Run only the new focused tests and confirm they fail for the pre-fix reason before writing production code.

### Task 3: Apply the minimal production hook-contract fix

**Files:**
- Modify: `hooks/hooks.json`
- Create: `scripts/plugin_runtime_context.py`
- Modify: `scripts/inject_registry_runtime.py`
- Modify: `scripts/synthesis_runtime_state.py` only at the environment-resolution boundary needed by activation/Stop hooks.
- Create: `docs/task11-evidence/task11r2-phase-c-hook-contract.md`
- Create: `docs/task11-evidence/task11r2-phase-d-contract-tests.md`

- [ ] Change only Windows hook command expansion from `%PLUGIN_ROOT%` to `%CLAUDE_PLUGIN_ROOT%` while preserving command shape, stdin/stdout, timeout, and exit-code behavior.
- [ ] Resolve `CLAUDE_PLUGIN_DATA` first and `PLUGIN_DATA` only as explicit compatibility fallback when the reserved key is absent; preserve present-empty as failure and never fallback from an empty/invalid reserved value. Keep the bridge helper outside the inherited 18-file integrity manifest so the baseline set remains unchanged, and prove the helper through loaded-module identity when the active runtime is available.
- [ ] Keep `_runtime_plugin_data` authoritative and overwrite model input; do not add cwd/cache/home/default inference or semantic repair.
- [ ] Run the focused contract tests green and record exact changed-file hashes plus semantic/oracle preservation checks.

### Task 4: Run repository-local regression before installation

**Files:**
- Create: `docs/task11-evidence/task11r2-phase-e-local-regression.md`

- [ ] Run `python -m pytest -q -p no:cacheprovider`, repository validators, compileall, `npm ci`, high-severity audit, MCP help, local initialize/tools-list/tool-call smoke, and `git diff --check`.
- [ ] Do not proceed to installation unless every required local check passes; record command, exit code, and observed counts.

### Task 5: Formally update/install and prove package parity

**Files:**
- Create: `docs/task11-evidence/task11r2-phase-f-install-update.md`
- Create: `docs/task11-evidence/task11r2-phase-g-plugin-integrity.md`

- [ ] Record configured source/cache/version/hook hashes immediately before the official update.
- [ ] Register the authoritative local marketplace through the CLI marketplace mechanism if required, then run `codex plugin add jdipt@sage1993 --json`; do not edit config/cache files directly.
- [ ] Record after-state resolution and run `python scripts/plugin_integrity.py --repo-root <AUTHORITATIVE_SOURCE> --installed-root <ACTIVE_CACHE>`.
- [ ] Require exact manifest parity and classify every inherited mismatch; any unresolved active-runtime mismatch keeps the verdict HOLD.

### Task 6: Capture fresh identity, injection, exact-turn, and negative traces

**Files:**
- Create: `docs/task11-evidence/task11r2-phase-h-runtime-identity.md`
- Create: `docs/task11-evidence/task11r2-phase-i-injection-trace.jsonl`
- Create: `docs/task11-evidence/task11r2-phase-j-exact-turn.md`
- Create: `docs/task11-evidence/task11r2-phase-k-fail-closed.md`

- [ ] Start a fresh app-server/session and capture CLI/app-server version, resolved plugin/source/cache, active hook/module paths and hashes, reserved/effective root/data states, and `_runtime_plugin_data`.
- [ ] Record T0–T5 with no unresolved command token, Python module entry, nonempty data acceptance, generated runtime field, and identical MCP authority.
- [ ] Prove one same-turn `NO_STATE → PENDING → ACTIVE → SYNTHESIS/ENFORCEMENT → STOP → FINALIZED/CLOSED` chain with identical session/turn/state identifiers.
- [ ] Run negative cases for missing/invalid data, missing registry, stale turn, wrong state ID, malformed states, and absent authoritative injection; every case must fail closed.

### Task 7: Run fresh ASH-06 stability and final regression

**Files:**
- Create: `docs/task11-evidence/task11r2-phase-l-ash06-3run.md`
- Create: `docs/task11-evidence/task11r2-phase-m-ash06-10run.md`
- Create: `docs/task11r2-hook-contract-runtime-identity-closure-acceptance.md`

- [ ] Run three independent fresh ASH-06 executions only after integrity, identity, injection, exact-turn, and negative gates pass; stop at HOLD if any run fails.
- [ ] Run ten independent fresh executions only after 3/3; preserve every run, including failures, and require 10/10 with zero false-green, critical-missing, identity, exact-turn, Stop, or runtime exceptions.
- [ ] Re-run the complete required regression suite, prove Task 9/10 regression and oracle unchanged, and render the final A–K evidence report with HOLD unless every required PASS condition is observed.
