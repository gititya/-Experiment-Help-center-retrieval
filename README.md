# Support retrieval experiment shell

A vendor-neutral starting point for testing whether section-level support search beats whole-article search, then checking whether an answer model stays grounded and routes customers safely.

It includes:

- a fixed whole-article control and section-search change;
- configurable safety gates;
- required-fact, citation, route, and forbidden-claim checks;
- optional OpenRouter answer, reranker, and dual-model judge stages;
- separate content-gap cases;
- input hashes, TDD receipts, and a walkthrough template.

The included corpus and cases are fictional examples. Replace them before using the shell for a real company or product.

## Start a new experiment

1. Copy or rename this repo.
2. Replace the four files in `data/`.
3. Write the question, acceptance receipts, thresholds, and limits in `docs/experiment-spec.md` before running results.
4. Add or change tests first and save the failing run in `evidence/`.
5. Run the deterministic control:

```bash
python3 run_experiment.py
python3 -m unittest discover -s tests -v
```

6. Review retrieval failures before enabling any model stage.
7. Load a scoped `OPENROUTER_API_KEY` only for the process that needs it, then run the requested live stage:

```bash
python3 run_experiment.py --with-rerank
python3 run_experiment.py --with-ai
python3 run_closing_eval.py
```

8. Review model disagreements, write the one-page result in `docs/walkthrough.md`, and stop when the fixed decision rule is answered.

## Data contracts

- `corpus.json`: articles with `article_id`, `title`, `locale`, `source_url`, `captured_at`, and heading-based `sections`.
- `cases.json`: answerable questions with expected article, section, route, required facts, and forbidden claims.
- `content-gap-cases.json`: questions that require account state, policy not in the corpus, or human judgment.
- `gates.json`: query phrases that require or exclude specific sections before an answer is drafted.

## Evidence boundary

The shell proves only that the experiment can run. New fixtures, thresholds, model behavior, source terms, and customer-language realism must be checked for each use.
