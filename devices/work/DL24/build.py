"""DL24: six source feeders converge through arrows on a three-layer nested hub (foundation, rules, a numbered
service core) that feeds five outcome cards (convergence-hub)."""
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

prs, s, th = open_lifted("DL24")
VARIANT = "nested-core-feeders-outcomes"
R, P = txt.Run, txt.Para

# banned chrome: the title underline, the footer line, the caption sentence along the hub's foot
for n in ("dev.37", "dev.70", "dev.41"):
    delete(s, n)

# title: one claim, two-tone
rename(s, "dev.36", "slot.title")
move(s, "slot.title", 0.38, 0.28, 12.55, 0.60)
text(s, "slot.title", [P(tuple(txt.title_runs(
    "Six sources converge on one governed platform that serves five teams",
    ("one governed platform",))))], th, size=22, bold=True, anchor="middle")

# hub: outer foundation ring, inner rules ring, accent core
for n, slot, box in (("dev.2", "struct.hub.outer", (4.51, 1.07, 4.32, 5.59)),
                     ("dev.3", "struct.hub.inner", (4.84, 1.47, 3.65, 5.08)),
                     ("dev.4", "struct.hub.core", (5.17, 1.97, 3.00, 4.47))):
    rename(s, n, slot)
    move(s, slot, *box)
    find(s, slot).adjustments[0] = 0.05 / min(box[2], box[3])
for n, slot, word, y in (("dev.38", "slot.hub.outer.label", "Shared data foundation", 1.14),
                         ("dev.39", "slot.hub.inner.label", "Common definitions and access", 1.54)):
    rename(s, n, slot)
    move(s, slot, 4.90 if "inner" in slot else 4.58, y, 3.52 if "inner" in slot else 4.17, 0.28)
    text(s, slot, [P((R(word, "accent-ink", bold=True, size=11),), align="center")], th, size=11,
         background="card", anchor="middle")
rename(s, "dev.40", "slot.hub.core.label")
move(s, "slot.hub.core.label", 5.23, 2.04, 2.88, 0.30)
text(s, "slot.hub.core.label", [P((R("Platform services", "on-accent", bold=True, size=12),), align="center")],
     th, size=12, background="accent", anchor="middle")

STEPS = [("dev.48", "dev.49", "dev.50", "Ingest once", "One schedule for every source", "database"),
         ("dev.51", "dev.52", "dev.53", "Standardize", "Shared terms on every record", "layers"),
         ("dev.54", "dev.55", "dev.56", "Govern access", "Role rules at query time", "shield-check"),
         ("dev.57", "dev.58", "dev.59", "Serve by API", "One endpoint per question", "plug")]
RULES = ("dev.5", "dev.6", "dev.7")
Y0, PITCH = 2.66, 0.98
for i, (num, head, body, h, b, g) in enumerate(STEPS, 1):
    y = Y0 + (i - 1) * PITCH
    for n, slot in ((num, "slot.step.%d.num" % i), (head, "slot.step.%d.head" % i), (body, "slot.step.%d.body" % i)):
        rename(s, n, slot)
    move(s, "slot.step.%d.num" % i, 5.24, y + 0.03, 0.46, 0.50)
    move(s, "slot.step.%d.head" % i, 5.73, y, 2.00, 0.28)
    move(s, "slot.step.%d.body" % i, 5.73, y + 0.27, 2.36, 0.28)
    text(s, "slot.step.%d.num" % i, [P((R("%02d" % i, "on-accent", bold=True, size=18),), align="center")], th,
         size=18, background="accent", anchor="middle")
    text(s, "slot.step.%d.head" % i, [P((R(h, "on-accent", bold=True, size=11),))], th, size=11,
         background="accent", anchor="middle")
    text(s, "slot.step.%d.body" % i, [P((R(b, "on-accent", size=10),))], th, size=10, background="accent",
         anchor="middle")
    icon(s, "slot.step.%d.icon" % i, g, 7.80, y + 0.01, 0.26, th, role="on-accent")
for i, n in enumerate(RULES, 1):
    rename(s, n, "struct.step.rule.%d" % i)
    move(s, "struct.step.rule.%d" % i, 5.30, Y0 + i * PITCH - 0.215, 2.73, 0.01)
    prims.set_fill(find(s, "struct.step.rule.%d" % i), "hairline", theme=th)

# feeders: six source cards on the left, an arrow from each landing on the foundation ring
FEEDERS = [("dev.8", "dev.9", "dev.10", "dev.42", "Sales history", "Daily orders, three regions",
            "layout-dashboard"),
           ("dev.11", "dev.12", "dev.13", "dev.43", "Audit records", "Inspections and fixes", "award"),
           ("dev.14", "dev.15", "dev.16", "dev.44", "Product data", "Specs, packs and prices", "book-open"),
           ("dev.17", "dev.18", "dev.19", "dev.45", "Customer master", "Accounts and service tiers", "user-check"),
           ("dev.20", "dev.21", "dev.22", "dev.46", "Partner feeds", "Weekly files from partners", "link"),
           ("dev.23", "dev.24", "dev.25", "dev.47", "Field service logs", "Visit notes, parts used", "list-checks")]
