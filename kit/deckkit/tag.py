"""Archetype tags: which archetype and variant each slide is, stored where a PowerPoint save keeps it.

Two homes, both written by tag():
  * docProps/custom.xml, one custom property per slide, named "deckkit:<sldId>" with the value
    "archetype:variant". Keyed by the stable p:sldId (it survives reordering, insertion and a PowerPoint
    save). One short property per slide, never one JSON blob: Office truncates long property strings.
  * the slide's own cSld/@name, the backup that travels with the slide when it is copied to another
    deck (its sldId changes there, its name does not).

read() merges them: the custom property wins, the cSld name fills in, and a slide with neither is
untagged (archetype None). The gates read tags through read(); nothing else parses these properties.

    tag(slide, "pillars", "icon-row")       # in a build, before package.save
    read("deck.pptx")                       # [{index, sld_id, archetype, variant, tag, source}, ...]
"""
from __future__ import annotations

import re

from lxml import etree

from .errors import DeckkitError
from .read.ns import NS, local

PREFIX = "deckkit:"
FMTID = "{D5CDD505-2E9C-101B-9397-08002B2CF9AE}"      # the user-defined property set
CT_CUSTOM = "application/vnd.openxmlformats-officedocument.custom-properties+xml"
RT_CUSTOM = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties"
NS_CP = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
NS_VT = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
PART = "docProps/custom.xml"
ID_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,47}")
TAG_RE = re.compile(r"^([a-z0-9][a-z0-9-]{0,47}):([a-z0-9][a-z0-9-]{0,47})$")
_P = "{%s}" % NS["p"]


def _check(what, v):
    if not isinstance(v, str) or not ID_RE.fullmatch(v):
        raise DeckkitError("tag %s" % what, need="lower-case id (a-z, 0-9, hyphen, up to 48)", have=repr(v),
                           hint="archetype ids come from the frozen taxonomy, e.g. 'process-flow'")
    return v


def parse(value: str | None) -> tuple[str, str] | None:
    """'archetype:variant' to (archetype, variant), or None when it is not a tag."""
    m = TAG_RE.match(value or "")
    return (m.group(1), m.group(2)) if m else None


# ------------------------------------------------------------------ the custom properties part

def _props_xml(props: dict[str, str]) -> bytes:
    root = etree.Element("{%s}Properties" % NS_CP, nsmap={None: NS_CP, "vt": NS_VT})
    for pid, (name, value) in enumerate(sorted(props.items()), start=2):     # pid 0 and 1 are reserved
        p = etree.SubElement(root, "{%s}property" % NS_CP, fmtid=FMTID, pid=str(pid), name=name)
        etree.SubElement(p, "{%s}lpwstr" % NS_VT).text = value
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def parse_props(blob: bytes | None) -> dict[str, str]:
    """Every user-defined property whose value is a string, by name."""
    if not blob:
        return {}
    root = etree.fromstring(blob)
    out = {}
    for p in root:
        if local(p) != "property":
            continue
        v = next((c.text or "" for c in p if local(c) in ("lpwstr", "lpstr", "bstr")), None)
        if v is not None:
            out[p.get("name", "")] = v
    return out


def _custom_part(prs):
    pkg = prs.part.package
    for rel in pkg._rels.values():
        if rel.reltype == RT_CUSTOM and not rel.is_external:
            return rel.target_part
    return None


def _write_props(prs, props: dict[str, str]):
    from pptx.opc.package import Part
    from pptx.opc.packuri import PackURI
    part = _custom_part(prs)
    blob = _props_xml(props)
    if part is None:
        pkg = prs.part.package
        part = Part(PackURI("/" + PART), CT_CUSTOM, pkg, blob)
        pkg.relate_to(part, RT_CUSTOM)
    else:
        part._blob = blob
    return part


def _sld_ids(prs) -> dict[int, int]:
    """id(slide element) to its p:sldId value."""
    out = {}
    lst = prs.part._element.find(_P + "sldIdLst")
    for sid, slide in zip(lst if lst is not None else [], prs.slides):
        out[id(slide._element)] = int(sid.get("id"))
    return out


# ------------------------------------------------------------------ public

def tag(slide, archetype: str, variant: str) -> str:
    """Tag a python-pptx slide as archetype:variant, in both homes. Returns the tag string."""
    value = "%s:%s" % (_check("archetype", archetype), _check("variant", variant))
    csld = slide._element.find(_P + "cSld")
    csld.set("name", value)
    prs = slide.part.package.presentation_part.presentation
    sid = _sld_ids(prs).get(id(slide._element))
    if sid is None:
        raise DeckkitError("tag", need="a slide in this presentation's sldIdLst", have="none")
    part = _custom_part(prs)
    props = parse_props(part.blob if part is not None else None)
    props[PREFIX + str(sid)] = value
    _write_props(prs, props)
    return value


def read(deck) -> list[dict]:
    """Tags per slide in deck order. `deck` is a path or a deckkit.read DeckRead.

    Each row: index (1-based), sld_id, archetype, variant, tag, source ('custom', 'name' or None)."""
    from .read.opc import DeckRead
    own = isinstance(deck, (str, bytes)) or hasattr(deck, "__fspath__")
    d = DeckRead(str(deck)) if own else deck
    try:
        props = {}
        for _rid, (typ, target, mode) in d.rels("").items():
            if typ == RT_CUSTOM and mode != "External" and d.has(target):
                props = parse_props(d.blob(target))
        out = []
        for i, (part, sid) in enumerate(zip(d.slide_parts, d.slide_ids), start=1):
            value, source = props.get(PREFIX + str(sid)), "custom"
            if parse(value) is None:
                csld = d.xml(part).find(_P + "cSld")
                value, source = (csld.get("name") if csld is not None else None), "name"
            pv = parse(value)
            out.append({"index": i, "sld_id": sid, "archetype": pv[0] if pv else None,
                        "variant": pv[1] if pv else None, "tag": value if pv else None,
                        "source": source if pv else None})
        return out
    finally:
        if own:
            d.close()


__all__ = ["tag", "read", "parse", "parse_props", "PREFIX", "PART", "RT_CUSTOM", "CT_CUSTOM"]
