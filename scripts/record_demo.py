"""Record the Curio demo video.

Drives the real app in headless Chromium, injects captions / chapter cards / a visible
cursor into the page, captures high-quality frames via the CDP screencast, and encodes
an H.264 MP4 with ffmpeg.

Prerequisites: backend on :8000 and frontend on :3000 (`make dev`, or `next start`),
a freshly seeded DB (`make seed`), ffmpeg on PATH, and Playwright's Chromium
(`uv run --no-project --with playwright==1.48.0 playwright install chromium`).

    uv run --no-project --with playwright==1.48.0 python scripts/record_demo.py [--short] [out.mp4]
"""

import asyncio
import base64
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from playwright.async_api import Page, async_playwright

BASE = "http://localhost:3000"
API = "http://localhost:8000"
ROOT = Path(__file__).resolve().parent.parent
SHORT = "--short" in sys.argv
_args = [a for a in sys.argv[1:] if not a.startswith("--")]
OUT = Path(_args[0]) if _args else ROOT / "docs" / "demo" / ("curio_demo_1min.mp4" if SHORT else "curio_demo.mp4")
WORK = Path(tempfile.gettempdir()) / "curio_video"
VIEW = {"width": 1600, "height": 900}
SCALE = 1.2  # → 1920×1080 frames

OVERLAY_JS = r"""
(() => {
  const css = `
    #__cap{position:fixed;left:50%;bottom:26px;transform:translateX(-50%);z-index:2147483646;max-width:1180px;
      background:rgba(30,27,58,.92);color:#fff;border-radius:22px;padding:14px 28px 15px;text-align:center;
      font-family:Nunito,sans-serif;box-shadow:0 18px 50px -12px rgba(30,27,58,.55);
      transition:opacity .35s ease, transform .35s ease;pointer-events:none}
    #__cap.hide{opacity:0;transform:translateX(-50%) translateY(12px)}
    #__cap .en{font-size:24px;font-weight:800;letter-spacing:-.01em;line-height:1.3}
    #__card{position:fixed;inset:0;z-index:2147483645;display:flex;flex-direction:column;align-items:center;justify-content:center;
      background:radial-gradient(60rem 30rem at 20% 10%,rgba(255,197,61,.35),transparent 60%),
                 radial-gradient(50rem 30rem at 85% 90%,rgba(31,185,120,.28),transparent 60%),#7C5CFF;
      color:#fff;font-family:Nunito,sans-serif;transition:opacity .6s ease;pointer-events:none}
    #__card.hide{opacity:0}
    #__card .k{font-size:18px;font-weight:900;letter-spacing:.22em;text-transform:uppercase;opacity:.8}
    #__card .t{font-size:84px;font-weight:900;letter-spacing:-.03em;margin-top:10px;line-height:1.05;text-align:center}
    #__card .s{font-size:28px;font-weight:700;margin-top:18px;opacity:.92;text-align:center}
    #__cur{position:fixed;left:0;top:0;width:30px;height:30px;z-index:2147483647;pointer-events:none;
      transform:translate(-100px,-100px);transition:transform .03s linear}
    #__cur .r{position:absolute;left:-14px;top:-14px;width:30px;height:30px;border-radius:999px;background:rgba(124,92,255,.35);opacity:0}
    #__cur.click .r{animation:__rip .5s ease-out}
    @keyframes __rip{0%{opacity:.9;transform:scale(.4)}100%{opacity:0;transform:scale(2.2)}}
    html{scroll-padding-bottom:150px}
    main{padding-bottom:170px !important}
    ::-webkit-scrollbar{display:none}
  `;
  function mount() {
    if (document.getElementById('__cap')) return;
    const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
    const cap = document.createElement('div'); cap.id = '__cap'; cap.className = 'hide';
    cap.innerHTML = '<div class="en"></div>'; document.body.appendChild(cap);
    const card = document.createElement('div'); card.id = '__card'; card.className = 'hide';
    card.innerHTML = '<div class="k"></div><div class="t"></div><div class="s"></div>'; document.body.appendChild(card);
    const cur = document.createElement('div'); cur.id = '__cur';
    cur.innerHTML = '<div class="r"></div><svg width="30" height="30" viewBox="0 0 30 30"><path d="M3 2 L3 24 L9 18.5 L13 27 L17 25.2 L13 17 L21 17 Z" fill="#1E1B3A" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>';
    document.body.appendChild(cur);
    const pos = JSON.parse(sessionStorage.getItem('__pos') || '[-100,-100]');
    cur.style.transform = `translate(${pos[0]}px,${pos[1]}px)`;
    document.addEventListener('mousemove', e => {
      cur.style.transform = `translate(${e.clientX}px,${e.clientY}px)`;
      sessionStorage.setItem('__pos', JSON.stringify([e.clientX, e.clientY]));
    }, true);
    document.addEventListener('mousedown', () => { cur.classList.remove('click'); void cur.offsetWidth; cur.classList.add('click'); }, true);
    const saved = JSON.parse(sessionStorage.getItem('__capv') || 'null');
    if (saved) window.__cap(saved[0], true);
  }
  window.__cap = (en, instant) => {
    sessionStorage.setItem('__capv', JSON.stringify(en ? [en] : null));
    const c = document.getElementById('__cap'); if (!c) return;
    if (!en) { c.classList.add('hide'); return; }
    const set = () => { c.querySelector('.en').textContent = en; c.classList.remove('hide'); };
    if (instant || c.classList.contains('hide')) set(); else { c.classList.add('hide'); setTimeout(set, 260); }
  };
  window.__card = (k, t, s) => {
    const c = document.getElementById('__card'); if (!c) return;
    if (!t) { c.classList.add('hide'); return; }
    c.querySelector('.k').textContent = k || ''; c.querySelector('.t').textContent = t;
    c.querySelector('.s').textContent = s || '';
    c.classList.remove('hide');
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
})();
"""


