"""P16 colour: every visible fill, line and text colour is a theme role tuple or an identity-registry hex.

A role tuple is (scheme slot, lumMod, lumOff) exactly as the theme's role expressions write it, so a client
cut stays a theme swap. An srgbClr is allowed only when its hex is in the theme's identity registry (RAG
status, vendor marks), which keeps its hue on purpose. An srgbClr equal to any theme slot's hex (the kit theme's
slots and the deck's own theme slots, dk1 and lt1 included) is a hard-coded theme colour that a theme swap would
leave behind: it fails unless its shape is named state.* or identity.*, even when the identity registry lists
the same hex. Scoped to what renders: shape fills and outlines,
run colours, table-cell fills and borders, the slide background. Bullet colours (buClr) and end-of-paragraph
run properties (endParaRPr) never paint a glyph and are ignored. phClr, sysClr and prstClr on a slide fail.
"""
from __future__ import annotations

import sys

from _shared import FAIL, Finding, cli
from deckkit.read.ns import local

GATE, TITLE = "P16", "colour"
COLOURS = ("srgbClr", "schemeClr", "sysClr", "prstClr", "scrgbClr", "hslClr")
SKIP = ("buClr", "endParaRPr", "defRPr", "lstStyle", "extLst")
VISIBLE = ("spPr", "grpSpPr", "rPr", "tcPr", "bgPr", "ln", "lnL", "lnR", "lnT", "lnB", "highlight")


def _tuple(el):
    mods = tuple((local(m), int(m.get("val", "0"))) for m in el if isinstance(m.tag, str))
    return el.get("val"), mods


def _owner(el):
    cur = el
    while cur is not None:
        if isinstance(cur.tag, str) and local(cur) in ("sp", "cxnSp", "pic", "grpSp", "graphicFrame"):
            for c in cur.iter("{*}cNvPr"):
                return c.get("name") or "id %s" % c.get("id")
        cur = cur.getparent()
    return "background"


def run(deck, ctx):
    out = []
    th = ctx.theme
    roles = {(e.slot, tuple(e.mods)): name for name, e in th.roles.items()}
    identity = {v["hex"].upper(): k for k, v in th.identity.items()}
    slots = {}
    for mp in ctx.dr.master_parts:
        for slot, hx in (ctx.dr.master(mp).theme.get("colors") or {}).items():
            slots.setdefault(hx.upper(), "deck theme " + slot)
    for slot, hx in th.slots.items():
        slots[hx.upper()] = slot
    for i in range(1, ctx.n + 1):
        root = ctx.slide_root(i)
        for el in root.iter():
            if not isinstance(el.tag, str) or local(el) not in COLOURS:
                continue
            anc = [local(a) for a in el.iterancestors() if isinstance(a.tag, str)]
            if any(a in SKIP for a in anc) or not any(a in VISIBLE for a in anc):
                continue
            kind = local(el)
            if kind == "schemeClr":
                t = _tuple(el)
                if t not in roles:
                    out.append(Finding(GATE, FAIL, i, _owner(el), "schemeClr %s %s is not a theme role"
                                       % (t[0], " ".join("%s %d" % m for m in t[1]) or "(no mods)")))
            elif kind == "srgbClr":
                hx = (el.get("val") or "").upper()
                owner = _owner(el)
                if hx in slots and not owner.startswith(("state.", "identity.")):
                    out.append(Finding(GATE, FAIL, i, owner, "srgb %s is a hard-coded theme colour (%s); write the "
                                       "role, or name the shape state.* or identity.*" % (hx, slots[hx])))
                elif hx not in identity:
                    out.append(Finding(GATE, FAIL, i, _owner(el), "srgb %s is neither a role nor in the identity registry"
                                       % hx))
            else:
                out.append(Finding(GATE, FAIL, i, _owner(el), "%s %s on glass" % (kind, el.get("val") or "")))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
