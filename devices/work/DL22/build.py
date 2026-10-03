"""DL22: a rising maturity curve with five numbered levels, a level card above each disc and its outcome below,
a fence marking where most teams sit today, and a foundations rail beside the plot (maturity-model)."""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import text as txt  # noqa: E402
from deckkit.canvas import Box  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL22")
VARIANT = "rising-curve-foundations-rail"

# the device grows into the height the foot band gave up: old y maps linearly onto the new plot
Y0, Y1, N0, N1 = 1.33, 5.72, 1.05, 6.80
K = (N1 - N0) / (Y1 - Y0)


def Y(y):
    return N0 + (y - Y0) * K


# the curve, its discs and fences take a steeper map so the level stacks fill the plot evenly top to bottom
def Yc(y):
    return 2.718 + (y - 2.69) * 1.573


def stretch(name, new, f=Y, bottom=None):
    sh = find(s, name)
    y, h = sh.top / EMU, sh.height / EMU
    rename(s, name, new)
    top = f(y)
    move(s, new, sh.left / EMU, top, sh.width / EMU, (bottom - top) if bottom is not None else f(y + h) - top)


def insets(name, l=0.0, t=0.0, r=0.0, b=0.0):
    bp = find(s, name)._element.find(".//" + qn("a:bodyPr"))
    for k, v in (("lIns", l), ("tIns", t), ("rIns", r), ("bIns", b)):
        bp.set(k, str(int(v * EMU)))


def para(t, role="ink", size=10, bold=False, align="left", sb=0):
    return txt.Para((txt.Run(t, role, bold=bold, size=size),), align=align, space_before=sb)


# ---- chrome the house rules ban: the foot band with its sentences, brand art and every corpus icon -------------
GONE = (["dev.55"] + ["dev.%d" % i for i in range(42, 54)] + ["dev.%d" % i for i in range(61, 82)]
        + ["dev.%d" % i for i in range(82, 119)] + ["dev.%d" % i for i in range(119, 177)])
for n in GONE:                  # a group takes its children with it
    try:
        delete(s, n)
    except KeyError:
        pass

# ---- title -----------------------------------------------------------------------------------------------------
rename(s, "dev.2", "slot.title")
move(s, "slot.title", 0.37, 0.28, 12.59, 0.56)
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "Finance value climbs fastest once teams move past automated posting", ("climbs fastest",))))],
    th, size=22, bold=True, anchor="middle")

# ---- plot, axes, curve, fences ---------------------------------------------------------------------------------
stretch("dev.3", "struct.plot")
stretch("dev.4", "struct.axis.y")
move(s, "struct.axis.y", find(s, "struct.axis.y").left / EMU, Y(1.46), 0, N1 - Y(1.46))   # lands on the plot edge
stretch("dev.5", "struct.axis.x")
stretch("dev.13", "struct.curve", Yc)
FENCE_B = Y(5.48)
for k, n in enumerate(("dev.14", "dev.15", "dev.16", "dev.17"), 1):
    stretch(n, "struct.fence.%d" % k, Yc, FENCE_B)

rename(s, "dev.7", "slot.axis.y.label")
mid = (Y(1.46) + N1) / 2
move(s, "slot.axis.y.label", 0.55 - 1.30, mid - 0.17, 2.60, 0.34)
text(s, "slot.axis.y.label", [para("Value to the business", "ink-strong", 10.5, True, "center")], th, size=10.5,
     anchor="middle")
for k, (n, yc, w) in enumerate((("dev.11", 1.835, "Highest"), ("dev.10", 2.865, "High"),
                                ("dev.9", 3.895, "Medium"), ("dev.8", 4.925, "Low")), 1):
    rename(s, n, "slot.axis.y.tick.%d" % k)
    move(s, "slot.axis.y.tick.%d" % k, 0.74, Yc(yc) - 0.13, 0.66, 0.26)
    text(s, "slot.axis.y.tick.%d" % k, [para(w, "ink-muted", 9, False, "right")], th, size=9, anchor="middle")

