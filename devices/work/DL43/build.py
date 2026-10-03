"""DL43: a five-row reference table (glyph tile, dimension and definition, what it is measured from) under two
brand header pills, beside a cluster map: the same five dimensions as near-black nodes, each dropping one arrow into
the bubble of suppliers it flags, with unflagged suppliers loose around them (reference-table)."""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import prims  # noqa: E402
from deckkit import text as txt  # noqa: E402
from deckkit.canvas import Box  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL43")
VARIANT = "coded-rows-cluster-map"


def flatten():
    """Every group into slide space, so moved children never sit under a stale group frame."""
    tree = s.shapes._spTree
    while True:
        g = next((e for e in tree if e.tag == qn("p:grpSp")), None)
        if g is None:
            return
        xf = g.find(qn("p:grpSpPr") + "/" + qn("a:xfrm"))
        off, ext, cho, che = (xf.find(qn("a:" + t)) for t in ("off", "ext", "chOff", "chExt"))
        sx = int(ext.get("cx")) / max(int(che.get("cx")), 1)
        sy = int(ext.get("cy")) / max(int(che.get("cy")), 1)
        for c in list(g):
            if c.tag in (qn("p:nvGrpSpPr"), qn("p:grpSpPr")):
                continue
            cx = c.find("./*/" + qn("a:xfrm"))
            o, e = cx.find(qn("a:off")), cx.find(qn("a:ext"))
            o.set("x", str(round(int(off.get("x")) + (int(o.get("x")) - int(cho.get("x"))) * sx)))
            o.set("y", str(round(int(off.get("y")) + (int(o.get("y")) - int(cho.get("y"))) * sy)))
            e.set("cx", str(round(int(e.get("cx")) * sx)))
            e.set("cy", str(round(int(e.get("cy")) * sy)))
            g.addprevious(c)
        tree.remove(g)


flatten()

# chrome the house rules ban: the caps kicker over the title, the white frame nesting the row cards, the page
# number, the italic reading note under the map. The reference's cluster map (about 170 micro shapes: member
# edges, rings, scattered dots, dashed drops, floating labels that collide with the bubbles) is redrawn below in
# the kit's own primitives on a measured grid.
KEEP = {"dev.3", "dev.193", "dev.200", "dev.201"} | {"dev.%d" % n for n in range(5, 30)}
for sh in list(s.shapes):
    if sh.name not in KEEP:
        delete(s, sh.name)


def radius(name, r=0.06):
    sh = find(s, name)
    gd = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst") + "/" + qn("a:gd"))
    if gd is not None:
        gd.set("fmla", "val %d" % round(r / (min(sh.width, sh.height) / EMU) * 100000))


def zero_insets(name, l=0, r=0):
    bp = find(s, name)._element.find(".//" + qn("a:bodyPr"))
    bp.set("lIns", str(int(l * EMU)))
    bp.set("rIns", str(int(r * EMU)))
    bp.set("tIns", "0")
    bp.set("bIns", "0")


# title at the kit's wide title geometry, 21pt, one line
rename(s, "dev.3", "slot.title")
move(s, "slot.title", 0.50, 0.13, 12.40, 0.40)
zero_insets("slot.title")
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "Five scored dimensions make every supplier's risk comparable at a glance", ("Five scored dimensions",))))],
    th, size=21, bold=True, anchor="middle")

# header pills: solid brand (ruling 12), one per column of the table and one over the map
PILL_Y, PILL_H = 0.95, 0.40
L0, L1 = 0.50, 7.40                       # the table
TX, TW = 1.48, 3.42                       # dimension and definition column
SX, SW = 5.02, 2.24                       # source and flag-rule column
R0, R1 = 7.70, 12.90                      # the map
for old, new, x, w, label in (("dev.193", "slot.head.dimension", TX, TW, "Dimension and definition"),
                              ("dev.200", "slot.head.source", SX, SW, "Source and flag rule")):
    rename(s, old, new)
    move(s, new, x, PILL_Y, w, PILL_H)
    text(s, new, [txt.Para((txt.Run(label, "on-accent", bold=True, size=12),), align="center")], th, size=12,
         background="accent", anchor="middle")

