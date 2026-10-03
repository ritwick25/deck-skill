"""P07 row: sibling cards never touch (gap >= 0.05in x k), and a row's headings start at one offset (spread <= 0.05in).

Cards are rect-like shapes filled in a card ROLE (paper, card, accent-tint, accent-wash: resolved through
the deck's theme, never a hex list) or outlined on no fill. They pair only at the same nesting depth, side
by side (or stacked) with at least 60% overlap on the other axis. Three or more cards that agree on top and
height are a row by construction, so their first content must sit at the same offset below the top (spread <= 0.05in
x k). A card's content is every leaf its box contains, by geometry alone (z-order does not matter: an outline card is
often drawn over its own heading) that carries text, is an icon or is a picture, plus a full-width header bar: a
filled shape as wide as the card (to 0.02in), starting at the card's top (it may overhang it by up to 0.10in x k)
and less than 60% of its height. A header bar is the card's first content wherever it is drawn.

The first content is the topmost content leaf (a header bar first), and its offset is anchor-aware, so a row
compares what the eye compares:
  * text compares by its frame's anchor: top-anchored text by its top, centre-anchored text by its centre,
    bottom-anchored text by its bottom;
  * an icon or a picture compares by its centre (marks of different sizes centre on one line);
  * a header bar with no text compares by its top;
  * a frame fitted to its text (spAutoFit, or the text fills 95% of it or more) has no room to move its text, so
    its anchor says nothing: when every card's first content is a fitted frame, the row is even when the frames
    agree on their tops or on their centres (a designer aligns fitted frames either way).
"""
from __future__ import annotations

import sys

from _shared import FAIL, Finding, bx, cards, cli, has_text, is_filled, kids_of

GATE, TITLE = "P07", "row"
MIN_GAP, HEAD_TOL = 0.05, 0.05
SAME_TOP, SAME_H, OVERLAP = 0.02, 0.02, 0.60
BAR_W_TOL = 0.02          # a header bar is the card's width to this (in)
BAR_OVERHANG = 0.10       # ... starts at the card's top, or overhangs it by up to this (x k)
BAR_H = 0.60              # ... and is less than this share of the card's height
FITTED = 0.95             # a frame whose text fills this share of it or more is fitted to its text


def header_bars(c, s, k: float = 1.0) -> list[dict]:
    """Filled shapes as wide as card c, starting at its top (or overhanging it a little), shorter than 60% of it."""
    C = c["L"]
    l, t, r, b = c["box"]
    out = []
    for L in s["shapes"]:
        if L is C or L["kind"] != "sp" or L.get("line_like") or not is_filled(L):
            continue
        x0, y0, x1, y1 = bx(L)
        if abs(x0 - l) <= BAR_W_TOL and abs(x1 - r) <= BAR_W_TOL and t - BAR_OVERHANG * k <= y0 <= t + 0.01 \
                and y1 <= b + 0.01 and (y1 - y0) < BAR_H * (b - t):
            out.append(L)
    return out


def ref_y(L) -> float:
    """The y a row compares for one content leaf: by anchor for text, the centre for a mark, the top otherwise."""
    x0, y0, x1, y1 = bx(L)
    if has_text(L):
        a = ((L["text"].get("body") or {}).get("anchor") or "t")
        return (y0 + y1) / 2 if a == "ctr" else y1 if a == "b" else y0
    if L.get("icon_like") or L["kind"] == "pic":
        return (y0 + y1) / 2
    return y0


def fitted(L) -> bool:
    """A text frame sized to its text: its anchor cannot move the text."""
    if not has_text(L):
        return False
    tx = L["text"]
    return (tx.get("body") or {}).get("autofit") == "shape" or (tx.get("occupancy") or 0.0) >= FITTED


def spread(firsts, tops) -> float:
    """The row's spread of first-content offsets below the card tops (see the module notes)."""
    def sp(vals):
        return max(vals) - min(vals)
    best = sp([ref_y(L) - t for L, t in zip(firsts, tops)])
    if all(fitted(L) for L in firsts):
        best = min(best, sp([bx(L)[1] - t for L, t in zip(firsts, tops)]),
                   sp([(bx(L)[1] + bx(L)[3]) / 2 - t for L, t in zip(firsts, tops)]))
    return best


def first_content(c, s, k: float = 1.0):
    """The card's first content leaf: a header bar when it has one, else its topmost text, icon or picture."""
    bars = header_bars(c, s, k)
    if bars:
        return min(bars, key=lambda L: (bx(L)[1], -L.get("z", 0)))
    kids = [L for L in kids_of(c, s, any_z=True, full_width=True)
            if has_text(L) or L.get("icon_like") or L["kind"] == "pic"]
    if not kids:
        return None
    return min(kids, key=lambda L: (bx(L)[1], ref_y(L)))


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
            firsts, tops = [], []
            for c in row:
                L = first_content(c, s, k)
                if L is not None:
                    firsts.append(L)
                    tops.append(c["box"][1])
            heads = [ref_y(L) - t for L, t in zip(firsts, tops)]
            if len(heads) > 1 and spread(firsts, tops) > HEAD_TOL * k:
                out.append(Finding(GATE, FAIL, i, ", ".join(c["L"]["name"] for c in row),
                                   "%d aligned cards, first content at %s below their tops"
                                   % (len(row), "/".join("%.2f" % h for h in heads))))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
