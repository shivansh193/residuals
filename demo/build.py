"""Build the Hyperframes composition (composition/index.html) and timeline.json from marks.json.

python build.py <data_dir> <out_dir>
data_dir has marks.json and narration.json; clips are expected at <out_dir>/clips/<name>.mp4.
"""
import html, json, os, sys

DATA, OUT = sys.argv[1], sys.argv[2]
M = json.load(open(os.path.join(DATA, "marks.json")))
FPS, W, H = 30, 1920, 1080
TARGET_MAX = 178.0
CARD = 1.5
ACCENT = "#ff4f1a"


def seg(clip, a, b):
    assert b > a, (clip, a, b)
    return (clip, round(a, 2), round(b, 2))


e, p, o, w = M["enrol"], M["preclear"], M["offers"], M["owner"]
# (kind, id, payload). Cut points come from the recorded marks.
PLAN = [
    ("slide", "hook", 4.0),
    ("slide", "title", 4.0),
    ("slide", "glance", 10.0),
    ("card", "enrol", "Enrol, with consent"),
    ("clip", "enrol", [seg("enrol", e["loaded"] - 0.4, e["liveness"] + 3.0),
                       seg("enrol", e["typed"] - 1.7, e["parse_clicked"] + 0.9),
                       seg("enrol", e["policy_shown"] - 0.9, e["end"])]),
    ("slide", "detect", 8.0),
    ("card", "preclear", "Pre-clear an ad"),
    ("clip", "preclear", [seg("preclear", p["loaded"] - 0.5, p["hover_segment"] + 3.4),
                          seg("preclear", p["scan_clicked"] - 0.8, p["result_read"] + 0.1)]),
    ("card", "pay", "Paid through PayPal"),
    ("clip", "pay", [seg("preclear", p["invoice_panel"] - 0.3, p["mark_paid"] + 1.4),
                     seg("preclear", p["webhook_paid"] - 0.5, p["webhook_paid"] + 3.2),
                     seg("preclear", p["payout_confirmed"] - 0.5, p["end"])]),
    ("slide", "paypal", 8.0),
    ("card", "offers", "No licence? No lawsuit."),
    # the logged "blocked" mark fired early, so the second cut starts from the scan click
    ("clip", "offers", [seg("offers", o["scan1"] - 2.5, o["offer_invoice"] + 3.0),
                        seg("offers", o["scan2"] - 1.0, o["end"])]),
    ("card", "owner", "The owner's ledger"),
    ("clip", "owner", [seg("owner", w["loaded"] - 0.3, w["ledger"]),
                       seg("owner", w["paypal_columns"] - 3.5, w["end"])]),
    ("slide", "results", 10.0),
    ("slide", "outro", 7.0),
]

# Captions per recorded chapter: (seconds into the chapter, text)
CAPTIONS = {
    "enrol": [(0.2, "Only the owner can enrol. A random phrase stops enrolment from an old recording."),
              (8.0, "Terms in plain English, as the owner would say them."),
              (12.8, "Gemini turns them into a policy. The owner confirms it.")],
    "preclear": [(0.2, "A brand pre-clears its radio ad. Demo files were analysed on a Kaggle GPU."),
                 (6.0, "Bryntum timeline: Mara Vell's voice, found as an AI clone."),
                 (12.6, "Pre-clearance prices each voice by its owner's own terms.")],
    "pay": [(0.2, "One PayPal invoice (Invoicing v2) for the licensed minutes."),
            (5.5, "Paid in the PayPal sandbox. The webhook takes about a minute (cut)."),
            (8.4, "Signed INVOICING.INVOICE.PAID verified → PayPal Payout to each owner."),
            (12.0, "Payout confirmed by webhook. Real PayPal IDs, fees shown.")],
    "offers": [(0.2, "QuickClips holds no licences."),
               (2.8, "So it gets a retroactive licence offer, not a lawsuit."),
               (15.8, "Measure 12 is political. Both owners block that."),
               (18.0, "No offer at all: the use is blocked and the owners are alerted.")],
    "owner": [(0.2, "The owner's dashboard: royalties paid out, hash chain intact, alerts."),
              (7.3, "AG Grid ledger: every use, with its PayPal invoice and payout IDs.")],
}