rename(s, "dev.201", "struct.head.map")
move(s, "struct.head.map", R0, PILL_Y, R1 - R0, PILL_H)
find(s, "struct.head.map").text_frame.text = ""
txt.textbox(s, Box(R0 + 0.20, PILL_Y + 0.06, R1 - R0 - 0.40, PILL_H - 0.12),
            [txt.Para((txt.Run("Suppliers grouped by their weakest dimension", "on-accent", bold=True, size=12),),
                      align="center")], "slot.head.map", th, background="accent", anchor="middle")

ROWS = [  # (card, tile, head, body, source, glyph, head text, body text, source, flag rule)
    ("dev.5", "dev.6", "dev.7", "dev.8", "dev.9", "truck", "Delivery reliability",
     "Order lines that arrive complete and inside the agreed delivery window", "Goods receipts", "Two late months in a row"),
    ("dev.10", "dev.11", "dev.12", "dev.13", "dev.14", "clipboard-check", "Quality conformance",
     "Lots rejected or reworked at inspection against all lots received", "Inspection results", "Any lot rejected twice"),
    ("dev.15", "dev.16", "dev.17", "dev.18", "dev.19", "landmark", "Financial health",
     "Credit and payment signals that warn of supplier distress months early", "Payment records", "Any credit downgrade"),
    ("dev.20", "dev.21", "dev.22", "dev.23", "dev.24", "shield-check", "Compliance standing",
     "Open audit findings, lapsed certificates and overdue corrective actions", "Audit register", "Findings past due date"),
    ("dev.25", "dev.26", "dev.27", "dev.28", "dev.29", "factory", "Capacity headroom",
     "Committed volume against the plant capacity each supplier has declared", "Capacity plans", "Commitments over capacity"),
]
ROW_Y, ROW_H, ROW_GAP = 1.47, 0.99, 0.1025
TILE = 0.62
for i, (card, tile, head, body, src, g, h, b, so, rule) in enumerate(ROWS, 1):
    y = ROW_Y + (i - 1) * (ROW_H + ROW_GAP)
    rename(s, card, "struct.row.%d" % i)
    move(s, "struct.row.%d" % i, L0, y, L1 - L0, ROW_H)
    prims.set_fill(find(s, "struct.row.%d" % i), "card", theme=th)
    prims.set_line(find(s, "struct.row.%d" % i), "hairline", 0.75, theme=th)
    radius("struct.row.%d" % i)
    rename(s, tile, "struct.row.%d.tile" % i)
    move(s, "struct.row.%d.tile" % i, 0.68, y + (ROW_H - TILE) / 2, TILE, TILE)
    prims.set_fill(find(s, "struct.row.%d.tile" % i), "accent", theme=th)
    radius("struct.row.%d.tile" % i, 0.08)
    icon(s, "slot.row.%d.icon" % i, g, 0.68 + 0.14, y + (ROW_H - TILE) / 2 + 0.14, 0.34, th, role="on-accent")
    rename(s, head, "slot.row.%d.head" % i)
    move(s, "slot.row.%d.head" % i, TX, y + 0.11, TW, 0.30)
    zero_insets("slot.row.%d.head" % i)
    text(s, "slot.row.%d.head" % i, h, th, size=14, bold=True, role="ink-deep", background="card")
    rename(s, body, "slot.row.%d.body" % i)
    move(s, "slot.row.%d.body" % i, TX, y + 0.43, TW, 0.46)
    zero_insets("slot.row.%d.body" % i)
    text(s, "slot.row.%d.body" % i, b, th, size=11, bold=False, role="ink", background="card")
    rename(s, src, "slot.row.%d.source" % i)
    move(s, "slot.row.%d.source" % i, SX, y + 0.12, SW - 0.14, ROW_H - 0.24)
    zero_insets("slot.row.%d.source" % i)
    text(s, "slot.row.%d.source" % i, [txt.Para((txt.Run(so, "accent-ink", bold=True, size=12),), align="right"),
                                        txt.Para((txt.Run(rule, "ink", size=11),), align="right", space_before=3)],
         th, size=12, background="card", anchor="middle")

