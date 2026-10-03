"""DL27: twelve numbered candidates plotted on a value by effort field split into four named quadrants, colored by
delivery wave, with a key rail that decodes each wave and number (prioritization-matrix)."""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import prims, text as txt  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL27")
VARIANT = "value-effort-waves"
R, P = txt.Run, txt.Para

# banned chrome: the subtitle sentence, the part counter at top right, the takeaway callout in the rail
for n in ("dev.3", "dev.4", "dev.69", "dev.70", "dev.71"):
    delete(s, n)

# title: one claim, two-tone
rename(s, "dev.2", "slot.title")
move(s, "slot.title", 0.45, 0.28, 12.40, 0.60)
text(s, "slot.title", [P(tuple(txt.title_runs(
    "Three quick wins start next quarter while four bets wait for the platform",
    ("Three quick wins",))))], th, size=22, bold=True, anchor="middle")

# field: four tinted quadrants, faint grid, dashed center cross, an outline frame on top
FX, FY, FW, FH = 0.95, 1.10, 8.20, 5.55
rename(s, "dev.7", "struct.field")                       # the four quadrant tints were one role: one zone
move(s, "struct.field", FX, FY, FW, FH)
prims.set_fill(find(s, "struct.field"), "card", theme=th)
prims.set_line(find(s, "struct.field"), None, theme=th)
for n in ("dev.8", "dev.9", "dev.10"):
    delete(s, n)
for i, n in enumerate(("dev.15", "dev.16", "dev.17", "dev.18", "dev.19", "dev.20", "dev.21", "dev.22"), 1):
    rename(s, n, "struct.grid.%d" % i)
for n in ("struct.grid.3", "struct.grid.4"):              # duplicates of the dashed center cross
    delete(s, n)
for n in ("struct.grid.1", "struct.grid.2", "struct.grid.5", "struct.grid.6"):
    prims.set_line(find(s, n), "hairline-soft", 0.75, theme=th)
for n in ("struct.grid.7", "struct.grid.8"):
    prims.set_line(find(s, n), "rule-strong", 1.0, theme=th, dash="dash")
rename(s, "dev.23", "struct.field.frame")
prims.set_fill(find(s, "struct.field.frame"), None, theme=th)
prims.set_line(find(s, "struct.field.frame"), "hairline", 1.0, theme=th)

QUADS = [("dev.11", "Quick wins", "zap", 1.07, 1.18), ("dev.12", "Strategic bets", "target", 5.17, 1.18),
         ("dev.13", "Fill-ins", "list-checks", 1.07, 3.95), ("dev.14", "Deprioritize", "hourglass", 5.17, 3.95)]
for i, (n, word, g, x, y) in enumerate(QUADS, 1):
    icon(s, "slot.quadrant.%d.icon" % i, g, x + 0.02, y + 0.03, 0.22, th)
    rename(s, n, "slot.quadrant.%d.label" % i)
    move(s, "slot.quadrant.%d.label" % i, x + 0.30, y, 1.80, 0.28)
    text(s, "slot.quadrant.%d.label" % i, [P((R(word, "accent-ink", bold=True, size=11),))], th, size=11,
         background="card", anchor="middle")

# axis names outside the field: value up the left edge, effort along the foot
rename(s, "dev.6", "slot.axis.y")
move(s, "slot.axis.y", 0.00, FY + FH / 2 - 0.15, 1.56, 0.30)
text(s, "slot.axis.y", [P((R("Business value", "ink-strong", bold=True, size=11),), align="center")], th,
     size=11, anchor="middle")
rename(s, "dev.5", "slot.axis.x")
move(s, "slot.axis.x", FX, FY + FH + 0.08, FW, 0.30)
text(s, "slot.axis.x", [P((R("Effort to deliver", "ink-strong", bold=True, size=11),), align="center")], th,
     size=11, anchor="middle")

# axis poles inside the field's foot: they read the effort axis from low to high
for name, word, x, al in (("slot.axis.x.low", "Low effort", FX + 0.12, "left"),
                          ("slot.axis.x.high", "High effort", FX + FW - 1.62, "right")):
    tb = s.shapes.add_textbox(int(x * EMU), int((FY + FH - 0.36) * EMU), int(1.50 * EMU), int(0.28 * EMU))
    tb.name = name
    text(s, name, [P((R(word, "ink", size=10),), align=al)], th, size=10, background="card", anchor="middle")

# waves: fill role of each wave's discs and its key dot, and the text role that reads on it
# (fill, numeral role, ring role, ring dash): solid for committed waves, hollow for later ones, dashed when parked
WAVES = [("accent", "on-accent", "paper", None), ("ink-strong", "paper", "paper", None),
         ("paper", "ink-deep", "ink-strong", None), ("paper", "ink", "rule-strong", "dash")]

