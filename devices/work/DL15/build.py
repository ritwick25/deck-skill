"""DL15: four horizons under a tonal chevron ramp, the first an operating sketch of today's desk, the next three
the same step network with person-run nodes turning into agent-run nodes, over a tools tray and an outcome
strip per horizon (value-horizons)."""
import argparse
import copy
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import text as txt  # noqa: E402
from lxml import etree  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL15")
VARIANT = "step-network-handover"


def walk(shapes):
    for sh in shapes:
        yield sh
        if sh.shape_type == 6:
            yield from walk(sh.shapes)


def kind(sh):
    el = sh._element
    g = el.find(".//" + qn("a:prstGeom"))
    if el.tag.endswith("}grpSp"):
        return "grpSp"
    if g is not None:
        return g.get("prst")
    return "cust" if el.find(".//" + qn("a:custGeom")) is not None else el.tag.split("}")[1]


def ins0(name, l=0.0, t=0.0):
    bp = find(s, name)._element.find(".//" + qn("a:bodyPr"))
    for k, v in (("lIns", l), ("rIns", l), ("tIns", t), ("bIns", t)):
        bp.set(k, str(int(v * EMU)))


def lab(name, value, size=8, role="ink-deep", bold=False, bg="paper", align="center", anchor="middle",
        l=0.0, t=0.0):
    ins0(name, l, t)
    vals = [value] if isinstance(value, str) else value
    paras = [txt.Para((txt.Run(v, role, bold=bold, size=size),), align=align) for v in vals]
    text(s, name, paras, th, size=size, background=bg, anchor=anchor)


def set_fill(name, scheme, mods=()):
    sp = find(s, name)._element.find(qn("p:spPr"))
    f = sp.find(qn("a:solidFill"))
    for c in list(f):
        f.remove(c)
    sc = etree.SubElement(f, qn("a:schemeClr"))
    sc.set("val", scheme)
    for k, v in mods:
        etree.SubElement(sc, qn("a:" + k)).set("val", str(v))


def clone(src, new):
    el = find(s, src)._element
    dup = copy.deepcopy(el)
    ids = [int(c.get("id")) for c in s._element.iter(qn("p:cNvPr"))]
    c = dup.find(".//" + qn("p:cNvPr"))
    c.set("id", str(max(ids) + 1))
    c.set("name", new)
    el.addnext(dup)


TINT = (("lumMod", 20000), ("lumOff", 80000))

# ---- 1. what the house rules ban, and fragments the lift left behind ------------------------------------------
dead = ["dev.9", "dev.59", "dev.475",                            # empty icon group, a stray dot, a one-off label
        "dev.341", "dev.343", "dev.177", "dev.183", "dev.321", "dev.327",   # letters stacked one per line
        "dev.38", "dev.39", "dev.40", "dev.48", "dev.51"]                   # words squeezed into 0.24in discs
for sh in list(walk(s.shapes)):
    k = kind(sh)
    if k == "flowChartDelay" or (k == "cust" and sh.width < 0.03 * EMU and sh.height < 0.03 * EMU):
        dead.append(sh.name)
for n in dict.fromkeys(dead):
    try:
        delete(s, n)
    except KeyError:
        pass                                                      # already gone with a deleted parent

# ---- title ----------------------------------------------------------------------------------------------------
rename(s, "dev.2", "slot.title")
move(s, "slot.title", 0.50, 0.22, 12.40, 0.70)
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "Agents run routine claims work by year three, people own the exceptions", ("by year three",))))],
    th, size=22, bold=True, anchor="middle")

# ---- horizon chevrons and the team band -----------------------------------------------------------------------
for h, (n, word, role, bg) in enumerate((("dev.8", "Today", "ink-deep", "accent-wash"),
                                         ("dev.348", "Year 1", "ink-deep", "accent-tint"),
                                         ("dev.61", "Year 2", "ink-deep", "accent-tint"),
                                         ("dev.195", "Year 3", "on-accent", "accent")), 1):
    rename(s, n, "slot.horizon.%d.label" % h)
    lab("slot.horizon.%d.label" % h, word, size=12, role=role, bold=True, bg=bg)
