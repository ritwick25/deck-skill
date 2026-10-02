"""Zones: the regions a person sees on a slide, as a flat list carrying a tree.

1. Pool. Content leaves only (chrome never); fully off-canvas leaves and text-free shapes that draw nothing
   are dropped; every box is clipped to the canvas. An unboxed text frame counts only the height its lines
   fill (walk's occupancy, placed by anchor), and is trimmed back to the edge of a drawn box it runs into.
2. Atoms. An outermost group is one atom unless it covers 40%+ of the canvas or holds 25+ leaves; then its
   children are taken one level down (recursively). Icon groups are always atoms; a table's cells are one
   atom. Links never block a cut and join the deepest zone holding their centre: connectors, line-like
   shapes, text-free bars 15x longer than thick (edge stripes, underlines), and backdrops (a text-free,
   non-box shape covering 15%+ of the canvas with 3+ atoms painted over it).
3. Containers. A rect-like atom (rect family preset, a custGeom whose path is a plain rectangle, or a group
   sitting on such a rect) with a visible fill or outline that holds 2+ other atoms: centre inside and 80%
   of the area inside, or a tab or badge across one edge (30% inside, span within the edge); above an
   opaque fill in paint order. Each atom belongs to the smallest container that holds it. A shape covering
   85%+ of the canvas is a background, not a zone.
4. Tree. The top level (containers and loose atoms) is cut by an n-ary XY-cut: a gap of 0.10 in at 13.333 in
   (scaled by canvas width) cuts; between two drawn boxes any visible gap cuts; when only one side is drawn
   boxes a touch or a 0.03 in overlap cuts; a rule lying in a gap marks it. Rows whose column gutters line
   up and are marked by rules, or are wider than the row gap, are read as columns. When no straight cut
   exists, small unboxed labels are set aside and the cut retried, then items closer than the gap are
   clustered. Every container with 3+ children is cut the same way inside. Runs of tiny parts (< 1% of the
   canvas) join their nearest neighbour. A cut or group node that is not a drawn box and holds 85%+ of its
   parent's leaves is transparent: its parts move up a level.
5. Output. Flat Z1..Zn in reading order (row bands by top, then left, parents first), each with parent,
   depth, box_in and box_pct (clipped), ids (every member leaf, descendants included), n, words, kinds,
   container (the box's leaf id or None) and full_bleed. A picture covering 85%+ of the canvas is its own
   depth-1 zone (full_bleed at 90%+). At most 24 zones: depth 1, then depth 2, then the largest.

API: zones(slide_read) -> list. Legacy forms kept: zones(leaves, canvas_w, canvas_h) -> {"zones", "containers"}
(groups from each leaf's group_path, icon groups from icon_group) and slide_zones(slide) -> {"zones",
"containers"}. contains() and is_rect_like() serve walk.mark_containers unchanged.
"""
from __future__ import annotations

RECT_LIKE = {"rect", "roundRect", "snip1Rect", "snip2SameRect", "snip2DiagRect", "snipRoundRect", "snipRect",
             "round1Rect", "round2SameRect", "round2DiagRect", "flowChartProcess", "flowChartAlternateProcess",
             "plaque", "frame", "foldedCorner", "bevel"}
EPS_IN = 0.02
MIN_CONTAINED = 3          # walk.mark_containers' legacy threshold (container_of); zones use CONTAINER_MIN

REF_W_IN = 13.333          # gaps and tolerances are stated at this canvas width and scaled
GAP_IN = 0.10              # a clear gap this wide always cuts
BOXED_GAP_IN = 0.015       # between two drawn boxes any visible gap cuts
OVERLAP_IN = 0.03          # when one side of the gap is all drawn boxes, a touch or a slight overlap cuts
STRADDLE_AREA = 0.30       # a tab or badge on a container's edge: this share inside, span within the edge
BAND_TOL_IN = 0.15         # reading order: tops within this share a row band
LINE_THIN_IN = 0.03        # a rule line is at most this thick
BAR_THIN_IN = 0.15         # a text-free bar at most this thick and RULE_ASPECT long is a rule, not a box
RULE_ASPECT = 15
GROUP_AREA = 0.40          # a group covering this share of the canvas is descended
GROUP_LEAVES = 25          # ... or holding this many leaves
CONTAIN_AREA = 0.80        # share of an atom's area that must sit inside its container
CONTAINER_MIN = 2          # atoms a container must hold
BASE_COVER = 0.90          # a group is box-based when its lowest rect covers this share of it
BACKGROUND = 0.85          # rect at or above this share of the canvas is a background
FULL_BLEED = 0.90          # picture at or above this share is full_bleed
PIC_ZONE = 0.85            # picture at or above this share is its own zone
TINY = 0.01                # parts below this share of the canvas join a neighbour
DOMINANT = 0.85            # a plain cut node holding this share of its parent's leaves is transparent
RECURSE_MIN = 3            # a container is cut inside when it has this many children
MAX_ZONES = 24
BACKDROP = 0.15            # a text-free non-box shape this big with 3+ atoms over it is a backdrop
BACKDROP_OVER = 3
INK_PAD = 1.05             # text ink height is the walk's occupancy estimate plus this margin
SEP_COVER = 0.50           # a rule must span this share of the band to mark a gutter


