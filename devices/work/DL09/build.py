"""DL09: value climbs an S-curve across four horizons, operating vignettes ride above it, value callouts below."""
import argparse
import copy
import shutil
import sys
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import prims  # noqa: E402
from deckkit import text as txt  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL09")
VARIANT = "s-curve-vignettes"
TOP, F = 1.62, 0.957            # the climb field is compressed toward its top so the value row clears the foot
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


def Y(y):
    return TOP + (y - TOP) * F


def sh(n):
    return find(s, n if isinstance(n, str) else "dev.%d" % n)


def box(n):
    x = sh(n)
    return x.left / EMU, x.top / EMU, x.width / EMU, x.height / EMU


def shift(names, dy, dx=0.0):
    for n in names:
        x = sh(n)
        x.top = int(x.top + dy * EMU)
        x.left = int(x.left + dx * EMU)


def tight(name, v=0.02, side=0.04):
    bp = sh(name)._element.find(".//" + qn("a:bodyPr"))
    for k, val in (("tIns", v), ("bIns", v), ("lIns", side), ("rIns", side)):
        bp.set(k, str(int(val * EMU)))


def R(t, role="ink", bold=False, size=10):
    return txt.Run(t, role, bold=bold, size=size)


def P(*runs, align=None, sb=0):
    return txt.Para(tuple(runs), space_before=sb, **({"align": align} if align else {}))


# ---- 1. flatten every group into slide space, then drop every vector icon (corpus art) for curated glyphs
def flatten():
    tree = s.shapes._spTree
    while True:
        g = next((e for e in tree if e.tag == qn("p:grpSp")), None)
        if g is None:
            return
        xf = g.find(qn("p:grpSpPr") + "/" + qn("a:xfrm"))
        off, ext, cho, che = (xf.find(qn("a:" + t)) for t in ("off", "ext", "chOff", "chExt"))
        sx = int(ext.get("cx")) / max(int(che.get("cx")), 1)
        sy = int(ext.get("cy")) / max(int(che.get("cy")), 1)
        for c in list(g):
            if c.tag in (qn("p:nvGrpSpPr"), qn("p:grpSpPr")):
                continue
            cx = c.find("./*/" + qn("a:xfrm"))
            o, e = cx.find(qn("a:off")), cx.find(qn("a:ext"))
            o.set("x", str(round(int(off.get("x")) + (int(o.get("x")) - int(cho.get("x"))) * sx)))
            o.set("y", str(round(int(off.get("y")) + (int(o.get("y")) - int(cho.get("y"))) * sy)))
            e.set("cx", str(round(int(e.get("cx")) * sx)))
            e.set("cy", str(round(int(e.get("cy")) * sy)))
            g.addprevious(c)
        tree.remove(g)


flatten()
ICONS = ([26, 27, 28] + list(range(31, 45)) + [50] + list(range(53, 59)) + [61] + list(range(65, 69))
         + list(range(71, 74)) + list(range(77, 96)) + list(range(102, 129)) + list(range(141, 149))
         + list(range(155, 182)) + list(range(193, 211)))
for n in ICONS:
    try:
        delete(s, "dev.%d" % n)
    except KeyError:
        pass               # a group that flattening already dissolved

# ---- 2. compress the climb field: rigid clusters move with the curve
pics = [p["box_in"] for p in __import__("json").loads((Path(__file__).resolve().parent / "lift.json").read_text())["pictures_removed"]]
VIG = {"a": [97, 98, 99, 100, 101, 129, 130, 131],
       "b": [150, 151, 152, 153, 154, 182, 183, 184, 185, 186],
       "c": [188, 189, 190, 191, 192, 211, 212, 213, 214],
       "d": [132, 133, 134, 135, 136, 137, 138, 139, 140]}
vdy = {}
for k, ns in VIG.items():
    t = min(box(n)[1] for n in ns)
    vdy[k] = Y(t) - t + {"a": -0.22, "b": -0.35}.get(k, 0.0)
    shift(ns, vdy[k])
RINGS = [(219, 220), (222, 223), (231, 232), (225, 226), (216, 217), (228, 229)]   # left to right
centres = []
for outer, inner in RINGS:
    x, y, w, h = box(outer)
    cy = y + h / 2
    shift([outer, inner], Y(cy) - cy)
    centres.append((x + w / 2, Y(cy)))

# ---- 3. the curve and the area under it, redrawn through the ring centres (Catmull-Rom as cubic Beziers)
BOTTOM = 5.88
CURVE, AREA = 3, 2


def bez_path(points):
    segs = []
    p = ([(2 * points[0][0] - points[1][0], points[0][1])] + points
         + [(2 * points[-1][0] - points[-2][0], points[-1][1])])      # level tangents at both ends
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        segs.append((c1, c2, p2))
    return segs


