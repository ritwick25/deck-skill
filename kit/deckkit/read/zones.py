"""Zones: the regions a person sees on a slide, as a flat list carrying a tree.

1. Pool. Content leaves only (chrome never); fully off-canvas leaves, points, and text-free shapes that draw
   nothing (no fill unlike the background, no outline, no cast shadow) are dropped; every box is clipped to the
   canvas. A shape whose painted fill casts an outer shadow draws (a white card on a white slide). An unboxed
   text frame counts its frame less the insets, and only the height its lines fill (walk's occupancy, placed by
   anchor); it is trimmed back to the edge of a drawn box it runs into. Leaves covered (80% of their area) by a
   later opaque picture or opaque fill of 15%+ of the canvas are hidden: listed in .occluded, in no zone.
2. Atoms. An outermost group is one atom unless it covers 40%+ of the canvas, holds 25+ leaves, or is sparse
   (spans 30% of the canvas along an axis with two or more cut gaps between its pieces: a row of nodes, a grid
   of tiles); then its children are taken one level down (recursively). Icon groups are always atoms; a table's
   cells are one atom. Links never block a cut and join the deepest zone holding their centre: connectors,
   line-like shapes (open custGeom strokes included), text-free bars 15x longer than thick, edge stripes (a
   text-free strip 4% of the canvas or thinner hugging an edge along half of it), backdrops (a text-free, non-box
   shape covering 15%+ of the canvas with 3+ atoms painted over it), and overlays (an outline-only box holding
   nothing that two or more atoms cross: a highlight frame over a table's columns).
3. Containers. A drawn box: a rect-like shape, any closed preset that is not hollow (callouts, chevrons, discs)
   or a closed custGeom covering half its own box, of 0.5%+ of the canvas, not an icon; a group sitting on
   such a box; or a picture (not an icon) of 0.5%+. It holds 2+ other atoms painted above an opaque fill: centre
   inside and 80% of the area inside, or a tab or badge attached to one edge (overlapping or touching it, its
   span along that edge within the box's give or take 15%, and 30% inside sticking out at most 25%, or a bar at
   most half the box's extent across the edge). Each atom belongs to the smallest container that holds it; an
   unboxed text frame it holds is trimmed to the box. A shape covering 85%+ of the canvas is a background.
4. Tree. A level is first tested for a hub-and-spoke layout: 5+ like-sized, roughly square nodes (0.5% to 3% of
   the canvas) whose centres lie on one circle (within 12% of the radius, covering 120 degrees) make a ring zone
   (with what sits on the nodes and the drawn ring), what sits near the centre a hub zone, and the pieces around
   them blocks (aligned items stacked within 2.5 cut gaps). Otherwise the level is cut by an n-ary XY-cut: a gap
   of 0.10 in at 13.333 in (scaled by canvas width) cuts; between two drawn boxes any visible gap cuts; when only
   one side is drawn boxes a touch or a 0.03 in overlap cuts; drawn bands overlapping by at most 20% of each
   one's extent cut; a rule lying in a gap marks it. Rows whose column gutters line up and are marked by rules,
   or are wider than the row gap, are read as columns. A row of 3+ top-aligned drawn boxes over a band that
   cannot be cut (domain headers over a mesh) is read as header columns: each header with what lies below it,
   bounds midway between neighbouring headers. When no straight cut exists, header columns are tried, then small
   unboxed labels are set aside and the cut retried, then items closer than the gap are clustered. Every
   container with 3+ children is cut the same way inside. Runs of tiny parts (< 1% of the canvas) join their
   nearest neighbour. A cut or group node that is not a drawn box and holds 85%+ of its parent's leaves is
   transparent: its parts move up a level. Finally every zone's box grows to hold its children's boxes.
5. Output. Flat Z1..Zn in reading order (row bands by top, then left, parents first), each with parent,
   depth, box_in and box_pct (clipped), ids (every member leaf, descendants included), n, words, kinds, base (the
   drawn box or picture the zone is built on, or None), container (base when the zone lies within its box plus
   2% of the canvas, else None) and full_bleed. A picture covering 85%+ of the canvas is its own depth-1 zone
   (full_bleed at 90%+). At most 36 zones, chosen depth 1, then depth 2, then the largest, with siblings of one
   width and height (within 2% of the canvas) kept or dropped as a set; a dropped zone takes its descendants
   (its leaves stay in its parent's ids).

API: zones(slide_read) -> ZoneList (a list) with .truncated = {"kept", "total", "dropped_sets": [{"parent",
"depth", "n", "leaves", "boxes_in"}]} and .occluded = [leaf ids]. Legacy forms kept: zones(leaves, canvas_w,
canvas_h) -> {"zones", "containers"} (groups from each leaf's group_path, icon groups from icon_group) and
slide_zones(slide) -> {"zones", "containers", "truncated", "occluded"}; containers maps each base to its members.
contains() and is_rect_like() serve walk.mark_containers unchanged.
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
MAX_ZONES = 36             # cap on zones per slide; repeated sibling sets are kept or dropped whole
SET_TOL = 0.02             # siblings whose width and height agree within this share of the canvas are one set
BACKDROP = 0.15            # a text-free non-box shape this big with 3+ atoms over it is a backdrop
BACKDROP_OVER = 3
INK_PAD = 1.05             # text ink height is the walk's occupancy estimate plus this margin
SEP_COVER = 0.50           # a rule must span this share of the band to mark a gutter
BOX_MIN = 0.005            # a drawn closed shape of any geometry at least this share of the canvas is a box ...
BOX_FILL = 0.50            # ... a custGeom only when its outline covers this share of its own box
HOLLOW = {"arc", "blockArc", "circularArrow", "leftCircularArrow", "leftRightCircularArrow", "curvedRightArrow",
          "curvedLeftArrow", "curvedUpArrow", "curvedDownArrow", "uturnArrow", "halfFrame", "corner",
          "bracketPair", "bracePair", "leftBracket", "rightBracket", "leftBrace", "rightBrace", "mathMultiply",
          "mathPlus", "plus", "noSmoking", "moon", "lightningBolt"}
TAB_OUT = 0.25             # a tab or badge sticks out of its container by at most this share of its extent
TAB_ALONG = 0.15           # ... its span along the edge stays within the container's give or take this share
TAB_THICK = 0.50           # ... or it is a bar on the edge at most this share of the container's extent across
BAND_OVERLAP = 0.20        # two drawn boxes overlapping by at most this share of each one's extent still cut
EDGE_THIN = 0.04           # a text-free strip this thin (share of the canvas across it) hugging an edge ...
EDGE_LONG = 0.50           # ... and this long (share of the canvas along it) is an edge stripe, a link
EDGE_TOUCH = 0.01          # ... hugging means within this share of the canvas of the edge
SPARSE_SPAN = 0.30         # a group spanning this share of the canvas along an axis ...
SPARSE_GAPS = 2            # ... whose children leave this many clear gaps (the cut gap) is descended
RING_MIN = 5               # radial layouts: this many like-sized nodes on a circle make a ring
RING_FIT = 0.12            # ... every centre within this share of the radius of the fitted circle
RING_ARC = 120.0           # ... covering at least this many degrees of it
HUB_REACH = 0.55           # ... and what sits within this share of the radius of its centre is the hub
HEAD_MIN = 3               # header columns: this many top-aligned drawn boxes side by side over the rest
OCCLUDER = 0.15            # an opaque picture or fill this big hides the earlier leaves it covers ...
OCCLUDED = 0.80            # ... by this share of their area
PARENT_TOL_PCT = 0.5       # a child zone never extends past its parent by more than this (percent of canvas)
CITE_TOL_PCT = 2.0         # a zone cites its container only when it lies within the container box plus this


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


def _paints(L) -> bool:
    """The shape paints a fill, whatever its colour (a white card on a white slide still paints)."""
    if L.get("grad"):
        return True
    f = L.get("fill") or {}
    t = f.get("type") or "none"
    if t == "none" or (t == "grp" and not f.get("hex")):
        return False
    return _alpha(f) >= 0.05


def _shadow_visible(L) -> bool:
    sh = (L.get("effects") or {}).get("shadow")
    if not sh or sh.get("kind") not in ("outer", "preset"):
        return False
    return sh.get("alpha") is None or float(sh["alpha"]) > 0.02


def _box_visible(L, bg_hex) -> bool:
    """A drawn box: a fill unlike the background, an outline, or a painted fill casting an outer shadow (a
    shadow-only white card on a white slide)."""
    return _fill_visible(L, bg_hex) or _line_visible(L) or (_paints(L) and _shadow_visible(L))


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


def _box_geom(ctx, L) -> bool:
    """A shape that can be a drawn box: rect-like, or any closed geometry (a callout, a chevron band, a disc, a
    custGeom panel) at least BOX_MIN of the canvas that is not an icon or an icon's part."""
    if _rect_geom(L):
        return True
    if L.get("kind") != "sp" or L.get("line_like") or L.get("icon_like") or L.get("icon_group"):
        return False
    g = L.get("geom") or {}
    if g.get("open") or (g.get("prst") is None and not g.get("cust")) or g.get("prst") in HOLLOW:
        return False
    if g.get("cust") and (g.get("fill_ratio") is None or g["fill_ratio"] < BOX_FILL):
        return False                  # a ring arc or a swoosh: its box is mostly empty
    return _area(ctx.box[L["id"]]) >= BOX_MIN * ctx.A


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
        self.occluded: list = []


