"""Figures on glass: which texts state a quantity, which only count or label, and which are set large.

A figure is a text whose whole content is one quantity or one range of quantities:
  * a number, optionally signed or approximate (~ < > + -), with an optional currency before it ($, EUR, USD,
    GBP and the currency signs) or after it (EUR, USD), and an optional unit after it: %, x, k, K, M, mn, bn, B,
    pp, pts, bps, or a trailing +;
  * a range of two of them joined by "to", a hyphen, an en dash or "vs" ("5 to 10%", "+6 to 7%", "$2-4M").
A text that is not a figure: an ordinal or label, never a quantity:
  * a number written with a leading zero ("01", "07", "012": a list or section ordinal);
  * a bare year (1900 to 2099);
  * a single bare digit painted inside a disc or step marker (its own filled shape, or a filled shape of
    MARKER_MAX_IN or less on a side that holds it);
  * any bare number on a divider (a section numeral).
large_figures() returns the figures a slide sets at LARGE times its median text size or larger.
"""
from __future__ import annotations

import re
import statistics

LARGE = 1.4                 # a figure set at this many times the slide's median text size is a stat
MARKER_MAX_IN = 0.8         # a disc or step marker is a filled shape no larger than this on a side
_CUR = r"(?:[$€£₹¥]|(?:US|EUR|USD|GBP|INR)\s?)"
_UNIT = r"(?:%|x|\u00d7|[kK]|M|mn|bn|B|pp|pts?|bps|\+|\s?(?:EUR|USD))"
_NUM = r"[~<>+\-\u2212]?" + _CUR + r"?\d[\d.,]*" + _UNIT + r"?"
FIGURE = re.compile(r"^" + _NUM + r"(?:\s?(?:to|-|\u2013|vs\.?)\s?" + _NUM + r")?$")     # \u2013: en dash
BARE = re.compile(r"^\d[\d.,]*$")
ORDINAL = re.compile(r"^0\d{1,2}$")
YEAR = re.compile(r"^(?:19|20)\d\d$")


def norm(text: str) -> str:
    return " ".join((text or "").split())


def is_figure(text: str) -> bool:
    """The whole text is one quantity or one range of quantities, and not an ordinal or a year."""
    t = norm(text)
    return bool(t) and bool(FIGURE.match(t)) and not ORDINAL.match(t) and not YEAR.match(t)


def _filled(L) -> bool:
    return ((L.get("fill") or {}).get("type") or "none") not in ("none", None)


def _marker(L, leaves) -> bool:
    """L sits in a disc or step marker: it is a small filled shape itself, or a small filled shape holds it."""
    def small(M):
        b = M["bbox"]
        return b["w_in"] <= MARKER_MAX_IN and b["h_in"] <= MARKER_MAX_IN
    if _filled(L) and small(L):
        return True
    lb = L["bbox"]
    cx, cy = lb["x_in"] + lb["w_in"] / 2.0, lb["y_in"] + lb["h_in"] / 2.0
    for M in leaves:
        if M is L or not _filled(M) or not small(M) or M.get("line_like"):
            continue
        b = M["bbox"]
        if b["x_in"] <= cx <= b["x_in"] + b["w_in"] and b["y_in"] <= cy <= b["y_in"] + b["h_in"]:
            return True
    return False


def large_figures(slide: dict, divider: bool = False) -> list[tuple[dict, float]]:
    """[(leaf, size / median)] for every text leaf on the slide's content layer whose text is a figure set at
    LARGE times the slide's median text size or larger. Ordinals, years, single digits in markers and, on a
    divider, every bare number are skipped."""
    leaves = slide["shapes"]
    texts = [L for L in leaves if L.get("text") and norm(L["text"]["text"]) and L["text"].get("size")]
    if not texts:
        return []
    med = statistics.median(L["text"]["size"]["dominant_pt"] for L in texts)
    out = []
    for L in texts:
        t = norm(L["text"]["text"])
        if not is_figure(t):
            continue
        bare = bool(BARE.match(t))
        if bare and divider:
            continue
        if bare and len(t) == 1 and _marker(L, leaves):
            continue
        r = L["text"]["size"]["dominant_pt"] / med if med else 0.0
        if r >= LARGE:
            out.append((L, round(r, 2)))
    return out


__all__ = ["LARGE", "FIGURE", "is_figure", "large_figures"]
