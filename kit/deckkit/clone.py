"""Copy shapes between slides and between packages, with every id and relationship re-pointed.

python-pptx has no cross-package clone. A deep copy carries the source's cNvPr ids, its r:embed /
r:link / r:id values (relationship ids are local to their own part) and its connector glue ids, and
PowerPoint calls the result corrupt while LibreOffice renders it anyway. copy_shapes fixes all three:

  ids     every copied cNvPr gets a fresh id above the destination slide's largest (ooxml.next_id)
  rels    every attribute in the r: namespace, at any depth, is resolved against the source part and
          re-created on the destination part; images are copied as parts (deduplicated by sha1), SVG
          parts are recreated with the svg content type and always carry a PNG fallback blip
  glue    stCxn/endCxn are remapped to the copy of their target, or stripped when the target was not
          copied (or always, under DEVICE_STRIP)

  charts  a chart frame (c:chart) is carried with its own copy of the chart part, its embedded workbook (Edit Data
          keeps working) and any chart style or colour parts, renumbered in the destination, even within one
          package (two slides never share one chart part). Its alt text is kept: the kit's frames end it with
          "(chart kind <kind>)", which gate P27 reads. A chart whose data is a linked external workbook, or that
          carries user shapes, is refused.

The strip policy removes what must never travel into client work: hyperlinks, custom data and tags,
HD Photo (artistic effect) layers, alt text (chart frames excepted), creation ids, and mc:AlternateContent (the
Fallback is kept). Extended charts (cx:chart, which LibreOffice cannot render), OLE objects, SmartArt, ink and
media raise UnsupportedPart before anything is written. Selection is by shape id or name, never by index.
"""
from __future__ import annotations

import copy as _copy
import hashlib
import io
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Callable, Iterable

from lxml import etree
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.opc.package import Part
from pptx.oxml.xmlchemy import OxmlElement
from pptx.parts.image import ImagePart
from pptx.shapes.shapetree import SlideShapeFactory

from .errors import GeometryError, UnsupportedPart
from .ooxml import finish, next_id
from .read.ns import NS, A, P, local, qn

R_NS = "{%s}" % NS["r"]
SVG_CT = "image/svg+xml"
SVG_EXT_URI = "{96DAC541-7B7A-43D3-8B79-37D633B846F1}"
HDPHOTO_EXT_URI = "{BEBA8EAE-BF5A-486C-A8C5-ECC9F3942E4B}"     # a14:imgProps (artistic effect layers)
RT_HDPHOTO = "http://schemas.microsoft.com/office/2007/relationships/hdphoto"
RASTER_CT = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif",
             "bmp": "image/bmp", "tif": "image/tiff", "tiff": "image/tiff", "emf": "image/x-emf",
             "wmf": "image/x-wmf"}
SHAPE_TAGS = ("sp", "pic", "cxnSp", "grpSp", "graphicFrame", "contentPart")
# graphicData URIs a frame may carry across: tables, and native charts with their parts
CHART_URI = "http://schemas.openxmlformats.org/drawingml/2006/chart"
FRAME_OK = ("http://schemas.openxmlformats.org/drawingml/2006/table", CHART_URI)
RT_CHART_STYLE = "http://schemas.microsoft.com/office/2011/relationships/chartStyle"
RT_CHART_COLORS = "http://schemas.microsoft.com/office/2011/relationships/chartColorStyle"
CHART_COPY_RELS = (RT.PACKAGE, RT.IMAGE, RT.OLE_OBJECT, RT_CHART_STYLE, RT_CHART_COLORS)
FRAME_KIND = {"chart": "chart", "chartex": "chart", "ole": "OLE object", "diagram": "SmartArt",
              "ink": "ink", "model3d": "3D model"}
MEDIA_TAGS = ("videoFile", "audioFile", "quickTimeFile", "wavAudioFile", "audioCd", "media")
FALLBACK_PX_MIN = 64          # smallest PNG fallback edge, px
FALLBACK_SCALE = 2.0          # fallback raster is 2x the displayed size at 96 dpi (gate P22)


# ------------------------------------------------------------------ policy and result