def _atom_of_leaves(ctx, key, ids, kind):
    a = _Atom(key, list(ids), _union(ctx.box[i] for i in ids), kind)
    zs = [ctx.by_id[i].get("z", 0) for i in ids]
    a.zmin, a.zmax = min(zs), max(zs)
    return a


def _set_base(ctx, a, lid):
    L = ctx.by_id[lid]
    if _box_visible(L, ctx.bg):
        a.base = lid
        a.opaque = _paints(L) and _alpha(L.get("fill") or {}) >= 0.5


def _mark_base(ctx, a: _Atom):
    """A single visible box leaf is its own base; a group sits on its lowest box when it covers it; a picture
    (not an icon) of BOX_MIN or more is its own base, so labels painted over a diagram image belong to it."""
    if a.kind == "pic":
        L = ctx.by_id[a.leaves[0]]
        if not L.get("icon_like") and a.area >= BOX_MIN * ctx.A:
            a.base = L["id"]
            pic = L.get("picture") or {}
            a.opaque = (pic.get("alpha_frac") or 0.0) <= 0.02
        return
    if a.kind == "leaf":
        if _box_geom(ctx, ctx.by_id[a.leaves[0]]):
            _set_base(ctx, a, a.leaves[0])
    elif a.kind == "group":
        low = min(a.leaves, key=lambda i: ctx.by_id[i].get("z", 0))
        if _box_geom(ctx, ctx.by_id[low]) and _area(ctx.box[low]) >= BASE_COVER * a.area > 0:
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
            if g in icon_groups or not (_area(box) >= GROUP_AREA * ctx.A or len(ids) >= GROUP_LEAVES
                                        or sparse(g, box)):
                atoms.append(_atom_of_leaves(ctx, "G%d" % g, ids, "group"))
            else:
                take(g)

    def sparse(g, box) -> bool:
        """A group spread across the slide in separate pieces (a row of nodes, a grid of tiles): it spans
        SPARSE_SPAN of the canvas along an axis and its children leave SPARSE_GAPS clear gaps of the cut gap
        along it. A group sitting on its own box (a card) never is."""
        ids = under[g]
        low = min(ids, key=lambda i: ctx.by_id[i].get("z", 0))
        if _box_geom(ctx, ctx.by_id[low]) and _area(ctx.box[low]) >= BASE_COVER * _area(box):
            return False
        parts = [_union(ctx.box[i] for i in under[c]) for c in sub.get(g, ())]
        parts += [ctx.box[i] for i in direct.get(g, []) if not _is_link(ctx.by_id[i], ctx.bar)]
        if len(parts) < SPARSE_GAPS + 1:
            return False
        for ax, dim in ((0, ctx.cw), (1, ctx.ch)):
            if box[ax + 2] - box[ax] < SPARSE_SPAN * dim:
                continue
            ps = sorted(parts, key=lambda b: b[ax])
            reach, gaps = ps[0][ax + 2], 0
            for b in ps[1:]:
                if b[ax] - reach >= ctx.gap:
                    gaps += 1
                reach = max(reach, b[ax + 2])
            if gaps >= SPARSE_GAPS:
                return True
        return False
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
    """A header tab or badge attached to one edge of c (overlapping it, or touching within the overlap
    tolerance), its span along that edge within c's span give or take TAB_ALONG of c's extent, and either a fair
    share inside (STRADDLE_AREA, sticking out by at most TAB_OUT of c's extent) or a thin bar on the edge (at
    most TAB_THICK of c's extent across it: a card's header strip). A full-width row crossing a highlight frame
    and an equal box stacked against another are not tabs."""
    dx = max(c.box[0] - a.box[2], a.box[0] - c.box[2])
    dy = max(c.box[1] - a.box[3], a.box[1] - c.box[3])
    if max(dx, dy) > ctx.overlap:
        return False
    cw_, ch_ = c.box[2] - c.box[0], c.box[3] - c.box[1]
    aw, ah = a.box[2] - a.box[0], a.box[3] - a.box[1]
    share = _inter(a.box, c.box) >= STRADDLE_AREA * a.area
    out_x = max(0.0, c.box[0] - a.box[0]) + max(0.0, a.box[2] - c.box[2])
    out_y = max(0.0, c.box[1] - a.box[1]) + max(0.0, a.box[3] - c.box[3])
    tx, ty = max(ctx.eps, TAB_ALONG * cw_), max(ctx.eps, TAB_ALONG * ch_)
    across_x = a.box[0] >= c.box[0] - tx and a.box[2] <= c.box[2] + tx     # on the top or bottom edge
    across_y = a.box[1] >= c.box[1] - ty and a.box[3] <= c.box[3] + ty     # on the left or right edge
    if across_x and ((share and out_y <= TAB_OUT * ch_) or ah <= TAB_THICK * ch_):
        return True
    return across_y and ((share and out_x <= TAB_OUT * cw_) or aw <= TAB_THICK * cw_)


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
            inside = _centre_in(a.box, c.box, ctx.eps) and \
                (a.area <= 1e-6 or _inter(a.box, c.box) >= CONTAIN_AREA * a.area)
            if not inside and not _straddles(ctx, a, c):
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
            c = a.parent
            if a.kind == "leaf" and a.base is None and _words(ctx.by_id[a.leaves[0]]) and \
                    _inter(a.box, c.box) >= CONTAIN_AREA * a.area:
                nb = (max(a.box[0], c.box[0]), max(a.box[1], c.box[1]), min(a.box[2], c.box[2]),
                      min(a.box[3], c.box[3]))
                if nb[2] > nb[0] and nb[3] > nb[1]:
                    a.box, a.area = nb, _area(nb)     # a text frame overhanging its card: the words sit inside


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
        if start - reach < -ctx.overlap and _band_cut(ctx, its, k, start, reach, lo_i, hi_i):
            out.append((reach, start, start - reach, False))
        elif start - reach >= -ctx.overlap:
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