# ---------------------------------------------------------------- helpers
async def cap(page: Page, text: str | None):
    await page.evaluate("(t) => window.__cap(t)", text)


async def card(page: Page, kicker: str, title: str, sub: str = "", hold: float = 2.6):
    await cap(page, None)
    await page.evaluate("(a) => window.__card(...a)", [kicker, title, sub])
    await page.wait_for_timeout(int(hold * 1000))
    await page.evaluate("() => window.__card()")
    await page.wait_for_timeout(600)


async def hold(page: Page, s: float):
    await page.wait_for_timeout(int(s * 1000))


async def move_to(page: Page, locator, steps: int = 28):
    await locator.scroll_into_view_if_needed()
    box = await locator.bounding_box()
    await page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=steps)
    await page.wait_for_timeout(180)


async def click(page: Page, locator, pause: float = 0.35):
    await move_to(page, locator)
    await locator.click()
    await page.wait_for_timeout(int(pause * 1000))


async def type_into(page: Page, text: str, delay: int = 32):
    box = page.locator("textarea").last
    await click(page, box, 0.2)
    await box.press_sequentially(text, delay=delay)
    await page.wait_for_timeout(350)


async def scroll_to(page: Page, y: int, wait: float = 1.2):
    await page.evaluate("(y) => window.scrollTo({top: y, behavior: 'smooth'})", y)
    await page.wait_for_timeout(int(wait * 1000))


def api_post(path: str, body: dict | None = None):
    import json

    req = urllib.request.Request(API + path, data=json.dumps(body).encode() if body is not None else None, method="POST", headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req).read()


