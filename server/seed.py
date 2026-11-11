"""Seed demo data: 5 fully synthetic voice personas and 4 voice users (all PayPal sandbox)."""
import json, os, time

from server import db

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OWNER_EMAIL = os.environ.get("SANDBOX_OWNER_EMAIL", "sb-7nfra53830207@business.example.com")
BUYER_EMAIL = os.environ.get("SANDBOX_BUYER_EMAIL", "sb-wqm5053792956@personal.example.com")

USERS = [
    ("brightline", "Brightline Appliances (brand)", ["mara", "juno", "ivy"]),
    ("northpeak", "Northpeak Studios (game studio)", ["theo"]),
    ("quickclips", "QuickClips Media (no licences)", []),
    ("measure12", "Committee for Measure 12 (political)", []),
]


def seed():
    db.init()
    if db.one("select count(*) n from voices")["n"]:
        return
    vs = json.load(open(os.path.join(ROOT, "fixtures", "voices.json")))
    for i, v in enumerate(vs):
        consent = {"type": "synthetic_persona",
                   "statement": "Fictional persona designed from blended Kokoro-82M voice packs. "
                                "Not cloned from any real person. See ASSETS.md.",
                   "liveness_phrase": None, "enrolled_by": "Residuals demo"}
        db.execute("insert into voices(id,name,owner_paypal_email,terms_text,policy_json,consent_json,enrolled_at,synthetic)"
                   " values (?,?,?,?,?,?,?,1)", v["id"], v["name"], OWNER_EMAIL, v["terms_text"],
                   json.dumps(v["policy"]), json.dumps(consent), time.time() - 86400 * (10 - i))
    for uid, name, lic in USERS:
        db.execute("insert into voice_users(id,name,billing_email,licensed_voice_ids) values (?,?,?,?)",
                   uid, name, BUYER_EMAIL, json.dumps(lic))