def _band_cut(ctx, its, k, start, reach, lo_i, hi_i) -> bool:
    """Stacked bands that overlap a little (chevron rows, layered panels): every item crossing the cut line is
    a drawn box overlapping the other side by at most BAND_OVERLAP of its own extent."""
    bef = [a for a in its[:k] if a.box[hi_i] > start + ctx.overlap]
    aft = [a for a in its[k:] if a.box[lo_i] < reach - ctx.overlap]
    if not bef or not aft:
        return False
    for a in bef:
        ext = a.box[hi_i] - a.box[lo_i]
        if not a.boxed() or a.box[hi_i] - start > BAND_OVERLAP * ext:
            return False
    for a in aft:
        ext = a.box[hi_i] - a.box[lo_i]
        if not a.boxed() or reach - a.box[lo_i] > BAND_OVERLAP * ext:
            return False
    return True


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


def _circle(pts):
    """Least-squares circle through points (Kasa fit): (cx, cy, r) or None when they are collinear."""
    n = float(len(pts))
    sx = sum(p[0] for p in pts)
    sy = sum(p[1] for p in pts)
    sxx = sum(p[0] * p[0] for p in pts)
    syy = sum(p[1] * p[1] for p in pts)
    sxy = sum(p[0] * p[1] for p in pts)
    sz = [p[0] * p[0] + p[1] * p[1] for p in pts]
    bx = -sum(z * p[0] for z, p in zip(sz, pts))
    by = -sum(z * p[1] for z, p in zip(sz, pts))
    bz = -sum(sz)
    m = [[sxx, sxy, sx, bx], [sxy, syy, sy, by], [sx, sy, n, bz]]
    for c in range(3):                                  # Gaussian elimination with partial pivoting
        piv = max(range(c, 3), key=lambda r: abs(m[r][c]))
        if abs(m[piv][c]) < 1e-9:
            return None
        m[c], m[piv] = m[piv], m[c]
        for r in range(3):
            if r != c:
                f = m[r][c] / m[c][c]
                m[r] = [m[r][k] - f * m[c][k] for k in range(4)]
    d, e, f = (m[k][3] / m[k][k] for k in range(3))
    cx, cy = -d / 2.0, -e / 2.0
    r2 = cx * cx + cy * cy - f
    return (cx, cy, r2 ** 0.5) if r2 > 0 else None


