"""P06 arrows: both ends of every headed connector land on a shape (within 0.09in), and on two different shapes.

Straight and bent connectors, line presets and block arrows come from the read layer's connector block,
whose touch() is the house arrow test (nearest non-line shape, full-bleed shapes skipped). A custom-geometry
path with an arrowhead (deckkit.prims.elbow) is measured at its path's first and last points, mapped
through the leaf's painted corners with its flips. An arrow whose two ends sit on the same shape points at
nothing.
"""
from __future__ import annotations

import sys

from _shared import FAIL, Finding, cli
from deckkit.read import connect as cx
from deckkit.read.ns import A

GATE, TITLE = "P06", "arrows"


def _headed(line) -> bool:
    line = line or {}
    return (line.get("head") or {}).get("type", "none") != "none" or \
           (line.get("tail") or {}).get("type", "none") != "none"


def _path_ends(ctx, i, L):
    """(start, end) of a custGeom open path in slide inches, or None."""
    el = ctx.element(i, L["id"])
    cg = el.find(".//" + A("custGeom")) if el is not None else None
    if cg is None:
        return None
    pts, wh = [], None
    for path in cg.iter(A("path")):
        w, h = float(path.get("w", "0") or 0), float(path.get("h", "0") or 0)
        for c in path:
            for pt in c.iter(A("pt")):
                try:
                    pts.append((float(pt.get("x")), float(pt.get("y")), w, h))
                except (TypeError, ValueError):
                    pass
    if len(pts) < 2:
        return None
    c0, c1, _c2, c3 = L["corners_in"]
    fh, fv = L["xfrm"]["flipH"], L["xfrm"]["flipV"]

    def at(x, y, w, h):
        u = x / w if w else 0.0
        v = y / h if h else 0.0
        u, v = (1 - u if fh else u), (1 - v if fv else v)
        return (c0[0] + u * (c1[0] - c0[0]) + v * (c3[0] - c0[0]),
                c0[1] + u * (c1[1] - c0[1]) + v * (c3[1] - c0[1]))
    return at(*pts[0]), at(*pts[-1])


def run(deck, ctx):
    out = []
    area = ctx.W * ctx.H
    for i in range(1, ctx.n + 1):
        leaves = ctx.slide(i)["shapes"]
        for L in leaves:
            c = L.get("connector")
            ends = None
            if c is not None:
                prst = c.get("prst")
                if not (_headed(L.get("line")) or prst in cx.BLOCK_ARROWS):
                    continue
                t = c.get("touch") or {}
                st, en = t.get("start") or {}, t.get("end") or {}
            elif (L.get("geom") or {}).get("cust") and _headed(L.get("line")):
                ends = _path_ends(ctx, i, L)
                if ends is None:
                    continue
                st = cx.touch(ends[0], leaves, L["id"], area)
                en = cx.touch(ends[1], leaves, L["id"], area)
            else:
                continue
            for which, tt in (("start", st), ("end", en)):
                if not tt.get("ok"):
                    gap = tt.get("gap_in")
                    out.append(Finding(GATE, FAIL, i, L["name"], "%s lands on nothing (%s from the nearest shape)"
                                       % (which, "%.3fin" % gap if gap is not None else "no shape")))
            if st.get("ok") and en.get("ok") and st.get("id") == en.get("id"):
                out.append(Finding(GATE, FAIL, i, L["name"], "both ends on the same shape (id %s)" % st.get("id")))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
