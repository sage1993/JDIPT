# Task 11R-3 Windows Cache-Lock / Atomic Installation / Active Runtime Closure Acceptance

Captured: 2026-09-08 (Asia/Seoul).

## Latest post-approval re-evaluation

The earlier sections preserve the pre-fix and pre-approval evidence. The
following is the latest fresh verification after the user approved
`jdipt@sage1993`'s modified hooks in Codex Desktop.

```text
OFFICIAL_INSTALL = PASS
CACHE_COMPLETENESS = PASS
SOURCE_CACHE_PARITY = PASS
FINAL_MISMATCH_COUNT = 0
HOOK_TRUST_STATUS = trusted for all 3 hooks
FRESH_APP_SERVER = YES
USER_PROMPT_SUBMIT = completed
PRE_TOOL_USE = completed
STOP_HOOK = executed and failed closed on missing Task 8 ledger
RUNTIME_PLUGIN_DATA_IN_MCP_INPUT = PRESENT_NONEMPTY
FULL_PYTEST = 689 passed
VALIDATE_REPO = PASS
AUTHORITY_TEMPORAL = PASS
PLUGIN_INTEGRITY = PASS
```

The original live error, `Invalid tool arguments: authoritative plugin data
was not injected`, no longer occurs. The fresh native MCP item contained the
authoritative session/turn values and:

```text
_runtime_plugin_data = C:\Users\KSH\.codex\plugins\data\jdipt-sage1993
```

The remaining native probe error is a separate semantic gate:

```text
Invalid tool arguments: ACTIVE Task 8 state requires a material obligation ledger
```

This is expected fail-closed behavior for a probe that did not provide the
independently supplied Task 8 ledger. It is not a cache, installation, hook
trust, command expansion, or runtime-data injection failure. Therefore the
overall Task 11R-3 verdict remains `HOLD` until a valid ledger-backed exact
turn is exercised; no further reinstall or reboot is required for the resolved
Windows cache/hook failure.

## Error and resolution record

| Observed error | Root cause | Resolution | Current result |
| --- | --- | --- | --- |
| `failed to back up plugin cache entry: Access is denied (os error 5)` | Running Codex/app-server family retained the versioned plugin cache during official installation. | Fully exit the related runtime, then use only the official `codex plugin add jdipt@sage1993 --json` installer. No cache copying or manual patching was used. | Official installation succeeded. |
| `ModuleNotFoundError: No module named 'scripts.plugin_runtime_context'` | A hook launched by absolute path did not bootstrap the repository package root. | Added direct-execution path bootstrap to `scripts/inject_registry_runtime.py`. | Source/cache integrity and focused tests pass. |
| Native Windows hook command failed with exit code 1 | `%CLAUDE_PLUGIN_ROOT%` was left for shell expansion instead of using Codex hook command interpolation. | Changed all Windows hook commands to quote-free `py -3 ${CLAUDE_PLUGIN_ROOT}\\scripts\\<hook>.py`. | `hooks/list` resolves commands to the installed cache path; all hooks complete. |
| `trustStatus=modified`; hook lifecycle absent | Codex persisted the previous hook hash and skipped untrusted modified hooks. | User approved `jdipt@sage1993` with Trust/Approve in Codex Desktop. | All 3 hooks report `trustStatus=trusted`. |
| `authoritative plugin data was not injected` | The installed cache was stale/pre-fix or the hook was not trusted/executed. | Official reinstall, fresh app-server, corrected command interpolation, and hook approval. | `_runtime_plugin_data` is present in the native MCP input. |
| `ACTIVE Task 8 state requires a material obligation ledger` | The acceptance probe activated Task 8 but supplied no independent ledger. | Preserve the semantic fail-closed gate; run the next acceptance probe with a valid ledger fixture. | Expected remaining HOLD condition; unrelated to Windows cache/hook closure. |


## A. Final Verdict

```text
TASK11R3 = HOLD
TASK11_REEVALUATION = HOLD
TASK12_READINESS = NOT_READY
OVERALL = HOLD
```

Mandatory stop conditions reached:

```text
S01 = LOCK_OWNER UNRESOLVED
S04 = CLEARED by official 0.153.4 install exit 0
S10 = INSTALL_STATE_DIVERGENCE UNRESOLVED
S12 = ACTIVE_HOOK post-install NOT_PROVEN
S13 = ACTIVE_MODULE NOT_PROVEN
S14 = ACTIVE_RUNTIME_IDENTITY != PROVEN
S17 = _runtime_plugin_data not present in live MCP input
S18 = T0_T5 != PASS
S19 = SAME_STATE != PROVEN
S20 = NEGATIVE_GATE != PASS
S21 = ASH06_3RUN != 3/3
S22 = ASH06_10RUN != 10/10
S24 = latest official install failed before applying the hook bootstrap fix
```

## B. Repository

```text
BASE_SHA = c6e225f1c549070581765583577c1c9aba6ceeb7
BRANCH = codex/task11-runtime-acceptance-closure
FINAL_HEAD = c6e225f1c549070581765583577c1c9aba6ceeb7
WORKTREE = F:\2026-PJ\JDIPT\.worktrees\task11-runtime-acceptance-closure
ROOT_DIRTY_PRESERVED = YES
```