rename(s, "dev.6", "struct.band")
hp = find(s, "slot.horizon.1.label")                              # the first plate stops where the next notch starts
move(s, "slot.horizon.1.label", hp.left / EMU, hp.top / EMU, 3.07, hp.height / EMU)

TEAM = {1: (0.813, 1.168, 1.523, 1.878, 2.233, 2.588), 2: (4.782, 5.137, 5.492, 5.847),
        3: (8.044, 8.399, 8.754), 4: (10.588, 10.919)}
for h, xs in TEAM.items():
    for k, x in enumerate(xs, 1):
        icon(s, "slot.horizon.%d.team.icon.%d" % (h, k), "users", x + 0.01, 1.807, 0.25, th, role="ink")
for h, n, x, word in ((2, "dev.350", 4.05, "4 pods"), (3, "dev.62", 7.36, "3 pods"), (4, "dev.196", 9.90, "2 pods")):
    rename(s, n, "slot.horizon.%d.team" % h)
    move(s, "slot.horizon.%d.team" % h, x, 1.83, 0.62, 0.20)
    lab("slot.horizon.%d.team" % h, word, size=9, bold=True, bg="card", align="right")
rename(s, "dev.349", "struct.horizon.2.team.group")
rename(s, "dev.338", "struct.horizon.4.callout")
rename(s, "dev.339", "slot.horizon.4.callout")
move(s, "slot.horizon.4.callout", 11.50, 1.77, 1.28, 0.31)
lab("slot.horizon.4.callout", ["People own the", "exceptions only"], size=8, role="on-accent", bold=True,
    bg="accent")

# ---- horizon 1: today's desk ----------------------------------------------------------------------------------
rename(s, "dev.10", "struct.today.arrow.1")                      # arrows land on the band, the pill and the tray
move(s, "struct.today.arrow.1", 2.09, 2.21, 0, 0.33)
rename(s, "dev.24", "struct.today.arrow.2")
move(s, "struct.today.arrow.2", 1.98, 5.33, 0, 0.44)
rename(s, "dev.23", "slot.today.head")
move(s, "slot.today.head", 0.60, 2.47, 1.00, 0.19)
lab("slot.today.head", "Claims desk", size=9, role="accent-ink", bold=True)
rename(s, "dev.20", "slot.today.member.1")
move(s, "slot.today.member.1", 1.06, 2.80, 0.80, 0.28)
lab("slot.today.member.1", ["Claims", "handler"], align="left")
rename(s, "dev.18", "slot.today.member.2")
move(s, "slot.today.member.2", 2.32, 2.80, 0.95, 0.28)
lab("slot.today.member.2", ["Rules", "macros"], align="left")
icon(s, "slot.today.member.1.icon", "user", 0.725, 2.835, 0.20, th, role="accent-ink")
icon(s, "slot.today.member.2.icon", "cog", 1.985, 2.835, 0.20, th, role="accent-ink")

rename(s, "dev.37", "slot.today.hub.label")
move(s, "slot.today.hub.label", 1.70, 4.44, 0.50, 0.16)
lab("slot.today.hub.label", "Handler", bold=True, bg="paper")
rename(s, "dev.60", "slot.today.hub.sub")
move(s, "slot.today.hub.sub", 1.70, 4.97, 0.50, 0.16)
lab("slot.today.hub.sub", "Inbox", bg="paper")
icon(s, "slot.today.hub.icon.1", "user", 1.84, 4.215, 0.20, th, role="ink-deep")
icon(s, "slot.today.hub.icon.2", "mail", 1.84, 4.73, 0.20, th, role="ink-deep")
for k, (n, g) in enumerate((("dev.47", "file-spreadsheet"), ("dev.33", "phone"), ("dev.34", "mail"),
                            ("dev.29", "file-text"), ("dev.49", "message-square")), 1):
    rename(s, n, "struct.today.channel.%d" % k)
    set_fill("struct.today.channel.%d" % k, "accent1", TINT)
    c = find(s, "struct.today.channel.%d" % k)
    icon(s, "slot.today.channel.%d.icon" % k, g, c.left / EMU + 0.045, c.top / EMU + 0.045, 0.15, th,
         role="accent-ink")