@dataclass(frozen=True)
class StripPolicy:
    """What copy_shapes removes from the copies. Every field defaults to removal.

    glue          "remap" keeps stCxn/endCxn pointing at the copy of their target and strips glue whose
                  target was not copied; "strip" removes all glue (LibreOffice re-routes glued bent
                  connectors on import, so devices carry none)
    placeholders  "demote" turns a placeholder with text into a plain shape carrying its inherited box
                  and drops an empty one; "raise" refuses
    """
    hyperlinks: bool = True        # a:hlinkClick, a:hlinkHover, a:hlinkMouseOver
    cust_data: bool = True         # p:custDataLst (and its tags parts)
    hdphoto: bool = True           # a14:imgProps layers and their .wdp parts
    alt_text: bool = True          # cNvPr descr and title
    alt_content: bool = True       # mc:AlternateContent, replaced by its Fallback
    creation_ids: bool = True      # a16:creationId and friends on cNvPr (identify the source deck)
    glue: str = "remap"
    placeholders: str = "demote"

    def __post_init__(self):
        if self.glue not in ("remap", "strip"):
            raise GeometryError("StripPolicy.glue", need="'remap' or 'strip'", have=self.glue)
        if self.placeholders not in ("demote", "raise"):
            raise GeometryError("StripPolicy.placeholders", need="'demote' or 'raise'", have=self.placeholders)


DEVICE_STRIP = StripPolicy(glue="strip")
CLEAN_STRIP = StripPolicy(glue="remap")


@dataclass
class IdMap:
    """Source to destination ids for one copy. Keyed by shape id and name, never by position."""
    ids: dict[int, int] = field(default_factory=dict)          # source id to destination id
    src_names: dict[str, list[int]] = field(default_factory=dict)
    elements: dict[int, object] = field(default_factory=dict)  # destination id to element
    top: list[int] = field(default_factory=list)               # destination ids of the top-level copies
    glue_remapped: int = 0
    glue_stripped: int = 0
    parts_added: list[str] = field(default_factory=list)       # destination partnames created
    duplicate_src_ids: set = field(default_factory=set)

    def __getitem__(self, src) -> int:
        """Destination id for a source id (int) or a unique source name (str)."""
        if isinstance(src, str):
            ids = self.src_names.get(src, [])
            if not ids:
                raise KeyError(f"no copied shape named {src!r}")
            if len(ids) > 1:
                raise LookupError(f"{len(ids)} copied shapes are named {src!r} (source ids {ids}); use the id")
            src = ids[0]
        if src in self.duplicate_src_ids:
            raise LookupError(f"source id {src} occurs more than once in the copied shapes")
        return self.ids[src]

    def __contains__(self, src) -> bool:
        try:
            self[src]
        except LookupError:
            return False
        return True

    def element(self, src):
        return self.elements[self[src]]

    def __len__(self) -> int:
        return len(self.ids)


# ------------------------------------------------------------------ helpers

def _el(obj):
    return getattr(obj, "_element", obj)


def _cnvpr(el):
    for c in el:
        if isinstance(c.tag, str) and local(c).startswith("nv"):
            return c.find(P("cNvPr"))
    return None


def _sid(el) -> int:
    c = _cnvpr(el)
    return int(c.get("id", "0")) if c is not None and (c.get("id") or "").isdigit() else 0


def _sname(el) -> str:
    c = _cnvpr(el)
    return c.get("name", "") if c is not None else ""


def _package_of(obj):
    """A Presentation, slide, part or package to its OPC package."""
    for attr in ("part", "_part"):
        p = getattr(obj, attr, None)
        if p is not None and hasattr(p, "package"):
            return p.package
    if hasattr(obj, "package") and hasattr(obj, "partname"):
        return obj.package
    if hasattr(obj, "iter_parts"):
        return obj
    raise GeometryError("package", need="a Presentation, slide, part or package", have=type(obj).__name__)


def _top_level(tree, strip: StripPolicy) -> list:
    """Top-level shape elements; mc:AlternateContent resolved to its Fallback under the policy."""
    out = []
    for el in tree:
        t = local(el)
        if t == "AlternateContent":
            if not strip.alt_content:
                out.append(el)
                continue
            fb = el.find(qn("mc:Fallback"))
            if fb is not None:
                out += [c for c in fb if local(c) in SHAPE_TAGS]
        elif t in SHAPE_TAGS:
            out.append(el)
    return out


