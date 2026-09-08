# Task 11 Exact Runtime Acceptance and Release Authority Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove or fail closed on the active JDIPT runtime identity, exact-turn lifecycle, ASH-06 live enforcement, and deterministic release authority without changing the Task 9 coverage algorithm or Task 10 semantic soundness contract.

**Architecture:** Add a read-only runtime-forensics/evidence layer that consumes authoritative hook payloads, exact-turn state, installed bundle hashes, and fresh ASH-06 observations. Extend the existing release manifest authority so missing, stale, malformed, ambiguous, or non-live evidence produces HOLD. Keep production semantic modules and the ASH-06 oracle unchanged; any runtime fix must be a minimal, root-cause-backed lifecycle fix with a regression test.

**Tech Stack:** Python 3, pytest, JSONL/JSON evidence, existing JDIPT hook scripts, `release_manifest.py`, `plugin_integrity.py`, npm/MCP smoke commands, PowerShell on Windows.

**Spec:** User-provided Task 11 — Exact Runtime Acceptance & Release Authority Closure.

## Global Constraints

- `TASK9_COVERAGE_ALGORITHM_MODIFIED = NO`.
- `TASK10_SOUNDNESS_CONTRACT_WEAKENED = NO`.
- `ASH06_ORACLE_MODIFIED = NO`.
- `AUTO_REPAIR = NO`, `SEMANTIC_INJECTION = NO`, `FREEFORM_REWRITE_REPAIR = NO`, `ORACLE_RELAXATION = NO`, and `FAIL_OPEN_FALLBACK = NO`.
- Preserve the dirty root worktree and the Task 10 worktree; work only in `F:\2026-PJ\JDIPT\.worktrees\task11-runtime-acceptance-closure`.
- Do not mutate the installed plugin/cache, `sage1993` binding, push, create a PR, or merge.
- Use the actual observed URLs and paths in evidence; do not invent source URLs or runtime identity.
- The final release decision must be deterministic and fail closed when any required evidence is missing, stale, malformed, ambiguous, or unresolved.

---

### Task 1: Freeze the Task 10 baseline and collect active-runtime identity evidence

**Files:**
- Create: `docs/task11-evidence/phase-a-runtime-identity.json`
- Create: `docs/task11-evidence/phase-a-runtime-identity.txt`
- Test: `tests/test_task11_runtime_acceptance.py`

**Interfaces:**
- Consumes: repository `HEAD`, `.codex-plugin/plugin.json`, `hooks/hooks.json`, `scripts/plugin_integrity.py`, installed/cache candidate roots, `codex --version`, and observed runtime data paths.
- Produces: a schema-validated identity record with explicit `SOURCE_MATCH`, `SOURCE_MISMATCH`, or `IDENTITY_UNRESOLVED` status and an exact mismatch classification for all inherited 18 mismatches.

- [ ] **Step 1: Inspect and record the clean Task 10 base identity.**

Run:

```powershell
git rev-parse HEAD
git status --short
git show c6e225f1c549070581765583577c1c9aba6ceeb7:.codex-plugin/plugin.json
codex --version
```

Expected: `HEAD` is `c6e225f1c549070581765583577c1c9aba6ceeb7`, no tracked changes in the new worktree, plugin id `jdipt`, and a version string captured verbatim.

- [ ] **Step 2: Write the failing evidence-shape test.**

```python
def test_phase_a_identity_is_explicit_and_fail_closed():
    evidence = load_task11_identity_evidence()
    assert evidence["status"] in {"SOURCE_MATCH", "SOURCE_MISMATCH", "IDENTITY_UNRESOLVED"}
    assert evidence["status"] != "SOURCE_MATCH" or evidence["source_path"] == evidence["resolved_source_path"]
    assert all(item["classification"] in {
        "EXPECTED_STALE_INSTALL",
        "ACTIVE_RUNTIME_RELEVANT",
        "ACTIVE_RUNTIME_IRRELEVANT",
        "UNKNOWN",
    } for item in evidence["plugin_integrity"]["mismatches"])
```

- [ ] **Step 3: Implement only the evidence serializer/validator.**

The serializer must preserve raw observed paths and SHA-256 digests, distinguish the repository candidate from the active cache candidate, and never infer `SOURCE_MATCH` from a path name alone. It must report `IDENTITY_UNRESOLVED` when the executable, plugin root, hook root, module path, registry path, or plugin-data path cannot be tied to one observed runtime event.

- [ ] **Step 4: Run the focused test and record the result.**

Run: `python -m pytest -q tests/test_task11_runtime_acceptance.py -k identity`

Expected: the identity record is accepted only with an explicit status and the inherited mismatch set is classified without deletion or cache mutation.

