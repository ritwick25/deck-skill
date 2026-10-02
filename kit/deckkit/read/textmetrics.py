"""Paragraph text and word counting. THE ONLY TOKENIZER in the system.

A word is a whitespace token containing a letter or digit, counted on paragraph-joined text: runs and
fields are re-joined before tokenising, so a mid-word run split ("L" + "eader") counts once.
The corpus pipeline, the extractor and the skill's budget gate all import this module.
"""
from __future__ import annotations

import re

from .ns import A, local

TOKEN = re.compile(r"\S+")
_ALNUM = re.compile(r"[^\W_]", re.UNICODE)   # any letter or digit, any script


def para_text(p) -> str:
    """a:p element to its text: a:r and a:fld text joined, a:br as a newline."""
    out = []
    for n in p:
        t = local(n)
        if t in ("r", "fld"):
            tt = n.find(A("t"))
            out.append((tt.text or "") if tt is not None else "")
        elif t == "br":
            out.append("\n")
    return "".join(out)


def tokens(text: str) -> list[str]:
    return [w for w in TOKEN.findall(text or "") if _ALNUM.search(w)]


def words(text: str) -> int:
    """Whitespace tokens that contain a letter or digit."""
    return sum(1 for w in TOKEN.findall(text or "") if _ALNUM.search(w))


def token_spans(text: str) -> list[tuple[int, int]]:
    """(start, end) character spans of the counted tokens, for attributing words to runs."""
    return [(m.start(), m.end()) for m in TOKEN.finditer(text or "") if _ALNUM.search(m.group())]
