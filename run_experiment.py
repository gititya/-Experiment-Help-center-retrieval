import argparse
import json
import os
from datetime import date
from pathlib import Path

from src.answer import run_answers
from src.experiment import compare_retrievers, file_sha256, load_json, summarize_retrieval, write_retrieval_results
from src.rerank import run_rerank
from src.search import gated_section_search


ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-ai", action="store_true")
    parser.add_argument("--with-rerank", action="store_true")
    args = parser.parse_args()

    corpus_path = ROOT / "data" / "corpus.json"
    cases_path = ROOT / "data" / "cases.json"
    gates_path = ROOT / "data" / "gates.json"
    corpus = load_json(corpus_path)
    cases = load_json(cases_path)
    gates = load_json(gates_path)
    rows = compare_retrievers(cases, corpus)
    summary = summarize_retrieval(rows)
    write_retrieval_results(rows, summary, ROOT / "results")
    manifest = {
        "run_date": date.today().isoformat(),
        "corpus_sha256": file_sha256(corpus_path),
        "cases_sha256": file_sha256(cases_path),
        "gates_sha256": file_sha256(gates_path),
        "corpus_articles": len(corpus),
        "corpus_sections": sum(len(article["sections"]) for article in corpus),
        "cases": len(cases),
        "retrieval": summary,
    }

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if args.with_rerank:
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")
        result_rows, result_summary = run_rerank(api_key, cases, corpus)
        (ROOT / "results" / "rerank-results.json").write_text(json.dumps({"summary": result_summary, "cases": result_rows}, indent=2) + "\n")
        manifest["rerank"] = result_summary
    if args.with_ai:
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")
        retriever = lambda question: gated_section_search(question, corpus, gates)
        result_rows, result_summary = run_answers(api_key, cases, retriever)
        (ROOT / "results" / "ai-results.json").write_text(json.dumps({"summary": result_summary, "cases": result_rows}, indent=2) + "\n")
        manifest["answers"] = result_summary

    (ROOT / "results" / "run-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
