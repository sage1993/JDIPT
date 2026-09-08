# Task 11R-3 Windows Cache-Lock / Atomic Installation / Active Runtime Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove or conservatively hold the complete Windows cache-lock, formal installation, source/cache parity, fresh-runtime identity, PLUGIN_DATA, exact-turn, fail-closed, ASH-06, and final-regression chain without mutating the cache directly or weakening semantic/oracle contracts.

**Architecture:** Operate only from the existing authoritative worktree `F:\2026-PJ\JDIPT\.worktrees\task11-runtime-acceptance-closure`. Capture read-only host/cache evidence first, establish a specific lock owner before any shutdown, use only the official `codex plugin` mechanism for installation, and gate every later phase on the prior phase's evidence. If any mandatory stop condition occurs, preserve evidence and publish HOLD.

**Tech Stack:** Windows PowerShell, Codex CLI plugin marketplace commands, Python 3, SHA-256 manifests, pytest, npm, repository validators, Restart Manager/host process inspection.

**Spec:** User-provided Task 11R-3 specification in `C:\Users\KSH\.codex\attachments\6b003aef-ac9a-4a96-8a94-c5901d025340\pasted-text.txt`.

## Global Constraints

- `AUTHORITATIVE_SOURCE = F:\2026-PJ\JDIPT\.worktrees\task11-runtime-acceptance-closure`.
- Preserve all pre-existing root and authoritative-worktree dirty changes; do not reset, checkout, or delete unrelated files.
- `ROOT_CAUSE = HOOK_COMMAND_EXPANSION`; `TASK11R3_BLOCKER_CLASS = WINDOWS_PLUGIN_CACHE_LIFECYCLE`.
- Do not directly copy, patch, restore, delete, or synthesize files in `C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4`.
- Do not kill all `codex.exe`, `python.exe`, or `node.exe`; terminate only a proven related process tree, and only after graceful shutdown fails.
- Do not change semantic production code, Task 9/10 contracts, ASH-06 oracle logic, expected-result rules, or version strings to hide parity failures.
- Do not push, create a PR, merge, or delete branches; do not create a commit unless the user separately requests it.
- A PASS requires every required gate in the specification; otherwise final verdict is `TASK11R3 = HOLD`, `TASK11_REEVALUATION = HOLD`, `TASK12_READINESS = NOT_READY`, `OVERALL = HOLD`.

---

### Task 1: Freeze baseline and initialize evidence

**Files:**
- Create: `docs/task11-evidence/task11r3-phase-a-baseline.md`
- Create: `docs/superpowers/plans/2026-09-07-task11r3-windows-cache-lock-runtime-closure.md`
- Preserve: all existing dirty files and prior Task 11/11R/11R-2 evidence

**Interfaces:**
- Consumes: current git state, authoritative worktree identity, active cache path.
- Produces: immutable baseline SHA/branch/root/dirty-state record and explicit preservation decisions.

- [ ] **Step 1: Record repository identity.** Run `git status --short`, `git branch --show-current`, `git rev-parse HEAD`, `git rev-parse --show-toplevel`, and `git diff --check` in both the root and authoritative worktree; preserve command output and exit codes.
- [ ] **Step 2: Record the fixed paths.** Capture `AUTHORITATIVE_SOURCE`, `CACHE_PATH`, plugin version, and the prior Task 11R-2 baseline mismatch count without editing either source or cache.
- [ ] **Step 3: Write Phase A evidence.** State `ROOT_DIRTY_PRESERVED = YES`, `CACHE_DIRECTLY_MODIFIED = NO`, `TASK9_MODIFIED = NO`, `TASK10_WEAKENED = NO`, and `ASH06_ORACLE_MODIFIED = NO` only where the captured baseline supports them.
- [ ] **Step 4: Re-run `git diff --check`.** Stop with HOLD if the baseline cannot be captured or unrelated dirty state cannot be preserved.

### Task 2: Prove process identity and cache lock ownership

**Files:**
- Create: `docs/task11-evidence/task11r3-phase-b-process-forensics.md`
- Create: `docs/task11-evidence/task11r3-phase-c-lock-owner.md`

**Interfaces:**
- Consumes: PID `60504`, active cache path, Codex process metadata, Windows handle-owner evidence.
- Produces: `PROCESS_IDENTITY`, process relation classification, `LOCK_OWNER`, and a safe shutdown decision.

