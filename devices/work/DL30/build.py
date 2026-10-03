"""DL30: two source groups feed three ingestion lanes, every lane converges on one ring that holds the shared
stores around a core, and a mosaic of domains and their use cases is served off the ring's far side
(convergence-hub)."""
import argparse
import copy
import math
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import prims, text as txt  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL30")
VARIANT = "lanes-into-ring-mosaic-readout"
R, P = txt.Run, txt.Para
RADIUS = 0.05                                     # the wide canvas card radius


def zero_ins(name):
    bp = find(s, name)._element.find(".//" + qn("a:bodyPr"))
    for k in ("lIns", "tIns", "rIns", "bIns"):
        bp.set(k, "0")


def to_front(name):
    el = find(s, name)._element
    el.getparent().remove(el)
    s.shapes._spTree.append(el)


def set_radius(name):
    sh = find(s, name)
    av = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst"))
    gd = av.find(qn("a:gd"))
    if gd is None:
        gd = av.makeelement(qn("a:gd"), {})
        av.append(gd)
    v = int(round(min(0.5, RADIUS / min(sh.width / EMU, sh.height / EMU)) * 100000))
    gd.set("name", "adj")
    gd.set("fmla", "val %d" % v)


# banned or decorative: the binary column, duplicate header texts, vertical letter-stacked kickers, spare
# second-line labels, the inner arrow of the stream lane, the elbow between lanes (each lane now converges on the
# ring itself), the old lane exits and the hub's floating arrow pairs (each store is wired to the core instead)
for n in ["dev.4", "dev.8", "dev.13", "dev.38", "dev.39", "dev.17", "dev.43", "dev.44", "dev.37",
          "dev.47", "dev.48", "dev.49", "dev.50", "dev.90", "dev.65"] + ["dev.%d" % i for i in range(72, 90)]:
    delete(s, n)

# title: one claim, two-tone
rename(s, "dev.2", "slot.title")
move(s, "slot.title", 0.37, 0.28, 12.56, 0.80)
text(s, "slot.title", [P(tuple(txt.title_runs(
    "Sources land once in one governed platform that serves ten use cases",
    ("one governed platform", "ten use cases"))))], th, size=22, bold=True, anchor="middle")

# geometry of the four columns
SX, SW = 0.37, 1.80                               # source cards
LX, LW, LH = 2.42, 1.52, 0.62                     # ingestion lanes
RX, RY, RD = 4.28, 1.87, 4.01                     # the ring
CX, CY, RR = RX + RD / 2, RY + RD / 2, RD / 2
BAND = RD * 0.09348
MX0, MX1 = 8.33, 12.96                            # the mosaic, right of the ring

# column headers on solid tabs
for n, slot, word, box in (("dev.9", "slot.sources.label", "Source systems", (SX, 1.36, SW, 0.33)),
                           ("dev.14", "slot.lanes.label", "Ingestion lanes", (LX, 1.36, LW, 0.33)),
                           ("dev.19", "slot.platform.label", "Governed data platform", (CX - 1.54, 1.36, 3.08, 0.33))):
    rename(s, n, slot)
    move(s, slot, *box)
    prims.set_fill(find(s, slot), "accent", theme=th)
    text(s, slot, [P((R(word, "on-accent", bold=True, size=11),), align="center")], th, size=11,
         background="accent", anchor="middle")

# source groups: two cards, a bold group name over its systems
SRC = [("dev.5", "dev.59", (1.94, 1.36), "Internal systems",
        ["Order management", "Billing", "Service desk", "Web store"]),
       ("dev.10", "dev.60", (3.42, 1.86), "External feeds",
        ["Partner sales", "Market panels", "Weather data", "Social listening", "Credit scores", "Supplier portals"])]
for i, (card, body, (y, h), head, items) in enumerate(SRC, 1):
    rename(s, card, "struct.source.%d" % i)
    move(s, "struct.source.%d" % i, SX, y, SW, h)
    set_radius("struct.source.%d" % i)
    rename(s, body, "slot.source.%d.body" % i)
    move(s, "slot.source.%d.body" % i, SX + 0.14, y + 0.10, SW - 0.24, h - 0.18)
    text(s, "slot.source.%d.body" % i, [P((R(head, "accent-ink", bold=True, size=11),))] +
         [P((R(t, "ink", size=10),), space_before=3) for t in items], th, size=10)

