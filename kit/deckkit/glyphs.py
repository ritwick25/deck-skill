"""Native line glyphs: Lucide icons converted to DrawingML custGeom, stroked in a theme role.

Why native and not pictures: a custGeom glyph is a shape, so its line is a schemeClr role and it recolours
with the theme (a client cut is a theme swap), it stays crisp at any zoom, and the twin can draw it as SVG.

Source: lucide-react (ISC, see kit/assets/LICENSE-lucide.txt). scripts/build_glyphs.py reads the icon
nodes from dist/esm/icons/*.mjs and writes kit/assets/glyphs.json through the converters below, so the
JSON holds DrawingML-ready operations and no SVG parsing happens at deck-build time.

Geometry, all in Lucide's 24 x 24 space (y down, as in DrawingML):
  * path d: M L H V C S Q T A Z, absolute and relative, implicit repeats, compact flags in arcs
  * circle, ellipse, rect (rx/ry), line, polyline, polygon
  * Q and T become cubics (exact); A becomes cubics of at most 90 degrees each (SVG 1.1 F.6.5)
  * output ops: ("M", x, y) ("L", x, y) ("C", x1, y1, x2, y2, x, y) ("Z",)

Rendering: one <a:path w=24000 h=24000> per fill class, stroke-only paths fill="none". Lucide draws at
stroke 2 on 24 with round caps and joins, so the line width is 2/24 of the glyph's side unless the
caller passes stroke_pt. The few source nodes Lucide fills (dot markers) go in a second path that is
filled and stroked in the same role, as the source draws them.
"""
from __future__ import annotations

import json
import math
import re
from functools import lru_cache
from pathlib import Path

from lxml import etree

from . import ooxml
from .canvas import EMU_PER_IN, Box
from .errors import GeometryError, UnsupportedPart
from .read.ns import NS

_A = "{%s}" % NS["a"]
_P = "{%s}" % NS["p"]

KIT = Path(__file__).resolve().parent.parent
GLYPHS_JSON = KIT / "assets" / "glyphs.json"
SPACE = 24.0                 # Lucide's viewBox side
SCALE = 1000                 # path units per Lucide unit: 24 -> 24000, integer coordinates
LUCIDE_STROKE = 2.0          # Lucide's stroke width in its own units
KAPPA = 0.5522847498307936   # cubic control distance for a quarter circle
MIN_SIDE_IN = 0.12           # below this a 2/24 stroke is under 0.75pt and the glyph reads as a smudge


class UnknownGlyph(UnsupportedPart, LookupError):
    """A glyph name that is not in glyphs.json. Never substituted with a near match."""


# ------------------------------------------------------------------ SVG path parsing

_NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_CMD = set("MmLlHhVvCcSsQqTtAaZz")
_ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}


class _Scan:
    def __init__(self, d: str):
        self.d = d
        self.i = 0

    def _skip(self):
        while self.i < len(self.d) and (self.d[self.i] in " \t\r\n,"):
            self.i += 1

    def done(self) -> bool:
        self._skip()
        return self.i >= len(self.d)

    def peek_cmd(self):
        self._skip()
        if self.i < len(self.d) and self.d[self.i] in _CMD:
            return self.d[self.i]
        return None

    def cmd(self) -> str:
        c = self.peek_cmd()
        if c is None:
            raise GeometryError("svg path", need="a command letter", have=self.d[self.i:self.i + 12])
        self.i += 1
        return c

    def num(self) -> float:
        self._skip()
        m = _NUM.match(self.d, self.i)
        if not m:
            raise GeometryError("svg path", need="a number", have=self.d[self.i:self.i + 12] or "end")
        self.i = m.end()
        return float(m.group(0))

    def flag(self) -> int:
        self._skip()
        if self.i < len(self.d) and self.d[self.i] in "01":
            self.i += 1
            return int(self.d[self.i - 1])
        raise GeometryError("svg arc flag", need="0 or 1", have=self.d[self.i:self.i + 6] or "end")

    def has_num(self) -> bool:
        self._skip()
        return self.i < len(self.d) and _NUM.match(self.d, self.i) is not None