- [ ] **Step 1: Inspect PID 60504 without terminating it.** Capture process name, executable path, start time, session ID, command line/parent data when permitted, and any child tree; classify each process as `RELATED_CONFIRMED`, `RELATED_PROBABLE`, `UNRELATED`, or `UNRESOLVED`.
- [ ] **Step 2: Query the exact cache files with Windows Restart Manager or an already-installed equivalent.** Record affected PIDs, process names, executable paths, and the exact registered cache paths; treat absence of direct handle evidence as `PROBABLE` or `UNRESOLVED`, never as `PROVEN`.
- [ ] **Step 3: Correlate the installer WinError 5/32 evidence with the exact active cache and app-server process.** Preserve the prior R-2 failure as historical evidence and distinguish current observations from inherited observations.
- [ ] **Step 4: Write Phase B/C evidence.** Do not proceed to termination or installation while the only classification is `UNRESOLVED`.

### Task 3: Gracefully stop only the related runtime and verify lock release

**Files:**
- Create: `docs/task11-evidence/task11r3-phase-d-runtime-shutdown.md`
- Create: `docs/task11-evidence/task11r3-phase-f-lock-release.md`

**Interfaces:**
- Consumes: Phase B/C relation and lock-owner evidence.
- Produces: `RELATED_RUNTIME_STOPPED`, shutdown outcome, post-shutdown process tree, and `CACHE_LOCK_RELEASED`.

- [ ] **Step 1: Attempt graceful shutdown of the related verification session/app-server/MCP children in documented order.** Record exact command, timestamp, result, and exit state; do not terminate unrelated processes.
- [ ] **Step 2: Re-inspect the specific process tree.** If graceful shutdown fails, force-terminate only the related confirmed/probable tree after recording the reason and exact PIDs; otherwise leave unrelated and unresolved processes untouched.
- [ ] **Step 3: Probe the cache lock without changing cache contents.** Use Restart Manager plus non-destructive file access/rename-lock evidence and record before/after results; require `CACHE_LOCK_RELEASED = YES`.
- [ ] **Step 4: Stop immediately with HOLD if a related lock remains, the owner is unresolved, or any unrelated process was terminated.** Do not invoke the installer in that case.

### Task 4: Capture pre-install cache state and run the official installer

**Files:**
- Create: `docs/task11-evidence/task11r3-phase-g-preinstall-cache.md`
- Create: `docs/task11-evidence/task11r3-phase-h-official-install.md`

**Interfaces:**
- Consumes: released lock, proven authoritative source, formal marketplace binding.
- Produces: official installer exit/result, generated cache path/version, and a traceable install invocation.

- [ ] **Step 1: Inventory the cache read-only.** Record existence, file count, byte count, required-file states, and pre-install classification (`EMPTY`, `PARTIAL`, `COMPLETE_BUT_STALE`, or `COMPLETE_UNKNOWN`).
- [ ] **Step 2: Verify marketplace resolution.** Run the official CLI listing commands and record `jdipt@sage1993`, configured source, installed version, and current cache path; do not edit config files directly.
- [ ] **Step 3: Invoke the supported official command.** Use `codex plugin add jdipt@sage1993 --json` only after Tasks 2–3 pass, capturing stdout, stderr, start/end time, and exit code.
- [ ] **Step 4: Treat exit code 0 as process success only.** Do not start a runtime until completeness, inventory parity, and cryptographic parity all pass.

### Task 5: Prove completeness, inventory parity, integrity, and install-state coherence

**Files:**
- Create: `docs/task11-evidence/task11r3-phase-i-cache-completeness.md`
- Create: `docs/task11-evidence/task11r3-phase-j-inventory-parity.md`
- Create: `docs/task11-evidence/task11r3-phase-k-content-parity.md`
- Create: `docs/task11-evidence/task11r3-phase-l-install-state.md`

**Interfaces:**
- Consumes: generated official cache and source manifest.
- Produces: `CACHE_COMPLETE`, missing/zero-byte counts, source/cache inventory comparison, SHA-256 parity, and coherent install metadata/pointer evidence.

- [ ] **Step 1: Check every required production artifact.** Require present, non-empty, and readable for plugin manifest, hook manifest, `SKILL.md`, all Task 8–11 scripts, and required references.
- [ ] **Step 2: Compare full package inventories.** Record source count, cache count, missing files, unexpected files, and any formally documented generated metadata; do not silently ignore unexpected files.
- [ ] **Step 3: Run `python scripts/plugin_integrity.py --repo-root F:\\2026-PJ\\JDIPT\\.worktrees\\task11-runtime-acceptance-closure --installed-root C:\\Users\\KSH\\.codex\\plugins\\cache\\sage1993\\jdipt\\0.2.4`.** Preserve all mismatches and require final mismatch count zero.
- [ ] **Step 4: Compare installed metadata, version directory, active pointer, and marketplace catalog.** Require `INSTALL_STATE_DIVERGENCE = 0`; stop with HOLD for any divergence or partial cache.

### Task 6: Start a fresh runtime and prove active identity, stale-reference absence, and T0–T5