SLIDES = {
    "hook": ("", "“Two voice actors say they heard their own voices in videos they never recorded.”",
             [], "Lehrman & Sage v. Lovo, S.D.N.Y. 2024 · CBS News"),
    "title": ("PayPal AI Hackathon", "Residuals", [], "Royalties for licensed AI voice clones, paid through PayPal."),
    "glance": ("At a glance", "Consent → detection → PayPal → royalty", [
        ("Enrol", "Consent statement + random liveness phrase, checked by Gemini"),
        ("Terms", "Plain English → structured policy (Gemini), confirmed by the owner"),
        ("Detect", "VAD · ECAPA voice match · clone probe · Whisper (Kaggle GPU)"),
        ("Bill", "PayPal Invoicing v2: one invoice per scan"),
        ("Pay", "Signed webhook → PayPal Payouts to each owner"),
        ("Record", "Hash-chained ledger · AG Grid · Bryntum · Render · APIMatic SDKs")], ""),
    "detect": ("How detection works", "From audio to minutes per voice", [
        ("Silero VAD", "Finds speech"),
        ("ECAPA-TDNN", "1.5 s windows matched to enrolled voices, calibrated threshold"),
        ("Clone probe", "wav2vec2 features, leave-one-persona-out"),
        ("Whisper small", "Transcript, mapped to segments"),
        ("Gemini", "Use type: ad, game, political, non-profit…"),
        ("Kaggle T4", "Run ahead of time for the 5 demo files")], ""),
    "paypal": ("PayPal, end to end", "Sandbox, verified at every step", [
        ("Invoicing v2", "Cent-rounded line per voice · PayPal-Request-Id per scan"),
        ("Webhooks", "INVOICING.INVOICE.PAID and PAYOUTS-ITEM.* verified by PayPal"),
        ("Payouts", "sender_batch_id = roy-{invoice}-{voice}: a retry can't pay twice"),
        ("Fees in the open", "10% platform fee per line · PayPal's $0.25 payout fee shown"),
        ("Sandbox finding", "Per-use payouts would cost more than they pay → batch per invoice")], ""),
    "results": ("Results (5 synthetic personas, 400 clips)", "What we measured, including what's weak", [
        ("Speaker match", "EER 0% on whole clips (originals and clones) · 1.1% on 1.5 s windows"),
        ("Clone detection", "89.8% accuracy, but 14.5% false positives → shown as evidence, never billed"),
        ("Minutes", "MAPE 10.8% · always under-counts (−12.9%), so it never over-bills"),
        ("Use type", "Gemini: 5/5 demo files, 40/40 labelled sentences"),
        ("Honest limit", "Synthetic voices only. The pretrained deepfake detector flagged nothing as fake.")], ""),
    "outro": ("", "Your voice. Your terms. Your royalties.", [],
              "residuals.onrender.com · github.com/shivansh193/residuals · Built with PayPal, Gemini, AG Grid, Bryntum, Render, APIMatic · Every voice is a fictional synthetic persona."),
}

# ---------- lay out the timeline ----------
t = 0.0
sections, videos, captions, timeline = [], [], [], []
for kind, sid, payload in PLAN:
    if kind == "slide":
        sections.append(("slide", sid, t, payload)); timeline.append({"section": sid, "start": t, "dur": payload})
        t += payload
    elif kind == "card":
        sections.append(("card", sid, t, CARD, payload)); timeline.append({"section": sid, "start": t, "dur": None})
        t += CARD
    else:
        start = t
        for clip, a, b in payload:
            videos.append((clip, t, b - a, a)); t += b - a
        for off, text in CAPTIONS[sid]:
            captions.append((start + off, text))
        timeline[-1]["dur"] = round(t - timeline[-1]["start"], 2)
