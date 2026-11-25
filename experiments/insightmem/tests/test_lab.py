import json
import tempfile
import unittest
from pathlib import Path

from insightmem.store import MemoryMessage
from insightmem_lab import start_experiment


class ExperimentRunTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_round_trip_saves_manifest_and_results(self):
        run = start_experiment(self.root, "round-trip")
        messages = [MemoryMessage(role="user", content="The parser drops backslashes.")]
        stored = run.add("request-1", "user-a", "session-1", messages)
        hits = run.search("user-a", "parser backslashes", top_k=3)
        result_path = run.save("results.json", {"stored_chunks": stored, "hits": hits})

        self.assertGreater(stored, 0)
        self.assertTrue(hits)
        self.assertIn(messages[0].content, hits[0]["content"])
        self.assertTrue(run.database_path.is_file())
        self.assertTrue((run.directory / "manifest.json").is_file())
        self.assertEqual(json.loads(result_path.read_text(encoding="utf-8"))["hits"], hits)

    def test_replay_is_idempotent_and_users_are_isolated(self):
        run = start_experiment(self.root, "isolation")
        message_a = [MemoryMessage(role="user", content="User A prefers concise replies.")]
        message_b = [MemoryMessage(role="user", content="B-ONLY-SENTINEL is visible to user B.")]

        first = run.add("request-a", "user-a", "session-a", message_a)
        replay = run.add("request-a", "user-a", "session-a", message_a)
        run.add("request-b", "user-b", "session-b", message_b)

        self.assertEqual(first, replay)
        self.assertFalse(any("B-ONLY-SENTINEL" in hit["content"] for hit in run.search("user-a", "B-ONLY-SENTINEL")))
        self.assertTrue(any("B-ONLY-SENTINEL" in hit["content"] for hit in run.search("user-b", "B-ONLY-SENTINEL")))
        self.assertEqual(run.stats()["requests"], 2)
        self.assertEqual(run.stats()["users"], 2)

    def test_save_rejects_nested_paths(self):
        run = start_experiment(self.root, "safe-output")
        with self.assertRaises(ValueError):
            run.save("../escape.json", {})


if __name__ == "__main__":
    unittest.main()
