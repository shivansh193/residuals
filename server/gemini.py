"""Minimal Gemini REST client with retry (the shared quota sometimes returns 503)."""
import json, os, time
import requests

URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiError(Exception):
    pass


def generate_json(prompt, schema=None, retries=3, timeout=60):
    model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}
    if schema:
        body["generationConfig"]["responseSchema"] = schema
    last = None
    for i in range(retries):
        try:
            r = requests.post(URL.format(model=model), json=body, timeout=timeout,
                              headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]})
            if r.status_code in (429, 500, 503):
                last = f"{r.status_code}"
                time.sleep(2 * (i + 1))
                continue
            r.raise_for_status()
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except (requests.RequestException, KeyError, ValueError) as e:
            last = repr(e)[:200]
            time.sleep(2 * (i + 1))
    raise GeminiError(f"Gemini failed after {retries} tries: {last}")
