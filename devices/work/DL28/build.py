"""DL28: a winding road with one pin per year, and beside each pin a card that grows with the horizon: team size,
the business areas served as glyph discs, and the use cases live, the new ones starred (value-horizons)."""
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

prs, s, th = open_lifted("DL28")
VARIANT = "winding-road-growing-cards"


def para(t, role="ink", size=10, bold=False, align="left"):
    return txt.Para((txt.Run(t, role, bold=bold, size=size),), align=align)


def insets(name, l=0.0, t=0.0, r=0.0, b=0.0):
    bp = find(s, name)._element.find(".//" + qn("a:bodyPr"))
    for k, v in (("lIns", l), ("tIns", t), ("rIns", r), ("bIns", b)):
        bp.set(k, str(int(v * EMU)))


def leaves(shapes):
    for sh in shapes:
        if sh.shape_type == 6:
            yield from leaves(sh.shapes)
        else:
            yield sh


def fill_of(sh):
    c = sh._element.find(".//" + qn("p:spPr") + "/" + qn("a:solidFill") + "/" + qn("a:schemeClr"))
    return c.get("val") if c is not None else None


ON = {"accent1": "on-accent", "tx1": "paper", "bg1": "ink-deep"}

# ---- chrome the house rules ban: the source footnote at the foot ------------------------------------------------
for n in ("dev.85", "dev.86", "dev.87", "dev.211"):
    delete(s, n)

# ---- title -----------------------------------------------------------------------------------------------------
rename(s, "dev.213", "slot.title")
move(s, "slot.title", 0.30, 0.14, 7.70, 0.84)
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "One AI team scales from a pilot to every area", ("every area",))))],
    th, size=22, bold=True, anchor="middle")

# ---- road and pins ---------------------------------------------------------------------------------------------
# the road runs edge to edge under the cards, so it is named as a bleed
rename(s, "dev.2", "bleed.road")
rename(s, "dev.3", "bleed.road.line")
# a pin keeps its body and its white eye; the two shading halves and the inner ring go
for k, n in enumerate(("dev.5", "dev.11", "dev.18", "dev.25", "dev.32", "dev.39"), 1):
    base = int(n.split(".")[1])
    for j in (2, 3, 4):
        delete(s, "dev.%d" % (base + j))
    rename(s, n, "struct.pin.%d" % k)
    rename(s, "dev.%d" % (base + 1), "struct.pin.%d.body" % k)
    rename(s, "dev.%d" % (base + 5), "struct.pin.%d.eye" % k)


def radius(name, r=0.05):
    sh = find(s, name)
    gd = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst") + "/" + qn("a:gd"))
    v = int(round(r / (min(sh.width, sh.height) / EMU) * 100000))
    if gd is None:
        gd = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst")).makeelement(qn("a:gd"), {})
        sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst")).append(gd)
        gd.set("name", "adj" if "roundRect" == sh._element.find(".//" + qn("a:prstGeom")).get("prst") else "adj1")
    gd.set("fmla", "val %d" % v)


def paper_fill(name):
    sp = find(s, name)._element.find(qn("p:spPr"))
    for tag in ("a:noFill", "a:solidFill"):
        e = sp.find(qn(tag))
        if e is not None:
            sp.remove(e)
    f = sp.makeelement(qn("a:solidFill"), {})
    f.append(f.makeelement(qn("a:schemeClr"), {"val": "bg1"}))
    sp.insert(2, f)

YEARS = (("dev.4", 0.90, "2027"), ("dev.17", 1.24, "2028"), ("dev.24", 5.32, "2029"), ("dev.38", 8.83, "2030"),
         ("dev.31", 4.10, "2031"), ("dev.45", 8.43, "2032"))
for k, (n, x, y) in enumerate(YEARS, 1):
    nm = "slot.horizon.%d.year" % k
    rename(s, n, nm)
    sh = find(s, nm)
    move(s, nm, x, sh.top / EMU, 0.66, sh.height / EMU)
    insets(nm)
    paper_fill(nm)
    text(s, nm, [para(y, "accent-ink", 16, True)], th, size=16, anchor="middle")

