"""Record the demo chapters against the live site with a scripted, human-paced browser.

python demo/record.py [chapter ...]     chapters: enrol preclear offers owner (default: all)
Outputs demo/rec/<chapter>.webm and demo/rec/marks.json (seconds from each recording's start).
"""
import asyncio, json, os, sys, time, urllib.request

from playwright.async_api import async_playwright

BASE = os.environ.get("DEMO_BASE", "https://residuals.onrender.com")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rec")
VW, VH = 1440, 900
os.makedirs(OUT, exist_ok=True)
MARKS_PATH = os.path.join(OUT, "marks.json")
MARKS = json.load(open(MARKS_PATH)) if os.path.exists(MARKS_PATH) else {}

CURSOR = """
(() => {
  const add = () => {
    if (document.getElementById('__cur')) return;
    const d = document.createElement('div'); d.id = '__cur';
    Object.assign(d.style, {position:'fixed', left:'-40px', top:'-40px', width:'22px', height:'22px', borderRadius:'50%',
      background:'rgba(255,79,26,.35)', border:'2px solid #ff4f1a', zIndex:2147483647, pointerEvents:'none',
      transform:'translate(-50%,-50%)', transition:'width .12s, height .12s, background .12s'});
    document.body.appendChild(d);
    addEventListener('mousemove', e => { d.style.left = e.clientX + 'px'; d.style.top = e.clientY + 'px'; }, true);
    addEventListener('mousedown', () => { d.style.width = d.style.height = '14px'; d.style.background = 'rgba(255,79,26,.7)'; }, true);
    addEventListener('mouseup', () => { d.style.width = d.style.height = '22px'; d.style.background = 'rgba(255,79,26,.35)'; }, true);
  };
  if (document.body) add(); else addEventListener('DOMContentLoaded', add);
})();
"""


class Take:
    def __init__(self, name, page):
        self.name, self.page, self.t0, self.marks = name, page, time.monotonic(), {}
        self.mx, self.my = VW / 2, VH / 2

    def mark(self, key):
        self.marks[key] = round(time.monotonic() - self.t0, 2)
        print(f"  [{self.name}] {key} @ {self.marks[key]}s", flush=True)

    async def glide(self, loc):
        await loc.scroll_into_view_if_needed()
        b = await loc.bounding_box()
        x, y = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
        await self.page.mouse.move(x, y, steps=28)
        self.mx, self.my = x, y
        await self.page.wait_for_timeout(250)

    async def click(self, loc, pause=900):
        await self.glide(loc)
        await self.page.mouse.down(); await self.page.wait_for_timeout(90); await self.page.mouse.up()
        await self.page.wait_for_timeout(pause)

    async def scroll_to(self, loc, block="center"):
        await loc.evaluate(f"e => e.scrollIntoView({{behavior:'smooth', block:'{block}'}})")
        await self.page.wait_for_timeout(1100)


def warm():
    for _ in range(30):
        try:
            if b"ok" in urllib.request.urlopen(BASE + "/health", timeout=30).read():
                return
        except Exception:
            pass
        time.sleep(5)
    raise SystemExit("site not reachable")


async def enrol(t: Take):
    p = t.page
    await p.goto(BASE + "/enrol"); await p.wait_for_selector("text=Read aloud")
    await p.wait_for_timeout(1500); t.mark("loaded")
    await t.click(p.get_by_placeholder("Name you perform under"), 300)
    await p.keyboard.type("Mara Vell", delay=70)
    await p.wait_for_timeout(600)
    await t.glide(p.locator("text=2. Liveness phrase")); t.mark("liveness"); await p.wait_for_timeout(2600)
    ta = p.locator("textarea")
    await t.click(ta, 200)
    await p.keyboard.press("Control+A"); await p.keyboard.press("Delete")
    await p.keyboard.type("$30 a minute for ads, $8 for audiobooks, free for non-profits, never for politics. Credit me.", delay=28)
    t.mark("typed"); await p.wait_for_timeout(700)
    await t.click(p.get_by_role("button", name="Turn into a policy with Gemini"), 200)
    t.mark("parse_clicked")
    await p.wait_for_selector("text=Check this is what you meant", timeout=90000)
    t.mark("policy_shown")
    await t.scroll_to(p.locator("text=Check this is what you meant"))
    await p.wait_for_timeout(3500); t.mark("end")


