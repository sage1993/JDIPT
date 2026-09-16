# JDIPT Runtime Synthesis Enforcement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (or superpowers:subagent-driven-development) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the existing generic synthesis-integrity contract to a real plugin-bundled Stop hook that preserves every registered material proposition through final-answer reconciliation and one bounded repair.

**Architecture:** `synthesis_runtime_state.py` owns an atomic, plugin-data-only turn ledger and adapts registered runtime propositions to the existing deterministic `synthesis_integrity.py` reconciler. `jdipt_runtime_mcp.py` exposes `register_material_proposition` over stdio MCP and deterministically builds the mandatory clause. `stop_synthesis_gate.py` loads only the exact session/turn state, no-ops for unrelated turns, blocks the first mismatch with a repair continuation, and fail-closes after the bounded retry. Plugin packaging, Skill instructions, and structural validators document and verify this path without adding case-specific tokens.

**Tech Stack:** Python 3.13, standard-library dataclasses/json/pathlib/tempfile, stdio JSON-RPC MCP, pytest, Codex plugin `hooks/hooks.json`, Markdown/YAML/JSON contract validation.

**Spec:** `C:/Users/KSH/Downloads/JDIPT PR #14 Runtime Synthesis Enforcement 구현 작업지시서.md`

## Global Constraints

- Preserve all pre-existing dirty and untracked files; never use `git reset`, `git clean`, `git checkout -- .`, `git restore .`, or `git stash`.
- Do not modify `scripts/ansim_housing_oracle.py` or replace existing `scripts/synthesis_integrity.py` behavior; extend only generic interfaces required by runtime integration.
- Keep `law-interpretation-request` explicit-only and keep `allow_implicit_invocation: false`.
- Store runtime state only beneath `PLUGIN_DATA`; never write runtime state into the repository, and do not persist secrets or full legal source text.
- Do not hard-code ASH-06, 안심주택, 250m, 350m, 400%, 사업대상지, or other case-specific tokens in production runtime enforcement.
- Use the documented Stop output contract: `{}` for accepted/no-op, `decision: "block"` plus a generic deterministic clause for the first repair, and `continue: false` with a fail-closed system message after the bounded retry.
- Do not commit, push, merge, rebase, or mark PR #14 ready for review in this task.

---

### Task 1: Implement the plugin-data runtime state store

**Files:**
- Create: `tests/test_synthesis_runtime_state.py`
- Create: `scripts/synthesis_runtime_state.py`

**Interfaces:**
- `RuntimeMaterialProposition` (exported as `MaterialProposition`) is a frozen dataclass with `proposition_id`, `status`, `subject`, `condition`, `procedure`, `operative_verb_lexeme`, `legal_object`, `legal_effect`, `source_clause`, `mandatory_render_clause`, `relation_type`, `base_proposition_id`, `exception_proposition_id`, and `current_status`.
- `RuntimeTurnState` is a mutable dataclass with `session_id`, `turn_id`, `jdipt_active`, `repair_count`, and `propositions`.
- `runtime_state_path(plugin_data, session_id, turn_id) -> Path`, `save_runtime_state(state, plugin_data=None) -> Path`, `load_runtime_state(session_id, turn_id, plugin_data=None) -> RuntimeTurnState | None`, `update_repair_count(state, repair_count, plugin_data=None) -> RuntimeTurnState`, and `register_material_proposition(fields, plugin_data=None) -> RuntimeTurnState` are the public state APIs.
- `to_integrity_proposition()` adapts a runtime proposition to the existing `scripts.synthesis_integrity.MaterialProposition` without copying the full source corpus.

- [ ] **Step 1: Write failing tests for atomic plugin-data persistence.**