TOTAL = round(t, 2)
assert TOTAL <= TARGET_MAX, f"plan is {TOTAL}s, over {TARGET_MAX}s"
caps = sorted(captions)
cap_items = []
for i, (s, text) in enumerate(caps):
    nxt = caps[i + 1][0] if i + 1 < len(caps) else s + 6
    end = min(nxt, s + 7.5)
    # a caption never runs into a slide or card
    for sec in sections:
        if sec[2] > s:
            end = min(end, sec[2]); break
    cap_items.append((s, round(end - s, 2), text))
for a, b in zip(cap_items, cap_items[1:]):
    assert a[0] + a[1] <= b[0] + 1e-6, "captions overlap"

# ---------- HTML ----------
def esc(x):
    return html.escape(x, quote=True)


parts = []
els = []  # (id, start, dur) for GSAP fades
n = 0
for s in sections:
    n += 1
    if s[0] == "card":
        _, sid, st, dur, title = s
        els.append((f"s{n}", st, dur))
        parts.append(f'<section id="s{n}" class="card-sec" data-start="{st:.2f}" data-duration="{dur:.2f}" data-track-index="3">'
                     f'<div class="chap mono">CHAPTER</div><div class="chapt">{esc(title)}</div></section>')
        continue
    _, sid, st, dur = s
    eyebrow, head, cards, foot = SLIDES[sid]
    els.append((f"s{n}", st, dur))
    cls = "slide " + sid
    grid = "".join(f'<div class="c stag"><div class="mono k">{esc(k)}</div><div class="v">{esc(v)}</div></div>' for k, v in cards)
    parts.append(f'<section id="s{n}" class="{cls}" data-start="{st:.2f}" data-duration="{dur:.2f}" data-track-index="3">'
                 + (f'<div class="mono eyebrow">{esc(eyebrow)}</div>' if eyebrow else "")
                 + f'<h1 class="{"big" if not cards else ""}">{esc(head)}</h1>'
                 + (f'<div class="cards n{len(cards)}">{grid}</div>' if cards else "")
                 + (f'<div class="foot">{esc(foot)}</div>' if foot else "") + "</section>")
vid_html = []
for i, (clip, st, dur, ms) in enumerate(videos):
    vid_html.append(f'<video id="v{i}" class="rec" src="clips/{clip}.mp4" muted playsinline data-start="{st:.2f}" '
                    f'data-duration="{dur:.2f}" data-media-start="{ms:.2f}" data-track-index="1"></video>')
cap_html = [f'<div id="c{i}" class="cap" data-start="{s:.2f}" data-duration="{d:.2f}" data-track-index="2">{esc(tx)}</div>'
            for i, (s, d, tx) in enumerate(cap_items)]

js_fades = []
for el, st, dur in els:
    js_fades.append(f'tl.fromTo("#{el}", {{opacity:0}}, {{opacity:1, duration:0.35}}, {st:.2f});')
    js_fades.append(f'tl.fromTo("#{el} .stag", {{opacity:0, y:18}}, {{opacity:1, y:0, duration:0.45, stagger:0.12}}, {st + 0.25:.2f});')
    js_fades.append(f'tl.to("#{el}", {{opacity:0, duration:0.3}}, {st + dur - 0.3:.2f});')
for i, (s, d, _) in enumerate(cap_items):
    js_fades.append(f'tl.fromTo("#c{i}", {{opacity:0, y:8}}, {{opacity:1, y:0, duration:0.3}}, {s:.2f});')
    js_fades.append(f'tl.to("#c{i}", {{opacity:0, duration:0.25}}, {s + d - 0.25:.2f});')
# recording frame visible whenever a clip plays
js_fades.append(f'tl.set("#frame", {{opacity:0}}, 0);')
for clip, st, dur, ms in videos:
    js_fades.append(f'tl.set("#frame", {{opacity:1}}, {st:.2f}); tl.set("#frame", {{opacity:0}}, {st + dur:.2f});')
js_fades.append(f'tl.set({{}}, {{}}, {TOTAL:.2f});')

