"""DL33: four agenda parts as a two-by-two grid, a giant numeral leading each part beside its heading, a rule and
three scope lines; one part is lit in solid brand to mark where the session stands (agenda, section-divider)."""
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

prs, s, th = open_lifted("DL33")
VARIANT = "lit-quadrant-grid"

# the source's tiles carry gradients, a soft shadow and right-aligned headings; every tile is redrawn flat in the
# kit (ruling 12: the lit part solid brand, the rest card with a hairline) and every text sits on one left edge
for n in range(3, 23):
    delete(s, "dev.%d" % n)

rename(s, "dev.2", "slot.title")
tb = Box(0.50, 0.13, 12.40, 0.40)                                # the kit's wide title geometry, 21pt, one line
move(s, "slot.title", tb.x, tb.y, tb.w, tb.h)
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "Four parts from planning baseline to gated pilot", ("Four parts",))))], th, size=21, bold=True,
    anchor="middle")
bp = find(s, "slot.title")._element.find(".//" + qn("a:bodyPr"))
for k in ("lIns", "tIns", "rIns", "bIns"):
    bp.set(k, "0")

PARTS = [
    ("Planning today", ("Accuracy by region", "Hours per monthly cycle", "Where overrides cluster")),
    ("The forecasting approach", ("One model, every region", "Planner review and override", "Data needed first")),
    ("Pilot plan and gates", ("Wave one: three regions", "Accuracy gate before rollout", "Owners and weekly review")),
    ("Commercials and next steps", ("Fee phased by gate", "Decisions this month", "The first ninety days")),
]
LIT = 1                                                          # the part the session is on
X0, X1, GAP_X = 0.50, 12.90, 0.30
Y0, TILE_H, GAP_Y = 0.92, 2.92, 0.26
TILE_W = (X1 - X0 - GAP_X) / 2
NUM_W, PAD = 1.62, 0.30
for i, (head, scope) in enumerate(PARTS, 1):
    col, row = (i - 1) % 2, (i - 1) // 2
    x, y = X0 + col * (TILE_W + GAP_X), Y0 + row * (TILE_H + GAP_Y)
    lit = i == LIT
    bg = "accent" if lit else "card"
    tile = Box(x, y, TILE_W, TILE_H)
    if lit:
        prims.block(s, tile, fill="accent", radius_in=0.05, name="struct.part.%d.tile" % i, theme=th)
    else:
        prims.card(s, tile, fill="card", line="hairline", radius_in=0.05, name="struct.part.%d.tile" % i, theme=th)
    num_role, head_role, body_role = ("on-accent",) * 3 if lit else ("ink-deep", "ink-deep", "ink")
    txt.textbox(s, Box(x + PAD, y + 0.22, NUM_W, TILE_H - 0.44),
                [txt.Para((txt.Run(str(i), num_role, bold=True, size=120),), line_spacing=0.9)],
                "slot.part.%d.num" % i, th, anchor="middle", background=bg)
    tx = x + PAD + NUM_W + 0.16
    tw = x + TILE_W - PAD - tx
    txt.textbox(s, Box(tx, y + 0.34, tw, 0.70),
                [txt.Para((txt.Run(head, head_role, bold=True, size=16),))],
                "slot.part.%d.head" % i, th, anchor="bottom", background=bg)
    prims.hairline(s, (tx, y + 1.16), (x + TILE_W - PAD, y + 1.16), role="hairline-soft" if lit else "hairline",
                   weight_pt=1.0, name="struct.part.%d.rule" % i, theme=th)
    txt.textbox(s, Box(tx, y + 1.32, tw, 1.36),
                [txt.Para((txt.Run(line, body_role, size=13),), space_before=0 if k == 0 else 7)
                 for k, line in enumerate(scope)],
                "slot.part.%d.scope" % i, th, background=bg)

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
out = save(prs, "DL33", th, archetype="agenda", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