# ---- five levels on the curve ----------------------------------------------------------------------------------
LEVELS = [  # disc, label, body, card, desc, old disc centre, glyph, head, desc, label, body
    ("dev.18", "dev.19", "dev.20", "dev.33", "dev.34", (2.49, 4.53), "file-spreadsheet", "Manual",
     "Staff key and check every entry by hand", "Slow close", "Errors only surface late in the review"),
    ("dev.21", "dev.22", "dev.23", "dev.35", "dev.36", (4.35, 4.33), "list-checks", "Assisted",
     "Rules flag gaps for staff to review and fix", "Fewer errors", "Staff still clear every exception by hand"),
    ("dev.24", "dev.25", "dev.26", "dev.37", "dev.38", (6.13, 3.95), "workflow", "Automated",
     "Bots post routine entries end to end", "Faster close", "Exceptions queue for an analyst to clear"),
    ("dev.27", "dev.28", "dev.29", "dev.39", "dev.40", (7.95, 3.46), "brain-circuit", "Augmented",
     "Models forecast and suggest next steps", "Earlier insight", "Analysts act on model advice each day"),
    ("dev.30", "dev.31", "dev.32", "dev.41", "dev.54", (9.76, 2.69), "bot", "Autonomous",
     "Agents run the close within set limits", "Continuous close", "People govern the policy and every limit"),
]
W, SHIFT = 1.62, 0.10          # stack width, and how far a stack leans left off its disc, clear of the rising curve
for i, (disc, lab, body, card, desc, (ocx, ocy), g, head, d, l, b) in enumerate(LEVELS, 1):
    cy = Yc(ocy)
    x0 = ocx - W / 2 - SHIFT
    rename(s, disc, "slot.level.%d.num" % i)
    move(s, "slot.level.%d.num" % i, ocx - 0.15, cy - 0.15, 0.30, 0.30)
    insets("slot.level.%d.num" % i)
    text(s, "slot.level.%d.num" % i, [para(str(i), "on-accent", 10, True, "center")], th, size=10,
         anchor="middle", background="accent")

    rename(s, card, "slot.level.%d.head" % i)
    move(s, "slot.level.%d.head" % i, x0, cy - 1.20, W, 0.42)
    insets("slot.level.%d.head" % i, 0.42, 0.03, 0.04, 0.03)
    text(s, "slot.level.%d.head" % i, [para(head, "ink-deep", 11, True)], th, size=11, anchor="middle")
    icon(s, "slot.level.%d.icon" % i, g, x0 + 0.11, cy - 1.20 + 0.06, 0.30, th, role="accent")

    rename(s, desc, "slot.level.%d.desc" % i)
    move(s, "slot.level.%d.desc" % i, x0, cy - 0.74, W, 0.46)
    text(s, "slot.level.%d.desc" % i, [para(d, "ink", 10, False, "center")], th, size=10, background="card")

    # level 5 sits where the curve climbs steepest: its outcome drops clear of the line and leans right
    lx, dy = (ocx - W / 2 + 0.15, 0.40) if i == 5 else (ocx - W / 2, 0.0)
    rename(s, lab, "slot.level.%d.label" % i)
    move(s, "slot.level.%d.label" % i, lx, cy + 0.22 + dy, W, 0.26)
    text(s, "slot.level.%d.label" % i, [para(l, "accent-ink", 10.5, True, "center")], th, size=10.5,
         background="card")
    rename(s, body, "slot.level.%d.body" % i)
    move(s, "slot.level.%d.body" % i, lx, cy + 0.48 + dy, W, 0.46)
    text(s, "slot.level.%d.body" % i, [para(b, "ink", 10, False, "center")], th, size=10, background="card")

# the fence under level 3 marks where most teams sit today
rename(s, "dev.6", "slot.marker")
f2, f3 = find(s, "struct.fence.2"), find(s, "struct.fence.3")
fx0, fx1 = f2.left / EMU, f3.left / EMU
move(s, "slot.marker", fx0 + 0.05, Yc(3.95) + 1.06, fx1 - fx0 - 0.10, 0.40)
insets("slot.marker", 0.04, 0.02, 0.04, 0.02)
text(s, "slot.marker", [para("Most teams today", "accent-ink", 10.5, True, "center")], th, size=10.5,
     background="card", anchor="middle")

# ---- foundations rail ------------------------------------------------------------------------------------------
rename(s, "dev.12", "struct.rail")
RT, RB = Y(1.46), N1
move(s, "struct.rail", 10.96, RT, 2.00, RB - RT)
icon(s, "slot.rail.icon", "layers", 11.10, RT + 0.17, 0.40, th, role="accent")
txt.textbox(s, Box(11.58, RT + 0.10, 1.30, 0.56), [para("Foundations", "ink-deep", 10.5, True),
                                                   para("for every level", "ink-deep", 10.5, True)],
            "slot.rail.head", th, size=10.5, anchor="middle", background="accent-wash")
RAIL = (("dev.56", "shield-check", "Controls", "Every entry has an audit trail"),
        ("dev.57", "user-check", "Oversight", "People approve agent limits"),
        ("dev.58", "boxes", "Integration", "One ledger and data model"),
        ("dev.59", "database", "Data quality", "Master data cleaned monthly"),
        ("dev.60", "graduation-cap", "Skills", "Analysts trained for each level"))
top, gap = RT + 0.82, 0.12
h = (RB - 0.12 - top - gap * 4) / 5
for k, (n, g, hd, bd) in enumerate(RAIL, 1):
    y = top + (k - 1) * (h + gap)
    rename(s, n, "slot.rail.item.%d" % k)
    move(s, "slot.rail.item.%d" % k, 11.06, y, 1.80, h)
    insets("slot.rail.item.%d" % k, 0.48, 0.06, 0.06, 0.06)
    text(s, "slot.rail.item.%d" % k, [para(hd, "ink-deep", 11, True), para(bd, "ink", 10.5, False, sb=2)], th,
         size=11, anchor="middle")
    icon(s, "slot.rail.item.%d.icon" % k, g, 11.15, y + h / 2 - 0.16, 0.32, th, role="accent")

for k in range(1, 6):                      # rail cards keep the house corner radius
    sh = find(s, "slot.rail.item.%d" % k)
    gd = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst") + "/" + qn("a:gd"))
    gd.set("fmla", "val %d" % round(0.05 / (min(sh.width, sh.height) / EMU) * 100000))

out = save(prs, "DL22", th, archetype="maturity-model", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
