import csv
import hashlib
import json
from pathlib import Path

from .search import section_search, whole_article_search


def load_json(path):
    return json.loads(Path(path).read_text())


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compare_retrievers(cases, corpus):
    rows = []
    for case in cases:
        whole = whole_article_search(case["question"], corpus)
        section = section_search(case["question"], corpus)
        rows.append({
            "case_id": case["case_id"],
            "topic": case.get("topic"),
            "question": case["question"],
            "expected_article_id": case["expected_article_id"],
            "expected_section_id": case["expected_section_id"],
            "whole_article_hit_at_3": case["expected_article_id"] in {row["article_id"] for row in whole},
            "whole_section_hit_at_3": case["expected_section_id"] in {row["section_id"] for row in whole},
            "section_article_hit_at_3": case["expected_article_id"] in {row["article_id"] for row in section},
            "section_hit_at_3": case["expected_section_id"] in {row["section_id"] for row in section},
            "whole_results": [row["section_id"] for row in whole],
            "section_results": [row["section_id"] for row in section],
        })
    return rows


def summarize_retrieval(rows):
    if not rows:
        raise ValueError("At least one labelled case is required")
    total = len(rows)
    whole = sum(row["whole_section_hit_at_3"] for row in rows)
    section = sum(row["section_hit_at_3"] for row in rows)
    fixed = sum(row["section_hit_at_3"] and not row["whole_section_hit_at_3"] for row in rows)
    regressions = sum(row["whole_section_hit_at_3"] and not row["section_hit_at_3"] for row in rows)
    return {
        "cases": total,
        "whole_section_hits": whole,
        "whole_section_hit_rate": round(whole / total, 4),
        "section_hits": section,
        "section_hit_rate": round(section / total, 4),
        "cases_fixed": fixed,
        "retrieval_regressions": regressions,
        "net_improvement": fixed - regressions,
        "decision": "keep" if fixed / total >= 0.2 and not regressions else "selective" if fixed > regressions else "drop",
    }


def write_retrieval_results(rows, summary, output_dir):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "retrieval-results.json").write_text(json.dumps({"summary": summary, "cases": rows}, indent=2) + "\n")
    columns = list(rows[0])
    with (output / "retrieval-results.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "whole_results": "|".join(row["whole_results"]), "section_results": "|".join(row["section_results"])})
