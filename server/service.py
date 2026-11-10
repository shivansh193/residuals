"""Scan -> decisions -> ledger -> PayPal invoice; invoice paid -> royalty payouts."""
import json, math, os, time, uuid
from datetime import date

from server import billing, db, paypal

THRESHOLD = float(os.environ.get("MATCH_CONFIDENCE_THRESHOLD", "0.7"))
FEE_PCT = float(os.environ.get("PAYPAL_PLATFORM_FEE_PCT", "10"))
BASE_URL = os.environ.get("APP_BASE_URL", "https://residuals.onrender.com")


def score_to_confidence(score, eer_threshold, scale=0.05):
    """Map ECAPA cosine score to 0..1 with 0.5 at the EER threshold (calibrated in docs/SPIKES.md)."""
    return 1 / (1 + math.exp(-(score - eer_threshold) / scale))


def summarise(analysis):
    """Group matched segments by registered voice."""
    th = analysis.get("eer_threshold", 0.35)
    by = {}
    for s in analysis["segments"]:
        if not s.get("voice_id"):
            continue
        d = max(0.0, s["end"] - s["start"])
        g = by.setdefault(s["voice_id"], {"seconds": 0.0, "w_conf": 0.0, "w_clone": 0.0, "segments": []})
        g["seconds"] += d
        g["w_conf"] += d * score_to_confidence(s["score"], th)
        g["w_clone"] += d * s.get("clone_prob", 0.0)
        g["segments"].append(s)
    out = {}
    for vid, g in by.items():
        sec = g["seconds"] or 1e-9
        out[vid] = {"seconds": round(g["seconds"], 2), "confidence": round(g["w_conf"] / sec, 3),
                    "clone_prob": round(g["w_clone"] / sec, 3), "is_clone": g["w_clone"] / sec >= 0.5,
                    "segments": g["segments"]}
    return out


def process_scan(analysis, user_id, kind="preclear"):
    user = db.one("select * from voice_users where id=?", user_id)
    if not user:
        raise ValueError("unknown voice user")
    licensed = set(json.loads(user["licensed_voice_ids"] or "[]"))
    scan_id = "scn_" + uuid.uuid4().hex[:12]
    use_type = analysis.get("use_type", "other")
    results = []
    for vid, m in summarise(analysis).items():
        v = db.voice(vid)
        if not v:
            continue
        a = billing.assess({"confidence": m["confidence"], "use_type": use_type, "seconds": m["seconds"]},
                           v["policy"], vid in licensed, THRESHOLD, FEE_PCT)
        row = db.append_use({
            "id": "use_" + uuid.uuid4().hex[:12], "scan_id": scan_id, "voice_id": vid, "user_id": user_id,
            "file_name": analysis["file_name"], "seconds": m["seconds"], "is_clone": int(m["is_clone"]),
            "clone_prob": m["clone_prob"], "confidence": m["confidence"], "use_type": use_type,
            "decision": a["decision"], "rate_cents_per_min": a["rate_cents_per_min"],
            "amount_cents": a["amount_cents"], "platform_fee_cents": a["platform_fee_cents"],
            "royalty_cents": a["royalty_cents"], "status": {
                billing.BILL: "pending_invoice", billing.OFFER: "pending_invoice", billing.FREE: "free",
                billing.BLOCKED: "blocked", billing.REVIEW: "owner_review"}[a["decision"]]})
        if a["decision"] == billing.BLOCKED:
            db.execute("insert into alerts(voice_id,scan_id,kind,message,created_at) values (?,?,?,?,?)",
                       vid, scan_id, "blocked_use",
                       f"{user['name']} submitted '{analysis['file_name']}' using your voice "
                       f"({m['seconds']:.0f}s, {'AI clone' if m['is_clone'] else 'original'}) for a "
                       f"'{use_type}' use, which your terms block. No licence was offered.", time.time())
        elif a["decision"] == billing.REVIEW:
            db.execute("insert into alerts(voice_id,scan_id,kind,message,created_at) values (?,?,?,?,?)",
                       vid, scan_id, "needs_review",
                       f"Possible use of your voice in '{analysis['file_name']}' (confidence "
                       f"{m['confidence']:.0%}, below the auto-billing threshold). Please review.", time.time())
        results.append({**row, "voice_name": v["name"], "segments": m["segments"],
                        "attribution_required": v["policy"].get("attribution_required", False)})
    scan = {"id": scan_id, "file_id": analysis.get("file_id"), "file_name": analysis["file_name"],
            "user_id": user_id, "created_at": time.time(), "result_json": json.dumps(analysis), "kind": kind}
    db.execute("insert into scans(id,file_id,file_name,user_id,created_at,result_json,kind) values (?,?,?,?,?,?,?)",
               *scan.values())
    billable = [r for r in results if r["decision"] in (billing.BILL, billing.OFFER)]
    invoice = create_invoice(scan_id, user, analysis["file_name"], billable) if billable else None
    return {"scan_id": scan_id, "file_name": analysis["file_name"], "use_type": use_type,
            "use_type_reason": analysis.get("use_type_reason"), "duration_s": analysis.get("duration_s"),
            "matches": results, "invoice": invoice}


