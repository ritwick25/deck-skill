"""P10 density: every content slide argues with a device; no unearned tile grid; no accent bar; few caps kickers.

  * a content slide (any family but Frame, or an untagged slide over 20 words) carries at least one icon
    (the read layer's icon units: pictures, icon-sized vector groups, lone vector glyphs) or at least two
    connectors: headed arrows, plus undirected connectors that link two distinct tiles (both ends land on drawn
    shapes, deckkit.read.connect's touch), which is how a node-and-edge graph argues;
  * more than six identical tiles needs six icons or six connectors (the same count) to earn it;
  * the left or top accent bar, judged by colour on any deck (deckkit.rules.is_accent_strip by='colour'):
      - a filled strip (deckkit.rules.is_strip: at most 0.10in thick, longer than 0.18in and 2x its thickness,
        x k) is a bar when it is at least 1.5pt (0.0208in) thick, its colour is not grey (HLS saturation 0.15 or
        more, and not a rule role of the theme), it is not named state.*, and it sits within 0.30in (x k) of a
        text block's left edge (a vertical strip) or top edge (a horizontal strip), parallel to it. A thinner strip
        is a divider;
      - a line (a cxnSp or a line-like sp) without an arrowhead counts only when it is at least 2pt heavy, vertical
        or horizontal, not grey, within 0.15in (x k) of a text block's left edge and no longer than 1.5x that
        block's height, so a chart reference line, an axis or a divider between columns is never a bar;
    a text block's edge is its frame's or its ink box's (deckkit.read.walk._text_box), whichever is nearer. A kit
    deck is held to the stricter role rule when it is built (by='role': any strip outside the rule roles);
  * an upper-case label sitting above the content of more than half the cards is a kicker on every card.
"""
from __future__ import annotations

import math
import sys
from collections import Counter

from _shared import FAIL, Finding, bx, cards, cli, has_text, is_filled, is_lined, is_state, kids_of, text_of, words
from deckkit.read.walk import _text_box
from deckkit.rules import HEADED, is_accent_strip, is_grey

GATE, TITLE = "P10", "density"
MAX_TILES = 6
BAR_REACH = 0.30        # how far (x k) a filled bar may sit from the text edge it marks
LINE_REACH = 0.15       # how far (x k) a line may sit from the text block's left edge
LINE_MIN_PT = 2.0       # a lighter line is a rule, never a bar
LINE_SPAN = 1.5         # a line longer than this many times the block's height is not the block's bar
AXIS_EPS = 0.02         # a line whose box is this thin across is vertical or horizontal
PT_IN = 1.0 / 72.0
TILE_MIN_AREA = 0.04  # sq in: a link joins boxes, not a chart's 0.14in dots


def _headed(L) -> bool:
    line = L.get("line") or {}
    return (line.get("head") or {}).get("type", "none") not in (None, "none") or \
        (line.get("tail") or {}).get("type", "none") not in (None, "none") or \
        (L.get("connector") or {}).get("head") in HEADED


def _arrows(shapes) -> int:
    n = 0
    for L in shapes:
        line = L.get("line") or {}
        headed = (line.get("head") or {}).get("type", "none") != "none" or \
                 (line.get("tail") or {}).get("type", "none") != "none"
        if headed and (L.get("connector") is not None or (L.get("geom") or {}).get("cust")):
            n += 1
        elif (L.get("connector") or {}).get("prst", "").endswith("Arrow"):
            n += 1
    return n


def _is_tile(L) -> bool:
    """A box a link can join: a filled or outlined shape (not a line), a picture or a graphic frame."""
    if L is None or L.get("line_like") or L.get("connector") is not None:
        return False
    return L["kind"] in ("pic", "graphic") or (L["kind"] == "sp" and (is_filled(L) or is_lined(L)))


def _links(shapes) -> int:
    """Undirected connectors whose two ends land on two distinct tiles (a graph's edges). A chart's polyline lands
    on labels and dots, never on two tiles."""
    by_id = {L["id"]: L for L in shapes}
    n = 0
    for L in shapes:
        c = L.get("connector")
        if c is None or _headed(L) or c.get("prst", "").endswith("Arrow"):
            continue
        if (L.get("line") or {}).get("type") in (None, "none"):
            continue
        t = c.get("touch") or {}
        st, en = t.get("start") or {}, t.get("end") or {}
        if not (st.get("ok") and en.get("ok")) or st.get("id") is None or st.get("id") == en.get("id"):
            continue
        a, b = by_id.get(st["id"]), by_id.get(en["id"])
        if _is_tile(a) and _is_tile(b) and min(a["bbox"]["w_in"] * a["bbox"]["h_in"],
                                                b["bbox"]["w_in"] * b["bbox"]["h_in"]) >= TILE_MIN_AREA:
            n += 1
    return n


def _seg_dist(a0, a1, b0, b1) -> float:
    """Shortest distance between two segments that do not cross: the least end-to-segment distance."""
    def pt_seg(p, s0, s1):
        dx, dy = s1[0] - s0[0], s1[1] - s0[1]
        ll = dx * dx + dy * dy
        t = 0.0 if ll == 0 else max(0.0, min(1.0, ((p[0] - s0[0]) * dx + (p[1] - s0[1]) * dy) / ll))
        return math.hypot(p[0] - (s0[0] + t * dx), p[1] - (s0[1] + t * dy))
    if a0[0] == a1[0] and b0[0] == b1[0] and min(a0[1], a1[1]) <= max(b0[1], b1[1]) and \
            min(b0[1], b1[1]) <= max(a0[1], a1[1]):
        return abs(a0[0] - b0[0])                       # two vertical segments that overlap in y
    return min(pt_seg(a0, b0, b1), pt_seg(a1, b0, b1), pt_seg(b0, a0, a1), pt_seg(b1, a0, a1))


