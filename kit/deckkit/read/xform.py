"""Affine geometry for shapes and groups.

A transform is a 6-tuple (a, b, c, d, e, f): x' = a x + c y + e, y' = b x + d y + f, y pointing down.
Rotation follows OOXML: positive is clockwise on screen, stored in 1/60000 degree.
Groups map chOff/chExt onto off/ext with independent x and y scale, then apply their own flip and
rotation about the group centre, so non-uniform scale under a rotated parent produces shear in the
composed matrix; leaf_geometry reports it.
"""
from __future__ import annotations

import math

from .ns import A, is_true

EMU_IN = 914400.0
EMU_PT = 12700.0

Affine = tuple[float, float, float, float, float, float]
IDENT: Affine = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def mul(A_: Affine, B: Affine) -> Affine:
    """A after B."""
    a1, b1, c1, d1, e1, f1 = A_
    a2, b2, c2, d2, e2, f2 = B
    return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2, a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


def T(x: float, y: float) -> Affine:
    return (1.0, 0.0, 0.0, 1.0, float(x), float(y))


def S(sx: float, sy: float) -> Affine:
    return (float(sx), 0.0, 0.0, float(sy), 0.0, 0.0)


def R(deg: float) -> Affine:
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    return (c, s, -s, c, 0.0, 0.0)


def ap(M: Affine, x: float, y: float) -> tuple[float, float]:
    a, b, c, d, e, f = M
    return (a * x + c * y + e, b * x + d * y + f)


def inv(M: Affine) -> Affine | None:
    a, b, c, d, e, f = M
    det = a * d - b * c
    if abs(det) < 1e-18:
        return None
    ia, ib, ic, id_ = d / det, -b / det, -c / det, a / det
    return (ia, ib, ic, id_, -(ia * e + ic * f), -(ib * e + id_ * f))


def read_xfrm(x) -> dict | None:
    """a:xfrm or p:xfrm element to a raw dict in EMU. None when off or ext is missing."""
    if x is None:
        return None
    off, ext = x.find(A("off")), x.find(A("ext"))
    if off is None or ext is None:
        return None
    r = dict(x=int(off.get("x", "0")), y=int(off.get("y", "0")),
             w=int(ext.get("cx", "0")), h=int(ext.get("cy", "0")),
             rot=int(x.get("rot", "0")) / 60000.0,
             fh=is_true(x.get("flipH")), fv=is_true(x.get("flipV")))
    co, ce = x.find(A("chOff")), x.find(A("chExt"))
    if co is not None and ce is not None:
        r.update(chx=int(co.get("x", "0")), chy=int(co.get("y", "0")),
                 chw=int(ce.get("cx", "0")), chh=int(ce.get("cy", "0")))
    return r


def _about_centre(r: dict, inner: Affine) -> Affine:
    cx, cy = r["x"] + r["w"] / 2.0, r["y"] + r["h"] / 2.0
    return mul(T(cx, cy), mul(inner, T(-cx, -cy)))


def rot_only(r: dict) -> Affine:
    return _about_centre(r, R(r["rot"]))


def own(r: dict) -> Affine:
    """Flip, then rotate, about the shape centre."""
    return _about_centre(r, mul(R(r["rot"]), S(-1.0 if r["fh"] else 1.0, -1.0 if r["fv"] else 1.0)))


def group_scale_own(r: dict) -> tuple[float, float]:
    sx = r["w"] / r["chw"] if r.get("chw") else 1.0
    sy = r["h"] / r["chh"] if r.get("chh") else 1.0
    return sx, sy


def group_child_to_parent(r: dict) -> Affine:
    """grpSp: map chOff/chExt onto off/ext (non-uniform scale allowed), then the group's own flip and rotation."""
    sx, sy = group_scale_own(r)
    fit = mul(T(r["x"], r["y"]), mul(S(sx, sy), T(-r.get("chx", r["x"]), -r.get("chy", r["y"]))))
    return mul(own(r), fit)


def leaf_geometry(r: dict, P: Affine) -> dict:
    """P maps parent space to slide space (the product of ancestor group_child_to_parent)."""
    Mr, Mf = mul(P, rot_only(r)), mul(P, own(r))
    x, y, w, h = r["x"], r["y"], r["w"], r["h"]
    pts = [ap(Mr, px, py) for px, py in ((x, y), (x + w, y), (x + w, y + h), (x, y + h))]
    a, b, c, d, _, _ = Mr
    nu, nv = math.hypot(a, b), math.hypot(c, d)
    shear = bool(nu and nv) and abs(a * c + b * d) / (nu * nv) > 1e-3
    ccx, ccy = ap(Mr, x + w / 2.0, y + h / 2.0)
    fa, fb, fc, fd, _, _ = Mf
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return dict(
        frame=dict(cx_in=ccx / EMU_IN, cy_in=ccy / EMU_IN, w_in=w * nu / EMU_IN, h_in=h * nv / EMU_IN,
                   rot_deg=round(math.degrees(math.atan2(b, a)) % 360.0, 2),
                   mirrored=(fa * fd - fb * fc) < 0, sheared=bool(shear)),
        corners_in=[(px / EMU_IN, py / EMU_IN) for px, py in pts],
        bbox_in=(min(xs) / EMU_IN, min(ys) / EMU_IN, (max(xs) - min(xs)) / EMU_IN, (max(ys) - min(ys)) / EMU_IN),
        start_in=tuple(v / EMU_IN for v in ap(Mf, x, y)),      # path start, headEnd
        end_in=tuple(v / EMU_IN for v in ap(Mf, x + w, y + h)),  # path end, tailEnd
        group_scale=(round(math.hypot(P[0], P[1]), 4), round(math.hypot(P[2], P[3]), 4)),
        M_rot=Mr, M_full=Mf)


def local_point(r: dict, P: Affine, u: float, v: float) -> tuple[float, float]:
    """A point given as fractions (u, v) of the shape's own box, in slide inches, flips and rotation applied."""
    Mf = mul(P, own(r))
    px, py = ap(Mf, r["x"] + u * r["w"], r["y"] + v * r["h"])
    return (px / EMU_IN, py / EMU_IN)
