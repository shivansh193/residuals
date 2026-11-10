"""Pure billing logic: decide what happens to each detected use, and price it.

No I/O here, so it is fully unit-tested (tests/test_billing.py).
"""
import hashlib, json, math

from server.policy import rate_for

# Decisions
REVIEW = "review"        # below confidence threshold: never billed automatically
BLOCKED = "blocked"      # owner forbids this use type: alert owner, no offer
FREE = "free"            # owner allows free use for this type
BILL = "bill"            # user holds a licence: invoice
OFFER = "offer"          # no licence: retroactive licence offer (same invoice, different framing)


def decide(use, policy, licensed: bool, threshold: float):
    """use: {"confidence": float, "use_type": str, "seconds": float}"""
    if use["confidence"] < threshold:
        return REVIEW
    if use["use_type"] in policy["blocked"]:
        return BLOCKED
    if use["use_type"] in policy["free_for"]:
        return FREE
    return BILL if licensed else OFFER


def price_cents(seconds: float, cents_per_min: int) -> int:
    """Round half up to whole cents. Any billable use costs at least 1 cent."""
    if seconds <= 0 or cents_per_min <= 0:
        return 0
    exact = seconds / 60.0 * cents_per_min
    return max(1, int(math.floor(exact + 0.5)))


def split_fee(amount_cents: int, fee_pct: float):
    """Platform fee is rounded down so the owner never loses a rounding cent."""
    fee = int(math.floor(amount_cents * fee_pct / 100.0))
    return fee, amount_cents - fee


def assess(use, policy, licensed, threshold, fee_pct):
    d = decide(use, policy, licensed, threshold)
    rate = rate_for(policy, use["use_type"])
    amount = price_cents(use["seconds"], rate) if d in (BILL, OFFER) else 0
    fee, royalty = split_fee(amount, fee_pct)
    return {"decision": d, "rate_cents_per_min": rate if d in (BILL, OFFER) else 0,
            "amount_cents": amount, "platform_fee_cents": fee, "royalty_cents": royalty}


def fmt_usd(cents: int) -> str:
    return f"{cents // 100}.{cents % 100:02d}"


# ---- tamper-evident ledger ----

def entry_hash(prev_hash: str, entry: dict) -> str:
    payload = json.dumps(entry, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((prev_hash + "|" + payload).encode()).hexdigest()


def verify_chain(entries):
    """entries: list of (entry_dict, prev_hash, hash) in order. Returns index of first bad row or -1."""
    prev = "0" * 64
    for i, (e, p, h) in enumerate(entries):
        if p != prev or entry_hash(p, e) != h:
            return i
        prev = h
    return -1
