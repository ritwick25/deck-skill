"""DL01: four decision cards linked by chevrons over a dated milestone rail (the-ask)."""
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
# and the next-step band along the foot (P09): its step moves into the title
for n in ("dev.3", "dev.29", "dev.30", "dev.31", "dev.32", "dev.4", "dev.5", "dev.6", "dev.7"):
    delete(s, n)

# title: one claim, two-tone
rename(s, "dev.2", "slot.title")
move(s, "slot.title", 0.48, 0.36, 12.40, 0.55)
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "Four decisions this month put the forecasting pilot live by week fourteen", ("Four decisions",))))],
    th, size=22, bold=True, anchor="middle")

CARDS = [  # (card, number, head, body, glyph, head text, body text)
    ("dev.25", "dev.51", "dev.36", "dev.33", "circle-check", "Endorse the scope",
     "Two product lines and three regions in wave one"),
    ("dev.28", "dev.52", "dev.37", "dev.34", "user-check", "Nominate one owner",
     "A planning lead who signs off accuracy targets"),
    ("dev.26", "dev.53", "dev.38", "dev.35", "database", "Grant data access",
     "Three years of order history ready by week two"),
    ("dev.27", "dev.54", "dev.39", "dev.40", "shield-check", "Agree the gate",
     "Go live once accuracy holds for four weeks"),
]
CARD_Y, CARD_H = 1.20, 2.06
for i, (card, num, head, body, g, h, b) in enumerate(CARDS, 1):
    cx = find(s, card).left / EMU
    rename(s, card, "struct.card.%d" % i)
    rename(s, num, "slot.card.%d.num" % i)
    rename(s, head, "slot.card.%d.head" % i)
    rename(s, body, "slot.card.%d.body" % i)
    move(s, "slot.card.%d.num" % i, cx + 0.15, CARD_Y + 0.22, 0.70, 0.42)
    text(s, "slot.card.%d.num" % i, "%02d" % i, th, size=20, bold=True, role="accent-ink", background="accent-wash")
    move(s, "slot.card.%d.head" % i, cx + 0.15, CARD_Y + 0.92, 2.26, 0.34)
    text(s, "slot.card.%d.head" % i, h, th, size=14, bold=True, role="ink-deep", background="accent-wash")
    move(s, "slot.card.%d.body" % i, cx + 0.15, CARD_Y + 1.26, 2.26, 0.56)
    text(s, "slot.card.%d.body" % i, b, th, size=12, role="ink", background="accent-wash")
    icon(s, "slot.card.%d.icon" % i, g, cx + 1.81, CARD_Y + 0.18, 0.55, th, role="accent")

rename(s, "dev.41", "struct.chevrons")
for k, n in enumerate(range(42, 51), 1):                      # the three double chevrons and their parts
    rename(s, "dev.%d" % n, "struct.chevron.%d.%d" % ((k - 1) // 3 + 1, (k - 1) % 3 + 1))
for st in list(find(s, "struct.chevrons")._element.iter(qn("p:style"))):
    st.getparent().remove(st)
grp = find(s, "struct.chevrons")
grp.top = int((CARD_Y + CARD_H / 2 - grp.height / EMU / 2) * EMU)   # chevrons sit on the cards' midline


def radius(name, r=0.05):
    sh = find(s, name)
    gd = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst") + "/" + qn("a:gd"))
    gd.set("fmla", "val %d" % round(r / (min(sh.width, sh.height) / EMU) * 100000))


for i in range(1, 5):
    move(s, "struct.card.%d" % i, find(s, "struct.card.%d" % i).left / EMU, CARD_Y, 2.56, CARD_H)
    radius("struct.card.%d" % i)

# milestone rail in a card-tone panel, given the height the foot band and the long card bodies held
PANEL_Y, PANEL_H = CARD_Y + CARD_H + 0.14, 2.58
RAIL_Y = PANEL_Y + 1.12
from deckkit import prims  # noqa: E402
from deckkit.canvas import Box  # noqa: E402
panel = prims.card(s, Box(0.45, PANEL_Y, 12.44, PANEL_H), fill="card", line="hairline", radius_in=0.05,
                   name="struct.rail.panel", theme=th)
s.shapes._spTree.remove(panel._element)
s.shapes._spTree.insert(2, panel._element)                     # behind the rail it holds
rename(s, "dev.55", "slot.rail.label")
move(s, "slot.rail.label", 0.62, PANEL_Y + 0.26, 4.00, 0.34)
text(s, "slot.rail.label", "Outcomes by date", th, size=14, bold=True, role="accent-ink", background="card")
rename(s, "dev.12", "struct.rail.line")
move(s, "struct.rail.line", 2.00, RAIL_Y, 9.36, 0)             # dot 1 to dot 4, so the arrow lands on a box
dots = [("dev.22", "dev.23", "dev.24"), ("dev.19", "dev.20", "dev.21"),
        ("dev.16", "dev.17", "dev.18"), ("dev.13", "dev.14", "dev.15")]
for i, trio in enumerate(dots, 1):
    for j, n in enumerate(trio, 1):
        rename(s, n, "struct.rail.dot.%d.%d" % (i, j))
    sh = find(s, "struct.rail.dot.%d.1" % i)                    # the group; its rings follow
    sh.top = int((RAIL_Y - sh.height / EMU / 2) * EMU)
MILES = [("Week 2", "Scope and business owner confirmed"),
         ("Week 6", "First forecasts run beside the current plan"),
         ("Week 10", "Accuracy checked against the gate thresholds"),
         ("Week 14", "Planners act on pilot forecasts each month")]
for i, (n, (d, line)) in enumerate(zip(("dev.8", "dev.9", "dev.10", "dev.11"), MILES), 1):
    rename(s, n, "slot.milestone.%d" % i)
    sh = find(s, "slot.milestone.%d" % i)
    move(s, "slot.milestone.%d" % i, sh.left / EMU, RAIL_Y + 0.26, 2.50, 0.90)
    text(s, "slot.milestone.%d" % i, [
        txt.Para((txt.Run(d, "ink-deep" if i == 1 else "accent-ink", bold=True, size=14),), align="center"),
        txt.Para((txt.Run(line, "ink", size=12),), align="center", space_before=3)], th, size=12, background="card")

out = save(prs, "DL01", th, archetype="the-ask", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
