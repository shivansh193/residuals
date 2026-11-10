"""Residuals API."""
import glob, json, os, re, secrets, time

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    pass

from server import billing, db, enrol, gemini, paypal, policy, seed, service

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, "fixtures")
app = FastAPI(title="Residuals API", version="0.1.0", servers=[{"url": "https://residuals.onrender.com"}],
              description="Royalties for licensed AI voice clones, paid through PayPal (sandbox).")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def _startup():
    seed.seed()


def demo_files():
    out = {}
    for p in sorted(glob.glob(os.path.join(FIX, "analysis", "*.json"))):
        a = json.load(open(p))
        out[a["file_id"]] = a
    return out


# ---------- public API ----------

class Segment(BaseModel):
    start: float
    end: float
    voice_id: str | None = None
    score: float
    clone_prob: float
    text: str | None = None


class Match(BaseModel):
    id: str
    seq: int
    voice_id: str
    voice_name: str
    seconds: float
    is_clone: int
    clone_prob: float
    confidence: float
    use_type: str
    decision: str
    rate_cents_per_min: int
    amount_cents: int
    platform_fee_cents: int
    royalty_cents: int
    invoice_id: str | None = None
    status: str
    hash: str
    attribution_required: bool = False
    segments: list[Segment] = []


class InvoiceOut(BaseModel):
    id: str
    url: str
    total: str
    offer: bool
    status: str


class ScanResult(BaseModel):
    scan_id: str
    file_name: str
    use_type: str
    use_type_reason: str | None = None
    duration_s: float | None = None
    matches: list[Match]
    invoice: InvoiceOut | None = None


class Policy(BaseModel):
    currency: str
    rates_cents_per_min: dict[str, int]
    default_rate_cents_per_min: int
    free_for: list[str]
    blocked: list[str]
    attribution_required: bool
    notes: str = ""


class PolicyOut(BaseModel):
    voice_id: str
    name: str
    terms_text: str
    policy: Policy
    consent: dict


class ScanReq(BaseModel):
    file_id: str
    user_id: str