FW = 3.00                                    # feeder card width: the freed gap carries the fan-in
HUB_L, HUB_R = 4.51, 8.83
TRUNK_IN, TRUNK_OUT = 4.00, 9.15
OUT_X = 9.48
ENTRY = {1: 2, 2: 2, 3: 2, 4: 5, 5: 5, 6: 5}  # feeders 1-3 meet at feeder 2's height, 4-6 at feeder 5's
for i, (card, bar, tile, tx, h, b, g) in enumerate(FEEDERS, 1):
    y = 1.07 + (i - 1) * 0.95
    rename(s, card, "struct.feeder.%d" % i)
    move(s, "struct.feeder.%d" % i, 0.50, y, FW, find(s, "struct.feeder.%d" % i).height / EMU)
    rename(s, tile, "struct.feeder.%d.tile" % i)
    prims.set_fill(find(s, "struct.feeder.%d.tile" % i), "paper", theme=th)
    icon(s, "slot.feeder.%d.icon" % i, g, 0.719, y + 0.226, 0.375, th)
    rename(s, tx, "slot.feeder.%d.text" % i)
    move(s, "slot.feeder.%d.text" % i, 1.27, y + 0.06, FW + 0.50 - 1.27 - 0.08, 0.71)
    text(s, "slot.feeder.%d.text" % i, [P((R(h, "accent-ink", bold=True, size=12),)),
                                        P((R(b, "ink", size=10),), space_before=2)], th, size=12,
         background="card", anchor="middle")
    delete(s, bar)                           # the lifted parallel bar: feeders fan in instead (below)

# outcomes: five equal cards on the right, an arrow from the ring landing on each
OUTCOMES = [("dev.26", "dev.27", "dev.60", "dev.61", "Faster market reports", "New reports ship in days instead of quarters",
             "rocket"),
            ("dev.28", "dev.29", "dev.62", "dev.63", "Fewer audit findings", "One lineage trail answers each reviewer",
             "shield-check"),
            ("dev.30", "dev.31", "dev.64", "dev.65", "Steadier forecasts", "Demand models train on one reconciled history",
             "brain"),
            ("dev.32", "dev.33", "dev.66", "dev.67", "One leadership view", "Every review reads the same numbers",
             "monitor"),
            ("dev.34", "dev.35", "dev.68", "dev.69", "Self-serve analysts", "Teams query governed data without tickets",
             "users")]
CH, GAP = 0.974, 0.18
for i, (card, bar, head, body, h, b, g) in enumerate(OUTCOMES, 1):
    y = 1.07 + (i - 1) * (CH + GAP)
    rename(s, card, "struct.outcome.%d" % i)
    move(s, "struct.outcome.%d" % i, OUT_X, y, 12.90 - OUT_X, CH)
    rename(s, head, "slot.outcome.%d.head" % i)
    rename(s, body, "slot.outcome.%d.body" % i)
    icon(s, "slot.outcome.%d.icon" % i, g, OUT_X + 0.153, y + 0.165, 0.292, th)
    move(s, "slot.outcome.%d.head" % i, OUT_X + 0.58, y + 0.15, 2.74, 0.32)
    move(s, "slot.outcome.%d.body" % i, OUT_X + 0.14, y + 0.48, 3.18, 0.34)
    text(s, "slot.outcome.%d.head" % i, [P((R(h, "accent-ink", bold=True, size=12),))], th, size=12,
         background="card", anchor="middle")
    text(s, "slot.outcome.%d.body" % i, [P((R(b, "ink", size=10),))], th, size=10, background="card",
         anchor="middle")
    delete(s, bar)                           # outcomes fan out of one exit point instead (below)


def fy(i):
    sh = find(s, "struct.feeder.%d" % i)
    return (sh.top + sh.height / 2) / EMU


# fan in: each feeder runs to a trunk beside the hub, the trunk carries three feeders to one entry point; the
# three arrowheads of an entry coincide, so the eye reads three sources becoming one stream
for i in range(1, 7):
    y0, y1 = fy(i), fy(ENTRY[i])
    pts = [(0.50 + FW, y0), (HUB_L, y1)] if abs(y0 - y1) < 1e-6 else \
        [(0.50 + FW, y0), (TRUNK_IN, y0), (TRUNK_IN, y1), (HUB_L, y1)]
    prims.elbow(s, pts, role="accent", weight_pt=1.25, name="struct.feeder.%d.arrow" % i, theme=th)
# fan out: one exit point on the hub's right edge branches to every outcome
core = find(s, "struct.hub.outer")
EXIT = (core.top + core.height / 2) / EMU
for i in range(1, 6):
    sh = find(s, "struct.outcome.%d" % i)
    yo = (sh.top + sh.height / 2) / EMU
    pts = [(HUB_R, EXIT), (OUT_X, yo)] if abs(yo - EXIT) < 1e-6 else \
        [(HUB_R, EXIT), (TRUNK_OUT, EXIT), (TRUNK_OUT, yo), (OUT_X, yo)]
    prims.elbow(s, pts, role="accent", weight_pt=1.25, name="struct.outcome.%d.arrow" % i, theme=th)

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
out = save(prs, "DL24", th, archetype="convergence-hub", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
