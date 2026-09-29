import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DatasetTests(unittest.TestCase):
    def test_labels_exist_and_routes_are_valid(self):
        corpus = json.loads((ROOT / "data" / "corpus.json").read_text())
        cases = json.loads((ROOT / "data" / "cases.json").read_text())
        article_ids = {article["article_id"] for article in corpus}
        section_ids = {section["section_id"] for article in corpus for section in article["sections"]}
        self.assertEqual(len({case["case_id"] for case in cases}), len(cases))
        for case in cases:
            self.assertIn(case["expected_article_id"], article_ids)
            self.assertIn(case["expected_section_id"], section_ids)
            self.assertIn(case["expected_route"], {"answer", "clarify", "virtual_assistant", "human"})

    def test_content_gaps_stay_separate(self):
        gaps = json.loads((ROOT / "data" / "content-gap-cases.json").read_text())
        self.assertTrue(gaps)
        self.assertTrue(all(case["topic"] == "content_gap" for case in gaps))
        self.assertTrue(all("expected_section_id" not in case for case in gaps))


if __name__ == "__main__":
    unittest.main()
