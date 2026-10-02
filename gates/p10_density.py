"""P10 density: every content slide argues with a device; no unearned tile grid; no accent bar; few caps kickers.

  * a content slide (any family but Frame, or an untagged slide over 20 words) carries at least one icon
    (the read layer's icon units: pictures, icon-sized vector groups, lone vector glyphs) or at least two
    arrows (headed connectors);
  * more than six identical tiles needs six icons or six arrows to earn it;
  * a thin filled strip (or a heavy line) in a non-grey colour, immediately left of or above a text block, is
    the left or top accent bar: allowed only on a state.* shape;
  * an upper-case label sitting above the content of more than half the cards is a kicker on every card.
"""
from __future__ import annotations

import sys
from collections import Counter

from _shared import FAIL, Finding, bx, cards, cli, has_text, is_state, kids_of, text_of, words

GATE, TITLE = "P10", "density"
MAX_TILES = 6
BAR_THIN, BAR_LONG, BAR_REACH = 0.10, 0.18, 0.30
GREYS = ("paper", "card", "hairline", "hairline-soft", "rule-strong")


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


def _bars(shapes, ctx):
    greys = {ctx.theme.hex(r) for r in GREYS}
    texts = [(bx(L), L) for L in shapes if has_text(L)]
    hits = []
    for L in shapes:
        if is_state(L) or L["kind"] not in ("sp", "cxn"):
            continue
        x0, y0, x1, y1 = bx(L)
        w, h = x1 - x0, y1 - y0
        if L.get("line_like") or L["kind"] == "cxn":
            line = L.get("line") or {}
            if line.get("type") in (None, "none") or (line.get("w_pt") or 0) < 2.0 or line.get("hex") in greys:
                continue
            colour = line.get("hex")
        else:
            f = L.get("fill") or {}
            if f.get("type") != "solid" or f.get("hex") in greys or has_text(L):
                continue
            colour = f.get("hex")
        k = ctx.k
        vertical = w < BAR_THIN * k and h > BAR_LONG * k and h > 2 * w
        horizontal = h < BAR_THIN * k and w > BAR_LONG * k and w > 2 * h
        for (tx0, ty0, tx1, ty1), T in texts:
            if T is L:
                continue
            if vertical and 0 <= tx0 - x1 < BAR_REACH * k and ty0 < y1 and ty1 > y0:
                hits.append((L, colour, "left", text_of(T)))
                break
            if horizontal and 0 <= ty0 - y1 < BAR_REACH * k and tx0 < x1 and tx1 > x0 and (x1 - x0) < 0.9 * ctx.W:
                hits.append((L, colour, "top", text_of(T)))
                break
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
        icons, arrows = len(s["icons"]), _arrows(shapes)
        if content and icons < 1 and arrows < 2:
            out.append(Finding(GATE, FAIL, i, "", "no icon and fewer than two arrows: nothing drawn argues the slide"))
        sizes = Counter((round(L["bbox"]["w_in"], 2), round(L["bbox"]["h_in"], 2)) for L in shapes
                        if L["kind"] == "sp" and L["bbox"]["w_in"] > 0.7 * ctx.k and L["bbox"]["h_in"] > 0.35 * ctx.k
                        and not L.get("line_like"))
        run_ = sizes.most_common(1)[0][1] if sizes else 0
        if run_ > MAX_TILES and icons < MAX_TILES and arrows < MAX_TILES:
            out.append(Finding(GATE, FAIL, i, "", "%d identical tiles with %d icons and %d arrows" % (run_, icons, arrows)))
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
