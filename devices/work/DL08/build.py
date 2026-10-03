"""DL08: domain tabs over an agent disc mesh, one domain spotlit as the starting point, on a platform panel."""
import argparse
import copy
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import text as txt  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

HERE = Path(__file__).resolve().parent
prs, s, th = open_lifted("DL08")
VARIANT = "domain-tabs-agent-mesh"
LIFT = json.loads((HERE / "lift.json").read_text())


def clone(src, name, x, y, w, h, after=None):
    el = copy.deepcopy(find(s, src)._element)
    find(s, after or src)._element.addnext(el)
    ids = [int(c.get("id")) for c in s._element.iter(qn("p:cNvPr"))]
    el.find(".//" + qn("p:cNvPr")).set("name", name)
    el.find(".//" + qn("p:cNvPr")).set("id", str(max(ids) + 1))
    move(s, name, x, y, w, h)


def tight(name, v=0.02, side=0.06):
    bp = find(s, name)._element.find(".//" + qn("a:bodyPr"))
    for k, val in (("tIns", v), ("bIns", v), ("lIns", side), ("rIns", side)):
        bp.set(k, str(int(val * EMU)))


# title: one claim, two-tone
rename(s, "dev.165", "slot.title")
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "Sales execution goes first, since its six agents feed the other four domains",
    ("Sales execution",))))], th, size=22, bold=True, anchor="middle")

# header bar over the device
rename(s, "dev.30", "slot.header")
tight("slot.header")
text(s, "slot.header", [txt.Para((txt.Run("Commercial agent network", "on-accent",
                                          bold=True, size=13),), align="center")],
     th, size=13, background="accent", anchor="middle")

# key strip: users, agent status legend, starting rule
rename(s, "dev.31", "struct.key")
rename(s, "dev.41", "struct.key.divider.1")
rename(s, "dev.42", "struct.key.divider.2")
rename(s, "dev.38", "slot.key.1.label")
move(s, "slot.key.1.label", 2.22, 1.72, 1.02, 0.54)
text(s, "slot.key.1.label", "Serves reps and planners", th, size=10.5, bold=True, role="ink-deep", anchor="middle")
rename(s, "dev.39", "slot.key.2.label")
move(s, "slot.key.2.label", 4.06, 1.72, 1.10, 0.54)
text(s, "slot.key.2.label", "Agent status", th, size=10.5, bold=True, role="ink-deep", anchor="middle")
rename(s, "dev.40", "slot.legend.1")
move(s, "slot.legend.1", 5.70, 1.81, 0.95, 0.36)
clone("slot.legend.1", "slot.legend.2", 6.95, 1.81, 0.95, 0.36)
clone("slot.legend.1", "slot.legend.3", 8.20, 1.81, 0.95, 0.36)
for i, w in enumerate(("Live", "Planned", "Shared"), 1):
    text(s, "slot.legend.%d" % i, w, th, size=10.5, role="ink", anchor="middle")
SWATCH = ("dev.89", "dev.88", "dev.102")                        # filled, outline, toned discs
for i, (src, x) in enumerate(zip(SWATCH, (5.45, 6.70, 7.95)), 1):
    clone(src, "struct.legend.disc.%d" % i, x, 1.89, 0.20, 0.20, after="struct.key")   # top level, above the strip
rename(s, "dev.43", "slot.key.3.label")
move(s, "slot.key.3.label", 10.40, 1.72, 2.20, 0.54)
text(s, "slot.key.3.label", "Start where data and owners are ready", th, size=10.5, bold=True, role="ink-deep",
     anchor="middle")

# domain tabs, the spotlit one third
DOMAINS = [("dev.33", "Demand planning"), ("dev.37", "Pricing"), ("dev.34", "Sales execution"),
           ("dev.35", "Trade promotion"), ("dev.36", "Customer service")]
for i, (n, label) in enumerate(DOMAINS, 1):
    rename(s, n, "slot.domain.%d" % i)
    tight("slot.domain.%d" % i)
    bg = "accent" if i == 3 else "ink-deep"
    text(s, "slot.domain.%d" % i, [txt.Para((txt.Run(label, "on-accent" if i == 3 else "paper", bold=True,
                                                     size=13),), align="center")],
         th, size=13, background=bg, anchor="middle")
