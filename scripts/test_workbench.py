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
  // Objects on the desk. The Freshfleet folder is hidden while closed (its photo stands in for it).
  const shown = () => [...d.querySelectorAll('.obj')].filter(e => e.offsetWidth > 0);
  const boxesOf = () => shown().map(e => ({id: e.id, left: e.offsetLeft, top: e.offsetTop, width: e.offsetWidth, height: e.offsetHeight, tilt: e.style.getPropertyValue('--tilt'), closed: e.classList.contains('closed')}));
  const bioLines = () => { const b = d.querySelector('#badge .bio'); return Math.round(b.offsetHeight / parseFloat(w.getComputedStyle(b).lineHeight)); };
  out.initial = {boxes: boxesOf(), bioLines: bioLines()};

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

  // 4b. The Freshfleet photo opens the Freshfleet folder (it is no longer inside Projects).
  await step('freshfleet', async () => {
  const photo = d.getElementById('p-freshfleet');
  photo.scrollIntoView({block: 'center'}); await sleep(50);
  const [fx, fy] = center(photo.getBoundingClientRect());
  pointer(photo, 'pointerdown', fx, fy); pointer(photo, 'pointerup', fx, fy);
  await sleep(450);
  const fw = d.getElementById('freshfleet');
  out.freshfleet = {closed: fw.classList.contains('closed'), width: fw.offsetWidth, text: fw.innerText.includes('UR10e robot arm')};
  fw.querySelector('[data-toggle]').click(); await sleep(300);
  });

  // 5. Tidy desk: everything closed, untilted, equal width, in aligned rows and columns, no overlaps.
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
    pressed: d.getElementById('tidy').getAttribute('aria-pressed'),
    bioLines: bioLines()
  };
  });

  // 6. While tidy is on, opening a window and putting it away sends it back to its grid slot.
  await step('putAway', async () => {
  const slot = d.getElementById('projects'), before = {left: slot.offsetLeft, top: slot.offsetTop, width: slot.offsetWidth};
  d.querySelector('.menubar nav a[data-open="projects"]').click(); await sleep(450);
  const openedAt = {left: slot.offsetLeft, top: slot.offsetTop, closed: slot.classList.contains('closed')};
  slot.querySelector('[data-toggle]').click(); await sleep(450);
  out.putAway = {before: before, openedAt: openedAt, after: {left: slot.offsetLeft, top: slot.offsetTop, width: slot.offsetWidth},
    closed: slot.classList.contains('closed'), tilt: slot.style.getPropertyValue('--tilt'),
    pressed: d.getElementById('tidy').getAttribute('aria-pressed')};
  });

  // 7. Pressing Tidy desk again switches it off and restores the page-load arrangement.
  await step('untidy', async () => {
  d.getElementById('tidy').click(); await sleep(450);
  out.untidy = {pressed: d.getElementById('tidy').getAttribute('aria-pressed'), boxes: boxesOf()};
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
    for name in ("underline", "openFromMenu", "resize", "openFromDesk", "freshfleet", "tidy", "putAway", "untidy"):
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

    ff = r.get("freshfleet")
    if ff and (ff["closed"] or ff["width"] == 0 or not ff["text"]):
        fail(f"clicking the Freshfleet photo did not open the Freshfleet folder: {ff}")

    pa = r.get("putAway")
    if pa:
        if pa["openedAt"]["closed"]:
            fail("with tidy on, Projects did not open")
        elif (pa["openedAt"]["left"], pa["openedAt"]["top"]) == (pa["before"]["left"], pa["before"]["top"]):
            fail("with tidy on, Projects opened in its slot, so the put-away check proves nothing")
        if not pa["closed"]:
            fail("put away did not close Projects")
        if pa["after"] != pa["before"]:
            fail(f"with tidy on, put away left Projects at {pa['after']}, expected its slot {pa['before']}")
        if pa["tilt"] != "0deg":
            fail(f"with tidy on, put away left Projects tilted {pa['tilt']}")
        if pa["pressed"] != "true":
            fail("opening and putting away a window switched tidy off")

    u = r.get("untidy")
    if u:
        if u["pressed"] != "false":
            fail("second press of Tidy desk did not switch it off")
        start = {b["id"]: b for b in r["initial"]["boxes"]}
        for b in u["boxes"]:
            s0 = start[b["id"]]
            # 1px tolerance for sub-pixel rounding of scaled positions.
            moved = any(abs(b[k] - s0[k]) > 1 for k in ("left", "top", "width", "height"))
            if moved or b["tilt"] != s0["tilt"] or b["closed"] != s0["closed"]:
                fail(f"untidy left {b['id']} at {b}, expected the starting {s0}")

    if "tidy" not in r:
        return
    if r["tidy"]["pressed"] != "true":
        fail("Tidy desk button does not show as pressed after turning tidy on")
    # The page starts with Home and Research open; tidy must put them away too.
    if not r["beforeTidyOpen"]:
        fail("no windows were open before Tidy desk, so the tidy check proves nothing")
    t = r["tidy"]
    if t["open"]:
        fail(f"Tidy desk left these windows open: {t['open']}")
    if t["tilted"]:
        fail(f"Tidy desk left these objects tilted: {t['tilted']}")
    boxes = t["boxes"]
    widths = {b["width"] for b in boxes}
    if len(widths) != 1:
        fail(f"Tidy desk objects have different widths: {sorted(widths)}")
    lefts = sorted({b["left"] for b in boxes})
    tops = sorted({b["top"] for b in boxes})
    cols = max(sum(1 for b in boxes if b["top"] == top) for top in tops)
    if len(lefts) != cols:
        fail(f"Tidy desk columns do not line up: {len(lefts)} distinct left edges for {cols} columns")
    for i, a in enumerate(boxes):
        if a["left"] < 0 or a["left"] + a["width"] > t["deskW"]:
            fail(f"after Tidy desk, {a['id']} sticks out of the desk")
        for b in boxes[i + 1:]:
            if overlaps(a, b):
                fail(f"after Tidy desk, {a['id']} overlaps {b['id']}")


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
    print("OK: menu underline, centered open (menu and desk), corner resize, tidy grid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