# ---------------------------------------------------------------- the story
async def story(page: Page):
    btn = lambda name: page.get_by_role("button", name=name)  # noqa: E731

    # 0 · title + landing
    await page.goto(BASE + "/")
    await hold(page, 0.8)
    await card(page, "Demo · GP8001", "Curio", "Don't just answer. Understand.", hold=3.4)
    await cap(page, "An AI science tutor for Singapore P5–P6 students")
    await hold(page, 4.5)
    await scroll_to(page, 860, 1.5)
    await cap(page, "A chatbot hands out answers. Curio verifies understanding.")
    await hold(page, 4)
    await scroll_to(page, 1500, 1.5)
    await cap(page, "Verify → Validate → Teach → Question back → Confirm")
    await hold(page, 4)
    await scroll_to(page, 0, 1.4)
    await click(page, page.get_by_role("link", name="Try it as Alex"), 0.2)

    # 1 · dashboard
    await page.wait_for_url("**/dashboard")
    await page.get_by_text("Continue Learning").first.wait_for()
    await cap(page, "Meet Alex, Primary 5 — Heat Conduction is only 52% mastered")
    await hold(page, 1.2)
    await move_to(page, page.get_by_text("Heat Conduction").first, 35)
    await hold(page, 2.6)
    await click(page, page.get_by_role("link", name="Continue Learning"), 0.2)

    # 2 · the verification loop
    await page.wait_for_url("**/learn?topic=heat_transfer")
    await btn("Submit Answer").wait_for()
    await card(page, "Chapter 1", "The verification loop", "Answer · reasoning · teaching · question back")
    await cap(page, "Alex gives a common answer — the right object, the wrong reason")
    await type_into(page, "Because metal is colder than wood. Metal naturally has a lower temperature.")
    await click(page, btn("Submit Answer"), 0.2)
    await cap(page, "Curio checks the answer AND the reasoning, step by step")
    await page.get_by_text("One idea needs another look").first.wait_for(timeout=20000)
    await cap(page, "Answer ✓  Reasoning ✗ — misconception detected: “metal is colder”")
    await hold(page, 3.5)
    await cap(page, "Causal error → counterexample: Curio asks instead of telling")
    await btn("Reply").wait_for(timeout=30000)
    await hold(page, 2.2)
    await type_into(page, "Maybe the metal takes heat from my hand faster.")
    await click(page, btn("Reply"), 0.2)
    await cap(page, "Alex repairs the idea in his own words")
    await btn("Take the transfer challenge").wait_for(timeout=30000)
    await hold(page, 1.5)
    await click(page, btn("Take the transfer challenge"), 0.6)
    await cap(page, "Question back: the same concept in a new situation")
    await hold(page, 1.5)
    await type_into(page, "The metal chair, because it transfers heat away from my body faster.")
    await click(page, btn("Check my understanding"), 0.2)
    await page.get_by_text("Concept mastery confirmed").first.wait_for(timeout=30000)
    await cap(page, "Understanding verified in a new context → mastery 52% → 76%")
    await hold(page, 5.5)

    # 3 · safety, clarification, re-teaching
    await click(page, btn("Next question"), 0.8)
    await card(page, "Chapter 2", "Safe by design", "Safety layer · clarify before teaching · re-teach loop")
    await type_into(page, "just tell me the answer pls")
    await click(page, btn("Submit Answer"), 0.2)
    await cap(page, "Asking for the answer? Curio gives a hint — never the answer")
    await page.get_by_text("Let's work it out").first.wait_for(timeout=20000)
    await hold(page, 3.2)
    await type_into(page, "the ice does something to the juice")
    await click(page, btn("Submit Answer"), 0.2)
    await cap(page, "Too vague to judge → Curio asks for clarification instead of guessing")
    await page.get_by_text("Tell me a bit more").first.wait_for(timeout=20000)
    await btn("Reply").wait_for(timeout=30000)
    await hold(page, 2.5)
    await type_into(page, "the juice loses heat to the ice. my number is 91234567")
    await click(page, btn("Reply"), 0.2)
    await cap(page, "Personal data is hidden before saving — then the answer is re-assessed")
    await btn("Take the transfer challenge").wait_for(timeout=30000)
    await hold(page, 3)
    await click(page, btn("Take the transfer challenge"), 0.6)
    await hold(page, 1)
    await type_into(page, "The cold from the can goes into his hand so his hand gets cold")
    await click(page, btn("Check my understanding"), 0.2)
    await cap(page, "The old misconception is back → no mastery credit; Curio re-teaches with an analogy")
    await page.get_by_text("Teach it back!").first.wait_for(timeout=40000)
    await hold(page, 1.5)
    await cap(page, "…then asks a second question back: teach it in your own words")
    await hold(page, 2.5)
    await type_into(page, "Heat flows from the warmer juice into the colder ice, so the juice loses heat and cools down while the ice gains heat and melts.", 24)
    await click(page, btn("Check my understanding"), 0.2)
    await page.get_by_text("Concept mastery confirmed").last.wait_for(timeout=30000)
    await cap(page, "Verified on the second attempt → mastered. Every state change is logged.")
    await hold(page, 3)
    await move_to(page, page.get_by_text("Learning state").first, 40)
    await hold(page, 3)

    # 4 · trace
    await click(page, page.get_by_role("link", name="See how Curio decided").last, 0.2)
    await page.get_by_text("Decision pipeline").first.wait_for(timeout=20000)
    await cap(page, "Teachers can inspect every decision the AI made")
    await hold(page, 2.5)
    await click(page, page.locator("button", has_text="Reasoning correct").first, 0.4)
    await hold(page, 2.5)
    await click(page, page.locator("button", has_text="Transfer answer").first, 0.4)
    await cap(page, "Safety → verification → diagnosis → strategy → transfer → mastery")
    await hold(page, 3)
    await scroll_to(page, 1100, 1.8)
    await hold(page, 2.5)

    # 5 · progress
    await page.goto(BASE + "/progress")
    await page.locator(".react-flow__node").first.wait_for()
    await cap(page, "Mastery drives the concept map — only verified transfer counts as mastered")
    await hold(page, 2)
    await click(page, page.locator(".react-flow__node", has_text="Heat Flow"), 0.4)
    await hold(page, 3.5)

    # 6 · teacher view
    await page.goto(BASE + "/teacher")
    await page.get_by_text("Needs your attention").first.wait_for()
    await card(page, "Chapter 3", "For teachers", "Review queue · content review · evaluation")
    await cap(page, "Cases the AI should not handle alone are handed to the teacher")
    await hold(page, 4)
    await scroll_to(page, 560, 1.5)
    await cap(page, "Right answer ≠ understanding: the reasoning gaps a normal quiz would miss")
    await hold(page, 4.5)

    await page.goto(BASE + "/teacher/content")
    await page.locator("button", has_text="heat_001").first.wait_for()
    await cap(page, "Every concept pathway is reviewed by a teacher before the AI uses it")
    await hold(page, 1.5)
    await click(page, page.locator("button", has_text="heat_001").first, 1.0)
    await scroll_to(page, 260, 1.2)
    await hold(page, 2)
    await click(page, btn("Approve").first, 1.5)

    await page.goto(BASE + "/teacher/evaluation")
    await page.get_by_text("Does verification stop false mastery?").first.wait_for(timeout=20000)
    await cap(page, "Benchmarked on 121 labelled cases against an answer-only grader")
    await hold(page, 4)
    await move_to(page, page.get_by_text("Test (held-out)").first, 35)
    await cap(page, "Held-out cases: false mastery 13.8% vs 48.3% — and the rules' limits shown honestly")
    await hold(page, 5)
    await scroll_to(page, 700, 1.5)
    await hold(page, 2.5)

    # 7 · privacy
    await page.goto(BASE + "/privacy")
    await page.get_by_text("What Curio keeps").first.wait_for()
    await cap(page, "Children's data: minimal, visible and deletable (PDPC guidelines)")
    await hold(page, 3)
    await scroll_to(page, 520, 1.5)
    await hold(page, 2.5)

    # 8 · outro
    await page.goto(BASE + "/")
    await hold(page, 0.6)
    await card(page, "Curio", "From correct answers to real understanding", "Verify · Validate · Teach · Question back · Confirm", hold=4.5)