```python
def test_round_trip_uses_only_plugin_data_and_exact_session_turn(tmp_path):
    state = RuntimeTurnState(
        session_id="session-a",
        turn_id="turn-1",
        jdipt_active=True,
        repair_count=0,
        propositions=[RuntimeMaterialProposition(
            proposition_id="P1", status="CLOSED", subject="A", condition="C",
            procedure="P", operative_verb_lexeme="지정", legal_object="O",
            legal_effect="Z", source_clause="C와 P 뒤 O를 Z로 지정한다.",
            mandatory_render_clause="C와 P를 충족하면 A는 O를 Z로 지정할 수 있다.",
            relation_type="base", base_proposition_id=None,
            exception_proposition_id=None, current_status="CURRENT_CONFIRMED",
        )],
    )
    path = save_runtime_state(state, tmp_path)
    assert path.parent == tmp_path / "synthesis-runtime" / "session-a"
    assert load_runtime_state("session-a", "turn-1", tmp_path) == state
    assert load_runtime_state("session-b", "turn-1", tmp_path) is None
    assert not (tmp_path / "turn-1.json").exists()
```

- [ ] **Step 2: Add failing tests for malformed, stale, cross-session, and unsafe state.**

```python
def test_malformed_state_raises_fail_closed_error(tmp_path):
    path = runtime_state_path(tmp_path, "session-a", "turn-1")
    path.parent.mkdir(parents=True)
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(RuntimeStateError):
        load_runtime_state("session-a", "turn-1", tmp_path)

def test_register_builds_mandatory_clause_deterministically(tmp_path):
    state = register_material_proposition({
        "session_id": "session-a", "turn_id": "turn-1", "status": "CLOSED",
        "subject": "A", "condition": "C", "procedure": "P",
        "operative_verb_lexeme": "지정", "legal_object": "O",
        "legal_effect": "Z", "source_clause": "증거 문장",
        "relation_type": "exception", "current_status": "CURRENT_CONFIRMED",
    }, tmp_path)
    assert state.jdipt_active is True
    assert state.propositions[0].mandatory_render_clause
    assert state.propositions[0].mandatory_render_clause != "증거 문장"
```

- [ ] **Step 3: Run the new tests and verify a correct missing-API failure.**

Run: `py -3.13 -m pytest -q tests/test_synthesis_runtime_state.py`

Expected: collection failure because `scripts.synthesis_runtime_state` does not yet exist.

- [ ] **Step 4: Implement validation, atomic write, exact-path load, and deterministic clause creation.**

Use a temporary file in the same directory, UTF-8 JSON with stable keys, flush and `os.fsync`, then `os.replace`. Reject path separators/control characters in session and turn IDs, reject unknown status values, cap field lengths, and raise `RuntimeStateError` for malformed or schema-invalid JSON. `register_material_proposition` sets `jdipt_active=True`, creates the mandatory clause from structured fields using `build_mandatory_render_clause`, and merges only the exact session/turn state.

- [ ] **Step 5: Run the state tests and verify they pass.**

Run: `py -3.13 -m pytest -q tests/test_synthesis_runtime_state.py`

Expected: all state round-trip, atomicity, malformed-state, stale-state, and deterministic-clause tests PASS.

---

### Task 2: Add the Stop hook gate and bounded repair

**Files:**
- Create: `tests/test_stop_synthesis_gate.py`
- Create: `scripts/stop_synthesis_gate.py`
- Modify: `hooks/hooks.json`

**Interfaces:**
- `handle_stop_event(event: Mapping[str, Any], plugin_data: Path | None = None) -> dict[str, Any]` is the testable gate entry point.
- The CLI reads exactly one JSON object from stdin and writes exactly one JSON object to stdout.
- The gate adapts state propositions with `to_integrity_proposition`, calls `reconcile_draft`, and uses `repair_draft` only to construct the deterministic repair clause; it never paraphrases free-form text.

- [ ] **Step 1: Write failing tests for unrelated no-op, accepted output, first block, second fail-closed, and missing/malformed state.**

