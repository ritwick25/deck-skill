"""DL35: a promise close. The next step is stated large at the upper left over a role-level contact block, and one
full-height solid brand panel on the right restates the deck's one-line promise under a short rule (closing)."""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import prims  # noqa: E402
from deckkit import text as txt  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL35")
VARIANT = "promise-panel-close"

# chrome the house rules ban: the full-slide white ground (the slide is already paper), the tall brand bar binding
# the contact column (left-accent), the caps kicker over the title, and the page number (no footer). The two
# removed pictures were the logo lockup at the top: a logo becomes nothing.
for n in ("dev.2", "dev.4", "dev.5", "dev.15"):
    delete(s, n)

# the panel: one solid brand field at full height, bleeding off the right edge (ruling 12: never a tint)
rename(s, "dev.3", "bleed.panel")
prims.set_fill(find(s, "bleed.panel"), "accent", theme=th)
move(s, "bleed.panel", 8.40, 0.0, 13.333 - 8.40, 7.50)

PX, PW = 8.95, 3.85                                              # panel text column, inside the content band
delete(s, "dev.14")                                              # a coloured strip is an edge bar (P16): the mark is a glyph
icon(s, "slot.promise.icon", "target", PX, 2.14, 0.56, th, role="on-accent")
rename(s, "dev.13", "slot.promise")
move(s, "slot.promise", PX, 2.98, PW, 2.10)
text(s, "slot.promise", "One weekly forecast that every planner trusts, owned by the planning office from week fourteen",
     th, size=22, bold=True, role="on-accent", background="accent")

# the next step, stated at cover size on the kit's title edge, two-tone, no bar beside it
X, W = 0.50, 7.30
rename(s, "dev.6", "slot.headline")
TITLE_Y, TITLE_H = 1.30, 1.86
move(s, "slot.headline", X, TITLE_Y, W, TITLE_H)
TITLE = "Approve the pilot scope and forecasts reach planners in fourteen weeks"
text(s, "slot.headline", [txt.Para(tuple(txt.title_runs(TITLE, ("Approve the pilot scope",))))], th, size=34,
     bold=True, anchor="top")

# the contact block: role-level lines only, flush with the title, grouped by spacing alone
CY = 3.70
rename(s, "dev.7", "slot.contact.1.label")
move(s, "slot.contact.1.label", X, CY, 6.00, 0.34)
text(s, "slot.contact.1.label", "Engagement lead", th, size=14, bold=True, role="accent-ink")
rename(s, "dev.8", "slot.contact.1.line")
move(s, "slot.contact.1.line", X, CY + 0.36, 6.00, 0.32)
text(s, "slot.contact.1.line", "Director, data and AI platforms", th, size=13, bold=False, role="ink")

rename(s, "dev.9", "slot.contact.2.label")
move(s, "slot.contact.2.label", X, CY + 0.98, 6.00, 0.34)
text(s, "slot.contact.2.label", "Pilot team", th, size=14, bold=True, role="accent-ink")
LINES = ["Planning analytics lead, accuracy and targets",
         "Forecast engineering lead, models and runs",
         "Data integration lead, order history feeds"]
for i, (n, line) in enumerate(zip(("dev.10", "dev.11", "dev.16"), LINES), 1):
    rename(s, n, "slot.contact.2.line.%d" % i)
    move(s, "slot.contact.2.line.%d" % i, X, CY + 1.34 + (i - 1) * 0.36, 6.60, 0.32)
    text(s, "slot.contact.2.line.%d" % i, line, th, size=13, bold=False, role="ink")

delete(s, "dev.12")                                              # a sentence at the foot reads as a footer (P09)

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
move(s, "slot.headline", X, TITLE_Y, W, TITLE_H)                   # finish widens a content title; a closing's stays put
out = save(prs, "DL35", th, archetype="closing", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
