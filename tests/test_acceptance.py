import json
import unittest
from pathlib import Path

from src.answer import parse_model_json
from src.evaluate import evaluate_answer
from src.experiment import compare_retrievers, summarize_retrieval
from src.judge import JUDGE_MODELS, parse_judge_bundle
from src.search import gated_section_search, section_search, whole_article_search


ROOT = Path(__file__).resolve().parents[1]
CORPUS = json.loads((ROOT / "data" / "corpus.json").read_text())
CASES = json.loads((ROOT / "data" / "cases.json").read_text())
GATES = json.loads((ROOT / "data" / "gates.json").read_text())


class AcceptanceTests(unittest.TestCase):
    def test_section_search_finds_exact_instruction(self):
        result = section_search("stop my plan from renewing", CORPUS)
        self.assertEqual(result[0]["section_id"], "subscription-cancel")

    def test_whole_article_control_returns_one_section_per_article(self):
        result = whole_article_search("order still processing", CORPUS)
        self.assertEqual(len({row["article_id"] for row in result}), len(result))

    def test_configured_safety_gate_requires_reviewed_section(self):
        result = gated_section_search("That login request was not me", CORPUS, GATES)
        self.assertEqual(result[0]["section_id"], "account-unrecognized-login")

    def test_paired_comparison_and_summary(self):
        rows = compare_retrievers(CASES, CORPUS)
        self.assertEqual({row["case_id"] for row in rows}, {case["case_id"] for case in CASES})
        self.assertEqual(summarize_retrieval(rows)["cases"], len(CASES))

    def test_answer_contract_checks_route_citation_and_claims(self):
        case = CASES[4]
        answer = {
            "answer": "Processing can take up to two business days.",
            "citations": ["delivery-pending"],
            "next_step": "Check the order page.",
            "route": "answer",
        }
        self.assertTrue(evaluate_answer(case, answer, {"delivery-pending"})["pass"])

    def test_fenced_json_is_accepted(self):
        self.assertEqual(parse_model_json('```json\n{"route":"answer"}\n```')["route"], "answer")

    def test_two_judge_models_are_fixed(self):
        self.assertEqual(JUDGE_MODELS, ("anthropic/claude-haiku-4.5", "qwen/qwen3.8-27b"))

    def test_incomplete_judge_bundle_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "sop_adherence"):
            parse_judge_bundle(json.dumps({
                "source_of_truth": {
                    "pass": True,
                    "score": 1.0,
                    "failure_type": None,
                    "exact_failure_span": None,
                    "rationale": "Grounded.",
                    "safer_requirement": "None.",
                    "confidence": "high",
                }
            }))


if __name__ == "__main__":
    unittest.main()
