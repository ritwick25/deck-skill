"""DL36: six equal wedges ring a solid brand hub, clockwise arrows drawn on the outer rim, each stage with a glyph in
its wedge and a heading and one line outside it; four flanking panels list what sustains the loop (lifecycle-loop)."""
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

prs, s, th = open_lifted("DL36")
VARIANT = "wedge-ring-panels"

# the subtitle, the tooling foot band (vendor names, a labelled full-width band) and the three pastel side panels
# with their hollow roundels go; the panels are redrawn flat as four equal cards, two per flank
for n in ["dev.%d" % k for k in (3, 4, 5, 6, 7)] + ["dev.%d" % k for k in range(39, 63)]:
    delete(s, n)                                                 # dev.7 is the band's column group, 8 to 13

rename(s, "dev.2", "slot.title")
tb = Box(0.50, 0.13, 12.40, 0.40)                                # the kit's wide title geometry, 21pt, one line
move(s, "slot.title", tb.x, tb.y, tb.w, tb.h)
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "Six controls keep every production model accurate, safe and affordable", ("Six controls",))))],
    th, size=21, bold=True, anchor="middle")
bp = find(s, "slot.title")._element.find(".//" + qn("a:bodyPr"))
for k in ("lIns", "tIns", "rIns", "bIns"):
    bp.set(k, "0")

# the wheel: scaled about its own centre into the height the foot band held
S = 1.15
C0 = (6.665, 3.285)                                             # the lifted wheel's centre
C1 = (6.70, 3.86)                                               # the content band's centre


def scale_xy(x, y):
    return C1[0] + (x - C0[0]) * S, C1[1] + (y - C0[1]) * S


def scale_shape(name):
    sh = find(s, name)
    x, y = scale_xy(sh.left / EMU, sh.top / EMU)
    sh.left, sh.top = int(x * EMU), int(y * EMU)
    sh.width, sh.height = int(sh.width * S), int(sh.height * S)


# (group, wedge, arrowhead, label, picture box of its icon, stage, line, glyph, label side)
STAGES = [
    ("dev.14", "dev.15", "dev.16", "dev.33", (7.076, 1.814, 0.433), "Assess", "Readiness, standards and gaps",
     "file-search", "right"),
    ("dev.29", "dev.30", "dev.31", "dev.34", (7.832, 3.001, 0.433), "Deploy", "Automated release and scaling",
     "rocket", "right"),
    ("dev.26", "dev.27", "dev.28", "dev.35", (7.317, 4.271, 0.433), "Monitor", "Drift, health and spend",
     "activity", "right"),
    ("dev.23", "dev.24", "dev.25", "dev.36", (5.757, 4.293, 0.433), "Evaluate", "Accuracy against agreed tests",
     "clipboard-check", "left"),
    ("dev.20", "dev.21", "dev.22", "dev.37", (4.987, 3.079, 0.433), "Govern", "Policy, access and audit trail",
     "shield-check", "left"),
    ("dev.17", "dev.18", "dev.19", "dev.38", (5.677, 1.816, 0.524), "Improve", "Retrain and tune on evidence",
     "refresh-cw", "left"),
]
# label boxes (x, y, w, h) set by hand beside each wedge's outer rim, clear of the rim and the flanking panels
LABELS = {
    "Assess": (8.42, 1.18, 2.25, 0.66),
    "Deploy": (9.26, 3.42, 1.42, 0.90),
    "Monitor": (8.42, 5.70, 2.25, 0.66),
    "Evaluate": (2.72, 5.70, 2.20, 0.66),
    "Govern": (2.80, 3.42, 1.38, 0.90),
    "Improve": (2.72, 1.18, 2.20, 0.66),
}
for i, (grp, wedge, head, lab, pic, stage, line, g, side) in enumerate(STAGES, 1):
    rename(s, grp, "struct.stage.%d" % i)
    rename(s, wedge, "struct.stage.%d.wedge" % i)
    rename(s, head, "struct.stage.%d.arrowhead" % i)
    scale_shape("struct.stage.%d" % i)                          # the group scales its wedge and arrowhead with it
    for part in ("wedge", "arrowhead"):
        ln = find(s, "struct.stage.%d.%s" % (i, part))._element.find(".//" + qn("a:ln"))
        ln.set("w", "15875")                                    # 1.25pt, so the rim arrows carry at projector scale
    px, py, side_in = pic
    cx, cy = scale_xy(px + side_in / 2, py + side_in / 2)
    icon(s, "slot.stage.%d.icon" % i, g, cx - 0.27, cy - 0.27, 0.54, th, role="accent")
    rename(s, lab, "slot.stage.%d.label" % i)
    x, y, w, h = LABELS[stage]
    move(s, "slot.stage.%d.label" % i, x, y, w, h)
    al = "right" if side == "left" else "left"
    text(s, "slot.stage.%d.label" % i, [
        txt.Para((txt.Run(stage, "ink-deep", bold=True, size=13),), align=al),
        txt.Para((txt.Run(line, "ink", size=11),), align=al, space_before=2)], th, size=11)

