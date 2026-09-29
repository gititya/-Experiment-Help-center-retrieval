import json
import os
from pathlib import Path

from src.answer import MODEL as ANSWER_MODEL, call_answer
from src.judge import JUDGE_MODELS, QUALITY_JUDGES, call_judges
from src.rerank import MODEL as RERANKER_MODEL, rerank_sections


ROOT = Path(__file__).resolve().parent
MAX_TOTAL_COST_USD = 1.0


def load(path):
    return json.loads((ROOT / path).read_text())


def expected_process(case):
    steps = [
        "Include one supported form of each required fact: "
        + " AND ".join(" OR ".join(options) for options in case["required_facts"]),
        f'Return route={case["expected_route"]}.',
    ]
    if case["forbidden_claims"]:
        steps.insert(1, "Do not state: " + "; ".join(case["forbidden_claims"]))
    return steps


def main():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    corpus = load("data/corpus.json")
    cases = load("data/cases.json") + load("data/content-gap-cases.json")
    raw_dir = ROOT / "artifacts" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    total_cost = 0.0
    for source_case in cases:
        case = dict(source_case)
        if "expected_process" not in case:
            case["expected_process"] = expected_process(case)
        evidence, rerank_usage = rerank_sections(api_key, case["question"], corpus)
        answer, answer_usage = call_answer(api_key, case, evidence)
        judges = {}
        total_cost += rerank_usage["cost_usd"] + answer_usage["cost_usd"]
        for model in JUDGE_MODELS:
            verdicts, raw, usage = call_judges(api_key, model, case, answer, evidence)
            total_cost += usage["cost_usd"]
            (raw_dir / f'{case["case_id"]}-{model.replace("/", "-")}.txt').write_text(raw + "\n")
            judges[model] = {"verdicts": verdicts, "usage": usage}
        if total_cost > MAX_TOTAL_COST_USD:
            raise RuntimeError("Closing evaluation exceeded the $1 cost cap")
        disagreements = [
            judge_id for judge_id in QUALITY_JUDGES
            if len({judges[model]["verdicts"][judge_id]["pass"] for model in JUDGE_MODELS}) > 1
        ]
        route_ok = answer.get("route") == case["expected_route"]
        rows.append({
            "case_id": case["case_id"],
            "topic": case["topic"],
            "question": case["question"],
            "expected_route": case["expected_route"],
            "evidence": [row["section_id"] for row in evidence],
            "answer": answer,
            "judges": judges,
            "judge_disagreements": disagreements,
            "route_ok": route_ok,
            "dual_model_pass": route_ok and all(
                judges[model]["verdicts"][judge_id]["pass"]
                for model in JUDGE_MODELS for judge_id in QUALITY_JUDGES
            ),
        })
    summary = {
        "cases": len(rows),
        "answer_model": ANSWER_MODEL,
        "reranker_model": RERANKER_MODEL,
        "judge_models": list(JUDGE_MODELS),
        "route_passes": sum(row["route_ok"] for row in rows),
        "dual_model_passes": sum(row["dual_model_pass"] for row in rows),
        "disagreement_cases": sum(bool(row["judge_disagreements"]) for row in rows),
        "cost_usd": round(total_cost, 6),
        "decision": "human_review_required" if any(row["judge_disagreements"] for row in rows) else "review_complete",
    }
    (ROOT / "results" / "closing-eval.json").write_text(json.dumps({"summary": summary, "cases": rows}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