def _radial(ctx, items, seps):
    """A hub-and-spoke layout: RING_MIN or more like-sized, roughly square nodes (BOX_MIN to 3% of the canvas:
    discs and petals, not icons) whose centres lie on one
    circle (within RING_FIT of its radius, covering RING_ARC degrees). The ring (the nodes and what sits on
    them) and the hub (what sits near the circle's centre) become parts of their own; the rest is cut as
    usual beside them. None when there is no ring."""
    cands = []
    for a in items:
        w, h = a.box[2] - a.box[0], a.box[3] - a.box[1]
        if a.link or a.container or w <= 0 or h <= 0 or not (0.6 <= w / h <= 1.67):
            continue
        if not (BOX_MIN * ctx.A <= a.area <= 0.03 * ctx.A):
            continue
        cands.append((a, w, h))
    if len(cands) < RING_MIN:
        return None
    best = None
    for a0, w0, h0 in cands:
        like = [c for c in cands if abs(c[1] - w0) <= 0.25 * w0 and abs(c[2] - h0) <= 0.25 * h0]
        if len(like) < RING_MIN or (best is not None and len(like) <= len(best)):
            continue
        best = like
    if best is None:
        return None
    nodes = [c[0] for c in best]
    pts = [((a.box[0] + a.box[2]) / 2.0, (a.box[1] + a.box[3]) / 2.0) for a in nodes]
    fit = _circle(pts)
    if fit is None:
        return None
    cx, cy, r = fit
    size = max(max(c[1], c[2]) for c in best)
    if r < 1.2 * size or r > 0.6 * max(ctx.cw, ctx.ch):
        return None
    if max(abs(((p[0] - cx) ** 2 + (p[1] - cy) ** 2) ** 0.5 - r) for p in pts) > RING_FIT * r:
        return None
    import math
    ang = sorted(math.degrees(math.atan2(p[1] - cy, p[0] - cx)) % 360.0 for p in pts)
    gaps = [b - a for a, b in zip(ang, ang[1:])] + [ang[0] + 360.0 - ang[-1]]
    if 360.0 - max(gaps) < RING_ARC:
        return None
    ring = list(nodes)
    rb = _union(n.box for n in nodes)
    pad = 0.05 * r
    for a in items:
        if a in ring or a.link:
            continue
        if any(a.area < n.area and _centre_in(a.box, n.box, 0.0) for n in nodes):
            ring.append(a)                      # an icon or number sitting on a node
        elif not a.boxed() and not _words(ctx.by_id[a.leaves[0]]) and a.box[0] >= rb[0] - pad and \
                a.box[1] >= rb[1] - pad and a.box[2] <= rb[2] + pad and a.box[3] <= rb[3] + pad:
            ring.append(a)                      # the drawn ring itself, end dots, spokes
    hub = []
    for a in items:
        if a in ring or a.link:
            continue
        ax_, ay_ = (a.box[0] + a.box[2]) / 2.0, (a.box[1] + a.box[3]) / 2.0
        if ((ax_ - cx) ** 2 + (ay_ - cy) ** 2) ** 0.5 <= HUB_REACH * r and \
                a.box[0] >= cx - r and a.box[2] <= cx + r and a.box[1] >= cy - r and a.box[3] <= cy + r:
            hub.append(a)
    rest = [a for a in items if a not in ring and a not in hub]
    parts = [{"items": ring, "attach": []}]
    if hub:
        parts.append({"items": hub, "attach": []})
    for block in _blocks(ctx, rest):
        parts.append(_cut(ctx, block, seps) if len(block) > 3 else {"items": block, "attach": []})
    return {"split": None, "parts": parts, "attach": []}


