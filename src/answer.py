import json

from .evaluate import evaluate_answer, summarize_answers
from .openrouter import post_json


MODEL = "anthropic/claude-haiku-4.5"
MAX_COST_USD = 1.0
SYSTEM_PROMPT = """Answer support questions using only the supplied source sections.
Return JSON only with this exact shape:
{"answer":"short direct answer","citations":["section-id"],"next_step":"one concrete step","route":"answer|clarify|virtual_assistant|human","rationale":"one sentence"}

Rules:
- Cite only supplied section IDs.
- Preserve numbers, limits, timing, and safety warnings exactly.
- Do not promise an outcome, eligibility, timing, refund, or account action unless a source states it.
- Use route=answer when the evidence fully answers the question.
- Use route=clarify when one missing customer fact selects between documented paths.
- Use route=virtual_assistant when authenticated account-state lookup is needed without human judgment.
- Use route=human for compromise, recovery, or a documented instruction to contact support.
"""


def parse_model_json(content):
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    if not text:
        raise ValueError("Model returned empty content")
    return json.loads(text)


def call_answer(api_key, case, evidence):
    sources = [
        {key: row[key] for key in ("section_id", "article_title", "locale", "heading", "text")}
        for row in evidence
    ]
    body = post_json(api_key, "chat/completions", {
        "model": MODEL,
        "temperature": 0,
        "max_tokens": 320,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps({"question": case["question"], "sources": sources})},
        ],
    })
    answer = parse_model_json(body["choices"][0]["message"]["content"])
    usage = body.get("usage", {})
    return answer, {
        "generation_id": body.get("id"),
        "model": body.get("model", MODEL),
        "prompt_tokens": int(usage.get("prompt_tokens", 0)),
        "completion_tokens": int(usage.get("completion_tokens", 0)),
        "cost_usd": round(float(usage.get("cost", 0)), 8),
    }


def run_answers(api_key, cases, retriever):
    rows = []
    total_cost = 0.0
    for case in cases:
        evidence = retriever(case["question"])
        answer, usage = call_answer(api_key, case, evidence)
        total_cost += usage["cost_usd"]
        if total_cost > MAX_COST_USD:
            raise RuntimeError("Answer run exceeded the $1 cost cap")
        grade = evaluate_answer(case, answer, {row["section_id"] for row in evidence})
        rows.append({"case_id": case["case_id"], "answer": answer, "evidence": [row["section_id"] for row in evidence], "usage": usage, "grade": grade})
    summary = summarize_answers([row["grade"] for row in rows])
    summary.update({"model": MODEL, "cost_usd": round(total_cost, 6)})
    return rows, summary
