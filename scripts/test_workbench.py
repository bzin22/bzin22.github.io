#!/usr/bin/env python3
"""Drives the workbench home page in headless Chrome and checks the desk interactions.

Run after `bundle exec jekyll build`:

    python3 scripts/test_workbench.py                 # tests _site/index.html
    python3 scripts/test_workbench.py path/to/page.html

Serves the page's folder on a local port, loads it in a 1440x700 iframe inside a small
harness page, clicks and drags with synthetic pointer events, and reads back positions.
The harness POSTs its results back to the server; Chrome is then killed, because
--dump-dom with a virtual time budget hangs on this machine often enough to be useless.
Exits non-zero and prints one line per failure. Stdlib plus a local Chrome, no framework.
"""

import functools
import queue
import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HARNESS = "/__workbench_test__.html"
RESULT = "/__workbench_result__"

# The iframe is 700px tall so the desk (min-height 900px) scrolls, which is the case
# where "open in the center of the page" and "open where the object sits" differ.
FRAME_W, FRAME_H = 1440, 700
SCROLL_Y = 150

HARNESS_HTML = """<!doctype html><html><body style="margin:0">
<iframe id="f" src="PAGE" style="width:%dpx;height:%dpx;border:0"></iframe>
<script>
const out = {};
const sleep = ms => new Promise(r => setTimeout(r, ms));
function pointer(el, type, x, y) {
  el.dispatchEvent(new f.contentWindow.PointerEvent(type, {bubbles: true, cancelable: true, pointerId: 7, button: 0, clientX: x, clientY: y, isPrimary: true}));
}
function center(r) { return [r.left + r.width / 2, r.top + r.height / 2]; }
const report = body => fetch('RESULT_PATH', {method: 'POST', body: body});
async function step(name, fn) { try { await fn(); } catch (e) { out[name] = {error: String(e)}; } }
async function run() {
  const w = f.contentWindow, d = w.document;
  if (d.fonts) await Promise.race([d.fonts.ready, sleep(3000)]);
  await sleep(400);
  const menuH = d.querySelector('.menubar').offsetHeight;
  // Objects on the desk.
  const shown = () => [...d.querySelectorAll('.obj')].filter(e => e.offsetWidth > 0);
  const boxesOf = () => shown().map(e => ({id: e.id, left: e.offsetLeft, top: e.offsetTop, width: e.offsetWidth, height: e.offsetHeight, tilt: e.style.getPropertyValue('--tilt'), closed: e.classList.contains('closed')}));
  const bioLines = () => { const b = d.querySelector('#badge .bio'); return Math.round(b.offsetHeight / parseFloat(w.getComputedStyle(b).lineHeight)); };
  out.initial = {boxes: boxesOf(), bioLines: bioLines(),
    button: d.getElementById('tidy').textContent.trim(),
    pressed: d.getElementById('tidy').hasAttribute('aria-pressed'),
    open: [...d.querySelectorAll('.win:not(.closed)')].map(e => e.id),
    aboutLabels: [...d.querySelectorAll('.menubar nav a[data-open="home"], #home .bar .title, #home .cover-title')].map(e => e.textContent.trim()),
    aboutHeading: !!d.querySelector('#home .content h1'),
    aboutArt: !!d.querySelector('#home .cover img, #home .cover svg, #home .cover i'),
    cvArt: ['reframe', 'apple', 'freshfleet'].every(name => !!d.querySelector('#cv [data-ph="' + name + '"]')),
    cvText: d.getElementById('cv').textContent.includes('UR10e robot arm'),
    removed: ['print', 'p-freshfleet', 'p-reframe', 'p-apple', 'freshfleet'].every(id => !d.getElementById(id))};
  // Move a desk item so Tidy desk has a real change to undo.
  const sticky = d.getElementById('sticky');
  const oldSticky = {left: sticky.offsetLeft, top: sticky.offsetTop};
  const [sx, sy] = center(sticky.getBoundingClientRect());
  pointer(sticky, 'pointerdown', sx, sy);
  pointer(sticky, 'pointermove', sx + 65, sy + 20);
  pointer(sticky, 'pointerup', sx + 65, sy + 20);
  out.moved = {before: oldSticky, after: {left: sticky.offsetLeft, top: sticky.offsetTop}};

  // 1. Menu underline stays within the word.
  await step('underline', async () => { out.underline = [...d.querySelectorAll('.menubar nav a')].map(a => {
    const svg = a.querySelector('.scribble').getBoundingClientRect();
    const range = d.createRange(); range.selectNodeContents(a.querySelector('.word').firstChild);
    const text = range.getBoundingClientRect();
    return {word: a.textContent.trim(), overLeft: text.left - svg.left, overRight: svg.right - text.right};
  }); });

  // 2. Opening from the menu while scrolled puts the window in the middle of what you can see.
  await step('openFromMenu', async () => {
  w.scrollTo(0, SCROLL_Y); await sleep(50);
  d.querySelector('.menubar nav a[data-open="projects"]').click();
  await sleep(450);
  const pr = d.getElementById('projects').getBoundingClientRect();
  out.openFromMenu = {closed: d.getElementById('projects').classList.contains('closed'),
    cx: center(pr)[0], cy: center(pr)[1], wantCx: w.innerWidth / 2, wantCy: (menuH + w.innerHeight) / 2,
    top: pr.top, bottom: pr.bottom, menuH: menuH, viewH: w.innerHeight};
  });

  // 3. Resize by dragging the corner handle: grows by the drag, and stops at the minimum size.
  await step('resize', async () => {
  const proj = d.getElementById('projects');
  const w0 = proj.offsetWidth, h0 = proj.offsetHeight;
  const handle = proj.querySelector('.resize-handle');
  let [hx, hy] = center(handle.getBoundingClientRect());
  pointer(handle, 'pointerdown', hx, hy); pointer(handle, 'pointermove', hx + 80, hy - 60); pointer(handle, 'pointerup', hx + 80, hy - 60);
  const grown = {dw: proj.offsetWidth - w0, dh: proj.offsetHeight - h0};
  [hx, hy] = center(handle.getBoundingClientRect());
  pointer(handle, 'pointerdown', hx, hy); pointer(handle, 'pointermove', hx - 3000, hy - 3000); pointer(handle, 'pointerup', hx - 3000, hy - 3000);
  out.resize = {grown: grown, minW: proj.offsetWidth, minH: proj.offsetHeight};
  });

  // 4. Clicking a closed object on the desk (the CV clipboard) also opens it centered.
  await step('openFromDesk', async () => {
  const cvCover = d.querySelector('#cv .cover');
  cvCover.scrollIntoView({block: 'end'}); await sleep(50);
  const [cx, cy] = center(cvCover.getBoundingClientRect());
  pointer(cvCover, 'pointerdown', cx, cy); pointer(cvCover, 'pointerup', cx, cy);
  await sleep(450);
  const cr = d.getElementById('cv').getBoundingClientRect();
  out.openFromDesk = {closed: d.getElementById('cv').classList.contains('closed'),
    cx: center(cr)[0], cy: center(cr)[1], wantCx: w.innerWidth / 2, wantCy: (menuH + w.innerHeight) / 2};
  });

  // 5. Tidy desk closes open windows and restores the moved item to the aligned grid.
  await step('tidy', async () => {
  w.scrollTo(0, 0);
  out.beforeTidyOpen = [...d.querySelectorAll('.win:not(.closed)')].map(e => e.id);
  d.getElementById('tidy').click();
  await sleep(450);
  const objs = shown();
  out.tidy = {
    open: [...d.querySelectorAll('.win:not(.closed)')].map(e => e.id),
    tilted: objs.filter(e => { const t = w.getComputedStyle(e).transform; return t !== 'none' && t !== 'matrix(1, 0, 0, 1, 0, 0)'; }).map(e => e.id + ' ' + w.getComputedStyle(e).transform),
    boxes: objs.map(e => ({id: e.id, left: e.offsetLeft, top: e.offsetTop, width: e.offsetWidth, height: e.offsetHeight})),
    deskW: d.getElementById('desk').clientWidth,
    button: d.getElementById('tidy').textContent.trim(),
    pressed: d.getElementById('tidy').hasAttribute('aria-pressed'),
    bioLines: bioLines()
  };
  });

  // 6. Opening a window and putting it away sends it back to its grid slot.
  await step('putAway', async () => {
  const slot = d.getElementById('projects'), before = {left: slot.offsetLeft, top: slot.offsetTop, width: slot.offsetWidth};
  d.querySelector('.menubar nav a[data-open="projects"]').click(); await sleep(450);
  const openedAt = {left: slot.offsetLeft, top: slot.offsetTop, closed: slot.classList.contains('closed')};
  slot.querySelector('[data-toggle]').click(); await sleep(450);
  out.putAway = {before: before, openedAt: openedAt, after: {left: slot.offsetLeft, top: slot.offsetTop, width: slot.offsetWidth},
    closed: slot.classList.contains('closed'), tilt: slot.style.getPropertyValue('--tilt'),
    button: d.getElementById('tidy').textContent.trim()};
  });

  // 7. Pressing Tidy desk again must leave the desk aligned.
  await step('secondTidy', async () => {
  d.getElementById('tidy').click(); await sleep(450);
  out.secondTidy = {button: d.getElementById('tidy').textContent.trim(),
    open: [...d.querySelectorAll('.win:not(.closed)')].map(e => e.id), boxes: boxesOf()};
  });
  await report(JSON.stringify(out));
}
f.addEventListener('load', () => run().catch(e => report(JSON.stringify({error: String(e.stack)}))));
</script></body></html>""".replace("SCROLL_Y", str(SCROLL_Y)).replace("RESULT_PATH", RESULT) % (FRAME_W, FRAME_H)


