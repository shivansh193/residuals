"""Minimal Gemini REST client.

Free-tier quotas are per model and small, so calls fall back through a list of models:
a daily-quota 429 moves to the next model at once; 503/500 and per-minute 429s retry with backoff.
"""
import json, os, time
import requests

URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODELS = "gemini-3.5-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-2.5-flash,gemini-2.5-flash-lite"
_dead = {}  # model -> time its daily quota ran out


class GeminiError(Exception):
    pass


def models():
    ms = os.environ.get("GEMINI_MODELS") or (os.environ.get("GEMINI_MODEL", "") + "," + DEFAULT_MODELS)
    seen, out = set(), []
    for m in ms.split(","):
        m = m.strip()
        if m and m not in seen and time.time() - _dead.get(m, 0) > 3600:
            seen.add(m)
            out.append(m)
    return out


def generate_json(prompt, schema=None, retries=2, timeout=60, parts=None):
    body = {"contents": [{"parts": (parts or []) + [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}
    if schema:
        body["generationConfig"]["responseSchema"] = schema
    errors = []
    for model in models():
        for i in range(retries):
            try:
                r = requests.post(URL.format(model=model), json=body, timeout=timeout,
                                  headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]})
            except requests.RequestException as e:
                errors.append(f"{model}: {repr(e)[:80]}")
                continue
            if r.status_code == 429 and "per day" in r.text.lower():
                _dead[model] = time.time()
                errors.append(f"{model}: daily quota")
                break
            if r.status_code in (429, 500, 503):
                errors.append(f"{model}: {r.status_code}")
                time.sleep(3 * (i + 1))
                continue
            if r.status_code >= 400:
                errors.append(f"{model}: {r.status_code}")
                break
            try:
                text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
            except (KeyError, IndexError, ValueError) as e:
                errors.append(f"{model}: bad response {repr(e)[:60]}")
    raise GeminiError("; ".join(errors[-6:]) or "no Gemini model available")
