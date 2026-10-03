"""The device library at runtime: native slides lifted from the references, sanitised and theme-mapped (ruling 3,
ruling 14). A device is placed whole onto a new slide and its named slots are filled; nothing of the reference
text survives (P18), and a slot left at its sample string fails P19.

    from deckkit import devices
    devices.catalogue()                         # [{id, name, archetypes, family, variant, slots, ...}]
    s = devices.place(prs, "DL07", {"slot.title": "Three decisions start the build in November",
                                    "slot.card.1.head": "Confirm the pilot region", ...}, theme=th)

Slot kinds: title (two-tone keywords allowed: pass (text, keywords)), text (a string, or a list of strings for
paragraphs, or kit Paras), glyph (a curated glyph name), delete (pass None to remove an optional slot's shapes).
A text slot is rewritten in its own box at its own size and role, fit-checked; a slot that does not fit raises
Overflows with the height it needs, so the caller cuts words rather than shrinking type.
"""
from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation

from . import text as txt
from .canvas import Box
from .clone import DEVICE_STRIP, copy_shapes
from .errors import GeometryError
from .geom import find
from .glyphs import glyph
from .read.ns import qn

ROOT = Path(__file__).resolve().parent.parent.parent / "devices"
PPTX = ROOT / "devices.pptx"
JSON = ROOT / "devices.json"
EMU = 914400


def catalogue() -> list[dict]:
    if not JSON.is_file():
        return []
    d = json.loads(JSON.read_text())
    return list(d.get("devices", {}).values()) if isinstance(d.get("devices"), dict) else d.get("devices", [])


def _entry(device_id: str) -> dict:
    for e in catalogue():
        if e["id"] == device_id:
            return e
    raise GeometryError("device %s" % device_id, need="an id in devices/devices.json",
                        have=", ".join(e["id"] for e in catalogue()) or "no library")


def _run_style(shape):
    """The size, bold and colour role-element of the shape's first run, so a refill keeps the device's type."""
    r = shape._element.find(".//" + qn("a:r"))
    rpr = r.find(qn("a:rPr")) if r is not None else None
    size = int(rpr.get("sz")) / 100.0 if rpr is not None and rpr.get("sz") else None
    bold = rpr is not None and rpr.get("b") in ("1", "true")
    return size, bold


def _role_of(shape, theme) -> str:
    """The text role the device wrote on this slot (its first run's schemeClr matched against the theme)."""
    r = shape._element.find(".//" + qn("a:r") + "/" + qn("a:rPr") + "/" + qn("a:solidFill") + "/" + qn("a:schemeClr"))
    if r is None:
        return "ink"
    from lxml import etree
    want = etree.tostring(r)
    for role in txt.TEXT_ROLES if hasattr(txt, "TEXT_ROLES") else ("ink-deep", "ink", "ink-strong", "ink-muted",
                                                                   "accent-ink", "on-accent", "navy"):
        if etree.tostring(theme.spec(role)) == want:
            return role
    return "ink"


def insets_of(shape):
    """The text frame's own insets (bodyPr lIns/tIns/rIns/bIns, PowerPoint defaults when absent), in inches."""
    from . import measure as _m
    bp = shape._element.find(".//" + qn("a:bodyPr"))
    d = {"lIns": 91440, "tIns": 45720, "rIns": 91440, "bIns": 45720}
    v = {k: int(bp.get(k)) if bp is not None and bp.get(k) is not None else d[k] for k in d}
    return _m.Insets(v["lIns"] / 914400, v["tIns"] / 914400, v["rIns"] / 914400, v["bIns"] / 914400)


def place(prs, device_id: str, fill: dict, *, theme, keywords=()):
    """A new slide carrying device `device_id` with its slots filled from `fill` {slot name: value}."""
    e = _entry(device_id)
    lib = Presentation(str(PPTX))
    src = lib.slides[e["index"] - 1]
    s = prs.slides.add_slide(prs.slide_layouts[0])
    copy_shapes(src, s, strip=DEVICE_STRIP)
    slots = {x["name"]: x for x in e.get("slots", [])}
    unknown = [k for k in fill if k not in slots]
    if unknown:
        raise GeometryError("device %s slots" % device_id, need=" / ".join(sorted(slots)), have=", ".join(unknown))
    for name, value in fill.items():
        spec = slots[name]
        shape = find(s, name)
        if value is None:
            shape._element.getparent().remove(shape._element)
            continue
        if spec.get("kind") == "glyph":
            box = Box(shape.left / EMU, shape.top / EMU, shape.width / EMU, shape.height / EMU)
            role = spec.get("role", "accent")
            shape._element.getparent().remove(shape._element)
            glyph(s, value, box, role=role, shape_name=name, theme=theme)
            continue
        size, bold = _run_style(shape)
        role = spec.get("role") or _role_of(shape, theme)
        bg = spec.get("background", "paper")
        if spec.get("kind") == "title":
            text_, kws = value if isinstance(value, tuple) else (value, keywords)
            paras = [txt.Para(txt.title_runs(text_, kws))]
        elif isinstance(value, str):
            paras = [txt.Para((txt.Run(value, role, bold=bold, size=size),))]
        elif value and isinstance(value[0], str):
            paras = [txt.Para((txt.Run(v, role, bold=bold, size=size),), space_before=0 if i == 0 else 3)
                     for i, v in enumerate(value)]
        else:
            paras = list(value)
        box = Box(shape.left / EMU, shape.top / EMU, shape.width / EMU, shape.height / EMU)
        ins = insets_of(shape)
        txt.check_fit("device %s slot %s" % (device_id, name), paras, box, theme, ins, size=size)
        txt.write(shape.text_frame, paras, theme, ins, size=size, anchor=spec.get("anchor", "top"), background=bg)
    return s