# ---- cards: body, panel, team size, area discs, use cases, new-item stars ---------------------------------------
CARDS = [
    # body, panel, count, count box, team, people icon, rows, dots, discs (row-major glyphs), stars (y), star x
    dict(body="dev.46", panel="dev.47", count="dev.48", cbox=(2.08, 1.23, 0.26), team="2", people=(1.645, 1.166),
         rows=["dev.49"], dots=[], discs=["dev.50"], glyphs=["megaphone"], stars=[], sx=None,
         items=["Campaign drafts"], rbox=(2.40, 1.22, 1.04, 0.60)),
    dict(body="dev.52", panel="dev.53", count="dev.54", cbox=(2.53, 2.73, 0.26), team="4", people=(2.087, 2.661),
         rows=["dev.55"], dots=[], discs=["dev.56"], glyphs=["megaphone"], stars=[], sx=None,
         items=["Brief summaries"], rbox=(2.85, 2.72, 1.04, 0.60)),
    dict(body="dev.136", panel="dev.137", count="dev.150", cbox=(5.64, 1.26, 0.36), team="8", people=(5.146, 1.203),
         rows=["dev.%d" % i for i in range(138, 144)], dots=["dev.%d" % i for i in range(144, 150)],
         discs=["dev.155", "dev.153", "dev.151"], glyphs=["megaphone", "search", "chart-column"],
         stars=[1.238, 1.495, 1.752, 2.009, 2.266], sx=8.343,
         items=["Campaign variants", "Verbatim coding", "Weekly sales forecast",
                "Competitor digest", "Field call summaries", "Brief summaries"]),
    dict(body="dev.157", panel="dev.158", count="dev.173", cbox=(10.00, 1.30, 0.40), team="14",
         people=(9.512, 1.239), rows=["dev.%d" % i for i in range(159, 166)],
         dots=["dev.%d" % i for i in range(166, 173)],
         discs=["dev.178", "dev.176", "dev.174", "dev.180"], glyphs=["megaphone", "search", "chart-column", "coins"],
         stars=[], sx=None,
         items=["Shared prompt library", "Model review board", "Usage and cost tracking", "Price scenario testing",
                "Forecast accuracy checks", "One data request queue", "Analyst training plan"]),
    dict(body="dev.58", panel="dev.59", count="dev.69", cbox=(3.30, 4.46, 0.46), team="22", people=(2.878, 4.399),
         rows=["dev.%d" % i for i in range(60, 69)], dots=["dev.%d" % i for i in range(88, 97)],
         discs=["dev.75", "dev.73", "dev.71", "dev.77", "dev.79", "dev.81", "dev.83"],
         glyphs=["megaphone", "search", "chart-column", "coins", "truck", "database", "headphones"],
         stars=[4.502, 4.759, 5.273, 5.53, 6.558], sx=2.533,
         items=["Demand sensing", "Supplier risk alerts", "Price scenario testing",
                "Order status assistant", "Inventory rebalancing", "Weekly sales forecast",
                "Verbatim coding", "Campaign variants", "Data quality alerts"]),
    dict(body="dev.98", panel="dev.99", count="dev.118", cbox=(9.93, 3.73, 0.46), team="30", people=(9.512, 3.666),
         rows=["dev.%d" % i for i in range(100, 109)], dots=["dev.%d" % i for i in range(109, 118)],
         discs=["dev.124", "dev.122", "dev.120", "dev.126", "dev.128", "dev.130", "dev.132", "dev.134"],
         glyphs=["megaphone", "search", "chart-column", "coins", "truck", "database", "headphones", "shield-check"],
         stars=[3.702, 3.959, 4.215, 4.472, 4.729, 5.757], sx=12.709,
         items=["Contract clause review", "Fraud pattern alerts", "Service chat assistant", "Next best offer",
                "Output policy checks", "Demand sensing", "Supplier risk alerts",
                "Order status assistant", "Self-serve models"]),
]
rename(s, "dev.70", "struct.card.5.areas")
rename(s, "dev.119", "struct.card.6.areas")
for c, C in enumerate(CARDS, 1):
    rename(s, C["body"], "struct.card.%d.body" % c)
    rename(s, C["panel"], "struct.card.%d.panel" % c)
    radius("struct.card.%d.body" % c)
    radius("struct.card.%d.panel" % c)
    cn = "slot.card.%d.count" % c
    rename(s, C["count"], cn)
    x, y, w = C["cbox"]
    move(s, cn, x, y - 0.02, w, 0.34)
    insets(cn)
    text(s, cn, [para(C["team"], "accent-ink", 13, True)], th, size=13, anchor="middle")
    px, py = C["people"]
    side = 0.33 if c <= 2 else 0.40
    py = max(py, find(s, "struct.card.%d.body" % c).top / EMU + 0.045)
    icon(s, "slot.card.%d.icon" % c, "users", px, py, side, th, role="ink-strong")
    # area discs, row-major, each a group holding one ellipse
    for k, (dn, g) in enumerate(zip(C["discs"], C["glyphs"]), 1):
        grp = find(s, dn)
        disc = list(leaves(grp.shapes))[0] if grp.shape_type == 6 else grp
        rename(s, dn, "struct.card.%d.area.%d" % (c, k))
        disc.name = "struct.card.%d.area.%d.disc" % (c, k)
        d = disc.width / EMU
        side = d * 0.58
        icon(s, "slot.card.%d.area.%d" % (c, k), g, disc.left / EMU + (d - side) / 2,
             disc.top / EMU + (d - side) / 2, side, th, role=ON[fill_of(disc)])
    # use cases
    starred = set()
    for sy in C["stars"]:
        for r, rn in enumerate(C["rows"], 1):
            sh = find(s, rn)
            if abs(sh.top / EMU + sh.height / EMU / 2 - (sy + 0.1015)) < 0.12:
                starred.add(r)
    for r, (rn, item) in enumerate(zip(C["rows"], C["items"]), 1):
        nm = "slot.card.%d.item.%d" % (c, r)
        rename(s, rn, nm)
        if "rbox" in C:
            move(s, nm, *C["rbox"])
            text(s, nm, [para(item, "ink", 10.5)], th, size=10.5, background="card", anchor="middle")
        else:
            insets(nm, 0.16, 0.0, 0.30 if C["stars"] else 0.04, 0.0)
            text(s, nm, [para(item, "ink", 10)], th, size=10, background="paper", anchor="middle")
        if r in starred:
            sh = find(s, nm)
            icon(s, "slot.card.%d.star.%d" % (c, r), "sparkles", C["sx"],
                 sh.top / EMU + (sh.height / EMU - 0.20) / 2, 0.20, th, role="accent")
    for r, dn in enumerate(C["dots"], 1):
        rename(s, dn, "struct.card.%d.dot.%d" % (c, r))
        clr = find(s, "struct.card.%d.dot.%d" % (c, r))._element.find(
            ".//" + qn("p:spPr") + "/" + qn("a:solidFill") + "/" + qn("a:schemeClr"))
        if clr is not None and clr.get("val") == "bg1":
            for ch in list(clr):
                clr.remove(ch)
            clr.set("val", "accent1")

