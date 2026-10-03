"""P03 bounds: every shape stays on the slide (0.05in x k) and inside the content band's left and right edges
(0.10in x k); bleed.* names excepted.

  * slide edge: every shape's rotated absolute box (deckkit.geom.iter_abs: every group transform composed, rotation
    and flips applied, so a rotated label is judged by the box the renderer paints) stays within 0.05in (x k) of
    the slide;
  * content margins: every shape stays within 0.10in (x k) of the canvas's content band at left and right
    (deckkit.canvas: WIDE.content x 0.50 to 12.90in, STD 0.28 to 9.72in), so the edges line up from slide to
    slide. A text block that draws no fill and no outline is judged by where its words sit (its ink box,
    _shared.ink_box), anything that draws by its frame. One finding per top-level shape, naming its worst leaf.
    Top and bottom belong to P09 (chrome) and P24 (fill).
A shape named bleed.*, or inside a group named bleed.*, is exempt from both. Hidden shapes are skipped (they do
not render; P19 reports them).
"""
from __future__ import annotations

import sys

from _shared import FAIL, Finding, cli, geom, ink_box
from deckkit.read.ns import local

GATE, TITLE = "P03", "bounds"
TOL_IN = 0.05
MARGIN_IN = 0.10


def _bleed(name: str | None) -> bool:
    return (name or "").startswith("bleed.")


def run(deck, ctx):
    out = []
    tol = TOL_IN * ctx.k
    W, H = ctx.W, ctx.H
    for i, slide in enumerate(ctx.prs().slides, start=1):
        bleed_ids = set()
        for g in geom.iter_abs(slide, groups=True, hidden=False):
            if _bleed(g.name) or g.parent_id in bleed_ids:
                bleed_ids.add(g.id)
                continue
            if local(g.el) == "grpSp" or not g.has_xfrm:
                continue
            off = {"left": -g.x, "top": -g.y, "right": g.r - W, "bottom": g.b - H}
            side = max(off, key=off.get)
            if off[side] > tol:
                out.append(Finding(GATE, FAIL, i, g.name or "id %d" % g.id,
                                   "%.3fin past the %s edge" % (off[side], side)))
        out += _margins(ctx, i)
    return out


def _margins(ctx, i) -> list[Finding]:
    """One FAIL per top-level shape whose leaves reach past the content band's left or right edge."""
    band = ctx.canvas.content
    tol = MARGIN_IN * ctx.k
    names = {int(c.get("id", "0")): c.get("name") or "" for c in ctx.slide_root(i).iter("{*}cNvPr")}
    worst = {}
    for L in ctx.slide(i)["shapes"]:
        if _bleed(L["name"]) or any(_bleed(names.get(g)) for g in L["group_path"]):
            continue
        x0, _y0, x1, _y1 = ink_box(L)
        over = {"left": band.x - x0, "right": x1 - band.r}
        side = max(over, key=over.get)
        if over[side] <= tol:
            continue
        top = L["group_path"][0] if L["group_path"] else L["id"]
        if over[side] > worst.get(top, (0.0,))[0]:
            worst[top] = (over[side], side, L["name"] or "id %d" % L["id"])
    out = []
    for top, (d, side, leaf) in sorted(worst.items(), key=lambda kv: -kv[1][0]):
        owner = names.get(top) or leaf
        where = owner if owner == leaf else "%s (%s)" % (owner, leaf)
        out.append(Finding(GATE, FAIL, i, where, "%.2fin past the content band's %s edge at %.2fin (bleed.* only for "
                           "a shape that bleeds on purpose)" % (d, side, band.x if side == "left" else band.r)))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
