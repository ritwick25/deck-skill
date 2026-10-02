"""P01 floor: every run's effective size (sz x normAutofit fontScale) is at least 8.0pt, explicit sz on every run.

Every run is read through deckkit.read, so group children, table cells and master or layout chrome are
all included, and the size is the one the renderer draws (the inheritance chain resolved, fontScale
applied). A run with no sz of its own inherits from a chain the kit never relies on: it fails too.
"""
from __future__ import annotations

import sys

from _shared import FAIL, Finding, cli

GATE, TITLE = "P01", "floor"
FLOOR = 8.0


def run(deck, ctx):
    out = []
    for i in range(1, ctx.n + 1):
        s = ctx.slide(i)
        for L in s["shapes"] + s["chrome"]:
            tx = L.get("text")
            if not tx:
                continue
            for p in tx["paragraphs"]:
                for r in p["runs"]:
                    if not r["t"].strip():
                        continue
                    eff = r["size_rendered_pt"]
                    if eff < FLOOR - 1e-9:
                        scale = tx["body"].get("font_scale") or 1.0
                        how = " (%.1fpt at fontScale %d%%)" % (r["size_pt"], round(scale * 100)) if scale < 1 else ""
                        out.append(Finding(GATE, FAIL, i, L["name"], "%.2fpt run%s: %r" % (eff, how, r["t"][:40])))
                    if r["size_src"] != "run":
                        out.append(Finding(GATE, FAIL, i, L["name"], "run with no explicit sz (inherits %.1fpt via %s): %r"
                                           % (r["size_pt"], r["size_src"], r["t"][:40])))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
