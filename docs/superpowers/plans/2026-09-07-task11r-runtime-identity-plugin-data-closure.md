# Task 11R Runtime Identity and PLUGIN_DATA Closure Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to execute this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the active `jdipt@sage1993` resolution and `PLUGIN_DATA` propagation boundary, then make only a root-cause-backed minimal fix or close the task fail-closed with HOLD.

**Architecture:** Treat the installed cache, hook command, process environment, Python module loader, and MCP child process as separate observable boundaries. Use a read-only forensic collector and a minimal probe hook before considering any production change. Compare repository candidate, package/install source, active cache, and live-loaded module identities by exact path and SHA-256.

**Tech Stack:** Windows PowerShell, `codex-cli 0.153.3`, Python 3, JSON/JSONL evidence, SHA-256, existing JDIPT hooks and MCP bridge, pytest, repository validators.

**Spec:** User-provided `JDIPT Task 11R — Active Runtime Identity / PLUGIN_DATA Injection Root-Cause Closure`.

## Global Constraints

- Preserve the Task 11 verdict as HOLD until every mandatory stop condition is cleared by fresh evidence.
- Do not modify Task 8 material obligations, Task 9 render/coverage logic, Task 10 proposition soundness, or the ASH-06 semantic oracle.
- Do not mutate the installed cache or `jdipt@sage1993` binding during baseline and root-cause investigation.
- Do not use `git reset --hard`, `git clean -fd`, stash, push, PR, or merge.
- Keep `PLUGIN_DATA` state distinct as `ABSENT`, `PRESENT_EMPTY`, and `PRESENT_NONEMPTY`.
- Do not infer live-loaded module identity from a candidate path; capture `module.__file__` and its SHA-256 in a real hook/MCP execution.
- Execute ASH-06 10-run only after fresh ASH-06 3-run is complete 3/3.

### Task 1: Freeze baseline and map all candidate/runtime locations

**Files:**
- Create: `docs/task11r-evidence/baseline.json`
- Create: `docs/task11r-evidence/baseline.txt`

- [ ] Capture `git rev-parse HEAD`, branch, root status, Task 11 worktree status, remote-tracking SHA, installed cache path, expected plugin-data path, executable path, and exact `codex --version` output.
- [ ] Record the existing Task 11 evidence as inherited evidence without rewriting it.
- [ ] Enumerate read-only plugin registry, binding, install metadata, cache, package, manifest, and hook paths under `C:\Users\KSH\.codex\plugins`.
- [ ] Hash the repository candidate and active cache for `hooks/hooks.json` plus every inherited mismatch path; record missing files explicitly.

### Task 2: Build the read-only boundary probe

**Files:**
- Create: `scripts/task11r_runtime_probe.py`
- Create: `tests/test_task11r_runtime_probe.py`

- [ ] Write tests for `ABSENT`, `PRESENT_EMPTY`, and `PRESENT_NONEMPTY`, selective environment capture, process identity, raw argv capture, and `module.__file__` hashing.
- [ ] Implement a probe that reads only named environment keys, event/tool fields, stdin JSON, executable/parent identity, command line, and selected module metadata; never dump the full environment or secret values.
- [ ] Make the probe usable directly as a hook command and as a child-process wrapper probe without invoking semantic logic.
- [ ] Run the focused probe tests before using the probe against Codex.

### Task 3: Trace resolution and hook-command contracts

**Files:**
- Create: `docs/task11r-evidence/phase-a-resolution-chain.jsonl`
- Create: `docs/task11r-evidence/phase-c-hook-contract.json`
- Create: `docs/task11r-evidence/resolution-inspection.txt`

- [ ] Capture `plugin list`, binding/provider/version/install metadata, cache-root derivation, and active `hooks.json` using the actual installed runtime.
- [ ] For each resolution step write `INPUT`, `RESOLVER`, `RULE`, `OUTPUT`, `SOURCE_OF_TRUTH`, and `EVIDENCE` from observed data only.
- [ ] Parse active PreToolUse and Stop commands, arguments, quoting, wrapper, working directory, stdin/stdout, exit-code contract, and literal versus expanded `%PLUGIN_DATA%`, `%PLUGIN_ROOT%`, and `$env:` tokens.
- [ ] Run the minimal probe through the actual app-server hook path and capture raw argv and child environment at T0–T5 where the host exposes the boundary; mark inaccessible stages as `UNOBSERVED` rather than guessing.