def _flatten_alt_content(root) -> None:
    """Replace every nested mc:AlternateContent with the children of its Fallback (or nothing)."""
    for ac in list(root.iter(qn("mc:AlternateContent"))):
        parent = ac.getparent()
        if parent is None:
            continue
        fb = ac.find(qn("mc:Fallback"))
        i = parent.index(ac)
        for c in (list(fb) if fb is not None else []):
            parent.insert(i, c)
            i += 1
        parent.remove(ac)


def _remove_all(root, tag) -> int:
    n = 0
    for e in list(root.iter(tag)):
        e.getparent().remove(e)
        n += 1
    return n


def _drop_ext(root, uri_pred) -> None:
    for ext in list(root.iter(A("ext"))):
        if uri_pred(ext.get("uri", ""), ext):
            lst = ext.getparent()
            lst.remove(ext)
            if len(lst) == 0 and lst.getparent() is not None:
                lst.getparent().remove(lst)


def _apply_strip(el, strip: StripPolicy) -> None:
    if strip.alt_content:
        _flatten_alt_content(el)
    if strip.hyperlinks:
        for tag in ("hlinkClick", "hlinkHover", "hlinkMouseOver"):
            _remove_all(el, A(tag))
    if strip.cust_data:
        _remove_all(el, P("custDataLst"))
    if strip.hdphoto:
        _drop_ext(el, lambda uri, e: uri == HDPHOTO_EXT_URI or e.find(qn("a14:imgProps")) is not None)
    if strip.alt_text:
        for c in el.iter(P("cNvPr")):
            if _is_chart_frame(c.getparent().getparent()):
                continue                                   # a chart's alt text states its kind (gate P27)
            for attr in ("descr", "title"):
                if attr in c.attrib:
                    del c.attrib[attr]
    if strip.creation_ids:
        for c in el.iter(P("cNvPr")):
            lst = c.find(A("extLst"))
            if lst is not None:
                c.remove(lst)


def _is_chart_frame(el) -> bool:
    if el is None or local(el) != "graphicFrame":
        return False
    gd = el.find(A("graphic") + "/" + A("graphicData"))
    return gd is not None and gd.get("uri") == CHART_URI


def _unsupported(el, part) -> None:
    """Refuse charts, OLE, SmartArt, ink, 3D models and media before anything is written."""
    for gf in el.iter(P("graphicFrame")):
        gd = gf.find(A("graphic") + "/" + A("graphicData"))
        uri = gd.get("uri", "") if gd is not None else ""
        if uri in FRAME_OK:
            continue
        kind = FRAME_KIND.get(uri.rstrip("/").rsplit("/", 1)[-1], uri or "unknown graphic")
        raise UnsupportedPart(f"{_sname(gf) or 'graphicFrame'} (id {_sid(gf)}) is a {kind}",
                              need="a table, native chart, shape or picture", have=kind,
                              hint="rebuild it from build.py with the kit (deckkit.charts for a chart); an extended "
                                   "chart, OLE object or SmartArt does not travel")
    for cp in el.iter(P("contentPart")):
        raise UnsupportedPart(f"content part (id {_sid(cp)})", need="a shape", have="ink content part",
                              hint="redraw the ink as a freeform")
    for m in el.iter(*[A(t) for t in MEDIA_TAGS], qn("p14:media")):
        owner = m
        while owner is not None and local(owner) not in SHAPE_TAGS:
            owner = owner.getparent()
        raise UnsupportedPart(f"{_sname(owner) if owner is not None else 'shape'} carries {local(m)}",
                              need="a still picture", have="media", hint="use a poster frame image")


# ------------------------------------------------------------------ parts

def _sha1(blob: bytes) -> str:
    return hashlib.sha1(blob).hexdigest()


def add_svg_part(pkg, blob: bytes) -> Part:
    """An image/svg+xml part in pkg holding blob, reused when an identical SVG is already there.

    python-pptx has no SVG part class; the part is a plain Part with the svg content type, which the
    serialiser writes as an Override. The caller relates it (relate_to(part, RT.IMAGE))."""
    pkg = _package_of(pkg)
    head = blob[:2048].lstrip()
    if b"<svg" not in blob[:4096] and not head.startswith(b"<?xml"):
        raise UnsupportedPart("svg part", need="SVG markup", have=f"{len(blob)} bytes without <svg",
                              hint="pass the SVG file's bytes")
    sha = _sha1(blob)
    for p in pkg.iter_parts():
        if p.content_type == SVG_CT and _sha1(p.blob) == sha:
            return p
    return Part(pkg.next_image_partname("svg"), SVG_CT, pkg, blob)


