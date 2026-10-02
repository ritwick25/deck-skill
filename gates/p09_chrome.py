"""P09 chrome: no foot band, foot sentence, subtitle, page number, confidentiality line, footer logo or master chrome.

Thresholds are fractions of the canvas, measured on the accepted WIDE deck and scaled so both canvases
work: the foot line is 6.30 / 7.5 of the height, a band is 8 / 13.333 of the width from 6.20 / 7.5 down, a
narrow card is under 6.5 / 13.333 of the width. The subtitle is the read layer's own role (text directly
under the title, smaller, four words or more, at least 40% of the title's width) and must not sit on a
filled shape. deck.json may grant P09:subtitle (R-NOSUB) or P09:foot (R-NOFOOT) inside its own folder.
"""
from __future__ import annotations

import sys

from _shared import FAIL, NOTE, Finding, bx, cli, has_text, is_filled, is_lined, text_of, words
from deckkit.read.deckinfo import CONFIDENTIAL

GATE, TITLE = "P09", "chrome"
FOOT_Y, BAND_Y, BAND_W, CARD_W = 6.30 / 7.5, 6.20 / 7.5, 8.0 / 13.333, 6.5 / 13.333
LOGO_Y = 0.90
FOOT_WORDS = 5


def _inside(b, c, eps=0.02):
    return b[0] >= c[0] - eps and b[1] >= c[1] - eps and b[2] <= c[2] + eps and b[3] <= c[3] + eps


def run(deck, ctx):
    out = []
    W, H, k = ctx.W, ctx.H, ctx.k
    foot_ok = ctx.overridden("P09:foot")
    sub_ok = ctx.overridden("P09:subtitle")
    for src, key in ((foot_ok, "P09:foot"), (sub_ok, "P09:subtitle")):
        if src:
            out.append(Finding(GATE, NOTE, None, key, "overridden by deck.json (%s)" % src))
    for i in range(1, ctx.n + 1):
        s = ctx.slide(i)
        shapes = s["shapes"]
        boxes = [(bx(L), L) for L in shapes if L["kind"] == "sp" and (is_filled(L) or is_lined(L))]
        for L in s["chrome"]:
            if has_text(L) or L["kind"] == "pic":
                out.append(Finding(GATE, FAIL, i, L["name"] or "master/layout",
                                   "persistent chrome on the master or layout: %r" % (text_of(L)[:40] or L["kind"])))
        root = ctx.slide_root(i)
        if any((f.get("type") or "") == "slidenum" for f in root.iter("{*}fld")):
            out.append(Finding(GATE, FAIL, i, "", "slide-number field"))
        for L in shapes:
            b = bx(L)
            role = (L.get("role_guess") or {}).get("role")
            ph = (L.get("placeholder") or {}).get("type")
            t = " ".join(text_of(L).split())
            if ph in ("sldNum", "ftr", "dt"):
                out.append(Finding(GATE, FAIL, i, L["name"], "%s placeholder" % ph))
            if role == "page-number":
                out.append(Finding(GATE, FAIL, i, L["name"], "page number %r" % t))
            if t and CONFIDENTIAL.search(t):
                out.append(Finding(GATE, FAIL, i, L["name"], "confidentiality line %r" % t[:50]))
            if L["kind"] == "sp" and not foot_ok and (is_filled(L) or is_lined(L)) and b[2] - b[0] >= BAND_W * W \
                    and b[1] >= BAND_Y * H and b[3] - b[1] > 0.05 * k:
                out.append(Finding(GATE, FAIL, i, L["name"], "foot band %.1fin wide at %.2fin" % (b[2] - b[0], b[1])))
            if L["kind"] == "pic" and b[1] >= LOGO_Y * H:
                out.append(Finding(GATE, FAIL, i, L["name"], "picture in the foot (a footer logo) at %.2fin" % b[1]))
            if not has_text(L):
                continue
            if not foot_ok and b[1] >= FOOT_Y * H and words(t) >= FOOT_WORDS and L["kind"] != "cell":
                narrow = [c for c, CL in boxes if CL is not L and (c[2] - c[0]) < CARD_W * W and _inside(b, c)]
                if not narrow:
                    out.append(Finding(GATE, FAIL, i, L["name"], "foot sentence at %.2fin: %r" % (b[1], t[:50])))
            if role == "subtitle" and not sub_ok and t != t.upper():
                cy = (b[1] + b[3]) / 2
                on_fill = any(c[1] <= cy <= c[3] and b[0] >= c[0] - 0.15 and b[2] <= c[2] + 0.15
                              for c, CL in boxes if CL is not L and is_filled(CL))
                if not on_fill:
                    out.append(Finding(GATE, FAIL, i, L["name"], "subtitle under the title: %r" % t[:50]))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
