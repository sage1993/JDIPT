# Task 11R Phase G — Controlled Minimal Reproduction

The probe used only the active cache's `inject_registry_runtime.py` and a
minimal JSON PreToolUse payload. It did not call semantic logic and did not
write the installed cache.

| Probe | Environment | Output | Conclusion |
| --- | --- | --- | --- |
| G1 | no `PLUGIN_ROOT`, no `PLUGIN_DATA` | literal `%PLUGIN_ROOT%` path; exit 2 | command expansion fails before Python |
| G2 | `CLAUDE_PLUGIN_ROOT` only | same literal `%PLUGIN_ROOT%` path; exit 2 | no implicit alias |
| G3 | `PLUGIN_ROOT` only | deny: `PLUGIN_DATA is unavailable`; exit 0 | Python reached; no data producer |
| G4 | `PLUGIN_ROOT` + nonempty `PLUGIN_DATA` | allow and `_runtime_plugin_data` inserted; exit 0 | bridge works when contract is satisfied |
| G5 | `PLUGIN_ROOT` + `CLAUDE_PLUGIN_DATA` only | deny: `PLUGIN_DATA is unavailable`; exit 0 | no CLAUDE-to-PLUGIN alias |

## Fresh app-server reproduction

```text
executable = C:\Users\KSH\.codex\plugins\.plugin-appserver\codex.exe
version = codex-cli 0.153.4
session_id = 01a07bc6-7202-74e0-8550-b1b081ed51b3
prompt = explicit $law-interpretation-request, one register_material_proposition call
```

```text
hook: UserPromptSubmit
hook: UserPromptSubmit Failed
hook: PreToolUse
hook: PreToolUse Failed
mcp: jdipt_runtime/register_material_proposition started
Mcp error -32602: Invalid tool arguments: authoritative plugin data was not injected
hook: Stop
hook: Stop Failed
```

No fresh state directory for this session/turn was created below the expected
`C:\Users\KSH\.codex\plugins\data\jdipt-sage1993\synthesis-runtime` root.