- [ ] **Step 5: Capture the inherited mismatch baseline.**

Run: `python scripts/plugin_integrity.py --repo-root . --installed-root <observed-installed-root>`

Expected: the exact mismatch list and count are copied into `docs/task11-evidence/phase-a-runtime-identity.json`; no mismatch is silently discarded as merely pre-existing.

### Task 2: Add exact-turn lifecycle evidence and invariant validation

**Files:**
- Create: `scripts/runtime_acceptance.py`
- Create: `tests/test_task11_runtime_acceptance.py`
- Modify: `scripts/jdipt_activation.py` only if a proven lifecycle defect requires it
- Modify: `scripts/inject_registry_runtime.py` only if a proven lifecycle defect requires it
- Modify: `scripts/stop_synthesis_gate.py` only if a proven lifecycle defect requires it
- Create: `docs/task11-evidence/exact-turn-lifecycle.jsonl`

**Interfaces:**
- Consumes: hook events and authoritative runtime-state snapshots keyed by `(session_id, turn_id)`.
- Produces: lifecycle records for `NO_STATE → PENDING → ACTIVE → SYNTHESIS/ENFORCEMENT → STOP RECONCILIATION → FINALIZED/CLOSED`, plus R1–R5 invariant results.

- [ ] **Step 1: Write tests for R1–R5 before changing production code.**

Cover missing identity, missing registry, malformed/stale registry, cross-turn state reuse, atomic activation, same-state Stop reads, and ambiguous identity. Each invalid case must return a fail-closed result and never be converted into a successful enforcement result.

- [ ] **Step 2: Run the focused tests and record the initial result.**

Run: `python -m pytest -q tests/test_task11_runtime_acceptance.py -k 'turn or invariant or lifecycle'`

Expected: any test exposing a defect is recorded as RED with the root-cause category from `ACTIVE_SOURCE_IDENTITY`, `PLUGIN_DATA_INJECTION`, `TURN_IDENTITY`, `REGISTRY_LIFECYCLE`, `ACTIVATION_TRANSITION`, `STOP_STATE_BINDING`, `HOOK_INPUT_CONTRACT`, `HOOK_OUTPUT_CONTRACT`, `INSTALLED_CACHE`, `OTHER`, or `UNRESOLVED`.

- [ ] **Step 3: Implement the smallest evidence/invariant change.**

Use the existing `RegistryService` and exact-turn persistence as the authority. Do not add a second registry, a state fallback, semantic repair, a document-global keyword check, or an ASH-06-specific production path. If the root cause is unresolved, do not patch production; retain HOLD evidence.

- [ ] **Step 4: Re-run focused tests and verify the red/green boundary.**

Run: `python -m pytest -q tests/test_task11_runtime_acceptance.py -k 'turn or invariant or lifecycle'`

Expected: valid transitions pass, all ambiguity/missing-authority cases fail closed, and no Task 9/10 semantic file changes are present.

### Task 3: Implement deterministic release authority inputs and ASH-06 run evidence

**Files:**
- Modify: `scripts/release_manifest.py`
- Modify: `scripts/run_release_gate.py` only to consume the new evidence schema
- Create: `config/task11-runtime-acceptance.schema.json`
- Create: `tests/test_task11_release_authority.py`
- Create: `docs/task11-evidence/ash06-3run.json`
- Create: `docs/task11-evidence/ash06-10run.json`

**Interfaces:**
- Consumes: static validation, regression results, active identity, turn continuity, ASH-06 3-run/10-run matrices, semantic soundness, plugin classification, and MCP runtime evidence.
- Produces: one deterministic `RELEASE_READY` decision; missing/stale/malformed/ambiguous evidence always yields `FALSE`/HOLD.

- [ ] **Step 1: Write release-authority tests.**

Assert that a complete all-PASS evidence set returns PASS; each missing required section, stale snapshot, wrong run count, cross-turn reuse, false-green count, identity mismatch, unresolved root cause, or plugin mismatch classification returns HOLD.

- [ ] **Step 2: Run tests against the unimplemented gate.**

Run: `python -m pytest -q tests/test_task11_release_authority.py`

Expected: the new deterministic contract fails until the authority consumes every required input.

- [ ] **Step 3: Implement the schema and authority evaluation.**

Require exactly 3/3 for the first gate and exactly 10/10 for the stability gate. Require zero critical proposition missing, invalid semantic promotion, false green, cross-turn reuse, runtime exception, and unresolved root-cause patch markers. Do not let subsystem PASS flags override a missing or failed required section.

- [ ] **Step 4: Run the focused release tests.**

Run: `python -m pytest -q tests/test_task11_release_authority.py`

Expected: all deterministic gate tests pass and only a complete, fresh, internally consistent evidence manifest can return PASS.

