"""Absolute geometry for python-pptx shapes, group baking and the small z-order and reflow helpers.

Every transform comes from deckkit.read.xform (read_xfrm, group_child_to_parent, leaf_geometry), so a
box measured here is the box the read layer and the gates measure. Nothing in this module re-derives
the OOXML group maths.

Units: boxes are reported in inches; xfrm values are written in EMU, rounded to the nearest EMU.
Fonts are never scaled. A group's chOff/chExt scale applies to geometry only (PowerPoint does not
scale text, line weights or insets with a group), so baking a group keeps every run size as written.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Iterator

from pptx.oxml.xmlchemy import OxmlElement
from pptx.shapes.shapetree import BaseShapeFactory, SlideShapeFactory

from .errors import GeometryError
from .ooxml import next_id
from .read.ns import A, P, is_true, local
from .read.walk import Walker
from .read.xform import EMU_IN, IDENT, Affine, ap, group_child_to_parent, leaf_geometry, mul, read_xfrm

SHAPE_TAGS = ("sp", "pic", "cxnSp", "grpSp", "graphicFrame", "contentPart")
KIND = {"sp": "sp", "pic": "pic", "cxnSp": "cxn", "grpSp": "grp", "graphicFrame": "frame",
        "contentPart": "content"}
_LIN_TOL = 1e-9          # linear part of an identity transform
_EMU_TOL = 0.5           # translation part of an identity transform, in EMU
_ORTHO_TOL = 1e-6        # cosine between the two box axes above which the composed map is a shear
_CHECK_TOL_IN = 2.0 / EMU_IN * 2   # post-bake self-check: corners agree to a few EMU


# ------------------------------------------------------------------ records

@dataclass
class AbsGeom:
    """One shape's absolute geometry on the slide.

    x, y, w, h  axis-aligned box the renderer paints (rotation, flips and every ancestor group applied)
    cx, cy      centre; frame_w, frame_h the shape's own sides after group scale, before rotation
    rot_deg     absolute rotation; mirrored when the composed map flips handedness; sheared when a
                rotated child sits under non-uniform group scale (bake_groups refuses those)
    corners     the four box corners in paint order (top-left, top-right, bottom-right, bottom-left)
    start, end  path start and end (connector endpoints), flips and rotation applied
    """
    el: object
    id: int
    name: str
    kind: str
    depth: int
    parent_id: int
    hidden: bool
    x: float
    y: float
    w: float
    h: float
    cx: float
    cy: float
    frame_w: float
    frame_h: float
    rot_deg: float
    mirrored: bool
    sheared: bool
    corners: list = field(default_factory=list)
    start: tuple = (0.0, 0.0)
    end: tuple = (0.0, 0.0)
    group_scale: tuple = (1.0, 1.0)
    has_xfrm: bool = True
    _proxy: object = field(default=None, repr=False)

    @property
    def r(self) -> float:
        return self.x + self.w

    @property
    def b(self) -> float:
        return self.y + self.h

    @property
    def ltrb(self) -> tuple[float, float, float, float]:
        return (self.x, self.y, self.x + self.w, self.y + self.h)

    @property
    def shape(self):
        """The python-pptx proxy for this element (None when built from a bare element)."""
        return self._proxy


@dataclass
class BakeReport:
    groups: list[int] = field(default_factory=list)     # group ids rewritten to identity
    leaves: list[int] = field(default_factory=list)     # descendant ids whose xfrm was rewritten


# ------------------------------------------------------------------ element helpers

def _el(shape_or_el):
    return getattr(shape_or_el, "_element", shape_or_el)


def _cnvpr(el):
    for c in el:
        if local(c).startswith("nv"):
            return c.find(P("cNvPr"))
    return None


def shape_id(el) -> int:
    c = _cnvpr(_el(el))
    return int(c.get("id", "0")) if c is not None else 0


def shape_name(el) -> str:
    c = _cnvpr(_el(el))
    return c.get("name", "") if c is not None else ""


def _xfrm_el(el, create: bool = False):
    """The element's own xfrm: a:xfrm under spPr/grpSpPr, p:xfrm on a graphicFrame."""
    t = local(el)
    if t == "graphicFrame":
        x = el.find(P("xfrm"))
        if x is None and create:
            raise GeometryError(f"{shape_name(el) or 'graphicFrame'} has no p:xfrm", hint="frames always carry one")
        return x
    pr = el.find(P("grpSpPr")) if t == "grpSp" else el.find(P("spPr"))
    if pr is None:
        if create:
            raise GeometryError(f"{shape_name(el) or t} has no shape properties", hint="not a drawable shape")
        return None
    x = pr.find(A("xfrm"))
    if x is None and create:
        from lxml import etree
        x = OxmlElement("a:xfrm")      # python-pptx's element classes, so its proxies keep working
        pr.insert(0, x)
        etree.SubElement(x, A("off"), x="0", y="0")
        etree.SubElement(x, A("ext"), cx="0", cy="0")
    return x


