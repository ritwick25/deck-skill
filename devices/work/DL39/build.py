"""DL39: two options compared on one question set. Left, a question-by-option dot matrix with a count per option and
a near-black verdict panel; right, the wiring each option implies: a point-to-point mesh with its link count above
the same apps and systems wired through one hub (options-comparison)."""
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

prs, s, th = open_lifted("DL39")
VARIANT = "matrix-and-wiring-arithmetic"
P, R = txt.Para, txt.Run

# The source's eyebrow, title rule, page number and pastel hub go (no footer, ruling 12). Its composition stays:
# a coverage matrix left, a solid header over each half, two wiring cards right with the arithmetic beside each
# drawing. Every shape is redrawn flat in the kit so the mesh and the arrows land on what they join and the type
# clears the floor with room (the source's pill and column labels sat at 8pt).
for sh in list(s.shapes):
    if sh.name != "dev.3":
        sh._element.getparent().remove(sh._element)

rename(s, "dev.3", "slot.title")
move(s, "slot.title", 0.50, 0.13, 12.40, 0.40)                   # the kit's wide title geometry, 21pt, one line
bp = find(s, "slot.title")._element.find(".//" + qn("a:bodyPr"))
for k in ("lIns", "tIns", "rIns", "bIns"):
    bp.set(k, "0")
text(s, "slot.title", [P(tuple(txt.title_runs(
    "One shared hub answers every service question with 14 links, not 48", ("One shared hub",))))],
    th, size=21, bold=True, anchor="middle")


def tb(box, paras, name, bg, anchor="top"):
    txt.textbox(s, box, paras, name, th, anchor=anchor, background=bg)


X0, X1, Y0, Y1 = 0.50, 12.90, 0.85, 6.84
LW = 5.55                                                       # the left half; the right takes the rest
DIV = X0 + LW + 0.20
RX = DIV + 0.20
RW = X1 - RX
HEAD_H, TOP = 0.38, Y0 + 0.38 + 0.14

for nm, (hx, hw, lab) in (("left", (X0, LW, "Which option answers each question")),
                          ("right", (RX, RW, "What each option takes to wire up"))):
    prims.block(s, Box(hx, Y0, hw, HEAD_H), fill="accent", radius_in=0.05, name="struct.%s.head" % nm, theme=th)
    tb(Box(hx + 0.16, Y0 + 0.04, hw - 0.32, HEAD_H - 0.08), [P((R(lab, "on-accent", bold=True, size=13),))],
       "slot.%s.head" % nm, "accent", anchor="middle")
prims.hairline(s, (DIV, TOP), (DIV, Y1), role="hairline", name="struct.divider", theme=th)

# --- left: the question-by-option matrix -------------------------------------------------------------------------
VERDICT_H = 1.06
MAT = Box(X0, TOP, LW, Y1 - VERDICT_H - 0.16 - TOP)
prims.card(s, MAT, fill="paper", line="rule-strong", name="struct.matrix", theme=th)
PAD = 0.22
LAB_X, COL0 = X0 + PAD, X0 + 2.40
COL_W = (X0 + LW - PAD - COL0) / 3
OPTS = (("headphones", "Tickets"), ("receipt", "Billing"), ("network", "Shared hub"))
hy = TOP + 0.16
for c, (g, lab) in enumerate(OPTS, 1):
    cx = COL0 + (c - 0.5) * COL_W
    icon(s, "slot.option.%d.icon" % c, g, cx - 0.15, hy, 0.30, th, role="accent")
    tb(Box(cx - COL_W / 2, hy + 0.36, COL_W, 0.24), [P((R(lab, "ink-deep", bold=True, size=11),), align="center")],
       "slot.option.%d.name" % c, "paper", anchor="middle")
r0 = hy + 0.70
prims.hairline(s, (LAB_X, r0), (X0 + LW - PAD, r0), role="rule-strong", name="struct.matrix.rule.0", theme=th)
QUESTIONS = [("Open tickets for one customer", (1, 3)),
             ("Invoices disputed this month", (2, 3)),
             ("Refund time by product line", (2, 3)),
             ("Customers with a ticket and a dispute", (3,)),
             ("Repeat callers after a credit note", (3,))]