def _image_part(pkg, blob: bytes, ext: str) -> Part:
    ext = ext.lower()
    if ext == "svg":
        return add_svg_part(pkg, blob)
    ct = RASTER_CT.get(ext)
    if ct is None:
        raise UnsupportedPart(f"image part .{ext}", need="png, jpeg, gif, bmp, tiff, emf, wmf or svg", have=ext)
    sha = _sha1(blob)
    for p in pkg.iter_parts():
        if isinstance(p, ImagePart) and p.sha1 == sha:
            return p
    return ImagePart(pkg.next_image_partname(ext), ct, pkg, blob)


def rasterise_svg(blob: bytes, px_w: int, px_h: int) -> bytes:
    """PNG bytes of an SVG at the given pixel size, via rsvg-convert (cairosvg is broken here)."""
    exe = shutil.which("rsvg-convert") or (shutil.which("rsvg-convert", path="/opt/homebrew/bin:/usr/local/bin"))
    if exe is None:
        raise UnsupportedPart("svg fallback raster", need="rsvg-convert on PATH", have="missing",
                              hint="brew install librsvg; an SVG never ships without its PNG fallback")
    px_w, px_h = max(FALLBACK_PX_MIN, int(px_w)), max(FALLBACK_PX_MIN, int(px_h))
    try:
        out = subprocess.run([exe, "-w", str(px_w), "-h", str(px_h), "-f", "png"], input=blob,
                             capture_output=True, check=True, timeout=60).stdout
    except subprocess.CalledProcessError as e:
        raise UnsupportedPart("svg fallback raster", need="a renderable SVG",
                              have=e.stderr.decode("utf-8", "replace").strip()[:120] or "rsvg-convert failed")
    if not out.startswith(b"\x89PNG"):
        raise UnsupportedPart("svg fallback raster", need="PNG output", have=f"{len(out)} bytes")
    return out


def _fallback_px(pic_el) -> tuple[int, int]:
    """Displayed size in px at 96 dpi, times FALLBACK_SCALE."""
    from .read.xform import EMU_IN
    x = pic_el.find(P("spPr") + "/" + A("xfrm"))
    ext = x.find(A("ext")) if x is not None else None
    w = int(ext.get("cx", "0")) if ext is not None else 0
    h = int(ext.get("cy", "0")) if ext is not None else 0
    return (round(w / EMU_IN * 96 * FALLBACK_SCALE), round(h / EMU_IN * 96 * FALLBACK_SCALE))