## C. Process / Lock Forensics

```text
ORIGINAL_APP_SERVER_PID = 60504
PROCESS_IDENTITY = codex.exe; C:\Users\KSH\.codex\plugins\.plugin-appserver\codex.exe; app-server; parent 69196
LOCK_OWNER = UNRESOLVED
LOCK_OWNER_PID = 51412 (RELATED_PROBABLE; direct handle owner not proven)
LOCK_OWNER_EVIDENCE = official backup returned Access denied while app-server PID 51412 had related jdipt_runtime MCP children; direct handle query remained unavailable
GRACEFUL_SHUTDOWN = ATTEMPTED for PID 51412 via CloseMainWindow; returned false and process remained
FORCE_TERMINATION = NO
UNRELATED_PROCESS_TERMINATED = NO
CACHE_LOCK_BEFORE = NO_CURRENT_OWNER_REPORTED
CACHE_LOCK_AFTER = NO_CURRENT_OWNER_REPORTED
CACHE_LOCK_RELEASED = YES for current registered-file probe
```

## D. Formal Installation

```text
AUTHORITATIVE_SOURCE = F:\2026-PJ\JDIPT\.worktrees\task11-runtime-acceptance-closure
INSTALL_METHOD = codex plugin add jdipt@sage1993 --json
INSTALL_EXIT_CODE = 0 on earlier official standalone codex-cli 0.153.4 retry; latest post-hook-fix attempt failed with Access denied (os error 5) during cache backup
INSTALL_PROCESS_RESULT = HOLD for latest source revision; latest official installer did not complete
INSTALLED_VERSION = 0.2.4 (catalog/cache observation)
GENERATED_CACHE = C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4
CACHE_DIRECTLY_MODIFIED = NO
```

## E. Cache Completeness / Inventory

```text
CACHE_STATE_BEFORE = COMPLETE_UNKNOWN
CACHE_STATE_AFTER = STRUCTURALLY_COMPLETE_UNKNOWN_PROVENANCE
SOURCE_FILE_COUNT = not comparable as a full-tree count; scoped runtime manifest used
CACHE_FILE_COUNT = 8868
REQUIRED_FILE_MISSING_COUNT = 0
ZERO_BYTE_REQUIRED_FILE_COUNT = 0
MATERIAL_MISSING_FILE_COUNT = 0
MATERIAL_UNEXPECTED_FILE_COUNT = 0
FULL_INVENTORY_MISSING = none in the scoped installed package comparison
CACHE_COMPLETE = YES for post-reinstall snapshot
PARTIAL_CACHE = NO
```

## F. Integrity

```text
BASE_MISMATCH_COUNT = 18
FINAL_MISMATCH_COUNT = 0 in scoped runtime manifest
TASK11R3_INTRODUCED_MISMATCH_COUNT = 0
PLUGIN_INTEGRITY = PASS for current scoped read-only comparison
RESOLVED_BY_FORMAL_INSTALL = PASS on official 0.153.4 retry
```

## G. Installation State Coherence

```text
INSTALL_METADATA_VERSION = 0.2.4
CACHE_VERSION = 0.2.4
ACTIVE_POINTER_VERSION = NOT_OBSERVED
INSTALL_STATE_DIVERGENCE = UNRESOLVED
```

## H. Active Runtime Identity

```text
OLD_APP_SERVER_REUSED = YES for the post-hook-fix attempt; current PID 51412 was not restarted after the repository hook fix
NEW_APP_SERVER_PID = NOT_CREATED after the latest source revision
CLI_VERSION = codex-cli 0.153.4 official standalone binary
APP_SERVER_VERSION = codex-cli 0.153.4
CONFIGURED_SOURCE = F:\2026-PJ\JDIPT\.worktrees\task11-runtime-acceptance-closure
ACTIVE_CACHE = C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4
ACTIVE_HOOK = NOT_PROVEN for the post-hook-fix cache; installed hook directly reproduced ModuleNotFoundError before the source fix
ACTIVE_HOOK_SHA256 = d0fe41e6b75094f562e88ba363f591709b5f625facffcb5fee414c4fcbb7274b
ACTIVE_MODULE = NOT_PROVEN
ACTIVE_MODULE_SHA256 = NOT_AVAILABLE
SOURCE_RELATION = RUNTIME_MANIFEST_MATCH_OBSERVED; LIVE_IDENTITY_NOT_PROVEN
ACTIVE_RUNTIME_IDENTITY = NOT_PROVEN
OLD_CACHE_REFERENCE_COUNT = NOT_OBSERVED
DELETED_PATH_REFERENCE_COUNT = NOT_OBSERVED
```

## I. PLUGIN_DATA

```text
CLAUDE_PLUGIN_ROOT = NOT_RUN
CLAUDE_PLUGIN_DATA = NOT_RUN
PLUGIN_ROOT = NOT_RUN
PLUGIN_DATA = NOT_PROVEN
_runtime_plugin_data = NOT_PRESENT_IN_LIVE_MCP_INPUT
T0 = FAIL / active hook not proven
T1 = NOT_PROVEN
T2 = NOT_PROVEN
T3 = NOT_PROVEN
T4 = FAIL / no injection observed
T5 = FAIL / MCP rejected missing injection
```

