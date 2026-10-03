"""DL45: lane rows across a lever, a target figure, its measure and three phase cells, filled where value lands, over a
near-black benchmark band spanning the grid (coverage-matrix)."""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import prims  # noqa: E402
from deckkit import text as txt  # noqa: E402
from deckkit.text import Para, Run  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL45")
VARIANT = "lane-phase-matrix"
NUMBERS = {}

# chrome the house rules ban: the kicker and folio, the footer pair, the subtitle, the source line and the dark
# next-step band along the foot (P09); the lifted figure texts and chip words, redrawn as kit stats and glyphs
DROP = [2, 3, 4, 5, 7, 94, 95, 96, 86, 87, 89, 90, 92, 93,
        20, 21, 31, 32, 43, 44, 54, 55, 65, 66, 76, 77,
        24, 35, 37, 48, 59, 71, 81, 83]
for n in DROP:
    delete(s, "dev.%d" % n)


def P(t, role="ink", size=11.0, bold=False, align="left", before=0):
    return Para((Run(t, role, bold=bold, size=size),), align=align, space_before=before)


def radius(name, r=0.05):
    sh = find(s, name)
    gd = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst") + "/" + qn("a:gd"))
    if gd is not None:
        gd.set("fmla", "val %d" % round(r / (min(sh.width, sh.height) / EMU) * 100000))


# title: one claim, two-tone, at the kit title geometry
rename(s, "dev.6", "slot.title")
move(s, "slot.title", 0.50, 0.13, 12.40, 0.40)
text(s, "slot.title", [Para(tuple(txt.title_runs(
    "Six workstreams carry the margin case, each with a figure and a window", ("Six workstreams",))))],
    th, size=21, bold=True, anchor="middle")

# columns across the content band (0.50 to 12.90)
LANE_X, LANE_W = 0.50, 2.12
LEVER_X, LEVER_W = 2.78, 3.28
FIG_X, FIG_W = 6.20, 1.44
MEAS_X, MEAS_W = 7.78, 3.06
CELL_W, CELL_GAP = 0.56, 0.08
CELL_X = [10.98 + k * (CELL_W + CELL_GAP) for k in range(3)]

# header row: each column named once; the figure column's head is the shared basis label (P23)
HEAD_Y, HEAD_H = 0.92, 0.28
HEADS = [("dev.8", "slot.head.lane", LANE_X + 0.14, LANE_W - 0.14, "Lane"),
         ("dev.9", "slot.head.lever", LEVER_X, LEVER_W, "Lever"),
         ("dev.10", "slot.head.figure", FIG_X, FIG_W, prims.basis_label("target")),
         ("dev.11", "slot.head.measure", MEAS_X, MEAS_W, "Measured by")]
for old, new, x, w, t in HEADS:
    rename(s, old, new)
    move(s, new, x, HEAD_Y, w, HEAD_H)
    text(s, new, t, th, size=10, bold=True, role="ink-muted", anchor="bottom")
for k, old in enumerate(("dev.12", "dev.13", "dev.14"), 1):
    nm = "slot.head.phase.%d" % k
    rename(s, old, nm)
    move(s, nm, CELL_X[k - 1] - 0.04, HEAD_Y, CELL_W + 0.08, HEAD_H)
    text(s, nm, [P("Phase %d" % k, "ink-muted", 9, True, "center")], th, size=9, anchor="bottom")
rename(s, "dev.15", "struct.head.rule")
move(s, "struct.head.rule", 0.50, HEAD_Y + HEAD_H + 0.04, 12.40, 0)

