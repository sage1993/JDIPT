# Task 11R — Active Runtime Identity / PLUGIN_DATA Injection Root-Cause Closure

Investigation date: 2026-09-07 (Asia/Seoul)

## A. Final Verdict

```text
Task 11R: HOLD
Task 11 re-evaluation: HOLD
Task 12 readiness: NOT_READY
Overall: HOLD
```

The immediate root cause is proven, but the post-fix identity and exact-turn
acceptance gates are not satisfied. No production semantic code, active cache,
binding, or ASH-06 oracle was modified.

## B. Repository State

```text
Base SHA: c6e225f1c549070581765583577c1c9aba6ceeb7
Branch: codex/task11-runtime-acceptance-closure
Final HEAD: c6e225f1c549070581765583577c1c9aba6ceeb7
Remote SHA: UNRESOLVED; no remote state was changed
Working tree: Task 11 inherited evidence plus scoped Task 11R evidence/probe untracked
root dirty preservation: YES
installed-cache modifications: NO
sage1993 binding modifications: NO
PUSH: NO
PR: NO
MERGE: NO
COMMIT: NO
```

The original root worktree's dirty changes were preserved. The active cache at
`C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4` was read only.
The inherited Task 11 record identified the app-server as `codex-cli 0.153.3`;
the fresh Task 11R executable reported `codex-cli 0.153.4`. This observed
runtime-version drift is recorded as identity evidence, not treated as the
PLUGIN_DATA root cause.

## C. Exact Root Cause

```text
ROOT_CAUSE = HOOK_COMMAND_EXPANSION
DEFECT_BOUNDARY = app-server hook dispatcher reserved-environment contract -> Windows command expansion
ROOT_CAUSE_OUTCOME = D. HOOK_BRIDGE_ROOT_CAUSE_PROVEN
```

```text
SOURCE:
  config.toml enables jdipt@sage1993 and three enabled jdipt MCP providers
→ TRANSITION:
  catalog resolves jdipt_runtime to the sage1993 installed cache
  C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4
→ DEFECT BOUNDARY:
  active hooks.json asks Windows to expand %PLUGIN_ROOT%, while the active
  app-server hook-discovery contract exposes CLAUDE_PLUGIN_ROOT and
  CLAUDE_PLUGIN_DATA; exact controlled execution leaves %PLUGIN_ROOT% literal
→ OBSERVED FAILURE:
  cmd.exe exits 2 before Python; PreToolUse is reported Failed; the MCP call
  has no _runtime_plugin_data and active jdipt_runtime_mcp.py rejects it with
  "authoritative plugin data was not injected"
```

This is proven, not `PROBABLE`, `SUSPECTED`, `LIKELY`, or `UNRESOLVED`.
The detailed causal chain and controlled probes are in
[Task 11R Phase F/H](task11-evidence/task11r-phase-f-root-cause.md) and
[Task 11R Phase G](task11-evidence/task11r-phase-g-controlled-reproduction.md).

## D. Plugin Resolution Chain

```text
CLI binding jdipt@sage1993
→ C:\Users\KSH\.codex\config.toml [plugins."jdipt@sage1993"].enabled = true
→ [marketplaces.sage1993] source_type = local
→ source = C:\Users\KSH\.codex\visualizations\2026\09\06\01a0769a-1b77-7a83-990e-e8f32ba44634\jdipt-correctness-stabilization
→ plugin catalog selects jdipt version 0.2.4
→ installed cache = C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4
→ app-server MCP catalog host_root = the same installed cache
→ hooks.json is loaded from the installed cache
```

The fresh app-server also printed duplicate `jdipt_runtime` providers for
`jdipt@task3-typed-semantic-controls` and `jdipt@task4-semantic-soundness`,
then explicitly selected `jdipt@sage1993`. The Task 11R candidate worktree was
not in this chain. See [Phase A](task11-evidence/task11r-phase-a-resolution-chain.md).

## E. PLUGIN_DATA Injection Chain