# ------------------------------------------------------------------ legacy helpers (walk imports these)

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


# ------------------------------------------------------------------ boxes

def _area(b) -> float:
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def _union(boxes):
    boxes = list(boxes)
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def _inter(a, b) -> float:
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def _clip(L, cw, ch):
    b = L["bbox"]
    x0, y0 = b["x_in"], b["y_in"]
    x1, y1 = x0 + b["w_in"], y0 + b["h_in"]
    x0, x1 = max(0.0, min(cw, x0)), max(0.0, min(cw, x1))
    y0, y1 = max(0.0, min(ch, y0)), max(0.0, min(ch, y1))
    return (x0, y0, x1, y1)


def _centre_in(inner, outer, eps) -> bool:
    cx, cy = (inner[0] + inner[2]) / 2, (inner[1] + inner[3]) / 2
    return outer[0] - eps <= cx <= outer[2] + eps and outer[1] - eps <= cy <= outer[3] + eps


# ------------------------------------------------------------------ leaf tests

def _alpha(d) -> float:
    a = d.get("alpha")
    return 1.0 if a is None else float(a)


def _fill_visible(L, bg_hex) -> bool:
    if L.get("grad"):
        return True
    f = L.get("fill") or {}
    t = f.get("type") or "none"
    if t == "none" or (t == "grp" and not f.get("hex")):
        return False
    if _alpha(f) < 0.05:
        return False
    if t == "solid" and bg_hex and (f.get("hex") or "").upper() == bg_hex.upper():
        return False
    return True


def _line_visible(L) -> bool:
    ln = L.get("line") or {}
    if (ln.get("type") or "none") == "none" or _alpha(ln) < 0.05:
        return False
    w = ln.get("w_pt")
    return (0.75 if w is None else w) > 0


def _rect_geom(L) -> bool:
    if L.get("kind") != "sp" or L.get("line_like"):
        return False
    g = L.get("geom") or {}
    if g.get("prst") in RECT_LIKE:
        return True
    return bool(g.get("cust")) and bool(g.get("rect_path"))


def _is_link(L, bar_in: float = BAR_THIN_IN) -> bool:
    """Connectors, line-like shapes and text-free rule bars (an edge stripe, an underline) link or divide
    regions; they never make one."""
    if L.get("kind") == "cxn" or L.get("line_like"):
        return True
    if L.get("kind") not in ("sp", "pic") or _words(L):
        return False
    w, h = L["bbox"]["w_in"], L["bbox"]["h_in"]
    lo, hi = min(w, h), max(w, h)
    return lo <= bar_in and hi >= RULE_ASPECT * max(lo, 1e-3)


def _words(L) -> int:
    t = L.get("text")
    return int(t.get("words") or 0) if t else 0


# ------------------------------------------------------------------ atoms

class _Atom:
    __slots__ = ("key", "leaves", "box", "zmin", "zmax", "kind", "base", "opaque", "link", "container",
                 "children", "parent", "area")

    def __init__(self, key, leaves, box, kind):
        self.key, self.leaves, self.box, self.kind = key, leaves, box, kind
        self.zmin = self.zmax = 0
        self.base = None          # leaf id of the drawn box this atom is (or sits on)
        self.opaque = False
        self.link = False
        self.container = False
        self.children: list = []
        self.parent = None
        self.area = _area(box)

    def boxed(self) -> bool:
        return self.base is not None or self.kind in ("table", "pic")


class _Ctx:
    def __init__(self, cw, ch, bg_hex):
        self.cw, self.ch, self.bg = cw, ch, bg_hex
        self.A = cw * ch
        k = cw / REF_W_IN if cw else 1.0
        self.gap, self.boxed_gap, self.band = GAP_IN * k, BOXED_GAP_IN * k, BAND_TOL_IN * k
        self.overlap = OVERLAP_IN * k
        self.thin = LINE_THIN_IN * k
        self.bar = BAR_THIN_IN * k
        self.eps = EPS_IN * k
        self.by_id: dict = {}
        self.box: dict = {}


