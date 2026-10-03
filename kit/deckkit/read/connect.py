"""Connector and line-like endpoints, glue, arrow contact and line classes.

Endpoints come from leaf_geometry start/end (the path's first and last points with flips and
rotation applied). touch() uses the same tolerance as the house arrow gate.

Every cxnSp, line-like leaf and open custGeom path (stroked, unfilled: walk's _open_path, ends at the path's first
and last points) gets one class (classify):
  degenerate  shorter than 0.05 in;
  stroke      part of an icon unit, a legend sample (inside a legend container), shorter than 0.15 in, or an open
              path without an arrowhead that loops back (its ends closer than 25% of its drawn length: a ring or
              swirl drawn as one stroke, not a line between two places);
  connector   0.15 in or longer and an arrowhead (a block arrow counts), glue at an end, or each end within
              0.09 in of the EDGE of a distinct shape, neither shape containing the other and neither
              containing the whole line, unless the line is a divider drawn across a shape that holds it
              with both ends on its outline (contact);
  rule        everything else: a separator with no arrowhead, no glue, not touching two distinct shapes.
"""
from __future__ import annotations

import math
import re

from .ns import A, P

ARROW_TOL_IN = 0.09
CONNECTOR_MIN_IN = 0.15     # shorter lines are strokes
DEGENERATE_IN = 0.05        # shorter lines are degenerate
HOLD_EPS_IN = 0.01          # an end this close to an outline counts as on it (inside, for holding the line)
LEGEND_MAX_AREA = 0.25      # a legend container covers less than this share of the canvas
LEGEND_LABEL_WORDS = 6      # a legend label is this many words or fewer
LEGEND_GAP_IN = 0.35        # ... and starts within this of its sample's end
LEGEND_SAMPLE_MAX_IN = 1.2  # a legend sample is a horizontal line no longer than this
LOOP_CHORD = 0.25           # an open path whose ends are closer than this share of its length loops back
LEGEND_RX = re.compile(r"(?i)\blegend\b|^\s*key\s*:?\s*$")

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


def touch(pt, leaves, self_id, canvas_area: float | None = None, other=None) -> dict:
    """The shape an arrow end lands on: {"id", "gap_in", "inside", "ok"}.

    Candidates are drawing, on-canvas leaves (connectors, other lines, full-bleed shapes and shapes that draw
    nothing skipped). With `other` (the connector's opposite end), a shape that holds the whole connector (both
    ends inside it or on its outline) is never a target: an enclosing panel is where the arrow is drawn, not what
    it points at. Candidates are ranked by the distance from pt to their EDGE (outline), the smaller shape first
    on a tie. ok: the end lies within ARROW_TOL_IN of that edge, or inside that shape (an arrowhead drawn onto
    its target). inside: pt lies within the target's outline. Without `other` nothing is excluded for holding
    the line and every candidate is still ranked by its edge.
    """
    best = None
    for L in leaves:
        if L["id"] == self_id or L["kind"] == "cxn" or L.get("line_like") or L.get("on_canvas") == "off":
            continue
        area = L["bbox"]["w_in"] * L["bbox"]["h_in"]
        if canvas_area and area >= 0.9 * canvas_area:
            continue
        if not _draws(L):
            continue
        poly = L["corners_in"]
        g = edge_gap(pt, L)
        if other is not None and _holds(poly, pt, g) and _holds(poly, other, edge_gap(other, L)):
            continue                                    # the shape holds the whole connector
        key = (g, area)
        if best is None or key < best[0]:
            best = (key, L)
    if best is None:
        return {"id": None, "gap_in": None, "inside": False, "ok": False}
    (g, _a), L = best
    inside = gap(pt, L) == 0.0
    return {"id": L["id"], "gap_in": round(g, 3), "inside": inside, "ok": g <= ARROW_TOL_IN or inside}


def connector_block(prst: str, start, end, line: dict, glue_: dict | None, orient: str | None = None) -> dict:
    """The connector block of a cxnSp, a line-like preset, a block arrow or an open custGeom path (prst
    "custom"; orient "curve" or "elbow" when the path is not straight, else measured from the ends)."""
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    return {"prst": prst, "start_in": [round(start[0], 3), round(start[1], 3)],
            "end_in": [round(end[0], 3), round(end[1], 3)], "length_in": round(length, 3),
            "orientation": orient or orientation(prst, start, end), "glue": glue_ or {"start": None, "end": None},
            "touch": None, "head": (line or {}).get("head", {"type": "none"}),
            "tail": (line or {}).get("tail", {"type": "none"}), "dash": (line or {}).get("dash"),
            "w_pt": (line or {}).get("w_pt"), "hex": (line or {}).get("hex")}