```text
app-server hook discovery
→ active commandWindows uses py -3 "%PLUGIN_ROOT%\\scripts\\...py"
→ no usable PLUGIN_ROOT expansion; literal path reaches cmd.exe
→ Python hook process is not entered
→ no PLUGIN_DATA is read or mapped to _runtime_plugin_data
→ PreToolUse fails, then MCP receives no authoritative runtime field
→ jdipt_runtime_mcp.py fails closed
```

Required-state trace:

```text
T0 = hook command selected from active cache; PLUGIN_* direct child state not exposed
T1 = effective PLUGIN_ROOT/PLUGIN_DATA contract absent for the active command
T2 = cmd.exe literal %PLUGIN_ROOT% path; exit 2
T3 = Python hook not entered; module.__file__ not observed
T4 = _runtime_plugin_data absent at MCP command construction
T5 = MCP runtime rejects the call; no fresh runtime state
```

The trace distinguishes `ABSENT`, `PRESENT_EMPTY`, and `PRESENT_NONEMPTY` in
the probe implementation. In this live run the effective required values are
`ABSENT`; the direct Python bridge test also proves that an empty or missing
`PLUGIN_DATA` is rejected rather than defaulted. Full JSONL evidence is in
[Phase B](task11-evidence/task11r-phase-b-injection-trace.jsonl); the exact
hook contract is in [Phase C](task11-evidence/task11r-phase-c-hook-contract.md).

## F. Runtime Identity Matrix

```text
A candidate = F:\2026-PJ\JDIPT\.worktrees\task11-runtime-acceptance-closure
B configured package source = C:\Users\KSH\.codex\visualizations\2026\09\06\01a0769a-1b77-7a83-990e-e8f32ba44634\jdipt-correctness-stabilization
C active cache = C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4
D live-loaded Python module = NOT_OBSERVED
```

The active hook path and hash are proven:

```text
ACTIVE_HOOK = C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4\hooks\hooks.json
ACTIVE_HOOK_SHA256 = 840509260e9ab3f5a69a01a37302eb361c9c0a637c0d863777c25d96d30cbf81
ACTIVE_MODULE = NOT_PROVEN; the hook failed before module telemetry
PLUGIN_DATA_EXPECTED = C:\Users\KSH\.codex\plugins\data\jdipt-sage1993
```

The core-file A/B/C hash matrix is in
[Phase E](task11-evidence/task11r-phase-e-runtime-identity-matrix.md). The
observed result remains:

```text
ACTIVE_RUNTIME_IDENTITY = IDENTITY_UNRESOLVED
SOURCE_RELATION = SOURCE_MISMATCH
```

## G. 18 Mismatch Resolution

All 18 are inherited and remain `STILL_BLOCKING`; none was silently promoted
to resolved and none was changed by Task 11R.

| Inherited mismatch | Final status |
| --- | --- |
| `SKILL.md` digest mismatch | STILL_BLOCKING |
| `plugin/hooks/hooks.json` digest mismatch | STILL_BLOCKING |
| `plugin/scripts/jdipt_activation.py` digest mismatch | STILL_BLOCKING |
| `plugin/scripts/jdipt_runtime_mcp.py` digest mismatch | STILL_BLOCKING |
| `plugin/scripts/legal_proposition.py` digest mismatch | STILL_BLOCKING |
| `plugin/scripts/material_obligation_ingress.py` missing | STILL_BLOCKING |
| `plugin/scripts/material_obligation_ledger.py` missing | STILL_BLOCKING |
| `plugin/scripts/proposition_obligation_closure.py` missing | STILL_BLOCKING |
| `plugin/scripts/proposition_registry.py` digest mismatch | STILL_BLOCKING |
| `plugin/scripts/proposition_relations.py` digest mismatch | STILL_BLOCKING |
| `plugin/scripts/proposition_render_coverage.py` missing | STILL_BLOCKING |
| `plugin/scripts/proposition_rendering.py` digest mismatch | STILL_BLOCKING |
| `plugin/scripts/proposition_soundness.py` missing | STILL_BLOCKING |
| `plugin/scripts/proposition_source_closure.py` missing | STILL_BLOCKING |
| `plugin/scripts/stop_synthesis_gate.py` digest mismatch | STILL_BLOCKING |
| `plugin/scripts/synthesis_runtime_state.py` digest mismatch | STILL_BLOCKING |
| `references/legal-issue-mapping.md` digest mismatch | STILL_BLOCKING |
| `references/source-policy.md` digest mismatch | STILL_BLOCKING |