# the hub: one solid brand disc naming what the loop serves
rename(s, "dev.32", "slot.hub")
scale_shape("slot.hub")
hub = find(s, "slot.hub")
prims.set_fill(hub, "accent", theme=th)
prims.set_line(hub, None, theme=th)
text(s, "slot.hub", [
    txt.Para((txt.Run("Production models", "on-accent", bold=True, size=14),), align="center"),
    txt.Para((txt.Run("Decisions the business runs on", "on-accent", size=11),), align="center", space_before=3)],
    th, size=11, background="accent", anchor="middle")

# four flanking panels, flat cards with a hairline, three capabilities each behind a ringed glyph
PANELS = [
    ("Build and change", (("Prompt and config versions", "file-text"), ("Release pipelines", "git-branch"),
                          ("Controlled experiments", "flask-conical"))),
    ("Data foundations", (("Source data contracts", "database"), ("Lineage and catalog", "workflow"),
                          ("Benchmark sets", "table"))),
    ("Quality and safety", (("Evaluation suites", "list-checks"), ("Data quality checks", "search"),
                            ("Policy and compliance", "scale"))),
    ("Run and optimize", (("Monitoring and alerts", "bell"), ("Incident response", "headphones"),
                          ("Cost and performance", "gauge"))),
]
PW, PY0, PH, GAP = 2.10, 0.95, 2.79, 0.20
for k, (head, items) in enumerate(PANELS, 1):
    col, row = (k - 1) // 2, (k - 1) % 2
    x = 0.50 if col == 0 else 12.90 - PW
    y = PY0 + row * (PH + GAP)
    prims.card(s, Box(x, y, PW, PH), fill="card", line="hairline", radius_in=0.05,
               name="struct.panel.%d" % k, theme=th)
    txt.textbox(s, Box(x + 0.18, y + 0.20, PW - 0.30, 0.34),
                [txt.Para((txt.Run(head, "accent-ink", bold=True, size=12),))],
                "slot.panel.%d.head" % k, th, background="card")
    for j, (label, g) in enumerate(items, 1):
        iy = y + 0.70 + (j - 1) * 0.68
        prims.circle(s, Box(x + 0.18, iy, 0.46, 0.46), fill="paper", line="accent",
                     name="struct.panel.%d.item.%d.ring" % (k, j), theme=th)
        icon(s, "slot.panel.%d.item.%d.icon" % (k, j), g, x + 0.28, iy + 0.10, 0.26, th, role="accent")
        txt.textbox(s, Box(x + 0.76, iy - 0.02, PW - 0.76 - 0.12, 0.50),
                    [txt.Para((txt.Run(label, "ink", size=11),))],
                    "slot.panel.%d.item.%d" % (k, j), th, anchor="middle", background="card")

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
out = save(prs, "DL36", th, archetype="lifecycle-loop", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