# ------------------------------------------------------------------ edge contact and line classes

def edge_gap(pt, leaf) -> float:
    """Distance from pt to the outline of leaf (inside or outside); ellipses by their inscribed ellipse."""
    corners = leaf["corners_in"]
    prst = (leaf.get("geom") or {}).get("prst")
    if prst in ("ellipse", "flowChartConnector"):
        (x0, y0), (x1, y1), _, (x3, y3) = corners
        cx = (corners[0][0] + corners[2][0]) / 2.0
        cy = (corners[0][1] + corners[2][1]) / 2.0
        ux, uy, vx, vy = x1 - x0, y1 - y0, x3 - x0, y3 - y0
        a, b = math.hypot(ux, uy) / 2.0, math.hypot(vx, vy) / 2.0
        if a > 0 and b > 0:
            dx, dy = pt[0] - cx, pt[1] - cy
            lu = (dx * ux + dy * uy) / (2 * a)
            lv = (dx * vx + dy * vy) / (2 * b)
            r = math.hypot(lu / a, lv / b)
            if r == 0:
                return min(a, b)
            return math.hypot(lu, lv) * abs(1 - 1 / r)
    return dist_to_poly(pt, corners)


def _bbox_t(L):
    b = L["bbox"]
    return (b["x_in"], b["y_in"], b["x_in"] + b["w_in"], b["y_in"] + b["h_in"])


def _box_in(inner, outer, eps=0.02) -> bool:
    return (inner[0] >= outer[0] - eps and inner[1] >= outer[1] - eps and inner[2] <= outer[2] + eps
            and inner[3] <= outer[3] + eps)


def _draws(L) -> bool:
    """A leaf a line could land on: it has words, is a picture, table cell or graphic, or shows a fill or outline."""
    if L["kind"] in ("pic", "cell", "graphic"):
        return True
    t = L.get("text")
    if t and (t.get("words") or 0) > 0:
        return True
    f = (L.get("fill") or {}).get("type") or "none"
    ln = (L.get("line") or {}).get("type") or "none"
    return f != "none" or ln != "none" or bool(L.get("grad"))


def _holds(poly, pt, gap) -> bool:
    """pt lies inside poly or on its outline (within HOLD_EPS_IN)."""
    return (gap is not None and gap <= HOLD_EPS_IN) or point_in_poly(pt, poly)


def contact(start, end, leaves, self_id, canvas_area: float | None = None, straight: bool = True,
            tol: float = ARROW_TOL_IN) -> dict:
    """Edge contact at both ends: {"start": {"id", "gap_in"} | None, "end": ..., "distinct": bool, "across": id}.

    A target is a drawing, on-canvas leaf (connectors, other lines and full-bleed shapes skipped) whose outline
    lies within tol of the end and which does not hold the whole line (both ends inside it). For a straight
    line, a shape whose outline also passes within tol of the line's midpoint is a rail the line runs along,
    not a target. distinct: the two ends land on two different shapes, neither box containing the other.
    across: the smallest drawn shape holding the whole line with both ends on its outline (a divider drawn
    across a band or card, such as a timeline's week ticks), else None."""
    mid = ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0)
    near = {"start": [], "end": []}
    across = None
    for L in leaves:
        if L["id"] == self_id or L["kind"] == "cxn" or L.get("line_like") or L.get("on_canvas") == "off":
            continue
        bx = _bbox_t(L)
        area = (bx[2] - bx[0]) * (bx[3] - bx[1])
        if canvas_area and area >= 0.9 * canvas_area:
            continue
        hits = {}
        for key, pt in (("start", start), ("end", end)):
            if bx[0] - tol <= pt[0] <= bx[2] + tol and bx[1] - tol <= pt[1] <= bx[3] + tol:
                g = edge_gap(pt, L)
                if g <= tol:
                    hits[key] = g
        if not hits or not _draws(L):
            continue
        poly = L["corners_in"]
        if _holds(poly, start, hits.get("start")) and _holds(poly, end, hits.get("end")):
            if len(hits) == 2 and (across is None or area < across[0]):
                across = (area, L["id"])                # both ends on its outline: a divider across it
            continue                                    # the shape holds the whole line
        if straight and edge_gap(mid, L) <= tol:
            continue                                    # a rail: the line runs along this outline
        for key, g in hits.items():
            near[key].append((g, area, L["id"], bx))
    out = {"start": None, "end": None, "distinct": False, "across": across[1] if across else None}
    for key in ("start", "end"):
        if near[key]:
            g, _a, lid, _b = min(near[key])
            out[key] = {"id": lid, "gap_in": round(g, 3)}
    best = None
    for gs, _as, ids, bs in near["start"]:
        for ge, _ae, ide, be in near["end"]:
            if ids == ide or _box_in(bs, be) or _box_in(be, bs):
                continue
            if best is None or gs + ge < best[0]:
                best = (gs + ge, (ids, gs), (ide, ge))
    if best is not None:
        out["start"] = {"id": best[1][0], "gap_in": round(best[1][1], 3)}
        out["end"] = {"id": best[2][0], "gap_in": round(best[2][1], 3)}
        out["distinct"] = True
    return out