def _ancestor_groups(el) -> list:
    """grpSp ancestors from the outermost down, stopping at the spTree (whose xfrm the read layer ignores)."""
    out = []
    for anc in el.iterancestors():
        t = local(anc)
        if t == "spTree":
            break
        if t == "grpSp":
            out.append(anc)
    out.reverse()
    return out


def parent_transform(el) -> Affine:
    """The composed child-to-slide transform of every group above el (IDENT at top level)."""
    M = IDENT
    for g in _ancestor_groups(_el(el)):
        r = read_xfrm(_xfrm_el(g))
        if r is not None:
            M = mul(M, group_child_to_parent(r))
    return M


def _raw_xfrm(el, proxy=None) -> tuple[dict, bool]:
    """The raw xfrm dict; a placeholder with no xfrm inherits through python-pptx (layout, then master)."""
    r = read_xfrm(_xfrm_el(el))
    if r is not None:
        return r, True
    if proxy is not None:
        try:
            x, y, w, h = proxy.left, proxy.top, proxy.width, proxy.height
        except (AttributeError, ValueError):
            x = y = w = h = None
        if None not in (x, y, w, h):
            return dict(x=int(x), y=int(y), w=int(w), h=int(h), rot=0.0, fh=False, fv=False), True
    return dict(x=0, y=0, w=0, h=0, rot=0.0, fh=False, fv=False), False


def _geom(el, P_: Affine, proxy=None, depth=None, parent_id=None) -> AbsGeom:
    r, has = _raw_xfrm(el, proxy)
    g = leaf_geometry(r, P_)
    fr = g["frame"]
    bx, by, bw, bh = g["bbox_in"]
    c = _cnvpr(el)
    if depth is None:
        anc = _ancestor_groups(el)
        depth = len(anc)
        parent_id = shape_id(anc[-1]) if anc else 0
    return AbsGeom(
        el=el, id=int(c.get("id", "0")) if c is not None else 0, name=c.get("name", "") if c is not None else "",
        kind=KIND.get(local(el), local(el)), depth=depth, parent_id=parent_id or 0,
        hidden=c is not None and is_true(c.get("hidden")),
        x=bx, y=by, w=bw, h=bh, cx=fr["cx_in"], cy=fr["cy_in"], frame_w=fr["w_in"], frame_h=fr["h_in"],
        rot_deg=fr["rot_deg"], mirrored=fr["mirrored"], sheared=fr["sheared"],
        corners=list(g["corners_in"]), start=tuple(g["start_in"]), end=tuple(g["end_in"]),
        group_scale=tuple(g["group_scale"]), has_xfrm=has, _proxy=proxy)


def _proxy(el, slide):
    if slide is None:
        return None
    top = el.getparent() is not None and local(el.getparent()) == "spTree"
    factory = SlideShapeFactory if top else BaseShapeFactory
    try:
        return factory(el, slide.shapes)
    except Exception:          # an unknown element still gets geometry, just no proxy
        return None