def _atom_of_leaves(ctx, key, ids, kind):
    a = _Atom(key, list(ids), _union(ctx.box[i] for i in ids), kind)
    zs = [ctx.by_id[i].get("z", 0) for i in ids]
    a.zmin, a.zmax = min(zs), max(zs)
    return a


def _set_base(ctx, a, lid):
    L = ctx.by_id[lid]
    fv, lv = _fill_visible(L, ctx.bg), _line_visible(L)
    if fv or lv:
        a.base = lid
        a.opaque = fv and _alpha(L.get("fill") or {}) >= 0.5


def _mark_base(ctx, a: _Atom):
    """A single rect-like visible leaf is its own base; a group sits on its lowest rect when it covers it."""
    if a.kind == "leaf":
        if _rect_geom(ctx.by_id[a.leaves[0]]):
            _set_base(ctx, a, a.leaves[0])
    elif a.kind == "group":
        low = min(a.leaves, key=lambda i: ctx.by_id[i].get("z", 0))
        if _rect_geom(ctx.by_id[low]) and _area(ctx.box[low]) >= BASE_COVER * a.area > 0:
            _set_base(ctx, a, low)


def _atoms(ctx, pool, icon_groups):
    """Outermost groups as atoms, descending into big ones; tables merged; links set apart."""
    sub: dict = {}            # gid (0 = slide) -> child gids
    direct: dict = {}         # gid (0 = slide) -> leaf ids directly inside
    under: dict = {}          # gid -> every leaf id under it
    order: dict = {}          # gid -> first z seen
    for L in pool:
        gp = list(L.get("group_path") or [])
        direct.setdefault(gp[-1] if gp else 0, []).append(L["id"])
        for i, g in enumerate(gp):
            under.setdefault(g, []).append(L["id"])
            order.setdefault(g, L.get("z", 0))
            sub.setdefault(gp[i - 1] if i else 0, set()).add(g)
    atoms: list = []

    def take(gid):
        for lid in direct.get(gid, []):
            L = ctx.by_id[lid]
            a = _atom_of_leaves(ctx, "L%d" % lid, [lid], "pic" if L["kind"] == "pic" else "leaf")
            a.link = _is_link(L, ctx.bar)
            atoms.append(a)
        for g in sorted(sub.get(gid, ()), key=lambda g: order.get(g, 0)):
            ids = under[g]
            box = _union(ctx.box[i] for i in ids)
            if g in icon_groups or not (_area(box) >= GROUP_AREA * ctx.A or len(ids) >= GROUP_LEAVES):
                atoms.append(_atom_of_leaves(ctx, "G%d" % g, ids, "group"))
            else:
                take(g)
    take(0)
    tables: dict = {}
    out = []
    for a in atoms:
        L = ctx.by_id[a.leaves[0]]
        if a.kind != "group" and L["kind"] == "cell":
            tables.setdefault((L.get("cell") or {}).get("table_id"), []).append(a)
        else:
            out.append(a)
    for tid, parts in tables.items():
        out.append(_atom_of_leaves(ctx, "T%s" % tid, [i for p in parts for i in p.leaves], "table"))
    for a in out:
        _mark_base(ctx, a)
    return out


def _straddles(ctx, a, c) -> bool:
    """A header tab or badge sitting across one edge of c: a fair share inside and its span along that edge
    within c's span."""
    if _inter(a.box, c.box) < STRADDLE_AREA * a.area:
        return False
    e = ctx.eps
    across_x = a.box[0] >= c.box[0] - e and a.box[2] <= c.box[2] + e     # sits on the top or bottom edge
    across_y = a.box[1] >= c.box[1] - e and a.box[3] <= c.box[3] + e     # sits on the left or right edge
    return across_x or across_y


def _containers(ctx, atoms):
    """Mark containers and give every atom its smallest holding container."""
    holders: dict = {}
    for c in atoms:
        if c.base is None or c.link:
            continue
        cz = ctx.by_id[c.base].get("z", 0)
        held = []
        for a in atoms:
            if a is c or a.link:
                continue
            if a.area > c.area or (a.area == c.area and a.zmin <= c.zmin):
                continue
            if not _centre_in(a.box, c.box, ctx.eps):
                continue
            if a.area > 1e-6 and _inter(a.box, c.box) < CONTAIN_AREA * a.area and not _straddles(ctx, a, c):
                continue
            if c.opaque and a.zmax <= cz:
                continue
            held.append(a)
        if len(held) >= CONTAINER_MIN:
            c.container = True
            holders[c.key] = held
    for c in sorted((a for a in atoms if a.container), key=lambda a: -a.area):
        for a in holders[c.key]:
            if a.parent is None or a.parent.area > c.area:
                a.parent = c
    for a in atoms:
        if a.parent is not None:
            a.parent.children.append(a)


