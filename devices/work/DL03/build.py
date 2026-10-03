"""DL03: a three-column case study. Starting point on the left, a five-step build flow over enablers and a data
foundation in the middle, reported results as figure cards on a solid rail at the right (case-study)."""
import argparse
import copy
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import text as txt  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL03")
VARIANT = "context-flow-results-rail"

# chrome the house rules ban: the subtitle under the title, the tracker chips and the tag under them
for n in ("dev.21", "dev.30", "dev.31", "dev.32", "dev.33", "dev.34", "dev.35"):
    delete(s, n)



def P(t, role, size, bold=False, before=0, align="center"):
    return txt.Para((txt.Run(t, role, bold=bold, size=size),), align=align, space_before=before)


# title: one claim, two-tone
rename(s, "dev.2", "slot.title")
move(s, "slot.title", 0.48, 0.28, 12.40, 0.56)
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "Weekly demand sensing cut stockouts by a third across twelve plants", ("cut stockouts by a third",))))],
    th, size=22, bold=True, anchor="middle")

# column headers
for n, slot, label in (("dev.3", "slot.context.head", "Starting point"), ("dev.5", "slot.build.head", "What was built")):
    rename(s, n, slot)
    text(s, slot, [P(label, "on-accent", 13, True)], th, size=13, background="accent", anchor="middle")
rename(s, "dev.4", "struct.context.frame")
rename(s, "dev.6", "struct.build.frame")
rename(s, "dev.7", "struct.results.rail")

# context: two figures with glyphs, four short lines, an engagement card
rename(s, "dev.26", "struct.context.divider")
for i, (num, lab, n, l, g, x) in enumerate((("dev.22", "dev.24", "12", "plants", "factory", 0.882),
                                             ("dev.23", "dev.25", "9 wk", "plan lag", "hourglass", 2.031)), 1):
    rename(s, num, "slot.context.fig.%d" % i)
    delete(s, lab)
    cx = find(s, "slot.context.fig.%d" % i).left / EMU
    move(s, "slot.context.fig.%d" % i, cx - 0.14, 2.50, 0.95, 0.62)
    text(s, "slot.context.fig.%d" % i, [P(n, "accent-ink", 15, True), P(l, "ink", 10)], th, size=10)
    icon(s, "slot.context.fig.%d.icon" % i, g, x + 0.03 if i == 1 else x, 1.95, 0.44, th, role="accent")
move(s, "struct.context.divider", 1.69, 2.56, 0, 0.50)

PAINS = ["Monthly forecast built by hand in spreadsheets",
         "One order in eight shipped short",
         "Planners reconciled four separate data sources",
         "Excess stock held to cover forecast error"]
rows = [(3.30, 0.42), (3.84, 0.42), (4.38, 0.42), (4.92, 0.42)]
for i, (n, t, (y, h)) in enumerate(zip(("dev.9", "dev.10", "dev.11", "dev.12"), PAINS, rows), 1):
    rename(s, n, "slot.context.line.%d" % i)
    move(s, "slot.context.line.%d" % i, 0.65, y, 2.08, h)
    text(s, "slot.context.line.%d" % i, PAINS[i - 1], th, size=10, role="ink", anchor="middle")
for i, (n, y) in enumerate(zip(("dev.16", "dev.17", "dev.18"), (3.78, 4.32, 4.86)), 1):
    rename(s, n, "struct.context.rule.%d" % i)
    move(s, "struct.context.rule.%d" % i, 0.65, y, 2.08, 0)

rename(s, "dev.13", "struct.engagement.card")
rename(s, "dev.14", "slot.engagement.head")
rename(s, "dev.15", "slot.engagement.body")
move(s, "slot.engagement.head", 0.63, 5.86, 2.14, 0.26)
text(s, "slot.engagement.head", "Engagement", th, size=12, bold=True, role="accent-ink")
move(s, "slot.engagement.body", 0.63, 6.12, 2.14, 0.48)
text(s, "slot.engagement.body", "Sixteen weeks with one central planning team", th, size=10, role="ink")

# build: scope line, five step discs joined by double chevrons, a one-line step under each
rename(s, "dev.58", "slot.build.scope")
text(s, "slot.build.scope", [P("One weekly planning cycle replaced the monthly spreadsheet forecast", "ink-deep", 10)],
     th, size=10, background="accent-wash", anchor="middle")

STEPS = [("Audit", "Map data sources and forecast error", "file-search"),
         ("Model", "Train demand models on order history", "brain-circuit"),
         ("Sense", "Add weekly orders and promotion signals", "activity"),
         ("Plan", "Review exceptions, not every line", "list-checks"),
         ("Scale", "Roll out plant by plant over six weeks", "rocket")]
fill_accent = copy.deepcopy(find(s, "struct.results.rail")._element.find(qn("p:spPr")).find(qn("a:solidFill")))
for i, (n, disc, (h, b, g)) in enumerate(zip(("dev.59", "dev.60", "dev.61", "dev.62", "dev.63"),
                                             ("dev.68", "dev.69", "dev.70", "dev.71", "dev.72"), STEPS), 1):
    rename(s, disc, "struct.step.%d.disc" % i)
    sp = find(s, "struct.step.%d.disc" % i)._element.find(qn("p:spPr"))
    sp.find(qn("a:prstGeom")).addnext(copy.deepcopy(fill_accent))
    d = find(s, "struct.step.%d.disc" % i)
    dx, dy, dw = d.left / EMU, d.top / EMU, d.width / EMU
    icon(s, "slot.step.%d.icon" % i, g, dx + (dw - 0.36) / 2, dy + (dw - 0.36) / 2, 0.36, th, role="on-accent")
    rename(s, n, "slot.step.%d" % i)
