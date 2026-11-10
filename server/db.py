"""SQLite storage. Demo data is seeded on first start (see server/seed.py)."""
import json, os, sqlite3, threading, time

from server import billing

DB = os.environ.get("DB_PATH", "residuals.db")
_lock = threading.Lock()

SCHEMA = """
create table if not exists voices(
  id text primary key, name text, owner_paypal_email text, terms_text text, policy_json text,
  consent_json text, enrolled_at real, synthetic int default 1, status text default 'active');
create table if not exists voice_users(
  id text primary key, name text, billing_email text, licensed_voice_ids text);
create table if not exists scans(
  id text primary key, file_id text, file_name text, user_id text, created_at real, result_json text,
  invoice_id text, invoice_status text, invoice_url text, kind text);
create table if not exists uses(
  id text primary key, seq integer unique, scan_id text, voice_id text, user_id text, file_name text,
  seconds real, is_clone int, clone_prob real, confidence real, use_type text, decision text,
  rate_cents_per_min int, amount_cents int, platform_fee_cents int, royalty_cents int,
  invoice_id text, payout_batch_id text, payout_fee_cents int, status text, created_at real,
  prev_hash text, hash text);
create table if not exists alerts(
  id integer primary key autoincrement, voice_id text, scan_id text, kind text, message text, created_at real);
create table if not exists webhook_events(
  id text primary key, type text, verified int, resource_id text, received_at real, action text);
"""

# Fields covered by the ledger hash (immutable facts at the time of detection)
HASHED = ["id", "seq", "scan_id", "voice_id", "user_id", "file_name", "seconds", "is_clone", "confidence",
          "use_type", "decision", "rate_cents_per_min", "amount_cents", "platform_fee_cents", "royalty_cents",
          "created_at"]


def conn():
    c = sqlite3.connect(DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init():
    with conn() as c:
        c.executescript(SCHEMA)


def rows(sql, *a):
    with conn() as c:
        return [dict(r) for r in c.execute(sql, a).fetchall()]


def one(sql, *a):
    r = rows(sql, *a)
    return r[0] if r else None


def execute(sql, *a):
    with _lock, conn() as c:
        c.execute(sql, a)


def append_use(u: dict):
    """Append one ledger row with its hash-chain link. Serialised by a lock."""
    with _lock, conn() as c:
        last = c.execute("select seq, hash from uses order by seq desc limit 1").fetchone()
        u["seq"] = (last["seq"] + 1) if last else 1
        prev = last["hash"] if last else "0" * 64
        u["created_at"] = u.get("created_at") or time.time()
        entry = {k: u.get(k) for k in HASHED}
        u["prev_hash"], u["hash"] = prev, billing.entry_hash(prev, entry)
        cols = list(u.keys())
        c.execute(f"insert into uses({','.join(cols)}) values ({','.join('?' * len(cols))})",
                  [u[k] for k in cols])
    return u


def verify_ledger():
    rs = rows("select * from uses order by seq")
    bad = billing.verify_chain([({k: r[k] for k in HASHED}, r["prev_hash"], r["hash"]) for r in rs])
    return {"entries": len(rs), "valid": bad == -1, "first_bad_seq": None if bad == -1 else rs[bad]["seq"]}


def voice(vid):
    v = one("select * from voices where id=?", vid)
    if v:
        v["policy"] = json.loads(v.pop("policy_json"))
        v["consent"] = json.loads(v.pop("consent_json") or "{}")
    return v


def voices():
    return [voice(r["id"]) for r in rows("select id from voices order by enrolled_at")]