```python
def test_unrelated_turn_is_a_noop(tmp_path):
    result = handle_stop_event({"session_id": "s", "turn_id": "t", "last_assistant_message": "OK"}, tmp_path)
    assert result == {}

def test_first_degraded_stop_blocks_with_mandatory_clause_and_increments_repair(tmp_path, closed_state):
    save_runtime_state(closed_state, tmp_path)
    result = handle_stop_event({
        "session_id": "s", "turn_id": "t", "stop_hook_active": False,
        "last_assistant_message": "C를 충족하면 기준이 완화될 수 있다.",
    }, tmp_path)
    assert result["decision"] == "block"
    assert "지정" in result["reason"] and "P" in result["reason"]
    assert load_runtime_state("s", "t", tmp_path).repair_count == 1

def test_second_degraded_stop_never_continues_again(tmp_path, closed_state):
    save_runtime_state(replace(closed_state, repair_count=1), tmp_path)
    result = handle_stop_event({
        "session_id": "s", "turn_id": "t", "stop_hook_active": True,
        "last_assistant_message": "C를 충족하면 기준이 완화될 수 있다.",
    }, tmp_path)
    assert result["continue"] is False
    assert "fail-closed" in result["systemMessage"]
```

- [ ] **Step 2: Run the gate tests and verify they fail because the gate API is missing.**

Run: `py -3.13 -m pytest -q tests/test_stop_synthesis_gate.py`

Expected: collection failure for the missing `scripts.stop_synthesis_gate` module.

- [ ] **Step 3: Implement the activation and reconciliation paths.**

If no exact state exists, return `{}`; if the exact file exists but is malformed, return a fail-closed response. If `jdipt_active` is false, return `{}`. For a valid active state, reconcile `last_assistant_message`. On the first failure (`repair_count == 0` and `stop_hook_active` false), atomically set repair count to one and return `decision: "block"` with every unresolved proposition’s mandatory clause. On any later failure, return `continue: false`, `stopReason`, and a concise generic `systemMessage` without starting another continuation. An OPEN proposition must remain neutral and must not be promoted.

- [ ] **Step 4: Replace the temporary probe hook with the production Windows-compatible hook.**

Use the verified plugin command form:

```json
{
  "description": "JDIPT runtime synthesis integrity enforcement",
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$PLUGIN_ROOT/scripts/stop_synthesis_gate.py\"",
            "commandWindows": "py -3 \"%PLUGIN_ROOT%\\scripts\\stop_synthesis_gate.py\"",
            "timeout": 30,
            "statusMessage": "Validating legal synthesis"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 5: Run the gate tests and verify they pass.**

Run: `py -3.13 -m pytest -q tests/test_stop_synthesis_gate.py`

Expected: PASS for no-op isolation, accepted output, first block, deterministic repair reason, malformed state, OPEN safety, and second-stop fail-closed behavior.

---

### Task 3: Expose the material proposition registry through bundled MCP

**Files:**
- Create: `.mcp.json`
- Create: `scripts/jdipt_runtime_mcp.py`
- Create: `tests/test_jdipt_runtime_mcp.py`
- Modify: `.codex-plugin/plugin.json`

**Interfaces:**
- `register_material_proposition(arguments: Mapping[str, Any]) -> dict[str, Any]` validates the registry payload, calls `synthesis_runtime_state.register_material_proposition`, and returns only proposition metadata plus the state path relative to plugin data.
- `serve(stdin, stdout) -> None` implements the minimal MCP stdio lifecycle: `initialize`, `notifications/initialized`, `tools/list`, and `tools/call` for `register_material_proposition`.
- `.mcp.json` defines one local server named `jdipt_runtime` with a Windows-compatible `py -3` command pointing to `%PLUGIN_ROOT%\scripts\jdipt_runtime_mcp.py`.

- [ ] **Step 1: Write failing tests for registration and tools/list/tools/call protocol.**

```python
def test_register_material_proposition_returns_deterministic_clause(tmp_path, monkeypatch):
    monkeypatch.setenv("PLUGIN_DATA", str(tmp_path))
    result = register_material_proposition({
        "session_id": "s", "turn_id": "t", "status": "CLOSED",
        "subject": "A", "condition": "C", "procedure": "P",
        "operative_verb_lexeme": "승인", "legal_object": "O",
        "legal_effect": "Z", "source_clause": "source",
    })
    assert result["proposition"]["mandatory_render_clause"]
    assert "승인" in result["proposition"]["mandatory_render_clause"]

