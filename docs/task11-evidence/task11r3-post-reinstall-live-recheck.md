# Task 11R-3 Post-Reinstall Live Recheck

Captured: 2026-09-08 (Asia/Seoul).

## Post-restart and hook bootstrap finding

After the user restarted Codex, the stale `jdipt@task3-typed-semantic-controls`
binding was removed successfully through the official command. The current
Codex app-server is:

```text
PID = 51412
PATH = C:\Users\KSH\.codex\plugins\.plugin-appserver\codex.exe
START = 2026-09-08 00:10:43 +09:00
RELATED_CHILD = python.exe scripts/jdipt_runtime_mcp.py
```

The current configuration contains only `jdipt@sage1993`; the task3 cache
directory remains as an empty directory and was not manually deleted.

The first valid live calls were initially obscured by an invalid probe using
fields outside the MCP schema. A subsequent valid call using only
`proposition_id`, `status`, `materiality`, and `subject` still failed with:

```text
Invalid tool arguments: authoritative plugin data was not injected
```

Direct execution of the installed hook by its absolute Windows path reproduced
the underlying defect before any cache mutation:

```text
ModuleNotFoundError: No module named 'scripts.plugin_runtime_context'
```

The repository hook was corrected to bootstrap its package root when executed
as an absolute script path. The source-level direct-execution regression test
now passes (`19 passed`). The installed cache still contains the pre-fix hook,
because the next official installer attempt was deliberately used to apply the
fix and failed during cache backup with `Access is denied (os error 5)` while
the current Codex app-server was running. No cache file was copied, patched,
restored, or deleted manually.

## Formal installation and cache

The reinstalled standalone Codex binary was used for the official install:

```text
CLI = C:\Users\KSH\.codex\packages\standalone\releases\0.153.4-x86_64-pc-windows-msvc\bin\codex.exe
CLI_VERSION = codex-cli 0.153.4
INSTALL_COMMAND = codex plugin add jdipt@sage1993 --json
INSTALL_EXIT_CODE = 0
GENERATED_CACHE = C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4
```

The second official invocation also exited 0 after the cache was observed
empty by a later read. The resulting cache was then inspected without direct
copy, patch, restore, or version manipulation:

```text
CACHE_FILE_COUNT = 8868
CACHE_TOTAL_BYTES = 582029307
REQUIRED_FILE_MISSING_COUNT = 0
ZERO_BYTE_REQUIRED_FILE_COUNT = 0
PLUGIN_INTEGRITY = PASS
SOURCE_CACHE_SCOPED_HASH_MISMATCHES = 0
```

The installed `hooks/hooks.json` is byte-for-byte identical to the
authoritative source and contains the `%CLAUDE_PLUGIN_ROOT%` Windows command
expansion.

## Stale configuration and process state

Before the successful stale-binding cleanup, the user configuration contained:

```text
[plugins."jdipt@task3-typed-semantic-controls"]
enabled = true
```

The corresponding cache directory exists but is empty:

```text
C:\Users\KSH\.codex\plugins\cache\task3-typed-semantic-controls\jdipt\0.2.4
TASK3_CACHE_FILE_COUNT = 0
```

The official removal command for this exact stale plugin was attempted and
failed with Windows `os error 32` because another process was using the cache
entry. No force termination or manual cache deletion was performed.

The pre-cleanup app-server observation was:

```text
PID = 29100
PATH = C:\Users\KSH\.codex\plugins\.plugin-appserver\codex.exe
START = 2026-09-07 23:30:02 +09:00
```

That process was not reused as post-install fresh-runtime evidence. The newer
PID 51412 above is also not valid evidence for the post-hook-fix install until
the official installer succeeds and a fresh runtime is started afterward.

## Fresh CLI probe result

A standalone `codex exec` was run with a per-process override disabling the
stale task3 plugin. The model made exactly one real call to
`mcp__jdipt_runtime__register_material_proposition`. The call failed with:

```text
Invalid tool arguments: authoritative plugin data was not injected
```

The recorded MCP arguments contained no `_runtime_plugin_data`, and the
post-install JDIPT hook traces were not updated. Therefore this probe proves
neither a positive runtime lifecycle nor active hook identity; it is a
fail-closed live recheck while the pre-install app-server is still present.

```text
ACTIVE_HOOK = NOT_PROVEN
ACTIVE_MODULE = NOT_PROVEN
PLUGIN_DATA = NOT_PROVEN
_runtime_plugin_data = NOT_PRESENT_IN_MCP_INPUT
EXACT_TURN = NOT_RUN
ASH06 = NOT_RUN
```

The next safe step is to exit the Codex desktop process completely so the
current app-server and its related runtime children are gone, then run the
official installer again and start a new Codex process. No unrelated process
was terminated and the cache was not manually modified.

## 2026-09-08 post-reboot retry

The user rebooted Windows and relaunched Codex. A new desktop/app-server
process family was observed:

```text
CHATGPT_PROCESS = 19048 (ChatGPT.exe)
APP_SERVER = 9184 (C:\Users\KSH\.codex\plugins\.plugin-appserver\codex.exe)
APP_SERVER_START = 2026-09-08 07:35:43 +09:00
RELATED_RUNTIME_CHILDREN = python.exe scripts/jdipt_runtime_mcp.py (3)
```

The official standalone installer was retried after the reboot, but failed at
the same cache-backup operation:

```text
INSTALL_COMMAND = codex plugin add jdipt@sage1993 --json
INSTALL_EXIT_CODE = non-zero
ERROR = failed to back up plugin cache entry: Access is denied (os error 5)
```

The cache ACL was readable and showed the user and Administrators with full
control, while the active app-server and its runtime children were still
present. No cache content was changed. The installed cache therefore remains
the pre-fix copy, and the runtime acceptance gates remain unproven until the
desktop process is fully exited before the next official install.

## Active-host diagnostic after the successful installation

The user's subsequent official installation succeeded, and the app-server
reported `jdipt@sage1993` as an enabled, trusted plugin hook. However,
`hooks/list` also showed that the active cache still contained the quoted
Windows command form. The authoritative source has now been corrected to use
quote-free `py -3 %CLAUDE_PLUGIN_ROOT%\\scripts\\<hook>.py` commands, and the
focused source suite passes with 26 tests. This change is not yet in the
official cache because the Desktop process currently holds the cache lock;
the live MCP result remains fail-closed and the acceptance verdict remains
HOLD until official installation and fresh-runtime recheck are completed.

## Isolated official-install verification

An isolated temporary `CODEX_HOME` was configured against the authoritative
local marketplace. The official installer completed successfully, the
installed hook manifest contained the quote-free Windows commands, and
`plugin_integrity.py` returned `INSTALLATION_INTEGRITY: PASS` for that
isolated cache. The isolated native CLI probe could not reach a model MCP
call because that temporary home had no credentials and returned `401
Unauthorized`; it is therefore not live acceptance evidence. The temporary
home and schema artifacts were removed afterward.

The current GPT Work nested `functions.exec` route is also not treated as a
native PreToolUse acceptance route: its nested MCP invocation does not produce
the Codex hook lifecycle event needed to prove injection. The remaining
acceptance step is the user's real Desktop cache installation followed by a
fresh native MCP call.
