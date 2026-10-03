"""P24 fill: a content slide fills its canvas (density beats air).

On every content slide (a tagged slide whose family is not Frame; an untagged slide over 20 content words), the
content box is the union of every drawn content leaf (fill, outline, text, picture or icon), leaving out the
title, page numbers, footers, full-bleed backgrounds and anything off the canvas, clipped to the canvas content
band (deckkit.canvas: WIDE 0.50, 0.85, 12.40 x 5.99 in). Two measures, both required:
  * extent: the content box's height is at least 70% of the band's height;
  * cover: the content box's area is at least 55% of the band's area.
A slide whose content sits in the top half of the band with air below it fails both.
"""
from __future__ import annotations

import sys

from _shared import FAIL, Finding, bx, cli, full_bleed, is_drawn

GATE, TITLE = "P24", "fill"
EXTENT, COVER = 0.70, 0.55
UNTAGGED_WORDS = 20
CHROME_ROLES = ("title", "page-number", "footer", "background")


def content_box(s, ctx):
    """(l, t, r, b) of the slide's drawn content clipped to the canvas content band, or None when there is none."""
    band = ctx.canvas.content
    l = t = float("inf")
    r = b = float("-inf")
    for L in s["shapes"]:
        role = (L.get("role_guess") or {}).get("role")
        if L["name"] == "title" or role in CHROME_ROLES or not is_drawn(L) or full_bleed(L, ctx) \
                or L.get("on_canvas") == "off":
            continue
        x0, y0, x1, y1 = bx(L)
        x0, y0 = max(x0, band.x), max(y0, band.y)
        x1, y1 = min(x1, band.r), min(y1, band.y + band.h)
        if x1 <= x0 or y1 <= y0:
            continue
        l, t, r, b = min(l, x0), min(t, y0), max(r, x1), max(b, y1)
    return None if l == float("inf") else (l, t, r, b)


def run(deck, ctx):
    out = []
    band = ctx.canvas.content
    for i in range(1, ctx.n + 1):
        s = ctx.slide(i)
        if ctx.tags()[i - 1]["archetype"]:
            if ctx.is_frame(i):
                continue
        elif s["text"]["words_content"] <= UNTAGGED_WORDS:
            continue
        box = content_box(s, ctx)
        if box is None:
            out.append(Finding(GATE, FAIL, i, "", "a content slide with nothing drawn in the content band"))
            continue
        l, t, r, b = box
        extent = (b - t) / band.h
        cover = (r - l) * (b - t) / (band.w * band.h)
        if extent < EXTENT:
            out.append(Finding(GATE, FAIL, i, "", "content spans %.0f%% of the band's height (%.2f to %.2fin), min "
                               "%.0f%%" % (100 * extent, t, b, 100 * EXTENT)))
        if cover < COVER:
            out.append(Finding(GATE, FAIL, i, "", "content box covers %.0f%% of the band (%.2f x %.2fin), min %.0f%%"
                               % (100 * cover, r - l, b - t, 100 * COVER)))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
