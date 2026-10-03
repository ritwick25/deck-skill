"""P04 padding: a child that starts inside a container clears all four edges (fail under 0.04in, advisory to 0.10in, x k).

Containers are rect-like shapes with a fill or an outline, at least 1.2 x 0.45in. A child is any drawn
leaf painted above the container whose top-left corner lies inside it (the start-inside rule keeps a
header bar from "containing" text five inches below it). Connectors are never children: an arrow's job is
to leave the shape it starts on. Two idioms are deliberate and pass: an overlay (a text box coincident
with its shape on every side, within 0.035in) and a span (a child running the container's full width or
full height, padded by its own insets). state.* marks sit on an edge by definition (a quotation bar). An edge pin
sits on its container's border by notation (spec 3.1: a VPC endpoint or load balancer pinned to the VPC edge): a
picture of 0.20 to 0.62in whose centre lies on one of the container's edges (within 0.02in) is not its child.

The idioms are judged on the child's frame (they describe how a frame is placed); the clearances are measured on
what the eye sees: a text block that draws no fill and no outline by its ink box (deckkit.read.walk._text_box,
occupancy-trimmed and aligned, through _shared.ink_box), so a frame that runs past a card while its two words sit
well inside is not an overflow. Anything that draws (a filled text shape, a picture, a card) keeps its frame.
"""
from __future__ import annotations

import sys

from _shared import ADVISORY, FAIL, Finding, bx, cli, full_bleed, ink_box, is_drawn, is_rect_like, is_state

GATE, TITLE = "P04", "padding"
PIN_MIN, PIN_MAX, PIN_TOL = 0.20, 0.62, 0.02


def edge_pin(L, box) -> bool:
    """A picture centred on one edge of box: an endpoint or a load balancer pinned to a boundary (spec 3.1)."""
    if L["kind"] != "pic":
        return False
    x0, y0, x1, y1 = bx(L)
    w, h = x1 - x0, y1 - y0
    if not (PIN_MIN <= max(w, h) <= PIN_MAX):
        return False
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    cl, ct, cr, cb = box
    on_v = (abs(cx - cl) <= PIN_TOL or abs(cx - cr) <= PIN_TOL) and ct <= cy <= cb
    on_h = (abs(cy - ct) <= PIN_TOL or abs(cy - cb) <= PIN_TOL) and cl <= cx <= cr
    return on_v or on_h
MIN_CLEAR, ADVISE = 0.04, 0.10
MIN_W, MIN_H = 1.20, 0.45
EPS, COINCIDENT, SPAN = 0.02, 0.035, 0.02


def run(deck, ctx):
    out = []
    k = ctx.k
    for i in range(1, ctx.n + 1):
        s = ctx.slide(i)
        shapes = s["shapes"]
        cons = [L for L in shapes if L["kind"] == "sp" and is_rect_like(L) and not full_bleed(L, ctx)
                and L["bbox"]["w_in"] >= MIN_W * k and L["bbox"]["h_in"] >= MIN_H * k]
        for C in cons:
            cl, ct, cr, cb = bx(C)
            for L in shapes:
                if L is C or L.get("z", 0) <= C.get("z", 0) or L.get("line_like") or L["kind"] == "cxn":
                    continue
                if not is_drawn(L) or is_state(L) or L["kind"] == "cell":
                    continue
                fx0, fy0, fx1, fy1 = bx(L)
                if (fx1 - fx0) * (fy1 - fy0) >= (cr - cl) * (cb - ct):
                    continue                       # the child is the bigger shape: it is not inside
                if edge_pin(L, (cl, ct, cr, cb)):
                    continue                       # an edge pin: on the border by notation
                fclr = {"left": fx0 - cl, "top": fy0 - ct, "right": cr - fx1, "bottom": cb - fy1}
                if all(abs(v) <= COINCIDENT for v in fclr.values()):
                    continue                       # overlay: text drawn exactly on its shape
                if (abs(fclr["left"]) <= SPAN and abs(fclr["right"]) <= SPAN) or \
                        (abs(fclr["top"]) <= SPAN and abs(fclr["bottom"]) <= SPAN):
                    if min(fclr.values()) >= -SPAN:
                        continue                   # span: padded by its own insets
                x0, y0, x1, y1 = ink_box(L)
                if not (cl - EPS <= x0 < cr and ct - EPS <= y0 < cb):
                    continue
                clr = {"left": x0 - cl, "top": y0 - ct, "right": cr - x1, "bottom": cb - y1}
                side = min(clr, key=clr.get)
                v = clr[side]
                what = "%s in %s" % (L["name"] or "id %d" % L["id"], C["name"] or "id %d" % C["id"])
                if v < 0:
                    out.append(Finding(GATE, FAIL, i, what, "overflows its container by %.3fin (%s)" % (-v, side)))
                elif v < MIN_CLEAR * k:
                    out.append(Finding(GATE, FAIL, i, what, "%.3fin from the %s edge (floor %.2f)" % (v, side, MIN_CLEAR * k)))
                elif v < ADVISE * k:
                    out.append(Finding(GATE, ADVISORY, i, what, "%.3fin from the %s edge" % (v, side)))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
