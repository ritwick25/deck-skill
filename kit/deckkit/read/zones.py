"""Zones: containers first, then a recursive XY-cut, numbered Z1.. in reading order.

A filled or outlined rect-like leaf that contains at least 3 other leaves becomes one atomic item
(outermost container wins). Full-bleed leaves (>= 90% of the canvas) and chrome are excluded, as are
off-canvas leaves. Zones are the cut tree's leaves at depth <= 3.
"""
from __future__ import annotations

RECT_LIKE = {"rect", "roundRect", "snip1Rect", "snip2SameRect", "snip2DiagRect", "snipRoundRect",
             "round1Rect", "round2SameRect", "round2DiagRect", "flowChartProcess", "flowChartAlternateProcess",
             "plaque", "frame", "foldedCorner", "bevel"}
EPS_IN = 0.02
MIN_CONTAINED = 3


def contains(outer: dict, inner: dict, eps: float = EPS_IN) -> bool:
    a, b = outer["bbox"], inner["bbox"]
    return (b["x_in"] >= a["x_in"] - eps and b["y_in"] >= a["y_in"] - eps and
            b["x_in"] + b["w_in"] <= a["x_in"] + a["w_in"] + eps and
            b["y_in"] + b["h_in"] <= a["y_in"] + a["h_in"] + eps)


def is_rect_like(L: dict) -> bool:
    g = L.get("geom") or {}
    if L["kind"] not in ("sp",) or g.get("prst") not in RECT_LIKE:
        return False
    fill = (L.get("fill") or {}).get("type", "none")
    line = (L.get("line") or {}).get("type", "none")
    return fill != "none" or line != "none"


def xy_cut(items, depth=0, min_gap=0.15, max_depth=4):
    """items: (id, x0, y0, x1, y1) in inches. Largest clear gap wins; rows (y) tried before columns (x)."""
    if depth >= max_depth or len(items) <= 2:
        return {"items": items}
    best = None
    for ax in (1, 0):
        spans = sorted((it[1 + ax], it[3 + ax]) for it in items)
        reach = spans[0][1]
        for lo, hi in spans[1:]:
            if lo - reach >= min_gap and (best is None or lo - reach > best[0]):
                best = (lo - reach, ax, (lo + reach) / 2)
            reach = max(reach, hi)
    if best is None:
        return {"items": items}
    _, ax, cut = best
    return {"axis": "y" if ax else "x", "cut": cut,
            "children": [xy_cut([i for i in items if i[3 + ax] <= cut], depth + 1, min_gap, max_depth),
                         xy_cut([i for i in items if i[1 + ax] >= cut], depth + 1, min_gap, max_depth)]}


def _collect(node, depth, out, zone_depth=3):
    if "children" in node and depth < zone_depth:
        for c in node["children"]:
            _collect(c, depth + 1, out, zone_depth)
        return
    flat = []

    def walk(n):
        if "children" in n:
            for c in n["children"]:
                walk(c)
        else:
            flat.extend(n["items"])
    walk(node)
    if flat:
        out.append(flat)


def zones(leaves: list[dict], canvas_w: float, canvas_h: float) -> dict:
    """leaves: content leaf records (with bbox, kind, geom, fill, line, text). Returns zones and the cut tree."""
    area = canvas_w * canvas_h
    pool = []
    for L in leaves:
        b = L["bbox"]
        if L.get("on_canvas") == "off" or b["w_in"] * b["h_in"] >= 0.9 * area:
            continue
        if b["w_in"] <= 0 and b["h_in"] <= 0:
            continue
        pool.append(L)
    by_id = {L["id"]: L for L in pool}
    # containers, outermost first
    cands = []
    for L in pool:
        if not is_rect_like(L):
            continue
        inside = [M["id"] for M in pool if M is not L and M["z"] > L["z"] and contains(L, M)]
        if len(inside) >= MIN_CONTAINED:
            cands.append((L["bbox"]["w_in"] * L["bbox"]["h_in"], L["id"], inside))
    cands.sort(key=lambda t: -t[0])
    absorbed: dict = {}
    containers = {}
    for _a, cid, inside in cands:
        if cid in absorbed:
            continue
        members = [i for i in inside if i not in absorbed and i not in containers]
        containers[cid] = members
        for i in members:
            absorbed[i] = cid
    items = []
    for L in pool:
        if L["id"] in absorbed:
            continue
        b = L["bbox"]
        items.append((L["id"], b["x_in"], b["y_in"], b["x_in"] + b["w_in"], b["y_in"] + b["h_in"]))
    tree = xy_cut(items)
    groups: list[list] = []
    _collect(tree, 0, groups)
    out = []
    for n, its in enumerate(groups, 1):
        ids = []
        for it in its:
            ids.append(it[0])
            ids.extend(containers.get(it[0], []))
        x0 = min(i[1] for i in its)
        y0 = min(i[2] for i in its)
        x1 = max(i[3] for i in its)
        y1 = max(i[4] for i in its)
        kinds: dict = {}
        wds = 0
        for i in ids:
            L = by_id[i]
            kinds[L["kind"]] = kinds.get(L["kind"], 0) + 1
            wds += (L.get("text") or {}).get("words", 0) if L.get("text") else 0
        out.append({"id": "Z%d" % n,
                    "box_in": [round(x0, 3), round(y0, 3), round(x1 - x0, 3), round(y1 - y0, 3)],
                    "box_pct": [round(100 * x0 / canvas_w, 2), round(100 * y0 / canvas_h, 2),
                                round(100 * (x1 - x0) / canvas_w, 2), round(100 * (y1 - y0) / canvas_h, 2)],
                    "n": len(ids), "words": wds, "kinds": kinds,
                    "container": [i[0] for i in its if i[0] in containers], "ids": ids})
    return {"zones": out, "containers": containers}


def slide_zones(slide: dict) -> dict:
    """Zones for a read_slide() dict's content leaves."""
    return zones(slide["shapes"], slide["canvas"]["w_in"], slide["canvas"]["h_in"])