class _Relinker:
    """Re-creates the source relationships a set of copies uses, on the destination part."""

    def __init__(self, src_part, dst_part, idmap: IdMap):
        self.src, self.dst, self.idmap = src_part, dst_part, idmap
        self.same_pkg = src_part.package is dst_part.package
        self.cache: dict[str, str] = {}
        self.pkg_parts_before = {str(p.partname) for p in dst_part.package.iter_parts()}

    def check(self, rid: str, where: str) -> None:
        """Refuse up front whatever new() would refuse, so a failed copy writes nothing."""
        if not rid:
            return
        try:
            rel = self.src.rels[rid]
        except KeyError:
            raise UnsupportedPart(f"{where}: r:id {rid}", need="a relationship on the source part",
                                  have="dangling", hint="the source slide is broken; repair it first")
        if rel.is_external:
            return
        rt = rel.reltype
        if rt == RT.CHART:
            self._check_chart(rel.target_part, where)
            return
        if rt == RT.IMAGE:
            ext = rel.target_part.partname.ext.lower()
            if ext != "svg" and ext not in RASTER_CT:
                raise UnsupportedPart(f"{where}: image .{ext}", need="png, jpeg or svg", have=ext)
            return
        if rt == RT_HDPHOTO or self.same_pkg:
            return
        raise UnsupportedPart(f"{where}: relationship {rt.rsplit('/', 1)[-1]}", need="image, hdphoto or external link",
                              have=rt.rsplit("/", 1)[-1], hint="cross-package copies carry pictures and links only")

    @staticmethod
    def _check_chart(cp, where: str) -> None:
        for r in cp.rels.values():
            if r.is_external:
                raise UnsupportedPart(f"{where}: chart data", need="an embedded workbook", have="a linked external file",
                                      hint="embed the data (Edit Data, then save) or rebuild the chart with the kit")
            if r.reltype not in CHART_COPY_RELS:
                raise UnsupportedPart(f"{where}: chart relationship {r.reltype.rsplit('/', 1)[-1]}",
                                      need="workbook, image, style or colour parts", have=r.reltype.rsplit("/", 1)[-1],
                                      hint="chart user shapes do not travel; draw annotations with the kit")

    def _copy_chart(self, cp) -> str:
        """A fresh chart part in the destination package with its own workbook and style parts, related to the
        destination slide part; returns the slide-side relationship id."""
        from pptx.parts.chart import ChartPart
        pkg = self.dst.package
        new = ChartPart.load(pkg.next_partname(ChartPart.partname_template), cp.content_type, pkg, cp.blob)
        out = self.dst.relate_to(new, RT.CHART)              # reachable now, so the next partname counts it
        remap = {}
        for rid, r in sorted(cp.rels.items()):
            tp = r.target_part
            if r.reltype == RT.IMAGE:
                target = _image_part(pkg, tp.blob, tp.partname.ext)
            else:
                tmpl = re.sub(r"\d*(\.[A-Za-z0-9]+)$", r"%d\1", str(tp.partname))
                target = type(tp).load(pkg.next_partname(tmpl), tp.content_type, pkg, tp.blob)
            remap[rid] = new.relate_to(target, r.reltype)
        for e, k, v in list(_r_attrs(new._element)):
            if v in remap:
                e.set(k, remap[v])
        return out

    def new(self, rid: str) -> str:
        if rid in self.cache:
            return self.cache[rid]
        rel = self.src.rels[rid]
        if not rel.is_external and rel.reltype == RT.CHART:
            out = self._copy_chart(rel.target_part)
            self.cache[rid] = out
            return out
        if rel.is_external:
            out = self.dst.relate_to(rel.target_ref, rel.reltype, is_external=True)
        elif self.same_pkg and rel.reltype not in (RT.IMAGE,):
            out = self.dst.relate_to(rel.target_part, rel.reltype)
        elif rel.reltype == RT.IMAGE:
            tp = rel.target_part
            target = tp if self.same_pkg else _image_part(self.dst.package, tp.blob, tp.partname.ext)
            out = self.dst.relate_to(target, RT.IMAGE)
        elif rel.reltype == RT_HDPHOTO:
            tp = rel.target_part
            pkg = self.dst.package
            sha = _sha1(tp.blob)
            target = next((p for p in pkg.iter_parts() if p.content_type == tp.content_type and _sha1(p.blob) == sha),
                          None)
            if target is None:
                target = Part(pkg.next_partname("/ppt/media/hdphoto%d.wdp"), tp.content_type, pkg, tp.blob)
            out = self.dst.relate_to(target, RT_HDPHOTO)
        else:      # pragma: no cover - check() refuses these first
            raise UnsupportedPart(f"relationship {rel.reltype}")
        self.cache[rid] = out
        return out

    def added(self) -> list[str]:
        now = {str(p.partname) for p in self.dst.package.iter_parts()}
        return sorted(now - self.pkg_parts_before)


def _r_attrs(root):
    for e in root.iter():
        if not isinstance(e.tag, str):
            continue
        for k, v in e.attrib.items():
            if k.startswith(R_NS):
                yield e, k, v


# ------------------------------------------------------------------ core

def _demote_placeholder(el, proxy, policy: StripPolicy) -> bool:
    """False when the placeholder should be dropped (empty); True when it was turned into a plain shape."""
    nvpr = None
    for c in el:
        if isinstance(c.tag, str) and local(c).startswith("nv"):
            nvpr = c.find(P("nvPr"))
    ph = nvpr.find(P("ph")) if nvpr is not None else None
    if ph is None:
        return True
    if policy.placeholders == "raise":
        raise UnsupportedPart(f"{_sname(el)} (id {_sid(el)}) is a placeholder", need="a plain shape",
                              have=f"ph type={ph.get('type', 'body')}", hint="use placeholders='demote'")
    has_text = any((t.text or "").strip() for t in el.iter(A("t")))
    if local(el) == "sp" and not has_text:
        return False
    sppr = el.find(P("spPr"))
    if sppr is not None and sppr.find(A("xfrm")) is None:
        try:
            box = (proxy.left, proxy.top, proxy.width, proxy.height)
        except Exception:
            box = (None,)
        if None in box:
            raise UnsupportedPart(f"{_sname(el)} (id {_sid(el)}) placeholder", need="an inherited box",
                                  have="none on its layout", hint="give the placeholder its own position")
        x = OxmlElement("a:xfrm")
        etree.SubElement(x, A("off"), x=str(int(box[0])), y=str(int(box[1])))
        etree.SubElement(x, A("ext"), cx=str(int(box[2])), cy=str(int(box[3])))
        sppr.insert(0, x)
    nvpr.remove(ph)
    return True