def _children(container) -> Iterator:
    """Shape elements in paint order; mc:AlternateContent resolved exactly as the read layer resolves it."""
    for el in container:
        t = local(el)
        if t == "AlternateContent":
            pick = Walker._mc_pick(None, el)       # the read layer's own choice rule, not a copy of it
            if pick is None:
                continue
            for sub in pick:
                if local(sub) in SHAPE_TAGS:
                    yield sub
        elif t in SHAPE_TAGS:
            yield el


def _sptree(slide):
    return slide.shapes._spTree


# ------------------------------------------------------------------ public: measuring

def abs_box(shape) -> AbsGeom:
    """Absolute geometry of one shape (leaf or group), every ancestor group's transform composed.

    Accepts a python-pptx shape or a bare lxml shape element. A placeholder without its own xfrm
    inherits its box through python-pptx when a proxy is given."""
    el = _el(shape)
    proxy = shape if shape is not el else None
    return _geom(el, parent_transform(el), proxy)


def iter_abs(slide, *, groups: bool = False, hidden: bool = True) -> Iterator[AbsGeom]:
    """Every leaf on the slide in paint order, group children included, with absolute geometry.

    groups=True also yields each group (before its children). hidden=False skips hidden shapes and the
    descendants of hidden groups, matching what renders."""
    def walk(container, M, depth, pid):
        for el in _children(container):
            c = _cnvpr(el)
            hid = c is not None and is_true(c.get("hidden"))
            if hid and not hidden:
                continue
            if local(el) == "grpSp":
                if groups:
                    yield _geom(el, M, _proxy(el, slide), depth, pid)
                r = read_xfrm(_xfrm_el(el))
                Mi = mul(M, group_child_to_parent(r)) if r is not None else M
                yield from walk(el, Mi, depth + 1, shape_id(el))
            else:
                yield _geom(el, M, _proxy(el, slide), depth, pid)

    yield from walk(_sptree(slide), IDENT, 0, 0)


def rotated_box(shape_or_xywh, rot_deg: float | None = None) -> tuple[float, float, float, float]:
    """The axis-aligned (left, top, right, bottom) box a renderer paints.

    Given a shape, this is its absolute box (groups composed). Given (x, y, w, h) in inches plus a
    rotation, it is the box of that rectangle rotated about its centre."""
    if isinstance(shape_or_xywh, (tuple, list)):
        x, y, w, h = shape_or_xywh
        t = math.radians(rot_deg or 0.0)
        aw = abs(w * math.cos(t)) + abs(h * math.sin(t))
        ah = abs(w * math.sin(t)) + abs(h * math.cos(t))
        cx, cy = x + w / 2.0, y + h / 2.0
        return (cx - aw / 2.0, cy - ah / 2.0, cx + aw / 2.0, cy + ah / 2.0)
    return abs_box(shape_or_xywh).ltrb


def find(slide, name_or_id):
    """The one shape with this id (int) or name (str), searched through every group.

    Missing raises KeyError; a name carried by more than one shape raises LookupError naming the ids,
    because returning whichever comes first is how duplicate-id defects hide."""
    key_is_id = isinstance(name_or_id, int)
    hits = []
    for c in _sptree(slide).iter(P("cNvPr")):
        if (key_is_id and c.get("id") == str(name_or_id)) or (not key_is_id and c.get("name") == name_or_id):
            el = c.getparent().getparent()
            if local(el) in SHAPE_TAGS:
                hits.append(el)
    if not hits:
        raise KeyError(f"shape {name_or_id!r} is not on this slide")
    if len(hits) > 1:
        raise LookupError(f"{len(hits)} shapes match {name_or_id!r} (ids {[shape_id(e) for e in hits]}); "
                          "name them uniquely or look up by id")
    return _proxy(hits[0], slide)


