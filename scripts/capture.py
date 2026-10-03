#!/usr/bin/env python3
"""Capture an HTML page as a 2x PNG for a product-screen slide, and prove its smallest type clears the 8pt floor
at the width the capture will be placed.

    $PY scripts/capture.py page.html out.png [--width 1280] [--height 800] [--scale 2] [--placed-width 11.5]
                           [--full-page] [--selector CSS]

Playwright (Chromium) renders the page at the CSS viewport (--width x --height) and device scale (--scale, at least
2, so a slide placement keeps 192 pixels per inch). Before the screenshot it walks every element that draws text
(a visible, non-empty text node, not display:none, visibility:hidden or zero opacity, inside the captured area)
and records the smallest computed font size in CSS pixels and where it is. The type a reader sees on the slide is
that size times the placement scale:

    smallest pt = min_font_px x (placed_width_in x 72 / css_width)

which must be at least 8pt (the house floor). Under it the capture is refused: no PNG is written and the exit is 1.
Otherwise the PNG and its sidecar <stem>.capture.json (css_width, css_height, scale, min_font_px, min_font_where,
placed_width_in, min_pt, sha256 of the PNG) are written; deckkit.exhibits.screen_frame reads the sidecar,
re-checks the floor at the width it actually places the capture, and records the figure in the picture's alt text.

A page carrying any external request (http, https, //) is refused: a capture is of a self-contained page.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "kit"))
from deckkit.measure import FLOOR  # noqa: E402  (the kit's one floor)
EXTERNAL = re.compile(r"""(?:src|href)\s*=\s*["'](?:https?:)?//|@import\s+url\(\s*["']?(?:https?:)?//|url\(\s*["']?(?:https?:)?//""",
                      re.I)

_SMALLEST = r"""
function (clip) {
  const out = {px: null, where: null, count: 0};
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walker.nextNode())) {
    const t = (n.nodeValue || "").trim();
    if (!t) continue;
    const el = n.parentElement;
    if (!el) continue;
    const cs = getComputedStyle(el);
    if (cs.display === "none" || cs.visibility === "hidden" || parseFloat(cs.opacity) === 0) continue;
    const range = document.createRange();
    range.selectNodeContents(n);
    const rects = Array.from(range.getClientRects()).filter(function (r) { return r.width > 0 && r.height > 0; });
    if (!rects.length) continue;
    const inside = rects.some(function (r) { return r.right > clip.x && r.left < clip.x + clip.w && r.bottom > clip.y && r.top < clip.y + clip.h; });
    if (!inside) continue;
    let s = parseFloat(cs.fontSize);
    // an ancestor transform scales what is painted
    let p = el, scale = 1;
    while (p && p !== document.documentElement) {
      const tr = getComputedStyle(p).transform;
      if (tr && tr !== "none") { const m = new DOMMatrix(tr); scale *= Math.sqrt(m.a * m.a + m.b * m.b); }
      p = p.parentElement;
    }
    s *= scale;
    out.count += 1;
    if (out.px === null || s < out.px) { out.px = s; out.where = el.tagName.toLowerCase() + (el.className ? "." + String(el.className).split(" ")[0] : "") + ": " + t.slice(0, 40); }
  }
  return out;
}
"""


def capture(html, out, *, width=1280, height=800, scale=2.0, placed_width_in=11.5, full_page=False,
            selector=None) -> dict:
    """Render html (a path) to out (a PNG) and write its sidecar. Returns the sidecar record. Raises SystemExit
    with a message (and writes nothing) when the page reaches outside itself or its smallest type, placed at
    placed_width_in, falls under the floor."""
    from playwright.sync_api import sync_playwright
    html, out = Path(html).resolve(), Path(out)
    src = html.read_text(encoding="utf-8")
    if EXTERNAL.search(src):
        raise SystemExit("FAIL %s requests something outside itself (%s); inline it" % (html.name,
                                                                                       EXTERNAL.search(src).group(0)))
    if scale < 2:
        raise SystemExit("FAIL device scale %.1f: at least 2, so the slide keeps 192 pixels per inch" % scale)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": int(width), "height": int(height)},
                                    device_scale_factor=float(scale))
            page.goto(html.as_uri(), wait_until="load")
            page.evaluate("document.fonts ? document.fonts.ready.then(function () { return true; }) : true")
            if selector:
                el = page.query_selector(selector)
                if el is None:
                    raise SystemExit("FAIL selector %r matches nothing" % selector)
                bb = el.bounding_box()
                clip = {"x": bb["x"], "y": bb["y"], "w": bb["width"], "h": bb["height"]}
            elif full_page:
                dims = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.scrollHeight]")
                clip = {"x": 0, "y": 0, "w": dims[0], "h": dims[1]}
            else:
                clip = {"x": 0, "y": 0, "w": int(width), "h": int(height)}
            found = page.evaluate(_SMALLEST, clip)
            css_w = clip["w"]
            min_px = found["px"]
            min_pt = round(min_px * placed_width_in * 72.0 / css_w, 2) if min_px else 0.0
            if min_px and min_pt < FLOOR:
                raise SystemExit("FAIL smallest type %.1fpx (%s) is %.2fpt placed %.2fin wide; the floor is %.0fpt. "
                                 "Raise it to %.1fpx, narrow the CSS width, or place the capture wider"
                                 % (min_px, found["where"], min_pt, placed_width_in, FLOOR,
                                    FLOOR * css_w / (placed_width_in * 72.0)))
            out.parent.mkdir(parents=True, exist_ok=True)
            tmp = out.with_suffix(".tmp.png")
            if selector:
                page.query_selector(selector).screenshot(path=str(tmp))
            else:
                page.screenshot(path=str(tmp), full_page=bool(full_page))
        finally:
            browser.close()
    tmp.replace(out)
    rec = {"source": html.name, "css_width": css_w, "css_height": clip["h"], "scale": float(scale),
           "min_font_px": min_px, "min_font_where": found["where"], "text_nodes": found["count"],
           "placed_width_in": float(placed_width_in), "min_pt": min_pt,
           "sha256": hashlib.sha256(out.read_bytes()).hexdigest()}
    out.with_name(out.stem + ".capture.json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    return rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("html")
    ap.add_argument("out")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=800)
    ap.add_argument("--scale", type=float, default=2.0)
    ap.add_argument("--placed-width", type=float, default=11.5, help="inches the capture will span on the slide")
    ap.add_argument("--full-page", action="store_true")
    ap.add_argument("--selector")
    a = ap.parse_args(argv)
    try:
        rec = capture(a.html, a.out, width=a.width, height=a.height, scale=a.scale, placed_width_in=a.placed_width,
                      full_page=a.full_page, selector=a.selector)
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 1
    print("OK %s %dx%d css at %gx; smallest type %.1fpx (%s) = %.2fpt at %.2fin"
          % (a.out, rec["css_width"], rec["css_height"], rec["scale"], rec["min_font_px"] or 0, rec["min_font_where"],
             rec["min_pt"], rec["placed_width_in"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
