# Task 11R Phase E — Runtime Identity Matrix

`A` = Task 11R candidate worktree. `B` = configured `sage1993` local
marketplace source. `C` = installed active cache. `D` = live loaded Python
module identity; it is deliberately `NOT_OBSERVED` because the active hook
failed before Python emitted module telemetry.

| Relative path | A SHA-256 | B SHA-256 | C SHA-256 | D live module |
| --- | --- | --- | --- | --- |
| `hooks/hooks.json` | `a3119fecc9b3c2892da2ceaad69fa25ddcf210f50274955fca82915b75a05db9` | `840509260e9ab3f5a69a01a37302eb361c9c0a637c0d863777c25d96d30cbf81` | `840509260e9ab3f5a69a01a37302eb361c9c0a637c0d863777c25d96d30cbf81` | NOT_OBSERVED |
| `scripts/jdipt_activation.py` | `a5f8fd35f89be063dd54fede440dde503979da8a7e434b020c9c45ce01a43ec5` | `9d2a30f30228dcd53e28973bcfe635f7c6c91c55ed2c5a25a2b56ba100eb3a16` | `9d2a30f30228dcd53e28973bcfe635f7c6c91c55ed2c5a25a2b56ba100eb3a16` | NOT_OBSERVED |
| `scripts/jdipt_runtime_mcp.py` | `4ddf2794e1c871e903c909aa7e9bed0f05d1321d556a1e279233dfcbb6ec87b9` | `6ec7e9e21711dd277de610addef88191aa159f2b9a1c7a668b3f72f9ae647583` | `6ec7e9e21711dd277de610addef88191aa159f2b9a1c7a668b3f72f9ae647583` | NOT_OBSERVED |
| `scripts/proposition_registry.py` | `716a16c01f2744108e00171f31b2b141f09bfe17e8d84a21d1c0c796771832a6` | `79bc4a4a0609d677563e42a612a8213ee3c59d9e20bedc5df87f4255639f1436` | `79bc4a4a0609d677563e42a612a8213ee3c59d9e20bedc5df87f4255639f1436` | NOT_OBSERVED |
| `scripts/synthesis_runtime_state.py` | `05b55bf27f81d1c9db7ffc4419e222e514f027b09e8ae57dd68f075b348b034a` | `f7c9367db730aa60006bfdffa135b1e2037d917cac5a6269962f4a2df41c6ff7` | `f7c9367db730aa60006bfdffa135b1e2037d917cac5a6269962f4a2df41c6ff7` | NOT_OBSERVED |
| `scripts/stop_synthesis_gate.py` | `706c1a58b5b44bd96b6c3844a6ce386c19cb4f11dc7e7f40360cdc38d3a8f344` | `9b10a933da12de953dd61cda0477041f4c195b02485291077bc5aba107f12560` | `9b10a933da12de953dd61cda0477041f4c195b02485291077bc5aba107f12560` | NOT_OBSERVED |
| `scripts/material_obligation_ingress.py` | `3aeeb24bb493f3d4662f6b60efff9fd235d2d650ac45ff30ad18c0d9a90ddae2` | MISSING | MISSING | NOT_OBSERVED |
| `scripts/material_obligation_ledger.py` | `1e745227ce02b7198b68567a0689534754b255d87a32ad42d1d70f3cfe36c983` | MISSING | MISSING | NOT_OBSERVED |
| `scripts/proposition_obligation_closure.py` | `b503de8feb129b472bd024a768edb73f62cb40a3e78eb2d19c99a848c4be484f` | MISSING | MISSING | NOT_OBSERVED |
| `scripts/proposition_render_coverage.py` | `195d28618e75d9ca0bc5b908b0fe94c99be96167cb95c93fc0676faea2d97b35` | MISSING | MISSING | NOT_OBSERVED |
| `scripts/proposition_soundness.py` | `eb11e19377a3098e4cdec0b40dba2152e6390d5ea001f8a002ff2ce171c0d16a` | MISSING | MISSING | NOT_OBSERVED |
| `scripts/proposition_source_closure.py` | `7ad03971679a269795b21cdefb90a42b3f04bc091f3482eaecc329d98d765571` | MISSING | MISSING | NOT_OBSERVED |
| `.codex-plugin/plugin.json` | `d0a90b855382141960b01fa58d489cc1a536283e73234de9868c2de68b76ae9b` | `d0a90b855382141960b01fa58d489cc1a536283e73234de9868c2de68b76ae9b` | `d0a90b855382141960b01fa58d489cc1a536283e73234de9868c2de68b76ae9b` | NOT_OBSERVED |

The complete plugin integrity comparison contains exactly the inherited 18
mismatches. No Task 11R file was installed into or copied over the active
cache.