def body_extent(slide, top_floor: float, *, skip: Iterable = ()) -> tuple[float, float]:
    """(top, bottom) in inches of the top-level shapes whose absolute top is at or below top_floor.

    skip holds shape ids or names to leave out (the title, a bleed image). Raises GeometryError when no
    shape qualifies, rather than returning an invented extent."""
    skip = set(skip)
    tops, bots = [], []
    for el in _children(_sptree(slide)):
        if shape_id(el) in skip or shape_name(el) in skip:
            continue
        g = _geom(el, IDENT, _proxy(el, slide), 0, 0)
        if not g.has_xfrm or g.y < top_floor:
            continue
        tops.append(g.y)
        bots.append(g.b)
    if not tops:
        raise GeometryError("body extent", need=f"a shape at or below {top_floor:.2f} in", have="none",
                            hint="lower top_floor or check the skip list")
    return min(tops), max(bots)


# ------------------------------------------------------------------ public: editing

def to_front(slide, shape):
    """Re-append a top-level shape so it paints last (clones append, so a cloned card can land on top)."""
    el = _el(shape)
    parent = el.getparent()
    if parent is None or local(parent) != "spTree":
        raise GeometryError(f"{shape_name(el)} is inside a group", hint="to_front moves top-level shapes only")
    parent.remove(el)
    _sptree(slide).append(el)
    return shape


def affine_y(slide, old_top: float, old_bot: float, new_top: float, new_bot: float, *,
             skip: Iterable = (), grow_small: float = 0.55) -> float:
    """Map the band [old_top, old_bot] onto [new_top, new_bot] (inches) for top-level shapes.

    Shapes taller than grow_small stretch with the band; smaller ones move by their centre so badges
    and chips keep their proportions. Groups always move by centre and never stretch, because
    stretching a group's ext without its chExt is a scaled group transform. skip takes ids or names.
    Returns the scale factor."""
    if old_bot - old_top <= 0:
        raise GeometryError("affine_y source band", need="> 0 in", have=old_bot - old_top)
    f = (new_bot - new_top) / (old_bot - old_top)
    skip = set(skip)
    eps = 0.005
    for el in _children(_sptree(slide)):
        if shape_id(el) in skip or shape_name(el) in skip:
            continue
        x = _xfrm_el(el)
        r = read_xfrm(x)
        if r is None:
            continue
        t, h = r["y"] / EMU_IN, r["h"] / EMU_IN
        if t < old_top - eps or t > old_bot + eps:
            continue
        if h >= grow_small and local(el) != "grpSp":
            nt, nh = new_top + (t - old_top) * f, h * f
        else:
            c = t + h / 2.0
            nt, nh = new_top + (c - old_top) * f - h / 2.0, h
        dy = int(round(nt * EMU_IN)) - r["y"]
        x.find(A("off")).set("y", str(r["y"] + dy))
        x.find(A("ext")).set("cy", str(int(round(nh * EMU_IN))))
    return f


# ------------------------------------------------------------------ public: baking

def _is_identity(M: Affine) -> bool:
    a, b, c, d, e, f = M
    return (abs(a - 1) < _LIN_TOL and abs(b) < _LIN_TOL and abs(c) < _LIN_TOL and abs(d - 1) < _LIN_TOL
            and abs(e) < _EMU_TOL and abs(f) < _EMU_TOL)


def _unit(vx: float, vy: float) -> tuple[float, float, float]:
    n = math.hypot(vx, vy)
    return (vx / n, vy / n, n) if n > 0 else (0.0, 0.0, 0.0)


