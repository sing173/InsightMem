import json
import tempfile
import unittest
from pathlib import Path

from email_memory_lab import (
    AgentConfig,
    EmailAgent,
    LocalStore,
    evaluate_config,
    load_labeled_emails,
    seed_memories,
    start_run,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class EmailMemoryLabTests(unittest.TestCase):
    def setUp(self):
        self.cases = load_labeled_emails(PROJECT_ROOT / "data" / "emails.json")
        self.store = LocalStore()
        seed_memories(self.store, PROJECT_ROOT / "data" / "memories.json", "user-a")
        self.by_id = {case.email.id: case for case in self.cases}

    def evaluate(self, config):
        return evaluate_config(self.cases, self.store, "user-a", config)

    def test_baseline_exposes_memory_failures(self):
        summary = self.evaluate(AgentConfig())["summary"]
        self.assertEqual(summary["routing_accuracy"], {"passed": 8, "total": 10, "value": 0.8})
        self.assertEqual(summary["writing_compliance"], {"passed": 0, "total": 4, "value": 0.0})
        self.assertEqual(summary["required_memory_recall"], {"passed": 0, "total": 6, "value": 0.0})

    def test_semantic_memory_adds_signature(self):
        result = EmailAgent(self.store, "user-a", AgentConfig(use_semantic=True)).handle(
            self.by_id["docs-question"].email
        )
        self.assertEqual(result.action, "respond")
        self.assertIn("John Doe", result.response)
        self.assertIn("semantic:signature", result.used_memory)

    def test_episodic_memory_routes_vendor_outreach(self):
        result = EmailAgent(self.store, "user-a", AgentConfig(use_episodic=True)).handle(
            self.by_id["vendor-pricing"].email
        )
        self.assertEqual(result.action, "ignore")
        self.assertIn("episodic:vendor-documentation-pricing", result.used_memory)

    def test_procedural_memory_routes_event_invites(self):
        result = EmailAgent(self.store, "user-a", AgentConfig(use_procedural=True)).handle(
            self.by_id["event-invite"].email
        )
        self.assertEqual(result.action, "ignore")
        self.assertIn("procedural:email-style", result.used_memory)

    def test_full_config_passes_all_cases(self):
        result = self.evaluate(AgentConfig(True, True, True))
        self.assertEqual(result["summary"]["routing_accuracy"]["passed"], 10)
        self.assertEqual(result["summary"]["writing_compliance"]["passed"], 4)
        self.assertEqual(result["summary"]["required_memory_recall"]["passed"], 6)
        self.assertEqual(result["failures"], [])

    def test_user_memory_is_isolated(self):
        isolated_store = LocalStore()
        seed_memories(isolated_store, PROJECT_ROOT / "data" / "memories.json", "user-b")
        result = EmailAgent(isolated_store, "user-b", AgentConfig(use_semantic=True)).handle(
            self.by_id["docs-question"].email
        )
        self.assertIn("Jane Smith", result.response)
        self.assertNotIn("John Doe", result.response)

    def test_runner_saves_manifest_and_results(self):
        with tempfile.TemporaryDirectory() as temporary:
            run = start_run(temporary, "test-run", {"config": "baseline"})
            results = self.evaluate(AgentConfig())
            path = run.save("results.json", results)
            manifest = json.loads((run.directory / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["run_name"], "test-run")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["summary"], results["summary"])
            with self.assertRaises(ValueError):
                run.save("../escape.json", {})


if __name__ == "__main__":
    unittest.main()