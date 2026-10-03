"""DL11: a quarter and month grid over a phase lane, a milestone axis whose gates and checkpoints drop their labels
above and below the line, and a per-quarter stat row that closes on the target quarter (gantt)."""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import text as txt  # noqa: E402
from deckkit.prims import set_fill, set_line  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL11")
VARIANT = "phase-lane-milestone-axis-stat-row"

# chrome the house rules ban: the foot sentence, the foot band and its sentence; the disc's placeholder numeral
for n in ("dev.83", "dev.84", "dev.85", "dev.44"):
    delete(s, n)


def P(runs, align=None):
    return txt.Para(tuple(runs), align=align) if align else txt.Para(tuple(runs))


R = txt.Run

# title: one claim, two-tone
rename(s, "dev.86", "slot.title")
move(s, "slot.title", 0.50, 0.36, 12.33, 0.62)
text(s, "slot.title", [P(txt.title_runs(
    "Every region runs the new planning process within five quarters", ("five quarters",)))],
    th, size=22, bold=True, anchor="middle")

# period header: five quarters over fifteen months
QUARTERS = ("Q1 2027", "Q2 2027", "Q3 2027", "Q4 2027", "Q1 2028")
for i, q in enumerate(QUARTERS, 1):
    fill, lab = "dev.%d" % (2 * i), "dev.%d" % (2 * i + 1)
    rename(s, fill, "struct.quarter.%d" % i)
    rename(s, lab, "slot.quarter.%d" % i)
    x = find(s, "struct.quarter.%d" % i).left / EMU
    for n in ("struct.quarter.%d" % i, "slot.quarter.%d" % i):
        move(s, n, x, 1.30, 1.94, 0.34)
    set_fill(find(s, "struct.quarter.%d" % i), "ink-strong", theme=th)
    text(s, "slot.quarter.%d" % i, [P((R(q, "paper", bold=True, size=11),), align="center")], th, size=11,
         anchor="middle", background="ink-strong")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar")
for i, m in enumerate(MONTHS, 1):
    fill, lab = "dev.%d" % (10 + 2 * i), "dev.%d" % (11 + 2 * i)
    rename(s, fill, "struct.month.%d" % i)
    rename(s, lab, "slot.month.%d" % i)
    x = find(s, "struct.month.%d" % i).left / EMU
    for n in ("struct.month.%d" % i, "slot.month.%d" % i):
        move(s, n, x, 1.66, 0.64, 0.30)
    set_fill(find(s, "struct.month.%d" % i), "card", theme=th)
    text(s, "slot.month.%d" % i, [P((R(m, "ink", size=9),), align="center")], th, size=9, anchor="middle",
         background="card")

# lane 1: the phase tab and its two bars
rename(s, "dev.42", "struct.lane.1.tab")
move(s, "struct.lane.1.tab", 0.50, 2.12, 2.35, 0.70)
set_fill(find(s, "struct.lane.1.tab"), "accent", theme=th)
rename(s, "dev.43", "struct.lane.1.disc")
move(s, "struct.lane.1.disc", 0.66, 2.25, 0.44, 0.44)
set_fill(find(s, "struct.lane.1.disc"), "paper", theme=th)
icon(s, "slot.lane.1.icon", "calendar-check", 0.75, 2.34, 0.26, th, role="accent")
rename(s, "dev.45", "slot.lane.1.label")
move(s, "slot.lane.1.label", 1.20, 2.12, 1.58, 0.70)
text(s, "slot.lane.1.label", [P((R("Program phases", "on-accent", bold=True, size=12),))], th, size=12,
     anchor="middle", background="accent")
PHASES = (("dev.46", "dev.47", "accent-wash", "Build and pilot in two regions", 3.00, 5.85),
          ("dev.48", "dev.49", "accent-tint", "Scale to every region", 8.95, 3.85))
for i, (bar, lab, role, words, bx, bw) in enumerate(PHASES, 1):
    rename(s, bar, "struct.phase.%d.bar" % i)
    rename(s, lab, "slot.phase.%d.label" % i)
    b = find(s, "struct.phase.%d.bar" % i)
    move(s, "struct.phase.%d.bar" % i, bx, 2.12, bw, 0.70)
    set_fill(b, role, theme=th)
    set_line(b, "hairline", 0.75, theme=th)
    move(s, "slot.phase.%d.label" % i, b.left / EMU + 0.10, 2.12, b.width / EMU - 0.20, 0.70)
    text(s, "slot.phase.%d.label" % i, [P((R(words, "ink-deep", bold=True, size=13),))], th, size=13,
         anchor="middle", background=role)