def _decompose(r: dict, M_parent: Affine, what: str) -> dict:
    """New absolute xfrm (EMU) for a shape whose parent map is M_parent: same centre, same painted
    corners, rotation and flips chosen so the box is not sheared. Refuses a shear."""
    g = leaf_geometry(r, M_parent)
    a, b, c, d, _, _ = g["M_full"]
    w, h = r["w"], r["h"]
    u1x, u1y, n1 = _unit(a, b)
    u2x, u2y, n2 = _unit(c, d)
    if w > 0 and h > 0 and n1 > 0 and n2 > 0 and abs(u1x * u2x + u1y * u2y) > _ORTHO_TOL:
        rot_child = r["rot"]
        raise GeometryError(
            f"{what}: rotated child ({rot_child:.1f} deg) under non-uniform group scale",
            need="an orthogonal box", have=f"axes at {math.degrees(math.acos(max(-1, min(1, u1x*u2x+u1y*u2y)))):.2f} deg",
            hint="the composed map is a shear; redraw the child unrotated or ungroup it in PowerPoint first")
    fh0, fv0 = bool(r["fh"]), bool(r["fv"])
    chosen = None
    for fh, fv in ((fh0, fv0), (not fh0, fv0), (fh0, not fv0), (not fh0, not fv0)):
        sx, sy = (-1.0 if fh else 1.0), (-1.0 if fv else 1.0)
        if n1 > 0 and w > 0:
            th = math.atan2(sx * u1y, sx * u1x)
        elif n2 > 0 and h > 0:
            th = math.atan2(-sy * u2x, sy * u2y)
        else:
            th = math.atan2(sx * u1y, sx * u1x) if n1 > 0 else 0.0
        if w > 0 and h > 0 and n2 > 0:
            # R(th) e2 times sy must equal u2
            ex, ey = -math.sin(th) * sy, math.cos(th) * sy
            if abs(ex - u2x) > 1e-6 or abs(ey - u2y) > 1e-6:
                continue
        chosen = (th, fh, fv)
        break
    if chosen is None:      # pragma: no cover - orthogonal maps always decompose
        raise GeometryError(f"{what}: cannot decompose the composed transform", hint="report this shape")
    th, fh, fv = chosen
    nw, nh = w * n1, h * n2
    ccx, ccy = ap(g["M_full"], r["x"] + w / 2.0, r["y"] + h / 2.0)
    deg = math.degrees(th) % 360.0
    if abs(deg - 360.0) < 1e-7:
        deg = 0.0
    return dict(x=int(round(ccx - nw / 2.0)), y=int(round(ccy - nh / 2.0)), w=int(round(nw)), h=int(round(nh)),
                rot=deg, fh=fh, fv=fv, before=g)


def _paint_points(r: dict, M_parent: Affine) -> list[tuple[float, float]]:
    """Slide-space EMU points of the box's four corners and both path ends under the full map
    (flips included), in parameter order, so an equivalent flip/rotation pair compares equal."""
    Mf = leaf_geometry(r, M_parent)["M_full"]
    x, y, w, h = r["x"], r["y"], r["w"], r["h"]
    return [ap(Mf, x + u * w, y + v * h) for u, v in ((0, 0), (1, 0), (1, 1), (0, 1), (0.5, 0.5))]


def _drift(p1, p2) -> float:
    return max(max(abs(a[0] - b[0]), abs(a[1] - b[1])) for a, b in zip(p1, p2))


def _write_xfrm(el, nx: dict) -> None:
    x = _xfrm_el(el, create=True)
    rot = int(round(nx["rot"] * 60000)) % 21600000
    if rot:
        x.set("rot", str(rot))
    elif "rot" in x.attrib:
        del x.attrib["rot"]
    for attr, on in (("flipH", nx["fh"]), ("flipV", nx["fv"])):
        if on:
            x.set(attr, "1")
        elif attr in x.attrib:
            del x.attrib[attr]
    x.find(A("off")).set("x", str(nx["x"]))
    x.find(A("off")).set("y", str(nx["y"]))
    x.find(A("ext")).set("cx", str(max(0, nx["w"])))
    x.find(A("ext")).set("cy", str(max(0, nx["h"])))


