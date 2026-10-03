"""P25 text contrast: every run on glass clears the WCAG 2.x minimum against what is painted behind it.

For every text run, the colour behind it is the nearest visible shape below the run in z-order whose box holds the
run's text box, else the slide background:
  * the run's text box is where its glyphs sit (the read layer's ink box: the lines the text fills, placed by the
    frame's anchor, at the estimated width when every line fits unwrapped); a table cell keeps its whole cell;
  * the shape that carries the text is the first candidate (its fill is painted under its own text), then every
    shape lower in z-order on the slide, then the layout and master shapes, then the slide background. A box holds
    the text box when it contains it (within HOLD_EPS), or when it contains the text box's centre and covers at
    least HOLD_SHARE of its area: a text frame drawn a little wider than the pill or band it sits on is still on
    that pill, never on whatever lies under the pill;
  * text wholly under an opaque shape drawn above it (a solid fill at full alpha, or a picture) is not on glass:
    it is counted in the slide's note, never measured;
  * visible means a fill that is not none and not fully transparent; a fill with alpha is composited over what is
    below it, and a run with alpha over its background (a gradient reads as its stops' mean, a pattern as its
    foreground, as deckkit.read.colour resolves them);
  * a picture (or a picture fill) behind the text cannot be resolved to one colour: the run is not measured, and
    the slide gets one note counting such runs.
The minimum is deckkit.rules.contrast_min, the builder's own predicate: 4.5:1, or 3.0:1 for 14pt bold and larger or
18pt and larger (the rendered size, autofit scale included). One finding per text shape, naming its worst run.
"""
from __future__ import annotations

import sys

from _shared import FAIL, NOTE, Finding, bx, cli, crash, has_text
from deckkit.read.colour import contrast, hex2rgb, rgb2hex
from deckkit.read.walk import _text_box
from deckkit.rules import contrast_min

GATE, TITLE = "P25", "contrast"
HOLD_EPS = 0.03          # inches a holding box may fall short of the text box on any side (EMU rounding, ink estimate)
HOLD_SHARE = 0.60        # ... or the share of the text box it covers, with the text box's centre inside it
PAGE = "FFFFFF"          # a slide with no background fill shows white


def _alpha(f) -> float:
    a = f.get("alpha")
    return 1.0 if a is None else float(a)


def _visible(L) -> bool:
    if L.get("on_canvas") == "off":
        return False
    if L["kind"] == "pic":
        return True
    f = L.get("fill") or {}
    return f.get("type") not in (None, "none") and _alpha(f) > 0.0


def _contains(L, box, eps=HOLD_EPS) -> bool:
    x0, y0, x1, y1 = bx(L)
    return x0 <= box[0] + eps and y0 <= box[1] + eps and x1 >= box[2] - eps and y1 >= box[3] - eps


def _holds(L, box) -> bool:
    """L's box contains the text box, or holds its centre and covers HOLD_SHARE of it."""
    if _contains(L, box):
        return True
    x0, y0, x1, y1 = bx(L)
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    if not (x0 <= cx <= x1 and y0 <= cy <= y1):
        return False
    area = max(1e-9, (box[2] - box[0]) * (box[3] - box[1]))
    ow = max(0.0, min(x1, box[2]) - max(x0, box[0]))
    oh = max(0.0, min(y1, box[3]) - max(y0, box[1]))
    return ow * oh >= HOLD_SHARE * area


def _opaque(M) -> bool:
    if M["kind"] == "pic":
        return True
    f = M.get("fill") or {}
    return f.get("type") in ("solid", "picture") and _alpha(f) >= 1.0


def hidden(L, s) -> bool:
    """L's text box lies wholly under an opaque shape drawn above it."""
    box = _text_box(L)
    z = L.get("z", 0)
    return any(M is not L and M.get("z", 0) > z and M.get("on_canvas") != "off" and _opaque(M) and _contains(M, box)
               for M in s["shapes"])