# ------------------------------------------------------------------ XY-cut

def _gaps(ctx, items, ax, seps):
    """Accepted gaps along ax (0 = x, 1 = y) as (lo, hi, width, marked)."""
    lo_i, hi_i = ax, ax + 2
    its = sorted(items, key=lambda a: a.box[lo_i])
    other = 1 - ax
    span_lo = min(a.box[other] for a in items)
    span_hi = max(a.box[other + 2] for a in items)
    out = []
    reach = its[0].box[hi_i]
    for k in range(1, len(its)):
        start = its[k].box[lo_i]
        if start - reach >= -ctx.overlap:
            lo, hi = reach, start
            width = hi - lo
            marked = False
            for s in seps:
                if s[0] != ax or not (lo - ctx.thin <= s[1] <= hi + ctx.thin):
                    continue
                cover = max(0.0, min(s[3], span_hi) - max(s[2], span_lo))
                if span_hi > span_lo and cover >= SEP_COVER * (span_hi - span_lo):
                    marked = True
                    break
            ok = width >= ctx.gap or (marked and width >= ctx.boxed_gap)
            if not ok:
                before = [a for a in its[:k] if a.box[hi_i] >= lo - ctx.gap]
                after = [a for a in its[k:] if a.box[lo_i] <= hi + ctx.gap]
                bb, ab = all(a.boxed() for a in before), all(a.boxed() for a in after)
                ok = (bb and ab and width >= ctx.boxed_gap) or (bb != ab)
            if ok:
                out.append((lo, hi, width, marked))
        reach = max(reach, its[k].box[hi_i])
    return out


def _split(items, ax, gaps):
    cuts = [g[1] for g in gaps]
    parts = [[] for _ in range(len(cuts) + 1)]
    for a in items:
        k = 0
        while k < len(cuts) and a.box[ax] >= cuts[k] - 1e-9:
            k += 1
        parts[k].append(a)
    return [p for p in parts if p]


def _score(gaps):
    return max((g[2] + (100.0 if g[3] else 0.0)) for g in gaps) if gaps else -1.0


def _cut(ctx, items, seps, force_ax=None):
    """n-ary XY-cut node: {"split": ax, "parts": [...]} or {"items": [...]}; every node carries "attach"."""
    if len(items) <= 1:
        return {"items": items, "attach": []}
    if force_ax is None:
        gx, gy = _gaps(ctx, items, 0, seps), _gaps(ctx, items, 1, seps)
        if not gx and not gy:
            return _cut_past_noise(ctx, items, seps)
        ax, gaps = (1, gy) if _score(gy) >= _score(gx) else (0, gx)
    else:
        ax, gaps = force_ax, _gaps(ctx, items, force_ax, seps)
        if not gaps:
            return {"items": items, "attach": []}
    strips = _split(items, ax, gaps)
    # rows whose gutters line up read as columns (proximity, or rules drawn in the gutters)
    bands: list = []
    k = 0
    while k < len(strips):
        band = list(strips[k])
        cols = 0
        n = 1
        while force_ax is None and k + n < len(strips):
            nxt = strips[k + n]
            row_gap = min(a.box[ax] for a in nxt) - max(a.box[ax + 2] for a in band)
            og = _gaps(ctx, band + nxt, 1 - ax, seps)
            strong = sum(1 for g in og if g[3] or g[2] >= ctx.gap)
            if og and all(g[3] or g[2] > row_gap for g in og) and strong >= cols and \
                    sum(1 for c in _split(band + nxt, 1 - ax, og) if _size({"items": c, "attach": []})
                        >= TINY * ctx.A) >= 2:
                band += nxt
                cols = strong
                n += 1
            else:
                break
        bands.append((band, n > 1))
        k += n
    if len(bands) == 1 and bands[0][1]:
        return _cut(ctx, items, seps, force_ax=1 - ax)
    parts = [_cut(ctx, band, seps, force_ax=1 - ax) if merged else _cut(ctx, band, seps) for band, merged in bands]
    return _merge_tiny(ctx, {"split": ax, "parts": parts, "attach": []})


def _cut_past_noise(ctx, items, seps):
    """Small loose items (labels, badges) straddling a gutter block the cut. Cut without them, then hand each
    to the part holding its centre, else the nearest part."""
    small = [a for a in items if a.area < TINY * ctx.A and not a.boxed() and not a.container]
    rest = [a for a in items if a not in small]
    if small and len(rest) >= 2:
        node = _cut(ctx, rest, seps)
        if "items" not in node:
            for a in small:
                min(node["parts"], key=lambda p: _gap2(a.box, _node_box(p)))["attach"].append(a)
            return node
    return _clusters(ctx, items, seps)