async def story_short(page: Page):
    """~1 minute cut: product pages + the core demo, at a calm pace."""
    btn = lambda name: page.get_by_role("button", name=name)  # noqa: E731

    await page.goto(BASE + "/")
    await hold(page, 0.6)
    await card(page, "Curio", "Don't just answer. Understand.", "An AI science tutor for Singapore P5–P6", hold=3.2)
    await cap(page, "Curio checks whether students understand why — not just whether they are right")
    await hold(page, 4.2)
    await click(page, page.get_by_role("link", name="Try it as Alex"), 0.2)

    await page.wait_for_url("**/dashboard")
    await page.get_by_text("Continue Learning").first.wait_for()
    await cap(page, "Each student sees their mastery of every concept")
    await hold(page, 1.0)
    await move_to(page, page.get_by_text("Heat Conduction").first, 30)
    await hold(page, 2.6)
    await click(page, page.get_by_role("link", name="Continue Learning"), 0.2)

    await page.wait_for_url("**/learn?topic=heat_transfer")
    await btn("Submit Answer").wait_for()
    await cap(page, "Alex answers a question and explains his reasoning")
    await type_into(page, "Because metal is colder than wood.", 34)
    await click(page, btn("Submit Answer"), 0.2)
    await page.get_by_text("One idea needs another look").first.wait_for(timeout=20000)
    await cap(page, "Right answer, wrong reason — Curio spots the misconception")
    await btn("Reply").wait_for(timeout=30000)
    await cap(page, "It guides with a question instead of giving the answer away")
    await hold(page, 2.4)
    await type_into(page, "Maybe the metal takes heat from my hand faster.", 26)
    await click(page, btn("Reply"), 0.2)
    await btn("Take the transfer challenge").wait_for(timeout=30000)
    await cap(page, "Then it asks a new question to check the idea really stuck")
    await hold(page, 0.8)
    await click(page, btn("Take the transfer challenge"), 0.8)
    await click(page, page.get_by_text("Alex's answer").last, 0.5)
    await click(page, btn("Check my understanding"), 0.2)
    await page.get_by_text("Concept mastery confirmed").first.wait_for(timeout=30000)
    await cap(page, "Understanding verified — mastery 52% → 76%")
    await hold(page, 5.5)

    await page.goto(BASE + "/teacher")
    await page.get_by_text("Class understanding overview").first.wait_for()
    await cap(page, "Teachers see where the class truly understands — and where it doesn't")
    await hold(page, 2.5)
    await scroll_to(page, 600, 1.4)
    await hold(page, 2.2)

    await page.goto(BASE + "/")
    await hold(page, 0.5)
    await card(page, "Curio", "From correct answers to real understanding", "Verify · Teach · Question back · Confirm", hold=3.6)


