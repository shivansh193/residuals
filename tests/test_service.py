"""End-to-end service tests with PayPal mocked: scan -> decisions -> invoice -> paid -> payouts (idempotent)."""
import os, tempfile

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "t.db")

from server import db, paypal, seed, service  # noqa: E402

CALLS = []


def fake_call(method, path, body=None, idem=None):
    CALLS.append((method, path, idem))
    if path == "/v2/invoicing/invoices":
        return {"id": "INV-TEST-1"}
    if path.endswith("/send"):
        return {"href": "https://sandbox/inv"}
    raise AssertionError(path)


PAID = set()


def fake_payout(receiver, usd, batch_id, note):
    if batch_id in PAID:
        raise paypal.PayPalError(f"400 Batch with given sender_batch_id already exists "
                                 f"/v1/payments/payouts/B{len(PAID)}X")
    PAID.add(batch_id)
    CALLS.append(("PAYOUT", batch_id, usd))
    return {"batch_header": {"payout_batch_id": f"B{len(PAID)}"}}


def analysis(use_type, voice_segments):
    segs = [{"start": s, "end": e, "voice_id": v, "score": sc, "clone_prob": 0.9}
            for v, s, e, sc in voice_segments]
    return {"file_id": "f", "file_name": "ad.wav", "use_type": use_type, "eer_threshold": 0.35, "segments": segs}


def setup_module():
    paypal.call = fake_call
    paypal.payout = fake_payout
    seed.seed()


def test_licensed_unlicensed_blocked_review_in_one_scan():
    # Brightline is licensed for mara; theo is not licensed by Brightline; silas blocks political only.
    r = service.process_scan(analysis("ad", [("mara", 0, 74, 0.6), ("theo", 80, 110, 0.6),
                                             ("ivy", 120, 125, 0.30)]), "brightline")
    d = {m["voice_id"]: m for m in r["matches"]}
    assert d["mara"]["decision"] == "bill" and d["mara"]["amount_cents"] == 62      # 74s @ 50c/min
    assert d["theo"]["decision"] == "offer" and d["theo"]["amount_cents"] == 20     # 30s @ 40c default
    assert d["ivy"]["decision"] == "review" and d["ivy"]["amount_cents"] == 0       # low confidence
    assert r["invoice"]["id"] == "INV-TEST-1" and r["invoice"]["offer"] is True
    assert r["invoice"]["total"] == "0.82"


def test_blocked_use_alerts_owner_and_is_not_invoiced():
    r = service.process_scan(analysis("political", [("silas", 0, 40, 0.7)]), "measure12")
    assert r["matches"][0]["decision"] == "blocked" and r["invoice"] is None
    assert any(a["kind"] == "blocked_use" for a in db.rows("select * from alerts where voice_id='silas'"))


def test_paid_invoice_pays_each_owner_once():
    first = service.on_invoice_paid("INV-TEST-1")
    assert sorted(a.split(":")[0] for a in first) == ["mara", "theo"]
    n = len([c for c in CALLS if c[0] == "PAYOUT"])
    again = service.on_invoice_paid("INV-TEST-1")          # webhook retry
    assert all(a.endswith("already_paid") for a in again)
    assert len([c for c in CALLS if c[0] == "PAYOUT"]) == n
    royalty = [c for c in CALLS if c[0] == "PAYOUT" and "mara" in c[1]][0][2]
    assert royalty == "0.56"                                  # 62c minus 10% fee (6c)


def test_ledger_chain_valid_then_tamper_detected():
    assert db.verify_ledger()["valid"]
    db.execute("update uses set amount_cents=9999 where seq=1")
    v = db.verify_ledger()
    assert not v["valid"] and v["first_bad_seq"] == 1
