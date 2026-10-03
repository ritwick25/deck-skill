"""P05 overlap: no two drawn, non-nested boxes overlap by more than 0.10 x 0.10in (x k).

Nested is fine (text on its card, an icon inside its tile): one box wholly inside the other, within
0.02in. Lines and connectors are not boxes. Table cells tile by construction. A chevron row nests each
step's point into the next step's notch on purpose, so two chevron-family presets are not compared when they
share one parent group (the row the kit draws as one group). Two chevrons both loose on the slide nest only when
they read as one row: the same top and height (within 0.02in) and an overlap no deeper than the point
(height x adj, 0.5 by default). A chevron in a group and one outside it are compared like any other boxes.

Text is judged by what the eye sees: a text block that draws no fill and no outline is its ink box
(deckkit.read.walk._text_box, occupancy-trimmed and aligned, through _shared.ink_box), so two frames that cross
while their words do not are not an overlap. Anything that draws keeps its frame, and nesting is judged on the
same boxes.
"""
from __future__ import annotations

import sys

from _shared import FAIL, Finding, box_contains, cli, full_bleed, ink_box, is_drawn

GATE, TITLE = "P05", "overlap"
MIN_IN = 0.10
NEST = ("chevron", "homePlate", "notchedRightArrow")
ROW_EPS = 0.02


def _loose_row(a, ab, b, bb) -> bool:
    """Two loose chevron-family shapes drawn as one row: same top and height, nested no deeper than the point."""
    if abs(ab[1] - bb[1]) > ROW_EPS or abs((ab[3] - ab[1]) - (bb[3] - bb[1])) > ROW_EPS:
        return False
    depth = max(((L.get("geom") or {}).get("adj") or {}).get("adj", 50000) / 1e5 * (box[3] - box[1])
                for L, box in ((a, ab), (b, bb)))
    return min(ab[2], bb[2]) - max(ab[0], bb[0]) <= depth + ROW_EPS


def run(deck, ctx):
    out = []
    m = MIN_IN * ctx.k
    for i in range(1, ctx.n + 1):
        boxes = [L for L in ctx.slide(i)["shapes"]
                 if L["kind"] in ("sp", "pic", "graphic") and not L.get("line_like") and is_drawn(L)
                 and not full_bleed(L, ctx) and not L["name"].startswith("bleed.")]
        seen = [(L, ink_box(L)) for L in boxes]
        for a_i, (a, ab) in enumerate(seen):
            ax0, ay0, ax1, ay1 = ab
            for b, bb in seen[a_i + 1:]:
                bx0, by0, bx1, by1 = bb
                ow, oh = min(ax1, bx1) - max(ax0, bx0), min(ay1, by1) - max(ay0, by0)
                if ow <= m or oh <= m:
                    continue
                if box_contains(ab, bb) or box_contains(bb, ab):
                    continue
                pa, pb = (a.get("geom") or {}).get("prst"), (b.get("geom") or {}).get("prst")
                if pa in NEST and pb in NEST and a["group_path"] and a["group_path"][-1:] == b["group_path"][-1:]:
                    continue                            # one chevron row, nested by design
                if pa in NEST and pb in NEST and not a["group_path"] and not b["group_path"] and \
                        _loose_row(a, ab, b, bb):
                    continue                            # a loose chevron row on the slide
                out.append(Finding(GATE, FAIL, i, "%s / %s" % (a["name"] or a["id"], b["name"] or b["id"]),
                                   "overlap %.2f x %.2fin" % (ow, oh)))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
