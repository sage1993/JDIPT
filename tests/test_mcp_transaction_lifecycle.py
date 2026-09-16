from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.jdipt_runtime_mcp import (
    begin_runtime_turn,
    register_material_proposition,
    submit_material_obligation_ledger,
)
from scripts.turn_anchor import create_turn_anchor


class McpTransactionLifecycleTests(unittest.TestCase):
    def test_issued_capability_survives_ledger_and_proposition_handoff(self):
        ledger = {
            "obligations": [
                {
                    "obligation_id": "ob-1",
                    "issue_type": "source",
                    "source_status": "SOURCE_UNRESOLVED",
                    "proposition_ids": ["p-1"],
                }
            ],
            "verified_source_evidence": [],
        }
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "synthesis-runtime").mkdir()
            create_turn_anchor(root)
            begun = begin_runtime_turn(root)
            capability = begun["turn_capability"]
            self.assertTrue(capability)
            self.assertEqual(
                submit_material_obligation_ledger(capability, ledger, root)["state"],
                "LEDGER_RECORDED",
            )
            result = register_material_proposition(
                capability,
                {
                    "proposition_id": "p-1",
                    "status": "OPEN",
                    "materiality": "MATERIAL",
                },
                root,
            )
            self.assertEqual(result["proposition_id"], "p-1")


if __name__ == "__main__":
    unittest.main()
