# Verification

Date: 2026-09-29

- The first test run failed before `src/` and result files existed; see `tdd-red.txt`.
- The deterministic example run completed with three articles, six sections, and six labelled cases.
- Both retrievers scored 6/6 on the fictional fixture, so the example decision is `drop`: the change adds no measured value when the control already works.
- Twelve tests passed for pairing, retrieval, configurable gates, answer checks, judge parsing, dataset labels, result coverage, and frozen-input hashes.
- The repository contains no source-company names, data, URLs, labels, results, or claims.
- Security and protected-file checks passed.
- Live OpenRouter stages are implemented but were not run in this generic shell.