TOT_H = 0.50
RP = (MAT.y + MAT.h - TOT_H - 0.10 - r0) / len(QUESTIONS)
for r, (q, cols) in enumerate(QUESTIONS, 1):
    ry = r0 + (r - 1) * RP
    tb(Box(LAB_X, ry + (RP - 0.44) / 2, COL0 - LAB_X - 0.10, 0.44), [P((R(q, "ink", size=12),), line_spacing=0.95)],
       "slot.question.%d" % r, "paper", anchor="middle")
    for c in cols:
        cx = COL0 + (c - 0.5) * COL_W
        prims.circle(s, Box(cx - 0.09, ry + RP / 2 - 0.09, 0.18, 0.18), fill="accent",
                     name="struct.mark.%d.%d" % (r, c), theme=th)
    if r < len(QUESTIONS):
        prims.hairline(s, (LAB_X, ry + RP), (X0 + LW - PAD, ry + RP), role="hairline",
                       name="struct.matrix.rule.%d" % r, theme=th)
ty = r0 + len(QUESTIONS) * RP
prims.hairline(s, (LAB_X, ty), (X0 + LW - PAD, ty), role="rule-strong", name="struct.matrix.rule.total", theme=th)
tb(Box(LAB_X, ty + 0.08, COL0 - LAB_X - 0.10, TOT_H - 0.12), [P((R("Questions answered", "ink-muted", size=11),))],
   "slot.total.label", "paper", anchor="middle")
for c in range(1, 4):
    n = sum(1 for _, cols in QUESTIONS if c in cols)
    cx = COL0 + (c - 0.5) * COL_W
    tb(Box(cx - COL_W / 2, ty + 0.08, COL_W, TOT_H - 0.12),
       [P((R("%d of %d" % (n, len(QUESTIONS)), "accent-ink" if c == 3 else "ink-deep", bold=True, size=14),),
          align="center")], "slot.total.%d" % c, "paper", anchor="middle")

VB = Box(X0, Y1 - VERDICT_H, LW, VERDICT_H)
prims.block(s, VB, fill="ink-deep", radius_in=0.05, name="struct.verdict", theme=th)
tb(Box(VB.x + PAD, VB.y + 0.16, VB.w - 2 * PAD, 0.30),
   [P((R("Only the shared hub answers all five", "accent-bright", bold=True, size=15),))],
   "slot.verdict.head", "ink-deep", anchor="middle")
tb(Box(VB.x + PAD, VB.y + 0.50, VB.w - 2 * PAD, 0.42),
   [P((R("Each system answers its own questions, and neither sees one customer across both",
         "paper", size=12),), line_spacing=0.95)], "slot.verdict.body", "ink-deep", anchor="top")

# --- right: the wiring each option implies ------------------------------------------------------------------------
CH = (Y1 - TOP - 0.16) / 2
SYSTEMS = ("Tickets", "Billing", "Orders", "CRM", "Telephony", "Documents")
APPS = 8
DOT, DOT_X = 0.10, RX + 0.30
PILL_W, PILL_H = 1.10, 0.27
NUMBERS = {}
STAT_X = RX + 3.62
STAT_W = X1 - 0.24 - STAT_X


def wiring_card(i, y, label, sub):
    prims.card(s, Box(RX, y, RW, CH), fill="paper", line="rule-strong", name="struct.wiring.%d" % i, theme=th)
    tb(Box(RX + 0.22, y + 0.14, 2.70, 0.30), [P((R(label, "accent-ink", bold=True, size=14),))],
       "slot.wiring.%d.label" % i, "paper", anchor="middle")
    tb(Box(RX + 3.00, y + 0.14, RW - 3.24, 0.30), [P((R(sub, "ink-muted", bold=True, size=11),))],
       "slot.wiring.%d.sub" % i, "paper", anchor="middle")
    lo, hi = y + 0.62, y + CH - 0.20                                 # the drawing's vertical span
    dots = [lo + (hi - lo) * k / (APPS - 1) for k in range(APPS)]
    pills = [lo + (hi - lo) * k / (len(SYSTEMS) - 1) for k in range(len(SYSTEMS))]
    return dots, pills


