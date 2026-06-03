import tempfile
import unittest
from pathlib import Path

from app.brain import ticket_classification
from app.store import Store


class StoreTests(unittest.TestCase):
    def test_ticket_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "ops.db")
            payload = {
                "title": "Payroll issue",
                "description": "Salary is lower than expected",
                "submitter_name": "Priya",
                "submitter_email": "priya@example.com"
            }
            ticket = store.create_ticket(payload, ticket_classification(payload["title"], payload["description"]))
            self.assertEqual(ticket["id"], 1)
            self.assertEqual(store.ticket_metrics()["total"], 1)


if __name__ == "__main__":
    unittest.main()