class Handler(http.server.SimpleHTTPRequestHandler):
    page = "/"
    results = queue.Queue()

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
        self.send_response(204)
        self.end_headers()
        Handler.results.put(body)

    def do_GET(self):
        if self.path == HARNESS:
            body = HARNESS_HTML.replace("PAGE", self.page).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def log_message(self, *args):
        pass


def measure(page_file):
    folder, name = os.path.split(os.path.abspath(page_file))
    Handler.page = "/" + name
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=folder))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}{HARNESS}"
    with tempfile.TemporaryDirectory() as profile:
        chrome = subprocess.Popen(
            [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={profile}",
             "--remote-debugging-port=0", f"--window-size={FRAME_W + 40},{FRAME_H + 200}", url],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            text = Handler.results.get(timeout=60)
        except queue.Empty:
            text = None
        finally:
            chrome.kill()
            chrome.wait()
            server.shutdown()
    if text is None:
        raise RuntimeError("harness sent no result within 60s")
    return json.loads(text)


def overlaps(a, b):
    return a["left"] < b["left"] + b["width"] and b["left"] < a["left"] + a["width"] and \
        a["top"] < b["top"] + b["height"] and b["top"] < a["top"] + a["height"]


def check(r, fail):
    if "error" in r:
        fail(f"harness crashed: {r['error']}")
        return
    for name in ("underline", "openFromMenu", "resize", "openFromDesk", "tidy", "putAway", "secondTidy"):
        if isinstance(r.get(name), dict) and "error" in r[name]:
            fail(f"{name} step threw: {r[name]['error']}")
            r.pop(name)
    # Underline: the path spans x=2..98 of the word box, so it should sit inside the text.
    # The old version used left/right 6px inside a 9px-padded link, overshooting 3px per side.
    for u in r.get("underline", []):
        if u["overLeft"] > 0.5 or u["overRight"] > 0.5:
            fail(f"menu underline for {u['word']!r} runs past the word ({u['overLeft']:.1f}px left, {u['overRight']:.1f}px right)")

    for key, label in (("openFromMenu", "Projects from the menu"), ("openFromDesk", "the CV clipboard from the desk")):
        if key not in r:
            continue
        o = r[key]
        if o["closed"]:
            fail(f"opening {label} left it closed")
            continue
        # 2px tolerance covers sub-pixel rounding of the centered left/top.
        if abs(o["cx"] - o["wantCx"]) > 2 or abs(o["cy"] - o["wantCy"]) > 2:
            fail(f"opening {label} put its center at ({o['cx']:.0f}, {o['cy']:.0f}), "
                 f"expected the visible center ({o['wantCx']:.0f}, {o['wantCy']:.0f})")
    o = r.get("openFromMenu")
    if o and not o["closed"] and (o["top"] < o["menuH"] - 1 or o["bottom"] > o["viewH"] + 1):
        fail(f"Projects window is not fully on screen (top {o['top']:.0f}, bottom {o['bottom']:.0f})")

    rs = r.get("resize")
    if rs and (abs(rs["grown"]["dw"] - 80) > 1 or abs(rs["grown"]["dh"] + 60) > 1):
        fail(f"dragging the resize corner by (+80, -60) changed the size by ({rs['grown']['dw']}, {rs['grown']['dh']})")
    if rs and (rs["minW"], rs["minH"]) != (280, 220):
        fail(f"shrinking a window past its minimum left it {rs['minW']}x{rs['minH']}, expected 280x220")

    # The bio is 13 words. Beside a 92px photo it wrapped to 6 lines in the tidy grid
    # (about 2 words a line). Full width under the photo it needs 3 at the 220px text width.
    if r["initial"]["bioLines"] > 3:
        fail(f"badge bio wraps to {r['initial']['bioLines']} lines on the starting desk, expected 3 or fewer")
    if "tidy" in r and r["tidy"]["bioLines"] > 3:
        fail(f"badge bio wraps to {r['tidy']['bioLines']} lines on the tidy desk, expected 3 or fewer")

    pa = r.get("putAway")
    if pa:
        if pa["openedAt"]["closed"]:
            fail("Projects did not open after tidying")
        elif (pa["openedAt"]["left"], pa["openedAt"]["top"]) == (pa["before"]["left"], pa["before"]["top"]):
            fail("Projects opened in its slot, so the put-away check proves nothing")
        if not pa["closed"]:
            fail("put away did not close Projects")
        if pa["after"] != pa["before"]:
            fail(f"with tidy on, put away left Projects at {pa['after']}, expected its slot {pa['before']}")
        if pa["tilt"] != "0deg":
            fail(f"put away left Projects tilted {pa['tilt']}")
        if pa["button"] != "Tidy desk":
            fail("putting away a window changed the Tidy desk button")

    if "tidy" not in r:
        return
    if r["initial"]["button"] != "Tidy desk" or r["initial"]["pressed"] or r["initial"]["open"]:
        fail("the page did not load aligned with Tidy desk as an action button")
    if r["initial"]["aboutLabels"] != ["About", "About me", "About me"] or r["initial"]["aboutHeading"]:
        fail("the workbench About labels or duplicate heading are wrong")
    if r["initial"]["aboutArt"]:
        fail("the About card still contains illustrations")
    if r["moved"]["before"] == r["moved"]["after"]:
        fail("the desk item did not move before Tidy desk was clicked")
    if r["tidy"]["button"] != "Tidy desk" or r["tidy"]["pressed"]:
        fail("Tidy desk changed into a toggle after clicking")
    # The menu/desk interactions open windows; tidy must put them away too.
    if not r["beforeTidyOpen"]:
        fail("no windows were open before Tidy desk, so the tidy check proves nothing")
    t = r["tidy"]
    if not r["initial"]["cvArt"] or not r["initial"]["cvText"] or not r["initial"]["removed"]:
        fail("the CV illustrations or desk object cleanup is missing")
    if t["open"]:
        fail(f"Tidy desk left these windows open: {t['open']}")
    if t["tilted"]:
        fail(f"Tidy desk left these objects tilted: {t['tilted']}")
    boxes = t["boxes"]
    widths = {b["width"] for b in boxes if b["id"] != "pencil"}
    if len(widths) != 1:
        fail(f"Tidy desk objects have different widths: {sorted(widths)}")
    grid_boxes = [b for b in boxes if b["id"] != "pencil"]
    lefts = sorted({b["left"] for b in grid_boxes})
    tops = sorted({b["top"] for b in grid_boxes})
    cols = max(sum(1 for b in grid_boxes if b["top"] == top) for top in tops)
    if len(lefts) != cols:
        fail(f"Tidy desk columns do not line up: {len(lefts)} distinct left edges for {cols} columns")
    for stage in (r["initial"]["boxes"], boxes):
        placed = {b["id"]: b for b in stage}
        note, pencil = placed["sticky"], placed["pencil"]
        if abs((note["left"] + note["width"] / 2) - (pencil["left"] + pencil["width"] / 2)) > 1:
            fail("the pencil is not centered below the sticky note")
        if pencil["top"] < note["top"] + note["height"] + 12:
            fail("the pencil is not below the sticky note")
    for i, a in enumerate(boxes):
        if a["left"] < 0 or a["left"] + a["width"] > t["deskW"]:
            fail(f"after Tidy desk, {a['id']} sticks out of the desk")
        for b in boxes[i + 1:]:
            if overlaps(a, b):
                fail(f"after Tidy desk, {a['id']} overlaps {b['id']}")
    start = {b["id"]: b for b in r["initial"]["boxes"]}
    for b in boxes:
        s0 = start[b["id"]]
        if any(abs(b[k] - s0[k]) > 1 for k in ("left", "top", "width", "height")):
            fail(f"Tidy desk left {b['id']} away from its original slot")
    again = r.get("secondTidy")
    if again and (again["button"] != "Tidy desk" or again["open"] or again["boxes"] != r["initial"]["boxes"]):
        fail("clicking Tidy desk again scattered the desk")


def main():
    page = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "_site", "index.html")
    if not os.path.isfile(page):
        print(f"FAIL: {page} does not exist; run `bundle exec jekyll build` first")
        return 1
    failures = []
    check(measure(page), failures.append)
    for message in failures:
        print(f"FAIL: {message}")
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("OK: menu underline, centered open, corner resize, one-way tidy button")
    return 0


if __name__ == "__main__":
    sys.exit(main())