## J. Exact-Turn / Fail-Closed

```text
PRETOOL = FAIL / actual MCP call made without injected runtime data
PENDING = NOT_OBSERVED
ACTIVE = NOT_OBSERVED
SYNTHESIS = NOT_RUN
STOP = NOT_OBSERVED
FINAL_STATE = NOT_OBSERVED
SAME_STATE = NOT_PROVEN
FAIL_CLOSED = OBSERVED for missing injection; fresh active runtime not proven
NEGATIVE_GATE = NOT_RUN
```

## K. ASH-06

```text
3_RUN = NOT_RUN
10_RUN = NOT_RUN
SEMANTIC_FALSE_GREEN = NOT_RUN
CRITICAL_MISSING = NOT_RUN
RUNTIME_EXCEPTION = NOT_RUN
IDENTITY_FAILURE = NOT_RUN
PLUGIN_DATA_FAILURE = NOT_RUN
EXACT_TURN_FAILURE = NOT_RUN
STOP_FAILURE = NOT_RUN
STALE_CACHE_REFERENCE = NOT_RUN
```

## L. Final Regression

```text
FULL_PYTEST = PASS — 688 passed before the hook bootstrap fix; focused post-fix contract tests = 19 passed
VALIDATE_REPO = PASS
AUTHORITY_TEMPORAL = PASS
COMPILEALL = PASS
PLUGIN_INTEGRITY = PASS — scoped runtime manifest
NPM_CI = PASS
NPM_AUDIT = PASS
MCP_LOCAL = PASS
MCP_ACTIVE = FAIL — valid actual call rejected missing authoritative injection from the pre-fix installed hook
DIFF_CHECK = PASS
```

## M. Preservation

```text
TASK9_MODIFIED = NO
TASK10_WEAKENED = NO
ASH06_ORACLE_MODIFIED = NO
ROOT_DIRTY_PRESERVED = YES
CACHE_DIRECTLY_MODIFIED = NO
UNRELATED_PROCESS_TERMINATED = NO
```

## N. Git

```text
COMMIT = NO
PUSH = NO
PR = NO
MERGE = NO
```

The next safe action is to fully exit the Codex desktop process so the current
app-server and related runtime children release the cache, then rerun the
official installer and start a fresh runtime. This task did not repair ACLs,
kill the current app-server, copy cache files, relax semantics, or claim a
positive active acceptance from the pre-fix installed hook. The repository hook
bootstrap fix is covered by the focused tests but is not yet present in the
official cache because the latest official installation was blocked by the
Windows cache lifecycle.

## O. Post-reboot retry addendum

After a full Windows reboot, Codex was relaunched and a new app-server was
observed at PID 9184 (started 2026-09-08 07:35:43 +09:00), with three related
`scripts/jdipt_runtime_mcp.py` child processes. The official standalone
`codex-cli 0.153.4` installer was then retried against the authoritative
source, but again returned `failed to back up plugin cache entry: Access is
denied (os error 5)`. The app-server/runtime family was still active at the
time of the attempt. No cache content was manually changed, and the verdict
remains HOLD pending a fully exited desktop process followed by official
installation and fresh-runtime acceptance.

## P. Active-host diagnostic and command-line correction

The official app-server `hooks/list` diagnostic was run against the
authoritative worktree after the user's live MCP failure. It reported the
JDIPT PreToolUse hook as `enabled=true`, `trustStatus=trusted`, and
`source=plugin`, but its resolved command was still the cached form:

```text
py -3 "%CLAUDE_PLUGIN_ROOT%\\scripts\\inject_registry_runtime.py"
```

The authoritative source was then corrected so all three Windows hook
commands use the quote-free form required by Codex's Windows `cmd /C`
invocation wrapper:

```text
py -3 %CLAUDE_PLUGIN_ROOT%\\scripts\\<hook>.py
```

The hook contract now has a regression assertion forbidding embedded command
quotes, and the focused runtime/bridge suite passes with 26 tests. The cache
has not been manually edited; the official cache remains the previous copy
until the next successful official installation. `TASK11R3 = HOLD` remains
the correct verdict pending that installation and a fresh Desktop MCP call.

## Q. Isolated official-install verification

To separate package installation from the live Desktop cache lock, an
isolated temporary `CODEX_HOME` was used with the same authoritative local
marketplace. The official `codex-cli 0.153.4 plugin add jdipt@sage1993 --json`
completed successfully, the installed `hooks/hooks.json` contained the new
quote-free Windows commands, and the scoped `plugin_integrity.py` comparison
returned `INSTALLATION_INTEGRITY: PASS`.

The isolated home had no login credentials, so its native `codex exec` probe
stopped at upstream `401 Unauthorized` before a model-generated MCP call. No
positive live injection result is claimed from that run. The real Desktop
cache remains unchanged and `TASK11R3 = HOLD` remains in force until the
official installation is performed against the user's active home and a
fresh native runtime call completes.