@app.post("/scan", tags=["public"], response_model=ScanResult, operation_id="scan", summary="Scan audio for registered voices, apply each owner's terms, bill via PayPal")
def scan(req: ScanReq):
    a = demo_files().get(req.file_id)
    if not a:
        raise HTTPException(404, "unknown file_id; see GET /api/demo-files")
    try:
        return service.process_scan(a, req.user_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except paypal.PayPalError as e:
        raise HTTPException(502, f"PayPal error: {e}")


@app.get("/policy/{voice_id}", tags=["public"], response_model=PolicyOut, operation_id="getPolicy", summary="A registered voice's machine-readable licence policy")
def get_policy(voice_id: str):
    v = db.voice(voice_id)
    if not v:
        raise HTTPException(404, "unknown voice")
    return {"voice_id": v["id"], "name": v["name"], "terms_text": v["terms_text"], "policy": v["policy"],
            "consent": {"type": v["consent"].get("type"), "enrolled_at": v["enrolled_at"]}}


# ---------- app API ----------

@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/voices")
def voices():
    out = []
    for v in db.voices():
        s = db.one("select count(*) n, coalesce(sum(case when status in ('paid_out','payout_sent') then royalty_cents end),0) earned,"
                   " coalesce(sum(case when status='invoiced' then royalty_cents end),0) pending,"
                   " coalesce(sum(seconds),0) secs from uses where voice_id=?", v["id"])
        v.pop("owner_paypal_email", None)
        out.append({**v, "stats": s})
    return out


@app.get("/api/users")
def users():
    return [{**u, "licensed_voice_ids": json.loads(u["licensed_voice_ids"])} for u in db.rows("select * from voice_users")]


@app.get("/api/demo-files")
def list_demo_files():
    return [{"file_id": a["file_id"], "file_name": a["file_name"], "title": a.get("title"),
             "duration_s": a.get("duration_s"), "audio_url": f"/audio/{a['audio']}", "description": a.get("description")}
            for a in demo_files().values()]


@app.get("/api/demo-files/{file_id}")
def demo_file(file_id: str):
    a = demo_files().get(file_id)
    if not a:
        raise HTTPException(404)
    return {**a, "audio_url": f"/audio/{a['audio']}"}


class TermsReq(BaseModel):
    terms: str


@app.post("/api/terms/parse")
def parse_terms(req: TermsReq):
    if not req.terms.strip() or len(req.terms) > 2000:
        raise HTTPException(400, "terms must be 1-2000 characters")
    try:
        return policy.parse_terms(req.terms)
    except gemini.GeminiError as e:
        raise HTTPException(503, f"AI temporarily unavailable: {e}")


@app.get("/api/scans")
def scans():
    return db.rows("select id,file_name,user_id,created_at,invoice_id,invoice_status,invoice_url from scans order by created_at desc limit 100")


@app.get("/api/scans/{scan_id}")
def get_scan(scan_id: str):
    s = db.one("select * from scans where id=?", scan_id)
    if not s:
        raise HTTPException(404)
    s["analysis"] = json.loads(s.pop("result_json"))
    s["uses"] = db.rows("select * from uses where scan_id=?", scan_id)
    return s


@app.get("/api/scans/{scan_id}/takedown/{voice_id}", response_class=PlainTextResponse)
def takedown(scan_id: str, voice_id: str):
    return service.takedown_notice(scan_id, voice_id)


@app.post("/api/invoices/{inv_id}/sandbox-pay")
def sandbox_pay(inv_id: str):
    if not db.one("select 1 from scans where invoice_id=?", inv_id):
        raise HTTPException(404, "not a Residuals invoice")
    return {"status": service.sandbox_mark_paid(inv_id),
            "note": "Payment recorded in the PayPal sandbox. PayPal now sends INVOICING.INVOICE.PAID to our webhook."}


@app.get("/api/invoices/{inv_id}")
def invoice_status(inv_id: str):
    s = db.one("select id, invoice_status, invoice_url from scans where invoice_id=?", inv_id)
    if not s:
        raise HTTPException(404)
    return {**s, "uses": db.rows("select id,voice_id,amount_cents,royalty_cents,platform_fee_cents,payout_batch_id,"
                                 "payout_fee_cents,status from uses where invoice_id=?", inv_id)}


@app.get("/api/ledger")
def ledger(voice_id: str | None = None):
    q = ("select u.*, v.name voice_name, vu.name user_name from uses u join voices v on v.id=u.voice_id "
         "join voice_users vu on vu.id=u.user_id")
    return db.rows(q + (" where u.voice_id=?" if voice_id else "") + " order by seq desc", *([voice_id] if voice_id else []))


@app.get("/api/ledger/verify")
def ledger_verify():
    return db.verify_ledger()


@app.get("/api/alerts")
def alerts(voice_id: str | None = None):
    q = "select a.*, v.name voice_name from alerts a join voices v on v.id=a.voice_id"
    return db.rows(q + (" where a.voice_id=?" if voice_id else "") + " order by created_at desc limit 100",
                   *([voice_id] if voice_id else []))


@app.get("/api/enrol/challenge")
def enrol_challenge():
    return enrol.new_challenge()


@app.post("/api/enrol")
async def enrol_voice(name: str = Form(...), paypal_email: str = Form(...), terms_text: str = Form(...),
                      policy_json: str = Form(...), challenge_id: str = Form(...),
                      consent_audio: UploadFile = File(...), liveness_audio: UploadFile = File(...),
                      reference_audio: UploadFile | None = File(None)):
    phrase = enrol.take_challenge(challenge_id)
    if not phrase:
        raise HTTPException(400, "Liveness phrase expired or already used. Reload the page for a new one.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", paypal_email):
        raise HTTPException(400, "Enter a valid PayPal email")
    c, l = await consent_audio.read(), await liveness_audio.read()
    if not (2_000 < len(c) < 5_000_000 and 1_000 < len(l) < 3_000_000):
        raise HTTPException(400, "Recordings are too short or too long")
    try:
        r = enrol.check(name, c, (consent_audio.content_type or "audio/webm").split(";")[0],
                        l, (liveness_audio.content_type or "audio/webm").split(";")[0], phrase)
    except gemini.GeminiError as e:
        raise HTTPException(503, f"AI temporarily unavailable: {e}")
    checks = {"consent_ok": r["consent_ok"], "consent_transcript": r["consent_transcript"],
              "liveness_ok": r["liveness_ok"], "liveness_transcript": r["liveness_transcript"],
              "liveness_expected": phrase, "liveness_similarity": r["liveness_similarity"],
              "same_speaker_likely": r["same_speaker_likely"],
              "sounds_like_playback_or_synthetic": r["sounds_like_playback_or_synthetic"], "reason": r["reason"]}
    if not r["verified"]:
        return {"verified": False, "checks": checks}
    pol = policy.normalise({"rates": [{"use_type": k, "cents_per_min": v} for k, v in
                                      json.loads(policy_json).get("rates_cents_per_min", {}).items()],
                            **{k: v for k, v in json.loads(policy_json).items() if k != "rates_cents_per_min"}})
    vid = "v_" + secrets.token_hex(4)
    db.execute("insert into voices(id,name,owner_paypal_email,terms_text,policy_json,consent_json,enrolled_at,synthetic,status)"
               " values (?,?,?,?,?,?,?,0,'pending_voiceprint')", vid, name[:80], paypal_email, terms_text[:2000],
               json.dumps(pol), json.dumps({"type": "self_enrolled", **checks}), time.time())
    return {"verified": True, "voice_id": vid, "status": "pending_voiceprint", "checks": checks,
            "note": "Your voiceprint is computed by the GPU worker from your reference speech before matching starts."}


@app.post("/webhooks/paypal")
async def paypal_webhook(req: Request):
    event = await req.json()
    headers = {k.lower(): v for k, v in req.headers.items()}
    ok = paypal.verify_webhook(headers, event)
    etype = event.get("event_type")
    res = event.get("resource") or {}
    rid = (res.get("invoice") or {}).get("id") or res.get("payout_item_id") or res.get("id")
    if db.one("select 1 from webhook_events where id=?", event.get("id")):
        return {"ok": True, "duplicate": True}
    action = None
    if ok:
        if etype == "INVOICING.INVOICE.PAID":
            action = ",".join(service.on_invoice_paid(rid))
        elif etype in ("PAYMENT.PAYOUTS-ITEM.SUCCEEDED", "PAYMENT.PAYOUTS-ITEM.FAILED",
                       "PAYMENT.PAYOUTS-ITEM.UNCLAIMED"):
            service.on_payout_item(res, etype.endswith("SUCCEEDED"))
            action = "payout_item_updated"
    db.execute("insert or ignore into webhook_events values (?,?,?,?,?,?)",
               event.get("id"), etype, int(ok), rid, time.time(), action)
    print(json.dumps({"event": etype, "id": event.get("id"), "verified": ok, "action": action}), flush=True)
    if not ok:
        raise HTTPException(400, "signature verification failed")
    return {"ok": True}


@app.get("/api/webhook-events")
def webhook_events():
    return db.rows("select * from webhook_events order by received_at desc limit 50")


# ---------- static ----------
if os.path.isdir(os.path.join(FIX, "audio_public")):
    app.mount("/audio", StaticFiles(directory=os.path.join(FIX, "audio_public")), name="audio")
WEB = os.path.join(ROOT, "web", "dist")
if os.path.isdir(WEB):
    app.mount("/assets", StaticFiles(directory=os.path.join(WEB, "assets")), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        f = os.path.join(WEB, path)
        return FileResponse(f if path and os.path.isfile(f) else os.path.join(WEB, "index.html"))