TASKS = (("dev.42", "Calls and email"), ("dev.41", "Policy lookups"), ("dev.46", ["Paper", "forms"]),
         ("dev.45", ["Shared", "sheets"]), ("dev.50", ["Rekeyed", "data"]), ("dev.44", ["Manual", "checks"]),
         ("dev.43", ["Payment", "sign-off"]))
for k, (n, w) in enumerate(TASKS, 1):
    rename(s, n, "slot.today.task.%d" % k)
    lab("slot.today.task.%d" % k, w, l=0.03)

rename(s, "dev.53", "slot.today.tools.head")
move(s, "slot.today.tools.head", 0.80, 5.83, 2.36, 0.18)
lab("slot.today.tools.head", "Four tools, rekeyed by hand", bold=True, bg="card")
rename(s, "dev.58", "slot.today.tools.note")
move(s, "slot.today.tools.note", 0.80, 6.32, 2.36, 0.18)
lab("slot.today.tools.note", "Case history split four ways", bg="card")
for k, (n, g) in enumerate((("dev.55", "monitor"), ("dev.54", "mail"), ("dev.56", "file-spreadsheet"),
                            ("dev.57", "folder")), 1):
    rename(s, n, "struct.today.tools.%d" % k)
    b = find(s, "struct.today.tools.%d" % k)
    icon(s, "slot.today.tools.%d.icon" % k, g, (b.left + b.width / 2) / EMU - 0.09,
         (b.top + b.height / 2) / EMU - 0.09, 0.18, th, role="ink-deep")

# ---- horizons 2 to 4: the same step network, handed over -----------------------------------------------------
STEP_WORDS = ("Intake", "Notice", "Policy", "Triage", "Verify", "Assess", "Reserve", "Fraud", "Settle", "Pay",
              "Close")
NETS = {
    2: dict(off=0.0, head=("dev.471", "Agent assist"),
            steps=("dev.454", "dev.455", "dev.456", "dev.457", "dev.458", "dev.459", "dev.460", "dev.453",
                   "dev.481", "dev.451", "dev.452"),
            parties=(("dev.461", "Client"), ("dev.342", "Vendor")),
            tools=("dev.356", "dev.355", "dev.354"), note="dev.357", outcome="dev.360",
            box="dev.361", tray="dev.352", strip="dev.358",
            words=("Inbox", "Rules", "Forms", "Queue"), note_text=["Shared", "case file"],
            out_text="Assist cuts handling time"),
    3: dict(off=3.074, head=("dev.193", "Agent led"),
            steps=("dev.168", "dev.169", "dev.170", "dev.172", "dev.173", "dev.174", "dev.175", "dev.167",
                   "dev.171", "dev.165", "dev.166"),
            parties=(("dev.176", "Client"), ("dev.182", "Vendor")),
            tools=("dev.68", "dev.67", "dev.66"), note="dev.69", outcome="dev.72",
            box="dev.73", tray="dev.64", strip="dev.70",
            words=("Inbox", "Rules", "Models", "Queue"), note_text=["Live case", "scoring"],
            out_text="Agents clear routine claims"),
    4: dict(off=6.175, head=("dev.337", "Agent run"),
            steps=("dev.312", "dev.313", "dev.314", "dev.316", "dev.317", "dev.318", "dev.319", "dev.311",
                   "dev.315", "dev.309", "dev.310"),
            parties=(("dev.320", "Client"), ("dev.326", "Vendor")),
            tools=("dev.202", "dev.201", "dev.200"), note="dev.203", outcome="dev.206",
            box="dev.207", tray="dev.198", strip="dev.204",
            words=("Agents", "Rules", "Models", "Audit"), note_text=["Full", "audit log"],
            out_text="People resolve exceptions"),
}
TOOL_CX = (3.966, 4.443, 4.987, 5.580)
TOOL_GLYPH = {"Inbox": "mail", "Rules": "list-checks", "Forms": "file-text", "Queue": "list-ordered",
              "Models": "brain-circuit", "Agents": "bot", "Audit": "file-check"}