# candidates: (disc, numeral, wave, x, y) with x, y the disc's top-left in inches
DISCS = [("dev.24", "dev.25", 0, 1.77, 1.61), ("dev.26", "dev.27", 0, 2.25, 1.98), ("dev.28", "dev.29", 0, 2.72, 2.30),
         ("dev.30", "dev.31", 1, 4.05, 1.49), ("dev.32", "dev.33", 1, 3.58, 2.05), ("dev.34", "dev.35", 1, 4.41, 2.76),
         ("dev.36", "dev.37", 1, 4.25, 3.40),
         ("dev.38", "dev.39", 2, 7.19, 1.38), ("dev.40", "dev.41", 2, 6.68, 2.93), ("dev.44", "dev.45", 2, 3.74, 4.15),
         ("dev.42", "dev.43", 2, 7.51, 4.27),
         ("dev.46", "dev.47", 3, 8.17, 5.62)]
D = 0.34
for i, (disc, num, w, x, y) in enumerate(DISCS, 1):
    fill, ink, ring, dash = WAVES[w]
    rename(s, disc, "struct.disc.%d" % i)
    move(s, "struct.disc.%d" % i, x, y, D, D)
    prims.set_fill(find(s, "struct.disc.%d" % i), fill, theme=th)
    prims.set_line(find(s, "struct.disc.%d" % i), ring, 1.5, theme=th, dash=dash)
    rename(s, num, "slot.disc.%d.num" % i)
    move(s, "slot.disc.%d.num" % i, x, y, D, D)
    text(s, "slot.disc.%d.num" % i, [P((R(str(i), ink, bold=True, size=10),), align="center")], th, size=10,
         background=fill, anchor="middle")

# key rail: a heading, then per wave a dot, a head and one numbered line per candidate
RX, RW = 9.55, 3.30
rename(s, "dev.48", "slot.key.head")
move(s, "slot.key.head", RX, 1.10, RW, 0.30)
text(s, "slot.key.head", [P((R("Candidates by delivery wave", "ink-deep", bold=True, size=12),))], th, size=12,
     anchor="middle")
KEY = [("dev.49", "dev.50", ("dev.51", "dev.52", "dev.53"), "Wave 1, next quarter",
        ("Invoice matching", "Contract clause search", "Service ticket triage")),
       ("dev.54", "dev.55", ("dev.56", "dev.57", "dev.58", "dev.59"), "Wave 2, within two quarters",
        ("Supplier risk alerts", "Demand forecast refresh", "Sales call summaries", "Field visit planning")),
       ("dev.60", "dev.61", ("dev.62", "dev.63", "dev.64", "dev.65"), "Wave 3, after the platform build",
        ("Dynamic pricing engine", "Inventory rebalancing", "Warranty claim screening", "Customer churn model")),
       ("dev.66", "dev.67", ("dev.68",), "Parked for review", ("Autonomous purchasing",))]
y, n0 = 1.52, 1
HEAD, ROW, GAP = 0.30, 0.27, 0.20
for w, (dot, head, rows, h, items) in enumerate(KEY, 1):
    fill, _, ring, dash = WAVES[w - 1]
    rename(s, dot, "struct.key.%d.dot" % w)
    move(s, "struct.key.%d.dot" % w, RX, y + 0.08, 0.15, 0.15)
    prims.set_fill(find(s, "struct.key.%d.dot" % w), fill, theme=th)
    prims.set_line(find(s, "struct.key.%d.dot" % w), None if ring == "paper" else ring, 1.25, theme=th, dash=dash)
    rename(s, head, "slot.key.%d.head" % w)
    move(s, "slot.key.%d.head" % w, RX + 0.25, y, RW - 0.25, HEAD)
    text(s, "slot.key.%d.head" % w, [P((R(h, "ink-deep", bold=True, size=11),))], th, size=11, anchor="middle")
    y += HEAD + 0.02
    for j, (row, item) in enumerate(zip(rows, items), 1):
        slot = "slot.key.%d.item.%d" % (w, j)
        rename(s, row, slot)
        move(s, slot, RX + 0.25, y, RW - 0.25, ROW)
        num = ("%2d" % n0).replace(" ", "\u2007")              # figure space keeps one-digit and two-digit rows aligned
        text(s, slot, [P((R(num, "ink-deep", bold=True, size=11), R("   " + item, "ink", size=11)))], th,
             size=11, anchor="middle")
        y += ROW
        n0 += 1
    y += GAP

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
out = save(prs, "DL27", th, archetype="prioritization-matrix", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