def _over(top_hex, alpha, bottom_hex) -> str:
    """top over bottom at alpha (source-over, in sRGB as the renderers composite)."""
    if alpha >= 1.0:
        return top_hex
    t, b = hex2rgb(top_hex), hex2rgb(bottom_hex)
    return rgb2hex(tuple(alpha * t[k] + (1.0 - alpha) * b[k] for k in range(3)))


def _page(s) -> tuple[str | None, str]:
    """The slide background's colour and a label for it; None when it is a picture."""
    f = (s.get("background") or {}).get("fill") or {}
    t = f.get("type")
    if t in (None, "none"):
        return PAGE, "the slide (white)"
    if t == "picture":
        return None, "a picture background"
    return _over(f.get("hex") or PAGE, _alpha(f), PAGE), "the slide background %s" % (f.get("hex") or PAGE)


def behind(L, s) -> tuple[str | None, str]:
    """(hex painted behind L's text, a label naming it); hex None when a picture is behind it."""
    box = _text_box(L)
    z = L.get("z", 0)
    stack = []                                  # nearest first: own fill, lower slide shapes, then chrome
    if L["kind"] != "pic" and _visible(L):
        stack.append(L)
    lower = [M for M in s["shapes"] if M is not L and M.get("z", 0) < z and _visible(M) and _holds(M, box)]
    stack += sorted(lower, key=lambda M: -M.get("z", 0))
    chrome = [M for M in s.get("chrome") or [] if _visible(M) and _holds(M, box)]
    stack += sorted(chrome, key=lambda M: -M.get("z", 0))
    layers = []
    for M in stack:
        f = M.get("fill") or {}
        if M["kind"] == "pic" or f.get("type") == "picture":
            return None, "the picture %s" % (M.get("name") or M["id"])
        layers.append((f.get("hex") or PAGE, _alpha(f), M))
        if _alpha(f) >= 1.0:
            break
    else:
        base, label = _page(s)
        if base is None:
            return None, label
        layers.append((base, 1.0, None))
    hx = layers[-1][0]
    for top, a, _M in reversed(layers[:-1]):
        hx = _over(top, a, hx)
    first = layers[0][2]
    if first is None:
        return hx, label
    return hx, ("its own fill %s" % hx if first is L else "%s (%s)" % (first.get("name") or first["id"], hx))


def run(deck, ctx):
    out = []
    for i in range(1, ctx.n + 1):
        s = ctx.slide(i)
        unmeasured = covered = 0
        for L in s["shapes"]:
            if not has_text(L) or L.get("on_canvas") == "off":
                continue
            try:
                if hidden(L, s):
                    covered += sum(1 for p in L["text"]["paragraphs"] for r in p["runs"] if r["t"].strip())
                    continue
                bg, label = behind(L, s)
                if bg is None:
                    unmeasured += sum(1 for p in L["text"]["paragraphs"] for r in p["runs"] if r["t"].strip())
                    continue
                worst = None
                for p in L["text"]["paragraphs"]:
                    for r in p["runs"]:
                        if not r["t"].strip():
                            continue
                        fg = _over(r.get("hex") or "000000", _alpha(r), bg)
                        ratio = contrast(fg, bg)
                        need = contrast_min(r["size_rendered_pt"], r["bold"])
                        if ratio + 1e-9 < need and (worst is None or ratio / need < worst[0] / worst[1]):
                            worst = (ratio, need, r, fg)
                if worst:
                    ratio, need, r, fg = worst
                    out.append(Finding(GATE, FAIL, i, L["name"] or str(L["id"]),
                                       "contrast %.2f:1, needs %.1f:1: %r (%s, %.1fpt%s) on %s"
                                       % (ratio, need, r["t"].strip()[:30], fg, r["size_rendered_pt"],
                                          " bold" if r["bold"] else "", label)))
            except Exception as e:  # one unreadable shape is a finding, and the gate goes on
                out.append(crash(GATE, i, L.get("name") or str(L.get("id")), e))
        if unmeasured:
            out.append(Finding(GATE, NOTE, i, "", "%d run(s) on a picture: contrast not measured" % unmeasured))
        if covered:
            out.append(Finding(GATE, NOTE, i, "", "%d run(s) under an opaque shape: not on glass, not measured"
                               % covered))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
