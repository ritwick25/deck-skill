"""P07 row: sibling cards never touch (gap >= 0.05in x k), and a row's headings start at one offset (spread <= 0.05in).

Cards are rect-like shapes filled in a card ROLE (paper, card, accent-tint, accent-wash: resolved through
the deck's theme, never a hex list) or outlined on no fill. They pair only at the same nesting depth, side
by side (or stacked) with at least 60% overlap on the other axis. Three or more cards that agree on top and
height are a row by construction, so their first children must start at the same offset below the top.
"""
from __future__ import annotations

import sys

from _shared import FAIL, Finding, cards, cli, has_text, kids_of

GATE, TITLE = "P07", "row"
MIN_GAP, HEAD_TOL = 0.05, 0.05
SAME_TOP, SAME_H, OVERLAP = 0.02, 0.02, 0.60


def _gap(a, b):
    """(gap, axis) when a and b sit beside or above each other with enough overlap, else None."""
    al, at, ar, ab = a["box"]
    bl, bt, br, bb = b["box"]
    ov_y = min(ab, bb) - max(at, bt)
    if ov_y > OVERLAP * max(ab - at, bb - bt):
        if bl >= ar - 0.02:
            return bl - ar, "x"
        if al >= br - 0.02:
            return al - br, "x"
    ov_x = min(ar, br) - max(al, bl)
    if ov_x > OVERLAP * max(ar - al, br - bl):
        if bt >= ab - 0.02:
            return bt - ab, "y"
        if at >= bb - 0.02:
            return at - bb, "y"
    return None


def run(deck, ctx):
    out = []
    k = ctx.k
    for i in range(1, ctx.n + 1):
        s = ctx.slide(i)
        cs = cards(s, ctx)
        for n, a in enumerate(cs):
            for b in cs[n + 1:]:
                if a["depth"] != b["depth"]:
                    continue
                g = _gap(a, b)
                if g is not None and -0.02 < g[0] < MIN_GAP * k:
                    out.append(Finding(GATE, FAIL, i, "%s / %s" % (a["L"]["name"], b["L"]["name"]),
                                       "cards %.3fin apart (%s), which reads as touching" % (g[0], g[1])))
        seen = set()
        for n, a in enumerate(cs):
            if id(a) in seen:
                continue
            row = [a] + [b for b in cs[n + 1:] if b["depth"] == a["depth"]
                         and abs(b["box"][1] - a["box"][1]) < SAME_TOP
                         and abs((b["box"][3] - b["box"][1]) - (a["box"][3] - a["box"][1])) < SAME_H
                         and (_gap(a, b) or (None, None))[1] == "x"]
            if len(row) < 3:
                continue
            seen.update(id(c) for c in row)
            heads = []
            for c in row:
                kids = [L for L in kids_of(c, s) if has_text(L) or L.get("icon_like") or L["kind"] == "pic"]
                if kids:
                    heads.append(min(L["bbox"]["y_in"] for L in kids) - c["box"][1])
            if len(heads) > 1 and max(heads) - min(heads) > HEAD_TOL * k:
                out.append(Finding(GATE, FAIL, i, ", ".join(c["L"]["name"] for c in row),
                                   "%d aligned cards, first content at %s below their tops"
                                   % (len(row), "/".join("%.2f" % h for h in heads))))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