def _gap2(a, b) -> float:
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return dx * dx + dy * dy


def _clusters(ctx, items, seps):
    """No straight cut exists (a radial or free layout): items closer than the gap form one cluster, and
    each cluster is cut on its own. Two drawn boxes join only when they touch."""
    n = len(items)
    root = list(range(n))

    def find(i):
        while root[i] != i:
            root[i] = root[root[i]]
            i = root[i]
        return i
    for i in range(n):
        a = items[i]
        for j in range(i + 1, n):
            b = items[j]
            lim = ctx.boxed_gap if (a.boxed() and b.boxed()) else ctx.gap
            dx = max(a.box[0] - b.box[2], b.box[0] - a.box[2])
            dy = max(a.box[1] - b.box[3], b.box[1] - a.box[3])
            if dx < lim and dy < lim:
                root[find(i)] = find(j)
    comps: dict = {}
    for i in range(n):
        comps.setdefault(find(i), []).append(items[i])
    if len(comps) < 2:
        return {"items": items, "attach": []}
    parts = [_cut(ctx, c, seps) if len(c) > 1 else {"items": c, "attach": []} for c in comps.values()]
    return _merge_tiny(ctx, {"split": None, "parts": parts, "attach": []})


def _node_items(node):
    if "items" in node:
        return node["items"] + node["attach"]
    return [a for p in node["parts"] for a in _node_items(p)] + node["attach"]


def _node_box(node):
    return _union(a.box for a in _node_items(node))


def _size(node) -> float:
    """A part's size: its box, or the summed area of what it holds when that is smaller (a thin strip of
    labels spread along a gutter is still small)."""
    its = _node_items(node)
    return min(_area(_union(a.box for a in its)), sum(a.area for a in its))


def _merge_tiny(ctx, node):
    parts = node["parts"]
    tiny = [_size(p) < TINY * ctx.A for p in parts]
    if all(tiny):
        return {"items": _node_items(node), "attach": []}
    ax = node["split"]
    keep = [p for p, t in zip(parts, tiny) if not t]
    for i, (p, t) in enumerate(zip(parts, tiny)):
        if not t:
            continue
        if ax is None:
            b = _node_box(p)
            tgt = min(keep, key=lambda q: _gap2(b, _node_box(q)))
            (tgt["items"] if "items" in tgt else tgt["attach"]).extend(_node_items(p))
            continue
        prev = next((parts[j] for j in range(i - 1, -1, -1) if not tiny[j]), None)
        nxt = next((parts[j] for j in range(i + 1, len(parts)) if not tiny[j]), None)
        b = _node_box(p)
        dp = b[ax] - _node_box(prev)[ax + 2] if prev is not None else float("inf")
        dn = _node_box(nxt)[ax] - b[ax + 2] if nxt is not None else float("inf")
        tgt = prev if dp <= dn else nxt
        (tgt["items"] if "items" in tgt else tgt["attach"]).extend(_node_items(p))
    if len(keep) == 1:
        keep[0]["attach"].extend(node["attach"])
        return keep[0]
    node["parts"] = keep
    return node


# ------------------------------------------------------------------ zone tree

class _Zone:
    __slots__ = ("box", "items", "container", "children", "kind", "extra")

    def __init__(self, box, items, kind, container=None):
        self.box, self.items, self.kind, self.container = box, items, kind, container
        self.children: list = []
        self.extra: list = []     # leaf ids joined without growing the box (links)

    def leaves(self) -> set:
        out = set(self.extra)
        for a in self.items:
            out |= _subtree(a)
        for c in self.children:
            out |= c.leaves()
        return out


def _subtree(a: _Atom) -> set:
    out = set(a.leaves)
    for c in a.children:
        out |= _subtree(c)
    return out


def _container_zone(ctx, c: _Atom, seps):
    tabs = [a.box for a in c.children if _inter(a.box, c.box) < CONTAIN_AREA * a.area]
    z = _Zone(_union([c.box] + tabs), [c], "container", container=c.base)
    if len(c.children) >= RECURSE_MIN:
        z.children = _level(ctx, c.children, seps, inside=True)
    return z