def _set_identity_group(g, x0: int, y0: int, x1: int, y1: int) -> None:
    from lxml import etree
    x = _xfrm_el(g, create=True)
    for attr in ("rot", "flipH", "flipV"):
        if attr in x.attrib:
            del x.attrib[attr]
    w, h = max(0, x1 - x0), max(0, y1 - y0)
    for tag, keys, vals in (("off", ("x", "y"), (x0, y0)), ("ext", ("cx", "cy"), (w, h)),
                            ("chOff", ("x", "y"), (x0, y0)), ("chExt", ("cx", "cy"), (w, h))):
        e = x.find(A(tag))
        if e is None:
            e = etree.SubElement(x, A(tag))
        for k, v in zip(keys, vals):
            e.set(k, str(int(v)))


def _corners_emu(el) -> list[tuple[float, float]]:
    """Painted corners in EMU of a shape whose ancestors are (now) identity."""
    r = read_xfrm(_xfrm_el(el))
    if r is None:
        return []
    return [(px * EMU_IN, py * EMU_IN) for px, py in leaf_geometry(r, IDENT)["corners_in"]]


def bake_groups(slide) -> BakeReport:
    """Write absolute geometry into every group child and make every group an identity transform.

    After baking, each group's off equals chOff and ext equals chExt (its children's bounding box), it
    carries no rotation or flip, and each child's own xfrm paints the same corners it painted before.
    Fonts, line weights and insets are untouched (groups never scaled them). Refuses with GeometryError,
    before writing anything, on a shear (a rotated child under non-uniform scale), on a table under a
    scaled group (its grid would not follow) and on a rotated graphic frame."""
    tree = _sptree(slide)
    plan: list[tuple[object, dict]] = []      # (leaf element, new xfrm), computed before any write
    groups_post: list[object] = []           # groups in post-order (children first)

    def walk(container, M):
        for el in _children(container):
            t = local(el)
            r = read_xfrm(_xfrm_el(el))
            if t == "grpSp":
                Mi = mul(M, group_child_to_parent(r)) if r is not None else M
                walk(el, Mi)
                own_identity = r is None or _is_identity(group_child_to_parent(r))
                if not (_is_identity(M) and own_identity):
                    groups_post.append(el)
                continue
            if r is None or _is_identity(M):
                continue
            what = shape_name(el) or f"id {shape_id(el)}"
            nx = _decompose(r, M, what)
            if t == "graphicFrame":
                if nx["rot"] or nx["fh"] or nx["fv"]:
                    raise GeometryError(f"{what}: graphic frame would need rotation {nx['rot']:.1f} deg",
                                        hint="frames cannot rotate; ungroup it from the rotated group")
                gd = el.find(A("graphic") + "/" + A("graphicData"))
                is_tbl = gd is not None and gd.find(A("tbl")) is not None
                if is_tbl and (abs(nx["w"] - r["w"]) > 1 or abs(nx["h"] - r["h"]) > 1):
                    raise GeometryError(f"{what}: table under a scaled group", need=f"{r['w']}x{r['h']} EMU",
                                        have=f"{nx['w']}x{nx['h']} EMU",
                                        hint="table grids do not scale with their frame; take it out of the group")
            # verify before writing anything: the new xfrm under identity parents paints the same points
            nx["before_pts"] = _paint_points(r, M)
            new_r = dict(x=nx["x"], y=nx["y"], w=nx["w"], h=nx["h"], rot=nx["rot"], fh=nx["fh"], fv=nx["fv"])
            bad = _drift(nx["before_pts"], _paint_points(new_r, IDENT))
            if bad > _CHECK_TOL_IN * EMU_IN:
                raise GeometryError(f"{what}: baked geometry would drift", need="<= 4 EMU", have=f"{bad:.0f} EMU",
                                    hint="report this shape; nothing was written")
            plan.append((el, nx))

    walk(tree, IDENT)
    report = BakeReport()
    for el, nx in plan:
        _write_xfrm(el, nx)
        report.leaves.append(shape_id(el))
    # groups bottom-up: every descendant is now absolute, so a group's box is the union of its children
    for g in groups_post:
        pts = []
        for ch in _children(g):
            if local(ch) == "grpSp":
                r = read_xfrm(_xfrm_el(ch))
                if r is not None:
                    pts += [(r["x"], r["y"]), (r["x"] + r["w"], r["y"] + r["h"])]
            else:
                pts += _corners_emu(ch)
        if not pts:
            continue
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        _set_identity_group(g, int(math.floor(min(xs) + 1e-6)), int(math.floor(min(ys) + 1e-6)),
                            int(math.ceil(max(xs) - 1e-6)), int(math.ceil(max(ys) - 1e-6)))
        report.groups.append(shape_id(g))
    # end state, re-read from the written XML: every child paints the points it painted before
    for el, nx in plan:
        r_now = read_xfrm(_xfrm_el(el))
        bad = _drift(nx["before_pts"], _paint_points(r_now, parent_transform(el)))
        if bad > _CHECK_TOL_IN * EMU_IN:
            raise GeometryError(f"{shape_name(el)}: baked geometry drifted after writing", need="<= 4 EMU",
                                have=f"{bad:.0f} EMU", hint="report this shape; nothing was clamped")
    for g in groups_post:
        if not _is_identity(group_child_to_parent(read_xfrm(_xfrm_el(g)))):
            raise GeometryError(f"{shape_name(g)}: group still carries a transform after baking")
    return report


