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

from .theme import ROLES as ROLES_OK, TEXT_ROLES as _TR

TEXT_ROLES_OK = tuple(_TR) + ("paper",)
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


def _clr_key(clr):
    """A schemeClr's identity: its slot and its lumMod/lumOff values, never its serialised XML (whose inherited
    namespace declarations differ between a placed shape and a theme spec)."""
    if clr is None:
        return None
    return (clr.get("val"), tuple(sorted((c.tag.split("}")[-1], c.get("val")) for c in clr)))


def _role_of(clr, theme, roles) -> str | None:
    """The role a colour element is: an exact schemeClr match, else (a raw srgbClr) the nearest role by RGB."""
    if clr is None:
        return None
    if clr.tag.endswith("srgbClr") and clr.get("val"):
        h = clr.get("val").upper()
        rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]

        def dist(r):
            t = theme.hex(r)
            return sum((a - int(t[i:i + 2], 16)) ** 2 for a, i in zip(rgb, (0, 2, 4)))
        return min(roles, key=dist)
    k = _clr_key(clr)
    for r in roles:
        if _clr_key(theme.spec(r)) == k:
            return r
    return None


def _para_styles(shape, theme) -> list[tuple]:
    """(size, bold, role, align, space_before) of each existing paragraph's first run, so a refill keeps the
    device's type, colour, alignment and rhythm line by line."""
    out = []
    root = shape._element if hasattr(shape, "_element") else shape._tc
    for p in root.iter(qn("a:p")):
        r = p.find(qn("a:r"))
        rpr = r.find(qn("a:rPr")) if r is not None else None
        if rpr is None:
            continue
        size = int(rpr.get("sz")) / 100.0 if rpr.get("sz") else None
        bold = rpr.get("b") in ("1", "true")
        sf = rpr.find(qn("a:solidFill"))
        clr = sf[0] if sf is not None and len(sf) else None
        role = _role_of(clr, theme, TEXT_ROLES_OK) or "ink"
        ppr = p.find(qn("a:pPr"))
        align = {"ctr": "center", "r": "right", "just": "justify"}.get(ppr.get("algn") if ppr is not None else None,
                                                                      "left")
        sb = ppr.find(qn("a:spcBef") + "/" + qn("a:spcPts")) if ppr is not None else None
        out.append((size, bold, role, align, int(sb.get("val")) / 100.0 if sb is not None else None))
    return out or [(None, False, "ink", "left", None)]


def _walk(shapes):
    for sh in shapes:
        yield sh
        if sh.shape_type == 6:
            yield from _walk(sh.shapes)


def _fill_role(sh, theme) -> str | None:
    if hasattr(sh, "_tc"):                                      # a table cell
        sf = sh._tc.find(qn("a:tcPr") + "/" + qn("a:solidFill"))
    else:
        sf = sh._element.find(qn("p:spPr") + "/" + qn("a:solidFill"))
    clr = sf[0] if sf is not None and len(sf) else None
    return _role_of(clr, theme, ROLES_OK) if clr is not None else None


def _backdrop(slide, shape, theme) -> str:
    """The fill a slot's text sits on: its own solid fill, else the smallest filled shape under its centre."""
    own = _fill_role(shape, theme)
    if own:
        return own
    from .geom import abs_box
    g = abs_box(shape)                                 # absolute: group children report group-space positions
    x0, y0, x1, y1 = g.x, g.y, g.x + g.w, g.y + g.h
    area = max(1e-6, (x1 - x0) * (y1 - y0))
    order = {sh.shape_id: i for i, sh in enumerate(_walk(slide.shapes))}   # paint order by shape id (lxml proxy
    me = order.get(shape.shape_id, 10 ** 9)                                  # ids are not stable)
    best = None
    for sh in _walk(slide.shapes):
        i = order.get(sh.shape_id, 0)
        if sh is shape or sh.shape_type == 6 or i > me:
            continue                                   # only what is painted behind the slot can be its ground
        b = abs_box(sh)
        ix = max(0.0, min(x1, b.x + b.w) - max(x0, b.x))
        iy = max(0.0, min(y1, b.y + b.h) - max(y0, b.y))
        if ix * iy < 0.6 * area:                       # a marker beside the text is not its ground
            continue
        r = _fill_role(sh, theme)
        if r and (best is None or i > best[0]):         # the topmost such fill is what the text is read against
            best = (i, r)
    return best[1] if best else "paper"


def _glyph_role(shape, theme) -> str:
    """The colour a device drew its glyph in (its first line or fill role), so an icon on a brand fill stays visible."""
    for path in (qn("a:ln") + "/" + qn("a:solidFill") + "/" + qn("a:schemeClr"),
                 qn("a:solidFill") + "/" + qn("a:schemeClr")):
        el = shape._element.find(".//" + path)
        r = _role_of(el, theme, ROLES_OK) if el is not None else None
        if r:
            return r
    return "accent"


