# Task 11R-3 Phase K — Cryptographic Content Parity

Command:

```text
python scripts/plugin_integrity.py --repo-root F:\2026-PJ\JDIPT\.worktrees\task11-runtime-acceptance-closure --installed-root C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4
```

Observed result:

```text
BASE_MISMATCH_COUNT = 18
FINAL_MISMATCH_COUNT = 0
TASK11R3_INTRODUCED_MISMATCH_COUNT = 0
PLUGIN_INTEGRITY = PASS (scoped runtime manifest observation)
RESOLVED_BY_FORMAL_INSTALL = NOT_PROVEN
```

All scoped runtime hashes printed by the command matched. The previous 18
mismatches are therefore absent from the current cache snapshot, but because
the official install attempt in this task exited 1, this evidence cannot claim
that the formal install resolved them.

The post-reinstall official 0.153.4 invocation exited 0 and the same command
reported `mismatches: []` and `INSTALLATION_INTEGRITY: PASS`. The installed
`hooks/hooks.json` also matches the authoritative source exactly. No direct
cache mutation was used.