def test_tools_list_exposes_only_the_registry_tool():
    response = dispatch_json_rpc({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    assert [tool["name"] for tool in response["result"]["tools"]] == ["register_material_proposition"]
```

- [ ] **Step 2: Run the MCP tests and verify a missing-API failure.**

Run: `py -3.13 -m pytest -q tests/test_jdipt_runtime_mcp.py`

Expected: collection failure because the server module does not yet exist.

- [ ] **Step 3: Implement the minimal stdio MCP server and packaging.**

Return JSON-RPC errors for malformed requests, unknown methods, invalid arguments, and unknown tools. Never emit debug text on stdout. Do not persist `source_clause` or other fields above the state-store bounds. Add `"mcpServers": "./.mcp.json"` to the plugin manifest while preserving `name`, version, `skills`, and interface contracts.

- [ ] **Step 4: Run the MCP tests and verify they pass.**

Run: `py -3.13 -m pytest -q tests/test_jdipt_runtime_mcp.py`

Expected: PASS for registry semantics, JSON-RPC dispatch, deterministic clause creation, and invalid-input rejection.

---

### Task 4: Make the Skill contract invoke the runtime registry

**Files:**
- Modify: `skills/law-interpretation-request/SKILL.md`
- Modify: `skills/law-interpretation-request/references/legal-issue-mapping.md`
- Modify: `skills/law-interpretation-request/references/source-policy.md`
- Modify: `skills/law-interpretation-request/references/logic-validation.md`
- Modify: `tests/test_synthesis_integrity_contract.py`
- Modify: `scripts/validate_repo.py`

**Interfaces:**
- The ASCII execution contract becomes authoritative for the sequence `Material Proposition Ledger → registry write → mandatory proposition sentence construction → mandatory slots in draft → explanatory synthesis → proposition-to-draft reconciliation → one targeted repair → one bounded re-check → final rendering`.
- It states that both CLOSED and material OPEN propositions are registered, that `mandatory_render_clause` is deterministic, and that the first successful registry write is the authoritative `jdipt_active` signal when no stable Skill activation identifier is available.

- [ ] **Step 1: Add failing contract assertions for registry invocation, plugin-data-only state, and bounded Stop behavior.**

```python
def test_runtime_contract_registers_before_mandatory_rendering():
    runtime = _section(_read(SKILL_ROOT / "SKILL.md"), "Synthesis Integrity Gate")
    sequence = ["Material Proposition Ledger", "registry write", "mandatory proposition sentence construction", "mandatory slots in draft", "explanatory synthesis", "proposition-to-draft reconciliation", "one targeted repair", "one bounded re-check", "final rendering"]
    assert [runtime.index(item) for item in sequence] == sorted(runtime.index(item) for item in sequence)
    assert "PLUGIN_DATA" in runtime
    assert "register_material_proposition" in runtime

def test_packaging_contract_requires_runtime_files_and_no_case_tokens():
    assert (ROOT / "hooks/hooks.json").is_file()
    assert (ROOT / "scripts/stop_synthesis_gate.py").is_file()
    assert (ROOT / "scripts/synthesis_runtime_state.py").is_file()
    assert "mcpServers" in _read(ROOT / ".codex-plugin/plugin.json")
```

- [ ] **Step 2: Run focused contract tests and verify they fail on missing runtime markers/files.**

Run: `py -3.13 -m pytest -q tests/test_synthesis_integrity_contract.py`

Expected: FAIL with missing registry/packaging markers before documentation edits.

- [ ] **Step 3: Update the authoritative Skill block and references.**

Keep existing generic markers, add the registry invocation immediately after the ledger, state that only the structured relation is sent to the registry, and state that the deterministic helper—not the model—creates `mandatory_render_clause`. Preserve explicit-only invocation, OPEN neutral handling, the exact four-H1 output contract, and all existing URL/source rules. Keep case-specific strings out of production docs and validator source.

- [ ] **Step 4: Extend structural validation without confusing static presence with semantic proof.**

Require `hooks/hooks.json`, the Stop/runtime/MCP files, the plugin manifest MCP path, Windows command, `PLUGIN_ROOT`, `PLUGIN_DATA`, `register_material_proposition`, bounded repair markers, and the focused behavior-test path. Scan runtime source and production Skill/reference text for the forbidden case tokens. Label the synthesis marker result as structural-only.

- [ ] **Step 5: Run focused contract and structural tests and verify they pass.**

Run: `py -3.13 -m pytest -q tests/test_synthesis_integrity_contract.py tests/test_structural_behavior_contract.py`

Expected: PASS with no ASH-06-specific hard-code failures and `allow_implicit_invocation` unchanged.

---

### Task 5: Run repository validation and runtime smoke checks

**Files:**
- Modify only validation/report files if a command requires an honest evidence note; do not modify the ASH-06 oracle or pre-existing dirty files unrelated to this implementation.

- [ ] **Step 1: Run focused runtime, synthesis, and packaging tests.**

Run separately:

```powershell
py -3.13 -m pytest -q tests/test_synthesis_runtime_state.py
py -3.13 -m pytest -q tests/test_stop_synthesis_gate.py
py -3.13 -m pytest -q tests/test_jdipt_runtime_mcp.py
py -3.13 -m pytest -q tests/test_synthesis_integrity_behavior.py tests/test_synthesis_integrity_contract.py
```

- [ ] **Step 2: Run all required static checks with fresh output.**

Run separately:

```powershell
py -3.13 -m pytest -q
py -3.13 scripts/validate_repo.py
py -3.13 scripts/validate_authority_temporal_contract.py
py -3.13 scripts/plugin_integrity.py
py -3.13 -m compileall -q scripts tests
git diff --check
```

- [ ] **Step 3: Synchronize and inspect the installed plugin artifact.**

Run `codex plugin add jdipt@sage1993 --json`, verify the cached artifact contains the same manifest, `.mcp.json`, `hooks/hooks.json`, and runtime scripts, and confirm `plugin_integrity.py` passes before live behavior claims.

- [ ] **Step 4: Run hook-specific live smoke with synthetic state.**

Use the Codex appserver (`C:\Users\KSH\.codex\plugins\.plugin-appserver\codex.exe`) with the installed plugin and a synthetic fixture to verify: hook loaded/trusted, Stop fired, `PLUGIN_ROOT` and `PLUGIN_DATA` were available, valid output no-ops, a degraded output receives exactly one continuation, and the repaired output is accepted. Use a separate no-state unrelated turn to verify no intervention. Store only presence booleans and counts in plugin data.

- [ ] **Step 5: Run fresh ASH-06 and stability only if the existing runner is available.**

Run three independent ASH-06 trials and the minimum ten-run stability gate using the existing runner/model configuration. Report every required dimension. If the runner or model is unavailable, report the exact environment limitation and keep PR #14 Draft/HOLD; do not convert old reports into fresh evidence.

- [ ] **Step 6: Inspect final diff and report without commit/push.**

Re-run `git status --short --branch`, `git diff --stat`, `git diff --name-only`, and `git ls-files --others --exclude-standard`. Confirm all pre-existing dirty files remain, no forbidden commands were used, and no commit/push occurred. Final decision may be `RUNTIME_ENFORCEMENT_PASS` only if every release gate passes; otherwise use `RUNTIME_ENFORCEMENT_FAIL` or `BLOCKED_BY_RUNTIME_CAPABILITY` according to the evidence.
