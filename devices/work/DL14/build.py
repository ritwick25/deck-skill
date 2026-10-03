"""DL14: a tangled many-to-many channel mesh on the left, a wedge, and an agent network around one hub on the right."""
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

prs, s, th = open_lifted("DL14")
VARIANT = "channel-mesh-to-agent-hub"


# ---- flatten every group into the slide, carrying its transform down -------------------------------------------
def flatten():
    tree = s.shapes._spTree
    while True:
        groups = [el for el in tree if el.tag == qn("p:grpSp")]
        if not groups:
            return
        for g in groups:
            xf = g.find(qn("p:grpSpPr") + "/" + qn("a:xfrm"))
            off, ext = xf.find(qn("a:off")), xf.find(qn("a:ext"))
            cho, che = xf.find(qn("a:chOff")), xf.find(qn("a:chExt"))
            sx = int(ext.get("cx")) / max(int(che.get("cx")), 1)
            sy = int(ext.get("cy")) / max(int(che.get("cy")), 1)
            for ch in list(g):
                if ch.tag not in (qn("p:sp"), qn("p:cxnSp"), qn("p:grpSp"), qn("p:pic")):
                    continue
                cx = ch.find(qn("p:spPr") + "/" + qn("a:xfrm"))
                if cx is None:
                    cx = ch.find(qn("p:grpSpPr") + "/" + qn("a:xfrm"))
                o, e = cx.find(qn("a:off")), cx.find(qn("a:ext"))
                o.set("x", str(int(round(int(off.get("x")) + (int(o.get("x")) - int(cho.get("x"))) * sx))))
                o.set("y", str(int(round(int(off.get("y")) + (int(o.get("y")) - int(cho.get("y"))) * sy))))
                e.set("cx", str(int(round(int(e.get("cx")) * sx))))
                e.set("cy", str(int(round(int(e.get("cy")) * sy))))
                if ch.tag == qn("p:grpSp") and (sx != 1 or sy != 1):
                    # child group: its own chOff/chExt stay, so its children scale with the new ext
                    pass
                g.addprevious(ch)
            tree.remove(g)


flatten()


def tight(name, v=0.01, side=0.03):
    bp = find(s, name)._element.find(".//" + qn("a:bodyPr"))
    for k, val in (("tIns", v), ("bIns", v), ("lIns", side), ("rIns", side)):
        bp.set(k, str(int(val * EMU)))


def label(old, new, value, box=None, size=9.0, bold=False, role="ink", align="center", anchor="middle",
          background=None):
    rename(s, old, new)
    if box:
        move(s, new, *box)
    tight(new)
    paras = [txt.Para((txt.Run(v, role, bold=bold, size=size),), align=align, space_before=0)
             for v in ([value] if isinstance(value, str) else value)]
    text(s, new, paras, th, size=size, anchor=anchor, background=background)


def glyph_in(shape_name, name, gname, side, role):
    sh = find(s, shape_name)
    x, y, w, h = sh.left / EMU, sh.top / EMU, sh.width / EMU, sh.height / EMU
    icon(s, name, gname, x + (w - side) / 2, y + (h - side) / 2, side, th, role=role)


# ---- delete: foot caption bands, duplicate discs, every drawn custom icon, a stray foot caption -----------------
for n in ("dev.149", "dev.151", "dev.147", "dev.273"):
    delete(s, n)
for n in list(range(14, 42)) + list(range(76, 120)) + list(range(122, 133)) + list(range(135, 146)) \
        + list(range(160, 171)) + list(range(173, 184)) + list(range(187, 198)) + list(range(200, 211)) \
        + list(range(219, 230)) + list(range(231, 242)):
    try:
        delete(s, "dev.%d" % n)
    except Exception:
        pass

# ---- title ---------------------------------------------------------------------------------------------------
rename(s, "dev.2", "slot.title")
move(s, "slot.title", 0.50, 0.13, 12.55, 0.71)
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "Customer requests move from crossed handoffs to one shared agent hub",
    ("one shared agent hub",))))], th, size=22, bold=True, anchor="middle")

# ---- frame: wedge, panel grounds, dashed state panels -----------------------------------------------------------
rename(s, "dev.3", "struct.shift.wedge")
rename(s, "dev.10", "struct.from.panel")
rename(s, "dev.152", "struct.to.panel")
move(s, "struct.from.panel", 0.50, 1.90, 4.22, 4.55)
move(s, "struct.to.panel", 7.22, 1.92, 4.40, 4.70)


def radius(name, r=0.05):
    sh = find(s, name)
    sh.adjustments[0] = r / min(sh.width / EMU, sh.height / EMU)


for n in ("struct.from.panel", "struct.to.panel"):
    radius(n)

