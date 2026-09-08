# Task 11R-2 Phase A — Baseline / Preservation

Captured: 2026-09-07 (Asia/Seoul)

## Repository baseline

```text
BASE_SHA = c6e225f1c549070581765583577c1c9aba6ceeb7
BRANCH = codex/task11-runtime-acceptance-closure
TOP_LEVEL = F:/2026-PJ/JDIPT/.worktrees/task11-runtime-acceptance-closure
ROOT_DIRTY_PRESERVED = YES
TASK9_MODIFIED = NO
TASK10_MODIFIED = NO
ASH06_ORACLE_MODIFIED = NO
CACHE_DIRECTLY_MODIFIED = NO
```

The candidate worktree has only pre-existing untracked Task 11 evidence/probe
artifacts at baseline; no tracked semantic production file was changed in this
task before this capture. The separate repository root at
`F:\2026-PJ\JDIPT` was already dirty and was not edited.

`git diff --check` returned no whitespace errors. Git emitted only the normal
LF/CRLF conversion warnings for pre-existing working-tree files.

## Runtime locations

```text
CANDIDATE_SOURCE = F:\2026-PJ\JDIPT\.worktrees\task11-runtime-acceptance-closure
CONFIGURED_SOURCE = C:\Users\KSH\.codex\visualizations\2026\09\06\01a0769a-1b77-7a83-990e-e8f32ba44634\jdipt-correctness-stabilization
ACTIVE_CACHE = C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4
PLUGIN_DATA_EXPECTED = C:\Users\KSH\.codex\plugins\data\jdipt-sage1993
CLI_EXECUTABLE = C:\Users\KSH\.codex\plugins\.plugin-appserver\codex.exe
CLI_VERSION = codex-cli 0.153.4
```

The configured source and active cache were already dirty before this task;
they were inspected read-only. No cache file was edited, copied, or replaced.

## Required artifact hashes

SHA-256 values were captured from the three relevant locations:

| Artifact | Candidate | Configured source | Active cache |
| --- | --- | --- | --- |
| `hooks/hooks.json` | `a3119fecc9b3c2892da2ceaad69fa25ddcf210f50274955fca82915b75a05db9` | `840509260e9ab3f5a69a01a37302eb361c9c0a637c0d863777c25d96d30cbf81` | `840509260e9ab3f5a69a01a37302eb361c9c0a637c0d863777c25d96d30cbf81` |
| `scripts/jdipt_activation.py` | `a5f8fd35f89be063dd54fede440dde503979da8a7e434b020c9c45ce01a43ec5` | `9d2a30f30228dcd53e28973bcfe635f7c6c91c55ed2c5a25a2b56ba100eb3a16` | `9d2a30f30228dcd53e28973bcfe635f7c6c91c55ed2c5a25a2b56ba100eb3a16` |
| `scripts/jdipt_runtime_mcp.py` | `4ddf2794e1c871e903c909aa7e9bed0f05d1321d556a1e279233dfcbb6ec87b9` | `6ec7e9e21711dd277de610addef88191aa159f2b9a1c7a668b3f72f9ae647583` | `6ec7e9e21711dd277de610addef88191aa159f2b9a1c7a668b3f72f9ae647583` |

## Integrity baseline

`python scripts/plugin_integrity.py --repo-root <candidate> --installed-root
<active-cache>` returned `INSTALLATION_INTEGRITY: FAIL` with exactly 18
mismatches. The complete inherited set is preserved below:

```text
digest mismatch: SKILL.md
digest mismatch: plugin/hooks/hooks.json
digest mismatch: plugin/scripts/jdipt_activation.py
digest mismatch: plugin/scripts/jdipt_runtime_mcp.py
digest mismatch: plugin/scripts/legal_proposition.py
missing installed file: plugin/scripts/material_obligation_ingress.py
missing installed file: plugin/scripts/material_obligation_ledger.py
missing installed file: plugin/scripts/proposition_obligation_closure.py
digest mismatch: plugin/scripts/proposition_registry.py
digest mismatch: plugin/scripts/proposition_relations.py
missing installed file: plugin/scripts/proposition_render_coverage.py
digest mismatch: plugin/scripts/proposition_rendering.py
missing installed file: plugin/scripts/proposition_soundness.py
missing installed file: plugin/scripts/proposition_source_closure.py
digest mismatch: plugin/scripts/stop_synthesis_gate.py
digest mismatch: plugin/scripts/synthesis_runtime_state.py
digest mismatch: references/legal-issue-mapping.md
digest mismatch: references/source-policy.md
```

```text
BASE_MISMATCH_COUNT = 18
TASK11R2_INTRODUCED_MISMATCH_COUNT = 0
```