# six lane rows: a near-black label block, the lever, a target stat, its measure, three phase cells
ROW_Y, ROW_H, ROW_GAP = 1.32, 0.70, 0.08
ROWS = [  # card, block, lane, lever, measure, cells, glyph, lane text, lever text, value, label, measure text, lands
    ("dev.16", "dev.17", "dev.18", "dev.19", "dev.22", ("dev.23", "dev.25", "dev.26"), "database",
     "Data foundation", "Contracted source feeds, with schema drift stopped at intake", "0",
     "unflagged breaks", "Breaks found after a model has already trained", (1,)),
    ("dev.27", "dev.28", "dev.29", "dev.30", "dev.33", ("dev.34", "dev.36", "dev.38"), "brain",
     "Forecast models", "A scored forecast per account, with its drivers shown", "3x",
     "top-decile precision", "Orders won in the top decile against the current list", (1, 2)),
    ("dev.39", "dev.40", "dev.41", "dev.42", "dev.45", ("dev.46", "dev.47", "dev.49"), "sliders-horizontal",
     "Planning engine", "A single optimizer settles capacity across all product lines", "6%",
     "volume uplift", "Shipped volume in test regions against matched control regions", (2,)),
    ("dev.50", "dev.51", "dev.52", "dev.53", "dev.56", ("dev.57", "dev.58", "dev.60"), "route",
     "Field execution", "Visit schedules ranked by travel cost and account value", "10 to 20%",
     "more selling time", "Customer-facing hours logged per week per seller", (2,)),
    ("dev.61", "dev.62", "dev.63", "dev.64", "dev.67", ("dev.68", "dev.69", "dev.70"), "message-square",
     "Digital channel", "Guided messages reach accounts between scheduled visits", "30%",
     "follow-up response", "Replies within ten days of a guided message", (3,)),
    ("dev.72", "dev.73", "dev.74", "dev.75", "dev.78", ("dev.79", "dev.80", "dev.82"), "refresh-cw",
     "Feedback loop", "Visit outcomes retrain models and update seller coaching", "44%",
     "advice accepted", "Share of suggestions sellers act on, by driver, each month", (2, 3)),
]
SH = max(prims.stat_height(s, FIG_W, r[9], r[10], kind="target", pt=16, label_pt=9, basis=False, theme=th)
         for r in ROWS)
assert SH <= ROW_H - 0.08, "row stats need %.2fin more height" % (SH - ROW_H + 0.08)
for i, (card, block, lane, lever, meas, cells, g, lane_t, lever_t, val, lab, meas_t, lands) in enumerate(ROWS, 1):
    y = ROW_Y + (i - 1) * (ROW_H + ROW_GAP)
    rename(s, card, "struct.row.%d" % i)
    move(s, "struct.row.%d" % i, 0.50, y, 12.40, ROW_H)
    prims.set_fill(find(s, "struct.row.%d" % i), "paper", theme=th)
    prims.set_line(find(s, "struct.row.%d" % i), "hairline", 0.75, theme=th)
    radius("struct.row.%d" % i)
    rename(s, block, "struct.row.%d.block" % i)
    move(s, "struct.row.%d.block" % i, LANE_X, y, LANE_W, ROW_H)
    prims.set_fill(find(s, "struct.row.%d.block" % i), "ink-strong", theme=th)
    prims.set_line(find(s, "struct.row.%d.block" % i), None, theme=th)
    radius("struct.row.%d.block" % i)
    icon(s, "slot.row.%d.icon" % i, g, LANE_X + 0.16, y + (ROW_H - 0.34) / 2, 0.34, th, role="paper")
    rename(s, lane, "slot.row.%d.lane" % i)
    move(s, "slot.row.%d.lane" % i, LANE_X + 0.60, y, LANE_W - 0.66, ROW_H)
    text(s, "slot.row.%d.lane" % i, lane_t, th, size=12, bold=True, role="paper", background="ink-strong",
         anchor="middle")
    rename(s, lever, "slot.row.%d.lever" % i)
    move(s, "slot.row.%d.lever" % i, LEVER_X, y, LEVER_W, ROW_H)
    text(s, "slot.row.%d.lever" % i, lever_t, th, size=11, bold=False, role="ink-deep", anchor="middle")
    nm = "slot.row.%d.figure" % i
    prims.stat(s, Box(FIG_X, y + (ROW_H - SH) / 2, FIG_W, SH), val, lab, kind="target", role="accent-ink", pt=16,
               label_pt=9, basis=False, name=nm, theme=th)
    NUMBERS[nm] = {"value": val, "kind": "target"}
    rename(s, meas, "slot.row.%d.measure" % i)
    move(s, "slot.row.%d.measure" % i, MEAS_X, y, MEAS_W, ROW_H)
    text(s, "slot.row.%d.measure" % i, meas_t, th, size=11, bold=False, role="ink", anchor="middle")
    for k, c in enumerate(cells, 1):
        cn = "struct.row.%d.phase.%d" % (i, k)
        rename(s, c, cn)
        cy = y + (ROW_H - 0.42) / 2
        move(s, cn, CELL_X[k - 1], cy, CELL_W, 0.42)
        on = k in lands
        prims.set_fill(find(s, cn), "accent" if on else "card", theme=th)
        prims.set_line(find(s, cn), None if on else "hairline", 0.75, theme=th)
        radius(cn)
        if on:   # the filled cell carries a mark too, so the state survives greyscale
            icon(s, "slot.row.%d.phase.%d.mark" % (i, k), "check", CELL_X[k - 1] + (CELL_W - 0.24) / 2,
                 cy + 0.09, 0.24, th, role="on-accent")