**Files:**
- Create: `docs/task11-evidence/task11r3-phase-m-active-runtime.md`
- Create: `docs/task11-evidence/task11r3-phase-n-active-identity.md`
- Create: `docs/task11-evidence/task11r3-phase-o-stale-runtime.md`
- Create: `docs/task11-evidence/task11r3-phase-p-plugin-data-trace.jsonl`

**Interfaces:**
- Consumes: complete/parity-passing cache and stopped old runtime.
- Produces: fresh app-server/session identity, active hook/module path/hash, stale-reference counts, and authoritative PLUGIN_DATA T0–T5 trace.

- [ ] **Step 1: Launch a new app-server/session through the supported CLI flow.** Record new PID/start time, CLI/app-server versions, and prove it differs from PID `60504`; do not reuse the old session or MCP process.
- [ ] **Step 2: Capture the full resolution chain.** Record binding, configured source, authoritative source, generated cache, active hooks path/hash, loaded Python module path/hash, plugin-data path, registry/state paths, and source/cache/live-content relation.
- [ ] **Step 3: Search active command lines, hook telemetry, and module paths for old/deleted cache references.** Require `OLD_CACHE_REFERENCE_COUNT = 0` and `DELETED_PATH_REFERENCE_COUNT = 0`.
- [ ] **Step 4: Trace T0–T5.** Preserve `ABSENT`, `PRESENT_EMPTY`, and `PRESENT_NONEMPTY` states; require non-empty host-reserved `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA`, successful Windows expansion, Python module entry/hash, effective `_runtime_plugin_data`, and equal hook/MCP authoritative data.
- [ ] **Step 5: Stop with HOLD if any active identity or PLUGIN_DATA field is unproven.** Do not enter ASH-06.

### Task 7: Validate exact-turn lifecycle and negative fail-closed behavior

**Files:**
- Create: `docs/task11-evidence/task11r3-phase-q-exact-turn.md`
- Create: `docs/task11-evidence/task11r3-phase-r-fail-closed.md`

**Interfaces:**
- Consumes: fresh runtime identity and T0–T5 trace.
- Produces: exact-turn state linkage and negative matrix results.

- [ ] **Step 1: Run one positive logical turn.** Observe `NO_STATE → PENDING → ACTIVE → SYNTHESIS/ENFORCEMENT → STOP RECONCILIATION → FINALIZED/CLOSED`, preserving turn/session/state identities and requiring same-state linkage.
- [ ] **Step 2: Run the required negative cases.** Exercise missing/empty/invalid plugin data, missing/malformed runtime data, missing registry, malformed PENDING/ACTIVE, stale turn, wrong state ID, and wrong runtime source; record `ALLOW = NO` and `FAIL_CLOSED = PASS` per case.
- [ ] **Step 3: Stop with HOLD if positive lifecycle or negative matrix is incomplete.** Do not claim ASH-06 readiness from local-only tests.

### Task 8: Execute ASH-06 gates, idempotency, and final regression

**Files:**
- Create: `docs/task11-evidence/task11r3-phase-s-ash06-3run.md`
- Create: `docs/task11-evidence/task11r3-phase-t-ash06-10run.md`
- Create: `docs/task11-evidence/task11r3-phase-u-installer-idempotency.md`
- Create: `docs/task11-evidence/task11r3-phase-v-final-regression.md`
- Create: `docs/task11r3-windows-cache-lock-runtime-closure-acceptance.md`

**Interfaces:**
- Consumes: all prior PASS gates and preserved ASH-06 oracle.
- Produces: 3-run and 10-run acceptance records, supported idempotency result, final regression results, and final verdict.

- [ ] **Step 1: Run three fresh independent ASH-06 runs.** Preserve every run including failures; require `COMPLETE_RUNTIME_PASS = 3/3` before starting the 10-run gate.
- [ ] **Step 2: Run ten consecutive fresh acceptance runs.** Record all semantic/oracle/runtime/identity/plugin-data/exact-turn/stop/stale-cache counters; do not discard or replace a failed run.
- [ ] **Step 3: Run one supported idempotency invocation only after 10/10.** Require cache completeness and parity to remain PASS; mark `NOT_APPLICABLE` only with a documented product-contract reason.
- [ ] **Step 4: Run the final commands exactly as specified:** `python -m pytest -q -p no:cacheprovider`, `python scripts/validate_repo.py`, `python scripts/validate_authority_temporal_contract.py`, `python -m compileall -q scripts tests`, `python scripts/plugin_integrity.py ...`, `npm ci`, `npm audit --audit-level=high`, `npm run mcp -- --help`, active MCP smoke, and `git diff --check`.
- [ ] **Step 5: Write the final report.** Emit PASS only if every specification criterion is satisfied; otherwise record the first mandatory stop condition and publish HOLD without semantic/oracle relaxation.