rename(s, "dev.32", "struct.spotlight")
for k, n in enumerate(range(2, 16), 1):
    rename(s, "dev.%d" % n, "struct.dropline.%d" % k)

# agent names and task pills
AGENTS = [  # (name shape, name, [(pill shape, task)])
    ("dev.158", "Forecast agent", [("dev.159", "Demand signal"), ("dev.160", "Regional bias alerts")]),
    ("dev.140", "Price guardrail agent", [("dev.141", "Discount floors"), ("dev.143", "Deal desk triage")]),
    ("dev.144", "Visit planner agent", [("dev.145", "Daily store route"), ("dev.146", "Shelf gap alerts")]),
    ("dev.153", "Order status agent", [("dev.154", "Delay notices"), ("dev.155", "Claim intake")]),
    ("dev.156", "Returns agent", [("dev.157", "Credit note drafts")]),
    ("dev.138", "Stock risk agent", [("dev.139", "Stock-out watch")]),
    ("dev.147", "Order capture agent", [("dev.148", "Voice and email orders")]),
    ("dev.149", "Call notes agent", [("dev.150", "Visit notes")]),
    ("dev.151", "Promo check agent", [("dev.152", "Uplift readout")]),
]
# labels and pills sit wholly inside or wholly outside the spotlight wedge
FIT = {"dev.140": (3.40, 1.75), "dev.144": (6.83, 1.25), "dev.145": (6.83, 1.25), "dev.146": (6.83, 1.25),
       "dev.147": (5.22, 1.60), "dev.148": (5.22, 1.60), "dev.149": (6.95, 1.10), "dev.150": (7.01, 1.05)}
for n, (x, w) in FIT.items():
    sh = find(s, n)
    move(s, n, x, sh.top / EMU, w, sh.height / EMU)
for n in ("dev.148", "dev.150"):                              # pills inside the wedge go to paper so they read
    sf = find(s, n)._element.find(qn("p:spPr") + "/" + qn("a:solidFill"))
    for c in list(sf):
        sf.remove(c)
    sf.append(sf.makeelement(qn("a:schemeClr"), {"val": "bg1"}))
INSIDE = {"dev.148", "dev.150"}
for k, (nm, name, pills) in enumerate(AGENTS, 1):
    rename(s, nm, "slot.agent.%d.name" % k)
    tight("slot.agent.%d.name" % k, 0.01, 0.03)
    text(s, "slot.agent.%d.name" % k, [txt.Para((txt.Run(name, "ink-deep", bold=True, size=8),), align="center")],
         th, size=8, anchor="middle")
    for j, (pn, task) in enumerate(pills, 1):
        rename(s, pn, "slot.agent.%d.task.%d" % (k, j))
        tight("slot.agent.%d.task.%d" % (k, j), 0.01, 0.05)
        text(s, "slot.agent.%d.task.%d" % (k, j), [txt.Para((txt.Run(task, "ink", size=8),), align="center")],
             th, size=8, background="paper" if pn in INSIDE else "accent-wash", anchor="middle")

# platform panel and its chips
rename(s, "dev.16", "struct.platform")
move(s, "struct.platform", 0.60, 5.51, 12.11, 1.45)
rename(s, "dev.44", "slot.platform.label")
move(s, "slot.platform.label", 3.03, 5.58, 7.25, 0.34)
text(s, "slot.platform.label", [txt.Para((txt.Run("Shared platform services", "accent-ink", bold=True, size=12),),
                                         align="center")], th, size=12, anchor="middle")
rename(s, "dev.17", "struct.platform.chips")
CHIPS = [("dev.18", "Product master"), ("dev.21", "Customer master"), ("dev.24", "Price book"),
         ("dev.19", "Store visits"), ("dev.22", "Order history"), ("dev.25", "Promo calendar"),
         ("dev.20", "Agent registry"), ("dev.23", "Evaluation runs"), ("dev.26", "Usage logs")]
for i, (n, label) in enumerate(CHIPS, 1):
    rename(s, n, "slot.platform.chip.%d" % i)
    tight("slot.platform.chip.%d" % i, 0.02, 0.05)
    text(s, "slot.platform.chip.%d" % i, [txt.Para((txt.Run(label, "ink-deep", bold=True, size=9.5),),
                                                   align="center")], th, size=9.5, background="card",
         anchor="middle")