def _copy_elements(src_part, items, dst_slide, strip: StripPolicy) -> IdMap:
    """items: [(source element, source proxy or None)] in paint order. Writes nothing until every
    refusal has had its chance."""
    idmap = IdMap()
    dst_part = dst_slide.part
    copies = []
    src_ids_in_set: dict[int, int] = {}
    for el, proxy in items:
        c = _copy.deepcopy(el)
        if local(c) in SHAPE_TAGS and not _demote_placeholder(c, proxy, strip):
            continue
        _apply_strip(c, strip)
        _unsupported(c, src_part)
        copies.append(c)
    relinker = _Relinker(src_part, dst_part, idmap)
    for c in copies:
        for e, k, v in _r_attrs(c):
            relinker.check(v, f"{_sname(c) or local(c)} {local(e)}@r:{k[len(R_NS):]}")
    # --- nothing has been written to the destination above this line ---
    # fresh ids, in document order, above the destination's largest id at this moment
    nid = next_id(dst_slide)
    for c in copies:
        for nv in c.iter(P("cNvPr")):
            old = int(nv.get("id", "0")) if (nv.get("id") or "").isdigit() else 0
            if old in src_ids_in_set:
                idmap.duplicate_src_ids.add(old)
            src_ids_in_set[old] = nid
            idmap.ids.setdefault(old, nid)
            idmap.src_names.setdefault(nv.get("name", ""), []).append(old)
            nv.set("id", str(nid))
            idmap.elements[nid] = nv.getparent().getparent()
            nid += 1
        idmap.top.append(int(_cnvpr(c).get("id")) if _cnvpr(c) is not None else 0)
    # glue
    for c in copies:
        for tag in ("stCxn", "endCxn"):
            for g in list(c.iter(A(tag))):
                old = int(g.get("id", "0"))
                if strip.glue == "remap" and old in idmap.ids and old not in idmap.duplicate_src_ids:
                    g.set("id", str(idmap.ids[old]))
                    idmap.glue_remapped += 1
                else:
                    g.getparent().remove(g)
                    idmap.glue_stripped += 1
    # relationships
    for c in copies:
        for e, k, v in list(_r_attrs(c)):
            if v:
                e.set(k, relinker.new(v))
    # every SVG blip gets a PNG fallback and the svg content type
    for c in copies:
        for blip in c.iter(A("blip")):
            svg = blip.find(A("extLst") + "/" + A("ext") + "/" + qn("asvg:svgBlip"))
            if svg is None:
                continue
            spart = dst_part.related_part(svg.get(R_NS + "embed"))
            if spart.content_type != SVG_CT:        # wrong content type in the source: recreate the part
                fixed = add_svg_part(dst_part.package, spart.blob)
                svg.set(R_NS + "embed", dst_part.relate_to(fixed, RT.IMAGE))
                spart = fixed
            if not blip.get(R_NS + "embed"):
                pic = blip
                while pic is not None and local(pic) not in ("pic", "sp"):
                    pic = pic.getparent()
                pw, ph = _fallback_px(pic) if pic is not None and local(pic) == "pic" else (256, 256)
                png = rasterise_svg(spart.blob, pw, ph)
                blip.set(R_NS + "embed", dst_part.relate_to(_image_part(dst_part.package, png, "png"), RT.IMAGE))
    tree = dst_slide.shapes._spTree
    for c in copies:
        tree.append(c)
    idmap.parts_added = relinker.added()
    return idmap