# the cluster map: five near-black dimension nodes, each with its row's glyph; one arrow from each node lands on
# the bubble of suppliers whose weakest dimension it is; bubbles stagger on two rows so every drop runs straight
NODE, BUB = 0.46, 1.30
XS = [R0 + BUB / 2 + k * (R1 - R0 - BUB) / 4 for k in range(5)]
LAB_Y, NODE_Y = 1.50, 1.80
BUB_Y = [2.62, 4.42, 2.62, 4.42, 2.62]                         # bubble tops: upper, lower, upper, lower, upper
NAMES = ["Delivery", "Quality", "Finance", "Compliance", "Capacity"]
MEMBERS = [  # supplier dots inside each bubble, offsets from its centre in inches
    [(-0.30, -0.22), (0.02, -0.34), (0.30, -0.16), (-0.12, 0.00), (0.18, 0.12), (-0.34, 0.20), (0.02, 0.32)],
    [(-0.22, -0.20), (0.20, -0.24), (-0.04, 0.10), (0.28, 0.20)],
    [(-0.20, -0.14), (0.18, -0.06), (-0.02, 0.24)],
    [(-0.28, -0.16), (0.06, -0.30), (0.30, 0.00), (-0.16, 0.18), (0.14, 0.28), (-0.02, -0.04)],
    [(-0.24, -0.24), (0.16, -0.26), (0.30, 0.10), (-0.30, 0.12), (0.02, 0.30)],
]
DOT = 0.12
for i, (cx, top, nm, mem) in enumerate(zip(XS, BUB_Y, NAMES, MEMBERS), 1):
    g = ROWS[i - 1][5]
    txt.textbox(s, Box(cx - 0.55, LAB_Y, 1.10, 0.24),
                [txt.Para((txt.Run(nm, "ink-deep", bold=True, size=12),), align="center")],
                "slot.node.%d.label" % i, th, background="paper")
    prims.circle(s, Box(cx - NODE / 2, NODE_Y, NODE, NODE), fill="ink-deep", name="struct.node.%d" % i, theme=th)
    icon(s, "slot.node.%d.icon" % i, g, cx - 0.13, NODE_Y + NODE / 2 - 0.13, 0.26, th, role="paper")
    prims.circle(s, Box(cx - BUB / 2, top, BUB, BUB), fill="accent", name="struct.cluster.%d" % i, theme=th)
    prims.connect(s, (cx, NODE_Y + NODE), (cx, top), head="end", role="ink-muted", weight_pt=1.0,
                  name="struct.cluster.%d.drop" % i, theme=th)
    ccy = top + BUB / 2
    for j, (dx, dy) in enumerate(mem, 1):
        prims.circle(s, Box(cx + dx - DOT / 2, ccy + dy - DOT / 2, DOT, DOT), fill="paper",
                     name="struct.cluster.%d.member.%d" % (i, j), theme=th)

# suppliers below threshold on no dimension, loose in the free ground between and under the bubbles
LOOSE = [(XS[0] + 0.05, 4.55), (XS[0] - 0.40, 5.15), (XS[0] + 0.30, 5.55), (XS[2], 4.62), (XS[2] - 0.16, 5.42),
         (XS[2] + 0.30, 5.62), (XS[4] - 0.05, 4.60), (XS[4] + 0.35, 5.20), (XS[4] - 0.30, 5.58),
         ((XS[0] + XS[1]) / 2, 6.00), ((XS[2] + XS[3]) / 2, 6.04)]
for k, (x, y) in enumerate(LOOSE, 1):
    prims.circle(s, Box(x - DOT / 2, y - DOT / 2, DOT, DOT), fill="card",
                 line="rule-strong", name="struct.loose.%d" % k, theme=th)

# legend: mark plus short label (deck grammar, not a reading instruction)
LEG_Y = 6.44
prims.circle(s, Box(R0 + 0.02, LEG_Y + 0.02, 0.24, 0.24), fill="accent", name="struct.legend.cluster", theme=th)
prims.circle(s, Box(R0 + 0.08, LEG_Y + 0.08, DOT, DOT), fill="paper", name="struct.legend.cluster.member", theme=th)
txt.textbox(s, Box(R0 + 0.36, LEG_Y, 2.30, 0.28), [txt.Para((txt.Run("Supplier below threshold", "ink", size=11),))],
            "slot.legend.flagged", th, background="paper")
prims.circle(s, Box(R0 + 2.80, LEG_Y + 0.08, DOT, DOT), fill="card", line="rule-strong",
             name="struct.legend.loose", theme=th)
txt.textbox(s, Box(R0 + 3.02, LEG_Y, 2.18, 0.28), [txt.Para((txt.Run("Clear on all five", "ink", size=11),))],
            "slot.legend.clear", th, background="paper")

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
out = save(prs, "DL43", th, archetype="reference-table", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
