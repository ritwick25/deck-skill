"""P24 fill: a content slide fills its canvas (density beats air), measured as content mass, never as a union box.

On every content slide (a tagged slide whose family is not Frame; an untagged slide over 20 content words), the
canvas content band (deckkit.canvas: WIDE 0.50, 0.85, 12.40 x 5.99 in) is rasterised into a GRID_X x GRID_Y grid
(48 x 27 cells). A cell is marked when one content box covers at least MARK of its area. Content boxes are:
  * drawn shapes: a fill or an outline (a card, a panel, a chevron, a disc, a glyph);
  * text, by its ink box (the read layer's estimate of where the glyphs sit, not the frame);
  * pictures and table cells.
Lines and connectors are left out (an arrow or a rule is not mass), and so is chrome: the title, page numbers,
footers, full-bleed backgrounds, anything off the canvas.

Two measures, both required:
  * extent: the row below which TAIL (3%) or less of the marked cells lie, as a share of the band's rows, at least
    EXTENT (85%). A three-word source line at the foot of a slide whose content stops halfway is 3% of the mass at
    most, so it never stretches the extent the way a union box would;
  * share: marked cells over all cells, at least SHARE (35%).
"""
from __future__ import annotations

import sys

from _shared import FAIL, Finding, bx, cli, full_bleed, has_text, is_filled, is_lined
from deckkit.read.walk import _text_box

GATE, TITLE = "P24", "fill"
GRID_X, GRID_Y = 48, 27
MARK = 0.25               # a box covering this share of a cell marks it
TAIL = 0.03               # the share of marked cells allowed below the extent row
EXTENT, SHARE = 0.85, 0.35
UNTAGGED_WORDS = 20
CHROME_ROLES = ("title", "page-number", "footer", "background")


def content_boxes(s, ctx) -> list[tuple[float, float, float, float]]:
    """The boxes that carry content mass on a slide (see the module notes)."""
    out = []
    for L in s["shapes"]:
        role = (L.get("role_guess") or {}).get("role")
        if L["name"] == "title" or role in CHROME_ROLES or full_bleed(L, ctx) or L.get("on_canvas") == "off":
            continue
        if L["kind"] == "cxn" or L.get("line_like") or L.get("connector") is not None:
            continue
        drawn = L["kind"] in ("pic", "cell", "graphic") or (L["kind"] == "sp" and (is_filled(L) or is_lined(L)))
        if drawn:
            out.append(bx(L))
        elif has_text(L):
            out.append(_text_box(L))
    return out


def grid(s, ctx) -> list[list[bool]]:
    """GRID_Y rows of GRID_X cells over the content band, True where content mass sits."""
    band = ctx.canvas.content
    cw, ch = band.w / GRID_X, band.h / GRID_Y
    cells = [[False] * GRID_X for _ in range(GRID_Y)]
    need = MARK * cw * ch
    for x0, y0, x1, y1 in content_boxes(s, ctx):
        c0 = max(0, int((x0 - band.x) // cw))
        c1 = min(GRID_X - 1, int((x1 - band.x) // cw))
        r0 = max(0, int((y0 - band.y) // ch))
        r1 = min(GRID_Y - 1, int((y1 - band.y) // ch))
        for r in range(r0, r1 + 1):
            top = band.y + r * ch
            oh = min(y1, top + ch) - max(y0, top)
            if oh <= 0:
                continue
            for c in range(c0, c1 + 1):
                if cells[r][c]:
                    continue
                left = band.x + c * cw
                ow = min(x1, left + cw) - max(x0, left)
                if ow > 0 and ow * oh >= need:
                    cells[r][c] = True
    return cells


def measures(cells) -> tuple[float, float, int]:
    """(extent, share, marked) for a grid: extent is the share of rows down to the row below which TAIL or less of
    the marked cells lie; share is marked cells over all cells."""
    per_row = [sum(row) for row in cells]
    marked = sum(per_row)
    if not marked:
        return 0.0, 0.0, 0
    allow = TAIL * marked
    below = 0
    last = len(per_row) - 1
    for r in range(len(per_row) - 1, -1, -1):
        if below + per_row[r] > allow:
            last = r
            break
        below += per_row[r]
    return (last + 1) / len(per_row), marked / (len(per_row) * len(cells[0])), marked


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
        extent, share, marked = measures(grid(s, ctx))
        if not marked:
            out.append(Finding(GATE, FAIL, i, "", "a content slide with nothing drawn in the content band"))
            continue
        if extent < EXTENT:
            out.append(Finding(GATE, FAIL, i, "", "content spans %.0f%% of the band's height (its mass ends at %.2fin, "
                               "%.0f%% or less of it below), min %.0f%%"
                               % (100 * extent, band.y + extent * band.h, 100 * TAIL, 100 * EXTENT)))
        if share < SHARE:
            out.append(Finding(GATE, FAIL, i, "", "content covers %.0f%% of the band (%d of %d cells), min %.0f%%"
                               % (100 * share, marked, GRID_X * GRID_Y, 100 * SHARE)))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
