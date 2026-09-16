import tempfile
import unittest
from pathlib import Path

from scripts.inject_registry_runtime import handle_pre_tool_use
from scripts.jdipt_activation import handle_user_prompt_submit
from scripts.jdipt_runtime_mcp import begin_runtime_turn
from scripts.stop_synthesis_gate import handle_stop_event
from scripts.turn_anchor import load_current_turn_anchor
from scripts.turn_anchor import create_turn_anchor


class NativeHookContractTests(unittest.TestCase):
    def test_pre_tool_use_does_not_inject_legacy_arguments_into_capability_tool(self):
        with tempfile.TemporaryDirectory() as raw:
            result = handle_pre_tool_use(
                {
                    "tool_name": "mcp__jdipt_runtime__register_material_proposition",
                    "session_id": "legacy-session",
                    "turn_id": "legacy-turn",
                    "tool_input": {
                        "turn_capability": "jtc_server_issued",
                        "proposition": {},
                    },
                },
                raw,
            )

        output = result["hookSpecificOutput"]
        self.assertEqual(output["permissionDecision"], "allow")
        self.assertNotIn("updatedInput", output)

    def test_user_prompt_submit_creates_the_current_turn_anchor(self):
        with tempfile.TemporaryDirectory() as raw:
            result = handle_user_prompt_submit(
                {
                    "prompt": "$law-interpretation-request 요건을 검토해줘.",
                },
                raw,
            )

            self.assertEqual(result, {})
            anchor = load_current_turn_anchor(Path(raw))
            self.assertEqual(anchor.epoch, 1)
            self.assertEqual(anchor.state, "AVAILABLE")

    def test_stop_rejects_an_unfinalized_canonical_transaction(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            create_turn_anchor(root)
            begin_runtime_turn(root)

            result = handle_stop_event(
                {
                    "last_assistant_message": (
                        "# 1. 질의요지\n\n# 2. 검토결론\n\n"
                        "# 3. 검토이유\n\n# 4. 관련 법령 및 자료"
                    ),
                },
                raw,
            )

        self.assertFalse(result["continue"])
        self.assertIn("finalized", result["systemMessage"])