SERVICES = [("dev.27", "Governed data products for every domain"),
            ("dev.28", "One agent runtime with shared evaluation"),
            ("dev.29", "Identity, access and audit trail on every call")]
for i, (n, label) in enumerate(SERVICES, 1):
    rename(s, n, "slot.platform.service.%d" % i)
    tight("slot.platform.service.%d" % i, 0.02, 0.08)
    text(s, "slot.platform.service.%d" % i, [txt.Para((txt.Run(label, "ink", size=9.5),), align="center")],
         th, size=9.5, background="card", anchor="middle")

# mesh links
LINKS = list(range(45, 87)) + [162, 164]
for k, n in enumerate(LINKS, 1):
    rename(s, "dev.%d" % n, "struct.link.%d" % k)

# agent discs: groups and ellipses, numbered by row then x
discs, groups = [], []
for n in [87, 88] + list(range(89, 138)) + [142, 161, 163]:
    sh = find(s, "dev.%d" % n)
    (groups if sh.shape_type == 6 else discs).append(sh)
for k, g in enumerate(sorted(groups, key=lambda g: (round(g.top / EMU, 1), g.left)), 1):
    g.name = "struct.agent.group.%d" % k


def abs_box(sh):
    """Slide-space box of a shape, walking up through group transforms."""
    x, y, w, h = sh.left, sh.top, sh.width, sh.height
    el = sh._element.getparent()
    while el.tag == qn("p:grpSp"):
        xf = el.find(qn("p:grpSpPr") + "/" + qn("a:xfrm"))
        off, ext = xf.find(qn("a:off")), xf.find(qn("a:ext"))
        cho, che = xf.find(qn("a:chOff")), xf.find(qn("a:chExt"))
        sx = int(ext.get("cx")) / max(int(che.get("cx")), 1)
        sy = int(ext.get("cy")) / max(int(che.get("cy")), 1)
        x = int(off.get("x")) + (x - int(cho.get("x"))) * sx
        y = int(off.get("y")) + (y - int(cho.get("y"))) * sy
        w, h = w * sx, h * sy
        el = el.getparent()
    return x / EMU, y / EMU, w / EMU, h / EMU


placed = []
for d in discs:
    bx = abs_box(d)
    placed.append((round(bx[1], 1), bx[0], d, bx))
placed.sort(key=lambda t: (t[0], t[1]))
for k, (_, _, d, bx) in enumerate(placed, 1):
    d.name = "struct.agent.%d" % k


def disc_role(d):
    fill = d._element.find(qn("p:spPr") + "/" + qn("a:solidFill") + "/" + qn("a:schemeClr"))
    if fill.get("val") == "accent1":
        return "on-accent"
    if fill.find(qn("a:lumMod")) is not None:
        return "paper"
    return "accent"


# glyphs: the four strip icons, then one bot mark in every agent disc
STRIP = {(1.729, 1.827): ("slot.key.1.icon.2", "store"), (1.201, 1.816): ("slot.key.1.icon.1", "users"),
         (3.605, 1.829): ("slot.key.2.icon", "scale"), (9.848, 1.809): ("slot.key.3.icon", "target")}
for p in LIFT["pictures_removed"]:
    x, y, w, h = p["box_in"]
    key = (round(x, 3), round(y, 3))
    if key in STRIP:
        nm, g = STRIP[key]
        icon(s, nm, g, x, y + (h - 0.36) / 2, 0.36, th, role="accent-ink")
        continue
    cx, cy = x + w / 2, y + h / 2
    k, d, bx = min(((k, d, bx) for k, (_, _, d, bx) in enumerate(placed, 1)),
                   key=lambda t: (t[2][0] + t[2][2] / 2 - cx) ** 2 + (t[2][1] + t[2][3] / 2 - cy) ** 2)
    side = 0.17
    icon(s, "slot.agent.disc.%d.icon" % k, "bot", bx[0] + (bx[2] - side) / 2, bx[1] + (bx[3] - side) / 2, side, th,
         role=disc_role(d))

# lift the whole device into the air under the title, clear of the foot line
DY = 0.25
for sh in s.shapes:
    if sh.name != "slot.title":
        sh.top = int(sh.top - DY * EMU)

out = save(prs, "DL08", th, archetype="use-case-map", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
