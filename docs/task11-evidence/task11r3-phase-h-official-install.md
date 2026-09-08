# Task 11R-3 Phase H — Official Installer Retry

Prerequisites observed before invocation:

```text
AUTHORITATIVE_SOURCE = F:\2026-PJ\JDIPT\.worktrees\task11-runtime-acceptance-closure
CACHE_LOCK_RELEASED = YES for current registered-file probe
```

Official command:

```text
codex plugin add jdipt@sage1993 --json
INSTALL_START_TIME = 2026-09-07T23:03:39.2483148+09:00
INSTALL_END_TIME = 2026-09-07T23:03:48.5025422+09:00
INSTALL_EXIT_CODE = 1
INSTALL_STDERR = failed to back up plugin cache entry: access denied (WinError 5)
```

```text
INSTALL_PROCESS_RESULT = FAIL
CACHE_DIRECTLY_MODIFIED = NO
```

The command was the supported official installer. No manual cache repair,
copy, patch, restore, or version bump was attempted after this failure.

## Post-reinstall official retry

After the Codex standalone binary was reinstalled, the same supported
installer was invoked through the official `codex-cli 0.153.4` binary:

```text
INSTALL_COMMAND = codex plugin add jdipt@sage1993 --json
INSTALL_EXIT_CODE = 0
INSTALL_PROCESS_RESULT = PASS
GENERATED_CACHE = C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4
CACHE_DIRECTLY_MODIFIED = NO
```

This process result is now PASS, but later active-runtime gates remain open.
