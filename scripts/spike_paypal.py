"""PayPal sandbox spikes 1 + 2 for Residuals.

Usage (reads .env; sandbox only):
  python scripts/spike_paypal.py invoice <buyer_email>      # create + send Invoicing v2 invoice
  python scripts/spike_paypal.py status <invoice_id>         # show invoice status
  python scripts/spike_paypal.py record <invoice_id>         # mark paid by API (fallback if no buyer login)
  python scripts/spike_paypal.py payout <receiver_email> <usd>
  python scripts/spike_paypal.py payout-status <batch_id>
  python scripts/spike_paypal.py webhook-create <public_url> # subscribe INVOICING.INVOICE.PAID + payouts events
  python scripts/spike_paypal.py webhook-serve               # local receiver that verifies signatures

Secrets are never printed.
"""
import json, os, sys, uuid
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if os.environ.get("PAYPAL_ENV", "sandbox") != "sandbox":
    sys.exit("Refusing to run: PAYPAL_ENV must be 'sandbox'.")
BASE = "https://api-m.sandbox.paypal.com"


def token():
    r = requests.post(f"{BASE}/v1/oauth2/token", data={"grant_type": "client_credentials"},
                      auth=(os.environ["PAYPAL_CLIENT_ID"], os.environ["PAYPAL_CLIENT_SECRET"]), timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def call(method, path, body=None, idem=None):
    h = {"Authorization": f"Bearer {token()}", "Content-Type": "application/json", "Prefer": "return=representation"}
    if idem:
        h["PayPal-Request-Id"] = idem
    r = requests.request(method, BASE + path, headers=h, json=body, timeout=30)
    if r.status_code >= 400:
        sys.exit(f"{method} {path} -> {r.status_code}: {r.text[:800]}")
    return r.json() if r.text else {}


def invoice(buyer_email):
    idem = f"spike-inv-{uuid.uuid4()}"
    inv = call("POST", "/v2/invoicing/invoices", {
        "detail": {"currency_code": "USD", "invoice_date": date.today().isoformat(),
                   "note": "Residuals licence: Voice 'Mara Vell', AI clone, 74 s, use type: ad.",
                   "terms_and_conditions": "Per-use voice licence under the owner's published terms."},
        "invoicer": {"business_name": "Residuals (sandbox)"},
        "primary_recipients": [{"billing_info": {"email_address": buyer_email}}],
        "items": [{"name": "Voice licence: Mara Vell (ad)", "quantity": "1.2333",
                   "unit_amount": {"currency_code": "USD", "value": "0.50"}, "unit_of_measure": "QUANTITY",
                   "description": "74 s at $0.50/min"}],
    }, idem=idem)
    inv_id = inv.get("id") or inv["href"].rsplit("/", 1)[-1]
    sent = call("POST", f"/v2/invoicing/invoices/{inv_id}/send", {"send_to_recipient": True}, idem=idem + "-send")
    print(json.dumps({"invoice_id": inv_id, "send": sent}, indent=1))


def status(inv_id):
    inv = call("GET", f"/v2/invoicing/invoices/{inv_id}")
    print(json.dumps({"id": inv["id"], "status": inv["status"], "amount": inv.get("amount"),
                      "payments": inv.get("payments")}, indent=1))


def record(inv_id):
    inv = call("GET", f"/v2/invoicing/invoices/{inv_id}")
    amt = inv["amount"]["value"]
    print(json.dumps(call("POST", f"/v2/invoicing/invoices/{inv_id}/payments", {
        "method": "PAYPAL", "payment_date": date.today().isoformat(),
        "amount": {"currency_code": "USD", "value": amt}}), indent=1))


def payout(receiver, usd):
    batch = f"spike-payout-{uuid.uuid4().hex[:16]}"
    res = call("POST", "/v1/payments/payouts", {
        "sender_batch_header": {"sender_batch_id": batch, "email_subject": "Your Residuals royalty",
                                "email_message": "Royalty for licensed use of your voice."},
        "items": [{"recipient_type": "EMAIL", "receiver": receiver, "sender_item_id": batch + "-1",
                   "amount": {"currency": "USD", "value": usd}, "note": "Residuals royalty (sandbox)"}],
    }, idem=batch)
    print(json.dumps(res, indent=1))


def payout_status(batch_id):
    print(json.dumps(call("GET", f"/v1/payments/payouts/{batch_id}"), indent=1))


def webhook_create(url):
    print(json.dumps(call("POST", "/v1/notifications/webhooks", {"url": url, "event_types": [
        {"name": n} for n in ["INVOICING.INVOICE.PAID", "PAYMENT.PAYOUTSBATCH.SUCCESS",
                              "PAYMENT.PAYOUTSBATCH.DENIED", "PAYMENT.PAYOUTS-ITEM.SUCCEEDED",
                              "PAYMENT.PAYOUTS-ITEM.FAILED", "PAYMENT.PAYOUTS-ITEM.UNCLAIMED"]]}), indent=1))


def verify(headers, event):
    res = call("POST", "/v1/notifications/verify-webhook-signature", {
        "auth_algo": headers.get("paypal-auth-algo"), "cert_url": headers.get("paypal-cert-url"),
        "transmission_id": headers.get("paypal-transmission-id"),
        "transmission_sig": headers.get("paypal-transmission-sig"),
        "transmission_time": headers.get("paypal-transmission-time"),
        "webhook_id": os.environ["PAYPAL_WEBHOOK_ID"], "webhook_event": event})
    return res.get("verification_status") == "SUCCESS"


class Hook(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        ok = verify({k.lower(): v for k, v in self.headers.items()}, body)
        print(json.dumps({"event": body.get("event_type"), "id": body.get("id"), "verified": ok}), flush=True)
        self.send_response(200 if ok else 400); self.end_headers()


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    {"invoice": invoice, "status": status, "record": record, "payout": payout, "payout-status": payout_status,
     "webhook-create": webhook_create,
     "webhook-serve": lambda: HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 8787))), Hook).serve_forever()
     }[cmd](*args)