def set_geom(n, points, closed):
    x0 = min(p[0] for p in points)
    x1 = max(p[0] for p in points)
    y0 = min(p[1] for p in points)
    y1 = BOTTOM if closed else max(p[1] for p in points)
    W, H = int((x1 - x0) * EMU), int((y1 - y0) * EMU)

    def pt(p):
        return '<a:pt x="%d" y="%d"/>' % (round((p[0] - x0) * EMU), round((p[1] - y0) * EMU))
    body = "<a:moveTo>%s</a:moveTo>" % pt(points[0])
    for c1, c2, e in bez_path(points):
        body += "<a:cubicBezTo>%s%s%s</a:cubicBezTo>" % (pt(c1), pt(c2), pt(e))
    if closed:
        body += "<a:lnTo>%s</a:lnTo><a:lnTo>%s</a:lnTo><a:close/>" % (pt((x1, y1)), pt((x0, y1)))
    xml = ('<a:custGeom xmlns:a="%s"><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/><a:rect l="0" t="0" r="r" b="b"/>'
           '<a:pathLst><a:path w="%d" h="%d"%s>%s</a:path></a:pathLst></a:custGeom>'
           % (A_NS, W, H, "" if closed else ' fill="none"', body))
    old = sh(n)._element.find(".//" + qn("a:custGeom"))
    old.getparent().replace(old, etree.fromstring(xml))
    move(s, "dev.%d" % n, x0, y0, (x1 - x0), (y1 - y0))


set_geom(CURVE, centres, False)


def sample(points, per=60):
    pts = [points[0]]
    p0 = points[0]
    for c1, c2, e in bez_path(points):
        for k in range(1, per + 1):
            t = k / per
            u = 1 - t
            pts.append((u ** 3 * p0[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * e[0],
                        u ** 3 * p0[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * e[1]))
        p0 = e
    return pts


def at(pts, x):
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        if xa <= x <= xb:
            return ya + (yb - ya) * (x - xa) / max(xb - xa, 1e-9)
    return pts[-1][1]


# the area under the climb, one slice per horizon so each slice's box clears the vignettes above the curve
CURVE_PTS = sample(centres)
GUIDES = [box(n)[0] for n in (4, 5, 6)]
EDGES = [centres[0][0]] + GUIDES + [centres[-1][0]]
area_el = sh(AREA)._element
for i, (xa, xb) in enumerate(zip(EDGES, EDGES[1:]), 1):
    poly = [(xa, at(CURVE_PTS, xa))] + [p for p in CURVE_PTS if xa < p[0] < xb] + [(xb, at(CURVE_PTS, xb))]
    rings = [cy - 0.09 for cx, cy in centres if xa - 0.001 <= cx <= xb + 0.001]
    y0 = min([y for _, y in poly] + rings) - 0.005
    W, H = int((xb - xa) * EMU), int((BOTTOM - y0) * EMU)

    def pt(q):
        return '<a:pt x="%d" y="%d"/>' % (round((q[0] - xa) * EMU), round((q[1] - y0) * EMU))
    body = "<a:moveTo>%s</a:moveTo>" % pt(poly[0]) + "".join("<a:lnTo>%s</a:lnTo>" % pt(q) for q in poly[1:])
    body += "<a:lnTo>%s</a:lnTo><a:lnTo>%s</a:lnTo><a:close/>" % (pt((xb, BOTTOM)), pt((xa, BOTTOM)))
    xml = ('<a:custGeom xmlns:a="%s"><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/><a:rect l="0" t="0" r="r" b="b"/>'
           '<a:pathLst><a:path w="%d" h="%d">%s</a:path></a:pathLst></a:custGeom>' % (A_NS, W, H, body))
    el = area_el if i == 1 else copy.deepcopy(area_el)
    if i > 1:
        prev.addnext(el)
        el.find(".//" + qn("p:cNvPr")).set("id", str(ooxml.next_id(s)))
    prev = el
    el.find(".//" + qn("p:cNvPr")).set("name", "struct.climb.area.%d" % i)
    old = el.find(".//" + qn("a:custGeom"))
    old.getparent().replace(old, etree.fromstring(xml))
    move(s, "struct.climb.area.%d" % i, xa, y0, xb - xa, BOTTOM - y0)
    prims.set_fill(sh("struct.climb.area.%d" % i), "accent-wash", theme=th)
rename(s, "dev.3", "struct.climb.curve")
for k, (o, i) in enumerate(RINGS, 1):
    rename(s, "dev.%d" % o, "struct.marker.%d" % k)
    rename(s, "dev.%d" % i, "struct.marker.%d.core" % k)
for k, n in enumerate((4, 5, 6), 1):
    rename(s, "dev.%d" % n, "struct.guide.%d" % k)
    x = box("struct.guide.%d" % k)[0]
    move(s, "struct.guide.%d" % k, x, TOP, 0, BOTTOM - TOP)

# ---- 4. title and horizon chevrons
rename(s, "dev.7", "slot.title")
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "Planning value climbs fastest once agents take over the routine steps",
    ("agents take over",))))], th, size=22, bold=True, anchor="middle")
