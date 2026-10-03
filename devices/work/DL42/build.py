"""DL42: five numbered reason panels set as a mosaic (two stacked on the left, a proof list, a four-practice grid,
a run list on the right), a controls band under the middle panels that backs every reason, and a platform strip of
mark slots along the foot that take vendor: keys (why-us)."""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import measure, prims  # noqa: E402
from deckkit import text as txt  # noqa: E402
from deckkit.canvas import Box  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL42")
VARIANT = "reason-mosaic-platform-strip"

# flatten every group into slide space (single-row wrappers, the grid row groups and the controls row group)
def flatten():
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
# the left column's outer frame, the empty top rect, and the two rotated foot rules (redrawn below)
for n in ("dev.7", "dev.89", "dev.75", "dev.112"):
    delete(s, n)

# title at the kit's wide title geometry, 21pt, one line, insets zero
rename(s, "dev.113", "slot.title")
move(s, "slot.title", 0.50, 0.13, 12.40, 0.40)
bp = find(s, "slot.title")._element.find(".//" + qn("a:bodyPr"))
for k in ("lIns", "tIns", "rIns", "bIns"):
    bp.set(k, "0")
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "Five reasons data leaders keep one partner from strategy to daily run", ("Five reasons",))))],
    th, size=21, bold=True, anchor="middle")


def put(name, box, paras, background="card", anchor="middle"):
    """Move a lifted text shape to box and write paras with zero insets, fit-checked."""
    move(s, name, box.x, box.y, box.w, box.h)
    txt.check_fit("slot %s" % name, paras, box, th, measure.ZERO)
    txt.write(find(s, name).text_frame, paras, th, measure.ZERO, anchor=anchor, background=background)


def body(t, size=11, role="ink", bold=False, align="left"):
    return [txt.Para((txt.Run(t, role, bold=bold, size=size),), align=align)]


def radius(name, r=0.06):
    sh = find(s, name)
    gd = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst") + "/" + qn("a:gd"))
    if gd is None:
        av = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst"))
        gd = av.makeelement(qn("a:gd"), {"name": "adj"})
        av.append(gd)
    gd.set("fmla", "val %d" % round(r / (min(sh.width, sh.height) / EMU) * 100000))


def head2(name, r=0.06):
    sh = find(s, name)
    av = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst"))
    for g in list(av):
        av.remove(g)
    for nm, v in (("adj1", round(r / (min(sh.width, sh.height) / EMU) * 100000)), ("adj2", 0)):
        av.append(av.makeelement(qn("a:gd"), {"name": nm, "fmla": "val %d" % v}))


def foot_card(name, r=0.06):
    """A card that hangs from its tab: square top corners, rounded bottom (round2SameRect flipped)."""
    sh = find(s, name)
    geo = sh._element.find(".//" + qn("a:prstGeom"))
    geo.set("prst", "round2SameRect")
    head2(name, r)
    sh._element.find(".//" + qn("a:xfrm")).set("flipV", "1")


def vline(name, x, y0, y1):
    """A connector drawn vertical; a rotated lifted one keeps its 90 degrees, so its box is laid on its centre."""
    sh = find(s, name)
    if abs(sh.rotation) > 1:
        L = y1 - y0
        move(s, name, x - L / 2, (y0 + y1) / 2, L, 0)
    else:
        move(s, name, x, y0, 0, y1 - y0)


def hline(name, x0, x1, y):
    move(s, name, x0, y, x1 - x0, 0)


# the mosaic grid inside the content band (x 0.50 to 12.90, y 0.85 to 6.84)
G = 0.12
C1, C2, C3, C4 = (0.50, 2.70), (3.32, 2.40), (5.84, 4.54), (10.50, 2.40)
HH = LAP = 0.42                 # header tab height; the card starts where the tab ends
TOP, MOS_END = 0.85, 5.46
PAD = 0.14