```text
BASE_MISMATCH_COUNT = 18
FINAL_MISMATCH_COUNT = 18
TASK11R_INTRODUCED_MISMATCH_COUNT = 0
PLUGIN_INTEGRITY_ACTIVE_RUNTIME = FAIL
```

The mismatch set is an independent cache/source parity blocker. The immediate
`PLUGIN_DATA` failure is the proven hook expansion boundary, not an unproven
claim that cache staleness itself generated the missing variable.

## H. Exact-Turn Runtime Evidence

```text
PRETOOL = FAIL; fresh app-server reported PreToolUse Failed
PENDING = NOT_OBSERVED
ACTIVE = NOT_OBSERVED
SYNTHESIS = NOT_RUN
STOP = FAIL; fresh app-server reported Stop Failed
SAME_STATE = NOT_PROVEN
FAIL_CLOSED = PASS for the MCP missing-authority rejection
```

The required lifecycle `NO_STATE → PENDING → ACTIVE → SYNTHESIS/ENFORCEMENT →
STOP → FINALIZED/CLOSED` was not observed. The exact-turn gate therefore does
not pass.

## I. ASH-06 3-Run

```text
3_RUN = 0/3 COMPLETE_RUNTIME_PASS; HOLD
PROCESS = NOT_ACCEPTED ASH-06 3-run
RUNTIME_IDENTITY = 0/3
ENFORCEMENT = 0/3
STOP_RECONCILIATION = 0/3
SEMANTIC_ORACLE = NOT_RUN AS A LIVE RUNTIME GATE
FALSE_GREEN = 0 observed
CRITICAL_MISSING = 0 observed in completed semantic checks
RUNTIME_EXCEPTION = 0
```

ASH-06 was not re-entered because identity and exact-turn prerequisites failed.

## J. ASH-06 10-Run

```text
10_RUN = NOT_RUN
reason = 3-run prerequisite did not pass
```

## K. Regression Verification

| Command | Result |
| --- | --- |
| `python -m pytest -q -p no:cacheprovider tests/test_task11r_runtime_probe.py` | PASS — 4 passed |
| `python -m pytest -q -p no:cacheprovider` | PASS — 670 passed |
| `python scripts/validate_repo.py` | PASS |
| `python scripts/validate_authority_temporal_contract.py` | PASS |
| `python -m compileall -q scripts tests` | PASS when rerun with required ACL elevation; initial unelevated run hit existing `__pycache__` ACL |
| `python scripts/plugin_integrity.py --repo-root . --installed-root <active cache>` | FAIL — inherited exact 18 mismatches |
| `npm ci` | PASS — 202 packages added, 203 audited, 0 vulnerabilities |
| `npm audit --audit-level=high` | PASS — 0 vulnerabilities |
| `npm run mcp -- --help` | PASS — exit 0 |
| local `jdipt_runtime_mcp.py` initialize/tools-list JSON-RPC smoke | PASS — server `jdipt-runtime` 0.2.4 and expected tool |
| active MCP live smoke | HOLD — fresh active call failed `authoritative plugin data was not injected` |
| `git diff --check` | PASS |

Task 9/Task 10 and broader Task 1R–8 results are preserved from the inherited
Task 11 acceptance evidence; Task 11R added no semantic implementation change.

## L. Semantic Contract Preservation