# ---------------------------------------------------------------- capture + encode
async def main():
    if WORK.exists():
        shutil.rmtree(WORK)
    (WORK / "frames").mkdir(parents=True)
    api_post("/api/demo/reset")

    frames: list[tuple[float, Path]] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport=VIEW, device_scale_factor=SCALE)
        await ctx.add_init_script(OVERLAY_JS)
        page = await ctx.new_page()
        cdp = await ctx.new_cdp_session(page)

        async def on_frame(params):
            n = len(frames)
            path = WORK / "frames" / f"f{n:06d}.jpg"
            path.write_bytes(base64.b64decode(params["data"]))
            frames.append((params["metadata"]["timestamp"], path))
            try:
                await cdp.send("Page.screencastFrameAck", {"sessionId": params["sessionId"]})
            except Exception:
                pass

        cdp.on("Page.screencastFrame", lambda prm: asyncio.ensure_future(on_frame(prm)))
        await page.goto(BASE + "/")
        await cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": 1920, "maxHeight": 1080, "everyNthFrame": 1})
        try:
            await (story_short(page) if SHORT else story(page))
        finally:
            await page.wait_for_timeout(400)
            await cdp.send("Page.stopScreencast")
            await browser.close()

    # concat list with real frame durations (screencast only emits frames on change)
    frames.sort(key=lambda x: x[0])
    lines = []
    for (t, f), (t2, _) in zip(frames, frames[1:] + [(frames[-1][0] + 0.5, None)]):
        lines.append(f"file '{f}'\nduration {max(0.001, t2 - t):.4f}")
    lines.append(f"file '{frames[-1][1]}'")
    (WORK / "list.txt").write_text("\n".join(lines) + "\n")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(WORK / "list.txt"),
            "-vf", "fps=30,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=white,format=yuv420p",
            "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-movflags", "+faststart", str(OUT),
        ],
        check=True,
    )
    total = frames[-1][0] - frames[0][0]
    print(f"frames={len(frames)} duration≈{total:.1f}s → {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")
    # leave the demo in a clean state
    api_post("/api/demo/reset")
    api_post("/api/teacher/pathways/heat_001/review", {"status": "draft", "reviewer": "Teacher", "note": ""})


if __name__ == "__main__":
    asyncio.run(main())