# three ingestion lanes: a titled box with two inputs each, every lane fed from a source card
LANES = [("dev.7", "dev.6", 2.25, "clock", "Batch loads", (("dev.34", "file-spreadsheet", "Files"),
                                                           ("dev.35", "table", "Tables"))),
         ("dev.41", "dev.40", 3.46, "refresh-cw", "Change capture", (("dev.45", "database", "Logs"),
                                                                    ("dev.46", "layers", "Replicas"))),
         ("dev.18", "dev.15", 4.66, "activity", "Event streams", (("dev.36", "smartphone", "Apps"),
                                                                 ("dev.16", "cpu", "Sensors")))]
for i, (box, head, y, hg, word, items) in enumerate(LANES, 1):
    rename(s, box, "struct.lane.%d" % i)
    move(s, "struct.lane.%d" % i, LX, y, LW, LH)
    set_radius("struct.lane.%d" % i)
    rename(s, head, "slot.lane.%d.head" % i)
    move(s, "slot.lane.%d.head" % i, LX + 0.26, y - 0.25, LW - 0.26, 0.22)
    zero_ins("slot.lane.%d.head" % i)
    text(s, "slot.lane.%d.head" % i, [P((R(word, "ink-deep", bold=True, size=10),))], th, size=10,
         anchor="middle")
    icon(s, "slot.lane.%d.icon" % i, hg, LX, y - 0.24, 0.20, th, role="accent")
    for j, (n, g, lab) in enumerate(items, 1):
        cx = LX + LW * (2 * j - 1) / 4
        icon(s, "slot.lane.%d.item.%d.icon" % (i, j), g, cx - 0.12, y + 0.07, 0.24, th, role="accent-ink")
        slot = "slot.lane.%d.item.%d" % (i, j)
        rename(s, n, slot)
        to_front(slot)                            # above its lane box
        move(s, slot, cx - 0.36, y + 0.34, 0.72, 0.22)
        zero_ins(slot)
        text(s, slot, [P((R(lab, "ink", size=9),), align="center")], th, size=9, anchor="middle")

# source cards into lanes
for idx, (n, y) in enumerate((("dev.12", 2.56), ("dev.42", 3.77), ("dev.11", 4.97)), 1):
    rename(s, n, "struct.feed.%d" % idx)
    move(s, "struct.feed.%d" % idx, SX + SW, y, LX - SX - SW, 0)

# the ring: a donut with four band labels
rename(s, "dev.91", "struct.ring")
move(s, "struct.ring", RX, RY, RD, RD)
for n, slot, word, side in (("dev.92", "slot.ring.top", "Single governed copy", "top"),
                            ("dev.95", "slot.ring.bottom", "Versioned and audited", "bottom"),
                            ("dev.94", "slot.ring.left", "Ingest", "left"),
                            ("dev.93", "slot.ring.right", "Serve", "right")):
    rename(s, n, slot)
    if side == "top":
        move(s, slot, CX - 0.90, RY + 0.07, 1.80, 0.24)
    elif side == "bottom":
        move(s, slot, CX - 0.90, RY + RD - BAND + 0.06, 1.80, 0.24)
    else:                                         # rotated 90: centred on the band, 0.24 thick
        bx = RX + BAND / 2 if side == "left" else RX + RD - BAND / 2
        move(s, slot, bx - 0.75, CY - 0.12, 1.50, 0.24)
    zero_ins(slot)
    text(s, slot, [P((R(word, "ink-deep", bold=True, size=10),), align="center")], th, size=10, anchor="middle",
         background="card")


def ring_x(y):
    return CX - math.sqrt(RR ** 2 - (y - CY) ** 2)


# every lane converges on the ring's near side
JX = LX + LW + 0.16
for i, (y0, y1) in enumerate(((2.56, CY - 0.30), (3.77, 3.77), (4.97, CY + 0.30)), 1):
    if y0 == y1:
        prims.connect(s, (LX + LW, y0), (ring_x(y1), y1), name="struct.lane.%d.out" % i, theme=th)
    else:
        prims.elbow(s, [(LX + LW, y0), (JX, y0), (JX, y1), (ring_x(y1), y1)], name="struct.lane.%d.out" % i,
                    theme=th)

