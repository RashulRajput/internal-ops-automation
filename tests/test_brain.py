import unittest

from app.brain import answer_question, chunk_text, leave_analysis, meeting_summary, ticket_classification


class BrainTests(unittest.TestCase):
    def test_ticket_classification(self):
        result = ticket_classification("VPN failed", "The remote team cannot work because VPN access is blocked")
        self.assertEqual(result["category"], "it_support")
        self.assertIn(result["priority"], {"high", "critical"})
        self.assertEqual(result["assigned_to"], "IT Helpdesk")

    def test_leave_analysis(self):
        result = leave_analysis({"leave_type": "annual", "start_date": "2026-06-15", "end_date": "2026-06-20"})
        self.assertEqual(result["total_days"], 6)
        self.assertIn(result["recommendation"], {"approved", "review"})

    def test_meeting_summary(self):
        result = meeting_summary("Rahul: Decision made. Neha: I will finish the design by Friday.")
        self.assertTrue(result["key_decisions"])
        self.assertTrue(result["action_items"])

    def test_document_answer(self):
        chunks = chunk_text("Annual leave requires seven days notice. Sick leave can be filed same day.")
        result = answer_question("How much notice for annual leave?", [{"name": "Leave Policy", "chunks": chunks}])
        self.assertIn("Annual leave", result["answer"])
        self.assertTrue(result["sources"])


if __name__ == "__main__":
    unittest.main()
