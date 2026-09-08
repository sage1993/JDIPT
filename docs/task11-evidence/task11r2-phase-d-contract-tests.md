# Task 11R-2 Phase D — Hook Contract Tests

The focused suite is `tests/test_task11r2_hook_contract.py`. It contains 18
tests covering the required D cases and the activation boundary.

```text
D-01 missing root/data                  = DENY
D-02 root only                          = DENY
D-03 data only                          = incomplete Windows hook contract
D-04 empty reserved root                = no fallback / fail-closed
D-05 empty reserved data                = no fallback / DENY
D-06 valid absolute data directory      = ALLOW
D-07 CLAUDE variables only              = reserved data bridge works
D-08 bare PLUGIN variables only         = deterministic compatibility fallback
D-09 invalid plugin-data path           = DENY
D-10 valid bridge                      = exact _runtime_plugin_data injection
D-11 malformed injected field           = MCP fail-closed
D-12 missing injected field             = MCP fail-closed
```

Additional assertions prove that activation persists `PENDING` under reserved
`CLAUDE_PLUGIN_DATA`, reserved data wins over a conflicting legacy value, and
all three Windows hook commands contain `%CLAUDE_PLUGIN_ROOT%` with no
`%PLUGIN_ROOT%` token.

```text
RED = collection failed before production bridge existed:
      ModuleNotFoundError: scripts.plugin_runtime_context
GREEN = 18 passed in 8.86s
GREEN_FOCUSED_WITH_REGRESSION = 19 passed in 0.12s
```

The full pre-install regression then passed with `688 passed`.

