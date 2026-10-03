"""DL12 build: the three-panel governance model (hub of roles, gated decision workflow, escalation guardrails).

Lifted from d01-s094. Run: python3 build.py [--out PATH]. Deterministic (P21).
"""
from __future__ import annotations

import argparse
import math
import shutil
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SKILL / "scripts"))
from devwork import *  # noqa: E402,F401,F403
from devwork import EMU, find, open_lifted, rename, delete, move, text, icon, save, qn  # noqa: E402
from deckkit import prims, text as txt  # noqa: E402
from deckkit.canvas import Box  # noqa: E402
from lxml import etree  # noqa: E402

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
VARIANT = "role-hub-workflow-escalation"


def flatten(s):
    """Lift every group's children onto the slide (all lifted groups carry an identity transform)."""
    tree = s.shapes._spTree
    while True:
        grps = [el for el in tree if etree.QName(el).localname == "grpSp"]
        if not grps:
            return
        for g in grps:
            off = g.find(qn("p:grpSpPr") + "/" + A + "xfrm")
            o, e = off.find(A + "off"), off.find(A + "ext")
            co, ce = off.find(A + "chOff"), off.find(A + "chExt")
            assert (o.get("x"), o.get("y"), e.get("cx"), e.get("cy")) == \
                   (co.get("x"), co.get("y"), ce.get("cx"), ce.get("cy")), "non-identity group"
            idx = list(tree).index(g)
            kids = [c for c in g if etree.QName(c).localname in ("sp", "grpSp", "cxnSp", "pic")]
            for k, c in enumerate(kids):
                tree.insert(idx + 1 + k, c)
            tree.remove(g)


def para(head, body, size, role="ink-deep", body_role=None, align=None):
    kw = {} if align is None else {"align": align}
    out = [txt.Para((txt.Run(head, role, bold=True, size=size),), space_before=0, **kw)]
    if body:
        out.append(txt.Para((txt.Run(body, body_role or role, bold=False, size=size),), space_before=2, **kw))
    return out


def set_insets(s, name, l=0.06, t=0.04, r=0.06, b=0.04, wrap=True):
    bp = find(s, name)._element.find(".//" + A + "bodyPr")
    for k, v in (("lIns", l), ("tIns", t), ("rIns", r), ("bIns", b)):
        bp.set(k, str(int(round(v * EMU))))
    bp.set("wrap", "square")
    for c in list(bp):
        if etree.QName(c).localname in ("spAutoFit", "normAutofit", "noAutofit"):
            bp.remove(c)


def arc(s, cx, cy, R, a1, a2, name, th):
    """An open quarter-ring segment (one cubic) from angle a1 to a2 in degrees, y down: a line, not a box."""
    t1, t2 = math.radians(a1), math.radians(a2)
    k = 4.0 / 3.0 * math.tan((t2 - t1) / 4.0)
    p0 = (cx + R * math.cos(t1), cy + R * math.sin(t1))
    p3 = (cx + R * math.cos(t2), cy + R * math.sin(t2))
    p1 = (p0[0] - k * R * math.sin(t1), p0[1] + k * R * math.cos(t1))
    p2 = (p3[0] + k * R * math.sin(t2), p3[1] - k * R * math.cos(t2))
    xs, ys = [p[0] for p in (p0, p1, p2, p3)], [p[1] for p in (p0, p1, p2, p3)]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    w, h = max(x1 - x0, 0.01), max(y1 - y0, 0.01)
    sh = s.shapes.add_shape(1, int(x0 * EMU), int(y0 * EMU), int(w * EMU), int(h * EMU))
    sh.name = name
    sp = sh._element.spPr
    W, H = int(w * EMU), int(h * EMU)

    def pt(p):
        e = etree.Element(A + "pt")
        e.set("x", str(int(round((p[0] - x0) * EMU))))
        e.set("y", str(int(round((p[1] - y0) * EMU))))
        return e
    cg = etree.Element(A + "custGeom")
    for t in ("avLst", "gdLst", "ahLst", "cxnLst"):
        etree.SubElement(cg, A + t)
    rc = etree.SubElement(cg, A + "rect", l="0", t="0", r="r", b="b")
    del rc
    pl = etree.SubElement(cg, A + "pathLst")
    path = etree.SubElement(pl, A + "path", w=str(W), h=str(H), fill="none")
    mv = etree.SubElement(path, A + "moveTo")
    mv.append(pt(p0))
    cb = etree.SubElement(path, A + "cubicBezTo")
    for p in (p1, p2, p3):
        cb.append(pt(p))
    sp.replace(sp.find(A + "prstGeom"), cg)
    prims.set_fill(sh, None, theme=th)
    prims.set_line(sh, "ink-muted", 0.75, theme=th, dash="dash")
    tx = sh._element.find(qn("p:txBody"))
    if tx is not None:
        sh._element.remove(tx)
    return sh


