"""DL34: a ghost numeral divider; the part name stacks large on the left and an oversized grey part numeral
counterweights it on the right, with nothing else on the ground (section-divider)."""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import text as txt  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL34")
VARIANT = "ghost-numeral"

# the two party marks are client and house logos, so both pictures went at lift and nothing replaces them; the
# dashed rule that separated them would be a stray mark on its own
delete(s, "dev.4")

# the part name: a divider stacks its title large (P14 allows three lines on a section-divider), starting on the
# kit title's left edge, its block centred on the numeral's midline
NUM_Y, NUM_H = 1.62, 5.10
MID = NUM_Y + NUM_H / 2
TITLE_H = 2.30
rename(s, "dev.2", "slot.headline")
move(s, "slot.headline", 0.50, MID - TITLE_H / 2, 6.70, TITLE_H)
bp = find(s, "slot.headline")._element.find(".//" + qn("a:bodyPr"))
for k in ("lIns", "tIns", "rIns", "bIns"):
    bp.set(k, "0")
text(s, "slot.headline", [txt.Para(tuple(txt.title_runs(
    "Where demand planning stands today", ("demand planning",))), line_spacing=0.95)],
    th, size=40, bold=True, anchor="middle")

# the ghost numeral: the largest type on the page, in ink-muted grey (the palest text role; the source pale grey fails P25),
# right edge on the content band (P03)
rename(s, "dev.3", "slot.numeral")
move(s, "slot.numeral", 7.40, NUM_Y, 5.50, NUM_H)
bp = find(s, "slot.numeral")._element.find(".//" + qn("a:bodyPr"))
for k in ("lIns", "tIns", "rIns", "bIns"):
    bp.set(k, "0")
text(s, "slot.numeral", [txt.Para((txt.Run("01", "ink-muted", bold=True, size=280),), align="right",
                                  line_spacing=0.9)], th, size=280, bold=True, anchor="middle")

# finish() would widen the title to the full title band, running the stacked part name into the numeral; the title
# here is a left stack, so the band check runs over every shape, the title included, and the tint remap follows
from assemble_devices import fit_band, remap_small_tints  # noqa: E402
assert fit_band(prs.slides[0], title="-") == 1.0             # already inside the content band (P03)
remap_small_tints(prs.slides[0], th)
out = save(prs, "DL34", th, archetype="section-divider", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