def _blocks(ctx, items) -> list:
    """The pieces placed around a ring: items stacked over one another (left edges or centres aligned, widths
    within 2.5x) within 2.5 cut gaps vertically, or closer than the cut gap in any direction, form a block (a
    heading over its body)."""
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
            wa, wb = a.box[2] - a.box[0], b.box[2] - b.box[0]
            aligned = abs(a.box[0] - b.box[0]) <= 2 * ctx.gap or \
                abs((a.box[0] + a.box[2]) - (b.box[0] + b.box[2])) <= 4 * ctx.gap
            dy = max(a.box[1] - b.box[3], b.box[1] - a.box[3])
            dx = max(a.box[0] - b.box[2], b.box[0] - a.box[2])
            stacked = aligned and min(wa, wb) >= 0.4 * max(wa, wb) and dy <= 2.5 * ctx.gap
            if stacked or (dx < ctx.gap and dy < ctx.gap):
                root[find(i)] = find(j)
    comps: dict = {}
    for i in range(n):
        comps.setdefault(find(i), []).append(items[i])
    return list(comps.values())


def _ext(a):
    """An atom's box with its children's (a container with a header tab reaches up to the tab)."""
    return _union([a.box] + [_ext(c) for c in a.children]) if a.children else a.box


def _header_columns(ctx, items, seps):
    """A row of HEAD_MIN or more drawn boxes whose tops align (a container counts by its box with its tabs), side
    by side across half the items' width, with everything else below their tops (domain headers over a mesh):
    each header heads a column running down to the foot, the column bounds set midway between neighbouring
    headers, every other item joining the column holding its centre. None when there is no such row."""
    ext = {id(a): _ext(a) for a in items}
    boxed = [a for a in items if a.boxed() and not a.link]
    if len(boxed) < HEAD_MIN:
        return None
    best = None
    for a0 in sorted(boxed, key=lambda a: ext[id(a)][1]):     # the topmost row of HEAD_MIN or more
        row = [a for a in boxed if abs(ext[id(a)][1] - ext[id(a0)][1]) <= ctx.band]
        if len(row) >= HEAD_MIN:
            best = row
            break
    if best is None:
        return None
    row = sorted(best, key=lambda a: (ext[id(a)][0] + ext[id(a)][2]) / 2.0)
    rb = [ext[id(a)] for a in row]
    top = min(b[1] for b in rb)
    lo, hi = min(a.box[0] for a in items), max(a.box[2] for a in items)
    if sum(b[2] - b[0] for b in rb) < 0.5 * (hi - lo) or \
            any(a.box[1] < top - ctx.band for a in items if a not in row):
        return None
    for a, b in zip(rb, rb[1:]):
        if (b[0] + b[2]) / 2.0 <= a[2] or (a[0] + a[2]) / 2.0 >= b[0]:
            return None                          # a header reaching past its neighbour's centre: not a row
    bounds = [(a[2] + b[0]) / 2.0 for a, b in zip(rb, rb[1:])]
    cols = [[a] for a in row]
    for a in items:
        if a in row:
            continue
        x = (a.box[0] + a.box[2]) / 2.0
        k = 0
        while k < len(bounds) and x >= bounds[k]:
            k += 1
        cols[k].append(a)
    if sum(1 for c in cols if len(c) > 1) < 2:
        return None
    parts = [_cut(ctx, c, seps) if len(c) > 1 else {"items": c, "attach": []} for c in cols]
    return _merge_tiny(ctx, {"split": 0, "parts": parts, "attach": []})