# state headers, one short label each
for old, new, head in (("dev.11", "slot.from.header", "Today, manual handoffs"),
                       ("dev.156", "slot.to.header", "Target, agent routing")):
    rename(s, old, new)
    tight(new, 0.03, 0.10)
    text(s, new, [txt.Para((txt.Run(head, "on-accent", bold=True, size=14),), align="center")],
         th, size=14, anchor="middle", background="accent")

label("dev.12", "slot.from.label", "Every role works every channel", (1.06, 1.97, 3.10, 0.24), size=10, bold=True,
      role="ink-deep")
label("dev.157", "slot.to.label", "Agents route each request through one hub", (7.62, 1.97, 3.60, 0.24), size=10,
      bold=True, role="ink-deep")

# ---- from state: four roles, crossed links, four channels, two customer groups ---------------------------------
ROLES = ("Sales rep", "Service desk", "Field tech", "Account lead")
for i, (disc, lab) in enumerate(zip(("dev.64", "dev.65", "dev.66", "dev.67"), ("dev.68", "dev.69", "dev.70", "dev.71")), 1):
    rename(s, disc, "struct.from.role.%d.disc" % i)
    glyph_in("struct.from.role.%d.disc" % i, "slot.from.role.%d.icon" % i, "user", 0.26, "paper")
    sh = find(s, lab)
    label(lab, "slot.from.role.%d" % i, ROLES[i - 1], (0.54, sh.top / EMU, 0.98, 0.22), size=8.5, bold=True,
          role="ink-deep")

CHANNELS = (("dev.13", "Email", "mail"), ("dev.7", "Phone", "phone"), ("dev.8", "Ticket form", "file-text"),
            ("dev.9", "Reports", "chart-column"))
for i, (n, word, g) in enumerate(CHANNELS, 1):
    rename(s, n, "struct.from.channel.%d" % i)
    sh = find(s, "struct.from.channel.%d" % i)
    x, y, w, h = sh.left / EMU, sh.top / EMU, sh.width / EMU, sh.height / EMU
    tight("struct.from.channel.%d" % i, 0.02, 0.12)
    text(s, "struct.from.channel.%d" % i, [txt.Para((txt.Run(word, "ink-deep", bold=True, size=10),),
                                                     align="left")], th, size=10, anchor="middle",
         background="accent-wash")
    rename(s, "struct.from.channel.%d" % i, "slot.from.channel.%d" % i)
    radius("slot.from.channel.%d" % i)
    icon(s, "slot.from.channel.%d.icon" % i, g, x + w - 0.44, y + (h - 0.30) / 2, 0.30, th, role="ink-deep")

for k, n in enumerate(list(range(42, 52)) + [74, 75, 146, 148], 1):
    rename(s, "dev.%d" % n, "struct.from.link.%d" % k)
for k, n in enumerate(range(52, 64), 1):
    rename(s, "dev.%d" % n, "struct.from.handoff.%d" % k)

for i, (disc, lab, word, g) in enumerate((("dev.134", "dev.72", "Distributors", "building"),
                                          ("dev.121", "dev.73", "Retailers", "store")), 1):
    rename(s, disc, "struct.from.customer.%d.disc" % i)
    glyph_in("struct.from.customer.%d.disc" % i, "slot.from.customer.%d.icon" % i, g, 0.26, "on-accent")
    sh = find(s, lab)
    label(lab, "slot.from.customer.%d" % i, word, (5.06, sh.top / EMU, 0.92, 0.20), size=9, bold=True,
          role="ink-deep")

# the from-state body spreads to the panel height the foot band gave up: centres scale, sizes hold, links stretch
K, C0, C1 = 1.166, 2.585, 2.635
for sh in s.shapes:
    if (sh.name.startswith(("struct.from.", "slot.from.")) and sh.name not in
            ("struct.from.panel", "slot.from.header", "slot.from.label")):
        y, h = sh.top / EMU, sh.height / EMU
        if sh._element.tag == qn("p:cxnSp"):
            sh.top, sh.height = int((C1 + (y - C0) * K) * EMU), int(h * K * EMU)
        else:
            sh.top = int((C1 + (y + h / 2 - C0) * K - h / 2) * EMU)
move(s, "struct.from.panel", 0.50, 1.90, 4.22, 4.72)
radius("struct.from.panel")

# ---- to state: the same four roles, four agents round one hub, two partner agents -------------------------------
for i, (disc, lab) in enumerate(zip(("dev.159", "dev.172", "dev.186", "dev.199"),
                                    ("dev.158", "dev.171", "dev.184", "dev.198")), 1):
    rename(s, disc, "struct.to.role.%d.disc" % i)
    glyph_in("struct.to.role.%d.disc" % i, "slot.to.role.%d.icon" % i, "user", 0.26, "paper")
    d = find(s, "struct.to.role.%d.disc" % i)
    label(lab, "slot.to.role.%d" % i, ROLES[i - 1], (7.26, d.top / EMU + 0.49, 1.00, 0.20), size=8.5, bold=True,
          role="ink-deep")