def _text_blocks(shapes):
    """(frame box, ink box, leaf) for every text block."""
    out = []
    for L in shapes:
        if has_text(L):
            try:
                ink = _text_box(L)
            except Exception:
                ink = bx(L)
            out.append((bx(L), ink, L))
    return out


def _strip_bar(L, texts, ctx):
    """(colour, side, text) when a filled strip is a bar beside a text block, else None."""
    f = L.get("fill") or {}
    if f.get("type") != "solid" or has_text(L):
        return None
    x0, y0, x1, y1 = bx(L)
    w, h = x1 - x0, y1 - y0
    colour = f.get("hex")
    if not colour or not is_accent_strip(w, h, colour, L.get("name"), ctx.theme, k=ctx.k, by="colour"):
        return None
    reach = BAR_REACH * ctx.k
    vertical = h >= w
    for fr, ink, T in texts:
        if T is L:
            continue
        if vertical:
            if fr[1] < y1 and fr[3] > y0 and any(0 <= e - x1 < reach for e in (fr[0], ink[0])):
                return colour, "left", text_of(T)
        elif fr[0] < x1 and fr[2] > x0 and (x1 - x0) < 0.9 * ctx.W and \
                any(0 <= e - y1 < reach for e in (fr[1], ink[1])):
            return colour, "top", text_of(T)
    return None


def _line_bar(L, texts, ctx):
    """(colour, side, text) when an undirected line is a bar at a text block's left edge, else None."""
    line = L.get("line") or {}
    if line.get("type") in (None, "none") or _headed(L):
        return None
    weight = line.get("w_pt") or 0.75
    colour = line.get("hex")
    if weight < LINE_MIN_PT - 1e-9 or not colour or is_grey(colour, ctx.theme):
        return None
    x0, y0, x1, y1 = bx(L)
    c = L.get("connector") or {}
    if c.get("start_in") and c.get("end_in"):
        a0, a1 = tuple(c["start_in"]), tuple(c["end_in"])
    elif x1 - x0 <= y1 - y0:
        a0, a1 = ((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)
    else:
        a0, a1 = (x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)
    vertical = abs(a1[0] - a0[0]) <= AXIS_EPS
    horizontal = abs(a1[1] - a0[1]) <= AXIS_EPS
    if not (vertical or horizontal):
        return None
    if vertical:
        a0, a1 = (a0[0], a0[1]), (a0[0], a1[1])
    length = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
    reach = LINE_REACH * ctx.k
    half = weight * PT_IN / 2
    for fr, ink, T in texts:
        if T is L or length > LINE_SPAN * (fr[3] - fr[1]):
            continue
        for e in (fr[0], ink[0]):
            if vertical and not (a0[0] - half <= e + 1e-9):
                continue                                 # a vertical line right of the edge is inside the block
            if _seg_dist(a0, a1, (e, fr[1]), (e, fr[3])) <= reach + half:
                return colour, "left", text_of(T)
    return None


def _bars(shapes, ctx):
    texts = _text_blocks(shapes)
    hits = []
    for L in shapes:
        if is_state(L) or L["kind"] not in ("sp", "cxn"):
            continue
        if L.get("line_like") or L["kind"] == "cxn":
            hit = _line_bar(L, texts, ctx)
        else:
            hit = _strip_bar(L, texts, ctx)
        if hit:
            hits.append((L,) + hit)
    return hits


def _caps_kicker(c, s) -> bool:
    kids = sorted((L for L in kids_of(c, s) if has_text(L)), key=lambda L: L["bbox"]["y_in"])
    if not kids:
        return False
    t = " ".join(text_of(kids[0]).split())
    return t == t.upper() and any(ch.isalpha() for ch in t) and words(t) <= 4 and len(kids) >= 2


def run(deck, ctx):
    out = []
    for i in range(1, ctx.n + 1):
        s = ctx.slide(i)
        shapes = s["shapes"]
        fam = ctx.slide_family(i)
        content = fam is not None and fam != "Frame" if ctx.tags()[i - 1]["archetype"] else \
            s["text"]["words_content"] > 20
        icons, arrows = len(s["icons"]), _arrows(shapes) + _links(shapes)
        if content and icons < 1 and arrows < 2:
            out.append(Finding(GATE, FAIL, i, "", "no icon and fewer than two arrows or links: nothing drawn argues "
                                                  "the slide"))
        sizes = Counter((round(L["bbox"]["w_in"], 2), round(L["bbox"]["h_in"], 2)) for L in shapes
                        if L["kind"] == "sp" and L["bbox"]["w_in"] > 0.7 * ctx.k and L["bbox"]["h_in"] > 0.35 * ctx.k
                        and not L.get("line_like"))
        run_ = sizes.most_common(1)[0][1] if sizes else 0
        if run_ > MAX_TILES and icons < MAX_TILES and arrows < MAX_TILES:
            out.append(Finding(GATE, FAIL, i, "", "%d identical tiles with %d icons and %d arrows or links" % (run_, icons, arrows)))
        for L, colour, side, near in _bars(shapes, ctx):
            out.append(Finding(GATE, FAIL, i, L["name"], "%s accent bar (%s) beside %r; only state.* may carry one"
                               % (side, colour, near[:30])))
        cs = cards(s, ctx)
        if len(cs) >= 2:
            n = sum(1 for c in cs if _caps_kicker(c, s))
            if n > len(cs) / 2:
                out.append(Finding(GATE, FAIL, i, "", "caps label above the content of %d of %d cards" % (n, len(cs))))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