CSS = f"""
@font-face {{ font-family: Geist; src: url(fonts/Geist-Regular.woff2) format('woff2'); font-weight: 400; }}
@font-face {{ font-family: Geist; src: url(fonts/Geist-SemiBold.woff2) format('woff2'); font-weight: 600; }}
@font-face {{ font-family: GeistMono; src: url(fonts/GeistMono-Regular.woff2) format('woff2'); }}
* {{ box-sizing: border-box; margin: 0; }}
html, body {{ width: {W}px; height: {H}px; background: #f4efe6; overflow: hidden; }}
#root {{ position: relative; width: {W}px; height: {H}px; background: #f4efe6; font-family: Geist, sans-serif; color: #141210; }}
.mono {{ font-family: GeistMono, monospace; }}
#frame {{ position: absolute; left: 192px; top: 24px; width: 1536px; height: 960px; border-radius: 22px; background: #fff;
  box-shadow: 0 24px 60px rgba(20,18,16,.18), 0 2px 6px rgba(20,18,16,.08); }}
video.rec {{ position: absolute; left: 192px; top: 24px; width: 1536px; height: 960px; border-radius: 22px; object-fit: cover; }}
.cap {{ position: absolute; left: 192px; width: 1536px; top: 1002px; height: 60px; display: flex; align-items: center; justify-content: center;
  font-size: 30px; font-weight: 600; letter-spacing: -.01em; opacity: 0; }}
.cap::before {{ content: ''; width: 10px; height: 10px; border-radius: 50%; background: {ACCENT}; margin-right: 16px; flex: none; }}
section {{ position: absolute; inset: 0; padding: 120px 160px; opacity: 0; background: #f4efe6; }}
.card-sec {{ display: flex; flex-direction: column; justify-content: center; }}
.chap {{ font-size: 22px; letter-spacing: .3em; color: {ACCENT}; margin-bottom: 20px; }}
.chapt {{ font-size: 96px; font-weight: 600; letter-spacing: -.035em; }}
.eyebrow {{ font-size: 22px; letter-spacing: .22em; text-transform: uppercase; color: {ACCENT}; margin-bottom: 18px; }}
h1 {{ font-size: 64px; font-weight: 600; letter-spacing: -.03em; line-height: 1.05; margin-bottom: 48px; }}
h1.big {{ font-size: 120px; margin-top: 140px; }}
.hook h1.big {{ font-size: 72px; line-height: 1.15; margin-top: 200px; max-width: 1500px; font-weight: 400; }}
.title h1.big {{ font-size: 180px; margin-top: 210px; }}
.title h1.big::after {{ content: '.'; color: {ACCENT}; }}
.outro h1.big {{ font-size: 110px; margin-top: 230px; }}
.cards {{ display: grid; gap: 22px; grid-template-columns: repeat(3, 1fr); }}
.cards.n5 {{ grid-template-columns: repeat(3, 1fr); }}
.c {{ background: #fbf8f2; border: 1px solid #d9d0bf; border-radius: 18px; padding: 30px 32px; min-height: 190px; }}
.k {{ font-size: 20px; letter-spacing: .12em; text-transform: uppercase; color: {ACCENT}; margin-bottom: 14px; }}
.v {{ font-size: 30px; line-height: 1.3; }}
.foot {{ position: absolute; left: 160px; right: 160px; bottom: 110px; font-size: 30px; color: #4a443c; }}
.results .c:nth-child(2) .v, .results .c:nth-child(5) .v {{ color: #b3261e; }}
"""

doc = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Residuals demo</title><style>{CSS}</style>
<script src="gsap.min.js"></script></head>
<body>
<div id="root" data-composition-id="residuals-demo" data-duration="{TOTAL:.2f}" data-width="{W}" data-height="{H}" data-fps="{FPS}">
<div id="frame"></div>
{''.join(vid_html)}
{''.join(cap_html)}
{''.join(parts)}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{paused: true}});
{chr(10).join(js_fades)}
window.__timelines.main = tl;
</script>
</body></html>"""

os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(doc)
json.dump({"total": TOTAL, "sections": timeline, "captions": cap_items}, open(os.path.join(OUT, "timeline.json"), "w"), indent=1)
print("total", TOTAL, "s;", len(videos), "cuts;", len(cap_items), "captions")
for s in timeline:
    print(f"  {s['section']:<10} {s['start']:7.2f}  {s['dur']}")