AGENTS = (("dev.211", "dev.246", "Intake", (9.65, 2.75, 0.48, 0.18)),
          ("dev.213", "dev.248", "Triage", (8.31, 4.04, 0.70, 0.18)),
          ("dev.214", "dev.249", "Quote", (10.82, 4.04, 0.76, 0.18)),
          ("dev.212", "dev.287", "Scheduling", (9.51, 6.36, 0.84, 0.18)))
for i, (disc, lab, word, box) in enumerate(AGENTS, 1):
    rename(s, disc, "struct.to.agent.%d.disc" % i)
    glyph_in("struct.to.agent.%d.disc" % i, "slot.to.agent.%d.icon" % i, "bot", 0.27, "on-accent")
    label(lab, "slot.to.agent.%d" % i, word, box, size=8, bold=True, role="ink-deep")

rename(s, "dev.215", "struct.to.hub")
label("dev.266", "slot.to.hub.head", "Agent hub", (9.46, 3.46, 0.94, 0.22), size=10, bold=True, role="on-accent",
      background="accent-deep")
label("dev.267", "slot.to.hub.body", ["Shared case", "record"], (9.46, 3.70, 0.94, 0.36), size=8.5, role="on-accent",
      background="accent-deep")

for i, (ell, lab, word) in enumerate((("dev.216", "dev.276", ["Partner", "agent"]),
                                      ("dev.217", "dev.277", ["Store", "agent"])), 1):
    rename(s, ell, "struct.to.partner.%d.disc" % i)
    e = find(s, "struct.to.partner.%d.disc" % i)
    ex, ey = e.left / EMU, e.top / EMU
    icon(s, "slot.to.partner.%d.icon" % i, "bot", ex + 0.29, ey + 0.10, 0.22, th, role="accent-ink")
    label(lab, "slot.to.partner.%d" % i, word, (ex + 0.12, ey + 0.34, 0.56, 0.32), size=8, bold=True,
          role="ink-deep", background="accent-wash")

for i, (disc, lab, word, g) in enumerate((("dev.230", "dev.278", "Dealers", "building"),
                                          ("dev.218", "dev.279", "Stores", "store")), 1):
    rename(s, disc, "struct.to.customer.%d.disc" % i)
    glyph_in("struct.to.customer.%d.disc" % i, "slot.to.customer.%d.icon" % i, g, 0.17, "on-accent")
    d = find(s, "struct.to.customer.%d.disc" % i)
    label(lab, "slot.to.customer.%d" % i, word, (d.left / EMU - 0.15, d.top / EMU - 0.20, 0.56, 0.17), size=8,
          role="ink")

label("dev.272", "slot.to.flow.1", ["Order status", "sync"], (11.82, 2.74, 0.84, 0.32), size=8, role="ink")
label("dev.274", "slot.to.flow.2", "Stock view", (11.86, 4.52, 0.74, 0.16), size=8, role="ink")
label("dev.264", "slot.to.exception", "Exceptions", None, size=8, bold=True, role="ink-deep")

# links of the target network
LINKS = [242, 243, 244, 245, 247, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 265, 268,
         269, 270, 271, 275, 280, 281, 282]
for k, n in enumerate(LINKS, 1):
    rename(s, "dev.%d" % n, "struct.to.link.%d" % k)

# snap every link end onto a box, drop the ones that float
for n in ("struct.to.link.10", "struct.to.link.13", "struct.to.link.23", "struct.to.link.24"):
    delete(s, n)
move(s, "struct.to.link.9", 7.97, 4.22, 3.22, 0.86)          # field tech to the quote agent label
move(s, "struct.to.link.11", 9.73, 4.65, 1.88, 1.02)         # scheduling agent to the quote agent label (rot 90)
move(s, "struct.to.link.21", 11.44, 3.77, 0.40, 0.0)          # quote agent to partner agent rim
move(s, "struct.to.link.22", 11.44, 3.89, 0.43, 0.0)
move(s, "struct.to.link.28", 11.40, 4.21, 0.54, 0.63)        # quote agent to store agent rim

# key
rename(s, "dev.153", "struct.key")
for i, (line, lab, word) in enumerate((("dev.284", "dev.283", "Request flow"), ("dev.285", "dev.286", "Data sync"),
                                       ("dev.155", "dev.154", "Staff escalation")), 1):
    rename(s, line, "struct.key.line.%d" % i)
    ln = find(s, "struct.key.line.%d" % i)
    label(lab, "slot.key.%d" % i, word, (12.06, ln.top / EMU - 0.09, 1.00, 0.18), size=8, role="ink", align="left")

# remaining grounds
for sh in list(s.shapes):
    if sh.name.startswith("dev."):
        sh.name = "struct.ground.%s" % sh.name.split(".")[1]

out = save(prs, "DL14", th, archetype="from-to-shift", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