```text
Task9 modified: NO
Task10 weakened: NO
ASH06 oracle modified: NO
AUTO_REPAIR: NO
AUTO_INJECTION: NO
SEMANTIC_REWRITE: NO
ORACLE_RELAXATION: NO
FAIL_OPEN: NO
```

## M. Task 12 Boundary

Task 12 cannot be entered.

```text
ROOT_CAUSE = PROVEN, but closure gates remain unmet
ACTIVE_RUNTIME_IDENTITY = IDENTITY_UNRESOLVED
SOURCE_RELATION = SOURCE_MISMATCH
PLUGIN_DATA = not PRESENT_NONEMPTY at the active hook boundary
LOADED_MODULE_IDENTITY = NOT_PROVEN
EXACT_TURN_CONTINUITY = NOT_PASS
ASH06_3RUN = 0/3
ASH06_10RUN = NOT_RUN
RELEASE_READY = FALSE
```

The correct next remediation is an authorized package hook-contract fix and
formal single-source install/update, followed by fresh active identity and
T0–T5 evidence. Blind cache copying, semantic changes, and oracle relaxation
remain prohibited.

## Final Report

```text
A. Final Verdict

TASK11R = HOLD
TASK11_REEVALUATION = HOLD
TASK12_READINESS = NOT_READY
OVERALL = HOLD

B. Exact Root Cause

ROOT_CAUSE = HOOK_COMMAND_EXPANSION
DEFECT_BOUNDARY = app-server hook dispatcher reserved-environment contract -> Windows command expansion
ROOT_CAUSE_OUTCOME = D. HOOK_BRIDGE_ROOT_CAUSE_PROVEN
PROOF = active command uses %PLUGIN_ROOT%; app-server hook contract exposes CLAUDE_PLUGIN_*; exact command fails before Python; live MCP rejects missing _runtime_plugin_data

C. Runtime Identity

ACTIVE_SOURCE = C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4
EXPECTED_SOURCE = F:\2026-PJ\JDIPT\.worktrees\task11-runtime-acceptance-closure
SOURCE_RELATION = SOURCE_MISMATCH

PLUGIN_DATA = C:\Users\KSH\.codex\plugins\data\jdipt-sage1993 (expected root; not delivered to active hook)
ACTIVE_HOOK = PROVEN path/hash at active cache
ACTIVE_MODULE = NOT_PROVEN

D. Plugin Integrity

BASE_MISMATCH_COUNT = 18
FINAL_MISMATCH_COUNT = 18
TASK11R_INTRODUCED_MISMATCH_COUNT = 0

E. Exact-Turn Runtime

PRETOOL = FAIL
PENDING = NOT_OBSERVED
ACTIVE = NOT_OBSERVED
SYNTHESIS = NOT_RUN
STOP = FAIL
SAME_STATE = NOT_PROVEN
FAIL_CLOSED = PASS

F. ASH-06

3_RUN = 0/3 COMPLETE_RUNTIME_PASS
10_RUN = NOT_RUN
SEMANTIC_FALSE_GREEN = 0 observed
CRITICAL_MISSING = 0 observed in completed semantic checks

G. Verification

FULL_PYTEST = PASS (670 passed)
VALIDATE_REPO = PASS
AUTHORITY_TEMPORAL = PASS
COMPILEALL = PASS (elevated rerun)
PLUGIN_INTEGRITY = FAIL (inherited 18 mismatches)
NPM_CI = PASS
NPM_AUDIT = PASS
MCP_LOCAL = PASS
MCP_ACTIVE = HOLD / FAIL-CLOSED
DIFF_CHECK = PASS

H. Preservation

TASK9_MODIFIED = NO
TASK10_WEAKENED = NO
ASH06_ORACLE_MODIFIED = NO
ROOT_DIRTY_PRESERVED = YES
SAGE1993_BINDING_MODIFIED = NO

I. Git

COMMIT = NO
PUSH = NO
PR = NO
MERGE = NO
```
