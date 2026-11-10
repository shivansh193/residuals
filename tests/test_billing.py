from server import billing as b
from server.policy import normalise

POLICY = normalise({"rates": [{"use_type": "ad", "cents_per_min": 50}, {"use_type": "political", "cents_per_min": 99}],
                    "default_rate_cents_per_min": 30, "free_for": ["nonprofit"], "blocked": ["political"],
                    "attribution_required": True})


def use(t="ad", s=74.0, c=0.9):
    return {"use_type": t, "seconds": s, "confidence": c}


def test_normalise_blocked_wins_over_rates():
    assert "political" not in POLICY["rates_cents_per_min"]
    assert POLICY["blocked"] == ["political"]


def test_decisions():
    assert b.decide(use(c=0.5), POLICY, True, 0.7) == b.REVIEW
    assert b.decide(use("political"), POLICY, True, 0.7) == b.BLOCKED
    assert b.decide(use("nonprofit"), POLICY, True, 0.7) == b.FREE
    assert b.decide(use("ad"), POLICY, True, 0.7) == b.BILL
    assert b.decide(use("ad"), POLICY, False, 0.7) == b.OFFER


def test_review_beats_blocked_low_confidence_is_never_acted_on():
    assert b.decide(use("political", c=0.1), POLICY, True, 0.7) == b.REVIEW


def test_price_rounding():
    assert b.price_cents(74, 50) == 62          # 61.67 -> 62
    assert b.price_cents(60, 50) == 50
    assert b.price_cents(0.5, 1) == 1           # tiny use still costs a cent
    assert b.price_cents(0, 50) == 0
    assert b.price_cents(30, 0) == 0


def test_fee_never_takes_rounding_cent_from_owner():
    assert b.split_fee(62, 10) == (6, 56)
    assert b.split_fee(9, 10) == (0, 9)
    fee, roy = b.split_fee(12345, 12.5)
    assert fee + roy == 12345


def test_assess_default_rate_and_zero_for_non_billable():
    a = b.assess(use("narration", 120), POLICY, True, 0.7, 10)
    assert a["rate_cents_per_min"] == 30 and a["amount_cents"] == 60
    z = b.assess(use("political"), POLICY, True, 0.7, 10)
    assert z["amount_cents"] == 0 and z["decision"] == b.BLOCKED


def test_hash_chain_detects_tampering():
    rows, prev = [], "0" * 64
    for i in range(3):
        e = {"n": i, "amount_cents": 10 * i}
        h = b.entry_hash(prev, e)
        rows.append((e, prev, h))
        prev = h
    assert b.verify_chain(rows) == -1
    rows[1][0]["amount_cents"] = 999
    assert b.verify_chain(rows) == 1


def test_fmt_usd():
    assert b.fmt_usd(62) == "0.62" and b.fmt_usd(1205) == "12.05"
