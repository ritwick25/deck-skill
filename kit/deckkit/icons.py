"""Pictures: vendor service marks, SVG pictures with their PNG fallback, and generated monograms.

Lifted from the fabric _prim icon / rasterize_icons and the hospital attach_icon + fix_svg_ct scripts:
  * attach_icon wrote a p:pic whose a:blip carried only the svgBlip extension; here the blip always
    carries a PNG fallback too (r:embed) and the svgBlip in its extLst, related through the package API
    rather than by regex on the slide XML
  * fix_svg_ct restored the svg Default content type after a python-pptx save; package.save() does that
    on every kit save, and fix_svg_ct() below repairs a deck saved some other way
  * rasterising goes through rsvg-convert only (cairosvg is broken on this machine), via
    clone.rasterise_svg, so there is one rasteriser in the kit

Vendor marks keep their hue on purpose: they are identity, not theme. Their source is the diagrams
package's resource tree (aws, azure, gcp), addressed by key 'aws/compute/ec2'. A product with no mark
gets a monogram tile drawn in a theme role, one consistent family so it reads as intentional.
"""
from __future__ import annotations

import difflib
import io
import re
import zipfile
from functools import lru_cache
from pathlib import Path

from lxml import etree

from . import ooxml
from .canvas import EMU_PER_IN, Box
from .clone import FALLBACK_PX_MIN, add_svg_part, rasterise_svg
from .errors import GeometryError, UnsupportedPart
from .read.ns import NS

_A = "{%s}" % NS["a"]
_P = "{%s}" % NS["p"]
_R = "{%s}" % NS["r"]
SVG_EXT_URI = "{96DAC541-7B7A-43D3-8B79-37D633B846F1}"
ASVG_NS = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"
RT_IMAGE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"

DIAGRAMS_RESOURCES = Path("/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/site-packages/"
                          "diagrams/resources")
VENDORS = ("aws", "azure", "gcp")
SVG_FALLBACK_SCALE = 4.0     # an SVG's PNG fallback is 4x its displayed size at 96 dpi
RASTER_MIN_SCALE = 2.0       # a raster placed bigger than half its pixels at 96 dpi is refused (gate P22)


# ------------------------------------------------------------------ helpers

def _resources() -> Path:
    try:
        import diagrams  # noqa: F401
        p = Path(diagrams.__file__).resolve().parent / "resources"
        if p.is_dir():
            return p
    except ImportError:
        pass
    if DIAGRAMS_RESOURCES.is_dir():
        return DIAGRAMS_RESOURCES
    raise UnsupportedPart("vendor icon set", need="the diagrams package resources", have="missing",
                          hint="pip install diagrams on the pinned interpreter")


@lru_cache(maxsize=1)
def vendor_keys() -> tuple[str, ...]:
    """Every 'vendor/category/name' key available (aws, azure, gcp)."""
    root = _resources()
    out = []
    for v in VENDORS:
        for f in sorted((root / v).rglob("*.png")):
            out.append(f.relative_to(root).with_suffix("").as_posix())
    return tuple(out)


def vendor_path(key: str) -> Path:
    k = key.strip().strip("/")
    if k.split("/")[0] not in VENDORS:
        raise UnsupportedPart("vendor icon %r" % key, need="a key under " + ", ".join(VENDORS), have=k.split("/")[0])
    p = _resources() / (k + ".png")
    if not p.is_file():
        close = difflib.get_close_matches(k, vendor_keys(), n=4, cutoff=0.5)
        raise UnsupportedPart("vendor icon %r" % key, need="a file under diagrams/resources", have="missing",
                              hint=("closest: " + ", ".join(close)) if close else "list vendor_keys()")
    return p


def _fit(box: Box, px_w: int, px_h: int) -> Box:
    """The largest box of the image's aspect centred in `box`."""
    ar = px_h / px_w if px_w else 1.0
    if box.h / box.w >= ar:
        w, h = box.w, box.w * ar
    else:
        w, h = box.h / ar, box.h
    return Box(box.cx - w / 2, box.cy - h / 2, w, h)


def _png_size(blob: bytes) -> tuple[int, int]:
    from PIL import Image
    with Image.open(io.BytesIO(blob)) as im:
        return im.size


