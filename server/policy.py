"""Licence terms: plain English -> structured policy (Gemini), owner confirms it.

Policy shape (all money in integer cents):
{
  "currency": "USD",
  "rates_cents_per_min": {"ad": 50, "narration": 30, ...},   # missing type -> default
  "default_rate_cents_per_min": 40,
  "free_for": ["nonprofit"],
  "blocked": ["political"],
  "attribution_required": false,
  "notes": "..."
}
"""
from server import gemini

USE_TYPES = ["ad", "narration", "elearning", "game", "nonprofit", "political", "social", "adult", "other"]

SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "rates": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
            "use_type": {"type": "STRING", "enum": USE_TYPES},
            "cents_per_min": {"type": "INTEGER"}}, "required": ["use_type", "cents_per_min"]}},
        "default_rate_cents_per_min": {"type": "INTEGER"},
        "free_for": {"type": "ARRAY", "items": {"type": "STRING", "enum": USE_TYPES}},
        "blocked": {"type": "ARRAY", "items": {"type": "STRING", "enum": USE_TYPES}},
        "attribution_required": {"type": "BOOLEAN"},
        "notes": {"type": "STRING"},
    },
    "required": ["rates", "default_rate_cents_per_min", "free_for", "blocked", "attribution_required"],
}

PROMPT = """You turn a voice owner's plain-English licence terms for their AI voice clone into a structured policy.
Use types: {types}.
- Rates are US cents per minute of their voice that is used. "$0.50 per minute" = 50.
- If they give one general rate, use it as default_rate_cents_per_min. If no rate at all, use 40.
- "free for X" -> free_for. "never for X" / "no X" / "not for X" -> blocked.
- A use type can't be in two of rates, free_for and blocked; blocked wins, then free_for.
- notes: one short sentence for anything you could not map (or empty).
Terms:
\"\"\"{terms}\"\"\""""


def normalise(raw):
    blocked = sorted(set(raw.get("blocked", [])) & set(USE_TYPES))
    free = sorted((set(raw.get("free_for", [])) & set(USE_TYPES)) - set(blocked))
    rates = {}
    for r in raw.get("rates", []):
        t = r.get("use_type")
        if t in USE_TYPES and t not in blocked and t not in free:
            rates[t] = max(0, int(r["cents_per_min"]))
    return {"currency": "USD", "rates_cents_per_min": rates,
            "default_rate_cents_per_min": max(0, int(raw.get("default_rate_cents_per_min", 40))),
            "free_for": free, "blocked": blocked,
            "attribution_required": bool(raw.get("attribution_required", False)),
            "notes": raw.get("notes", "")}


def parse_terms(terms: str):
    raw = gemini.generate_json(PROMPT.format(types=", ".join(USE_TYPES), terms=terms), SCHEMA)
    return normalise(raw)


def rate_for(policy, use_type):
    return policy["rates_cents_per_min"].get(use_type, policy["default_rate_cents_per_min"])