def copy_shapes(src_slide, dst_slide, *, select: Callable | Iterable | None = None,
                strip: StripPolicy = DEVICE_STRIP) -> IdMap:
    """Copy the source slide's top-level shapes (each group whole) onto dst_slide, in paint order.

    select is None (everything), a predicate on the python-pptx shape, or an iterable of shape ids
    and names. Works within one package and across packages. Returns the IdMap of every copied id,
    group children included. Raises UnsupportedPart (charts, OLE, SmartArt, ink, media, a dangling or
    foreign relationship) before writing anything."""
    tree = src_slide.shapes._spTree
    want = None
    if select is not None and not callable(select):
        want = set(select)
        if not want:
            raise GeometryError("copy_shapes select", need="at least one id or name", have="empty")
    items = []
    seen_keys = set()
    for el in _top_level(tree, strip):
        try:
            proxy = SlideShapeFactory(el, src_slide.shapes) if local(el) in SHAPE_TAGS else None
        except Exception:
            proxy = None
        if want is not None:
            keys = {_sid(el), _sname(el)} & want
            if not keys:
                continue
            seen_keys |= keys
        elif select is not None and not select(proxy):
            continue
        items.append((el, proxy))
    if want is not None and want - seen_keys:
        raise KeyError(f"not top-level shapes on the source slide: {sorted(map(str, want - seen_keys))}")
    return _copy_elements(src_slide.part, items, dst_slide, strip)


def clone_shape(slide, shape, *, name: str, strip: StripPolicy = DEVICE_STRIP):
    """One shape (any slide, any package, group children included) copied onto slide with a fresh id and
    the given name, so a sibling card matches exactly. Appended last in paint order; returns the proxy."""
    el = _el(shape)
    if not name:
        raise GeometryError("clone_shape", need="a role name", have="''", hint="every kit shape is named")
    idmap = _copy_elements(shape.part, [(el, shape)], slide, strip)
    if not idmap.top:
        raise GeometryError(f"{_sname(el)}", need="a shape to copy", have="an empty placeholder (dropped)")
    new = idmap.elements[idmap.top[0]]
    _cnvpr(new).set("name", name)
    return SlideShapeFactory(new, slide.shapes)


def reuse_picture(slide, source_pic, box, *, name: str, alt: str | None = None,
                  strip: StripPolicy = DEVICE_STRIP):
    """Place a copy of an existing picture (any slide, any package) at box, image part reused.

    box is a canvas.Box or (x, y, w, h) in inches. The copy is named, its alt text replaced by alt
    (or left empty for the notes-alt gate to flag), and finished (no p:style, one empty effectLst).
    """
    from .read.xform import EMU_IN
    el = _el(source_pic)
    if local(el) != "pic":
        raise GeometryError(f"{_sname(el)}", need="a picture", have=local(el))
    if not name:
        raise GeometryError("reuse_picture", need="a role name", have="''", hint="every kit shape is named")
    x, y, w, h = (box.x, box.y, box.w, box.h) if hasattr(box, "w") else box
    if not (w > 0 and h > 0):
        raise GeometryError("reuse_picture box", need="w > 0 and h > 0", have=f"w={w} h={h}")
    idmap = _copy_elements(source_pic.part, [(el, source_pic)], slide, strip)
    new = idmap.elements[idmap.top[0]]
    xf = new.find(P("spPr") + "/" + A("xfrm"))
    if xf is None:
        xf = OxmlElement("a:xfrm")
        etree.SubElement(xf, A("off"))
        etree.SubElement(xf, A("ext"))
        new.find(P("spPr")).insert(0, xf)
    for attr in ("rot", "flipH", "flipV"):
        if attr in xf.attrib:
            del xf.attrib[attr]
    xf.find(A("off")).set("x", str(int(round(x * EMU_IN))))
    xf.find(A("off")).set("y", str(int(round(y * EMU_IN))))
    xf.find(A("ext")).set("cx", str(int(round(w * EMU_IN))))
    xf.find(A("ext")).set("cy", str(int(round(h * EMU_IN))))
    nv = _cnvpr(new)
    nv.set("name", name)
    if alt:
        nv.set("descr", alt)
    shape = SlideShapeFactory(new, slide.shapes)
    finish(shape)
    return shape


__all__ = ["StripPolicy", "DEVICE_STRIP", "CLEAN_STRIP", "IdMap", "copy_shapes", "clone_shape", "reuse_picture",
           "add_svg_part", "rasterise_svg"]
