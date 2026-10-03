"""DL17: six headline figures on a dark band, each crowned by a glyph disc that breaks the band's top edge,
over three implication cards and one solid next-step panel (headline-figures)."""
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

prs, s, th = open_lifted("DL17")
VARIANT = "disc-band-figures-card-row"

# chrome the house rules ban: the kicker above the title, the page number, the footer logo
for n in ("dev.10", "dev.93", "dev.94"):    # dev.94 is the logo group, dev.95 to dev.102 go with it
    delete(s, n)
# the source's drawn icons (custom geometry), replaced by curated glyphs below
for i in list(range(35, 84)) + list(range(104, 110)):
    try:
        delete(s, "dev.%d" % i)
    except KeyError:                       # a member of a group already removed with its group
        pass


def P(t, role="ink", size=11, bold=False, before=0, align="center"):
    return txt.Para((txt.Run(t, role, bold=bold, size=size),), align=align, space_before=before)


def nofill(name):
    sp = find(s, name)._element.find(qn("p:spPr"))
    for f in sp.findall(qn("a:solidFill")):
        idx = list(sp).index(f)
        sp.remove(f)
        sp.insert(idx, sp.makeelement(qn("a:noFill"), {}))


# title: one claim, two-tone
rename(s, "dev.9", "slot.title")
move(s, "slot.title", 0.42, 0.30, 12.50, 0.80)
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "The invoice automation pilot paid back its cost in five months",
    ("five months",))))], th, size=26, bold=True, anchor="middle")

# the band the figures stand on, grown into the height the cards gave up
BAND_TOP, BAND_BOT = 2.022, 5.45
rename(s, "dev.11", "bleed.band")   # full-width bleed: the discs break its top edge by design
prims.set_fill(find(s, "bleed.band"), "ink-deep", theme=th)
move(s, "bleed.band", 0.0, BAND_TOP, 13.333, BAND_BOT - BAND_TOP)

FIGS = [("62%", "Invoices posted with no manual touch", "Up from 18% at the baseline", "file-check"),
        ("44%", "Shorter month-end close cycle", "Close now runs in five days, not nine", "calendar-check"),
        ("3x", "Vendor queries resolved per analyst", "Measured over the last eight weeks", "users"),
        ("$1.8M", "Annual run-rate savings identified", "Booked over the first two quarters", "piggy-bank"),
        ("91%", "First-pass match rate on payments", "Exceptions routed to one shared queue", "circle-check"),
        ("5 mo", "To recover the full pilot cost", "Against a twelve-month business case", "hourglass")]
NUMBERS = {}
STAT_Y = 2.98
STAT_H = max(prims.stat_height(s, 1.9, f[0], f[1], kind="measured", pt=42, label_pt=13, theme=th) for f in FIGS)
RINGS = ["dev.%d" % i for i in range(3, 9)]
DISCS = ["dev.%d" % i for i in range(24, 30)]
NUMS = ["dev.12", "dev.14", "dev.16", "dev.18", "dev.20", "dev.22"]
LABS = ["dev.13", "dev.15", "dev.17", "dev.19", "dev.21", "dev.23"]
for i, (fig, lab, basis, g) in enumerate(FIGS, 1):
    rename(s, RINGS[i - 1], "struct.fig.%d.ring" % i)
    rename(s, DISCS[i - 1], "struct.fig.%d.disc" % i)
    d = find(s, "struct.fig.%d.disc" % i)
    cx, cy = (d.left + d.width / 2) / EMU, (d.top + d.height / 2) / EMU
    icon(s, "slot.fig.%d.icon" % i, g, cx - 0.21, cy - 0.21, 0.42, th, role="accent")
    x = cx - 0.95
    delete(s, NUMS[i - 1])
    nm = "slot.fig.%d" % i
    g = prims.stat(s, Box(x, STAT_Y, 1.9, STAT_H), fig, lab, kind="measured", role="on-accent", pt=42,
                   label_pt=13, label_role="on-accent", background="ink-deep", name=nm, theme=th)
    for p_ in g._element.iter(qn("a:pPr")):              # the column reads centred under its disc
        p_.set("algn", "ctr")
    NUMBERS[nm] = {"value": fig, "kind": "measured"}
    rename(s, LABS[i - 1], "slot.fig.%d.basis" % i)
    move(s, "slot.fig.%d.basis" % i, x, STAT_Y + STAT_H + 0.10, 1.9, 0.50)
    text(s, "slot.fig.%d.basis" % i, [P(basis, "on-accent", 11)], th, size=11, background="ink-deep")