def _cut(ctx, items, seps, force_ax=None):
    """n-ary XY-cut node: {"split": ax, "parts": [...]} or {"items": [...]}; every node carries "attach"."""
    if len(items) <= 1:
        return {"items": items, "attach": []}
    if force_ax is None and len(items) >= RING_MIN + 1:
        node = _radial(ctx, items, seps)
        if node is not None:
            return node
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
    if ax == 1:
        parts = _headed_lumps(ctx, parts, seps)
    return _merge_tiny(ctx, {"split": ax, "parts": parts, "attach": []})


def _headed_lumps(ctx, parts, seps) -> list:
    """A row of headers cut off above an uncuttable band (a mesh under its domain headers): the two are read
    together as header columns."""
    out = []
    k = 0
    while k < len(parts):
        p = parts[k]
        if k + 1 < len(parts) and "items" in parts[k + 1] and len(parts[k + 1]["items"]) >= 2 * HEAD_MIN:
            heads = _node_items(p)
            if len(heads) >= HEAD_MIN and all(a.boxed() for a in heads):
                node = _header_columns(ctx, heads + _node_items(parts[k + 1]), seps)
                if node is not None:
                    out.append(node)
                    k += 2
                    continue
        out.append(p)
        k += 1
    return out


def _cut_past_noise(ctx, items, seps):
    """Small loose items (labels, badges) straddling a gutter block the cut. Cut without them, then hand each
    to the part holding its centre, else the nearest part."""
    node = _header_columns(ctx, items, seps)
    if node is not None:
        return node
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
    return _part_zones(ctx, node, seps)


def _part_zones(ctx, node, seps) -> list:
    """Zones for a cut node's parts; atoms attached to the node itself (a tiny part merged up a level) join the
    nearest part's zone, which grows to hold them."""
    kids = [_zone_of(ctx, p, seps) for p in node["parts"]]
    for a in node["attach"]:
        z = min(kids, key=lambda k: _gap2(a.box, k.box))
        z.items = z.items + [a]
        z.box = _union([z.box, a.box])
    return kids


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
    kids = _promote(ctx, _part_zones(ctx, node, seps), total, seps)
    for z in kids:
        _fix(ctx, z, seps)
    return kids


# ------------------------------------------------------------------ main

def _icon_groups(slide, leaves) -> set:
    if slide is not None and slide.get("icons") is not None:
        return {u["id"] for u in slide["icons"] if u.get("kind") == "group"}
    return {L["icon_group"] for L in leaves if L.get("icon_group")}


def _invisible(L, bg_hex) -> bool:
    """A text-free shape with no visible fill, outline or cast shadow draws nothing."""
    if L.get("kind") != "sp" or L.get("line_like") or _words(L):
        return False
    return not _box_visible(L, bg_hex)


def _ink(L, b, bg_hex):
    """An unboxed text shape occupies only its frame less the insets, and only the height its lines fill
    (walk's occupancy, placed by anchor) when they do not fill it."""
    t = L.get("text")
    if not t or not t.get("words") or L.get("kind") != "sp" or _box_visible(L, bg_hex):
        return b
    body = t.get("body") or {}
    if (body.get("vert") or "horz") != "horz" or ((L.get("frame") or {}).get("rot_deg") or 0) % 180:
        return b
    ins = body.get("insets_in") or [0.1, 0.05, 0.1, 0.05]
    x0, y0 = L["bbox"]["x_in"], L["bbox"]["y_in"]
    x1, y1 = x0 + L["bbox"]["w_in"], y0 + L["bbox"]["h_in"]
    if x1 - x0 > ins[0] + ins[2]:
        x0, x1 = x0 + ins[0], x1 - ins[2]
    occ = t.get("occupancy")
    inner = max(0.0, y1 - y0 - ins[1] - ins[3])
    if not occ or occ >= 1:
        top, th = y0 + min(ins[1], max(0.0, y1 - y0)), max(0.0, y1 - y0 - ins[1])  # text may run past the foot
    else:
        th = min(inner, occ * inner * INK_PAD)
        anchor = body.get("anchor") or "t"
        top = y1 - ins[3] - th if anchor == "b" else y0 + ins[1] + ((inner - th) / 2 if anchor == "ctr" else 0.0)
    nb = (max(b[0], x0), max(b[1], top), min(b[2], x1), min(b[3], top + th))
    return nb if nb[3] > nb[1] and nb[2] > nb[0] else b


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
    """Big text-free shapes or pictures (not drawn boxes, under PIC_ZONE of the canvas) with several atoms
    painted over them: decoration behind a layout. They never block a cut and join the zone holding their
    centre."""
    out = set()
    for a in atoms:
        if a.link or a.base is not None or a.kind not in ("leaf", "pic") or a.area < BACKDROP * ctx.A:
            continue
        if _words(ctx.by_id[a.leaves[0]]) or (a.kind == "pic" and a.area >= PIC_ZONE * ctx.A):
            continue
        over = sum(1 for b in atoms if b is not a and not b.link and b.zmin > a.zmax and b.area < a.area
                   and _centre_in(b.box, a.box, 0.0))
        if over >= BACKDROP_OVER:
            out.add(a)
    return out