async def preclear(t: Take):
    p = t.page
    await p.goto(BASE + "/preclear"); await p.wait_for_selector("text=Brightline spring campaign")
    await p.wait_for_timeout(2500); t.mark("loaded")
    await t.click(p.get_by_role("button", name="▶ Play"), 300); t.mark("play")
    await p.wait_for_timeout(5500)
    ev = p.locator(".b-sch-event").first
    await t.glide(ev); t.mark("hover_segment"); await p.wait_for_timeout(2800)
    await t.click(p.get_by_role("button", name="❚❚ Pause"), 500)
    await t.click(p.get_by_role("button", name="Scan for registered voices →"), 200); t.mark("scan_clicked")
    await p.wait_for_selector("text=registered voices found", timeout=90000); t.mark("result")
    await t.scroll_to(p.locator("text=registered voices found"), "start")
    await p.wait_for_timeout(3500); t.mark("result_read")
    # ---- PayPal ----
    panel = p.locator("text=PayPal Invoicing v2 · sandbox")
    await t.scroll_to(panel, "start"); t.mark("invoice_panel"); await p.wait_for_timeout(2500)
    inv = (await p.locator(".ppid").first.inner_text()).strip()
    await t.glide(p.get_by_role("link", name="Pay with PayPal")); await p.wait_for_timeout(1200)
    await t.click(p.get_by_role("button", name="Mark paid (sandbox)"), 300); t.mark("mark_paid")
    await p.wait_for_selector("text=PayPal sent INVOICING.INVOICE.PAID", timeout=300000); t.mark("webhook_paid")
    await p.wait_for_selector("text=PAYMENT.PAYOUTS-ITEM.SUCCEEDED received and verified", timeout=300000)
    t.mark("payout_confirmed")
    await t.glide(p.locator("table")); await p.wait_for_timeout(4000); t.mark("end")
    t.marks["invoice_id"] = inv


async def offers(t: Take):
    p = t.page
    await p.goto(BASE + "/preclear"); await p.wait_for_selector("text=Life hacks")
    await p.wait_for_timeout(1500); t.mark("loaded")
    sel = p.locator("select").first
    await t.glide(sel); await sel.select_option("quickclips"); await p.wait_for_timeout(900)
    await t.click(p.locator("button", has_text="QuickClips 'Life hacks' compilation"), 1500)
    await t.click(p.get_by_role("button", name="Scan for registered voices →"), 200); t.mark("scan1")
    await p.wait_for_selector("text=retroactive licence offered", timeout=90000); t.mark("offer")
    await t.scroll_to(p.locator("text=registered voices found"), "start"); await p.wait_for_timeout(2500)
    await t.glide(p.locator("text=takedown request template").first); await p.wait_for_timeout(1800)
    await t.scroll_to(p.locator("text=Retroactive licence offer:"), "center"); t.mark("offer_invoice")
    await p.wait_for_timeout(3000)
    await p.evaluate("window.scrollTo({top:0, behavior:'smooth'})"); await p.wait_for_timeout(1200)
    await t.glide(sel); await sel.select_option("measure12"); await p.wait_for_timeout(900)
    await t.click(p.locator("button", has_text="Measure 12 campaign spot"), 1500)
    await t.click(p.get_by_role("button", name="Scan for registered voices →"), 200); t.mark("scan2")
    await p.wait_for_selector("text=Blocked category", timeout=90000); t.mark("blocked")
    await t.scroll_to(p.locator("text=registered voices found"), "start")
    await p.wait_for_timeout(4500); t.mark("end")


async def owner(t: Take):
    p = t.page
    await p.goto(BASE + "/owner/mara"); await p.wait_for_selector("text=Royalties paid out")
    await p.wait_for_selector(".ag-row", timeout=30000)
    await p.wait_for_timeout(2500); t.mark("loaded")
    await t.glide(p.locator("text=Hash chain intact")); await p.wait_for_timeout(1500)
    await t.glide(p.locator("text=Blocked use").first); t.mark("alert"); await p.wait_for_timeout(2500)
    await t.scroll_to(p.locator("text=Usage ledger"), "start"); t.mark("ledger")
    await p.wait_for_timeout(1500)
    vp = p.locator(".ag-center-cols-viewport")
    await t.glide(vp)
    for _ in range(6):
        await vp.evaluate("e => e.scrollBy({left: 260, behavior: 'smooth'})"); await p.wait_for_timeout(700)
    t.mark("paypal_columns"); await p.wait_for_timeout(3500); t.mark("end")


CHAPTERS = {"enrol": enrol, "preclear": preclear, "offers": offers, "owner": owner}


async def main(names):
    warm()
    async with async_playwright() as pw:
        br = await pw.chromium.launch(headless=True)
        for name in names:
            print("recording", name, flush=True)
            ctx = await br.new_context(viewport={"width": VW, "height": VH}, record_video_dir=OUT,
                                       record_video_size={"width": VW, "height": VH}, device_scale_factor=1)
            await ctx.add_init_script(CURSOR)
            page = await ctx.new_page()
            t = Take(name, page)
            try:
                await CHAPTERS[name](t)
            finally:
                path = await page.video.path()
                await ctx.close()
                dst = os.path.join(OUT, f"{name}.webm")
                if os.path.exists(dst):
                    os.remove(dst)
                os.replace(path, dst)
                MARKS[name] = t.marks
                json.dump(MARKS, open(MARKS_PATH, "w"), indent=1)
        await br.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or list(CHAPTERS)))
