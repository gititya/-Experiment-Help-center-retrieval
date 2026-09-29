import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ResultTests(unittest.TestCase):
    def test_manifest_hashes_match_inputs(self):
        manifest = json.loads((ROOT / "results" / "run-manifest.json").read_text())
        for key, filename in (("corpus_sha256", "corpus.json"), ("cases_sha256", "cases.json"), ("gates_sha256", "gates.json")):
            digest = hashlib.sha256((ROOT / "data" / filename).read_bytes()).hexdigest()
            self.assertEqual(manifest[key], digest)

    def test_retrieval_results_cover_all_cases(self):
        cases = json.loads((ROOT / "data" / "cases.json").read_text())
        results = json.loads((ROOT / "results" / "retrieval-results.json").read_text())
        self.assertEqual({case["case_id"] for case in cases}, {row["case_id"] for row in results["cases"]})


if __name__ == "__main__":
    unittest.main()
