"""P24 fill: a content slide fills its canvas (density beats air), measured as content mass, never as a union box.

On every content slide (a tagged slide whose family is not Frame; an untagged slide over 20 content words), the
canvas content band (deckkit.canvas: WIDE 0.50, 0.85, 12.40 x 5.99 in) is rasterised into a GRID_X x GRID_Y grid
(48 x 27 cells). A cell is marked when one content box covers at least MARK of its area. Content boxes are:
  * drawn shapes: a fill or an outline (a card, a panel, a chevron, a disc, a glyph);
  * text, by its ink box (the read layer's estimate of where the glyphs sit, not the frame);
  * pictures and table cells.
Lines and connectors are left out (an arrow or a rule is not mass), and so is chrome: the title, page numbers,
footers, full-bleed backgrounds, anything off the canvas.

The MAIN MASS: the marked cells are dilated by one cell (each marked cell also claims its eight neighbours, so a
gutter one cell wide between cards never splits the mass), except that a band row with no marked cell stays empty
(the dilation never crosses an empty band row). The dilated grid is split into connected components, taken largest
first (by marked cells) until they hold MASS (85%) of the marked cells. A lone foot sentence is then left out: a
component of text only (no cell marked by a drawn box: a band, a logo row or a card row at the foot is mass), no
more than FOOT_ROWS (3) rows tall, that lies wholly below the largest component with at least one empty band row
between them. Both measures read only the main mass, so a sentence across the foot of a slide whose
content stops halfway never stretches the extent, however wide it runs.

Two measures, both required, on the main mass:
  * extent: the row below which TAIL (3%) or less of the main mass lies, as a share of the band's rows, at least
    EXTENT (85%);
  * share: the main mass's cells over all cells, at least SHARE (35%).

Which slides: a tagged slide whose family is not Frame; an untagged slide over 20 content words, except slide 1. A
cover counts as a content slide only when it is tagged as one: an untagged slide 1 is a frame.
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
MASS = 0.85               # the main mass: the largest components holding this share of the marked cells
FOOT_ROWS = 3             # a component this many rows tall or fewer, alone below the mass, is a foot sentence
UNTAGGED_WORDS = 20
CHROME_ROLES = ("title", "page-number", "footer", "background")


def content_boxes(s, ctx, drawn_only: bool = False) -> list[tuple[float, float, float, float]]:
    """The boxes that carry content mass on a slide (see the module notes); drawn_only=True leaves out the text that
    draws no box of its own (what a foot sentence is made of)."""
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
        elif has_text(L) and not drawn_only:
            out.append(_text_box(L))
    return out


def grid(s, ctx, drawn_only: bool = False) -> list[list[bool]]:
    """GRID_Y rows of GRID_X cells over the content band, True where content mass sits (drawn_only: see
    content_boxes)."""
    band = ctx.canvas.content
    cw, ch = band.w / GRID_X, band.h / GRID_Y
    cells = [[False] * GRID_X for _ in range(GRID_Y)]
    need = MARK * cw * ch
    for x0, y0, x1, y1 in content_boxes(s, ctx, drawn_only):
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


def main_mass(cells, drawn=None) -> list[list[bool]]:
    """The marked cells of the largest components (one-cell dilation, eight-connected) that together hold MASS of
    the marked cells, less any lone foot sentence. Components are ranked by their marked cells, largest first; ties
    by the topmost row. drawn: the grid marked by drawn boxes only; a component with a drawn cell is never a
    sentence (None: every cell is text)."""
    rows, cols = len(cells), len(cells[0]) if cells else 0
    marked = sum(sum(r) for r in cells)
    if not marked:
        return [row[:] for row in cells]
    empty_row = [not any(row) for row in cells]
    dil = [[False] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if cells[r][c]:
                for rr in range(max(0, r - 1), min(rows, r + 2)):
                    if empty_row[rr]:
                        continue                   # an empty band row separates; the dilation never fills it
                    for cc in range(max(0, c - 1), min(cols, c + 2)):
                        dil[rr][cc] = True
    label = [[-1] * cols for _ in range(rows)]
    comps = []
    for r in range(rows):
        for c in range(cols):
            if not dil[r][c] or label[r][c] >= 0:
                continue
            k = len(comps)
            stack, own = [(r, c)], []
            label[r][c] = k
            while stack:
                y, x = stack.pop()
                if cells[y][x]:
                    own.append((y, x))
                for yy in range(max(0, y - 1), min(rows, y + 2)):
                    for xx in range(max(0, x - 1), min(cols, x + 2)):
                        if dil[yy][xx] and label[yy][xx] < 0:
                            label[yy][xx] = k
                            stack.append((yy, xx))
            comps.append(own)
    comps = [cm for cm in comps if cm]
    comps.sort(key=lambda cm: (-len(cm), min(y for y, _x in cm)))
    keep, held = [], 0
    for cm in comps:
        keep.append(cm)
        held += len(cm)
        if held >= MASS * marked:
            break
    big_bottom = max(y for y, _x in comps[0])
    keep = [comps[0]] + [cm for cm in keep[1:] if not _foot_sentence(cm, big_bottom, empty_row, drawn)]
    out = [[False] * cols for _ in range(rows)]
    for cm in keep:
        for y, x in cm:
            out[y][x] = True
    return out


def _foot_sentence(cm, big_bottom: int, empty_row, drawn=None) -> bool:
    """A component of text only (no cell marked by a drawn box), at most FOOT_ROWS rows tall, wholly below the
    largest component's last row with an empty band row between them. A band, a logo row or a card row at the foot
    draws boxes, so it is mass."""
    if drawn is not None and any(drawn[y][x] for y, x in cm):
        return False
    top, bottom = min(y for y, _x in cm), max(y for y, _x in cm)
    return bottom - top + 1 <= FOOT_ROWS and top > big_bottom + 1 and \
        any(empty_row[r] for r in range(big_bottom + 1, top))


def measures(cells, drawn=None) -> tuple[float, float, int]:
    """(extent, share, marked) for a grid, on its main mass: extent is the share of rows down to the row below which
    TAIL or less of the main mass lies; share is the main mass's cells over all cells; marked counts every marked
    cell (zero means nothing is drawn). drawn: see main_mass."""
    total = sum(sum(row) for row in cells)
    cells = main_mass(cells, drawn)
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
    return (last + 1) / len(per_row), marked / (len(per_row) * len(cells[0])), total


def run(deck, ctx):
    out = []
    band = ctx.canvas.content
    for i in range(1, ctx.n + 1):
        s = ctx.slide(i)
        if ctx.tags()[i - 1]["archetype"]:
            if ctx.is_frame(i):
                continue
        elif i == 1 or s["text"]["words_content"] <= UNTAGGED_WORDS:
            continue                               # an untagged cover is a frame
        extent, share, marked = measures(grid(s, ctx), grid(s, ctx, drawn_only=True))
        if not marked:
            out.append(Finding(GATE, FAIL, i, "", "a content slide with nothing drawn in the content band"))
            continue
        if extent < EXTENT:
            out.append(Finding(GATE, FAIL, i, "", "content spans %.0f%% of the band's height (its mass ends at %.2fin, "
                               "%.0f%% or less of its main mass below), min %.0f%%"
                               % (100 * extent, band.y + extent * band.h, 100 * TAIL, 100 * EXTENT)))
        if share < SHARE:
            out.append(Finding(GATE, FAIL, i, "", "content covers %.0f%% of the band (%d of %d cells in its main mass), min %.0f%%"
                               % (100 * share, round(share * GRID_X * GRID_Y), GRID_X * GRID_Y, 100 * SHARE)))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