def arc_to_cubics(x1, y1, rx, ry, phi_deg, large, sweep, x2, y2) -> list[tuple]:
    """SVG elliptical arc (endpoint form) to cubic ops, each spanning at most 90 degrees (SVG 1.1 F.6.5)."""
    if abs(x1 - x2) < 1e-12 and abs(y1 - y2) < 1e-12:
        return []
    rx, ry = abs(rx), abs(ry)
    if rx < 1e-12 or ry < 1e-12:
        return [("L", x2, y2)]
    phi = math.radians(phi_deg % 360.0)
    cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (x1 - x2) / 2.0, (y1 - y2) / 2.0
    x1p = cp * dx + sp * dy
    y1p = -sp * dx + cp * dy
    lam = (x1p * x1p) / (rx * rx) + (y1p * y1p) / (ry * ry)
    if lam > 1.0:
        s = math.sqrt(lam)
        rx, ry = rx * s, ry * s
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    coef = math.sqrt(max(0.0, num / den)) if den > 0 else 0.0
    if large == sweep:
        coef = -coef
    cxp = coef * rx * y1p / ry
    cyp = -coef * ry * x1p / rx
    cx = cp * cxp - sp * cyp + (x1 + x2) / 2.0
    cy = sp * cxp + cp * cyp + (y1 + y2) / 2.0

    def ang(ux, uy, vx, vy):
        return math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)

    ux, uy = (x1p - cxp) / rx, (y1p - cyp) / ry
    vx, vy = (-x1p - cxp) / rx, (-y1p - cyp) / ry
    th1 = ang(1.0, 0.0, ux, uy)
    dth = ang(ux, uy, vx, vy)
    if not sweep and dth > 0:
        dth -= 2 * math.pi
    elif sweep and dth < 0:
        dth += 2 * math.pi
    n = max(1, int(math.ceil(abs(dth) / (math.pi / 2) - 1e-9)))
    delta = dth / n
    t = 4.0 / 3.0 * math.tan(delta / 4.0)

    def pt(ex, ey):
        return (cx + rx * ex * cp - ry * ey * sp, cy + rx * ex * sp + ry * ey * cp)

    out = []
    a1 = th1
    for i in range(n):
        a2 = a1 + delta
        c1 = pt(math.cos(a1) - t * math.sin(a1), math.sin(a1) + t * math.cos(a1))
        c2 = pt(math.cos(a2) + t * math.sin(a2), math.sin(a2) - t * math.cos(a2))
        e = (x2, y2) if i == n - 1 else pt(math.cos(a2), math.sin(a2))
        out.append(("C", c1[0], c1[1], c2[0], c2[1], e[0], e[1]))
        a1 = a2
    return out