def _anchor(shape) -> str:
    bp = shape._element.find(".//" + qn("a:bodyPr"))
    return {"ctr": "middle", "b": "bottom"}.get(bp.get("anchor") if bp is not None else None, "top")


def insets_of(shape):
    """The text frame's own insets (bodyPr lIns/tIns/rIns/bIns, PowerPoint defaults when absent), in inches."""
    from . import measure as _m
    bp = shape._element.find(".//" + qn("a:bodyPr"))
    d = {"lIns": 91440, "tIns": 45720, "rIns": 91440, "bIns": 45720}
    v = {k: int(bp.get(k)) if bp is not None and bp.get(k) is not None else d[k] for k in d}
    return _m.Insets(v["lIns"] / 914400, v["tIns"] / 914400, v["rIns"] / 914400, v["bIns"] / 914400)


def place(prs, device_id: str, fill: dict, *, theme, keywords=(), archetype: str | None = None,
          variant: str | None = None):
    """A new slide carrying device `device_id` with its slots filled from `fill` {slot name: value}.

    archetype= names the archetype the slide serves; it is required when the device serves more than one (the tag
    decides which budget, variety, fill and architecture rules judge the slide), and optional otherwise. variant=
    overrides the variant slug, for a declared series. A filled title slot is set in the kit's title geometry
    (canvas.title_box, title_pt, one line, two-tone keywords), so titles never jump between placed and composed
    slides; it is narrowed only to clear a device mark beside it (a legend at the top right)."""
    e = _entry(device_id)
    if archetype is None and len(e.get("archetypes") or []) > 1:
        raise GeometryError("device %s archetype" % device_id, need="archetype= one of " + " / ".join(e["archetypes"]),
                            have="none",
                            hint="the device serves %d archetypes; the tag decides which budget, variety, fill and "
                                 "architecture rules judge the slide, so name the one this slide is"
                                 % len(e["archetypes"]))
    lib = Presentation(str(PPTX))
    src = lib.slides[e["index"] - 1]
    s = prs.slides.add_slide(prs.slide_layouts[0])
    copy_shapes(src, s, strip=DEVICE_STRIP)
    from . import tag as _tag
    _tag.tag(s, archetype or e["archetypes"][0], variant or e["variant"])
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
            role = spec.get("role") if spec.get("role") in ROLES_OK else _glyph_role(shape, theme)
            shape._element.getparent().remove(shape._element)
            if isinstance(value, str) and value.startswith("vendor:"):       # an official cloud service mark
                from .icons import vendor
                side = min(box.w, box.h)
                vendor(s, value[len("vendor:"):], Box(box.x + (box.w - side) / 2, box.y + (box.h - side) / 2, side,
                                                      side), name=name, alt=spec.get("alt"), theme=theme)
            else:
                glyph(s, value, box, role=role, shape_name=name, theme=theme)
            continue
        if getattr(shape, "has_table", False) and shape.has_table:   # a table slot: rows of cell strings
            tbl = shape.table
            rows = list(value)
            if len(rows) > len(tbl.rows) or any(len(r) > len(tbl.columns) for r in rows):
                raise GeometryError("device %s table slot %s" % (device_id, name),
                                    need="at most %d x %d cells" % (len(tbl.rows), len(tbl.columns)),
                                    have="%d rows" % len(rows))
            for ri, row in enumerate(rows):
                for ci, v in enumerate(row):
                    cell = tbl.cell(ri, ci)
                    st = _para_styles(cell, theme)[0]
                    para = txt.Para((txt.Run(str(v), st[2], bold=st[1], size=st[0]),), align=st[3])
                    txt.write(cell.text_frame, [para], theme, size=st[0], anchor="middle",
                              background=_fill_role(cell, theme) or "paper")
            continue
        if shape.shape_type == 6:                       # a group slot (a figure with its label): fill its text
            kids = sorted((k for k in _walk(shape.shapes) if k.has_text_frame and k.text_frame.text.strip()),
                          key=lambda k: (k.top, k.left))
            vals = [value] if isinstance(value, str) else list(value)
            if len(vals) != len(kids):
                raise GeometryError("device %s group slot %s" % (device_id, name), need="%d values" % len(kids),
                                    have=len(vals), hint="one value per text in the group, top to bottom")
            kid_spec = {k2: v2 for k2, v2 in spec.items() if k2 not in ("background", "role", "anchor")}
            for k, v in zip(kids, vals):                # each child reads its own ground, colour and anchor
                _fill_text(s, k, [v], kid_spec, theme, device_id, name)
            continue
        _fill_text(s, shape, value, spec, theme, device_id, name, keywords)
    return s