def _edge_strip(ctx, a) -> bool:
    """A text-free strip hugging a canvas edge (a side bar, a gradient margin): EDGE_THIN or thinner across,
    EDGE_LONG or longer along."""
    if a.kind not in ("leaf", "pic") or _words(ctx.by_id[a.leaves[0]]):
        return False
    x0, y0, x1, y1 = a.box
    tx, ty = EDGE_TOUCH * ctx.cw, EDGE_TOUCH * ctx.ch
    vert = x1 - x0 <= EDGE_THIN * ctx.cw and y1 - y0 >= EDGE_LONG * ctx.ch and (x0 <= tx or x1 >= ctx.cw - tx)
    horz = y1 - y0 <= EDGE_THIN * ctx.ch and x1 - x0 >= EDGE_LONG * ctx.cw and (y0 <= ty or y1 >= ctx.ch - ty)
    return vert or horz


def _occluded(ctx, pool) -> set:
    """Leaves hidden under a later opaque picture (no transparency) or opaque fill covering OCCLUDER of the
    canvas: OCCLUDED of their area (or their centre, for a line) lies under it."""
    covers = []
    for L in pool:
        b = ctx.box[L["id"]]
        if _area(b) < OCCLUDER * ctx.A or L.get("line_like"):
            continue
        if L["kind"] == "pic":
            pic = L.get("picture") or {}
            if pic.get("svg_part") or (pic.get("alpha_frac") or 0.0) > 0.02 or \
                    float(pic.get("alpha") if pic.get("alpha") is not None else 1.0) < 0.95:
                continue
            if pic.get("px") is None and pic.get("alpha_frac") is None:
                continue                      # no pixel facts: transparency unknown
        elif L["kind"] == "sp":
            f = L.get("fill") or {}
            if f.get("type") != "solid" or _alpha(f) < 0.95 or L.get("grad"):
                continue
        else:
            continue
        covers.append((L.get("z", 0), b))
    out = set()
    if not covers:
        return out
    for L in pool:
        b, z = ctx.box[L["id"]], L.get("z", 0)
        for cz, cb in covers:
            if cz <= z:
                continue
            if (_area(b) > 1e-6 and _inter(b, cb) >= OCCLUDED * _area(b)) or \
                    (_area(b) <= 1e-6 and _centre_in(b, cb, 0.0)):
                out.add(L["id"])
                break
    return out


def _overlays(ctx, top) -> list:
    """Outline-only boxes that hold nothing and are crossed by two or more atoms (a highlight frame drawn over
    a table's columns): decoration over a layout, not a region."""
    out = []
    for a in top:
        if a.base is None or a.container or a.kind != "leaf" or _paints(ctx.by_id[a.base]):
            continue
        cross = 0
        for b in top:
            if b is a or b.link:
                continue
            i = _inter(a.box, b.box)
            if i > 0 and i < CONTAIN_AREA * b.area and i < CONTAIN_AREA * a.area:
                cross += 1
        if cross >= 2:
            out.append(a)
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
    hidden = _occluded(ctx, pool)
    ctx.occluded = sorted(hidden)
    pool = [L for L in pool if L["id"] not in hidden]
    if icon_groups is None:
        icon_groups = _icon_groups(None, pool)
    atoms = _atoms(ctx, pool, icon_groups)
    top: list = []
    bleed: list = []
    links: list = []
    _trim_text(ctx, atoms)
    drops = _backdrops(ctx, atoms)
    for a in atoms:
        if a.link or a in drops or _edge_strip(ctx, a):
            links.append(a)
        elif a.kind == "pic" and a.area >= PIC_ZONE * ctx.A:
            bleed.append(a)
        elif a.area >= BACKGROUND * ctx.A and a.kind in ("leaf", "pic"):
            pass                        # background: cut through, belongs to no zone
        else:
            top.append(a)
    _containers(ctx, top)
    for a in _overlays(ctx, top):
        top.remove(a)
        if a.parent is not None:
            a.parent.children.remove(a)
            a.parent = None
        links.append(a)
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
    for z in zs:
        _fit(z)
    return ctx, zs


def _fit(z):
    """Bottom up: a zone's box holds its children's boxes (a child never extends past its parent)."""
    for c in z.children:
        _fit(c)
    if z.children:
        z.box = _union([z.box] + [c.box for c in z.children])


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


class ZoneList(list):
    """The zone list, with .truncated = {"kept", "total", "dropped_sets"} (the cap record: dropped_sets lists
    every zone or sibling set dropped whole, with its parent zone id, depth, count and leaves) and .occluded
    (leaf ids hidden under a later opaque picture or fill, members of no zone)."""
    truncated: dict
    occluded: list


def _sets(rows) -> list:
    """Units for the cap: children of one parent with the same width and height (within SET_TOL of the
    canvas) form one set; every other zone is a unit of its own. Each unit is a list of row indices."""
    by_parent: dict = {}
    for i, r in enumerate(rows):
        by_parent.setdefault(r["parent"], []).append(i)
    units = []
    for kids in by_parent.values():
        groups: list = []
        for i in kids:
            b = rows[i]["z"].box
            w, h = b[2] - b[0], b[3] - b[1]
            for g in groups:
                if abs(g[0] - w) <= g[2] and abs(g[1] - h) <= g[3]:
                    g[4].append(i)
                    break
            else:
                groups.append([w, h, rows[i]["tw"], rows[i]["th"], [i]])
        units.extend(g[4] for g in groups)
    return units


