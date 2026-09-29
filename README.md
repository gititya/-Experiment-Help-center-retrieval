# Help Center Retrieval Experiment

A small test for one question: does searching individual Help Center sections surface the useful instruction more often than searching whole articles first?

The repo also checks whether an AI answer stays grounded, uses valid citations, avoids unsupported promises, and chooses the right support route.

The included articles and questions are fictional examples.

## Run it

```bash
python3 run_experiment.py
python3 -m unittest discover -s tests -v
```

This uses only Python's standard library.

## Use your own Help Center

Replace the example files in `data/`:

- `corpus.json`: Help articles split into sections.
- `cases.json`: answerable customer questions and expected results.
- `content-gap-cases.json`: questions the public content cannot answer.
- `gates.json`: safety rules that require specific sections.

Set the experiment question and decision rule in `docs/experiment-spec.md` before running it.

## Optional AI stages

Load `OPENROUTER_API_KEY` for the current process, then run:

```bash
python3 run_experiment.py --with-rerank
python3 run_experiment.py --with-ai
python3 run_closing_eval.py
```

Raw model output stays local. Review disagreements manually before treating any AI judge result as correct.