def panel(card, tab, label, x, w, y, h_to, n, reason):
    rename(s, card, "struct.reason.%d.card" % n)
    rename(s, tab, "struct.reason.%d.tab" % n)
    rename(s, label, "slot.reason.%d.head" % n)
    move(s, "struct.reason.%d.tab" % n, x, y, w, HH)
    move(s, "struct.reason.%d.card" % n, x, y + LAP, w, h_to - y - LAP)
    prims.set_fill(find(s, "struct.reason.%d.tab" % n), "accent", theme=th)
    prims.set_fill(find(s, "struct.reason.%d.card" % n), "paper", theme=th)
    prims.set_line(find(s, "struct.reason.%d.card" % n), "hairline", 0.75, theme=th)
    foot_card("struct.reason.%d.card" % n)
    head2("struct.reason.%d.tab" % n)
    put("slot.reason.%d.head" % n, Box(x + PAD, y + 0.02, w - 2 * PAD, HH - 0.04),
        [txt.Para((txt.Run("%02d" % n, "on-accent", bold=True, size=16), txt.Run("  " + reason, "on-accent",
                                                                                   bold=True, size=13)))],
        background="accent")


def rows(n, x, w, y0, y1, items, divs, gl_side=0.30):
    """A proof list: glyph left, one or two lines right, dashed rules between rows."""
    step = (y1 - y0) / len(items)
    for j, (shape, g, line) in enumerate(items, 1):
        ry = y0 + (j - 1) * step
        icon(s, "slot.reason.%d.row.%d.icon" % (n, j), g, x + PAD, ry + (step - gl_side) / 2, gl_side, th)
        rename(s, shape, "slot.reason.%d.row.%d" % (n, j))
        tx = x + PAD + gl_side + 0.14
        put("slot.reason.%d.row.%d" % (n, j), Box(tx, ry + 0.04, x + w - PAD - tx, step - 0.08), body(line),
            background="paper")
    for j, d in enumerate(divs, 1):
        rename(s, d, "struct.reason.%d.rule.%d" % (n, j))
        hline("struct.reason.%d.rule.%d" % (n, j), x + PAD, x + w - PAD, y0 + j * step)


# 01, left top: three rows
R1_END = 2.85
panel("dev.2", "dev.8", "dev.9", *C1, TOP, R1_END, 1, "Advice that ships")
rows(1, *C1, TOP + HH + 0.04, R1_END - 0.06,
     [("dev.94", "workflow", "Process maps tied to a build plan"),
      ("dev.83", "route", "Roadmaps ranked by value and effort"),
      ("dev.84", "wrench", "Process fixes landed in weeks")], ["dev.95", "dev.96"])

# 05, left bottom: four rows
R5_Y = R1_END + G
panel("dev.85", "dev.86", "dev.87", *C1, R5_Y, MOS_END, 5, "Strategy that pays")
rows(5, *C1, R5_Y + HH + 0.04, MOS_END - 0.06,
     [("dev.19", "compass", "Data vision tied to budget"),
      ("dev.21", "coins", "Revenue cases for data"),
      ("dev.23", "map", "One data and tech roadmap"),
      ("dev.25", "shield-check", "Owners and policy set early")], ["dev.97", "dev.98", "dev.99"])

# 02, centre left: four rows
MID_END = 4.18
panel("dev.3", "dev.4", "dev.17", *C2, TOP, MID_END, 2, "Models in use")
rows(2, *C2, TOP + HH + 0.04, MID_END - 0.06,
     [("dev.56", "truck", "Supply forecasts planners act on"),
      ("dev.58", "megaphone", "Marketing mix read every quarter"),
      ("dev.60", "gauge", "Operations alerts ahead of failure"),
      ("dev.62", "shopping-cart", "Online sales models tuned weekly")], ["dev.100", "dev.101", "dev.102"])

# 03, centre: a four-practice grid, a heading and three proof cells per column
panel("dev.5", "dev.10", "dev.11", *C3, TOP, MID_END, 3, "Engineering across four practices")
GX0, GX1 = C3[0] + PAD, C3[0] + C3[1] - PAD
CW = (GX1 - GX0) / 4
GY0 = TOP + HH + 0.06
CH_H = 0.40
CELL0, CELL1 = GY0 + CH_H, MID_END - 0.08
CELL = (CELL1 - CELL0) / 3
PRACTICES = [
    ("dev.26", "Pipelines", ("dev.31", "Legacy loads migrated"), ("dev.36", "Jobs tuned for cost"),
     ("dev.41", "Batch and stream ingest")),
    ("dev.27", "Models", ("dev.32", "Models moved to production"), ("dev.37", "Shared feature stores"),
     ("dev.42", "Retraining on a schedule")),
    ("dev.28", "Cloud", ("dev.33", "Data stores moved"), ("dev.38", "Apps rebuilt as services"),
     ("dev.43", "Spend tracked and cut")),
    ("dev.29", "Reporting", ("dev.34", "Lakes with named owners"), ("dev.39", "Data products with targets"),
     ("dev.44", "Dashboards teams open daily")),
]
for c, (hd, label, *cells) in enumerate(PRACTICES, 1):
    cx = GX0 + (c - 1) * CW
    rename(s, hd, "slot.practice.%d.head" % c)
    put("slot.practice.%d.head" % c, Box(cx + 0.04, GY0, CW - 0.10, CH_H),
        body(label, size=12, role="ink-deep", bold=True), background="paper", anchor="top")
    for r, (shape, line) in enumerate(cells, 1):
        rename(s, shape, "slot.practice.%d.cell.%d" % (c, r))
        put("slot.practice.%d.cell.%d" % (c, r), Box(cx + 0.04, CELL0 + (r - 1) * CELL + 0.04, CW - 0.10,
                                                     CELL - 0.08), body(line), background="paper")
