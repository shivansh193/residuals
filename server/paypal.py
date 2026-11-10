"""Thin PayPal sandbox client: OAuth, Invoicing v2, Payouts, webhook verification."""
import os, time
import requests

BASE = "https://api-m.sandbox.paypal.com"
_tok = {"v": None, "exp": 0}


def _env_guard():
    if os.environ.get("PAYPAL_ENV", "sandbox") != "sandbox":
        raise RuntimeError("Residuals only runs against the PayPal sandbox.")


def token():
    _env_guard()
    if _tok["v"] and time.time() < _tok["exp"] - 60:
        return _tok["v"]
    r = requests.post(f"{BASE}/v1/oauth2/token", data={"grant_type": "client_credentials"},
                      auth=(os.environ["PAYPAL_CLIENT_ID"], os.environ["PAYPAL_CLIENT_SECRET"]), timeout=30)
    r.raise_for_status()
    j = r.json()
    _tok.update(v=j["access_token"], exp=time.time() + j["expires_in"])
    return _tok["v"]


class PayPalError(Exception):
    pass


def call(method, path, body=None, idem=None):
    h = {"Authorization": f"Bearer {token()}", "Content-Type": "application/json", "Prefer": "return=representation"}
    if idem:
        h["PayPal-Request-Id"] = idem
    r = requests.request(method, BASE + path, headers=h, json=body, timeout=30)
    if r.status_code >= 400:
        raise PayPalError(f"{method} {path} -> {r.status_code}: {r.text[:500]}")
    return r.json() if r.text else {}


def verify_webhook(headers, event):
    res = call("POST", "/v1/notifications/verify-webhook-signature", {
        "auth_algo": headers.get("paypal-auth-algo"), "cert_url": headers.get("paypal-cert-url"),
        "transmission_id": headers.get("paypal-transmission-id"),
        "transmission_sig": headers.get("paypal-transmission-sig"),
        "transmission_time": headers.get("paypal-transmission-time"),
        "webhook_id": os.environ["PAYPAL_WEBHOOK_ID"], "webhook_event": event})
    return res.get("verification_status") == "SUCCESS"


def payout(receiver, usd, batch_id, note):
    """Idempotent: PayPal rejects a repeated sender_batch_id, and PayPal-Request-Id dedupes retries."""
    return call("POST", "/v1/payments/payouts", {
        "sender_batch_header": {"sender_batch_id": batch_id, "email_subject": "Your Residuals royalty",
                                "email_message": note},
        "items": [{"recipient_type": "EMAIL", "receiver": receiver, "sender_item_id": batch_id + "-1",
                   "amount": {"currency": "USD", "value": usd}, "note": note}]}, idem=batch_id)