# lane 2: the milestone axis, gates in the brand colour and checkpoints in ink, each named as one or the other
rename(s, "dev.50", "slot.lane.2.label")
move(s, "slot.lane.2.label", 0.50, 3.05, 2.35, 0.30)
text(s, "slot.lane.2.label", [P((R("Milestones and gates", "accent-ink", bold=True, size=11),))], th, size=11)
rename(s, "dev.51", "struct.axis")
move(s, "struct.axis", 3.00, 4.13, 9.80, 0.02)
set_fill(find(s, "struct.axis"), "hairline", theme=th)
LINE_Y, ABOVE_Y, BELOW_Y, LAB_H = 4.14, 3.02, 4.66, 0.56
MILESTONES = (  # connector, label, diamond, above, gate, head, line
    ("dev.52", "dev.53", "dev.54", False, False, "Baseline checkpoint", "Cycle times measured"),
    ("dev.55", "dev.56", "dev.57", True, True, "Pilot go gate", "Two regions go live"),
    ("dev.58", "dev.59", "dev.60", False, True, "Scale gate", "Pilot savings signed off"),
    ("dev.61", "dev.62", "dev.63", True, False, "Year-end checkpoint", "Eight regions live"),
    ("dev.64", "dev.65", "dev.66", False, True, "Rollout gate", "All twelve regions live"),
)
for i, (cx, lab, dia, above, gate, head, line) in enumerate(MILESTONES, 1):
    rename(s, dia, "struct.milestone.%d.mark" % i)
    rename(s, cx, "struct.milestone.%d.drop" % i)
    rename(s, lab, "slot.milestone.%d.label" % i)
    d = find(s, "struct.milestone.%d.mark" % i)
    side = 0.22 if i == 5 else 0.16
    xc = d.left / EMU + d.width / EMU / 2
    move(s, "struct.milestone.%d.mark" % i, xc - side / 2, LINE_Y - side / 2, side, side)
    set_fill(d, "accent" if gate else "ink-strong", theme=th)
    set_line(d, None, theme=th)
    if above:
        y0, y1, ly = ABOVE_Y + LAB_H + 0.01, LINE_Y - side / 2, ABOVE_Y
    else:
        y0, y1, ly = LINE_Y + side / 2, BELOW_Y - 0.01, BELOW_Y
    move(s, "struct.milestone.%d.drop" % i, xc, y0, 0, y1 - y0)
    set_line(find(s, "struct.milestone.%d.drop" % i), "rule-strong", 0.75, theme=th, dash="dash")
    if i == 5:  # the last label hangs right-aligned from the grid's right edge
        lx, lw, al = 10.83, 2.00, "right"
    else:
        lx, lw, al = xc - 1.10, 2.20, "center"
    move(s, "slot.milestone.%d.label" % i, lx, ly, lw, LAB_H)
    text(s, "slot.milestone.%d.label" % i,
         [P((R(head, "ink-deep", bold=True, size=10.5),), align=al), P((R(line, "ink", size=10.5),), align=al)],
         th, size=10.5, anchor="bottom" if above else "top")

# lane 3: one planned count per quarter, named as a target in its row label, the final quarter on the dark card
rename(s, "dev.82", "slot.lane.3.label")
move(s, "slot.lane.3.label", 0.50, 5.62, 2.35, 0.30)
text(s, "slot.lane.3.label", [P((R("Target regions live", "ink-deep", bold=True, size=11),))], th, size=11)
STATS = (("dev.67", "dev.68", "dev.69", "1", "Design region"),
         ("dev.70", "dev.71", "dev.72", "2", "Pilot pair live"),
         ("dev.73", "dev.74", "dev.75", "4", "Pilot extended"),
         ("dev.76", "dev.77", "dev.78", "8", "Scale wave one"),
         ("dev.79", "dev.80", "dev.81", "12", "Full rollout"))
for i, (card, num, lab, n, words) in enumerate(STATS, 1):
    target = i == len(STATS)
    bg = "ink-strong" if target else "card"
    rename(s, card, "struct.stat.%d" % i)
    rename(s, num, "slot.stat.%d.value" % i)
    rename(s, lab, "slot.stat.%d.label" % i)
    c = find(s, "struct.stat.%d" % i)
    x, w = 3.00 + (i - 1) * 1.98, 1.88  # five equal cards across the grid
    move(s, "struct.stat.%d" % i, x, 5.60, w, 1.05)
    set_fill(c, bg, theme=th)
    set_line(c, "hairline", 0.75, theme=th)
    move(s, "slot.stat.%d.value" % i, x, 5.72, w, 0.46)
    text(s, "slot.stat.%d.value" % i, [P((R(n, "paper" if target else "accent-ink", bold=True, size=14),),
                                         align="center")], th, size=14, anchor="middle", background=bg)
    move(s, "slot.stat.%d.label" % i, x + 0.05, 6.20, w - 0.10, 0.32)
    text(s, "slot.stat.%d.label" % i, [P((R(words, "paper" if target else "ink", size=10.5),), align="center")],
         th, size=10.5, anchor="top", background=bg)

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
out = save(prs, "DL11", th, archetype="gantt", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