def _check_raster(what: str, px_w: int, box: Box):
    need_px = box.w * 96 * RASTER_MIN_SCALE
    if px_w + 1e-6 < need_px:
        raise GeometryError(what, need="%d px" % round(need_px), have="%d px" % px_w,
                            hint="displayed at %.2fin it needs %gx its 96-dpi size; draw it at %.2fin or smaller"
                                 % (box.w, RASTER_MIN_SCALE, px_w / 96 / RASTER_MIN_SCALE))


def _alt(text: str) -> str:
    t = " ".join(str(text).split())
    if not t or len(t) > 120:
        raise GeometryError("picture alt text", need="1..120 characters", have=len(t),
                            hint="say what the mark is, e.g. 'Amazon EC2'")
    return t


def _name(name, what):
    if not isinstance(name, str) or not name.strip():
        raise GeometryError("%s name" % what, need="a semantic shape name", have=repr(name))
    return name


def _set_nv(pic, name, alt):
    nv = pic._element.find(".//" + _P + "cNvPr")
    nv.set("name", name)
    nv.set("descr", alt)


# ------------------------------------------------------------------ public

def rasterise(svg: bytes, px: int, px_h: int | None = None) -> bytes:
    """PNG bytes of an SVG, px wide; the height follows the SVG's own aspect unless px_h is given."""
    if px_h is None:
        w, h = svg_size(svg)
        px_h = max(1, round(px * h / w)) if w else px
    return rasterise_svg(svg, int(px), int(px_h))


_LEN = re.compile(r"^\s*([0-9.]+)")


def svg_size(svg: bytes) -> tuple[float, float]:
    """The SVG's intrinsic (w, h) from its viewBox, else its width/height attributes."""
    try:
        root = etree.fromstring(svg)
    except etree.XMLSyntaxError as e:
        raise UnsupportedPart("svg", need="well-formed SVG", have=str(e)[:80]) from None
    vb = root.get("viewBox")
    if vb:
        v = [float(t) for t in re.split(r"[\s,]+", vb.strip()) if t]
        if len(v) == 4 and v[2] > 0 and v[3] > 0:
            return v[2], v[3]
    w, h = _LEN.match(root.get("width") or ""), _LEN.match(root.get("height") or "")
    if w and h and float(w.group(1)) > 0 and float(h.group(1)) > 0:
        return float(w.group(1)), float(h.group(1))
    raise UnsupportedPart("svg", need="a viewBox or width/height", have="neither")


@ooxml.transactional
def vendor(slide, key: str, box: Box, *, name: str | None = None, alt: str | None = None):
    """A vendor service mark (diagrams resources, 'aws/compute/ec2'), aspect kept, centred in box,
    in its own colours. Refused when the raster is under 2x its displayed size."""
    p = vendor_path(key)
    label = _alt(alt or key.rsplit("/", 1)[-1].replace("-", " ").title())     # refused before anything is added
    blob = p.read_bytes()
    pw, ph = _png_size(blob)
    b = _fit(box, pw, ph)
    _check_raster("vendor icon %s" % key, pw, b)
    x, y, w, h = b.emu
    pic = slide.shapes.add_picture(io.BytesIO(blob), x, y, w, h)
    _set_nv(pic, name or "icon.%s" % key.replace("/", "."), label)
    ooxml.finish(pic)
    return pic


