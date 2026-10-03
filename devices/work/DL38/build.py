"""DL38: three peer offer pillars, each under a near-black header with its glyph, a two-line promise, three short
leads and a well holding a native miniature of what the pillar produces: a review table, a planning week and an
override log (offering-pillars)."""
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

prs, s, th = open_lifted("DL38")
VARIANT = "pillar-artifact-wells"
P, R = txt.Para, txt.Run

# The source's spaced-caps kicker per card, its eyebrow and page tag, the pastel well and the left bars on the log
# rows all go (mono kicker, no footer, ruling 12, left-accent rule). The three pillars keep the source's geometry:
# equal columns, promise, rule, three leads, then a well that proves the pillar with a miniature of its output.
# Every shape is redrawn flat in the kit so each well's miniature is native and its text clears the floor.
for sh in list(s.shapes):
    if sh.name != "dev.4":
        sh._element.getparent().remove(sh._element)

rename(s, "dev.4", "slot.title")
move(s, "slot.title", 0.50, 0.13, 12.40, 0.40)                   # the kit's wide title geometry, 21pt, one line
bp = find(s, "slot.title")._element.find(".//" + qn("a:bodyPr"))
for k in ("lIns", "tIns", "rIns", "bIns"):
    bp.set(k, "0")
text(s, "slot.title", [P(tuple(txt.title_runs(
    "Three services turn order history into a plan planners trust", ("Three services",))))],
    th, size=21, bold=True, anchor="middle")

X0, X1, GAP = 0.50, 12.90, 0.28
Y0, Y1 = 0.85, 6.84
W = (X1 - X0 - 2 * GAP) / 3
HEAD_H, PAD = 0.56, 0.22

PILLARS = [
    ("chart-line", "Forecasting service", "Weekly demand forecasts by region and product line",
     ("Trained on three years of orders", "Accuracy tracked against the plan",
      "A named driver behind each swing")),
    ("calendar-days", "Planning service", "A monthly plan redrafted from the forecast each week",
     ("Draft ready for the Monday meeting", "Supply constraints applied first",
      "One version shared by every region")),
    ("list-checks", "Review service", "Every planner override logged with its reason",
     ("Captured in the planning screen", "Reasons coded for monthly review",
      "Repeat overrides retrain the model")),
]


def tb(box, paras, name, bg, anchor="top"):
    txt.textbox(s, box, paras, name, th, anchor=anchor, background=bg)


wells = []
for i, (g, name, head, leads) in enumerate(PILLARS, 1):
    x = X0 + (i - 1) * (W + GAP)
    prims.card(s, Box(x, Y0, W, Y1 - Y0), fill="card", line="hairline", name="struct.pillar.%d" % i, theme=th)
    prims.block(s, Box(x, Y0, W, HEAD_H), fill="ink-deep", name="struct.pillar.%d.head" % i, theme=th)
    icon(s, "slot.pillar.%d.icon" % i, g, x + PAD, Y0 + 0.13, 0.30, th, role="accent-bright")
    tb(Box(x + PAD + 0.44, Y0 + 0.08, W - 2 * PAD - 0.44, HEAD_H - 0.16),
       [P((R(name, "paper", bold=True, size=14),))], "slot.pillar.%d.name" % i, "ink-deep", anchor="middle")
    iw = W - 2 * PAD
    tb(Box(x + PAD, Y0 + HEAD_H + 0.18, iw, 0.64),
       [P((R(head, "ink-deep", bold=True, size=15),), line_spacing=0.95)], "slot.pillar.%d.head" % i, "card",
       anchor="top")
    ry = Y0 + HEAD_H + 0.94
    prims.hairline(s, (x + PAD, ry), (x + W - PAD, ry), role="rule-strong", name="struct.pillar.%d.rule" % i,
                   theme=th)
    for k, lead in enumerate(leads, 1):
        ly = ry + 0.14 + (k - 1) * 0.33
        prims.circle(s, Box(x + PAD + 0.02, ly + 0.10, 0.08, 0.08), fill="accent",
                     name="struct.pillar.%d.dot.%d" % (i, k), theme=th)
        tb(Box(x + PAD + 0.20, ly, iw - 0.20, 0.28), [P((R(lead, "ink", size=12),))],
           "slot.pillar.%d.lead.%d" % (i, k), "card", anchor="middle")
    wy = ry + 0.14 + 3 * 0.33 + 0.16
    well = Box(x + PAD, wy, iw, Y1 - PAD - wy)
    prims.card(s, well, fill="paper", line="rule-strong", name="struct.pillar.%d.well" % i, theme=th)
    wells.append(well)

WP = 0.16                                                         # the well's inner padding


def well_label(i, w, label):
    tb(Box(w.x + WP, w.y + 0.12, w.w - 2 * WP, 0.28), [P((R(label, "accent-ink", bold=True, size=12),))],
       "slot.well.%d.label" % i, "paper", anchor="middle")


# --- well 1: a weekly accuracy review table ----------------------------------------------------------------------
w = wells[0]
well_label(1, w, "Weekly accuracy review")
cx = w.x + WP
cols = [(0.86, "left"), (w.w - 2 * WP - 0.86 - 0.62, "left"), (0.62, "right")]
HEAD = ("Region", "Main driver", "Error")
ROWS = [("North", "Promotion timing", "6%"), ("Central", "Supplier delay", "9%"),
        ("Coastal", "Weather shift", "4%"), ("Export", "Port backlog", "11%")]
hy = w.y + 0.52
x = cx
for c, ((cw, al), h) in enumerate(zip(cols, HEAD), 1):
    tb(Box(x, hy, cw, 0.24), [P((R(h, "ink-muted", size=10),), align=al)], "slot.well.1.col.%d" % c, "paper",
       anchor="middle")
    x += cw
