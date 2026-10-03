"""DL29: a half-wheel of five peer teams around one data core, fed by two layer cards and two base platforms."""
import argparse
import math
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import prims  # noqa: E402
from deckkit import text as txt  # noqa: E402
from deckkit.canvas import Box  # noqa: E402
from lxml import etree  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL29")
prims.bind(th)
VARIANT = "half-wheel-layered-base"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


def drop(*names):
    for n in names:
        try:
            delete(s, n)
        except Exception:
            pass                                   # already gone with its group


def set_prst(name, prst, adj=None, flip_v=False):
    """Swap a shape's geometry for a preset (no custom vector survives)."""
    sp = find(s, name)._element.find(qn("p:spPr"))
    old = sp.find(qn("a:custGeom"))
    if old is None:
        old = sp.find(qn("a:prstGeom"))
    new = etree.SubElement(sp, qn("a:prstGeom"))
    new.set("prst", prst)
    av = etree.SubElement(new, qn("a:avLst"))
    for k, v in (adj or {}).items():
        gd = etree.SubElement(av, qn("a:gd"))
        gd.set("name", k)
        gd.set("fmla", "val %d" % v)
    sp.remove(new)
    old.addprevious(new)
    sp.remove(old)
    if flip_v:
        sp.find(qn("a:xfrm")).set("flipV", "1")


def tb(name, box, words, *, size, role="ink", bold=False, bg="paper", align="ctr", anchor="top"):
    txt.textbox(s, box, [txt.Para((txt.Run(words, role, bold=bold, size=size),), align=align)], name, th,
                anchor=anchor, background=bg)


# chrome and residue: the fan's caption, the stray hub caption, the pipe, the plug marks on the ring,
# every lorem label, both foot captions, the base interiors (logo wells, dots), the old dividers and funnels
drop("dev.3", "dev.6", "dev.7", *("dev.%d" % i for i in range(8, 23)))
drop(*("dev.%d" % i for i in range(85, 179)))
drop(*("dev.%d" % i for i in range(70, 84)), "dev.189", "dev.190", "dev.187", "dev.188")
drop("dev.27", "dev.37", "dev.28", "dev.29", "dev.30", "dev.31", "dev.32", "dev.33", "dev.35", "dev.36")
drop(*("dev.%d" % i for i in range(39, 50)), "dev.50", *("dev.%d" % i for i in range(51, 55)))
drop("dev.57", "dev.58", "dev.59", "dev.60", *("dev.%d" % i for i in range(61, 65)))
drop(*("dev.%d" % i for i in range(179, 187)), "dev.66", "dev.67", "dev.68", "dev.69")

# title: one claim, two-tone
rename(s, "dev.2", "slot.title")
move(s, "slot.title", 0.48, 0.36, 12.40, 0.55)
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "One governed data core now serves all five planning teams",
    ("One governed data core",))))], th, size=24, bold=True, anchor="middle")

# the half-wheel: a flat wash fan, a two-tone ring, a paper hub, all on one center. Each is drawn as a true
# half (its own arc path), so its box is the half it paints and nothing below the center sits "on" it
CX, CY, FA, FB = 6.645, 3.95, 4.67, 2.68
R_OUT, R_IN, R_HUB = 1.55, 1.20, 0.98