def legend_lines(leaves: list[dict], canvas_area: float) -> set:
    """Ids of line-like leaves inside a legend container: a drawn rect-like box under LEGEND_MAX_AREA of the
    canvas that holds a text reading "Legend" (or "Key") and a sample pair, or two or more sample pairs making up
    60% of its text leaves. A sample pair is a horizontal line of 1.2 in or less with a label of six words or fewer
    starting within 0.35 in of its end, on its line. Lines in it are samples, not connectors."""
    from .zones import is_rect_like
    lines = [L for L in leaves if L.get("connector") is not None]
    if not lines:
        return set()
    texts = [L for L in leaves if L.get("text") and (L["text"].get("words") or 0) > 0]
    out: set = set()
    for C in leaves:
        if not is_rect_like(C):
            continue
        cb = _bbox_t(C)
        if (cb[2] - cb[0]) * (cb[3] - cb[1]) >= LEGEND_MAX_AREA * canvas_area:
            continue
        inside = [L for L in lines if L["id"] != C["id"] and _box_in(_bbox_t(L), cb)]
        if not inside:
            continue
        tin = [T for T in texts if T["id"] != C["id"] and _box_in(_bbox_t(T), cb)]
        own = C.get("text") and LEGEND_RX.search(C["text"].get("text") or "")
        heading = own or any(LEGEND_RX.search(T["text"]["text"]) for T in tin)
        labels = set()
        for L in inside:
            k = L["connector"]
            if k["orientation"] != "h" or (k.get("length_in") or 0.0) > LEGEND_SAMPLE_MAX_IN:
                continue                         # a sample is a short horizontal line
            xs = sorted((k["start_in"][0], k["end_in"][0]))
            y = (k["start_in"][1] + k["end_in"][1]) / 2.0
            for T in tin:
                if T["text"]["words"] > LEGEND_LABEL_WORDS:
                    continue
                tb = _bbox_t(T)
                if not (tb[1] - 0.05 <= y <= tb[3] + 0.05):
                    continue
                if -0.05 <= tb[0] - xs[1] <= LEGEND_GAP_IN or -0.05 <= xs[0] - tb[2] <= LEGEND_GAP_IN:
                    labels.add(T["id"])
        pairs = len(labels)
        if (heading and pairs >= 1) or (pairs >= 2 and pairs >= 0.6 * len(tin)):
            out.update(L["id"] for L in inside)
    return out


def classify(L: dict, legend: set | frozenset = frozenset()) -> str:
    """degenerate | stroke | connector | rule for a leaf carrying a connector block (with contact filled).
    An open path is measured by its chord (length_in) like any line; one whose drawn length (path_len_in) is
    longer than the degenerate threshold is not degenerate, and a loop without an arrowhead is a stroke."""
    k = L["connector"]
    n = k.get("length_in") or 0.0
    plen = k.get("path_len_in")
    if n < DEGENERATE_IN and (plen is None or plen < DEGENERATE_IN):
        return "degenerate"
    if L.get("icon_group") is not None or L.get("icon_like") or L["id"] in legend or n < CONNECTOR_MIN_IN:
        return "stroke"
    head = ((k.get("head") or {}).get("type") or "none") != "none" or \
        ((k.get("tail") or {}).get("type") or "none") != "none" or k.get("prst") in BLOCK_ARROWS
    if not head and plen and n < LOOP_CHORD * plen:
        return "stroke"
    g = k.get("glue") or {}
    ct = k.get("contact") or {}
    if head or g.get("start") or g.get("end") or (ct.get("distinct") and ct.get("across") is None):
        return "connector"
    return "rule"