@ooxml.transactional
def svg_picture(slide, svg: bytes, box: Box, png_fallback, *, name: str, alt: str):
    """An SVG picture: the svgBlip in the blip's extLst plus a PNG fallback in r:embed.

    png_fallback is PNG bytes, or "auto" to rasterise the SVG at 4x its displayed size with rsvg-convert.
    None is refused: an SVG never ships without its fallback (older readers draw the PNG)."""
    _name(name, "svg_picture")
    alt = _alt(alt)                          # refused before anything is added
    if png_fallback is None:
        raise UnsupportedPart("svg_picture %s" % name, need="a PNG fallback or 'auto'", have="None",
                              hint="pass png_fallback='auto' to rasterise it at 4x")
    sw, sh_ = svg_size(svg)
    b = _fit(box, sw, sh_)
    if png_fallback == "auto":
        px = max(FALLBACK_PX_MIN, round(b.w * 96 * SVG_FALLBACK_SCALE))
        png = rasterise(svg, px, max(FALLBACK_PX_MIN, round(b.h * 96 * SVG_FALLBACK_SCALE)))
    elif isinstance(png_fallback, (bytes, bytearray)) and bytes(png_fallback[:8]) == b"\x89PNG\r\n\x1a\n":
        png = bytes(png_fallback)
    else:
        raise UnsupportedPart("svg_picture %s fallback" % name, need="PNG bytes or 'auto'",
                              have=type(png_fallback).__name__)
    _check_raster("svg_picture %s fallback" % name, _png_size(png)[0], b)
    x, y, w, h = b.emu
    pic = slide.shapes.add_picture(io.BytesIO(png), x, y, w, h)
    part = slide.part
    spart = add_svg_part(part.package, bytes(svg))
    rid = part.relate_to(spart, RT_IMAGE)
    blip = pic._element.find(".//" + _A + "blip")
    ext_lst = blip.find(_A + "extLst")
    if ext_lst is None:
        ext_lst = etree.SubElement(blip, _A + "extLst")
    ext = etree.SubElement(ext_lst, _A + "ext", uri=SVG_EXT_URI)
    sb = etree.SubElement(ext, "{%s}svgBlip" % ASVG_NS, nsmap={"asvg": ASVG_NS})
    sb.set(_R + "embed", rid)
    _set_nv(pic, name, alt)
    ooxml.finish(pic)
    return pic


@ooxml.transactional
def monogram(slide, box: Box, letters: str, role: str = "ink-strong", *, name: str, pt=None, theme=None):
    """A monogram tile for a product with no offline mark: a rounded square in `role`, one to three
    letters centred in the role's text colour. One family: same radius, weight and proportions always.
    The letters are written by deckkit.text and measured before the tile exists."""
    from . import prims, text
    _name(name, "monogram")
    letters = str(letters).strip()
    if not (1 <= len(letters) <= 3) or not letters.replace("&", "").isalnum():
        raise GeometryError("monogram %s letters" % name, need="1-3 letters", have=letters)
    if role not in prims.ON_FILL:
        raise GeometryError("monogram %s role" % name, need=" / ".join(prims.ON_FILL), have=role)
    side = min(box.w, box.h)
    sq = Box(box.cx - side / 2, box.cy - side / 2, side, side)
    th = prims.theme_of(theme)
    if pt is None:
        share = {1: 0.50, 2: 0.40, 3: 0.30}[len(letters)]
        pt = int(side * 72 * share * 2) / 2.0     # never grown to the floor: check_pt raises
    what = "monogram %s" % name
    paras = [text.Para([text.Run(letters, role=prims.ON_FILL[role], bold=True, size=prims.check_pt(pt, what))],
                       align="center")]
    text.check_fit(what, paras, (side * 0.86, side), th)
    sh = prims._add(slide, "ROUNDED_RECTANGLE", sq, name)
    sh.adjustments[0] = 0.18
    prims.set_fill(sh, role, theme=th)
    prims.set_line(sh, None, theme=th)
    text.write(sh.text_frame, paras, th, anchor="middle")
    ooxml.finish(sh)
    return sh


def fix_svg_ct(path) -> bool:
    """Restore <Default Extension="svg"> in a saved package (python-pptx drops it). True when changed.
    package.save() already does this; this is for a deck saved some other way."""
    from .package import SVG_CT, write_members
    with zipfile.ZipFile(path) as z:
        members = {i.filename: z.read(i.filename) for i in z.infolist() if not i.is_dir()}
    ct = etree.fromstring(members["[Content_Types].xml"])
    q = "{%s}" % NS["ct"]
    if any(d.get("Extension", "").lower() == "svg" for d in ct.findall(q + "Default")):
        return False
    el = etree.Element(q + "Default", Extension="svg", ContentType=SVG_CT)
    first = ct.find(q + "Override")
    if first is not None:
        first.addprevious(el)
    else:
        ct.append(el)
    members["[Content_Types].xml"] = etree.tostring(ct, xml_declaration=True, encoding="UTF-8", standalone=True)
    write_members(members, path)
    return True


__all__ = ["vendor", "vendor_keys", "vendor_path", "svg_picture", "monogram", "rasterise", "svg_size", "fix_svg_ct",
           "SVG_FALLBACK_SCALE", "RASTER_MIN_SCALE"]