# shared stores around a core, each store wired to the core
rename(s, "dev.70", "struct.core")
move(s, "struct.core", CX - 0.46, CY - 0.38, 0.92, 0.76)
prims.set_fill(find(s, "struct.core"), "accent", theme=th)
rename(s, "dev.71", "slot.core")
move(s, "slot.core", CX - 0.46, CY - 0.18, 0.92, 0.50)
zero_ins("slot.core")
text(s, "slot.core", [P((R(t, "on-accent", bold=True, size=10),), align="center") for t in ("Shared", "model")],
     th, size=10, background="accent", anchor="middle")
STORES = [("dev.63", "dev.64", 0.0, -1.20, "Customers"), ("dev.62", "dev.96", 1.00, -0.62, "Orders"),
          ("dev.67", "dev.97", 1.00, 0.50, "Products"), ("dev.68", "dev.69", 0.0, 1.08, "Events"),
          ("dev.66", "dev.98", -1.00, 0.50, "Documents"), ("dev.61", "dev.99", -1.00, -0.62, "Features")]
SW2, SH2 = 0.80, 0.66
core = (CX - 0.46, CY - 0.38, CX + 0.46, CY + 0.38)
for i, (can, lab, dx, dy, word) in enumerate(STORES, 1):
    x, y = CX + dx - SW2 / 2, CY + dy - SH2 / 2
    rename(s, can, "struct.store.%d" % i)
    move(s, "struct.store.%d" % i, x, y, SW2, SH2)
    prims.set_fill(find(s, "struct.store.%d" % i), "card", theme=th)
    prims.set_line(find(s, "struct.store.%d" % i), "rule-strong", 0.75, theme=th)
    rename(s, lab, "slot.store.%d" % i)
    move(s, "slot.store.%d" % i, x - 0.06, y + 0.26, SW2 + 0.12, 0.30)
    zero_ins("slot.store.%d" % i)
    text(s, "slot.store.%d" % i, [P((R(word, "ink-deep", size=9),), align="center")], th, size=9,
         background="card", anchor="middle")
    if dx == 0:
        p1 = (CX, y + SH2) if dy < 0 else (CX, y)
        p2 = (CX, core[1]) if dy < 0 else (CX, core[3])
    else:
        yy = min(max(CY + dy, core[1] + 0.12), core[3] - 0.12)
        p1 = (x + SW2, yy) if dx < 0 else (x, yy)
        p2 = (core[0], yy) if dx < 0 else (core[2], yy)
    prims.connect(s, p1, p2, name="struct.spoke.%d" % i, theme=th)

# the readout mosaic: the five filled pieces merged into one shape (they tile by construction), redrawn right of
# the ring at a fixed horizontal scale, with its divider network on top
OX, OW = 7.73, 13.03 - 7.73
F = (MX1 - MX0) / OW


def mx(x):
    return MX0 + (x - OX) * F


PIECES = ("dev.20", "dev.21", "dev.22", "dev.23", "dev.51")
els = [find(s, n)._element for n in PIECES]
offs = [(int(e.find(".//" + qn("a:off")).get("x")), int(e.find(".//" + qn("a:off")).get("y")),
         int(e.find(".//" + qn("a:ext")).get("cx")), int(e.find(".//" + qn("a:ext")).get("cy"))) for e in els]
ux0, uy0 = min(o[0] for o in offs), min(o[1] for o in offs)
ux1, uy1 = max(o[0] + o[2] for o in offs), max(o[1] + o[3] for o in offs)
paths = []
for e, (ox, oy, cw, ch) in zip(els, offs):
    for p in e.find(".//" + qn("a:pathLst")):
        q = copy.deepcopy(p)
        pw, ph = int(p.get("w") or cw), int(p.get("h") or ch)
        q.set("w", str(ux1 - ux0))
        q.set("h", str(uy1 - uy0))
        for pt in q.iter(qn("a:pt")):
            pt.set("x", str(int(round(ox - ux0 + int(pt.get("x")) * cw / pw))))
            pt.set("y", str(int(round(oy - uy0 + int(pt.get("y")) * ch / ph))))
        paths.append(q)
plst = els[0].find(".//" + qn("a:pathLst"))
for p in list(plst):
    plst.remove(p)
for q in paths:
    plst.append(q)