def parse_path(d: str) -> list[list[tuple]]:
    """An SVG path string to subpaths of ops (M, L, C, Z only). Every subpath starts with M."""
    sc = _Scan(d)
    subs: list[list[tuple]] = []
    cur: list[tuple] | None = None
    x = y = sx = sy = 0.0
    last_c2 = None          # last cubic's second control point, for S
    last_q = None           # last quadratic control point, for T
    closed = False
    cmd = None
    while not sc.done():
        c = sc.peek_cmd()
        if c is not None:
            cmd = sc.cmd()
        elif cmd is None:
            raise GeometryError("svg path", need="a command first", have=d[:12])
        elif cmd in "Zz":
            raise GeometryError("svg path", need="a command after Z", have=d[sc.i:sc.i + 12])
        # an implicit repeat of M is L
        up = cmd.upper()
        rel = cmd.islower()
        if up not in ("M", "Z") and (cur is None or closed):
            # drawing with no open subpath: SVG continues from the current point (the start after Z)
            cur = [("M", x, y)]
            subs.append(cur)
            closed = False
        if up == "Z":
            if cur is not None and not closed:
                cur.append(("Z",))
                closed = True
            x, y = sx, sy
            last_c2 = last_q = None
            continue
        if up == "M":
            nx, ny = sc.num(), sc.num()
            if rel:
                nx, ny = x + nx, y + ny
            cur = [("M", nx, ny)]
            subs.append(cur)
            closed = False
            x, y, sx, sy = nx, ny, nx, ny
            last_c2 = last_q = None
            cmd = "l" if rel else "L"
            continue
        if up == "L":
            nx, ny = sc.num(), sc.num()
            if rel:
                nx, ny = x + nx, y + ny
            cur.append(("L", nx, ny))
            x, y = nx, ny
            last_c2 = last_q = None
        elif up == "H":
            nx = sc.num()
            nx = x + nx if rel else nx
            cur.append(("L", nx, y))
            x = nx
            last_c2 = last_q = None
        elif up == "V":
            ny = sc.num()
            ny = y + ny if rel else ny
            cur.append(("L", x, ny))
            y = ny
            last_c2 = last_q = None
        elif up in "CS":
            if up == "C":
                x1, y1 = sc.num(), sc.num()
                if rel:
                    x1, y1 = x + x1, y + y1
            else:
                x1, y1 = (2 * x - last_c2[0], 2 * y - last_c2[1]) if last_c2 else (x, y)
            x2, y2, ex, ey = sc.num(), sc.num(), sc.num(), sc.num()
            if rel:
                x2, y2, ex, ey = x + x2, y + y2, x + ex, y + ey
            cur.append(("C", x1, y1, x2, y2, ex, ey))
            last_c2 = (x2, y2)
            last_q = None
            x, y = ex, ey
        elif up in "QT":
            if up == "Q":
                qx, qy = sc.num(), sc.num()
                if rel:
                    qx, qy = x + qx, y + qy
            else:
                qx, qy = (2 * x - last_q[0], 2 * y - last_q[1]) if last_q else (x, y)
            ex, ey = sc.num(), sc.num()
            if rel:
                ex, ey = x + ex, y + ey
            cur.append(("C", x + 2.0 / 3.0 * (qx - x), y + 2.0 / 3.0 * (qy - y),
                        ex + 2.0 / 3.0 * (qx - ex), ey + 2.0 / 3.0 * (qy - ey), ex, ey))
            last_q = (qx, qy)
            last_c2 = None
            x, y = ex, ey
        elif up == "A":
            rx, ry, phi = sc.num(), sc.num(), sc.num()
            large, sweep = sc.flag(), sc.flag()
            ex, ey = sc.num(), sc.num()
            if rel:
                ex, ey = x + ex, y + ey
            cur.extend(arc_to_cubics(x, y, rx, ry, phi, large, sweep, ex, ey))
            x, y = ex, ey
            last_c2 = last_q = None
    return subs


# ------------------------------------------------------------------ SVG elements

def _f(attrs: dict, k: str, default: float | None = None) -> float:
    v = attrs.get(k)
    if v is None:
        if default is None:
            raise GeometryError("svg attribute %s" % k, need="a value", have="missing")
        return default
    return float(v)


def _ellipse_ops(cx, cy, rx, ry) -> list[tuple]:
    kx, ky = KAPPA * rx, KAPPA * ry
    return [("M", cx + rx, cy),
            ("C", cx + rx, cy + ky, cx + kx, cy + ry, cx, cy + ry),
            ("C", cx - kx, cy + ry, cx - rx, cy + ky, cx - rx, cy),
            ("C", cx - rx, cy - ky, cx - kx, cy - ry, cx, cy - ry),
            ("C", cx + kx, cy - ry, cx + rx, cy - ky, cx + rx, cy),
            ("Z",)]