def _zone_of(ctx, node, seps):
    att = node["attach"]
    if "items" in node:
        items = node["items"]
        if len(items) == 1 and items[0].container:
            z = _container_zone(ctx, items[0], seps)
        else:
            z = _Zone(_union(a.box for a in items), list(items), "atom" if len(items) == 1 else "group")
            if len(items) > 1:
                z.children = [_container_zone(ctx, a, seps) for a in items if a.container]
    else:
        kids = [_zone_of(ctx, p, seps) for p in node["parts"]]
        z = _Zone(_union(k.box for k in kids), [], "cut")
        z.children = kids
    if att:
        z.items = z.items + list(att)
        if z.kind != "container":
            z.box = _union([z.box] + [a.box for a in att])
    return z


def _promote(ctx, zs: list, total: int, seps) -> list:
    """A plain cut or group node holding DOMINANT of its parent's leaves gives way to its parts."""
    out = []
    for z in zs:
        if z.kind in ("cut", "group") and z.children and total and len(z.leaves()) >= DOMINANT * total:
            kids = list(z.children)
            loose = [a for a in z.items if not a.container] if z.kind == "group" else list(z.items)
            if loose:
                kids.extend(_loose_zones(ctx, loose, seps))
            out.extend(_promote(ctx, kids, total, seps))
        else:
            out.append(z)
    return out


def _loose_zones(ctx, loose, seps) -> list:
    """The loose atoms left by a promoted group, cut among themselves."""
    node = _cut(ctx, loose, seps)
    if "items" in node:
        return [_Zone(_union(a.box for a in _node_items(node)), _node_items(node), "rest")]
    return [_zone_of(ctx, p, seps) for p in node["parts"]]


def _fix(ctx, z, seps):
    """Apply the dominance rule below z: each cut node's parts measured against z itself."""
    if z.children:
        z.children = _promote(ctx, z.children, len(z.leaves()), seps)
        for c in z.children:
            _fix(ctx, c, seps)


def _level(ctx, items, seps, inside=False):
    """Zones for one level: the slide (inside=False) or a container's interior."""
    node = _cut(ctx, items, seps)
    if "items" in node:
        z = _zone_of(ctx, node, seps)
        return z.children if inside else [z]   # an uncuttable interior is the container itself
    total = len(set().union(*(_subtree(a) for a in items)))
    kids = _promote(ctx, [_zone_of(ctx, p, seps) for p in node["parts"]], total, seps)
    for z in kids:
        _fix(ctx, z, seps)
    return kids


# ------------------------------------------------------------------ main

def _icon_groups(slide, leaves) -> set:
    if slide is not None and slide.get("icons") is not None:
        return {u["id"] for u in slide["icons"] if u.get("kind") == "group"}
    return {L["icon_group"] for L in leaves if L.get("icon_group")}


def _invisible(L, bg_hex) -> bool:
    """A text-free shape with no visible fill or outline draws nothing."""
    if L.get("kind") != "sp" or L.get("line_like") or _words(L):
        return False
    return not (_fill_visible(L, bg_hex) or _line_visible(L))


def _ink(L, b, bg_hex):
    """An unboxed text shape occupies only the height its lines fill (walk's occupancy), placed by anchor."""
    t = L.get("text")
    if not t or not t.get("words") or L.get("kind") != "sp" or _fill_visible(L, bg_hex) or _line_visible(L):
        return b
    body = t.get("body") or {}
    if (body.get("vert") or "horz") != "horz" or ((L.get("frame") or {}).get("rot_deg") or 0) % 180:
        return b
    occ = t.get("occupancy")
    if not occ or occ >= 1:
        return b
    ins = body.get("insets_in") or [0.1, 0.05, 0.1, 0.05]
    y0, y1 = L["bbox"]["y_in"], L["bbox"]["y_in"] + L["bbox"]["h_in"]
    inner = max(0.0, y1 - y0 - ins[1] - ins[3])
    th = min(inner, occ * inner * INK_PAD)
    anchor = body.get("anchor") or "t"
    top = y1 - ins[3] - th if anchor == "b" else y0 + ins[1] + ((inner - th) / 2 if anchor == "ctr" else 0.0)
    nb = (b[0], max(b[1], top), b[2], min(b[3], top + th))
    return nb if nb[3] > nb[1] else b


