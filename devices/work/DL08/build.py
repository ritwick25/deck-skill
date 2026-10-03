"""DL08: domain tabs over an agent disc mesh, one domain spotlit as the starting point, on a platform panel."""
import argparse
import copy
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import prims, text as txt  # noqa: E402
from deckkit.canvas import Box  # noqa: E402

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
    "Sales execution goes first, since its agents feed the other four domains",
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


# ---- the agent field: the lifted mesh (27 unlabelled discs, about 40 undirected links) gives way to named agents
# in one column per domain, and directed feeds from the spotlit column into every other domain
for sh in list(s.shapes):
    if sh.name.startswith(("dev.", "struct.dropline.")) or sh.name == "struct.spotlight":
        delete(s, sh.name)

# key strip glyphs (the lifted bot pictures inside the mesh are not redrawn: every agent below carries its own)
STRIP = {(1.729, 1.827): ("slot.key.1.icon.2", "store"), (1.201, 1.816): ("slot.key.1.icon.1", "users"),
         (3.605, 1.829): ("slot.key.2.icon", "scale"), (9.848, 1.809): ("slot.key.3.icon", "target")}
for p in LIFT["pictures_removed"]:
    key = (round(p["box_in"][0], 3), round(p["box_in"][1], 3))
    if key in STRIP:
        x, y, w, h = p["box_in"]
        nm, g = STRIP[key]
        icon(s, nm, g, x, y + (h - 0.36) / 2, 0.36, th, role="accent-ink")

# lift the whole device into the air under the title, clear of the foot line
DY = 0.25
for sh in s.shapes:
    if sh.name != "slot.title":
        sh.top = int(sh.top - DY * EMU)

LIVE, PLANNED, SHARED = 1, 2, 3              # the legend's own discs, cloned so status reads from the key
AGENTS = {  # domain: [(name, task, status)], four per domain so every column holds the same rows
    1: [("Forecast", "Demand signal", LIVE), ("Stock risk", "Stock-out watch", PLANNED),
        ("Bias check", "Regional alerts", PLANNED), ("Supply plan", "Weekly build plan", SHARED)],
    2: [("Price guardrail", "Discount floors", SHARED), ("Deal desk", "Triage requests", PLANNED),
        ("Price watch", "Competitor moves", PLANNED), ("Rebate check", "Accrual review", PLANNED)],
    3: [("Visit planner", "Daily store route", LIVE), ("Shelf scan", "Gap alerts", LIVE),
        ("Order capture", "Voice and email", LIVE), ("Call notes", "Visit summaries", PLANNED)],
    4: [("Promo check", "Uplift readout", PLANNED), ("Claim audit", "Deduction review", PLANNED),
        ("Event plan", "Calendar fit", PLANNED), ("Display check", "In-store proof", SHARED)],
    5: [("Order status", "Delay notices", LIVE), ("Returns", "Credit notes", PLANNED),
        ("Claims", "Intake and routing", SHARED), ("Case summary", "Handover notes", PLANNED)],
}
LIT = 3
PANEL_TOP, PANEL_BOT, LANE = 2.71, 4.73, 4.99
ROW0, PITCH, DISC = 2.80, 0.48, 0.36


def box(name):
    sh = find(s, name)
    return sh.left / EMU, sh.top / EMU, sh.width / EMU, sh.height / EMU


def glyph_role(el):
    """The bot mark's role on a cloned legend disc: on-accent on the live fill, paper on the shared grey, accent
    on the planned outline."""
    fill = el.find(qn("p:spPr") + "/" + qn("a:solidFill") + "/" + qn("a:schemeClr"))
    if fill.get("val") == "accent1" and fill.find(qn("a:lumMod")) is None:
        return "on-accent"
    return "paper" if fill.find(qn("a:lumMod")) is not None else "accent"


tree = s.shapes._spTree
k = 0
panels = []
for d in range(1, 6):
    tx, _, tw, _ = box("slot.domain.%d" % d)
    pn = ("state.spotlight" if d == LIT else "struct.domain.%d.panel" % d)
    prims.rect(s, Box(tx, PANEL_TOP, tw, PANEL_BOT - PANEL_TOP), fill="accent-wash" if d == LIT else "card",
               line=None if d == LIT else "hairline-soft", name=pn, theme=th)
    panels.append(pn)
    for r, (name, task, status) in enumerate(AGENTS[d]):
        k += 1
        y = ROW0 + r * PITCH
        dn = "struct.agent.%d.disc" % k
        clone("struct.legend.disc.%d" % status, dn, tx + 0.10, y + 0.03, DISC, DISC, after="struct.key")
        el = find(s, dn)._element
        tree.remove(el)
        tree.append(el)                       # above its panel
        icon(s, "slot.agent.%d.icon" % k, "bot", tx + 0.10 + (DISC - 0.22) / 2, y + 0.03 + (DISC - 0.22) / 2,
             0.22, th, role=glyph_role(el))
        bg = "accent-wash" if d == LIT else "card"
        txt.textbox(s, Box(tx + 0.54, y, tw - 0.60, 0.22),
                    [txt.Para((txt.Run(name, "ink-deep", bold=True, size=10.5),))], "slot.agent.%d.name" % k, th,
                    background=bg)
        txt.textbox(s, Box(tx + 0.54, y + 0.22, tw - 0.60, 0.20), [txt.Para((txt.Run(task, "ink", size=10),))],
                    "slot.agent.%d.task" % k, th, background=bg)
for pn in reversed(panels):                   # every panel behind the agents it holds
    el = find(s, pn)._element
    tree.remove(el)
    tree.insert(2, el)

# feeds: one bus out of the spotlit column's foot into the foot of every other domain
lx, _, lw, _ = box("state.spotlight")
src = lx + lw / 2
for d in (1, 2, 4, 5):
    tx, _, tw, _ = box("struct.domain.%d.panel" % d)
    prims.elbow(s, [(src, PANEL_BOT), (src, LANE), (tx + tw / 2, LANE), (tx + tw / 2, PANEL_BOT)], role="accent",
                weight_pt=1.5, name="struct.feed.%d" % d, theme=th)

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
out = save(prs, "DL08", th, archetype="use-case-map", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
