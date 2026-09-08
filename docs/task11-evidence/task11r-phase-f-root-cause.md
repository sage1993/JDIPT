# Task 11R Phase F/H — Root Cause Decision

```text
ROOT_CAUSE = HOOK_COMMAND_EXPANSION
DEFECT_BOUNDARY = app-server hook dispatcher reserved-environment contract -> Windows command expansion
CLASSIFICATION = HOOK_COMMAND_EXPANSION
```

## Causal chain

```text
config.toml enables jdipt@sage1993
→ plugin catalog resolves jdipt_runtime to the installed cache
→ active hooks.json asks Windows to expand %PLUGIN_ROOT%
→ app-server hook discovery exposes the CLAUDE_PLUGIN_ROOT / CLAUDE_PLUGIN_DATA contract;
  controlled CLAUDE-only execution leaves %PLUGIN_ROOT% literal
→ cmd.exe attempts a path containing literal %PLUGIN_ROOT% and exits 2
→ Python hook is not entered, so no os.environ["PLUGIN_DATA"] read can produce
  an authoritative _runtime_plugin_data field
→ PreToolUse is reported Failed and the MCP tool is invoked without _runtime_plugin_data
→ active jdipt_runtime_mcp.py rejects the call with
  "authoritative plugin data was not injected"
→ UserPromptSubmit and Stop fail at the same hook-command boundary; no fresh
  PENDING → ACTIVE → STOP lifecycle is created
```

## Why this is proven

1. The active app-server printed its resolved host root and the active cache
   `hooks.json` hash.
2. The app-server binary's hook-discovery segment contains
   `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA`; bare `PLUGIN_*` strings are
   in a separate MCP path-placeholder segment.
3. Exact active Windows command + only `CLAUDE_PLUGIN_ROOT` reproduced the
   literal `%PLUGIN_ROOT%` path and exit code 2.
4. `PLUGIN_ROOT` without `PLUGIN_DATA` reached Python and denied; both PLUGIN
   variables returned allow and inserted `_runtime_plugin_data`.
5. The fresh app-server run produced the same failed hooks and downstream MCP
   error.

The 18 inherited cache/source mismatches remain an independent parity blocker.
The active cache contains the same failing hook-variable contract, and the
bridge works when its required variables are explicitly supplied. The evidence
therefore supports Task 11R Case 2: cache parity is separately blocking while
the immediate PLUGIN_DATA failure is hook command expansion.

## Correct remediation boundary

No cache overwrite was performed. The safe remediation is to select one
authoritative binding, use the formal install/update path to regenerate the
versioned cache, and update the package hook contract so the Windows command
consumes the app-server-reserved root/data names or an explicit wrapper maps
them to `PLUGIN_ROOT`/`PLUGIN_DATA` before Python starts. A fresh session must
then capture T0–T5, `module.__file__`, module SHA-256, and exact-turn state
before ASH-06. This remediation is not claimed as completed by Task 11R.