def _rect_ops(x, y, w, h, rx, ry) -> list[tuple]:
    rx, ry = min(rx, w / 2.0), min(ry, h / 2.0)
    if rx <= 0 or ry <= 0:
        return [("M", x, y), ("L", x + w, y), ("L", x + w, y + h), ("L", x, y + h), ("Z",)]
    kx, ky = KAPPA * rx, KAPPA * ry
    r, b = x + w, y + h
    return [("M", x + rx, y), ("L", r - rx, y),
            ("C", r - rx + kx, y, r, y + ry - ky, r, y + ry), ("L", r, b - ry),
            ("C", r, b - ry + ky, r - rx + kx, b, r - rx, b), ("L", x + rx, b),
            ("C", x + rx - kx, b, x, b - ry + ky, x, b - ry), ("L", x, y + ry),
            ("C", x, y + ry - ky, x + rx - kx, y, x + rx, y), ("Z",)]


def _points(s: str) -> list[float]:
    return [float(v) for v in _NUM.findall(s or "")]


def node_subpaths(tag: str, attrs: dict) -> list[list[tuple]]:
    """One SVG element (path, circle, ellipse, rect, line, polyline, polygon) to subpaths of ops."""
    if tag == "path":
        return parse_path(attrs.get("d", ""))
    if tag == "circle":
        r = _f(attrs, "r")
        return [_ellipse_ops(_f(attrs, "cx", 0.0), _f(attrs, "cy", 0.0), r, r)]
    if tag == "ellipse":
        return [_ellipse_ops(_f(attrs, "cx", 0.0), _f(attrs, "cy", 0.0), _f(attrs, "rx"), _f(attrs, "ry"))]
    if tag == "rect":
        rx = attrs.get("rx")
        ry = attrs.get("ry")
        rxv = float(rx) if rx is not None else (float(ry) if ry is not None else 0.0)
        ryv = float(ry) if ry is not None else rxv
        return [_rect_ops(_f(attrs, "x", 0.0), _f(attrs, "y", 0.0), _f(attrs, "width"), _f(attrs, "height"),
                          rxv, ryv)]
    if tag == "line":
        return [[("M", _f(attrs, "x1", 0.0), _f(attrs, "y1", 0.0)), ("L", _f(attrs, "x2", 0.0), _f(attrs, "y2", 0.0))]]
    if tag in ("polyline", "polygon"):
        v = _points(attrs.get("points"))
        if len(v) < 4 or len(v) % 2:
            raise GeometryError("svg %s points" % tag, need="two or more x,y pairs", have=len(v))
        ops = [("M", v[0], v[1])] + [("L", v[i], v[i + 1]) for i in range(2, len(v), 2)]
        if tag == "polygon":
            ops.append(("Z",))
        return [ops]
    raise UnsupportedPart("svg element <%s>" % tag, need="path, circle, ellipse, rect, line, polyline, polygon",
                          have=tag)


def _round(v: float) -> float:
    r = round(v, 3)
    return 0.0 if r == 0 else r


def icon_paths(nodes) -> list[dict]:
    """Lucide nodes [(tag, attrs), ...] to [{"fill": bool, "d": [subpath, ...]}], stroke-only first.

    Subpaths are lists of compact ops: ["M", x, y], ["L", x, y], ["C", x1, y1, x2, y2, x, y], ["Z"]."""
    groups = {False: [], True: []}
    for tag, attrs in nodes:
        filled = (attrs.get("fill") or "none") not in ("none", "")
        for sub in node_subpaths(tag, attrs):
            groups[filled].append([[op[0]] + [_round(v) for v in op[1:]] for op in sub])
    return [{"fill": k, "d": groups[k]} for k in (False, True) if groups[k]]


# ------------------------------------------------------------------ Lucide source reading

_NODE = re.compile(r'\[\s*"([a-z]+)"\s*,\s*\{([^}]*)\}\s*\]')
_ATTR = re.compile(r'"?([A-Za-z_][\w-]*)"?\s*:\s*"([^"]*)"')
_ALIAS = re.compile(r"export\s*\{\s*default\s*\}\s*from\s*'\./([\w-]+)\.mjs'")
_ALLOWED_ATTRS = {"d", "cx", "cy", "r", "rx", "ry", "x", "y", "width", "height", "x1", "y1", "x2", "y2",
                  "points", "fill", "key"}