def dot_col(i, ys, role):
    for k, cy in enumerate(ys, 1):
        prims.circle(s, Box(DOT_X - DOT / 2, cy - DOT / 2, DOT, DOT), fill=role,
                     name="struct.wiring.%d.app.%d" % (i, k), theme=th)


def pill_col(i, x, ys):
    for k, (cy, nm) in enumerate(zip(ys, SYSTEMS), 1):
        prims.pill(s, Box(x, cy - PILL_H / 2, PILL_W, PILL_H), nm, fill="card", pt=10,
                   name="slot.wiring.%d.system.%d" % (i, k), theme=th)


# card 1: point to point, every app wired to every system
y1 = TOP
dots, pills = wiring_card(1, y1, "Point to point", "%d apps, %d systems" % (APPS, len(SYSTEMS)))
PX1 = RX + 1.95
dot_col(1, dots, "ink-strong")
pill_col(1, PX1, pills)
n = 0
for a_, dy in enumerate(dots, 1):
    for b_, py in enumerate(pills, 1):
        n += 1
        prims.connect(s, (DOT_X + DOT / 2, dy), (PX1, py), head="none", role="rule-strong", weight_pt=0.5,
                      name="struct.wiring.1.link.%d.%d" % (a_, b_), theme=th)
mid = (dots[0] + dots[-1]) / 2
NUMBERS["slot.wiring.1.stat"] = {"value": str(n), "kind": "illustrative"}
prims.stat(s, Box(STAT_X, mid - 0.70, STAT_W, 1.46), str(n),
           "links to build and secure, %d apps times %d systems" % (APPS, len(SYSTEMS)),
           kind="illustrative", role="ink-deep", pt=40, label_pt=12, basis=False, name="slot.wiring.1.stat",
           theme=th)

# card 2: the same apps and systems, each wired once to the hub
y2 = TOP + CH + 0.16
dots, pills = wiring_card(2, y2, "Through a shared hub", "The same %d apps and %d systems" % (APPS, len(SYSTEMS)))
HUB = Box(RX + 0.90, dots[0] - 0.12, 0.92, dots[-1] - dots[0] + 0.24)
PX2 = HUB.x + HUB.w + 0.40
prims.block(s, HUB, fill="accent", radius_in=0.05, name="struct.hub", theme=th)
tb(Box(HUB.x + 0.04, HUB.y + HUB.h / 2 - 0.26, HUB.w - 0.08, 0.52),
   [P((R("Shared", "on-accent", bold=True, size=12),), align="center"),
    P((R("hub", "on-accent", bold=True, size=12),), align="center")], "slot.hub", "accent", anchor="middle")
dot_col(2, dots, "accent")
pill_col(2, PX2, pills)
for k, dy in enumerate(dots, 1):
    prims.connect(s, (DOT_X + DOT / 2, dy), (HUB.x, dy), head="end", role="accent", weight_pt=1.0,
                  name="struct.wiring.2.in.%d" % k, theme=th)
for k, py in enumerate(pills, 1):
    prims.connect(s, (PX2, py), (HUB.x + HUB.w, py), head="end", role="accent", weight_pt=1.0,
                  name="struct.wiring.2.out.%d" % k, theme=th)
m = APPS + len(SYSTEMS)
mid = (dots[0] + dots[-1]) / 2
NUMBERS["slot.wiring.2.stat"] = {"value": str(m), "kind": "illustrative"}
prims.stat(s, Box(STAT_X, mid - 0.70, STAT_W, 1.46), str(m),
           "links, one per app and one per system, each secured once", kind="illustrative", role="accent-ink",
           pt=40, label_pt=12, basis=False, name="slot.wiring.2.stat", theme=th)
tb(Box(STAT_X, y2 + CH - 0.38, STAT_W, 0.24), [P((R("Illustrative figures", "ink-muted", size=9),), align="right")],
   "slot.basis", "paper", anchor="middle")

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
from deckkit import package, tag  # noqa: E402
tag.tag(prs.slides[0], "options-comparison", VARIANT)
for sh in prs.slides[0].shapes:
    ooxml.finish(sh)
out = WORK / "DL39" / "device.pptx"
package.save(prs, out, title="Device DL39", theme=th, manifest={"numbers": NUMBERS}, overwrite=True,
             date="2026-10-03")
if a.out:
    shutil.copyfile(out, a.out)