for h, d in NETS.items():
    o = d["off"]
    p = "slot.horizon.%d" % h
    rename(s, d["box"], "struct.horizon.%d.net" % h)
    rename(s, d["tray"], "struct.horizon.%d.tray" % h)
    rename(s, d["strip"], "struct.horizon.%d.strip" % h)
    hn, hw = d["head"]
    rename(s, hn, p + ".net.head")
    move(s, p + ".net.head", 4.29 + o, 2.41, 0.86, 0.18)
    lab(p + ".net.head", hw, size=9, role="accent-ink", bold=True)
    for k, (n, w) in enumerate(zip(d["steps"], STEP_WORDS), 1):
        rename(s, n, p + ".step.%d" % k)
        sh = find(s, p + ".step.%d" % k)
        if sh.width < 0.46 * EMU:
            cx = (sh.left + sh.width / 2) / EMU
            move(s, p + ".step.%d" % k, cx - 0.23, sh.top / EMU, 0.46, sh.height / EMU)
        sh = find(s, p + ".step.%d" % k)
        move(s, p + ".step.%d" % k, sh.left / EMU, sh.top / EMU, sh.width / EMU, 0.18)
        if k == 6:                                                # clear of the node it names
            move(s, p + ".step.6", 5.08 + o, sh.top / EMU, 0.46, 0.18)
        lab(p + ".step.%d" % k, w)
    for k, (n, w) in enumerate(d["parties"], 1):
        rename(s, n, p + ".party.%d" % k)
        sh = find(s, p + ".party.%d" % k)
        cx = (sh.left + sh.width / 2) / EMU
        move(s, p + ".party.%d" % k, cx - 0.23, 3.12, 0.46, 0.18)
        lab(p + ".party.%d" % k, w, bold=True)
    clone(d["tools"][0], p + ".tool.1")
    for k, n in enumerate(d["tools"], 2):
        rename(s, n, p + ".tool.%d" % k)
    for k, (cx, w) in enumerate(zip(TOOL_CX, d["words"]), 1):
        move(s, p + ".tool.%d" % k, cx + o - 0.23, 6.00, 0.46, 0.16)
        lab(p + ".tool.%d" % k, w)
        icon(s, p + ".tool.%d.icon" % k, TOOL_GLYPH[w], cx + o - 0.10, 5.79, 0.20, th, role="ink-deep")
    rename(s, d["note"], p + ".tool.note")
    move(s, p + ".tool.note", 5.98 + o, 5.77, 0.58, 0.36)
    lab(p + ".tool.note", d["note_text"], bold=True)
    rename(s, d["outcome"], p + ".outcome")
    move(s, p + ".outcome", 4.36 + o, 6.59, 2.10, 0.22)
    lab(p + ".outcome", d["out_text"], size=9, align="left")
    icon(s, p + ".outcome.icon", ("timer", "bot", "user-check")[h - 2], 4.116 + o - 0.09, 6.61, 0.18, th,
         role="accent-ink")

# ---- nodes: grey is a person-run step, red an agent-run step, pink an outside party ---------------------------
def col(x):
    return 1 if x < 3.63 else 2 if x < 6.70 else 3 if x < 9.77 else 4