### Task 4: Resolve producer and identity matrix

**Files:**
- Create: `docs/task11r-evidence/phase-b-injection-trace.jsonl`
- Create: `docs/task11r-evidence/runtime-identity-matrix.json`
- Create: `docs/task11r-evidence/mismatch-resolution.json`

- [ ] Search the repository, installed cache, plugin metadata, and app-server-adjacent files for `PLUGIN_DATA`, `PLUGIN_ROOT`, `jdipt-sage1993`, and hook dispatch construction.
- [ ] Attribute each boundary to `Codex CLI`, app-server, resolver, dispatcher, manifest, hooks.json, wrapper, OS environment, or installation metadata only when a source or runtime trace connects it to the live path.
- [ ] Compare candidate source A, package/install source B, active cache C, and live-loaded module D for all required files and the 18 inherited mismatches.
- [ ] Use actual `module.__file__` and content SHA-256 for D; if no live load occurs, record `D = UNOBSERVED` and keep identity unresolved.
- [ ] Decide whether cache staleness is cause, symptom, shared installation defect, or unrelated based on boundary evidence, not correlation.

### Task 5: Controlled reproduction and root-cause decision

**Files:**
- Create: `docs/task11r-evidence/minimal-reproduction.json`
- Create: `docs/task11r-evidence/root-cause-decision.md`

- [ ] Run the minimal probe once with a known nonempty `PLUGIN_DATA`, once with the host default environment, and once through the active plugin hook path.
- [ ] Record whether the host preserves, empties, replaces, or omits the value at each observed boundary.
- [ ] Write one causal chain in the form `SOURCE → TRANSITION → DEFECT BOUNDARY → OBSERVED FAILURE`.
- [ ] Select exactly one proven root-cause class or `UNRESOLVED`; use `UNRESOLVED` when a required boundary is not observable or evidence conflicts.
- [ ] Keep production code and installed cache unchanged if the root cause is unresolved.

### Task 6: Apply only a proven minimal fix

**Files:**
- Modify: only the exact authoritative boundary identified in Task 5.
- Create: `docs/task11r-evidence/fix-provenance.json`
- Create: `tests/test_task11r_fix_regression.py`

- [ ] Write a failing regression test at the proven boundary before changing implementation.
- [ ] Capture before identity/hash and exact changed files; never overwrite a whole cache recursively.
- [ ] Apply one deterministic, fail-closed fix at the authoritative boundary, or leave production untouched when `UNRESOLVED`.
- [ ] Verify the regression test with the minimum change and confirm no semantic file changed.

### Task 7: Fresh post-fix identity, exact-turn, ASH-06, and regression gates

**Files:**
- Create or update: `docs/task11r-runtime-identity-plugin-data-closure-acceptance.md`
- Create: `docs/task11r-evidence/post-fix-identity.json`
- Create: `docs/task11r-evidence/exact-turn-runtime.jsonl`
- Create: `docs/task11r-evidence/ash06-3run.json`
- Create: `docs/task11r-evidence/ash06-10run.json`
- Create: `docs/task11r-evidence/regression-results.txt`

- [ ] In a fresh Codex session prove active source, expected source, `PLUGIN_ROOT`, nonempty expected `PLUGIN_DATA`, active hook hash, live module path/hash, and `SOURCE_MATCH`.
- [ ] Prove `NO_STATE → PENDING → ACTIVE → SYNTHESIS/ENFORCEMENT → STOP_RECONCILIATION → FINALIZED/CLOSED` with R1–R5 and same-turn identity evidence.
- [ ] Run fresh ASH-06 3-run and stop at HOLD if any run is incomplete; run 10-run only after 3/3 complete runtime passes.
- [ ] Run the required focused, full, validator, compileall, npm, MCP, plugin-integrity, and `git diff --check` checks without rewriting the semantic oracle.
- [ ] Write the required A–M acceptance document from observed evidence only; final verdict is `Task 11R: PASS` only if every stated PASS condition is met, otherwise `Task 11R: HOLD`.
