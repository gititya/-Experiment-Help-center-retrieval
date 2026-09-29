import json
import urllib.error
import urllib.request


def post_json(api_key, path, payload, timeout=90):
    request = urllib.request.Request(
        f"https://openrouter.ai/api/v1/{path}",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://local.support-retrieval-experiment.invalid",
            "X-Title": "Support retrieval experiment",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:500]
        raise RuntimeError(f"OpenRouter request failed ({error.code}): {detail}") from error
