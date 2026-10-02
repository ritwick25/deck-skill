"""Writer-side OOXML helpers: the finish pass every creator runs, autofit removal, ids, once-only checks.

finish() exists because python-pptx 1.0.2 `add_shape`, `add_connector` and `build_freeform` inject
`<p:style>` with fillRef idx=3 and effectRef idx=2. In a stock theme those resolve to a gradient fill
and a blurred outer shadow, and LibreOffice draws that shadow whatever an empty effectLst says. So the
style element goes, and the shape gets exactly one empty `<a:effectLst/>` (what `shadow.inherit =
False` writes). The flat fmtScheme in every kit theme is the second defence, never the first.

Namespaces and qn() come from deckkit.read.ns: one map for the reader and the writer.
"""
from __future__ import annotations

import collections

from lxml import etree

from .errors import GeometryError
from .read.ns import NS, local, qn

_A = "{%s}" % NS["a"]
_P = "{%s}" % NS["p"]

# Containers whose children are each maxOccurs=1 in the schema. A repeat is the defect PowerPoint
# offers to repair while every other reader passes (package_gate, 2026-08). Fill and geometry are
# choice groups, so two of ANY child here is equally wrong.
ONCE_ONLY = {
    _A + "spPr": "shape properties", _P + "spPr": "shape properties", _P + "grpSpPr": "group properties",
    _A + "rPr": "run properties", _A + "defRPr": "default run properties",
    _A + "endParaRPr": "end-paragraph run properties",
    _A + "bodyPr": "body properties", _A + "ln": "line properties",
    _A + "pPr": "paragraph properties", _A + "blipFill": "picture fill", _P + "blipFill": "picture fill",
    _A + "effectLst": "effect list", _A + "blip": "image reference",
}
# children that legitimately repeat inside one of the containers above
REPEATABLE = {_A + "tab", _A + "gs", _A + "ext", _A + "alphaModFix", _A + "lumMod", _A + "lumOff"}

# spPr child order (CT_ShapeProperties): xfrm, geometry, fill, ln, effect, scene3d, sp3d, extLst
_BEFORE_EFFECT = {"xfrm", "custGeom", "prstGeom", "noFill", "solidFill", "gradFill", "blipFill", "pattFill",
                  "grpFill", "ln"}
# bodyPr child order: prstTxWarp, autofit choice, scene3d, sp3d, flatTx, extLst
_AUTOFIT = ("noAutofit", "normAutofit", "spAutoFit")


def _el(obj):
    """A python-pptx shape, text frame or slide, or an lxml element, to its element."""
    for attr in ("_element", "_txBody"):
        e = getattr(obj, attr, None)
        if e is not None:
            return e
    return obj


def _sppr(el):
    for tag in (_P + "spPr", _P + "grpSpPr"):
        sp = el.find(tag)
        if sp is not None:
            return sp
    return None


def finish(shape, shadow: str = "none"):
    """Strip `<p:style>`, write exactly one empty effectLst. Runs in every creator, never opt-in.

    shadow must be "none": the kit has no soft shadow to offer (CLAUDE.md section 4). Returns shape.
    A graphicFrame (table, chart) has no spPr and is returned untouched apart from the style strip.
    """
    if shadow != "none":
        raise GeometryError("finish(shadow=%r)" % shadow, need="none", have=shadow,
                            hint="the kit draws no shadows; lift a shadow element off an accepted card instead")
    el = _el(shape)
    for st in el.findall(_P + "style"):
        el.remove(st)
    sp = _sppr(el)
    if sp is None:
        return shape
    for old in [c for c in sp if local(c) in ("effectLst", "effectDag")]:
        sp.remove(old)
    pos = 0
    for i, c in enumerate(sp):
        if local(c) in _BEFORE_EFFECT:
            pos = i + 1
    sp.insert(pos, etree.Element(_A + "effectLst"))
    return shape


def no_autofit(text_frame):
    """bodyPr gets `<a:noAutofit/>` and wrap="square"; spAutoFit and normAutofit (fontScale) go.

    python-pptx `add_textbox` writes wrap="none" plus spAutoFit, which lets LibreOffice grow a box past
    its declared height; normAutofit hides sub-floor text behind a fontScale. Returns the bodyPr.
    """
    el = _el(text_frame)
    body = el if local(el) == "bodyPr" else el.find(_A + "bodyPr")
    if body is None:
        raise GeometryError("no_autofit", need="a txBody with bodyPr", have=local(el))
    for c in [c for c in body if local(c) in _AUTOFIT]:
        body.remove(c)
    body.set("wrap", "square")
    pos = 1 if (len(body) and local(body[0]) == "prstTxWarp") else 0
    body.insert(pos, etree.Element(_A + "noAutofit"))
    return body


def _owner_id(el):
    """The cNvPr id of the nearest shape-like ancestor, for a readable report."""
    cur = el
    while cur is not None:
        if isinstance(cur.tag, str) and local(cur) in ("sp", "pic", "cxnSp", "grpSp", "graphicFrame"):
            nv = cur.find(".//" + _P + "cNvPr")
            return nv.get("id") if nv is not None else "?"
        cur = cur.getparent()
    return "-"


def once_only_violations(element) -> list[tuple[str, str, int, str]]:
    """[(container, child local name, count, owning shape id), ...] for every once-only repeat."""
    out = []
    for el in _el(element).iter():
        if el.tag not in ONCE_ONLY:
            continue
        seen = collections.Counter(c.tag for c in el if isinstance(c.tag, str))
        for tag, k in seen.items():
            if k > 1 and tag not in REPEATABLE:
                out.append((ONCE_ONLY[el.tag], etree.QName(tag).localname, k, _owner_id(el)))
    return out


def next_id(slide) -> int:
    """max(cNvPr id) + 1 at the moment of insertion. Never compute once before a loop: nine duplicate
    ids shipped that way (pptxlib, 2026-08-24)."""
    el = _el(slide)
    tree = getattr(getattr(slide, "shapes", None), "_spTree", None)
    root = tree if tree is not None else el
    ids = [int(e.get("id")) for e in root.iter(_P + "cNvPr") if (e.get("id") or "").isdigit()]
    return (max(ids) if ids else 1) + 1


__all__ = ["NS", "qn", "ONCE_ONLY", "REPEATABLE", "finish", "no_autofit", "once_only_violations", "next_id"]
