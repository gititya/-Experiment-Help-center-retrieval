# Support retrieval experiment

- Use Python's standard library only.
- Treat `data/corpus.json`, `data/cases.json`, `data/content-gap-cases.json`, and `data/gates.json` as replaceable examples until an experiment is frozen.
- Once a run starts, do not change frozen inputs, labels, thresholds, or decision rules after seeing results.
- Keep content-gap cases separate from answerable cases.
- Do not add real customer data, complaint narratives, secrets, or internal claims.
- Keep raw model output local and ignored; commit only evaluated, redacted results.
- Never store an API key in this repository.
- Record model disagreements for human review; no model judge gets the final say.
