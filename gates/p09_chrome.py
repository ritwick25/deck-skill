"""P09 chrome: no foot band, foot sentence, subtitle, page number, confidentiality line, footer logo or master chrome.

Thresholds are fractions of the canvas, measured on the accepted WIDE deck and scaled so both canvases
work: the foot line is 6.30 / 7.5 of the height, a band is 8 / 13.333 of the width from 6.20 / 7.5 down, a
narrow card is under 6.5 / 13.333 of the width. The subtitle is the read layer's own role (text directly
under the title, smaller, four words or more, at least 40% of the title's width) and must not sit on a
filled shape. deck.json may grant P09:subtitle (R-NOSUB) or P09:foot (R-NOFOOT) inside its own folder.

Page numbers: the read layer's page-number role (a spelled-out number in the top or bottom band, a bare number in a
corner), plus a page label in a page-number position: 'A1' to 'A9', 'Appendix N' or 'N / M', set at 14pt or smaller
in the top or bottom PAGE_BAND of the canvas, in its outer PAGE_SIDE on either side or centred on it (within
PAGE_MID), and not painted on its own filled shape (a section tab or a step disc carries an ordinal, not a page).
"""
from __future__ import annotations

import re
import sys

from _shared import FAIL, NOTE, Finding, bx, cli, has_text, is_filled, is_lined, text_of, words
from deckkit.read.deckinfo import CONFIDENTIAL

GATE, TITLE = "P09", "chrome"
COVER_LABEL_WORDS = 12   # a label line under a cover title (parties, engagement, date), never a sentence
FOOT_Y, BAND_Y, BAND_W, CARD_W = 6.30 / 7.5, 6.20 / 7.5, 8.0 / 13.333, 6.5 / 13.333
LOGO_Y = 0.90
FOOT_WORDS = 5
PAGE_LABEL = re.compile(r"^(?:A[1-9]|appendix\s+\d{1,3}|\d{1,3}\s*/\s*\d{1,3})$", re.I)
PAGE_BAND = 0.15          # the top or bottom share of the canvas height
PAGE_SIDE = 0.25          # the outer share of the canvas width on either side
PAGE_MID = 0.10           # ... or centred on the canvas, within this share of its width
PAGE_MAX_PT = 14.0


def page_label(L, t: str, W: float, H: float) -> bool:
    """A page label ('A1'..'A9', 'Appendix N', 'N / M') in a page-number position (see the module notes)."""
    if not PAGE_LABEL.match(t) or (L.get("fill") or {}).get("type") not in (None, "none"):
        return False
    size = ((L.get("text") or {}).get("size") or {}).get("dominant_pt") or 0.0
    if size > PAGE_MAX_PT:
        return False
    x0, y0, x1, y1 = bx(L)
    if not (y0 >= (1 - PAGE_BAND) * H or y1 <= PAGE_BAND * H):
        return False
    return x0 >= (1 - PAGE_SIDE) * W or x1 <= PAGE_SIDE * W or abs((x0 + x1) / 2 - W / 2) <= PAGE_MID * W


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
        cover = ctx.tags()[i - 1]["archetype"] == "cover"
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
            elif has_text(L) and page_label(L, t, W, H):
                out.append(Finding(GATE, FAIL, i, L["name"], "page label %r in a page-number position" % t))
            if t and CONFIDENTIAL.search(t):
                out.append(Finding(GATE, FAIL, i, L["name"], "confidentiality line %r" % t[:50]))
            if L["kind"] == "sp" and not foot_ok and (is_filled(L) or is_lined(L)) and b[2] - b[0] >= BAND_W * W \
                    and b[1] >= BAND_Y * H and b[3] - b[1] > 0.05 * k:
                out.append(Finding(GATE, FAIL, i, L["name"], "foot band %.1fin wide at %.2fin" % (b[2] - b[0], b[1])))
            elif L["kind"] == "sp" and not foot_ok and (is_filled(L) or is_lined(L)) and b[2] - b[0] >= BAND_W * W \
                    and b[3] >= (1 - PAGE_BAND) * H and b[3] - b[1] <= 1.0 * k:
                # a summary or next-step band whose top sits above BAND_Y: one sentence across most of the band
                for T in shapes:
                    if T is L or not has_text(T):
                        continue
                    tb = bx(T)
                    tt = " ".join(text_of(T).split())
                    if (tb[0] >= b[0] - 0.05 and tb[2] <= b[2] + 0.05 and tb[1] >= b[1] - 0.05 and tb[3] <= b[3] + 0.05
                            and words(tt) >= FOOT_WORDS and (tb[2] - tb[0]) >= 0.5 * (b[2] - b[0])):
                        out.append(Finding(GATE, FAIL, i, L["name"], "foot band carrying a sentence at %.2fin: %r"
                                           % (b[1], tt[:50])))
                        break
            if L["kind"] == "pic" and b[1] >= LOGO_Y * H:
                out.append(Finding(GATE, FAIL, i, L["name"], "picture in the foot (a footer logo) at %.2fin" % b[1]))
            if not has_text(L):
                continue
            if not foot_ok and b[1] >= FOOT_Y * H and words(t) >= FOOT_WORDS and L["kind"] != "cell":
                narrow = [c for c, CL in boxes if CL is not L and (c[2] - c[0]) < CARD_W * W and _inside(b, c)]
                if not narrow:
                    out.append(Finding(GATE, FAIL, i, L["name"], "foot sentence at %.2fin: %r" % (b[1], t[:50])))
            if role == "subtitle" and cover and words(t) <= COVER_LABEL_WORDS:
                continue                       # a cover's party, engagement and date lines are its label stack
            if role == "subtitle" and not sub_ok and t != t.upper():
                cy = (b[1] + b[3]) / 2
                on_fill = any(c[1] <= cy <= c[3] and b[0] >= c[0] - 0.15 and b[2] <= c[2] + 0.15
                              for c, CL in boxes if CL is not L and is_filled(CL))
                if not on_fill:
                    out.append(Finding(GATE, FAIL, i, L["name"], "subtitle under the title: %r" % t[:50]))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
