"""DL01: four decision cards linked by chevrons, a dated milestone rail, a next-step band (the-ask)."""
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

prs, s, th = open_lifted("DL01")
VARIANT = "decision-cards-rail"

# chrome the house rules ban: the subtitle and the caps kicker on every card
for n in ("dev.3", "dev.29", "dev.30", "dev.31", "dev.32"):
    delete(s, n)

# title: one claim, two-tone
rename(s, "dev.2", "slot.title")
move(s, "slot.title", 0.48, 0.30, 12.40, 0.50)
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "Four decisions this month put the forecasting pilot live by week fourteen", ("Four decisions",))))],
    th, size=22, bold=True, anchor="middle")

CARDS = [  # (card, number, head, body, glyph)
    ("dev.25", "dev.51", "dev.36", "dev.33", "circle-check", "Endorse the pilot scope",
     "Approve two product lines and three regions as the first wave. Any later change to scope, "
     "budget or timing goes to the steering group for a decision within a week."),
    ("dev.28", "dev.52", "dev.37", "dev.34", "user-check", "Nominate one owner",
     "Name one planning lead who signs off accuracy targets, settles disputed numbers and chairs the "
     "weekly review with the delivery team, with a deputy named for cover."),
    ("dev.26", "dev.53", "dev.38", "dev.35", "database", "Assign data access",
     "Grant read access to three years of shipment, order and promotion history so model training "
     "starts in week two, with the data steward approving new sources."),
    ("dev.27", "dev.54", "dev.39", "dev.40", "shield-check", "Agree the go-live gate",
     "Set the accuracy and bias thresholds the pilot must clear for four straight weeks before "
     "planners act on its numbers. A missed threshold extends the pilot by one month."),
]
for i, (card, num, head, body, g, h, b) in enumerate(CARDS, 1):
    cx = find(s, card).left / EMU
    rename(s, card, "struct.card.%d" % i)
    rename(s, num, "slot.card.%d.num" % i)
    rename(s, head, "slot.card.%d.head" % i)
    rename(s, body, "slot.card.%d.body" % i)
    text(s, "slot.card.%d.num" % i, "%02d" % i, th, role="accent-ink", background="accent-wash")
    move(s, "slot.card.%d.head" % i, cx + 0.15, 1.84, 2.26, 0.44)
    text(s, "slot.card.%d.head" % i, h, th, size=13, bold=True, role="ink-deep", background="accent-wash")
    move(s, "slot.card.%d.body" % i, cx + 0.15, 2.30, 2.26, 1.52)
    text(s, "slot.card.%d.body" % i, b, th, size=12, role="ink", background="accent-wash")
    icon(s, "slot.card.%d.icon" % i, g, cx + 1.86, 1.30, 0.50, th, role="accent")

rename(s, "dev.41", "struct.chevrons")
for k, n in enumerate(range(42, 51), 1):                      # the three double chevrons and their parts
    rename(s, "dev.%d" % n, "struct.chevron.%d.%d" % ((k - 1) // 3 + 1, (k - 1) % 3 + 1))
for st in list(find(s, "struct.chevrons")._element.iter(qn("p:style"))):
    st.getparent().remove(st)


def radius(name, r=0.05):
    sh = find(s, name)
    gd = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst") + "/" + qn("a:gd"))
    gd.set("fmla", "val %d" % round(r / (min(sh.width, sh.height) / EMU) * 100000))


for i in range(1, 5):
    move(s, "struct.card.%d" % i, find(s, "struct.card.%d" % i).left / EMU, 1.12, 2.56, 2.78)
    radius("struct.card.%d" % i)

# milestone rail
rename(s, "dev.55", "slot.rail.label")
move(s, "slot.rail.label", 0.45, 4.28, 4.00, 0.30)
text(s, "slot.rail.label", "Outcomes by date", th, size=14, bold=True, role="accent-ink")
rename(s, "dev.12", "struct.rail.line")
move(s, "struct.rail.line", 2.00, 4.88, 9.36, 0)               # dot 1 to dot 4, so the arrow lands on a box
dots = [("dev.22", "dev.23", "dev.24"), ("dev.19", "dev.20", "dev.21"),
        ("dev.16", "dev.17", "dev.18"), ("dev.13", "dev.14", "dev.15")]
for i, trio in enumerate(dots, 1):
    for j, n in enumerate(trio, 1):
        rename(s, n, "struct.rail.dot.%d.%d" % (i, j))
MILES = [("Week 2", "Scope and business owner confirmed"),
         ("Week 6", "First forecasts run beside the current plan"),
         ("Week 10", "Accuracy checked against the gate thresholds"),
         ("Week 14", "Planners act on pilot forecasts each month")]
for i, (n, (d, line)) in enumerate(zip(("dev.8", "dev.9", "dev.10", "dev.11"), MILES), 1):
    rename(s, n, "slot.milestone.%d" % i)
    text(s, "slot.milestone.%d" % i, [
        txt.Para((txt.Run(d, "ink-deep" if i == 1 else "accent-ink", bold=True, size=12),), align="center"),
        txt.Para((txt.Run(line, "ink", size=11),), align="center", space_before=2)], th, size=12)

# next-step band: dark label tab, glyph, one line
rename(s, "dev.4", "struct.band")
_bp = find(s, "struct.band")._element.find(qn("p:spPr"))       # the band takes the cards' wash and outline
_cp = find(s, "struct.card.1")._element.find(qn("p:spPr"))
for tag in ("a:solidFill", "a:ln"):
    old = _bp.find(qn(tag))
    new = copy.deepcopy(_cp.find(qn(tag)))
    if old is not None:
        old.addprevious(new)
        _bp.remove(old)
    else:
        _bp.find(qn("a:prstGeom")).addnext(new) if tag == "a:solidFill" else _bp.find(qn("a:solidFill")).addnext(new)
radius("struct.band")
rename(s, "dev.6", "struct.band.tab")
rename(s, "dev.7", "slot.band.label")
rename(s, "dev.5", "slot.band.body")
text(s, "slot.band.label", "Next step", th, role="paper", bold=True, background="ink-deep")
icon(s, "slot.band.icon", "list-checks", 1.60, 6.18, 0.33, th, role="paper")
move(s, "slot.band.body", 2.31, 6.20, 10.40, 0.30)
text(s, "slot.band.body", "Steering group signs the scope note on Friday, and data access requests open the "
     "following Monday", th, size=12, role="ink", anchor="middle",
     background="accent-wash")

out = save(prs, "DL01", th, archetype="the-ask", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
