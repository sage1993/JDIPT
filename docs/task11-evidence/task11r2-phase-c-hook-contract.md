# Task 11R-2 Phase C — Hook Contract Remediation

## Minimal production change

The only Windows command change is the environment variable consumed for the
script path:

```text
before: py -3 "%PLUGIN_ROOT%\\scripts\\<hook>.py"
after:  py -3 "%CLAUDE_PLUGIN_ROOT%\\scripts\\<hook>.py"
```

This change is present for `UserPromptSubmit`, `PreToolUse`, and `Stop` in
`hooks/hooks.json`. POSIX commands, stdin JSON, stdout JSON, timeout, and exit
code behavior are unchanged.

The Python bridge now resolves `CLAUDE_PLUGIN_DATA` first. The legacy
`PLUGIN_DATA` value is used only if the reserved key is absent. A present empty
reserved value is not replaced by the legacy value. Host-resolved data must be
an existing absolute directory; missing, empty, relative, non-directory, or
otherwise invalid data remains fail-closed. Explicit internal paths retain the
pre-existing create-on-write behavior needed by the registry service tests.

```text
FIX = Windows hook command expansion + reserved PLUGIN_DATA bridge
CHANGED_PRODUCTION_FILES =
  hooks/hooks.json
  scripts/plugin_runtime_context.py
  scripts/inject_registry_runtime.py
  scripts/synthesis_runtime_state.py
SEMANTIC_FILES_CHANGED = NO
FAIL_OPEN_ADDED = NO
AUTO_REPAIR_ADDED = NO
SYNTHETIC_PLUGIN_DATA = NO
```

## Post-fix source hashes

```text
hooks/hooks.json = d0fe41e6b75094f562e88ba363f591709b5f625facffcb5fee414c4fcbb7274b
scripts/plugin_runtime_context.py = c0313607db2ce273d195319c35d2b2acf43bf73d3fc508143072d0fa4d53ddb9
scripts/inject_registry_runtime.py = 55269c9d76cb6a516f9e2950278d91196c5d73e8c4d78337da33e1969cec6545
scripts/synthesis_runtime_state.py = 0ad561134e7323a1dfed3636968c70fd4036d546964a65ce392bf644abc75749
```
