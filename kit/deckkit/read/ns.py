"""OOXML namespaces and small element helpers shared by the read layer."""
from __future__ import annotations

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "a14": "http://schemas.microsoft.com/office/drawing/2010/main",
    "a16": "http://schemas.microsoft.com/office/drawing/2014/main",
    "adec": "http://schemas.microsoft.com/office/drawing/2017/decorative",
    "asvg": "http://schemas.microsoft.com/office/drawing/2016/SVG/main",
    "p14": "http://schemas.microsoft.com/office/powerpoint/2010/main",
    "p15": "http://schemas.microsoft.com/office/powerpoint/2012/main",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "dgm": "http://schemas.openxmlformats.org/drawingml/2006/diagram",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
    "ct": "http://schemas.openxmlformats.org/package/2006/content-types",
}

# Relationship types, by suffix
RT_SLIDE = "/slide"
RT_LAYOUT = "/slideLayout"
RT_MASTER = "/slideMaster"
RT_THEME = "/theme"
RT_IMAGE = "/image"
RT_HDPHOTO = "/hdphoto"

TABLE_URI = "http://schemas.openxmlformats.org/drawingml/2006/table"

_cache: dict[str, str] = {}


def qn(tag: str) -> str:
    """'a:off' to '{ns}off' (Clark notation)."""
    t = _cache.get(tag)
    if t is None:
        pfx, local_name = tag.split(":", 1)
        t = "{%s}%s" % (NS[pfx], local_name)
        _cache[tag] = t
    return t


def A(name: str) -> str:
    return qn("a:" + name)


def P(name: str) -> str:
    return qn("p:" + name)


def R(name: str) -> str:
    return qn("r:" + name)


def local(el) -> str:
    tag = el.tag
    if not isinstance(tag, str):  # comments, processing instructions
        return ""
    i = tag.rfind("}")
    return tag[i + 1:] if i >= 0 else tag


def first_child(el, names) -> object | None:
    """First child whose local name is in names (document order)."""
    if el is None:
        return None
    for c in el:
        if local(c) in names:
            return c
    return None


def path(el, *steps):
    """Follow child steps given as 'a:x' strings; None if any step is missing."""
    cur = el
    for s in steps:
        if cur is None:
            return None
        cur = cur.find(qn(s))
    return cur


def is_true(v) -> bool:
    return v in ("1", "true", "on")
