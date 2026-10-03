"""P02 fit: every text box's measured height fits its box (deckkit.measure, SLACK 1.15, tolerance 0.035in x k).

Each paragraph is rebuilt from the read layer's effective runs (each run measured with its own cut:
Arial Bold for bold, and so on) and wrapped at the text rectangle of the shape's preset minus its insets
and the paragraph's left margin, at SLACK 1.15 because PowerPoint sets text wider than LibreOffice
renders it. SLACK is this gate's own constant, never read from the measurer, so a build that patched the
measurer cannot pass its own check.

Every shape is checked on its own: a face with no metrics is a FAIL on that shape naming the face, and the
shape is still measured, in Arial of the same cut, with the fallback named on any overflow it shows. A shape or
slide that cannot be read at all is a FAIL on it, and the gate goes on with the rest.
"""
from __future__ import annotations

import sys

from _shared import ADVISORY, FAIL, FALLBACK_FACE, Finding, cli, crash, has_text, need_in
from deckkit.errors import Overflows

GATE, TITLE = "P02", "fit"
SLACK = 1.15
TOL_IN = 0.035


def check(ctx, i, L, tol) -> list[Finding]:
    body = L["text"]["body"]
    if body.get("vert") not in (None, "horz"):
        return [Finding(GATE, ADVISORY, i, L["name"], "vertical text (%s) not measured" % body["vert"])]
    unknown: list = []
    try:
        need, have, lines = need_in(ctx, i, L, SLACK, unknown)
    except Overflows as e:      # one word is wider than the line: it cannot fit at any height
        need = None
        wide = str(e).split(". ")[0]
    out = [Finding(GATE, FAIL, i, L["name"], "face %r has no metrics; measured as %s (a labelled fallback)"
                   % (f, FALLBACK_FACE)) for f in unknown]
    if need is None:
        out.append(Finding(GATE, FAIL, i, L["name"], "a word is wider than its line at SLACK %.2f%s: %s"
                           % (SLACK, ", measured as %s" % FALLBACK_FACE if unknown else "", wide)))
        return out
    if need > have + tol:
        out.append(Finding(GATE, FAIL, i, L["name"], "needs %.3fin, has %.3fin (%d lines at SLACK %.2f%s): %r"
                           % (need, have, lines, SLACK, ", measured as %s" % FALLBACK_FACE if unknown else "",
                              L["text"]["text"][:40])))
    return out


def run(deck, ctx):
    out = []
    tol = TOL_IN * ctx.k
    for i in range(1, ctx.n + 1):
        try:
            shapes = ctx.slide(i)["shapes"]
        except Exception as e:  # one unreadable slide never aborts the gate
            out.append(crash(GATE, i, "slide", e))
            continue
        for L in shapes:
            if not has_text(L):
                continue
            try:
                out.extend(check(ctx, i, L, tol))
            except Exception as e:  # one bad shape never aborts the gate
                out.append(crash(GATE, i, L.get("name") or "id %s" % L.get("id"), e))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