def _cap(rows) -> tuple[set, list]:
    """Rows kept under MAX_ZONES, all-or-none per sibling set: units in priority order (depth 1, then 2, then
    the largest), a unit kept when its parent is kept and it fits whole; a dropped zone takes its descendants
    with it. Returns (kept row indices, dropped units)."""
    units = _sets(rows)
    pri = lambda u: min((min(rows[i]["depth"], 3), -_area(rows[i]["z"].box), i) for i in u)   # noqa: E731
    keep: set = set()
    dropped: list = []
    gone: set = set()
    for u in sorted(units, key=pri):
        p = rows[u[0]]["parent"]
        if p is not None and p not in keep:
            gone.update(u)
            continue                      # an ancestor was dropped: the descendants go with it
        if len(keep) + len(u) <= MAX_ZONES:
            keep.update(u)
        else:
            dropped.append(u)
            gone.update(u)
    return keep, dropped


def _flatten(ctx, zs) -> list:
    rows = []
    tw, th = SET_TOL * ctx.cw, SET_TOL * ctx.ch

    def walk(z, parent, d):
        rows.append({"z": z, "parent": parent, "depth": d, "tw": tw, "th": th})
        me = len(rows) - 1
        for c in z.children:
            walk(c, me, d + 1)
    for z in zs:
        walk(z, None, 1)
    total = len(rows)
    all_rows = rows
    dropped_units: list = []
    if total > MAX_ZONES:
        keep, dropped_units = _cap(rows)
        old_rows = rows
        remap = {old: new for new, old in enumerate(i for i in range(total) if i in keep)}
        rows = [dict(old_rows[i], parent=remap.get(old_rows[i]["parent"]), old=i) for i in range(total) if i in keep]
    else:
        for i, r in enumerate(rows):
            r["old"] = i
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
    out = ZoneList()
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
        base = z.container if z.kind == "container" else None
        out.append({"id": zid[i], "parent": zid[r["parent"]] if r["parent"] is not None else None,
                    "depth": r["depth"],
                    "box_in": [round(x0, 3), round(y0, 3), round(x1 - x0, 3), round(y1 - y0, 3)],
                    "box_pct": [round(100 * x0 / ctx.cw, 2), round(100 * y0 / ctx.ch, 2),
                                round(100 * (x1 - x0) / ctx.cw, 2), round(100 * (y1 - y0) / ctx.ch, 2)],
                    "ids": ids, "n": len(ids), "words": wds, "kinds": kinds,
                    "container": base if base is not None and _holds_zone(ctx, base, z.box) else None,
                    "base": base,
                    "full_bleed": z.kind == "bleed" and _area(z.box) >= FULL_BLEED * ctx.A})
    old_zid = {r["old"]: zid[i] for i, r in enumerate(rows)}
    dropped_sets = []
    for u in dropped_units:
        p = all_rows[u[0]]["parent"]
        leaves = set().union(*(all_rows[i]["z"].leaves() for i in u))
        dropped_sets.append({"parent": old_zid.get(p) if p is not None else None,
                             "depth": all_rows[u[0]]["depth"], "n": len(u), "leaves": len(leaves),
                             "boxes_in": [[round(v, 3) for v in (b[0], b[1], b[2] - b[0], b[3] - b[1])]
                                          for b in (all_rows[i]["z"].box for i in u)]})
    out.truncated = {"kept": len(out), "total": total, "dropped_sets": dropped_sets}
    out.occluded = list(ctx.occluded)
    return out


def _holds_zone(ctx, lid, box) -> bool:
    """The container's own box, plus CITE_TOL_PCT of the canvas, holds the zone box."""
    b = _clip(ctx.by_id[lid], ctx.cw, ctx.ch)
    tx, ty = CITE_TOL_PCT / 100.0 * ctx.cw, CITE_TOL_PCT / 100.0 * ctx.ch
    return box[0] >= b[0] - tx and box[1] >= b[1] - ty and box[2] <= b[2] + tx and box[3] <= b[3] + ty


def _bg_hex(slide) -> str:
    fill = (slide.get("background") or {}).get("fill") or {}
    return fill.get("hex") or "FFFFFF"


def _containers_map(out) -> dict:
    """{drawn box leaf id: member ids} for every zone built on a drawn box (its base)."""
    return {z["base"]: [i for i in z["ids"] if i != z["base"]] for z in out if z.get("base") is not None}


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
    """{"zones": zones(slide), "containers": {...}, "truncated": {...}, "occluded": [...]} for a read_slide()
    dict."""
    out = zones(slide)
    return {"zones": out, "containers": _containers_map(out), "truncated": out.truncated,
            "occluded": out.occluded}


read_zones = zones