def build():
    prs, s, th = open_lifted("DL12")
    prims.bind(th)
    flatten(s)

    # 1. house-rule cuts: subtitle, foot band, column foot sentences, column number kickers, lifted dots
    for n in ("dev.3", "dev.4", "dev.5", "dev.6", "dev.13", "dev.14", "dev.52", "dev.53", "dev.54",
              "dev.15", "dev.47", "dev.49", "dev.51"):
        delete(s, n)

    # title
    delete(s, "dev.2")
    txt.title(s, "Three governance layers settle every delivery decision within ten days",
              keywords=("Three governance layers",), theme=th, name="slot.title")

    TOP, BOT = 0.92, 6.40
    # column headers and dividers
    heads = (("dev.8", 0.50, 4.40, "Operating model"), ("dev.9", 5.16, 4.63, "Decision workflow"),
             ("dev.10", 10.04, 2.86, "Escalation guardrails"))
    for i, (n, x, w, label) in enumerate(heads, 1):
        nm = "slot.column.%d.head" % i
        rename(s, n, nm)
        move(s, nm, x, TOP, w, 0.46)
        prims.set_fill(find(s, nm), "accent", theme=th)
        set_insets(s, nm, 0.1, 0.04, 0.1, 0.04)
        text(s, nm, [txt.Para((txt.Run(label, "on-accent", bold=True, size=12),), align="ctr")], th,
             size=12, background="accent", anchor="middle")
    for i, (n, x) in enumerate((("dev.11", 5.03), ("dev.12", 9.92)), 1):
        nm = "struct.divider.%d" % i
        rename(s, n, nm)
        move(s, nm, x, TOP, 0, BOT - TOP)
        prims.set_line(find(s, nm), "hairline", 0.75, theme=th, dash="dash")

    # 2. left: the role hub
    cx, cy, R, d = 2.70, 4.02, 1.15, 0.66
    core = 1.46
    rename(s, "dev.20", "struct.hub.core")
    move(s, "struct.hub.core", cx - core / 2, cy - core / 2, core, core)
    prims.set_fill(find(s, "struct.hub.core"), "accent", theme=th)
    nodes = (("dev.18", -90), ("dev.16", 0), ("dev.19", 90), ("dev.17", 180))   # top, right, bottom, left
    centres = []
    for i, (n, ang) in enumerate(nodes, 1):
        nm = "struct.hub.node.%d" % i
        rename(s, n, nm)
        px, py = cx + R * math.cos(math.radians(ang)), cy + R * math.sin(math.radians(ang))
        centres.append((px, py))
        move(s, nm, px - d / 2, py - d / 2, d, d)
        prims.set_fill(find(s, nm), "accent-tint", theme=th)
    gap = math.degrees(2 * math.asin((d / 2) / (2 * R)))
    for i, a0 in enumerate((-90, 0, 90, 180), 1):
        arc(s, cx, cy, R, a0 + gap, a0 + 90 - gap, "struct.hub.ring.%d" % i, th)
    icon(s, "slot.hub.core.icon", "user-check", cx - 0.16, cy - 0.56, 0.32, th, role="on-accent")
    for i, (g, (px, py)) in enumerate(zip(("map", "chart-column", "shield-alert", "users"), centres), 1):
        icon(s, "slot.hub.node.%d.icon" % i, g, px - 0.16, py - 0.16, 0.32, th, role="accent-ink")

    rename(s, "dev.21", "slot.hub.core.text")
    move(s, "slot.hub.core.text", cx - 0.60, cy - 0.20, 1.20, 0.76)
    set_insets(s, "slot.hub.core.text", 0.02, 0.02, 0.02, 0.02)
    text(s, "slot.hub.core.text", para("Program office", "Runs the weekly steering", 10, "on-accent",
                                       align="ctr"), th, size=10, background="accent")
    labels = (  # name, box, head, body, align
        ("dev.22", (3.12, cy - 1.72, 1.76, 0.58), "Product owner", "Sets scope and priorities", "l"),
        ("dev.24", (3.76, cy + 0.68, 1.14, 0.60), "Analytics lead", "Owns the baselines", "l"),
        ("dev.25", (0.52, cy + 1.18, 1.76, 0.58), "Risk partner", "Reviews controls each month", "r"),
        ("dev.23", (0.52, cy - 1.02, 1.14, 0.60), "Squad leads", "Ship each sprint", "r"),
    )
    for i, (n, (x, y, w, h), hd, bd, al) in enumerate(labels, 1):
        nm = "slot.hub.node.%d.text" % i
        rename(s, n, nm)
        move(s, nm, x, y, w, h)
        set_insets(s, nm, 0.02, 0.02, 0.02, 0.02)
        text(s, nm, para(hd, bd, 10, "ink-deep", align=al), th, size=10)

    # 3. middle: four gated stages, a down chevron, three forums with their cadence
    tw, tg, x0 = 1.09, 0.09, 5.16
    t_top, t_h = 1.58, 1.42
    stages = (("dev.29", "dev.33", "crosshair", "Intake", "Product owner"),
              ("dev.30", "dev.34", "file-search", "Scoping", "Analytics lead"),
              ("dev.31", "dev.35", "cog", "Build", "Squad leads"),
              ("dev.32", "dev.36", "file-check", "Release", "Risk partner"))
    for i, (tile, lab, g, hd, bd) in enumerate(stages, 1):
        x = x0 + (i - 1) * (tw + tg)
        tn, ln = "struct.stage.%d" % i, "slot.stage.%d.text" % i
        rename(s, tile, tn)
        move(s, tn, x, t_top, tw, t_h)
        prims.set_fill(find(s, tn), "accent-tint", theme=th)
        prims.set_line(find(s, tn), "accent", 0.75, theme=th)
        icon(s, "slot.stage.%d.icon" % i, g, x + tw / 2 - 0.19, t_top + 0.20, 0.38, th, role="accent-ink")
        rename(s, lab, ln)
        move(s, ln, x + 0.05, t_top + 0.68, tw - 0.10, 0.58)
        set_insets(s, ln, 0.02, 0.02, 0.02, 0.02)
        text(s, ln, para(hd, bd, 10, "ink-deep", align="ctr"), th, size=10, background="accent-tint")

    # down chevron pair (two loose chevrons, same box family, nested by design)
    rename(s, "dev.41", "struct.flow.down.1")
    rename(s, "dev.42", "struct.flow.down.2")
    dx = 7.475
    move(s, "struct.flow.down.1", dx - 0.09, 3.34, 0.18, 0.30)
    move(s, "struct.flow.down.2", dx - 0.09, 3.20, 0.18, 0.30)
    for n in ("struct.flow.down.1", "struct.flow.down.2"):
        prims.set_fill(find(s, n), "ink-strong", theme=th)
        prims.set_line(find(s, n), None, theme=th)

    f_top, f_h = 3.86, 0.62
    forums = (("dev.43", "dev.37", "Squad review", "Weekly", "Clears blockers within five days"),
              ("dev.44", "dev.38", "Steering forum", "Monthly", "Approves budget shifts"),
              ("dev.45", "dev.39", "Executive board", "Quarterly", "Sets direction and funding"))
    fw, fstep = 1.61, 1.51
    for i, (chev, cap, hd, cad, bd) in enumerate(forums, 1):
        x = x0 + (i - 1) * fstep
        cn, tn = "slot.forum.%d.head" % i, "slot.forum.%d.body" % i
        rename(s, chev, cn)
        move(s, cn, x, f_top, fw, f_h)
        prims.set_fill(find(s, cn), "accent", theme=th)
        prims.set_line(find(s, cn), None, theme=th)
        set_insets(s, cn, 0.12 if i > 1 else 0.06, 0.03, 0.08, 0.03)
        text(s, cn, [txt.Para((txt.Run(hd, "on-accent", bold=True, size=10),), align="ctr")], th, size=10,
             background="accent", anchor="middle")
        rename(s, cap, tn)
        cw = 1.42
        move(s, tn, x + (fw - 0.16) / 2 - cw / 2 + (0.08 if i > 1 else 0), 4.68, cw, 1.30)
        prims.set_fill(find(s, tn), "card", theme=th)
        prims.set_line(find(s, tn), "hairline", 0.75, theme=th)
        set_insets(s, tn, 0.10, 0.10, 0.10, 0.10)
        text(s, tn, para(cad, bd, 12, "ink-deep", align="ctr"), th, size=12, background="card", anchor="middle")

    # 4. right: escalation guardrails, three severities, each routed down to the next
    cards = (("dev.26", "Within tolerance", "Squads decide and record it in the sprint log", "ink-strong", "check"),
             ("dev.27", "Date or budget at risk", "Steering decides in five days", "accent",
              "triangle-alert"),
             ("dev.28", "Scope or control breach", "Board decides in ten days", "accent-deep",
              "x"))
    c_x, c_w, c_h, c_gap = 10.11, 2.72, 1.20, 0.58
    for i, (n, hd, bd, dot, g) in enumerate(cards, 1):
        y = 1.58 + (i - 1) * (c_h + c_gap)
        nm = "slot.card.%d.text" % i
        rename(s, n, nm)
        move(s, nm, c_x, y, c_w, c_h)
        fill = "accent-tint" if i == 2 else "accent-wash"
        prims.set_fill(find(s, nm), fill, theme=th)
        prims.set_line(find(s, nm), "accent", 0.75, theme=th)
        set_insets(s, nm, 0.14, 0.10, 0.58, 0.10)
        text(s, nm, para(hd, bd, 11, "ink-deep"), th, size=11, background=fill, anchor="middle")
        side = 0.34
        prims.circle(s, Box(c_x + c_w - side - 0.14, y + (c_h - side) / 2, side, side), fill=dot,
                     name="struct.card.%d.dot" % i, theme=th)
        icon(s, "slot.card.%d.icon" % i, g, c_x + c_w - side - 0.14 + 0.08, y + (c_h - side) / 2 + 0.08, 0.18, th,
             role="paper" if dot != "accent" else "on-accent")
        if i > 1:
            prims.connect(s, (c_x + c_w / 2, y - c_gap), (c_x + c_w / 2, y), head="end", role="ink-muted",
                          name="struct.escalate.%d" % (i - 1), theme=th)
    return prs, th


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    a = ap.parse_args()
    prs, th = build()
    from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
    finish(prs.slides[0], th)
    out = save(prs, "DL12", th, archetype="governance-model", variant=VARIANT)
    if a.out and Path(a.out).resolve() != out.resolve():
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(out, a.out)
    print(out)


if __name__ == "__main__":
    main()
