# Test-driven experiment process

1. State the customer problem in plain language.
2. Write the control, change, fixed inputs, main measure, and decision rule.
3. Write acceptance tests before implementation or model calls.
4. Run them once and save the expected failure in `evidence/tdd-red.txt`.
5. Freeze the corpus, answerable cases, content-gap cases, gates, and thresholds.
6. Run deterministic retrieval first.
7. Inspect misses and safety cases before adding an answer model.
8. If AI is useful, give it only retrieved evidence and cap spend.
9. Run separate grounding, process, and unsupported-promise judges through two models.
10. Preserve disagreements and review them manually.
11. Write what passed, failed, and was not tested. Stop at the decision rule.
