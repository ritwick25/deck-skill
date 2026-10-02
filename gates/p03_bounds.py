"""P03 bounds: every shape's rotated absolute box stays on the slide (0.05in x k); bleed.* names excepted.

Boxes come from deckkit.geom.iter_abs: every group transform composed, rotation and flips applied, so a
rotated label is judged by the box the renderer paints, not the unrotated box it stores. Hidden shapes are
skipped (they do not render; P19 reports them).
"""
from __future__ import annotations

import sys

from _shared import FAIL, Finding, cli, geom

GATE, TITLE = "P03", "bounds"
TOL_IN = 0.05


def run(deck, ctx):
    out = []
    tol = TOL_IN * ctx.k
    W, H = ctx.W, ctx.H
    for i, slide in enumerate(ctx.prs().slides, start=1):
        for g in geom.iter_abs(slide, hidden=False):
            if g.name.startswith("bleed.") or not g.has_xfrm:
                continue
            off = {"left": -g.x, "top": -g.y, "right": g.r - W, "bottom": g.b - H}
            side = max(off, key=off.get)
            if off[side] > tol:
                out.append(Finding(GATE, FAIL, i, g.name or "id %d" % g.id,
                                   "%.3fin past the %s edge" % (off[side], side)))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
