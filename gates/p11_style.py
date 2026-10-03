"""P11 style: no p:style, no gradient, no blurred or large shadow, no 3D or glow, no autofit, faces from the theme, the half-point ladder.

Read from the slide, layout and master XML (a ghost shadow lives in a style reference, not in a property
python-pptx shows) and from the read layer's resolved effects, so a shadow arriving through a theme
effect style is seen too. The theme's own fmtScheme must be flat (the second defence). A content slide's
title is set at the canvas title size. Every rounded card (the shared card set: rounded rect presets filled in a
card role or outlined) takes the canvas radius (WIDE 0.05in, STD 0.04in) within 0.01in, so one physical corner
runs through the deck.
"""
from __future__ import annotations

import re
import sys

from _shared import bx, FAIL, Finding, cards, cli
from deckkit.read.ns import local

GATE, TITLE = "P11", "style"
ONE_PX = 9525           # EMU: a shadow blurred or offset by more than a pixel is the soft-shadow tell
SHAPES = ("sp", "cxnSp", "pic", "grpSp", "graphicFrame")
MONO = re.compile(r"mono|courier|consolas|menlo|monaco|code|typewriter", re.I)
ROUNDED = ("roundRect", "round1Rect", "round2SameRect", "round2DiagRect", "snipRoundRect")
RADIUS_TOL = 0.01


def _owner(el):
    cur = el
    while cur is not None:
        if isinstance(cur.tag, str) and local(cur) in SHAPES:
            for c in cur.iter("{*}cNvPr"):
                return c.get("name") or "id %s" % c.get("id")
        cur = cur.getparent()
    return "background"


def _xml_checks(root, where_slide, out, part):
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        n = local(el)
        if n == "style" and el.getparent() is not None and local(el.getparent()) in SHAPES:
            refs = ", ".join("%s %s" % (local(c), c.get("idx")) for c in el)
            out.append(Finding(GATE, FAIL, where_slide, _owner(el), "<p:style> (%s) in %s" % (refs, part)))
        elif n == "gradFill":
            out.append(Finding(GATE, FAIL, where_slide, _owner(el), "gradient fill in %s" % part))
        elif n in ("outerShdw", "prstShdw"):
            blur, dist = int(el.get("blurRad", "0")), int(el.get("dist", "0"))
            if blur > ONE_PX or dist > ONE_PX:
                out.append(Finding(GATE, FAIL, where_slide, _owner(el), "shadow blur %.1fpt, offset %.1fpt in %s"
                                   % (blur / 12700, dist / 12700, part)))
        elif n in ("innerShdw", "glow", "reflection", "softEdge", "blur"):
            out.append(Finding(GATE, FAIL, where_slide, _owner(el), "%s effect in %s" % (n, part)))
        elif n in ("scene3d", "sp3d"):
            out.append(Finding(GATE, FAIL, where_slide, _owner(el), "3D (%s) in %s" % (n, part)))
        elif n in ("normAutofit", "spAutoFit"):
            out.append(Finding(GATE, FAIL, where_slide, _owner(el), "autofit (%s) in %s" % (n, part)))


def run(deck, ctx):
    out = []
    th, dr = ctx.theme, ctx.dr
    nf = th.fonts.get("numerals") or {}
    faces = {th.fonts["major"], th.fonts["minor"]}
    if nf:
        base = nf.get("face", "Montserrat")
        faces |= {base, "%s %s" % (base, nf.get("weight", "SemiBold")), base + " Medium", base + " Bold"}
    for i in range(1, ctx.n + 1):
        part = dr.slide_part(i)
        _xml_checks(dr.xml(part), i, out, part)
        s = ctx.slide(i)
        for L in s["shapes"]:
            e = L.get("effects") or {}
            if e.get("via", "").startswith("style") and (e.get("shadow") or e.get("glow") or e.get("soft_edge")):
                out.append(Finding(GATE, FAIL, i, L["name"], "effect through a theme style (%s)" % e["via"]))
            tx = L.get("text")
            if not tx:
                continue
            for p in tx["paragraphs"]:
                for r in p["runs"]:
                    if not r["t"].strip():
                        continue
                    if r["font"] not in faces:
                        why = "a mono face on glass" if MONO.search(r["font"] or "") else "not a theme face"
                        out.append(Finding(GATE, FAIL, i, L["name"], "face %r is %s (%s): %r"
                                           % (r["font"], why, ", ".join(sorted(faces)), r["t"][:30])))
                    if abs(r["size_pt"] * 2 - round(r["size_pt"] * 2)) > 1e-6:
                        out.append(Finding(GATE, FAIL, i, L["name"], "%.2fpt is off the half-point ladder" % r["size_pt"]))
        want = ctx.canvas.radius_in
        for c in cards(s, ctx):
            g = c["L"].get("geom") or {}
            r = g.get("radius_in")
            x0, y0, x1, y1 = bx(c["L"])
            full_round = r is not None and r >= 0.45 * min(x1 - x0, y1 - y0)     # a pill or a circle, not a corner
            if g.get("prst") in ROUNDED and r is not None and not full_round and abs(r - want) > RADIUS_TOL:
                out.append(Finding(GATE, FAIL, i, c["L"]["name"], "card radius %.3fin, the %s canvas sets %.2fin "
                                   "(within %.2fin)" % (r, ctx.canvas.name, want, RADIUS_TOL)))
        if not ctx.is_frame(i):
            for L in s["shapes"]:
                if L["name"] == "title" and L.get("text"):
                    szs = {r["size_pt"] for p in L["text"]["paragraphs"] for r in p["runs"] if r["t"].strip()}
                    if szs and szs != {ctx.canvas.title_pt}:
                        out.append(Finding(GATE, FAIL, i, "title", "title at %s pt, the %s canvas sets %gpt"
                                           % (sorted(szs), ctx.canvas.name, ctx.canvas.title_pt)))
    seen = set()
    for i in range(1, ctx.n + 1):
        lp = dr.layout_part_of(dr.slide_part(i))
        for part in (lp, dr.layout(lp).master_part if lp else None):
            if part and part not in seen:
                seen.add(part)
                _xml_checks(dr.xml(part), None, out, part)
    for mp in dr.master_parts:
        tp = dr.rel_target(mp, "/theme")
        if not tp:
            continue
        fm = dr.xml(tp).find(".//{*}fmtScheme")
        for el in (fm.iter() if fm is not None else []):
            if isinstance(el.tag, str) and local(el) in ("gradFill", "outerShdw", "innerShdw", "prstShdw", "glow",
                                                          "reflection", "softEdge", "scene3d", "sp3d"):
                out.append(Finding(GATE, FAIL, None, tp, "theme fmtScheme carries %s (it must be flat)" % local(el)))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