for k, d in enumerate(("dev.80", "dev.81", "dev.82"), 1):           # column rules
    rename(s, d, "struct.practice.rule.%d" % k)
    vline("struct.practice.rule.%d" % k, GX0 + k * CW - 0.02, GY0, CELL1)
SEG = {1: ("dev.46", "dev.47", "dev.48", "dev.49"), 2: ("dev.51", "dev.52", "dev.53", "dev.54")}
for r, segs in SEG.items():                                         # row rules, broken at the column rules
    for c, d in enumerate(segs, 1):
        rename(s, d, "struct.practice.row.%d.%d" % (r, c))
        x0 = GX0 + (c - 1) * CW + (0.06 if c > 1 else 0)
        hline("struct.practice.row.%d.%d" % (r, c), x0, GX0 + c * CW - 0.10, CELL0 + r * CELL)

# 04, right: five rows
panel("dev.15", "dev.16", "dev.88", *C4, TOP, MOS_END, 4, "One run team")
rows(4, *C4, TOP + HH + 0.04, MOS_END - 0.06,
     [("dev.65", "flask-conical", "Data labs for fast trials"),
      ("dev.67", "cloud-cog", "Cloud estate run around the clock"),
      ("dev.69", "git-branch", "Release and security operations"),
      ("dev.71", "activity", "Pipeline health watched daily"),
      ("dev.73", "headphones", "Data apps kept on support")], ["dev.90", "dev.91", "dev.92", "dev.93"])

# the controls band under 02 and 03: what backs every reason, unnumbered, ink-strong tab
BX, BW = C2[0], C3[0] + C3[1] - C2[0]
BY = MID_END + G
rename(s, "dev.12", "struct.controls.card")
rename(s, "dev.13", "struct.controls.tab")
rename(s, "dev.14", "slot.controls.head")
move(s, "struct.controls.tab", BX, BY, BW, HH)
move(s, "struct.controls.card", BX, BY + LAP, BW, MOS_END - BY - LAP)
prims.set_fill(find(s, "struct.controls.tab"), "ink-strong", theme=th)
prims.set_fill(find(s, "struct.controls.card"), "paper", theme=th)
prims.set_line(find(s, "struct.controls.card"), "hairline", 0.75, theme=th)
foot_card("struct.controls.card")
head2("struct.controls.tab")
put("slot.controls.head", Box(BX + PAD, BY + 0.02, BW - 2 * PAD, HH - 0.04),
    body("Controls built into every engagement", size=13, role="paper", bold=True, align="center"),
    background="ink-strong")
CTRL = [("dev.105", "library", "Catalog and lineage from day one"),
        ("dev.107", "id-card", "One trusted record per customer"),
        ("dev.109", "shield", "Quality and security checks on every load")]
SW = BW / 3
CY0, CY1 = BY + HH + 0.04, MOS_END - 0.06
for k, (shape, g, line) in enumerate(CTRL, 1):
    sx = BX + (k - 1) * SW
    icon(s, "slot.controls.%d.icon" % k, g, sx + 0.22, (CY0 + CY1) / 2 - 0.17, 0.34, th)
    rename(s, shape, "slot.controls.%d" % k)
    put("slot.controls.%d" % k, Box(sx + 0.70, CY0, SW - 0.70 - 0.16, CY1 - CY0), body(line), background="paper")
for k, d in enumerate(("dev.110", "dev.111"), 1):
    rename(s, d, "struct.controls.rule.%d" % k)
    vline("struct.controls.rule.%d" % k, BX + k * SW, CY0 + 0.04, CY1 - 0.04)

