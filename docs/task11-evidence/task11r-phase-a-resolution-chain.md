# Task 11R Phase A — Plugin Resolution Chain

Investigation date: 2026-09-07 (Asia/Seoul). This is read-only evidence. No
Codex binding, installed cache, or marketplace source was changed.

## Resolution records

```text
INPUT = jdipt@sage1993
RESOLVER = C:\Users\KSH\.codex\config.toml + `codex.exe plugin list --json`
RULE = [plugins."jdipt@sage1993"].enabled = true
OUTPUT = installed plugin jdipt, marketplace sage1993, version 0.2.4
SOURCE_OF_TRUTH = C:\Users\KSH\.codex\config.toml and direct CLI JSON
EVIDENCE = source.path =
  C:\Users\KSH\.codex\visualizations\2026\09\06\01a0769a-1b77-7a83-990e-e8f32ba44634\jdipt-correctness-stabilization
```

```text
INPUT = marketplace sage1993
RESOLVER = [marketplaces.sage1993] in config.toml
RULE = source_type = "local"
OUTPUT = C:\Users\KSH\.codex\visualizations\2026\09\06\01a0769a-1b77-7a83-990e-e8f32ba44634\jdipt-correctness-stabilization
SOURCE_OF_TRUTH = C:\Users\KSH\.codex\config.toml and `codex plugin marketplace list`
EVIDENCE = plugin.json at that root is jdipt 0.2.4
```

```text
INPUT = local marketplace source + plugin name jdipt
RESOLVER = Codex plugin installer/catalog
RULE = installed version 0.2.4 is selected for jdipt@sage1993
OUTPUT = C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4
SOURCE_OF_TRUTH = direct `plugin list --json` plus active app-server catalog warning
EVIDENCE = active catalog host_root was printed as the OUTPUT path
```

The same config enables `jdipt@task3-typed-semantic-controls` and
`jdipt@task4-semantic-soundness`. The fresh app-server emitted duplicate MCP
server warnings and then:

```text
conflicting MCP server actions; using resolved catalog outcome
server="jdipt_runtime"
plugin_id="jdipt@sage1993"
host_root="C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4"
```

That is direct active-source evidence. The candidate worktree is not the
configured marketplace source and is not the active host root.

No separate per-plugin installation database was present under
`C:\Users\KSH\.codex\plugins`; the observable install metadata is the CLI
catalog record, config binding, manifest, and cache path. The active cache is a
separate registered worktree at `8fcf3fdc726887ee3871a1772c1946150966521f` on
branch `codex-jdipt-correctness-stabilization`, and is dirty.