def read_lucide(icons_dir, name: str) -> tuple[str, list[tuple[str, dict]]]:
    """(canonical name, nodes) for one Lucide icon, following alias re-exports. Unknown attributes raise."""
    d = Path(icons_dir)
    seen = []
    cur = name
    while True:
        f = d / ("%s.mjs" % cur)
        if not f.exists():
            raise UnknownGlyph("lucide icon %r" % name, need="dist/esm/icons/%s.mjs" % cur, have="missing")
        src = f.read_text(encoding="utf-8")
        m = _ALIAS.search(src)
        if m and "__iconData" not in src:
            seen.append(cur)
            cur = m.group(1)
            if cur in seen or len(seen) > 4:
                raise UnknownGlyph("lucide icon %r" % name, need="an alias chain that ends", have=seen)
            continue
        break
    start = src.find("node:")
    if start < 0:
        raise UnknownGlyph("lucide icon %r" % cur, need="an icon node list", have="none")
    nodes = []
    for tag, body in _NODE.findall(src[start:]):
        attrs = dict(_ATTR.findall(body))
        bad = set(attrs) - _ALLOWED_ATTRS
        if bad:
            raise UnsupportedPart("lucide %s <%s>" % (cur, tag), need="geometry attributes only", have=sorted(bad),
                                  hint="a transform or style attribute would be silently dropped")
        attrs.pop("key", None)
        nodes.append((tag, attrs))
    if not nodes:
        raise UnknownGlyph("lucide icon %r" % cur, need="at least one node", have=0)
    return cur, nodes


# ------------------------------------------------------------------ the catalogue