# the platform strip: what the team builds on, in two groups of glyph slots (logos only, no names in text).
# Each slot takes a vendor: mark key at placement (devices.place draws the mark fresh with its alt record);
# a fixed vendor picture would lose that record when the library is cloned and fail P22 and P18.
SY0, SY1 = MOS_END + G + 0.02, 6.84
rename(s, "dev.6", "struct.platforms.card")
move(s, "struct.platforms.card", 0.50, SY0, 12.40, SY1 - SY0)
prims.set_fill(find(s, "struct.platforms.card"), "card", theme=th)
prims.set_line(find(s, "struct.platforms.card"), None, theme=th)
radius("struct.platforms.card")
rename(s, "dev.63", "slot.platforms.label")
put("slot.platforms.label", Box(0.66, SY0 + 0.10, 1.34, SY1 - SY0 - 0.20),
    body("Platforms the team builds on", size=12, role="ink-deep", bold=True), background="card")
DIV = 2.14
rename(s, "dev.77", "struct.platforms.pointer")
tri = find(s, "struct.platforms.pointer")
tw, thh = tri.width / EMU, tri.height / EMU                          # rotated 90: drawn tw tall, thh wide
move(s, "struct.platforms.pointer", DIV - tw / 2 + thh / 2, (SY0 + SY1) / 2 - thh / 2)
prims.hairline(s, (DIV, SY0 + 0.14), (DIV, SY1 - 0.14), role="ink-muted", name="struct.platforms.rule.1", theme=th)
GROUPS = [                       # glyph stand-ins; the comment names the vendor: key each slot was drawn for
    ("dev.74", "dev.76", "Cloud and warehouse", 2.36, 5.54,
     ["cloud",            # aws/aws
      "cloud-cog",        # azure/azure
      "cloud-upload",     # gcp/gcp
      "warehouse",        # saas/analytics/snowflake
      "layers",           # onprem/analytics/databricks
      "git-merge"]),      # onprem/analytics/dbt
    ("dev.78", "dev.79", "Engineering and analytics", 5.86, 12.74,
     ["code",             # programming/language/python
      "cpu",              # onprem/analytics/spark
      "workflow",         # onprem/workflow/airflow
      "network",          # onprem/queue/kafka
      "server",           # onprem/analytics/hadoop
      "boxes",            # onprem/workflow/kubeflow
      "database",         # onprem/database/mongodb
      "database-search",  # onprem/database/postgresql
      "chart-column",     # onprem/analytics/tableau
      "activity",         # saas/logging/datadog
      "chart-line",       # programming/language/r
      "terminal"]),       # programming/language/scala
]
PILL_H, MARK = 0.30, 0.30
mark_n = 0
for k, (pill, lab, label, x0, x1, keys) in enumerate(GROUPS, 1):
    rename(s, pill, "struct.platforms.group.%d.pill" % k)
    rename(s, lab, "slot.platforms.group.%d" % k)
    move(s, "struct.platforms.group.%d.pill" % k, x0, SY0 + 0.10, x1 - x0, PILL_H)
    prims.set_fill(find(s, "struct.platforms.group.%d.pill" % k), "paper", theme=th)
    radius("struct.platforms.group.%d.pill" % k, 0.05)
    put("slot.platforms.group.%d" % k, Box(x0 + 0.10, SY0 + 0.12, x1 - x0 - 0.20, PILL_H - 0.04),
        body(label, size=12, role="ink-deep", bold=True, align="center"), background="paper")
    per = len(keys) // 2
    slot = (x1 - x0) / per
    for i, key in enumerate(keys):
        r, c = divmod(i, per)
        mx = x0 + c * slot + (slot - MARK) / 2
        my = SY0 + 0.10 + PILL_H + 0.08 + r * (MARK + 0.06)
        mark_n += 1
        icon(s, "slot.platforms.mark.%d" % mark_n, key, mx, my, MARK, th, role="ink-strong")
prims.hairline(s, (5.70, SY0 + 0.14), (5.70, SY1 - 0.14), role="hairline", name="struct.platforms.rule.2", theme=th)

# cards behind everything they hold: the lifted order painted the fifth card over its own rows
tree = s.shapes._spTree
for nm in reversed(["struct.platforms.card", "struct.controls.card"] + ["struct.reason.%d.card" % n for n in range(1, 6)]):
    el = find(s, nm)._element
    tree.remove(el)
    tree.insert(2, el)

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
out = save(prs, "DL42", th, archetype="why-us", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
