"""DL13: dated gantt with phase cards and gate boxes, lifted from d01-s132 (ruling 14). Deterministic."""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import open_lifted, rename, delete, move, save, find  # noqa: E402
from devwork import text as _text  # noqa: E402
from deckkit.read.ns import qn  # noqa: E402


def text(s, name, value, th, **kw):
    """Uniform text insets (0.06 in sides, 0.03 in top and bottom), then the fit-checked writer."""
    bp = find(s, name)._element.find(".//" + qn("a:bodyPr"))
    for k, v in (("lIns", 54864), ("rIns", 54864), ("tIns", 27432), ("bIns", 27432)):
        bp.set(k, str(v))
    _text(s, name, value, th, **kw)
from deckkit import prims, text as txt  # noqa: E402

VARIANT = "milestone-axis-phase-cards"

ap = argparse.ArgumentParser()
ap.add_argument("--out")
args = ap.parse_args()

prs, s, th = open_lifted("DL13")
prims.bind(th)

# ---- chrome: the subtitle under the title goes
delete(s, "dev.11")

# ---- title
rename(s, "dev.10", "slot.title")
move(s, "slot.title", 0.48, 0.30, 12.40, 0.50)
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "Go-live lands in week 30 if the design gate clears by week 10",
    keywords=("week 30", "week 10"))))], th, size=22, anchor="middle")

# ---- vertical layout (inches)
AX_LBL, AX = 1.12, 1.44            # period labels, axis arrow top
L1, L2, BAR_H = 2.16, 3.04, 0.34   # lane tops
CARD_Y, CARD_H = 3.98, 1.24
GATE_Y, GATE_H = 5.62, 0.74

# ---- period axis: arrow, dots, labels
rename(s, "dev.12", "struct.axis.1")
move(s, "struct.axis.1", 0.94, AX, 12.13 - 0.94, 0.26)
prims.set_fill(find(s, "struct.axis.1"), "ink-deep")
periods = ["Kickoff", "Week 6", "Week 10", "Week 14", "Week 18", "Week 22", "Week 26", "Week 30"]
dots = ["dev.13", "dev.15", "dev.17", "dev.19", "dev.21", "dev.23", "dev.25", "dev.27"]
labels = ["dev.14", "dev.16", "dev.18", "dev.20", "dev.22", "dev.24", "dev.26", "dev.28"]
cx = []
for i, (d, l, p) in enumerate(zip(dots, labels, periods), 1):
    sh = find(s, d)
    cx.append(sh.left / 914400 + sh.width / 914400 / 2)
    rename(s, d, "struct.dot.%d" % i)
    move(s, "struct.dot.%d" % i, sh.left / 914400, AX - 0.02, 0.30, 0.30)
    prims.set_fill(sh, "accent")
    prims.set_line(sh, "paper", 1.5)
    rename(s, l, "slot.period.%d" % i)
    move(s, "slot.period.%d" % i, cx[-1] - 0.50, AX_LBL, 1.00, 0.26)
    text(s, "slot.period.%d" % i, [txt.Para((txt.Run(p, "ink-deep", bold=True, size=11),), align="center")],
         th, size=11, anchor="bottom")

# ---- dashed period and gate lines
gate_x = {4.50: 1, 9.16: 2, 12.28: 3}
for n, d in enumerate(["dev.2", "dev.3", "dev.4", "dev.5", "dev.6", "dev.7", "dev.8", "dev.9"], 1):
    sh = find(s, d)
    x = sh.left / 914400
    g = next((v for k, v in gate_x.items() if abs(k - x) < 0.05), None)
    if g:
        rename(s, d, "struct.gateline.%d" % g)
        sh.top, sh.height = int((AX + 0.28) * 914400), int((GATE_Y - 0.07 - AX - 0.28) * 914400)
        prims.set_line(sh, "ink-muted", 1.0, dash="dash")
    else:
        rename(s, d, "struct.gridline.%d" % n)
        sh.top, sh.height = int((AX + 0.28) * 914400), int((CARD_Y - AX - 0.28) * 914400)
        prims.set_line(sh, "hairline", 0.75, dash="dash")

# ---- bars: (shape, slot, x, w, lane top, fill, text role, label, align)
bars = [
    ("dev.29", 1, 0.83, 1.80, L1, "ink-strong", "paper", "Discover", "center"),
    ("dev.31", 2, 2.87, 1.46, L1, "accent-deep", "on-accent", "Design", "center"),
    ("dev.33", 3, 4.67, 1.34, L1, "accent-wash", "ink-deep", "Set up", "center"),
    ("dev.35", 4, 6.05, 2.94, L1, "accent", "on-accent", "Build and migrate", "center"),
    ("dev.36", 5, 9.32, 3.20, L1, "accent-wash", "ink-deep", "Training and adoption", "center"),
    ("dev.37", 6, 7.19, 3.36, L2, "navy", "paper", "Parallel run", "center"),
    ("dev.39", 7, 10.89, 1.22, L2, "hairline", "ink-deep", "Cutover", "center"),
]
for d, n, x, w, y, fill, role, label, al in bars:
    nm = "slot.bar.%d" % n
    rename(s, d, nm)
    move(s, nm, x, y, w, BAR_H)
    prims.set_fill(find(s, nm), fill)
    prims.set_line(find(s, nm), None)
    text(s, nm, [txt.Para((txt.Run(label, role, bold=True, size=10),), align=al)], th, size=10,
         background=fill, anchor="middle")