def identity_group(slide, shapes, name: str):
    """Wrap sibling top-level shapes in a new group whose transform is the identity.

    The group takes the z position of its lowest member, keeps the members' paint order, gets a fresh
    id and the given name, and its off/chOff and ext/chExt are the members' painted bounding box. Shapes
    inside a scaled group must be baked first (bake_groups); the group is never a scaled transform."""
    from lxml import etree
    if not name:
        raise GeometryError("identity_group", need="a role name", have="''", hint="every kit shape is named")
    els = [_el(s) for s in shapes]
    if not els:
        raise GeometryError("identity_group", need=">= 1 shape", have=0)
    tree = _sptree(slide)
    parents = {id(e.getparent()) for e in els}
    if len(parents) != 1 or els[0].getparent() is not tree:
        raise GeometryError("identity_group members", need="top-level siblings", have="mixed parents",
                            hint="bake_groups, then group shapes that sit directly on the slide")
    order = {id(e): i for i, e in enumerate(tree)}
    els.sort(key=lambda e: order[id(e)])
    pts = []
    for e in els:
        if local(e) == "grpSp":
            r = read_xfrm(_xfrm_el(e))
            if r is None:
                continue
            pts += [(px * EMU_IN, py * EMU_IN) for px, py in leaf_geometry(r, IDENT)["corners_in"]]
        else:
            pts += _corners_emu(e)
    if not pts:
        raise GeometryError("identity_group members", need="at least one positioned shape", have="none")
    gid = next_id(slide)
    g = OxmlElement("p:grpSp")         # python-pptx's element class, so the returned proxy works
    nv = etree.SubElement(g, P("nvGrpSpPr"))
    etree.SubElement(nv, P("cNvPr"), id=str(gid), name=name)
    etree.SubElement(nv, P("cNvGrpSpPr"))
    etree.SubElement(nv, P("nvPr"))
    etree.SubElement(g, P("grpSpPr"))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    _set_identity_group(g, int(math.floor(min(xs) + 1e-6)), int(math.floor(min(ys) + 1e-6)),
                        int(math.ceil(max(xs) - 1e-6)), int(math.ceil(max(ys) - 1e-6)))
    tree.insert(tree.index(els[0]), g)
    for e in els:
        g.append(e)
    return _proxy(g, slide)


__all__ = ["AbsGeom", "BakeReport", "abs_box", "iter_abs", "rotated_box", "bake_groups", "identity_group",
           "find", "affine_y", "to_front", "body_extent", "parent_transform", "shape_id", "shape_name"]
