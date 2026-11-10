"""Consent-first enrolment: random liveness phrase + Gemini check of the consent and liveness recordings."""
import base64, difflib, re, secrets, time

from server import gemini

WORDS = ("amber harbour violet copper meadow lantern orbit pebble quartz saffron tundra velvet willow "
         "cobalt ember falcon glacier hazel indigo juniper kestrel lagoon marble nectar opal prairie "
         "raven sierra thistle umber walnut zephyr").split()
_challenges = {}  # id -> (phrase, expires)
TTL = 600


def new_challenge():
    cid = secrets.token_hex(8)
    phrase = " ".join(secrets.choice(WORDS) for _ in range(4)) + f" {secrets.randbelow(90) + 10}"
    _challenges[cid] = (phrase, time.time() + TTL)
    for k, (_, exp) in list(_challenges.items()):
        if exp < time.time():
            _challenges.pop(k, None)
    return {"id": cid, "phrase": phrase, "expires_in": TTL}


def take_challenge(cid):
    phrase, exp = _challenges.pop(cid, (None, 0))
    return phrase if phrase and exp > time.time() else None


def _norm(s):
    return re.sub(r"[^a-z0-9 ]", "", s.lower().replace("-", " ")).split()


NUMS = {str(n): w for n, w in [(10, "ten"), (11, "eleven"), (12, "twelve")]}


def phrase_similarity(heard, phrase):
    a, b = _norm(heard), _norm(phrase)
    return difflib.SequenceMatcher(None, a, b).ratio()


SCHEMA = {"type": "OBJECT", "properties": {
    "consent_transcript": {"type": "STRING"}, "liveness_transcript": {"type": "STRING"},
    "consent_ok": {"type": "BOOLEAN"}, "same_speaker_likely": {"type": "BOOLEAN"},
    "sounds_like_playback_or_synthetic": {"type": "BOOLEAN"}, "reason": {"type": "STRING"}},
    "required": ["consent_transcript", "liveness_transcript", "consent_ok", "same_speaker_likely",
                 "sounds_like_playback_or_synthetic", "reason"]}


def check(name, consent_bytes, consent_mime, live_bytes, live_mime, phrase):
    parts = [
        {"text": "Recording A (consent statement):"},
        {"inline_data": {"mime_type": consent_mime, "data": base64.b64encode(consent_bytes).decode()}},
        {"text": "Recording B (liveness phrase):"},
        {"inline_data": {"mime_type": live_mime, "data": base64.b64encode(live_bytes).decode()}},
    ]
    prompt = (f"You verify consent for enrolling a voice. Transcribe both recordings exactly (numbers as digits). "
              f"consent_ok is true only if recording A clearly states the speaker's name ('{name}') and that they "
              f"consent to enrolling their own voice. same_speaker_likely: do A and B sound like the same person? "
              f"sounds_like_playback_or_synthetic: does either sound like a replayed recording or TTS? "
              f"reason: one short sentence.")
    r = gemini.generate_json(prompt, SCHEMA, parts=parts, timeout=90)
    sim = phrase_similarity(r["liveness_transcript"], phrase)
    r["liveness_similarity"] = round(sim, 2)
    r["liveness_ok"] = sim >= 0.75
    r["verified"] = bool(r["consent_ok"] and r["liveness_ok"] and r["same_speaker_likely"]
                         and not r["sounds_like_playback_or_synthetic"])
    return r