GREY, ACC = ("bg1", ("75000",)), ("accent1", ())
seen = {}
for sh in list(walk(s.shapes)):
    if kind(sh) != "ellipse" or sh.name.startswith(("slot.", "struct.")):
        continue
    if not (0.19 * EMU < sh.width < 0.30 * EMU and abs(sh.width - sh.height) < 0.06 * EMU):
        continue
    f = sh._element.find(qn("p:spPr") + "/" + qn("a:solidFill") + "/" + qn("a:schemeClr"))
    if f is None:
        continue
    mods = [c.get("val") for c in f if c.tag.endswith("lumMod")]
    x, y, w = sh.left / EMU, sh.top / EMU, sh.width / EMU
    if y > 6.9:
        continue                                                  # legend discs, done below
    if f.get("val") == "bg1" and mods == ["75000"]:
        g, role = "user", "ink-deep"
    elif f.get("val") == "accent1" and mods == ["20000"]:
        g, role = "user", "accent-ink"
    elif f.get("val") == "accent1" and not mods:
        g, role = "bot", "on-accent"
    else:
        continue
    h = col(x)
    seen[h] = seen.get(h, 0) + 1
    k = seen[h]
    rename(s, sh.name, "struct.horizon.%d.node.%d" % (h, k))
    side = 0.16
    icon(s, "slot.horizon.%d.node.%d.icon" % (h, k), g, x + w / 2 - side / 2, y + w / 2 - side / 2, side, th,
         role=role)

# ---- legend: mark plus short label ----------------------------------------------------------------------------
rename(s, "dev.485", "slot.legend.head")
move(s, "slot.legend.head", 2.30, 7.04, 1.00, 0.19)
lab("slot.legend.head", "Step owner", size=9, role="ink-muted", bold=True, align="right")
rename(s, "dev.482", "struct.legend.1")
rename(s, "dev.483", "struct.legend.1.disc")
set_fill("struct.legend.1.disc", "bg1", (("lumMod", 75000),))
icon(s, "slot.legend.1.icon", "user", 3.405, 7.07, 0.14, th, role="ink-deep")
rename(s, "dev.486", "slot.legend.1")
move(s, "slot.legend.1", 3.64, 7.04, 0.62, 0.19)
lab("slot.legend.1", "Person", size=9, align="left")
rename(s, "dev.487", "struct.legend.2")
rename(s, "dev.488", "struct.legend.2.disc")
icon(s, "slot.legend.2.icon", "bot", 4.365, 7.07, 0.14, th, role="on-accent")
rename(s, "dev.490", "slot.legend.2")
move(s, "slot.legend.2", 4.60, 7.04, 0.70, 0.19)
lab("slot.legend.2", "Agent", size=9, align="left")

# ---- every remaining shape is fixed structure -----------------------------------------------------------------
PART = {"straightConnector1": "line", "cust": "link", "ellipse": "dot", "grpSp": "group", "roundRect": "box",
        "rect": "box", "homePlate": "horizon", "chevron": "horizon"}
count = {}
for sh in list(walk(s.shapes)):
    if sh.name.startswith(("slot.", "struct.")):
        continue
    part = PART.get(kind(sh), "shape")
    count[part] = count.get(part, 0) + 1
    sh.name = "struct.%s.%d" % (part, count[part])



def radius(sh, r=0.05):
    av = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst"))
    gd = av.find(qn("a:gd"))
    if gd is None:
        gd = etree.SubElement(av, qn("a:gd"))
        gd.set("name", "adj")
    gd.set("fmla", "val %d" % round(r / (min(sh.width, sh.height) / EMU) * 100000))


for sh in walk(s.shapes):                                         # one card radius across the slide
    if kind(sh) == "roundRect" and min(sh.width, sh.height) > 0.2 * EMU:
        radius(sh)

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
out = save(prs, "DL15", th, archetype="value-horizons", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