HZ = [(8, "Today", "accent-wash"), (9, "Year 1", "accent-tint"), (10, "Year 2", "accent-tint"),
      (11, "Year 3 onward", "accent")]
for i, (n, label, bg) in enumerate(HZ, 1):
    rename(s, "dev.%d" % n, "slot.horizon.%d" % i)
    role = "on-accent" if bg == "accent" else "ink-deep"
    text(s, "slot.horizon.%d" % i, [P(R(label, role, True, 12), align="center")], th, size=12, background=bg,
         anchor="middle")

# ---- 5. operating vignettes: humans in accent chevrons, agents in the others, one output at the end
#  headers grow upward into two lines at 9.5pt
HEAD = {"a": (97, 98, "Planners run every step by hand"),
        "b": (150, 151, "Agents prepare the inputs, planners decide"),
        "c": (188, 189, "Agents draft the plan, planners approve")}
for k, (hd, card, words) in HEAD.items():
    cx, cy, cw, ch = box(card)
    move(s, "dev.%d" % hd, cx, cy - 0.44, cw, 0.40)
    rename(s, "dev.%d" % card, "struct.vignette.%s.card" % k)
    rename(s, "dev.%d" % hd, "slot.vignette.%s.head" % k)
    tight("slot.vignette.%s.head" % k, 0.02, 0.04)
    text(s, "slot.vignette.%s.head" % k, [P(R(words, "ink-deep", True, 9.5), align="center")], th, size=9.5,
         anchor="middle")
rename(s, "dev.133", "struct.vignette.d.card")
rename(s, "dev.132", "slot.vignette.d.head")
text(s, "slot.vignette.d.head", [P(R("Agents run the cycle,", "ink-deep", True, 11)),
                                 P(R("one planner oversees", "ink", False, 11))], th, size=11, anchor="middle")

STEPS = {  # chevron: (vignette, kind)
    99: ("a", "human"), 100: ("a", "human"), 101: ("a", "human"),
    185: ("b", "agent"), 186: ("b", "agent"), 152: ("b", "human"), 153: ("b", "human"), 154: ("b", "human"),
    190: ("c", "human"), 191: ("c", "agent"), 192: ("c", "human"), 214: ("c", "agent"),
    134: ("d", "agent"), 135: ("d", "agent"), 136: ("d", "agent")}
count = {}
for n, (v, kind) in STEPS.items():
    count[v] = count.get(v, 0) + 1
    nm = "struct.vignette.%s.step.%d" % (v, count[v])
    rename(s, "dev.%d" % n, nm)
    x, y, w, h = box(nm)
    side = min(0.19, h - 0.06)
    fill = sh(nm)._element.find(qn("p:spPr") + "/" + qn("a:solidFill") + "/" + qn("a:schemeClr")).get("val")
    role = "on-accent" if fill == "accent1" else "ink-deep"
    icon(s, nm + ".icon", "user" if kind == "human" else "bot", x + (w - side) / 2 - 0.02, y + (h - side) / 2,
         side, th, role=role)
rename(s, "dev.140", "struct.vignette.d.overseer")
x, y, w, h = box("struct.vignette.d.overseer")
icon(s, "struct.vignette.d.overseer.icon", "user", x + (w - 0.15) / 2, y + (h - 0.15) / 2, 0.15, th, role="on-accent")
for v, ns in (("a", (129, 130, 131)), ("b", (182, 183, 184)), ("c", (211, 212, 213)), ("d", (137, 138, 139))):
    for j, n in enumerate(ns, 1):
        rename(s, "dev.%d" % n, "struct.vignette.%s.link.%d" % (v, j))
# outputs: a database for the hand-run horizons, a plan file for the agent-run ones
OUT = {(2.191, 4.509): ("a", "database"), (4.123, 3.321): ("b", "database"),
       (6.855, 2.56): ("c", "file-text"), (9.712, 2.043): ("d", "file-text")}
for (px, py), (v, g) in OUT.items():
    pw = next(p for p in pics if round(p[0], 3) == px and round(p[1], 3) == py)
    side = 0.24
    icon(s, "struct.vignette.%s.output" % v, g, px + (pw[2] - side) / 2, py + vdy[v] + (pw[3] - side) / 2, side,
         th, role="ink-deep")