def create_invoice(scan_id, user, file_name, billable):
    offer = any(r["decision"] == billing.OFFER for r in billable)
    items = []
    for r in billable:
        label = "Retroactive licence" if r["decision"] == billing.OFFER else "Voice licence"
        items.append({"name": f"{label}: {r['voice_name']} ({r['use_type']})"[:200], "quantity": "1",
                      "unit_amount": {"currency_code": "USD", "value": billing.fmt_usd(r["amount_cents"])},
                      "description": (f"{r['seconds']:.0f}s of {'AI clone' if r['is_clone'] else 'original'} voice "
                                      f"in '{file_name}' at ${billing.fmt_usd(r['rate_cents_per_min'])}/min. "
                                      f"Ledger {r['id']}.")[:1000]})
    note = ("Residuals detected licensed voices in your file. Paying this invoice licenses the use under each "
            "voice owner's published terms; the owner's royalty is paid out automatically." if not offer else
            "Residuals detected voices used without a licence. Paying this invoice grants a retroactive licence "
            "under each owner's terms, instead of a takedown.")
    inv = paypal.call("POST", "/v2/invoicing/invoices", {
        "detail": {"currency_code": "USD", "invoice_date": date.today().isoformat(), "note": note,
                   "reference": scan_id, "terms_and_conditions": f"Terms: {BASE_URL}/policy"},
        "invoicer": {"business_name": "Residuals (sandbox)"},
        "primary_recipients": [{"billing_info": {"email_address": user["billing_email"],
                                                 "name": {"full_name": user["name"]}}}],
        "items": items}, idem=f"inv-{scan_id}")
    inv_id = inv.get("id") or inv["href"].rsplit("/", 1)[-1]
    sent = paypal.call("POST", f"/v2/invoicing/invoices/{inv_id}/send", {"send_to_recipient": True},
                       idem=f"send-{scan_id}")
    url = sent.get("href") or f"https://www.sandbox.paypal.com/invoice/p/#{inv_id}"
    db.execute("update scans set invoice_id=?, invoice_status='SENT', invoice_url=? where id=?", inv_id, url, scan_id)
    for r in billable:
        db.execute("update uses set invoice_id=?, status='invoiced' where id=?", inv_id, r["id"])
        r.update(invoice_id=inv_id, status="invoiced")
    total = sum(r["amount_cents"] for r in billable)
    return {"id": inv_id, "url": url, "total": billing.fmt_usd(total), "offer": offer, "status": "SENT"}


def sandbox_mark_paid(inv_id):
    """Sandbox-only shortcut for judges without a buyer login: record the payment by API.
    PayPal still emits INVOICING.INVOICE.PAID, so the real webhook -> payout chain runs."""
    inv = paypal.call("GET", f"/v2/invoicing/invoices/{inv_id}")
    if inv["status"] in ("PAID", "MARKED_AS_PAID"):
        return inv["status"]
    paypal.call("POST", f"/v2/invoicing/invoices/{inv_id}/payments", {
        "method": "PAYPAL", "payment_date": date.today().isoformat(),
        "amount": {"currency_code": "USD", "value": inv["amount"]["value"]}}, idem=f"pay-{inv_id}")
    return "MARKED_AS_PAID"


def on_invoice_paid(inv_id):
    """Pay each voice owner their royalty for this invoice. Idempotent per (invoice, voice)."""
    db.execute("update scans set invoice_status='PAID' where invoice_id=?", inv_id)
    uses = db.rows("select * from uses where invoice_id=?", inv_id)
    actions = []
    by_voice = {}
    for u in uses:
        by_voice.setdefault(u["voice_id"], []).append(u)
    for vid, us in by_voice.items():
        if all(u["payout_batch_id"] for u in us):
            actions.append(f"{vid}:already_paid")
            continue
        v = db.voice(vid)
        royalty = sum(u["royalty_cents"] for u in us)
        batch = f"roy-{inv_id}-{vid}"[:127]
        try:
            res = paypal.payout(v["owner_paypal_email"], billing.fmt_usd(royalty), batch,
                                f"Residuals royalty: {len(us)} licensed use(s) of your voice, invoice {inv_id}.")
            pb = res["batch_header"]["payout_batch_id"]
        except paypal.PayPalError as e:
            if "already exists" not in str(e):
                for u in us:
                    db.execute("update uses set status='payout_error' where id=?", u["id"])
                actions.append(f"{vid}:error")
                continue
            pb = _existing_batch(str(e)) or "existing"
        for u in us:
            db.execute("update uses set payout_batch_id=?, status='payout_sent' where id=?", pb, u["id"])
        actions.append(f"{vid}:payout:{pb}")
    return actions


def _existing_batch(err):
    import re
    m = re.search(r"/v1/payments/payouts/([A-Z0-9]+)", err)
    return m.group(1) if m else None


def on_payout_item(resource, ok):
    pb = resource.get("payout_batch_id")
    fee = resource.get("payout_item_fee", {}).get("value")
    fee_c = int(round(float(fee) * 100)) if fee else None
    db.execute("update uses set status=?, payout_fee_cents=coalesce(?, payout_fee_cents) where payout_batch_id=?",
               "paid_out" if ok else "payout_failed", fee_c, pb)


def takedown_notice(scan_id, voice_id):
    s = db.one("select * from scans where id=?", scan_id)
    u = db.one("select * from voice_users where id=?", s["user_id"])
    v = db.voice(voice_id)
    use = db.one("select * from uses where scan_id=? and voice_id=?", scan_id, voice_id)
    return (f"To: {u['name']}\nRe: Unlicensed use of the voice of {v['name']} in \"{s['file_name']}\"\n\n"
            f"Residuals detected {use['seconds']:.0f} seconds of {v['name']}'s voice "
            f"({'an AI clone' if use['is_clone'] else 'an original recording'}, match confidence "
            f"{use['confidence']:.0%}) in the file above, used as '{use['use_type']}'. "
            f"No licence was in place, and the retroactive licence offered on invoice {s['invoice_id']} "
            f"was declined.\n\nPlease remove the file from all channels within 7 days. The detection "
            f"record is entry #{use['seq']} in a hash-chained ledger (hash {use['hash'][:16]}...).\n\n"
            f"This is a template. It is not legal advice.")