def half(name, x, y, w, h, thick=None):
    """Replace a shape's geometry with an upper half ellipse (or a half annulus thick inches wide)."""
    move(s, name, x, y, w, h)
    W, H = int(w * EMU), int(h * EMU)
    sp = find(s, name)._element.find(qn("p:spPr"))
    old = sp.find(qn("a:custGeom"))
    if old is None:
        old = sp.find(qn("a:prstGeom"))
    path = ('<a:moveTo><a:pt x="0" y="%d"/></a:moveTo><a:arcTo wR="%d" hR="%d" stAng="10800000" swAng="10800000"/>'
            % (H, W // 2, H))
    if thick:
        T = int(thick * EMU)
        path += ('<a:lnTo><a:pt x="%d" y="%d"/></a:lnTo><a:arcTo wR="%d" hR="%d" stAng="0" swAng="-10800000"/>'
                 % (W - T, H, W // 2 - T, H - T))
    xml = ('<a:custGeom xmlns:a="%s"><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/><a:rect l="l" t="t" r="r" b="b"/>'
           '<a:pathLst><a:path w="%d" h="%d">%s<a:close/></a:path></a:pathLst></a:custGeom>' % (A_NS, W, H, path))
    old.addprevious(etree.fromstring(xml))
    sp.remove(old)


rename(s, "dev.23", "struct.fan")
half("struct.fan", CX - FA, CY - FB, 2 * FA, FB)
prims.set_fill(find(s, "struct.fan"), "accent-wash", theme=th)
rename(s, "dev.24", "struct.ring.outer")
half("struct.ring.outer", CX - R_OUT, CY - R_OUT, 2 * R_OUT, R_OUT, R_OUT - R_IN)
prims.set_fill(find(s, "struct.ring.outer"), "accent", theme=th)
rename(s, "dev.84", "struct.ring.inner")
half("struct.ring.inner", CX - R_IN, CY - R_IN, 2 * R_IN, R_IN, R_IN - R_HUB)
prims.set_fill(find(s, "struct.ring.inner"), "accent-deep", theme=th)
rename(s, "dev.65", "struct.hub")
half("struct.hub", CX - R_HUB, CY - R_HUB, 2 * R_HUB, R_HUB)
prims.set_fill(find(s, "struct.hub"), "paper", theme=th)
_hub = find(s, "struct.hub")._element
find(s, "struct.ring.inner")._element.addnext(_hub)              # the hub paints over the inner ring's box
tb("slot.hub", Box(CX - 0.75, CY - 0.70, 1.50, 0.62), "Shared data core", size=16, role="accent-ink", bold=True,
   anchor="bottom")

def on_fan(deg, t):
    r = math.radians(deg)
    return CX + t * FA * math.cos(r), CY - t * FB * math.sin(r)


for i, deg in enumerate((144, 108, 72, 36), 1):                 # four spokes cut the fan into five equal sectors
    dx, dy = FA * math.cos(math.radians(deg)), -FB * math.sin(math.radians(deg))
    n = math.hypot(dx, dy)
    p1 = (CX + R_OUT * dx / n, CY + R_OUT * dy / n)
    prims.connect(s, p1, on_fan(deg, 1.0), head="none", role="hairline", weight_pt=5,
                  name="struct.spoke.%d" % i, theme=th)

SECTORS = [(162, "chart-line", "Demand planning"), (126, "tag", "Pricing analytics"),
           (90, "truck", "Supply planning"), (54, "calculator", "Finance reporting"),
           (18, "users", "Customer insight")]
for i, (deg, g, label) in enumerate(SECTORS, 1):
    px, py = on_fan(deg, 0.80 if deg in (54, 126) else 0.70 if deg in (18, 162) else 0.78)
    icon(s, "slot.sector.%d.icon" % i, g, px - 0.19, py - 0.40, 0.38, th, role="accent-ink")
    tb("slot.sector.%d.label" % i, Box(px - 0.62, py + 0.03, 1.24, 0.40), label, size=11, role="ink-deep",
       bold=True, bg="accent-wash")

# the layer band: two cards, each led by an accent tab carrying its layer name
CARD_Y, CARD_H, CARD_W, TAB_W = 4.18, 1.08, 4.15, 0.40
LAYERS = [("dev.55", 1.86 + TAB_W + 0.04, 1.86, "Ingest",
           [("database", "Batch loads"), ("activity", "Event streams"), ("list-checks", "Quality checks"),
            ("git-branch", "Lineage tracking")]),
          ("dev.56", 6.82, 6.82 + CARD_W + 0.04, "Govern",
           [("lock", "Access control"), ("shield-check", "Privacy rules"), ("monitor", "Usage monitoring"),
            ("book-open", "Data catalog")])]
drop("dev.38", "dev.25", "dev.5", "dev.4")
tree = s.shapes._spTree
for i, (tablbl, cx, tx, name, items) in enumerate(LAYERS, 1):
    prims.block(s, Box(tx, CARD_Y, TAB_W, CARD_H), fill="accent", name="struct.card.%d.tab" % i, theme=th)
    prims.card(s, Box(cx, CARD_Y, CARD_W, CARD_H), fill="card", line="hairline", name="struct.card.%d" % i,
               theme=th)
    rename(s, tablbl, "slot.card.%d.tab" % i)
    lbl = find(s, "slot.card.%d.tab" % i)._element
    tree.remove(lbl)
    tree.append(lbl)                                              # the rotated label rides on its tab
    move(s, "slot.card.%d.tab" % i, tx + TAB_W / 2 - 0.47, CARD_Y + CARD_H / 2 - 0.15, 0.94, 0.30)
    text(s, "slot.card.%d.tab" % i, name, th, size=11, bold=True, role="on-accent", background="accent",
         anchor="middle")
    x0, colw = cx + 0.08, (CARD_W - 0.16) / 4
    for j, (g, label) in enumerate(items, 1):
        mx = x0 + (j - 0.5) * colw
        icon(s, "slot.card.%d.item.%d.icon" % (i, j), g, mx - 0.17, CARD_Y + 0.14, 0.34, th, role="accent")
        tb("slot.card.%d.item.%d.label" % (i, j), Box(mx - colw / 2 + 0.06, CARD_Y + 0.54, colw - 0.12, 0.40),
           label, size=10, role="ink", bg="card")
        if j > 1:
            prims.hairline(s, (x0 + (j - 1) * colw, CARD_Y + 0.16), (x0 + (j - 1) * colw, CARD_Y + CARD_H - 0.16),
                           name="struct.card.%d.rule.%d" % (i, j - 1), theme=th)

# the base: two deep platforms, each feeding its layer card through a funnel
BASE_Y, BASE_H = 5.86, 1.02
BASES = [("dev.26", 1.86, "Source systems",
          [("shopping-cart", "Orders"), ("warehouse", "Inventory"), ("file-text", "Contracts"),
           ("contact", "Accounts")]),
         ("dev.34", 6.82, "Model services",
          [("trending-up", "Forecasts"), ("sliders-horizontal", "Solvers"), ("layers", "Scenarios"),
           ("bell", "Alerts")])]
for i, (sh, bx, head, chips) in enumerate(BASES, 1):
    rename(s, sh, "struct.base.%d" % i)
    move(s, "struct.base.%d" % i, bx, BASE_Y, 4.59, BASE_H)
    prims.set_fill(find(s, "struct.base.%d" % i), "accent-deep", theme=th)
    tb("slot.base.%d.head" % i, Box(bx + 0.22, BASE_Y + 0.10, 3.00, 0.30), head, size=12, role="on-accent",
       bold=True, bg="accent-deep", align="l")
    colw = (4.59 - 0.44) / 4
    for j, (g, label) in enumerate(chips, 1):
        x = bx + 0.22 + (j - 1) * colw
        icon(s, "slot.base.%d.item.%d.icon" % (i, j), g, x, BASE_Y + 0.54, 0.26, th, role="on-accent")
        tb("slot.base.%d.item.%d.label" % (i, j), Box(x + 0.31, BASE_Y + 0.51, colw - 0.31, 0.32), label,
           size=10, role="on-accent", bg="accent-deep", align="l", anchor="middle")
    fx = bx + 2.295                                              # under the card center, tab included
    top = prims.rect(s, Box(fx - 0.45, CARD_Y + CARD_H, 0.90, 0.30), fill="accent", name="struct.funnel.%d.top" % i,
                     theme=th)
    set_prst("struct.funnel.%d.top" % i, "trapezoid", {"adj": 50000}, flip_v=True)
    prims.rect(s, Box(fx - 0.14, CARD_Y + CARD_H + 0.30, 0.28, BASE_Y - CARD_Y - CARD_H - 0.30), fill="accent",
               name="struct.funnel.%d.stem" % i, theme=th)

out = save(prs, "DL29", th, archetype="hub-and-spoke", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