# ---- destination callout on the road ---------------------------------------------------------------------------
rename(s, "dev.212", "slot.callout")
move(s, "slot.callout", 5.74, 5.56, 2.68, 0.42)
insets("slot.callout", 0.08, 0.03, 0.08, 0.03)
text(s, "slot.callout", [para("30 people, eight areas", "ink-deep", 12, True, "center")], th,
     size=12, background="card", anchor="middle")

# ---- key: the new-item star -------------------------------------------------------------------------------------
rename(s, "dev.97", "slot.key.label")
insets("slot.key.label", 0.04, 0.0, 0.04, 0.0)
text(s, "slot.key.label", [para("New in this horizon", "ink-strong", 10, True)], th, size=10, anchor="middle")
icon(s, "slot.key.icon", "sparkles", 5.576, 6.987, 0.203, th, role="accent")

# ---- legend: the eight business areas ---------------------------------------------------------------------------
rename(s, "dev.189", "slot.legend.head")
text(s, "slot.legend.head", [para("Areas", "ink-deep", 10.5, True)], th, size=10.5, anchor="middle")
LEG = [  # group, disc group (row 1), label, glyph | disc group (row 2), label, glyph
    ("dev.182", ("dev.183", "dev.187", "megaphone", "Marketing"), ("dev.185", "dev.188", "truck", "Supply")),
    ("dev.190", ("dev.191", "dev.195", "search", "Insight"), ("dev.193", "dev.196", "database", "Data")),
    ("dev.197", ("dev.198", "dev.202", "chart-column", "Sales"), ("dev.200", "dev.203", "headphones", "Care")),
    ("dev.204", ("dev.205", "dev.209", "coins", "Pricing"), ("dev.207", "dev.210", "shield-check", "Risk")),
]
k = 0
for col, (grp, *items) in enumerate(LEG, 1):
    rename(s, grp, "struct.legend.%d" % col)
    for dn, ln, g, label in items:
        k += 1
        dg = find(s, dn)
        disc = list(leaves(dg.shapes))[0]
        rename(s, dn, "struct.legend.%d.disc" % k)
        disc.name = "struct.legend.%d.disc.fill" % k
        d = disc.width / EMU
        side = d * 0.6
        icon(s, "slot.legend.%d.icon" % k, g, disc.left / EMU + (d - side) / 2, disc.top / EMU + (d - side) / 2,
             side, th, role=ON[fill_of(disc)])
        nm = "slot.legend.%d.label" % k
        rename(s, ln, nm)
        sh = find(s, nm)
        nxt = {1: 10.02, 2: 11.03, 3: 11.84, 4: 13.10}[col]
        move(s, nm, sh.left / EMU, sh.top / EMU - 0.03, nxt - sh.left / EMU, sh.height / EMU + 0.06)
        insets(nm)
        text(s, nm, [para(label, "ink", 10)], th, size=10, anchor="middle")

# ---- every leftover child gets its parent's name ----------------------------------------------------------------
def name_children(shapes):
    for sh in shapes:
        if sh.shape_type == 6:
            for j, ch in enumerate(leaves(sh.shapes), 1):
                if ch.name.startswith("dev."):
                    ch.name = "%s.part.%d" % (sh.name, j)
            name_children(sh.shapes)


name_children(s.shapes)


def walk_all(shapes):
    for sh in shapes:
        yield sh
        if sh.shape_type == 6:
            yield from walk_all(sh.shapes)


left = [sh.name for sh in walk_all(s.shapes) if sh.name.startswith("dev.")]
assert not left, left

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
out = save(prs, "DL28", th, archetype="value-horizons", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