def _trim_text(ctx, atoms):
    """An unboxed text frame often runs past where its words stop. Where one crosses a single edge of a drawn
    box it does not sit in (centre outside), it is trimmed back to that edge."""
    boxes = [b for b in atoms if not b.link and b.boxed()]
    for t in atoms:
        if t.kind != "leaf" or t.link or t.base is not None or not _words(ctx.by_id[t.leaves[0]]):
            continue
        for b in boxes:
            if b is t or b.area <= t.area or _inter(t.box, b.box) <= 0 or _centre_in(t.box, b.box, 0.0):
                continue
            x0, y0, x1, y1 = t.box
            opts = []
            if x0 < b.box[0] < x1 <= b.box[2] + ctx.eps:
                opts.append((x1 - b.box[0], (x0, y0, b.box[0], y1)))
            if b.box[0] - ctx.eps <= x0 < b.box[2] < x1:
                opts.append((b.box[2] - x0, (b.box[2], y0, x1, y1)))
            if y0 < b.box[1] < y1 <= b.box[3] + ctx.eps:
                opts.append((y1 - b.box[1], (x0, y0, x1, b.box[1])))
            if b.box[1] - ctx.eps <= y0 < b.box[3] < y1:
                opts.append((b.box[3] - y0, (x0, b.box[3], x1, y1)))
            if not opts:
                continue
            _loss, nb = min(opts, key=lambda o: o[0])
            if _area(nb) >= 0.5 * t.area:
                t.box, t.area = nb, _area(nb)


def _backdrops(ctx, atoms) -> set:
    """Big text-free shapes or pictures (not drawn boxes) with several atoms painted over them: decoration
    behind a layout. They never block a cut and join the zone holding their centre."""
    out = set()
    for a in atoms:
        if a.link or a.base is not None or a.kind != "leaf" or a.area < BACKDROP * ctx.A:
            continue
        if _words(ctx.by_id[a.leaves[0]]):
            continue
        over = sum(1 for b in atoms if b is not a and not b.link and b.zmin > a.zmax and b.area < a.area
                   and _centre_in(b.box, a.box, 0.0))
        if over >= BACKDROP_OVER:
            out.add(a)
    return out


def _build(leaves, cw, ch, bg_hex="FFFFFF", icon_groups=None):
    ctx = _Ctx(cw, ch, bg_hex)
    pool = []
    for L in leaves:
        if L.get("layer") == "chrome" or L.get("on_canvas") == "off":
            continue
        b = _clip(L, cw, ch)
        if (b[2] - b[0] <= 0 and b[3] - b[1] <= 0) or L["bbox"]["w_in"] < 0 or L["bbox"]["h_in"] < 0:
            continue
        if b[2] - b[0] < 0 or b[3] - b[1] < 0:
            continue
        if _invisible(L, bg_hex):
            continue
        ctx.by_id[L["id"]] = L
        ctx.box[L["id"]] = _ink(L, b, bg_hex)
        pool.append(L)
    if icon_groups is None:
        icon_groups = _icon_groups(None, pool)
    atoms = _atoms(ctx, pool, icon_groups)
    top: list = []
    bleed: list = []
    links: list = []
    _trim_text(ctx, atoms)
    drops = _backdrops(ctx, atoms)
    for a in atoms:
        if a.link or a in drops:
            links.append(a)
        elif a.kind == "pic" and a.area >= PIC_ZONE * ctx.A:
            bleed.append(a)
        elif a.area >= BACKGROUND * ctx.A and a.kind in ("leaf", "pic"):
            pass                        # background: cut through, belongs to no zone
        else:
            top.append(a)
    _containers(ctx, top)
    seps = []
    for a in links:
        if a in drops:
            continue
        b = a.box
        if b[2] - b[0] <= ctx.bar < b[3] - b[1]:
            seps.append((0, (b[0] + b[2]) / 2, b[1], b[3]))
        elif b[3] - b[1] <= ctx.bar < b[2] - b[0]:
            seps.append((1, (b[1] + b[3]) / 2, b[0], b[2]))
    roots = [a for a in top if a.parent is None]
    zs = _level(ctx, roots, seps) if roots else []
    zs += [_Zone(a.box, [a], "bleed") for a in bleed]
    _join_links(zs, links)
    return ctx, zs


def _join_links(zs, links):
    """Links join the deepest zone holding their centre, else the nearest top-level zone (box unchanged)."""
    flat = []

    def walk(z, d):
        flat.append((z, d))
        for c in z.children:
            walk(c, d + 1)
    for z in zs:
        walk(z, 1)
    tops = [z for z in zs if z.kind != "bleed"]
    orphans = []
    for a in links:
        cands = [(d, -_area(z.box), z) for z, d in flat if z.kind != "bleed" and _centre_in(a.box, z.box, 1e-6)]
        if cands:
            max(cands, key=lambda t: (t[0], t[1]))[2].extra.extend(a.leaves)
        elif tops:
            cx, cy = (a.box[0] + a.box[2]) / 2, (a.box[1] + a.box[3]) / 2

            def dist(z):
                dx = max(z.box[0] - cx, 0, cx - z.box[2])
                dy = max(z.box[1] - cy, 0, cy - z.box[3])
                return dx * dx + dy * dy
            min(tops, key=dist).extra.extend(a.leaves)
        else:
            orphans.append(a)
    if orphans:
        zs.append(_Zone(_union(a.box for a in orphans), orphans, "links"))


