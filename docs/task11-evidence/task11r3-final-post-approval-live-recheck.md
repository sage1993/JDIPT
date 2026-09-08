# Task 11R-3 Final Post-Approval Live Recheck

Captured: 2026-09-08 (Asia/Seoul).

## Scope

This evidence records the fresh native verification after the user selected
Trust/Approve for the modified `jdipt@sage1993` hooks. It supersedes neither
the earlier failure evidence nor the semantic Task 8 acceptance requirements;
it records the resolved Windows cache/hook boundary and the remaining exact
turn gate.

## Fresh runtime observations

The official Codex 0.153.4 app-server was started against the authoritative
worktree:

```text
F:\2026-PJ\JDIPT\.worktrees\task11-runtime-acceptance-closure
```

`hooks/list` reported all three JDIPT hooks as:

```text
source = plugin
pluginId = jdipt@sage1993
enabled = true
trustStatus = trusted
warnings = []
errors = []
```

Codex expanded the Windows hook commands to the installed cache path. A
fresh native turn then produced these lifecycle events:

```text
userPromptSubmit  = completed
preToolUse        = completed
stop              = executed
```

The native MCP item contained authoritative runtime metadata:

```text
session_id = active native session id
turn_id = active native turn id
_runtime_plugin_data = C:\Users\KSH\.codex\plugins\data\jdipt-sage1993
```

This proves that the previously failing runtime-data injection boundary is
closed in the fresh approved runtime.

## Error-to-resolution record

1. Official installation initially failed with Windows `os error 5` while
   backing up the cache. The related runtime was fully exited and the official
   installer was retried. Manual cache mutation was never used.
2. The installed hook initially failed with
   `ModuleNotFoundError: No module named 'scripts.plugin_runtime_context'`.
   The hook now bootstraps its package root for absolute-path execution.
3. The Windows command form using `%CLAUDE_PLUGIN_ROOT%` did not resolve in
   the native Codex hook runner. The source now uses quote-free
   `${CLAUDE_PLUGIN_ROOT}` interpolation, which Codex expands to the active
   cache path.
4. Codex marked the changed hook hashes `modified` and skipped them. The user
   approved the plugin hooks, after which all three reported `trusted` and the
   hook lifecycle executed.
5. The original `authoritative plugin data was not injected` error disappeared.
   The MCP request received `_runtime_plugin_data` from the authoritative
   plugin-data directory.
6. The final probe was rejected with
   `ACTIVE Task 8 state requires a material obligation ledger`. This is the
   intended semantic fail-closed result for a probe without the independently
   supplied ledger; it is not a Windows installation or hook-runtime failure.

## Regression gates

```text
python scripts/validate_repo.py = PASS
python scripts/validate_authority_temporal_contract.py = PASS
python scripts/plugin_integrity.py = PASS (mismatches = [])
python -m pytest -q = 689 passed
```

## Current verdict

```text
WINDOWS_CACHE_INSTALLATION = PASS
HOOK_TRUST_AND_EXECUTION = PASS
AUTHORITATIVE_RUNTIME_DATA_INJECTION = PASS
TASK8_LEDGER_BACKED_EXACT_TURN = NOT_COMPLETE
TASK11R3 = HOLD
```

