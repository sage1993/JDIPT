# Task 11R-2 Phase F — Formal Install / Update

## Before

```text
CONFIGURED_SOURCE_BEFORE = C:\Users\KSH\.codex\visualizations\2026\09\06\01a0769a-1b77-7a83-990e-e8f32ba44634\jdipt-correctness-stabilization
CACHE_PATH_BEFORE = C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4
PLUGIN_VERSION_BEFORE = 0.2.4
HOOK_SHA_BEFORE = 840509260e9ab3f5a69a01a37302eb361c9c0a637c0d863777c25d96d30cbf81
```

## Formal operations

The official marketplace command rejected an in-place replacement, so the
existing marketplace was removed and re-added through the CLI:

```text
codex plugin marketplace add <candidate>
  first attempt: rejected because sage1993 already existed
codex plugin marketplace remove sage1993 --json
  result: {"marketplaceName":"sage1993","installedRoot":null}
codex plugin marketplace add <candidate> --json
  result: installedRoot = F:\2026-PJ\JDIPT\.worktrees\task11-runtime-acceptance-closure
```

The official install operation was then attempted twice and the official
uninstall operation twice. Each install stopped while backing up the existing
cache entry with Windows access denied; each uninstall stopped because another
process held the cache entry open with Windows sharing violation. No cache file
was manually edited or copied.

```text
codex plugin add jdipt@sage1993 --json = FAIL
  failed to back up plugin cache entry: access denied (WinError 5)
codex plugin remove jdipt@sage1993 --json = FAIL
  failed to remove existing plugin cache entry: file in use (WinError 32)
retry install = FAIL — WinError 5
retry uninstall = FAIL — WinError 32
```

After the official attempts, the `0.2.4` directory remained but its runtime
contents were absent. The live plugin list still reports the candidate as the
configured source and `jdipt@sage1993` as version `0.2.4`, but that catalog entry
is not proof of an installed runtime package.

```text
CONFIGURED_SOURCE_AFTER = F:\2026-PJ\JDIPT\.worktrees\task11-runtime-acceptance-closure
CACHE_PATH_AFTER = C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4
FORMAL_INSTALL_UPDATE = FAIL
CACHE_DIRECTLY_MODIFIED = NO
```