# the rules between the columns, spanning the figure stack
for k, n in enumerate(("dev.30", "dev.31", "dev.32", "dev.33", "dev.34"), 1):
    rename(s, n, "struct.rule.%d" % k)
    sh = find(s, "struct.rule.%d" % k)
    move(s, "struct.rule.%d" % k, sh.left / EMU, 3.05, 0, 1.85)
    prims.set_line(sh, "ink-muted", 0.75, theme=th)

# the card row, shortened to its content
CARD_TOP, CARD_H = BAND_BOT, 7.5 - BAND_BOT
CARDS = [("dev.84", "dev.87", "dev.88", "Controls held",
          "Every posting keeps an audit trail and an approver", "shield-check"),
         ("dev.85", "dev.89", "dev.90", "Savings mix",
          "Two thirds from analyst time, a third from discounts", "chart-pie"),
         ("dev.86", "dev.91", "dev.92", "Team roles",
          "Analysts moved from keying invoices to exceptions", "user-check")]
for i, (fr, hd, bd, h, b, g) in enumerate(CARDS, 1):
    rename(s, fr, "struct.card.%d" % i)
    f = find(s, "struct.card.%d" % i)
    fx, fw = f.left / EMU, f.width / EMU
    fw -= 0.08                                           # sibling cards never touch
    prims.set_fill(f, "card", theme=th)
    move(s, "struct.card.%d" % i, fx, CARD_TOP, fw, CARD_H)
    bg = "card"
    rename(s, hd, "slot.card.%d.head" % i)
    move(s, "slot.card.%d.head" % i, fx + 0.30, CARD_TOP + 0.42, fw - 1.05, 0.46)
    text(s, "slot.card.%d.head" % i, [P(h, "ink-deep", 18, True, align="left")], th, size=18, background=bg,
         anchor="middle")
    icon(s, "slot.card.%d.icon" % i, g, fx + fw - 0.74, CARD_TOP + 0.42, 0.46, th, role="accent")
    rename(s, bd, "slot.card.%d.body" % i)
    move(s, "slot.card.%d.body" % i, fx + 0.30, CARD_TOP + 0.98, fw - 0.55, 0.70)
    text(s, "slot.card.%d.body" % i, [P(b, "ink", 13, align="left")], th, size=13, background=bg)

# the solid panel: the decision the figures support
rename(s, "dev.2", "struct.panel")
move(s, "struct.panel", 9.25, CARD_TOP, 13.333 - 9.25, CARD_H)
rename(s, "dev.103", "slot.panel.head")
move(s, "slot.panel.head", 9.55, CARD_TOP + 0.42, 3.48, 0.46)
text(s, "slot.panel.head", [P("Recommended next step", "on-accent", 18, True, align="left")], th, size=18,
     background="accent", anchor="middle")
el = __import__("copy").deepcopy(find(s, "slot.panel.head")._element)
find(s, "slot.panel.head")._element.addnext(el)
nv = el.find(".//" + qn("p:cNvPr"))
nv.set("name", "slot.panel.body")
nv.set("id", "5020")
move(s, "slot.panel.body", 9.55, CARD_TOP + 0.98, 3.48, 0.70)
text(s, "slot.panel.body", [P("Extend to two more regional centers next quarter",
                              "on-accent", 13, align="left")], th, size=13, background="accent")

from deckkit import package, tag  # noqa: E402
tag.tag(prs.slides[0], "headline-figures", VARIANT)
for sh in prs.slides[0].shapes:
    ooxml.finish(sh)
out = WORK / "DL17" / "device.pptx"
package.save(prs, out, title="Device DL17", theme=th, manifest={"numbers": NUMBERS}, overwrite=True,
             date="2026-10-03")
if a.out:
    shutil.copyfile(out, a.out)