# ---- 6. value callouts below the curve: a ringed icon disc and one line of value, stepping up by horizon
rename(s, "dev.25", "struct.start.disc")
move(s, "struct.start.disc", 0.98, 5.46, 0.36, 0.36)
icon(s, "struct.start.icon", "trending-up", 1.07, 5.55, 0.18, th, role="on-accent")
rename(s, "dev.23", "slot.start")
move(s, "slot.start", 1.40, 5.44, 1.86, 0.40)
tight("slot.start", 0.02, 0.04)
text(s, "slot.start", [P(R("Manual weekly cycle", "ink-deep", True, 10.5))], th, size=10.5,
     background="accent-wash", anchor="middle")

CALLOUTS = [  # (disc, text shape, glyph, x, y, keyword, rest)
    (49, 47, "coins", 3.48, 4.52, "Working capital", "released from safety stock"),
    (30, 29, "boxes", 3.48, 5.18, "Stock counts", "reconciled every night"),
    (60, 59, "target", 6.26, 3.70, "Service level", "held through demand swings"),
    (52, 45, "chart-column", 6.26, 4.38, "Forecast error", "tracked by product family"),
    (70, 69, "timer", 9.08, 3.52, "Plan cycle", "cut from days to hours"),
    (64, 63, "truck", 9.08, 4.18, "Expedited freight", "largely avoided"),
    (76, 74, "factory", 9.08, 4.84, "Plants", "scheduled to live demand"),
]
for i, (d, t, g, x, y, kw, rest) in enumerate(CALLOUTS, 1):
    rename(s, "dev.%d" % d, "struct.value.%d.disc" % i)
    move(s, "struct.value.%d.disc" % i, x, y, 0.36, 0.36)
    icon(s, "slot.value.%d.icon" % i, g, x + 0.08, y + 0.08, 0.20, th, role="accent")
    rename(s, "dev.%d" % t, "slot.value.%d.text" % i)
    tw = 2.06 if x < 9 else 3.10
    move(s, "slot.value.%d.text" % i, x + 0.44, y - 0.04, tw, 0.44)
    tight("slot.value.%d.text" % i, 0.02, 0.04)
    text(s, "slot.value.%d.text" % i, [P(R(kw, "ink-deep", True, 10), R(" " + rest, "ink", False, 10))], th,
         size=10, background="accent-wash", anchor="middle")

# ---- 7. value row: what full scale returns, one label block and five columns
SY, SH = 5.98, 0.80
rename(s, "dev.12", "struct.value-row")
move(s, "struct.value-row", 0.52, SY, 12.37, SH)
rename(s, "dev.13", "slot.value-row.label")
move(s, "slot.value-row.label", 0.64, SY + 0.10, 1.98, SH - 0.20)
tight("slot.value-row.label", 0.02, 0.10)
text(s, "slot.value-row.label", [P(R("Value at full scale", "on-accent", True, 11))], th, size=11,
     background="accent", anchor="middle")
icon(s, "slot.value-row.icon", "piggy-bank", 2.24, SY + 0.26, 0.28, th, role="on-accent")
COLS = [(14, "Lower inventory", "Less cover held across the network"),
        (15, "Higher service", "Fill rate steady through peaks"),
        (16, "Less freight", "Fewer rush loads every quarter"),
        (17, "Faster cycle", "Weekly plan becomes a daily one"),
        (18, "Planner time", "Shifted to supplier and customer issues")]
X0, CW = 2.82, (12.84 - 2.82) / 5
for i, (n, head, body) in enumerate(COLS, 1):
    nm = "slot.value-row.%d" % i
    rename(s, "dev.%d" % n, nm)
    move(s, nm, X0 + (i - 1) * CW + 0.10, SY + 0.06, CW - 0.18, SH - 0.12)
    tight(nm, 0.02, 0.04)
    text(s, nm, [P(R(head, "ink-deep", True, 10.5)), P(R(body, "ink", False, 10), sb=2)], th, size=10.5,
         anchor="top")
for i, n in enumerate((19, 20, 21, 22), 1):
    nm = "struct.value-row.divider.%d" % i
    rename(s, "dev.%d" % n, nm)
    move(s, nm, X0 + i * CW, SY + 0.12, 0, SH - 0.24)

for x in s.shapes:
    g = x._element.find(".//" + qn("a:prstGeom"))
    if g is not None and g.get("prst") == "roundRect":
        av = g.find(qn("a:avLst"))
        for c in list(av):
            av.remove(c)
        etree.SubElement(av, qn("a:gd"), name="adj", fmla="val %d" % round(0.05 / min(x.width, x.height) * EMU * 1e5))

leftover = [x.name for x in s.shapes if x.name.startswith("dev.")]
assert not leftover, leftover
out = save(prs, "DL09", th, archetype="value-horizons", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
