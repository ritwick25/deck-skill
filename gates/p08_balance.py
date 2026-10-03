"""P08 balance: a card's content does not float at its top (bottom air minus top air <= 0.12in x k).

A card with 0.16in of air above its content and 0.72in below reads as unfinished. Cards that share a top
and a height with a sibling are a row: their heights are set by the fullest card, so the row is judged by
the card with the least air below its content, never card by card (a short card in an even row is the
row's grammar, not a defect). Full-bleed panels are furniture, not cards.
"""
from __future__ import annotations

import sys

from _shared import FAIL, Finding, bx, cards, cli, ink_box, kids_of

GATE, TITLE = "P08", "balance"
TOL = 0.12


SLACK_CREDIT = 0.15     # the kit sizes a text frame at its measured height x 1.15 (deckkit.measure.SLACK)


def _bottom(L):
    """Where a kid's content ends: its ink, credited with the kit's fitting slack, never past its frame. A frame
    sized to its text reads as content; a frame stretched past its text is air (the half-empty card)."""
    ix0, iy0, ix1, iy1 = ink_box(L)
    fb = bx(L)[3]
    return min(fb, iy1 + SLACK_CREDIT * (iy1 - iy0) + 0.02)


def _air(c, s):
    kids = kids_of(c, s)
    if len(kids) < 2:
        return None
    l, t, r, b = c["box"]
    top = min(ink_box(L)[1] for L in kids) - t
    bot = b - max(_bottom(L) for L in kids)
    return top, bot


def run(deck, ctx):
    out = []
    tol = TOL * ctx.k
    for i in range(1, ctx.n + 1):
        s = ctx.slide(i)
        cs = [c for c in cards(s, ctx) if not ((c["box"][2] - c["box"][0]) > 0.9 * ctx.W and
                                               (c["box"][3] - c["box"][1]) > 0.8 * ctx.H)]
        done = set()
        for c in cs:
            if id(c) in done:
                continue
            row = [o for o in cs if o["depth"] == c["depth"] and abs(o["box"][1] - c["box"][1]) < 0.02
                   and abs((o["box"][3] - o["box"][1]) - (c["box"][3] - c["box"][1])) < 0.02]
            done.update(id(o) for o in row)
            airs = [(o, a) for o, a in ((o, _air(o, s)) for o in row) if a is not None]
            if not airs:
                continue
            o, (top, bot) = min(airs, key=lambda t: t[1][1])        # the fullest card of the row
            if bot - top > tol:
                where = o["L"]["name"] if len(row) == 1 else "row of %d (%s fullest)" % (len(row), o["L"]["name"])
                out.append(Finding(GATE, FAIL, i, where, "top-heavy: %.2fin above the content, %.2fin below"
                                   % (top, bot)))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