def _title_box(s, shape, canvas) -> Box:
    """The kit's title box for a device slide, narrowed to stop 0.20in short of any device shape beside it (a shape
    that overlaps the title band, starts right of its first inch and does not cover the whole box, like a page ground)."""
    from .geom import abs_box
    tb = canvas.title_box
    right = tb.r
    for sh in _walk(s.shapes):
        if sh.shape_id == shape.shape_id or sh.shape_type == 6:
            continue
        b = abs_box(sh)
        if b.w <= 0 or b.h <= 0:
            continue
        covers = b.x <= tb.x and b.y <= tb.y and b.x + b.w >= tb.r and b.y + b.h >= tb.b
        if covers or b.y >= tb.b + 0.05 or b.y + b.h <= tb.y or b.x < tb.x + 1.0:
            continue
        right = min(right, b.x - 0.20)
    return Box(tb.x, tb.y, right - tb.x, tb.h)


def _fill_title(s, shape, value, theme, device_id, name, keywords):
    """Set the title slot as text.title() sets a composed slide's title: the canvas title box, title_pt, the theme's
    major face, two-tone keywords, one line (canvas.title_max_lines). Raises Overflows when it wraps."""
    from . import measure
    from .canvas import EMU_PER_IN, canvas_of
    from .errors import OverBudget, Overflows
    from .read.textmetrics import words
    cv = canvas_of(s.part.package.presentation_part.presentation)
    text_, kws = value if isinstance(value, tuple) else (value, keywords)
    text_ = str(text_ or "")
    if words(text_) > txt.TITLE_MAX_WORDS:
        raise OverBudget("device %s slot %s" % (device_id, name), need=words(text_), have=txt.TITLE_MAX_WORDS,
                         hint="an action title is one claim; cut %d words" % (words(text_) - txt.TITLE_MAX_WORDS))
    box = _title_box(s, shape, cv)
    paras = [txt.Para(txt.title_runs(text_, kws))]
    major = txt._default_face(theme, "major")
    prepped = txt._prepare(paras, theme, cv.title_pt, major)
    fit = measure.fits([prepped[0][2]], (box.w, 1e9))
    if fit.n_lines > cv.title_max_lines or fit.need_in > box.h + 1e-9:
        raise Overflows("device %s slot %s" % (device_id, name), need=fit.n_lines, have=cv.title_max_lines,
                        unit="lines", hint="the %s title holds %d line at %gpt in %.2fin; cut words" % (
                            cv.name, cv.title_max_lines, cv.title_pt, box.w))
    shape.left, shape.top = int(round(box.x * EMU_PER_IN)), int(round(box.y * EMU_PER_IN))
    shape.width, shape.height = int(round(box.w * EMU_PER_IN)), int(round(box.h * EMU_PER_IN))
    txt.write(shape.text_frame, paras, theme, measure.ZERO, size=cv.title_pt, face=major, anchor="top",
              background=_backdrop(s, shape, theme))


def _fill_text(s, shape, value, spec, theme, device_id, name, keywords=()):
        if spec.get("kind") == "title":
            return _fill_title(s, shape, value, theme, device_id, name, keywords)
        styles = _para_styles(shape, theme)
        size = styles[0][0]
        bg = spec.get("background") if spec.get("background") in ROLES_OK else _backdrop(s, shape, theme)
        if isinstance(value, str) or (value and isinstance(value[0], str)):
            vals = [value] if isinstance(value, str) else list(value)
            paras = []
            for i, v in enumerate(vals):
                sz, bd, rl, al, sb = styles[min(i, len(styles) - 1)]
                want = spec.get("role") if spec.get("role") in TEXT_ROLES_OK else None
                paras.append(txt.Para((txt.Run(v, want or rl, bold=bd, size=sz or size),), align=al,
                                      space_before=0 if i == 0 else (sb if sb is not None else 3)))
        else:
            paras = list(value)
        from .geom import abs_box
        ab = abs_box(shape)
        # the fit is judged on the frame's own sides (a rotated axis label paints a thin box but reads along its length)
        box = Box(ab.x, ab.y, ab.frame_w, ab.frame_h) if ab.frame_w > 0 else Box(
            shape.left / EMU, shape.top / EMU, shape.width / EMU, shape.height / EMU)
        ins = insets_of(shape)
        try:
            txt.check_fit("device %s slot %s" % (device_id, name), paras, box, theme, ins, size=size)
        except Exception as x:                       # a hair over at the device's own size is rounding, not overflow
            if not (hasattr(x, "need") and hasattr(x, "have") and float(x.need) - float(x.have) <= 0.01):
                raise
        txt.write(shape.text_frame, paras, theme, ins, size=size, anchor=spec.get("anchor") or _anchor(shape),
                  background=bg)