def _flatten(ctx, zs) -> list:
    rows = []

    def walk(z, parent, d):
        rows.append({"z": z, "parent": parent, "depth": d})
        me = len(rows) - 1
        for c in z.children:
            walk(c, me, d + 1)
    for z in zs:
        walk(z, None, 1)
    if len(rows) > MAX_ZONES:           # depth 1, then depth 2, then the largest
        pri = sorted(range(len(rows)), key=lambda i: (min(rows[i]["depth"], 3), -_area(rows[i]["z"].box), i))
        keep = set(pri[:MAX_ZONES])
        for r in rows:
            p = r["parent"]
            while p is not None and p not in keep:
                p = rows[p]["parent"]
            r["parent"] = p
        remap = {old: new for new, old in enumerate(i for i in range(len(rows)) if i in keep)}
        rows = [dict(rows[i], parent=remap.get(rows[i]["parent"])) for i in range(len(rows)) if i in keep]
        for r in rows:
            d, p = 1, r["parent"]
            while p is not None:
                d, p = d + 1, rows[p]["parent"]
            r["depth"] = d
    # reading order: row bands by top, then left, parents before children
    band: dict = {}
    b, b_top = -1, None
    for i in sorted(range(len(rows)), key=lambda i: rows[i]["z"].box[1]):
        t = rows[i]["z"].box[1]
        if b_top is None or t - b_top > ctx.band:
            b, b_top = b + 1, t
        band[i] = b
    order = sorted(range(len(rows)), key=lambda i: (band[i], round(rows[i]["z"].box[0], 3), rows[i]["depth"],
                                                     -_area(rows[i]["z"].box)))
    zid = {i: "Z%d" % (k + 1) for k, i in enumerate(order)}
    out = []
    for i in order:
        r = rows[i]
        z = r["z"]
        x0, y0, x1, y1 = z.box
        ids = sorted(z.leaves(), key=lambda lid: ctx.by_id[lid].get("z", 0))
        kinds: dict = {}
        wds = 0
        for lid in ids:
            L = ctx.by_id[lid]
            kinds[L["kind"]] = kinds.get(L["kind"], 0) + 1
            wds += _words(L)
        out.append({"id": zid[i], "parent": zid[r["parent"]] if r["parent"] is not None else None,
                    "depth": r["depth"],
                    "box_in": [round(x0, 3), round(y0, 3), round(x1 - x0, 3), round(y1 - y0, 3)],
                    "box_pct": [round(100 * x0 / ctx.cw, 2), round(100 * y0 / ctx.ch, 2),
                                round(100 * (x1 - x0) / ctx.cw, 2), round(100 * (y1 - y0) / ctx.ch, 2)],
                    "ids": ids, "n": len(ids), "words": wds, "kinds": kinds,
                    "container": z.container if z.kind == "container" else None,
                    "full_bleed": z.kind == "bleed" and _area(z.box) >= FULL_BLEED * ctx.A})
    return out


def _bg_hex(slide) -> str:
    fill = (slide.get("background") or {}).get("fill") or {}
    return fill.get("hex") or "FFFFFF"


def _containers_map(out) -> dict:
    return {z["container"]: [i for i in z["ids"] if i != z["container"]] for z in out if z["container"] is not None}


def zones(slide_read, canvas_w: float | None = None, canvas_h: float | None = None):
    """zones(read_slide() dict) -> list of zone dicts, Z1.. in reading order.
    Legacy: zones(leaves, canvas_w, canvas_h) -> {"zones": [...], "containers": {leaf id: member ids}};
    groups come from each leaf's group_path and icon groups from its icon_group."""
    if isinstance(slide_read, dict):
        cv = slide_read["canvas"]
        ctx, zs = _build(slide_read["shapes"], cv["w_in"], cv["h_in"], _bg_hex(slide_read),
                         _icon_groups(slide_read, slide_read["shapes"]))
        return _flatten(ctx, zs)
    ctx, zs = _build(slide_read, canvas_w, canvas_h)
    out = _flatten(ctx, zs)
    return {"zones": out, "containers": _containers_map(out)}


def slide_zones(slide: dict) -> dict:
    """Legacy wrapper: {"zones": zones(slide), "containers": {...}} for a read_slide() dict."""
    out = zones(slide)
    return {"zones": out, "containers": _containers_map(out)}


read_zones = zones
