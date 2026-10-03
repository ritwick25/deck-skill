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
package's resource tree (aws, azure, gcp), addressed by key 'aws/compute/ec2', and a theme declares which
sources it accepts in its vendor registry (theme JSON "vendors"). vendor() names its picture
vendor.<key> and records the key in the alt text ('Ec2 (vendor mark aws/compute/ec2)'), so gate P22 knows
the mark is a registered vendor's own artwork and checks that its key resolves instead of its hue. A name and
an alt text can be typed onto any picture, so P22 also checks the picture's bytes: the blob's sha256 must be
the one kit/assets/vendor_hashes.json records for that key at that pixel size (the diagrams resource file,
embedded byte for byte; scripts/build_vendor_hashes.py rebuilds the table). vendor() checks the same table
before it draws, so a stale table refuses at build time rather than failing every mark at the gate.
A key is a relative path of plain segments: '..' anywhere, a leading '/' and a backslash are refused with or
without a theme bound.
A product with no mark gets a monogram tile drawn in a theme role, one consistent family so it reads as
intentional.
"""
from __future__ import annotations

import difflib
import hashlib
import io
import json
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
VENDORS = ("aws", "azure", "gcp", "onprem", "programming", "saas", "generic")   # ruling 18: product marks beyond the clouds
VENDOR_PREFIX = "vendor."
VENDOR_ALT = re.compile(r"\(vendor mark ([A-Za-z0-9_./-]+)\)\s*$")
SVG_FALLBACK_SCALE = 4.0     # an SVG's PNG fallback is 4x its displayed size at 96 dpi
RASTER_MIN_SCALE = 2.0       # a raster placed bigger than half its pixels at 96 dpi is refused (gate P22)
VENDOR_HASHES = Path(__file__).resolve().parent.parent / "assets" / "vendor_hashes.json"
MARKS_DIR = Path(__file__).resolve().parent.parent / "assets" / "marks"   # registry.json and the mark files
MARK_PREFIX = "mark."
MARK_ALT = re.compile(r"\(brand mark ([a-z0-9][a-z0-9-]*)\)\s*$")
MARK_KEY = re.compile(r"[a-z0-9][a-z0-9-]{0,60}")
MARK_FIELDS = ("name", "file", "sha256", "source", "fetched", "url")


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
    """Every 'vendor/category/name' key available (aws, azure, gcp, onprem, programming, saas, generic)."""
    root = _resources()
    out = []
    for v in VENDORS:
        for f in sorted((root / v).rglob("*.png")):
            out.append(f.relative_to(root).with_suffix("").as_posix())
    return tuple(out)


def vendor_key_refusal(key) -> str | None:
    """Why a string is not a vendor key, or None when it is one: a relative path of plain segments under a
    known vendor. '..' anywhere, a leading '/', a backslash, an empty segment or a NUL are refused."""
    k = str(key if key is not None else "").strip()
    if not k:
        return "an empty key"
    if "\\" in k:
        return "a backslash"
    if k.startswith("/"):
        return "a leading '/'"
    if ".." in k:
        return "'..'"
    if "\x00" in k:
        return "a NUL"
    if any(seg == "" or seg == "." for seg in k.split("/")):
        return "an empty or '.' segment"
    if k.split("/")[0] not in VENDORS:
        return "a vendor outside %s" % ", ".join(VENDORS)
    return None


def vendor_resolves(key: str, theme=None) -> bool:
    """True when key is a vendor key (vendor_key_refusal), names a mark file in the diagrams resources and,
    with a theme, its vendor (the key's first segment) is in the theme's vendor registry. Never raises."""
    if vendor_key_refusal(key) is not None:
        return False
    k = str(key).strip()
    v = k.split("/")[0]
    if theme is not None and v not in (getattr(theme, "vendors", None) or {}):
        return False
    try:
        return (_resources() / (k + ".png")).is_file()
    except UnsupportedPart:
        return False


def vendor_key_of(name: str, alt: str) -> str | None:
    """The key a vendor picture records: the alt text's '(vendor mark <key>)', when its name is
    vendor.<key> or vendor.<key>.<suffix>. None when either record is missing or they disagree."""
    m = VENDOR_ALT.search(alt or "")
    if not m or not (name or "").startswith(VENDOR_PREFIX):
        return None
    key = m.group(1)
    rest = name[len(VENDOR_PREFIX):]
    if rest == key or rest.startswith(key + "."):
        return key
    return None


def vendor_path(key: str) -> Path:
    """The mark file for a key. Refused (UnsupportedPart) for a key with '..', a leading '/' or a backslash,
    whether or not a theme is bound, and for a key that names no file."""
    why = vendor_key_refusal(key)
    if why is not None:
        raise UnsupportedPart("vendor icon %r" % key, need="a key 'vendor/category/name' under " + ", ".join(VENDORS),
                              have=why, hint="a key is a relative path of plain segments; list vendor_keys()")
    k = key.strip()
    root = _resources()
    p = root / (k + ".png")
    try:
        p.resolve().relative_to(root.resolve())
    except ValueError:
        raise UnsupportedPart("vendor icon %r" % key, need="a file under diagrams/resources",
                              have="a path outside it") from None
    if not p.is_file():
        close = difflib.get_close_matches(k, vendor_keys(), n=4, cutoff=0.5)
        raise UnsupportedPart("vendor icon %r" % key, need="a file under diagrams/resources", have="missing",
                              hint=("closest: " + ", ".join(close)) if close else "list vendor_keys()")
    return p


@lru_cache(maxsize=1)
def _vendor_table() -> dict:
    try:
        return json.loads(VENDOR_HASHES.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def vendor_hash(key: str, px_w: int, px_h: int) -> str | None:
    """The sha256 kit/assets/vendor_hashes.json records for the key's mark at px_w x px_h, or None."""
    return ((_vendor_table().get("keys") or {}).get(str(key)) or {}).get("%dx%d" % (px_w, px_h))


def vendor_sizes(key: str) -> tuple[str, ...]:
    """The pixel sizes ('256x256') kit/assets/vendor_hashes.json records for the key."""
    return tuple(sorted((_vendor_table().get("keys") or {}).get(str(key)) or {}))


def blob_sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


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
def vendor(slide, key: str, box: Box, *, name: str | None = None, alt: str | None = None, theme=None):
    """A vendor service mark (diagrams resources, 'aws/compute/ec2'), aspect kept, centred in box,
    in its own colours. Refused when the raster is under 2x its displayed size, and, when a theme is bound
    or passed, when the key's vendor is not in the theme's vendor registry.

    The picture is named vendor.<key> (name, when given, is a suffix: vendor.<key>.<name>, for two marks
    of one service on a slide) and its alt text is '<label> (vendor mark <key>)', so gate P22 can resolve
    the key; label is alt, else the key's last segment title-cased."""
    from . import prims
    p = vendor_path(key)
    k = key.strip()
    th = theme if theme is not None else (prims._ACTIVE[-1] if prims._ACTIVE else None)
    if th is not None and not vendor_resolves(k, th):
        reg = ", ".join(sorted(getattr(th, "vendors", None) or {})) or "empty"
        raise UnsupportedPart("vendor icon %r" % key, need="a vendor in the theme registry (%s)" % reg,
                              have=k.split("/")[0], hint="add the vendor to the theme's \"vendors\" registry")
    if name is not None:
        suffix = _name(name, "vendor")
        if not re.fullmatch(r"[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*", suffix):
            raise GeometryError("vendor %s name" % k, need="a dotted suffix (letters, digits, - and _)", have=name,
                                hint="the picture is named vendor.<key>.<suffix>")
    pic_name = VENDOR_PREFIX + k + ("." + name if name is not None else "")
    label = _alt(alt or k.rsplit("/", 1)[-1].replace("-", " ").title())
    label = _alt("%s (vendor mark %s)" % (label, k))                         # refused before anything is added
    blob = p.read_bytes()
    pw, ph = _png_size(blob)
    want = vendor_hash(k, pw, ph)
    if want != blob_sha256(blob):
        raise UnsupportedPart("vendor icon %r" % key, need="the sha256 kit/assets/vendor_hashes.json records at %dx%d"
                              % (pw, ph), have="none recorded" if want is None else "a different file",
                              hint="the diagrams resources changed; rebuild with scripts/build_vendor_hashes.py")
    b = _fit(box, pw, ph)
    _check_raster("vendor icon %s" % key, pw, b)
    x, y, w, h = b.emu
    pic = slide.shapes.add_picture(io.BytesIO(blob), x, y, w, h)
    _set_nv(pic, pic_name, label)
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
    text.check_contrast(what, paras, th, role)
    text.check_fit(what, paras, (side * 0.86, side), th)
    sh = prims._add(slide, "ROUNDED_RECTANGLE", sq, name)
    sh.adjustments[0] = 0.18
    prims.set_fill(sh, role, theme=th)
    prims.set_line(sh, None, theme=th)
    text.write(sh.text_frame, paras, th, anchor="middle", background=role)
    ooxml.finish(sh)
    return sh


# ------------------------------------------------------------------ brand marks (ruling 19)

def marks_dir(registry=None) -> Path:
    """The folder holding registry.json and the mark files: `registry` when given (a test fixture), else the kit's
    kit/assets/marks."""
    return Path(registry) if registry is not None else MARKS_DIR


def mark_registry(registry=None) -> dict:
    """{key: {name, file, sha256, source, fetched, url}} from <marks_dir>/registry.json; {} when it has none.
    A malformed entry raises UnsupportedPart: a mark is verified by bytes or not drawn at all."""
    p = marks_dir(registry) / "registry.json"
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        raise UnsupportedPart("mark registry", need="valid JSON", have=str(e)[:60]) from None
    out = {}
    for k, v in (data.get("marks", data) if isinstance(data, dict) else {}).items():
        if k.startswith("_"):
            continue
        if not MARK_KEY.fullmatch(str(k)) or not isinstance(v, dict) or any(not v.get(f) for f in MARK_FIELDS):
            raise UnsupportedPart("mark registry entry %r" % k, need="a key [a-z0-9-] and " + ", ".join(MARK_FIELDS),
                                  have=v, hint="every mark records where it came from, when, and its sha256")
        f = str(v["file"])
        if "/" in f or "\\" in f or f.startswith(".") or not f.lower().endswith((".svg", ".png")):
            raise UnsupportedPart("mark registry entry %r file" % k, need="a bare .svg or .png file name", have=f)
        out[str(k)] = dict(v)
    return out


def mark_key_of(name: str, alt: str) -> str | None:
    """The key a mark picture records: the alt text's '(brand mark <key>)', when its name is mark.<key> or
    mark.<key>.<suffix>. None when either record is missing or they disagree."""
    m = MARK_ALT.search(alt or "")
    if not m or not (name or "").startswith(MARK_PREFIX):
        return None
    key = m.group(1)
    rest = name[len(MARK_PREFIX):]
    return key if rest == key or rest.startswith(key + ".") else None


def mark_blob_refusal(key: str, svg_blob, png_blob, registry=None) -> str | None:
    """Why the blobs behind a mark picture are not the registered mark, or None when they are. An SVG mark is
    verified on its svgBlip part (the file's bytes, embedded unchanged) and must carry a PNG fallback; a PNG mark
    is verified on its r:embed blob."""
    entry = mark_registry(registry).get(key)
    if entry is None:
        return "mark %r is not in the mark registry (%s)" % (key, marks_dir(registry) / "registry.json")
    if entry["file"].lower().endswith(".svg"):
        if svg_blob is None:
            return "mark %r is registered as an SVG but the picture carries no svgBlip" % key
        if png_blob is None:
            return "mark %r has no PNG fallback" % key
        got = blob_sha256(svg_blob)
    else:
        if png_blob is None:
            return "mark %r has no picture blob (r:embed missing)" % key
        got = blob_sha256(png_blob)
    if got != entry["sha256"]:
        return ("mark %r blob sha256 %s is not the registered mark (%s); a picture renamed as a brand mark"
                % (key, got[:12], entry["sha256"][:12]))
    return None


@ooxml.transactional
def mark(slide, key: str, box: Box, *, name: str | None = None, alt: str | None = None, registry=None):
    """A brand mark from the kit's mark registry (kit/assets/marks/registry.json, ruling 19), aspect kept, centred in
    box, unaltered. The file's sha256 must equal its registry record or the mark is refused before anything is drawn.
    An SVG is embedded byte for byte with a PNG fallback rasterised by rsvg-convert (svg_picture); a PNG is embedded
    as it is and refused when it is under 2x its displayed size. The picture is named mark.<key> (name, when given, is
    a suffix) and its alt text is '<label> (brand mark <key>)', so gate P22 verifies it against the registry."""
    k = str(key or "").strip()
    if not MARK_KEY.fullmatch(k):
        raise UnsupportedPart("mark %r" % key, need="a registry key [a-z0-9-]", have=key)
    reg = mark_registry(registry)
    entry = reg.get(k)
    if entry is None:
        close = difflib.get_close_matches(k, list(reg), n=4, cutoff=0.5)
        raise UnsupportedPart("mark %r" % key, need="a key in %s" % (marks_dir(registry) / "registry.json"),
                              have="missing", hint=("closest: " + ", ".join(close)) if close else
                              "fetch it once (ruling 19) and record name, file, sha256, source, fetched and url")
    path = marks_dir(registry) / entry["file"]
    if not path.is_file():
        raise UnsupportedPart("mark %r file" % k, need=str(path), have="missing")
    blob = path.read_bytes()
    if blob_sha256(blob) != entry["sha256"]:
        raise UnsupportedPart("mark %r" % k, need="sha256 %s" % entry["sha256"][:12], have=blob_sha256(blob)[:12],
                              hint="the file changed since it was registered; re-verify it and update the record")
    if name is not None:
        suffix = _name(name, "mark")
        if not re.fullmatch(r"[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*", suffix):
            raise GeometryError("mark %s name" % k, need="a dotted suffix (letters, digits, - and _)", have=name)
    pic_name = MARK_PREFIX + k + ("." + name if name is not None else "")
    label = _alt(alt or entry["name"])
    label = _alt("%s (brand mark %s)" % (label, k))
    if entry["file"].lower().endswith(".svg"):
        return svg_picture(slide, blob, box, "auto", name=pic_name, alt=label)
    pw, ph = _png_size(blob)
    b = _fit(box, pw, ph)
    _check_raster("mark %s" % k, pw, b)
    x, y, w, h = b.emu
    pic = slide.shapes.add_picture(io.BytesIO(blob), x, y, w, h)
    _set_nv(pic, pic_name, label)
    ooxml.finish(pic)
    return pic


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


__all__ = ["mark", "mark_registry", "mark_key_of", "mark_blob_refusal", "marks_dir", "MARKS_DIR", "MARK_PREFIX",
           "vendor", "vendor_keys", "vendor_path", "vendor_resolves", "vendor_key_of", "vendor_key_refusal",
           "vendor_hash", "vendor_sizes", "blob_sha256", "VENDOR_PREFIX", "VENDOR_HASHES", "svg_picture", "monogram", "rasterise",
           "svg_size", "fix_svg_ct", "SVG_FALLBACK_SCALE", "RASTER_MIN_SCALE"]