for i, (x0, x1) in enumerate(((3.22, 4.61), (4.61, 6.03), (6.03, 7.45), (7.45, 8.92), (8.92, 10.40)), 1):
    move(s, "slot.step.%d" % i, x0 + 0.06, 3.00, x1 - x0 - 0.12, 1.16)
    h, b, _ = STEPS[i - 1]
    text(s, "slot.step.%d" % i, [P(h, "accent-ink", 11, True), P(b, "ink", 10, before=3)], th, size=10)
for k, n in enumerate(range(64, 68), 1):
    rename(s, "dev.%d" % n, "struct.step.rule.%d" % k)
for k, n in enumerate(range(73, 85)):
    rename(s, "dev.%d" % n, "struct.chevron.%d" % (k // 3 + 1) if k % 3 == 0 else
           "struct.chevron.%d.%d" % (k // 3 + 1, k % 3))
for k in range(1, 5):
    for st in list(find(s, "struct.chevron.%d" % k)._element.iter(qn("p:style"))):
        st.getparent().remove(st)

# enablers: a framed row of five glyph labels
rename(s, "dev.45", "struct.enablers.frame")
rename(s, "dev.46", "slot.enablers.head")
move(s, "struct.enablers.frame", 3.22, 4.38, 7.18, 1.29)
move(s, "slot.enablers.head", 3.40, 4.42, 6.82, 0.26)
text(s, "slot.enablers.head", [P("What made it stick", "accent-ink", 11, True)], th, size=11, anchor="middle")
for k, n in enumerate(range(52, 58), 1):
    rename(s, "dev.%d" % n, "struct.enablers.rule.%d" % k)
ENABLERS = [("Shared data model", "database"), ("Accuracy dashboard", "gauge"), ("Planner playbook", "file-text"),
            ("Weekly review", "calendar-check"), ("Model monitoring", "server-cog")]
for i, (n, (lab, g)) in enumerate(zip(("dev.47", "dev.48", "dev.49", "dev.50", "dev.51"), ENABLERS), 1):
    rename(s, n, "slot.enabler.%d.label" % i)
    x0 = 3.22 + (i - 1) * 1.436
    move(s, "slot.enabler.%d.label" % i, x0 + 0.08, 5.18, 1.28, 0.40)
    text(s, "slot.enabler.%d.label" % i, [P(lab, "ink", 10)], th, size=10, anchor="middle")
    icon(s, "slot.enabler.%d.icon" % i, g, x0 + (1.436 - 0.36) / 2, 4.76, 0.36, th, role="accent")

# foundation: four data inputs over one platform layer
rename(s, "dev.37", "struct.inputs.frame")
for k, n in enumerate(range(42, 45), 1):
    rename(s, "dev.%d" % n, "struct.inputs.rule.%d" % k)
INPUTS = ["Order history", "Promotion calendar", "Inventory positions", "Plant capacity"]
for i, (n, (x0, x1)) in enumerate(zip(("dev.38", "dev.39", "dev.40", "dev.41"),
                                      ((3.22, 4.84), (4.84, 6.51), (6.51, 8.38), (8.38, 10.40))), 1):
    rename(s, n, "slot.input.%d" % i)
    move(s, "slot.input.%d" % i, x0 + 0.06, 5.82, x1 - x0 - 0.12, 0.33)
    text(s, "slot.input.%d" % i, [P(INPUTS[i - 1], "ink-deep", 10, True)], th, size=10, anchor="middle")
rename(s, "dev.36", "slot.platform")
text(s, "slot.platform", [P("Governed cloud data platform", "ink-deep", 10, True)], th, size=10,
     background="card", anchor="middle")

# results: a label, two white figure cards on the solid rail, one closing line
rename(s, "dev.8", "slot.results.head")
move(s, "slot.results.head", 10.91, 1.12, 1.86, 0.32)
text(s, "slot.results.head", [P("Reported results", "on-accent", 13, True)], th, size=13, background="accent",
     anchor="middle")
FIGS = [("dev.19", "dev.27", "33%", "fewer stockouts", "Two quarters after go-live"),
        ("dev.28", "dev.29", "4 pts", "accuracy gain", "Measured at item and week level")]
for i, (card, det, v, lab, d) in enumerate(FIGS, 1):
    rename(s, card, "slot.result.%d" % i)
    rename(s, det, "slot.result.%d.detail" % i)
    c = find(s, "slot.result.%d" % i)
    cy = c.top / EMU
    text(s, "slot.result.%d" % i, [P(v, "accent-ink", 24, True), P(lab, "ink-deep", 11, True, before=2)], th,
         size=11)
    move(s, "slot.result.%d.detail" % i, 11.00, cy + 1.02, 1.68, 0.42)
    text(s, "slot.result.%d.detail" % i, [P(d, "ink", 10)], th, size=10)
rename(s, "dev.20", "slot.results.close")
move(s, "slot.results.close", 10.87, 5.40, 1.94, 0.62)
text(s, "slot.results.close", [P("Planning cycle time fell from five days to two", "on-accent", 11, True)], th,
     size=11, background="accent")

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
out = save(prs, "DL03", th, archetype="case-study", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
