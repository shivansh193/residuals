"""Residuals API (spike stage): health, PayPal webhook receiver, event log."""
import json, os, sqlite3, time
from fastapi import FastAPI, Request, HTTPException

from server import paypal

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DB = os.environ.get("DB_PATH", "residuals.db")
app = FastAPI(title="Residuals API")


def db():
    c = sqlite3.connect(DB)
    c.execute("create table if not exists webhook_events(id text primary key, type text, verified int, "
              "resource_id text, received_at real, action text)")
    return c


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/webhooks/paypal")
async def paypal_webhook(req: Request):
    event = await req.json()
    headers = {k.lower(): v for k, v in req.headers.items()}
    ok = paypal.verify_webhook(headers, event)
    etype, rid = event.get("event_type"), (event.get("resource") or {}).get("invoice", event.get("resource", {})).get("id")
    action = None
    with db() as c:
        dup = c.execute("select 1 from webhook_events where id=?", (event.get("id"),)).fetchone()
        if not dup:
            if ok and etype == "INVOICING.INVOICE.PAID" and os.environ.get("SPIKE_OWNER_EMAIL"):
                try:
                    res = paypal.payout(os.environ["SPIKE_OWNER_EMAIL"], os.environ.get("SPIKE_ROYALTY_USD", "0.55"),
                                        f"roy-{rid}", f"Residuals royalty for invoice {rid}")
                    action = "payout:" + res["batch_header"]["payout_batch_id"]
                except paypal.PayPalError as e:
                    action = "payout_error:" + str(e)[:200]
            c.execute("insert into webhook_events values (?,?,?,?,?,?)",
                      (event.get("id"), etype, int(ok), rid, time.time(), action))
    print(json.dumps({"event": etype, "id": event.get("id"), "verified": ok, "action": action}), flush=True)
    if not ok:
        raise HTTPException(400, "signature verification failed")
    return {"ok": True}


@app.get("/api/webhook-events")
def webhook_events():
    with db() as c:
        rows = c.execute("select id,type,verified,resource_id,received_at,action from webhook_events "
                         "order by received_at desc limit 50").fetchall()
    return [dict(zip(["id", "type", "verified", "resource_id", "received_at", "action"], r)) for r in rows]