# ---- exit rings at bar ends, with their dates beneath
rings = [("dev.30", 2.67, L1), ("dev.32", 4.415, L1), ("dev.34", 9.08, L1), ("dev.38", 10.635, L2), ("dev.45", 12.195, L2)]
for i, (d, x, y) in enumerate(rings, 1):
    nm = "struct.ring.%d" % i
    rename(s, d, nm)
    move(s, nm, x, y + (BAR_H - 0.17) / 2, 0.17, 0.17)
    prims.set_fill(find(s, nm), "paper")
    prims.set_line(find(s, nm), "accent", 1.25)
marks = [("dev.40", 2.755, L1, "Week 5 exit"), ("dev.41", 4.50, L1, "Week 10 exit"),
         ("dev.43", 9.165, L1, "Week 22 exit"), ("dev.44", 10.72, L2, "Week 26 exit"),
         ("dev.42", 12.28, L2, "Week 30 exit")]
for i, (d, c, y, lab) in enumerate(marks, 1):
    nm = "slot.mark.%d" % i
    rename(s, d, nm)
    move(s, nm, c - 0.48, y + BAR_H + 0.03, 0.96, 0.30)
    prims.set_fill(find(s, nm), "paper")   # a label chip on its own line: it masks the dashed line it sits on
    prims.set_line(find(s, nm), None)
    al = "center"
    text(s, nm, [txt.Para((txt.Run(lab, "ink-muted", size=9),), align=al)], th, size=9)

# ---- phase cards
cards = [
    ("dev.46", "dev.51", "dev.56", "ink-strong", "paper", "Discover", "Map every source feed", "Exit: scope agreed"),
    ("dev.47", "dev.52", "dev.57", "accent-deep", "on-accent", "Design", "Target data model",
     "Exit: design signed"),
    ("dev.48", "dev.53", "dev.58", "accent", "on-accent", "Build and migrate", "Migrate in three waves",
     "Exit: tests pass"),
    ("dev.49", "dev.54", "dev.59", "navy", "paper", "Parallel run", "Both systems live",
     "Exit: two clean closes"),
    ("dev.50", "dev.55", "dev.60", "hairline", "ink-deep", "Cutover", "Switch in one weekend",
     "Exit: legacy retired"),
]
for i, (c, h, b, fill, role, head, l1, l2) in enumerate(cards, 1):
    sh = find(s, c)
    x, w = sh.left / 914400, sh.width / 914400
    rename(s, c, "struct.card.%d" % i)
    move(s, "struct.card.%d" % i, x, CARD_Y, w, CARD_H)
    prims.set_fill(sh, "card")
    prims.set_line(sh, None)
    sh._element.find(".//" + qn("a:prstGeom")).find(qn("a:avLst")).clear()
    gd = sh._element.find(".//" + qn("a:prstGeom")).find(qn("a:avLst"))
    from lxml import etree
    etree.SubElement(gd, qn("a:gd"), name="adj", fmla="val %d" % round(0.05 / min(w, CARD_H) * 100000))
    rename(s, h, "slot.card.%d.head" % i)
    move(s, "slot.card.%d.head" % i, x + 0.11, CARD_Y + 0.12, w - 0.22, 0.38)
    prims.set_fill(find(s, "slot.card.%d.head" % i), fill)
    prims.set_line(find(s, "slot.card.%d.head" % i), None)
    text(s, "slot.card.%d.head" % i, [txt.Para((txt.Run(head, role, bold=True, size=11),), align="center")],
         th, size=11, background=fill, anchor="middle")
    rename(s, b, "slot.card.%d.body" % i)
    move(s, "slot.card.%d.body" % i, x + 0.11, CARD_Y + 0.58, w - 0.22, 0.56)
    text(s, "slot.card.%d.body" % i,
         [txt.Para((txt.Run(l1, "ink", size=11),), align="center"),
          txt.Para((txt.Run(l2, "ink-muted", bold=True, size=11),), align="center", space_before=2)],
         th, size=11, background="card")

# ---- decision gates
rename(s, "dev.61", "slot.gates.label")
move(s, "slot.gates.label", 0.54, GATE_Y + 0.20, 2.90, 0.34)
text(s, "slot.gates.label", [txt.Para((txt.Run("Three go or no-go gates", "ink-deep", bold=True, size=12),))],
     th, size=12, anchor="middle")
gates = [("dev.62", "dev.65", 3.76, 2.72, 4.50, "Gate 1 · Week 10", "Design signed, build budget released"),
         ("dev.63", "dev.66", 6.65, 2.93, 9.16, "Gate 2 · Week 22", "Defect backlog under the agreed limit"),
         ("dev.64", "dev.67", 9.76, 3.14, 12.28, "Gate 3 · Week 30", "Go-live call, legacy set to read-only")]
for i, (b, r, x, w, gx, head, body) in enumerate(gates, 1):
    nm = "slot.gate.%d" % i
    rename(s, b, nm)
    move(s, nm, x, GATE_Y, w, GATE_H)
    prims.set_fill(find(s, nm), "paper")
    prims.set_line(find(s, nm), "accent", 1.0)
    text(s, nm, [txt.Para((txt.Run(head, "accent-ink", bold=True, size=11),), align="center"),
                 txt.Para((txt.Run(body, "ink", size=11),), align="center", space_before=2)],
         th, size=11, anchor="middle")
    rn = "struct.gatering.%d" % i
    rename(s, r, rn)
    move(s, rn, gx - 0.07, GATE_Y - 0.07, 0.14, 0.14)
    prims.set_fill(find(s, rn), "paper")
    prims.set_line(find(s, rn), "accent", 1.25)

# gate rings above the gate boxes in z-order
tree = s.shapes._spTree
for i in (1, 2, 3):
    el = find(s, "struct.gatering.%d" % i)._element
    tree.remove(el)
    tree.append(el)

out = save(prs, "DL13", th, archetype="gantt", variant=VARIANT)
if args.out:
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(out, args.out)
print(out)
