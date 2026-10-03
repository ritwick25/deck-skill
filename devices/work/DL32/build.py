"""DL32: a flush-left cover stack (kicker, two-line title, one label line, date) on a light ground, balanced by one
solid brand field under a curved silhouette that carries the deck's thesis as a small native motif: three inputs
feeding one hub (cover)."""
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

prs, s, th = open_lifted("DL32")
VARIANT = "stack-brand-field-motif"

# chrome the house rules ban: the stray lockup rule (its logos were removed), the tall brand bar binding the stack
# (left-accent), the web address line under the date (no footer)
for n in ("dev.3", "dev.4", "dev.9"):
    delete(s, n)

# the silhouette: the source's curved mask over a gradient picture is redrawn as one flat brand field of the same
# reading (a flat top shoulder, a long diagonal, a soft foot), in the kit's own path, never the source's vector
delete(s, "dev.2")
F_TOP, F_X0 = 2.55, 5.90                                         # shoulder height; where the foot meets the slide edge
PATH = [("m", 13.333, F_TOP), ("l", 10.55, F_TOP),
        ("c", 9.70, F_TOP, 9.35, 2.85, 8.95, 3.50),             # the shoulder rounds into the diagonal
        ("l", 7.55, 6.10),
        ("c", 7.05, 7.00, 6.55, 7.50, F_X0, 7.50),              # the foot flattens onto the slide edge
        ("l", 13.333, 7.50)]
FIELD = Box(F_X0, F_TOP, 13.333 - F_X0, 7.50 - F_TOP)
field = prims.rect(s, FIELD, fill="accent", name="bleed.field", theme=th)
sp = field._element.find(qn("p:spPr"))
geo = sp.find(qn("a:prstGeom"))
E = lambda v, o: str(int(round((v - o) * EMU)))                 # noqa: E731  inches to path EMU, relative to the box
cg = sp.makeelement(qn("a:custGeom"), {})
for tag in ("a:avLst", "a:gdLst", "a:ahLst", "a:cxnLst"):
    cg.append(cg.makeelement(qn(tag), {}))
r = cg.makeelement(qn("a:rect"), {"l": "l", "t": "t", "r": "r", "b": "b"})
cg.append(r)
pl = cg.makeelement(qn("a:pathLst"), {})
path = pl.makeelement(qn("a:path"), {"w": E(13.333, F_X0), "h": E(7.50, F_TOP)})
for op in PATH:
    if op[0] in ("m", "l"):
        el = path.makeelement(qn("a:moveTo" if op[0] == "m" else "a:lnTo"), {})
        el.append(el.makeelement(qn("a:pt"), {"x": E(op[1], F_X0), "y": E(op[2], F_TOP)}))
    else:
        el = path.makeelement(qn("a:cubicBezTo"), {})
        for k in range(3):
            el.append(el.makeelement(qn("a:pt"), {"x": E(op[1 + 2 * k], F_X0), "y": E(op[2 + 2 * k], F_TOP)}))
    path.append(el)
path.append(path.makeelement(qn("a:close"), {}))
pl.append(path)
cg.append(pl)
sp.replace(geo, cg)
s.shapes._spTree.remove(field._element)
s.shapes._spTree.insert(2, field._element)                      # first on the slide, behind the motif

# the title stack, flush left on the kit's title edge (0.50in), no bar: one left edge and a strict type ladder
X, W = 0.50, 7.40
rename(s, "dev.5", "slot.kicker")
move(s, "slot.kicker", X, 2.02, W, 0.26)
text(s, "slot.kicker", "PROPOSAL", th, size=11, bold=True, role="accent-ink")

rename(s, "dev.6", "slot.headline")
TITLE_Y, TITLE_H = 2.38, 1.24
move(s, "slot.headline", X, TITLE_Y, W, TITLE_H)
TITLE = "One demand forecast for every planning region"
text(s, "slot.headline", [txt.Para(tuple(txt.title_runs(TITLE, ("One demand forecast",))))], th, size=36, bold=True)

rename(s, "dev.7", "slot.label")
move(s, "slot.label", X, TITLE_Y + TITLE_H + 0.30, W, 0.34)
text(s, "slot.label", "Prepared for the group supply planning office", th, size=16, bold=False, role="ink")

rename(s, "dev.8", "slot.date")
move(s, "slot.date", X, TITLE_Y + TITLE_H + 0.84, 4.00, 0.30)
text(s, "slot.date", "October 2026", th, size=14, bold=True, role="ink-deep")

# the motif on the brand field: three inputs feed one hub, so the right side states the thesis, not a mood
D, HUB = 0.66, 1.10
HX, HY = 11.55, 4.95                                            # hub centre
FEEDS = [(9.95, 3.35, "shopping-cart", "Orders"),
         (9.10, 4.95, "truck", "Shipments"),
         (9.95, 6.55 - 0.42, "calendar", "Promotions")]
hub = prims.circle(s, Box(HX - HUB / 2, HY - HUB / 2, HUB, HUB), fill="ink-deep", name="struct.motif.hub", theme=th)
icon(s, "slot.motif.hub.icon", "chart-line", HX - 0.29, HY - 0.29, 0.58, th, role="accent-bright")
txt.textbox(s, Box(HX - 1.00, HY + HUB / 2 + 0.10, 2.00, 0.34),
            [txt.Para((txt.Run("One forecast", "on-accent", bold=True, size=14),), align="center")],
            "slot.motif.hub.label", th, background="accent")
import math  # noqa: E402
for i, (cx, cy, g, lab) in enumerate(FEEDS, 1):
    prims.circle(s, Box(cx - D / 2, cy - D / 2, D, D), fill="paper", name="struct.motif.%d.disc" % i, theme=th)
    icon(s, "slot.motif.%d.icon" % i, g, cx - 0.19, cy - 0.19, 0.38, th, role="accent-ink")
    txt.textbox(s, Box(cx - 0.85, cy + D / 2 + 0.06, 1.70, 0.30),
                [txt.Para((txt.Run(lab, "on-accent", size=12),), align="center")],
                "slot.motif.%d.label" % i, th, background="accent")
    dx, dy = HX - cx, HY - cy                                   # disc edge to hub edge, along the centre line
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    prims.connect(s, (cx + ux * D / 2, cy + uy * D / 2), (HX - ux * HUB / 2, HY - uy * HUB / 2), head="end",
                  role="paper", weight_pt=1.5, name="struct.motif.%d.arrow" % i, theme=th)

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
move(s, "slot.headline", X, TITLE_Y, W, TITLE_H)                   # finish widens a content title; a cover's stays put
out = save(prs, "DL32", th, archetype="cover", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