@lru_cache(maxsize=1)
def _catalogue() -> dict:
    try:
        with open(GLYPHS_JSON, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        raise UnknownGlyph("glyphs.json", need=str(GLYPHS_JSON), have="missing",
                           hint="run scripts/build_glyphs.py") from None


def names() -> list[str]:
    return sorted(_catalogue()["glyphs"])


def aliases() -> dict:
    return dict(_catalogue().get("aliases") or {})


def resolve(name: str) -> str:
    cat = _catalogue()
    if name in cat["glyphs"]:
        return name
    a = (cat.get("aliases") or {}).get(name)
    if a in cat["glyphs"]:
        return a
    import difflib
    close = difflib.get_close_matches(name, list(cat["glyphs"]) + list(cat.get("aliases") or {}), n=4)
    raise UnknownGlyph("glyph %r" % name, need="a name in glyphs.json", have="not curated",
                       hint=("closest: " + ", ".join(close)) if close else "add it to scripts/build_glyphs.py CURATED")


def paths(name: str) -> list[dict]:
    """The stored path groups for a glyph (see icon_paths)."""
    return _catalogue()["glyphs"][resolve(name)]["paths"]


def validate_paths(groups) -> list[str]:
    """Problems with a stored path list: empty, a subpath not opening with M, an unknown op, a wrong
    arity, a non-finite number, or a point outside the padded 24-unit square. [] means valid."""
    out = []
    if not groups:
        return ["no path groups"]
    for gi, g in enumerate(groups):
        if not g.get("d"):
            out.append("group %d empty" % gi)
        for si, sub in enumerate(g.get("d") or []):
            if not sub or sub[0][0] != "M":
                out.append("group %d subpath %d does not open with M" % (gi, si))
            if len(sub) < 2:
                out.append("group %d subpath %d has no segment" % (gi, si))
            for op in sub:
                k = op[0]
                if k not in _ARGS or k in ("H", "V", "S", "Q", "T", "A"):
                    out.append("group %d subpath %d op %r" % (gi, si, k))
                    continue
                if len(op) - 1 != _ARGS[k]:
                    out.append("group %d subpath %d %s arity %d" % (gi, si, k, len(op) - 1))
                    continue
                for v in op[1:]:
                    if not (isinstance(v, (int, float)) and math.isfinite(v) and -2.0 <= v <= SPACE + 2.0):
                        out.append("group %d subpath %d %s value %r" % (gi, si, k, v))
    return out


def _pt(parent, x, y):
    etree.SubElement(parent, _A + "pt", x=str(int(round(x * SCALE))), y=str(int(round(y * SCALE))))


def custgeom(name_or_groups) -> etree._Element:
    """A complete <a:custGeom> for a glyph name (or a path-group list), in a 24000-unit path space."""
    groups = paths(name_or_groups) if isinstance(name_or_groups, str) else name_or_groups
    bad = validate_paths(groups)
    if bad:
        raise GeometryError("glyph path list", need="valid ops", have=bad[:3])
    g = etree.Element(_A + "custGeom", nsmap={"a": NS["a"]})
    for t in ("avLst", "gdLst", "ahLst", "cxnLst"):
        etree.SubElement(g, _A + t)
    etree.SubElement(g, _A + "rect", l="l", t="t", r="r", b="b")
    pl = etree.SubElement(g, _A + "pathLst")
    side = str(int(SPACE * SCALE))
    for grp in groups:
        p = etree.SubElement(pl, _A + "path", w=side, h=side)
        if not grp["fill"]:
            p.set("fill", "none")
        for sub in grp["d"]:
            for op in sub:
                k = op[0]
                if k == "M":
                    _pt(etree.SubElement(p, _A + "moveTo"), op[1], op[2])
                elif k == "L":
                    _pt(etree.SubElement(p, _A + "lnTo"), op[1], op[2])
                elif k == "C":
                    c = etree.SubElement(p, _A + "cubicBezTo")
                    _pt(c, op[1], op[2])
                    _pt(c, op[3], op[4])
                    _pt(c, op[5], op[6])
                elif k == "Z":
                    etree.SubElement(p, _A + "close")
    return g


def stroke_for(side_in: float) -> float:
    """Lucide's 2-on-24 stroke at this glyph side, in points (rounded to 0.05pt)."""
    return round(side_in * 72.0 * LUCIDE_STROKE / SPACE * 20) / 20.0


# ------------------------------------------------------------------ the creator

def glyph(slide, name: str, box: Box, role: str = "ink-strong", stroke_pt: float | None = None, *,
          shape_name: str | None = None, theme=None):
    """Place glyph `name` centred in `box` (square side = the box's shorter side), stroked in `role`.

    Unfilled, round caps and joins, line width 2/24 of the side unless stroke_pt is given. The shape is
    named shape_name or "glyph.<name>". Returns the python-pptx shape."""
    from pptx.enum.shapes import MSO_SHAPE
    from . import prims
    th = prims.theme_of(theme)
    key = resolve(name)
    groups = paths(key)
    side = min(box.w, box.h)
    if side < MIN_SIDE_IN:
        raise GeometryError("glyph %s" % key, need=MIN_SIDE_IN, have=round(side, 3), unit="in",
                            hint="a glyph this small reads as a smudge; give it at least 0.12in")
    sq = Box(box.cx - side / 2.0, box.cy - side / 2.0, side, side)
    w_pt = stroke_for(side) if stroke_pt is None else float(stroke_pt)
    if not (0.25 <= w_pt <= 12.0):
        raise GeometryError("glyph %s stroke" % key, need="0.25..12pt", have=w_pt, unit="pt")
    x, y, w, h = sq.emu
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    el = sh._element
    sp = el.spPr
    prst = sp.find(_A + "prstGeom")
    sp.replace(prst, custgeom(groups))
    if any(g["fill"] for g in groups):
        prims.set_fill(sh, role, theme=th)
    else:
        prims.set_fill(sh, None, theme=th)
    prims.set_line(sh, role, w_pt, theme=th, cap="rnd", join="round")
    tx = el.find(_P + "txBody")
    if tx is not None:
        el.remove(tx)
    sh.name = shape_name or ("glyph.%s" % key)
    ooxml.finish(sh)
    return sh


__all__ = ["glyph", "custgeom", "paths", "names", "aliases", "resolve", "validate_paths", "stroke_for",
           "parse_path", "arc_to_cubics", "node_subpaths", "icon_paths", "read_lucide", "UnknownGlyph",
           "GLYPHS_JSON", "SPACE", "SCALE"]