prims.hairline(s, (cx, hy + 0.30), (w.x + w.w - WP, hy + 0.30), role="rule-strong", name="struct.well.1.rule.0",
               theme=th)
RP = 0.44
for r, row in enumerate(ROWS, 1):
    ry = hy + 0.34 + (r - 1) * RP
    x = cx
    for c, ((cw, al), v) in enumerate(zip(cols, row), 1):
        role, bold = ("ink-deep", True) if c == 1 else (("accent-ink", True) if c == 3 else ("ink", False))
        tb(Box(x, ry + 0.06, cw, 0.28), [P((R(v, role, bold=bold, size=11),), align=al)],
           "slot.well.1.cell.%d.%d" % (r, c), "paper", anchor="middle")
        x += cw
    if r < len(ROWS):
        prims.hairline(s, (cx, ry + RP), (w.x + w.w - WP, ry + RP), role="hairline",
                       name="struct.well.1.rule.%d" % r, theme=th)
tb(Box(cx, w.y + w.h - 0.38, w.w - 2 * WP, 0.24), [P((R("Illustrative figures", "ink-muted", size=9),))],
   "slot.well.1.basis", "paper", anchor="middle")

# --- well 2: one planning week as a calendar -------------------------------------------------------------------
w = wells[1]
well_label(2, w, "Planning week")
cx = w.x + WP
LAB_W = 0.76
DAY_W = (w.w - 2 * WP - LAB_W) / 5
hy = w.y + 0.52
for d, day in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri"), 1):
    tb(Box(cx + LAB_W + (d - 1) * DAY_W, hy, DAY_W, 0.24), [P((R(day, "ink-muted", size=10),), align="center")],
       "slot.well.2.day.%d" % d, "paper", anchor="middle")
prims.hairline(s, (cx, hy + 0.30), (w.x + w.w - WP, hy + 0.30), role="rule-strong", name="struct.well.2.rule.0",
               theme=th)
LANES = [("Forecast", 1, 2, "Model run", "accent"), ("Draft", 2, 3, "Drafted", "ink-deep"),
         ("Review", 3, 4, "Edits", "ink-deep"), ("Sign-off", 4, 5, "Agreed", "accent")]
RP = (w.y + w.h - 0.14 - (hy + 0.34)) / len(LANES)               # the lanes fill the well
for r, (lane, d0, d1, what, fill) in enumerate(LANES, 1):
    ry = hy + 0.34 + (r - 1) * RP
    tb(Box(cx, ry + (RP - 0.28) / 2, LAB_W, 0.28), [P((R(lane, "ink-deep", bold=True, size=11),))],
       "slot.well.2.lane.%d" % r, "paper", anchor="middle")
    bx = Box(cx + LAB_W + (d0 - 1) * DAY_W + 0.03, ry + (RP - 0.30) / 2, (d1 - d0 + 1) * DAY_W - 0.06, 0.30)
    prims.block(s, bx, fill=fill, radius_in=0.04, name="struct.well.2.slot.%d" % r, theme=th)
    tb(Box(bx.x + 0.04, bx.y, bx.w - 0.08, bx.h), [P((R(what, prims.ON_FILL[fill], bold=True, size=10),),
                                                     align="center")], "slot.well.2.slot.%d" % r, fill,
       anchor="middle")
    if r < len(LANES):
        prims.hairline(s, (cx, ry + RP), (w.x + w.w - WP, ry + RP), role="hairline",
                       name="struct.well.2.rule.%d" % r, theme=th)

# --- well 3: the override log, each row stamped with its review state -------------------------------------------
w = wells[2]
well_label(3, w, "Override log")
cx = w.x + WP
LOG = [("circle-check", "North, launch week raised", "New stores open that week"),
       ("circle-check", "Central, March cut back", "Supplier confirmed a delay"),
       ("circle-question-mark", "Coastal, June raised", "Reason queried by the lead"),
       ("circle-check", "Export, April held flat", "Port backlog clears in May")]
RP = 0.50
ly0 = w.y + 0.50
for r, (g, lead, why) in enumerate(LOG, 1):
    ry = ly0 + (r - 1) * RP
    icon(s, "slot.well.3.state.%d" % r, g, cx, ry + 0.06, 0.22, th,
         role="accent" if g == "circle-check" else "ink-muted")
    tb(Box(cx + 0.32, ry + 0.02, w.w - 2 * WP - 0.32, 0.22), [P((R(lead, "ink-deep", bold=True, size=11),))],
       "slot.well.3.row.%d.lead" % r, "paper", anchor="middle")
    tb(Box(cx + 0.32, ry + 0.23, w.w - 2 * WP - 0.32, 0.20), [P((R(why, "ink", size=10),))],
       "slot.well.3.row.%d.why" % r, "paper", anchor="middle")
    if r < len(LOG):
        prims.hairline(s, (cx, ry + RP - 0.03), (w.x + w.w - WP, ry + RP - 0.03), role="hairline",
                       name="struct.well.3.rule.%d" % r, theme=th)
# the legend for the two states, a mark plus a short label each
ky = w.y + w.h - 0.38
for k, (g, lab, role) in enumerate((("circle-check", "Accepted", "accent"),
                                    ("circle-question-mark", "Queried", "ink-muted")), 1):
    kx = cx + (k - 1) * 1.20
    icon(s, "slot.well.3.key.%d.icon" % k, g, kx, ky + 0.04, 0.16, th, role=role)
    tb(Box(kx + 0.22, ky, 0.90, 0.24), [P((R(lab, "ink-muted", size=9),))], "slot.well.3.key.%d" % k, "paper",
       anchor="middle")

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
out = save(prs, "DL38", th, archetype="offering-pillars", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
