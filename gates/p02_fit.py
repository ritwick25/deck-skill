"""P02 fit: every text box's measured height fits its box (deckkit.measure, SLACK 1.15, tolerance 0.035in x k).

Each paragraph is rebuilt from the read layer's effective runs (each run measured with its own cut:
Arial Bold for bold, and so on) and wrapped at the text rectangle of the shape's preset minus its insets
and the paragraph's left margin, at SLACK 1.15 because PowerPoint sets text wider than LibreOffice
renders it. SLACK is this gate's own constant, never read from the measurer, so a build that patched the
measurer cannot pass its own check.
"""
from __future__ import annotations

import sys

from _shared import ADVISORY, FAIL, Finding, cli, has_text, need_in
from deckkit.errors import UnknownFace

GATE, TITLE = "P02", "fit"
SLACK = 1.15
TOL_IN = 0.035


def run(deck, ctx):
    out = []
    tol = TOL_IN * ctx.k
    for i in range(1, ctx.n + 1):
        for L in ctx.slide(i)["shapes"]:
            if not has_text(L):
                continue
            body = L["text"]["body"]
            if body.get("vert") not in (None, "horz"):
                out.append(Finding(GATE, ADVISORY, i, L["name"], "vertical text (%s) not measured" % body["vert"]))
                continue
            try:
                need, have, lines = need_in(ctx, i, L, SLACK)
            except UnknownFace as e:
                out.append(Finding(GATE, FAIL, i, L["name"], "cannot measure: %s" % e))
                continue
            if need > have + tol:
                out.append(Finding(GATE, FAIL, i, L["name"], "needs %.3fin, has %.3fin (%d lines at SLACK %.2f): %r"
                                   % (need, have, lines, SLACK, L["text"]["text"][:40])))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
