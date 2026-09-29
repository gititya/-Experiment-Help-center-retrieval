import json

from .answer import parse_model_json
from .openrouter import post_json


JUDGE_MODELS = ("anthropic/claude-haiku-4.5", "qwen/qwen3.8-27b")
VERDICT_FIELDS = {"pass", "score", "failure_type", "exact_failure_span", "rationale", "safer_requirement", "confidence"}
QUALITY_JUDGES = {
    "source_of_truth": "Fail when the answer ignores supplied context, guesses, fabricates, or extends policy beyond the evidence.",
    "sop_adherence": "Fail when any required step in expected_process is missing, incomplete, unsupported, or out of order.",
    "unsupported_promise": "Fail when the answer promises a timeline, outcome, fix, refund, escalation, or guarantee without evidence or authority.",
}


def parse_judge_bundle(content):
    bundle = parse_model_json(content)
    for judge_id in QUALITY_JUDGES:
        if judge_id not in bundle:
            raise ValueError(f"Missing judge verdict: {judge_id}")
        missing = VERDICT_FIELDS - set(bundle[judge_id])
        if missing:
            raise ValueError(f"Missing {judge_id} fields: {sorted(missing)}")
    return bundle


def call_judges(api_key, model, case, answer, evidence):
    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": 900,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": json.dumps({
            "instructions": QUALITY_JUDGES,
            "ticket": case["question"],
            "agent_response": answer,
            "policy_context": evidence,
            "expected_process": case["expected_process"],
            "required_output": {
                judge_id: {field: "required" for field in VERDICT_FIELDS}
                for judge_id in QUALITY_JUDGES
            },
            "rule": "Judge each dimension separately. Return one valid JSON object only.",
        })}],
    }
    if model.startswith("qwen/"):
        payload["reasoning"] = {"enabled": False}
    body = post_json(api_key, "chat/completions", payload)
    raw = body["choices"][0]["message"].get("content")
    if not raw:
        raise RuntimeError(f"Judge returned no content for {model}")
    usage = body.get("usage", {})
    return parse_judge_bundle(raw), raw, {
        "generation_id": body.get("id"),
        "model": body.get("model", model),
        "cost_usd": round(float(usage.get("cost", 0)), 8),
    }
