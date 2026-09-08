# Task 11R Phase C — Hook Command Contract

Active file:

```text
C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4\hooks\hooks.json
SHA-256 = 840509260e9ab3f5a69a01a37302eb361c9c0a637c0d863777c25d96d30cbf81
```

```text
UserPromptSubmit command        = python3 "$PLUGIN_ROOT/scripts/jdipt_activation.py"
UserPromptSubmit commandWindows = py -3 "%PLUGIN_ROOT%\scripts\jdipt_activation.py"
PreToolUse command              = python3 "$PLUGIN_ROOT/scripts/inject_registry_runtime.py"
PreToolUse commandWindows       = py -3 "%PLUGIN_ROOT%\scripts\inject_registry_runtime.py"
Stop command                    = python3 "$PLUGIN_ROOT/scripts/stop_synthesis_gate.py"
Stop commandWindows             = py -3 "%PLUGIN_ROOT%\scripts\stop_synthesis_gate.py"
stdin                           = JSON hook event
stdout                          = JSON hook response
exit code                       = command hook process result
```

The hook command does not mention `PLUGIN_DATA`. The Python bridge reads
`os.environ["PLUGIN_DATA"]` only after the command reaches Python.

The active app-server binary is:

```text
C:\Users\KSH\.codex\plugins\.plugin-appserver\codex.exe
version = codex-cli 0.153.4
SHA-256 = e5aa76d19c7c94e2e9ef9b707d590206a73ac0e97c8ddc8382181242494bef75
```

Read-only ASCII inspection of its hook-discovery segment contains the adjacent
reserved names `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA`, while the bare
`PLUGIN_ROOT`/`PLUGIN_DATA` strings occur in a separate
`codex-mcp/src/agent_plugin_config.rs` path-placeholder segment. The hook
discovery segment also contains `hooks/src/engine/discovery.rs` and hook
failure diagnostics.

## Controlled expansion results

| Environment supplied | Result | Meaning |
| --- | --- | --- |
| neither `PLUGIN_ROOT` nor `PLUGIN_DATA` | literal `%PLUGIN_ROOT%` path; exit 2 | wrapper fails before Python |
| `CLAUDE_PLUGIN_ROOT` only | same literal `%PLUGIN_ROOT%` path; exit 2 | no implicit alias |
| `PLUGIN_ROOT` only | JSON deny: `PLUGIN_DATA is unavailable`; exit 0 | Python is reached, but data is not created |
| `PLUGIN_ROOT` + nonempty `PLUGIN_DATA` | JSON allow with `_runtime_plugin_data`; exit 0 | bridge works when contract is satisfied |
| `PLUGIN_ROOT` + `CLAUDE_PLUGIN_DATA` only | JSON deny: `PLUGIN_DATA is unavailable`; exit 0 | Python does not alias CLAUDE data |

The fresh app-server reproduced the failed-command path: `UserPromptSubmit
Failed`, `PreToolUse Failed`, then the MCP error `authoritative plugin data
was not injected`.