# the benchmark band spanning the grid: near-black, its label the shared basis label for its three figures (P23)
BAND_Y, BAND_H = ROW_Y + 6 * ROW_H + 5 * ROW_GAP + 0.12, 0.80
rename(s, "dev.84", "struct.band")
move(s, "struct.band", 0.50, BAND_Y, 12.40, BAND_H)
prims.set_fill(find(s, "struct.band"), "ink-deep", theme=th)
prims.set_line(find(s, "struct.band"), None, theme=th)
radius("struct.band")
rename(s, "dev.85", "slot.band.label")
move(s, "slot.band.label", 0.70, BAND_Y, 1.90, BAND_H)
text(s, "slot.band.label", prims.basis_label("benchmark"), th, size=12, bold=True, role="paper",
     background="ink-deep", anchor="middle")
BAND = [("4 to 8%", "margin uplift"), ("15 to 25%", "planning effort released"), ("3 to 5%", "more accounts reached")]
PITCH = (12.70 - 2.70) / 3
BH = max(prims.stat_height(s, PITCH - 0.40, v, lab, kind="benchmark", pt=20, label_pt=10, basis=False, theme=th)
         for v, lab in BAND)
for i, (v, lab) in enumerate(BAND, 1):
    nm = "slot.band.%d" % i
    prims.stat(s, Box(2.70 + (i - 1) * PITCH + 0.24, BAND_Y + (BAND_H - BH) / 2, PITCH - 0.40, BH), v, lab,
               kind="benchmark", role="accent-bright", label_role="paper", background="ink-deep", pt=20,
               label_pt=10, basis=False, name=nm, theme=th)
    NUMBERS[nm] = {"value": v, "kind": "benchmark"}
for k, n in enumerate(("dev.88", "dev.91"), 1):
    rename(s, n, "struct.band.rule.%d" % k)
    move(s, "struct.band.rule.%d" % k, 2.70 + k * PITCH, BAND_Y + 0.18, 0, BAND_H - 0.36)
    prims.set_line(find(s, "struct.band.rule.%d" % k), "ink-muted", 0.75, theme=th)

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
from deckkit import package, tag  # noqa: E402
finish(prs.slides[0], th)
tag.tag(prs.slides[0], "coverage-matrix", VARIANT)
for sh in prs.slides[0].shapes:
    ooxml.finish(sh)
out = WORK / "DL45" / "device.pptx"
package.save(prs, out, title="Device DL45", theme=th, manifest={"numbers": NUMBERS}, overwrite=True,
             date="2026-10-03")
if a.out:
    shutil.copyfile(out, a.out)
