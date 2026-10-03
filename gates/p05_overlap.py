"""P05 overlap: no two drawn, non-nested boxes overlap by more than 0.10 x 0.10in (x k).

Nested is fine (text on its card, an icon inside its tile): one box wholly inside the other, within
0.02in. Lines and connectors are not boxes. Table cells tile by construction. A chevron row nests each
step's point into the next step's notch on purpose, so two chevron-family presets are not compared when they
share one parent group (the row the kit draws as one group); chevrons from different groups, or loose on the
slide, are compared like any other boxes.
"""
from __future__ import annotations

import sys

from _shared import FAIL, Finding, bx, cli, contains, full_bleed, is_drawn

GATE, TITLE = "P05", "overlap"
MIN_IN = 0.10
NEST = ("chevron", "homePlate", "notchedRightArrow")


def run(deck, ctx):
    out = []
    m = MIN_IN * ctx.k
    for i in range(1, ctx.n + 1):
        boxes = [L for L in ctx.slide(i)["shapes"]
                 if L["kind"] in ("sp", "pic", "graphic") and not L.get("line_like") and is_drawn(L)
                 and not full_bleed(L, ctx) and not L["name"].startswith("bleed.")]
        for a_i, a in enumerate(boxes):
            ax0, ay0, ax1, ay1 = bx(a)
            for b in boxes[a_i + 1:]:
                bx0, by0, bx1, by1 = bx(b)
                ow, oh = min(ax1, bx1) - max(ax0, bx0), min(ay1, by1) - max(ay0, by0)
                if ow <= m or oh <= m:
                    continue
                if contains(a, b) or contains(b, a):
                    continue
                pa, pb = (a.get("geom") or {}).get("prst"), (b.get("geom") or {}).get("prst")
                if pa in NEST and pb in NEST and a["group_path"] and a["group_path"][-1:] == b["group_path"][-1:]:
                    continue                            # one chevron row, nested by design
                out.append(Finding(GATE, FAIL, i, "%s / %s" % (a["name"] or a["id"], b["name"] or b["id"]),
                                   "overlap %.2f x %.2fin" % (ow, oh)))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
