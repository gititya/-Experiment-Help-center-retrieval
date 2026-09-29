import re


VALID_ROUTES = {"answer", "clarify", "virtual_assistant", "human"}


def _normalize(text):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9@'-]+", " ", text.lower())).strip()


def evaluate_answer(case, answer, allowed_citations):
    combined = _normalize(f'{answer.get("answer", "")} {answer.get("next_step", "")}')
    missing = [
        alternatives
        for alternatives in case.get("required_facts", [])
        if not any(_normalize(alternative) in combined for alternative in alternatives)
    ]
    forbidden = [claim for claim in case.get("forbidden_claims", []) if _normalize(claim) in combined]
    citations = answer.get("citations") or []
    citations_ok = bool(citations) and set(citations).issubset(set(allowed_citations))
    route = answer.get("route")
    route_ok = route in VALID_ROUTES and route == case["expected_route"]
    avoidable = case["expected_route"] == "answer" and route == "virtual_assistant" and not missing
    return {
        "case_id": case["case_id"],
        "facts_ok": not missing,
        "missing_facts": missing,
        "citations_ok": citations_ok,
        "invalid_citations": sorted(set(citations) - set(allowed_citations)),
        "route_ok": route_ok,
        "expected_route": case["expected_route"],
        "actual_route": route,
        "avoidable_assistant_escalation": avoidable,
        "safety_ok": not forbidden,
        "forbidden_claims_found": forbidden,
        "pass": not missing and citations_ok and route_ok and not forbidden and not avoidable,
    }


def summarize_answers(grades):
    total = len(grades)
    passes = sum(grade["pass"] for grade in grades)
    return {
        "cases": total,
        "passes": passes,
        "pass_rate": round(passes / total, 4) if total else 0,
        "critical_unsupported_claims": sum(not grade["safety_ok"] for grade in grades),
        "avoidable_assistant_escalations": sum(grade["avoidable_assistant_escalation"] for grade in grades),
    }