els[0].find(".//" + qn("a:off")).set("x", str(ux0))
els[0].find(".//" + qn("a:off")).set("y", str(uy0))
els[0].find(".//" + qn("a:ext")).set("cx", str(ux1 - ux0))
els[0].find(".//" + qn("a:ext")).set("cy", str(uy1 - uy0))
for n in PIECES[1:]:
    delete(s, n)
rename(s, "dev.20", "struct.mosaic")
prims.set_fill(find(s, "struct.mosaic"), "accent", theme=th)
rename(s, "dev.52", "struct.mosaic.lines.1")
rename(s, "dev.104", "struct.mosaic.lines.2")
for slot in ("struct.mosaic", "struct.mosaic.lines.1", "struct.mosaic.lines.2"):
    sh = find(s, slot)
    move(s, slot, mx(sh.left / EMU), sh.top / EMU, sh.width / EMU * F, sh.height / EMU)

DOMAINS = [("dev.26", (8.40, 2.66, 0.98, 0.30), "megaphone", (8.90, 2.36), "Marketing",
            (("dev.29", "Audience segments"), ("dev.33", "Campaign lift"))),
           ("dev.25", (8.93, 3.23, 0.80, 0.42), "handshake", (9.72, 3.16), "Sales",
            (("dev.30", "Lead scoring"), ("dev.32", "Price guidance"))),
           ("dev.53", (9.06, 3.79, 0.92, 0.42), "headphones", (10.02, 3.86), "Service",
            (("dev.55", "Churn alerts"), ("dev.54", "Case routing"))),
           ("dev.56", (8.83, 4.39, 0.87, 0.42), "truck", (9.70, 4.54), "Supply",
            (("dev.28", "Demand forecast"), ("dev.57", "Stock balancing"))),
           ("dev.24", (8.24, 5.34, 0.91, 0.28), "coins", (8.68, 5.02), "Finance",
            (("dev.27", "Margin by account"), ("dev.31", "Cash forecast")))]
for i, (lab, (bx, by, bw, bh), g, (gx, gy), word, uses) in enumerate(DOMAINS, 1):
    slot = "slot.domain.%d.head" % i
    rename(s, lab, slot)
    move(s, slot, mx(bx), by, bw, bh)
    to_front(slot)
    text(s, slot, [P((R(word, "on-accent", bold=True, size=10),))], th, size=10, background="accent",
         anchor="bottom" if i in (1, 5) else "top")
    icon(s, "slot.domain.%d.icon" % i, g, mx(gx), gy, 0.30, th, role="on-accent")
    for j, (n, u) in enumerate(uses, 1):
        slot = "slot.domain.%d.use.%d" % (i, j)
        rename(s, n, slot)
        sh = find(s, slot)
        w = max(sh.width / EMU, 1.0)
        x = min(mx(sh.left / EMU), MX1 - 0.06 - w)
        if n == "dev.54":                         # clear of the cell divider on its left
            x, w = MX1 - 0.92, 0.86
        move(s, slot, x, sh.top / EMU, w, max(sh.height / EMU, 0.47))
        to_front(slot)
        text(s, slot, [P((R(u, "on-accent", size=10),))], th, size=10, background="accent")

# the platform foundations strip under the ring
rename(s, "dev.3", "struct.base")
move(s, "struct.base", CX - 2.005, 6.43, 4.01, 0.44)
set_radius("struct.base")
rename(s, "dev.58", "slot.base.label")
move(s, "slot.base.label", CX - 1.02, 6.18, 2.04, 0.25)
prims.set_fill(find(s, "slot.base.label"), "accent", theme=th)
zero_ins("slot.base.label")
text(s, "slot.base.label", [P((R("Platform foundations", "on-accent", bold=True, size=10),), align="center")], th,
     size=10, background="accent", anchor="middle")
for j, (n, word) in enumerate((("dev.100", "Access rules"), ("dev.101", "Data quality"),
                               ("dev.102", "Lineage"), ("dev.103", "Cost tracking")), 1):
    slot = "slot.base.%d" % j
    rename(s, n, slot)
    move(s, slot, CX - 1.945 + (j - 1) * 0.975, 6.47, 0.915, 0.36)
    zero_ins(slot)
    text(s, slot, [P((R(word, "ink", size=10),), align="center")], th, size=10, anchor="middle")

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
out = save(prs, "DL30", th, archetype="convergence-hub", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
