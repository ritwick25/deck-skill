"""Connector and line-like endpoints, glue and arrow contact.

Endpoints come from leaf_geometry start/end (the path's first and last points with flips and
rotation applied). touch() uses the same tolerance as the house arrow gate.
"""
from __future__ import annotations

import math

from .ns import A, P

ARROW_TOL_IN = 0.09

# block arrows: (start (u, v), end (u, v)) as fractions of the shape's own box, before flip/rotation
BLOCK_ARROWS = {
    "rightArrow": ((0.0, 0.5), (1.0, 0.5)), "notchedRightArrow": ((0.0, 0.5), (1.0, 0.5)),
    "stripedRightArrow": ((0.0, 0.5), (1.0, 0.5)), "leftArrow": ((1.0, 0.5), (0.0, 0.5)),
    "upArrow": ((0.5, 1.0), (0.5, 0.0)), "downArrow": ((0.5, 0.0), (0.5, 1.0)),
    "leftRightArrow": ((0.0, 0.5), (1.0, 0.5)), "upDownArrow": ((0.5, 0.0), (0.5, 1.0)),
}
LINE_PRESETS = ("line", "straightConnector1", "bentConnector2", "bentConnector3", "bentConnector4",
                "bentConnector5", "curvedConnector2", "curvedConnector3", "curvedConnector4",
                "curvedConnector5")


def glue(cxn) -> dict:
    """stCxn/endCxn of a p:cxnSp as {'start': {'id', 'idx'} | None, 'end': ...}."""
    out = {"start": None, "end": None}
    nv = cxn.find(P("nvCxnSpPr"))
    c = nv.find(P("cNvCxnSpPr")) if nv is not None else None
    if c is None:
        return out
    for key, tag in (("start", "stCxn"), ("end", "endCxn")):
        e = c.find(A(tag))
        if e is not None:
            out[key] = {"id": int(e.get("id", "0")), "idx": int(e.get("idx", "0"))}
    return out


def orientation(prst: str, s, e) -> str:
    if prst.startswith("bent"):
        return "elbow"
    if prst.startswith("curved"):
        return "curve"
    dx, dy = abs(e[0] - s[0]), abs(e[1] - s[1])
    if dy <= 0.02 or (dx > 0 and dy / dx < 0.035):
        return "h"
    if dx <= 0.02 or (dy > 0 and dx / dy < 0.035):
        return "v"
    return "diag"


def _seg_dist(p, a, b) -> float:
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def point_in_poly(p, poly) -> bool:
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xin = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xin:
                inside = not inside
    return inside


def dist_to_poly(p, poly) -> float:
    return min(_seg_dist(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def _ellipse_gap(p, corners) -> float:
    """Approximate distance from p to the ellipse inscribed in a (possibly rotated) box; 0 inside."""
    (x0, y0), (x1, y1), _, (x3, y3) = corners
    cx = (corners[0][0] + corners[2][0]) / 2.0
    cy = (corners[0][1] + corners[2][1]) / 2.0
    ux, uy = x1 - x0, y1 - y0
    vx, vy = x3 - x0, y3 - y0
    a = math.hypot(ux, uy) / 2.0
    b = math.hypot(vx, vy) / 2.0
    if a <= 0 or b <= 0:
        return dist_to_poly(p, corners)
    dx, dy = p[0] - cx, p[1] - cy
    lu = (dx * ux + dy * uy) / (2 * a)
    lv = (dx * vx + dy * vy) / (2 * b)
    r = math.hypot(lu / a, lv / b)
    if r <= 1.0:
        return 0.0
    # distance along the ray from the centre to the ellipse boundary
    return math.hypot(lu, lv) * (1 - 1 / r)


def gap(pt, leaf) -> float:
    corners = leaf["corners_in"]
    prst = (leaf.get("geom") or {}).get("prst")
    if prst in ("ellipse", "flowChartConnector"):
        return _ellipse_gap(pt, corners)
    return 0.0 if point_in_poly(pt, corners) else dist_to_poly(pt, corners)


def touch(pt, leaves, self_id, canvas_area: float | None = None) -> dict:
    """Nearest non-connector, non-line, on-canvas leaf to an endpoint; ok within ARROW_TOL_IN.

    Full-bleed leaves (90% of the canvas or more) are skipped: every point lies inside them.
    """
    best_id, best = None, (float("inf"), float("inf"))
    for L in leaves:
        if L["id"] == self_id or L["kind"] == "cxn" or L.get("line_like") or L.get("on_canvas") == "off":
            continue
        area = L["bbox"]["w_in"] * L["bbox"]["h_in"]
        if canvas_area and area >= 0.9 * canvas_area:
            continue
        key = (gap(pt, L), area)        # inside several shapes: the smallest one is the target
        if key < best:
            best_id, best = L["id"], key
    best = best[0]
    if best_id is None:
        return {"id": None, "gap_in": None, "ok": False}
    return {"id": best_id, "gap_in": round(best, 3), "ok": best <= ARROW_TOL_IN}


def connector_block(prst: str, start, end, line: dict, glue_: dict | None) -> dict:
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    return {"prst": prst, "start_in": [round(start[0], 3), round(start[1], 3)],
            "end_in": [round(end[0], 3), round(end[1], 3)], "length_in": round(length, 3),
            "orientation": orientation(prst, start, end), "glue": glue_ or {"start": None, "end": None},
            "touch": None, "head": (line or {}).get("head", {"type": "none"}),
            "tail": (line or {}).get("tail", {"type": "none"}), "dash": (line or {}).get("dash"),
            "w_pt": (line or {}).get("w_pt"), "hex": (line or {}).get("hex")}
