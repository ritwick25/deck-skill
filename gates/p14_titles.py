"""P14 titles: every slide has a title that fits its canvas lines, has 14 words or fewer, and keeps the two-tone rule.

  * the title is the shape named "title" (the kit's name), else the read layer's title role;
  * it wraps to no more than the canvas's title_max_lines at SLACK 1.15, and has at most 14 words;
  * no more than two titles share their opening two words;
  * two-tone keywords (runs in the accent-ink role) are one to three spans, and only in titles: a body
    paragraph mixing accent-ink runs with other runs is a two-tone keyword outside a title.
"""
from __future__ import annotations

import sys
from collections import defaultdict

from _shared import FAIL, Finding, cli, has_text, need_in, words
from deckkit.read.refnorm import shingle_tokens

GATE, TITLE = "P14", "titles"
MAX_WORDS, MAX_KEYWORDS, MAX_SHARE = 14, 3, 2


def _title(s):
    for L in s["shapes"]:
        if L["name"] == "title" and has_text(L):
            return L
    return next((L for L in s["shapes"] if (L.get("role_guess") or {}).get("role") == "title" and has_text(L)), None)


def _spans(p, ink):
    """Count runs of consecutive accent-ink text (blank runs neither open nor close a span)."""
    n, inside = 0, False
    for r in p["runs"]:
        if not r["t"].strip():
            continue
        on = r["hex"] == ink
        if on and not inside:
            n += 1
        inside = on
    return n


def run(deck, ctx):
    out = []
    ink = ctx.theme.hex("accent-ink")
    openers = defaultdict(list)
    for i in range(1, ctx.n + 1):
        s = ctx.slide(i)
        T = _title(s)
        if T is None:
            out.append(Finding(GATE, FAIL, i, "", "no title"))
        else:
            text = " ".join(T["text"]["text"].split())
            n = words(text)
            if n > MAX_WORDS:
                out.append(Finding(GATE, FAIL, i, T["name"], "%d words in the title (max %d)" % (n, MAX_WORDS)))
            _need, _have, lines = need_in(ctx, i, T, 1.15)
            if lines > ctx.canvas.title_max_lines:
                out.append(Finding(GATE, FAIL, i, T["name"], "title wraps to %d lines (the %s canvas holds %d)"
                                   % (lines, ctx.canvas.name, ctx.canvas.title_max_lines)))
            kw = sum(_spans(p, ink) for p in T["text"]["paragraphs"])
            if kw > MAX_KEYWORDS:
                out.append(Finding(GATE, FAIL, i, T["name"], "%d two-tone keywords (max %d)" % (kw, MAX_KEYWORDS)))
            toks = shingle_tokens(text)
            if len(toks) >= 2:
                openers[" ".join(toks[:2])].append(i)
        for L in s["shapes"]:
            if L is T or not has_text(L):
                continue
            for p in L["text"]["paragraphs"]:
                runs = [r for r in p["runs"] if r["t"].strip()]
                if any(r["hex"] == ink for r in runs) and any(r["hex"] != ink for r in runs):
                    out.append(Finding(GATE, FAIL, i, L["name"], "two-tone keyword outside a title: %r" % p["text"][:40]))
                    break
    for op, sl in openers.items():
        if len(sl) > MAX_SHARE:
            out.append(Finding(GATE, FAIL, None, "", "%d titles open with %r (slides %s; max %d)"
                               % (len(sl), op, ", ".join(map(str, sl)), MAX_SHARE)))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
