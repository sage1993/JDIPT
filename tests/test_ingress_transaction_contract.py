from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.material_obligation_ingress import record_material_obligation_ledger
from scripts.material_obligation_ledger import MaterialObligationLedger
from scripts.proposition_registry import RegistryService


class IngressTransactionContractTests(unittest.TestCase):
    def test_ingress_accepts_transaction_owned_registry_write(self):
        ledger = MaterialObligationLedger.from_mapping(
            {
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
        )
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "synthesis-runtime").mkdir()
            RegistryService(root).create("tx-1")
            registry = record_material_obligation_ledger(
                {
                    "transaction_id": "tx-1",
                    "material_obligation_ledger": ledger,
                },
                root,
            )
            self.assertEqual(registry.transaction_id, "tx-1")
            self.assertEqual(registry.ledger, ledger)


if __name__ == "__main__":
    unittest.main()
