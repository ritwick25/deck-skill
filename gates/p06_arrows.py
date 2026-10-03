"""P06 arrows: both ends of every headed connector land on a shape (within 0.09in of its edge, or drawn onto
it), and on two different shapes.

Every end comes from deckkit.read.connect.touch, the house arrow test: the candidates are drawing shapes that do
not hold the whole connector (an enclosing panel or card is where an arrow is drawn, never what it points at),
ranked by the distance from the end to their EDGE. Straight and bent connectors, line presets, block arrows and
open custom-geometry paths (deckkit.prims.elbow) all carry the read layer's connector block. A headed custom path
the read layer did not classify as a line is measured at its path's first and last points, through the same
touch(). An arrow whose two ends sit on the same shape points at nothing.

Two ends are not judged by touch() alone:
  * hidden: an end that lies under an opaque picture (no alpha channel, no alphaModFix below 100%) or an opaque
    solid-filled shape painted later (z above the connector) is invisible, so it is skipped, never a finding;
  * junction: an end within JUNCTION_TOL of another straight connector or line (a bus, a branch point) touches
    it, the way a tree of lines is drawn.
"""
from __future__ import annotations

import sys

from _shared import FAIL, Finding, cli
from deckkit.read import connect as cx
from deckkit.read.ns import A

GATE, TITLE = "P06", "arrows"
JUNCTION_TOL = 0.03     # an end this close to another line's stroke meets it
OPAQUE = 0.99           # alpha at or above this hides what lies under it


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


def _opaque(L) -> bool:
    """A leaf that hides what is painted under it: a picture with no transparency, or an opaque solid fill."""
    if L.get("line_like") or L.get("connector") is not None or L.get("on_canvas") == "off":
        return False
    if L["kind"] == "pic":
        pic = L.get("picture") or {}
        return not pic.get("has_alpha") and (pic.get("alpha") if pic.get("alpha") is not None else 1.0) >= OPAQUE
    f = L.get("fill") or {}
    return L["kind"] == "sp" and f.get("type") == "solid" and \
        (f.get("alpha") if f.get("alpha") is not None else 1.0) >= OPAQUE


def hidden(pt, L, leaves) -> int | None:
    """The id of an opaque leaf painted above connector L that covers pt, else None."""
    z = L.get("z", 0)
    for o in leaves:
        if o is L or o.get("z", 0) <= z or not _opaque(o):
            continue
        if cx.gap(pt, o) == 0.0:
            return o["id"]
    return None


def junction(pt, L, leaves) -> int | None:
    """The id of another straight connector or line whose stroke pt lies on (within JUNCTION_TOL), else None."""
    for o in leaves:
        c = o.get("connector")
        if o is L or c is None or (o.get("line") or {}).get("type") in (None, "none"):
            continue
        if c.get("orientation") not in ("h", "v", "diag") or not c.get("start_in") or not c.get("end_in"):
            continue
        half = (o.get("line") or {}).get("w_pt") or 0.75
        if cx._seg_dist(pt, tuple(c["start_in"]), tuple(c["end_in"])) <= JUNCTION_TOL + half / 144.0:
            return o["id"]
    return None


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
                if c.get("start_in") and c.get("end_in"):
                    ends = (tuple(c["start_in"]), tuple(c["end_in"]))
            elif (L.get("geom") or {}).get("cust") and _headed(L.get("line")):
                ends = _path_ends(ctx, i, L)
                if ends is None:
                    continue
                st = cx.touch(ends[0], leaves, L["id"], area, other=ends[1])
                en = cx.touch(ends[1], leaves, L["id"], area, other=ends[0])
            else:
                continue
            for k, (which, tt) in enumerate((("start", st), ("end", en))):
                if tt.get("ok"):
                    continue
                if ends is not None and (hidden(ends[k], L, leaves) is not None or
                                         junction(ends[k], L, leaves) is not None):
                    continue
                gap = tt.get("gap_in")
                out.append(Finding(GATE, FAIL, i, L["name"], "%s lands on nothing (%s from the nearest edge)"
                                   % (which, "%.3fin" % gap if gap is not None else "no shape")))
            if st.get("ok") and en.get("ok") and st.get("id") == en.get("id"):
                out.append(Finding(GATE, FAIL, i, L["name"], "both ends on the same shape (id %s)" % st.get("id")))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
