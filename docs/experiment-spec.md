# Experiment spec

Status: template

## Question

Does searching heading-based support sections surface the exact useful instruction more often than searching whole articles first?

## Customer problem

Replace this with the concrete customer friction and why it matters.

## Control and change

- Control: rank whole articles, then choose the best section inside each top article.
- Change: rank all sections directly.
- Fixed in both: corpus, cases, tokenizer, score, top-three limit, and labels.

## Measures

- Main: expected section appears in the first three results.
- Secondary: correct article, answer completeness, citation validity, route, unsupported claims, and avoidable escalation.

## Acceptance receipts

1. The paired comparison uses the same case and frozen inputs for both retrievers.
2. A complete public answer must not be escalated to an assistant merely because the model is uncertain.
3. Missing source facts must not be invented.
4. A required safety section must be present before drafting.
5. Model-judge disagreements require human review.

## Decision rule

Replace these example thresholds before the run:

- Keep the change if it fixes at least 20% of cases and creates no unsafe regression.
- Restrict it if it improves one topic but regresses another.
- Drop it if it creates an unsafe result or fails to improve retrieval.

## Limits

- Synthetic questions are not live customer demand.
- A small corpus is not the full help centre.
- Offline accuracy is not resolution, CSAT, or contact reduction.
- Public availability is not permission to republish source content.