### Task 4: Execute fresh live ASH-06 gates and MCP runtime smoke

**Files:**
- Create: `docs/task11-evidence/ash06-live-commands.txt`
- Create: `docs/task11-evidence/mcp-runtime.json`
- Create: `docs/task11-evidence/runtime-traces/` JSONL/JSON files only

**Interfaces:**
- Consumes: the actual installed runtime identity and host hook traces; uses the Task 10 oracle without source modification.
- Produces: separate fresh-run evidence for ASH-06 3-run and, only if 3/3 passes, 10-run stability; MCP smoke result with command, exit code, and observed response.

- [ ] **Step 1: Run three fresh explicit ASH-06 sessions.**

For each run capture plugin/runtime identity, PreToolUse, pending/activation, synthesis, Stop reconciliation, enforcement, semantic oracle, critical missing, invalid promotion, and runtime exception fields. Do not reuse an old trace or state file.

- [ ] **Step 2: Stop immediately on a 3-run failure.**

If any run is not a complete PASS, record `ASH06_3RUN != PASS`, do not execute the 10-run gate as an acceptance claim, and set the final release authority to HOLD.

- [ ] **Step 3: Run ten fresh sessions only after 3/3 PASS.**

Require 10/10 process, identity, enforcement, Stop reconciliation, and semantic oracle, with zero critical missing, false green, cross-turn reuse, and runtime exception.

- [ ] **Step 4: Run MCP smoke against the same runtime identity.**

Run `npm run mcp -- --help` and the repository’s local JSON-RPC smoke command, capturing exit status and response identity. A different or unresolved source path is HOLD, not PASS.

### Task 5: Run full regressions and write the acceptance document

**Files:**
- Create: `docs/task11-runtime-acceptance-closure-acceptance.md`
- Create: `docs/task11-evidence/regression-commands.txt`
- Create: `docs/task11-evidence/release-authority.json`

**Interfaces:**
- Consumes: all prior evidence and fresh verification output.
- Produces: the required Task 11 acceptance document with Final Verdict, repository state, active identity, 18-mismatch classification, exact-turn lifecycle, 3-run/10-run matrices, semantic preservation, all regression commands/results, scope/preservation, and Task 12 boundary.

- [ ] **Step 1: Run required verification commands.**

Run, in the Task 11 worktree:

```text
Task10 focused
Task9 regression
Task1R–8 regression
broader integration
full pytest
compileall
validate_repo
authority-temporal validator
plugin integrity
npm ci
npm audit
MCP smoke
git diff --check
```

Record exact commands, exit codes, counts, and any inherited plugin-integrity mismatch without converting it to PASS.

- [ ] **Step 2: Evaluate the deterministic release authority.**

Run the authority against the assembled evidence. If any mandatory stop condition is present, write `Task 11: HOLD`, `Task 12 readiness: NOT READY`, `Overall: HOLD`; never write PASS based on partial evidence.

- [ ] **Step 3: Write the acceptance document from observed evidence only.**

Include `BASE_SHA: c6e225f1c549070581765583577c1c9aba6ceeb7`, the actual Task 11 branch/HEAD, remote SHA, working-tree state, root-dirty preservation, unchanged `sage1993` binding, and explicit `PUSH/PR/MERGE: NO`.

- [ ] **Step 4: Perform final rendering and scope gates.**

Verify the acceptance document contains all required sections and that Task 9 coverage files, Task 10 soundness files, and ASH-06 oracle have no semantic changes. Run `git diff --check`, compileall, validators, focused tests, and full pytest again if any implementation file changed after the first verification.

- [ ] **Step 5: Commit only scoped Task 11 work if all required evidence is present.**

Do not commit a false PASS. If live evidence remains unresolved or fails, commit only the fail-closed acceptance/evidence and report HOLD; do not push, open a PR, or merge.

---

## Self-review checklist

- [ ] Phase A distinguishes `SOURCE_MATCH`, `SOURCE_MISMATCH`, and `IDENTITY_UNRESOLVED` without guessing.
- [ ] All 18 inherited plugin mismatches have a classification and active-runtime relevance assessment.
- [ ] R1–R5 exact-turn invariants are evidenced from actual hook/state records.
- [ ] ASH-06 3-run gate is a prerequisite for the 10-run gate.
- [ ] Semantic coverage and soundness remain independent and both are required.
- [ ] Release authority consumes every mandatory evidence category and fails closed.
- [ ] Required regressions and package/MCP checks are recorded.
- [ ] Root dirty changes, Task 10 worktree changes, installed cache, and binding are preserved.
- [ ] No Task 9 algorithm, Task 10 contract, or ASH-06 oracle change is included.
