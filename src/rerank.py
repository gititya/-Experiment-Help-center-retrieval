from .openrouter import post_json
from .search import section_rows


MODEL = "qwen/qwen3-reranker-8b"
MAX_COST_USD = 1.0


def rerank_sections(api_key, query, corpus, limit=3):
    rows = section_rows(corpus)
    documents = [f'{row["article_title"]}\n{row["heading"]}\n{row["text"]}' for row in rows]
    body = post_json(api_key, "rerank", {"model": MODEL, "query": query, "documents": documents, "top_n": limit})
    ranked = [{**rows[item["index"]], "relevance_score": item["relevance_score"]} for item in body["results"]]
    return ranked, {
        "provider": body.get("provider"),
        "cost_usd": float(body.get("usage", {}).get("cost", 0)),
    }


def run_rerank(api_key, cases, corpus):
    rows = []
    total_cost = 0.0
    for case in cases:
        ranked, usage = rerank_sections(api_key, case["question"], corpus)
        total_cost += usage["cost_usd"]
        if total_cost > MAX_COST_USD:
            raise RuntimeError("Rerank run exceeded the $1 cost cap")
        rows.append({
            "case_id": case["case_id"],
            "expected_section_id": case["expected_section_id"],
            "hit_at_3": case["expected_section_id"] in {row["section_id"] for row in ranked},
            "results": [row["section_id"] for row in ranked],
            "usage": usage,
        })
    return rows, {"model": MODEL, "cases": len(rows), "hits": sum(row["hit_at_3"] for row in rows), "cost_usd": round(total_cost, 6)}
