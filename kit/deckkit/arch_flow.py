"""Flow diagrams in the house grammar: CI/CD and release, MLOps and LLMOps, data lineage and medallion, event-driven
integration, and agent state machines (library/design/tech-diagrams/spec.md 3.6, 3.7, 3.9, 3.11; ruling 21).

Built beside deckkit.arch, never inside it: arch.Diagram places floating marks on nested group grids and routes
between them; these types are pipelines and graphs whose anatomy is a row of columns joined by gates, rails and
loops. They share arch's notation (its type ladder, flow stroke, badge, house frame kinds and colours, read from the
arch module so a change there carries here) and draw on a measured grid of their own:

    b = arch_flow.Board(WIDE.content, theme, cols=[1.4, 0.7, 2.2], rows=[0.30, HEAD_BAR, "auto", "auto"])
    b.frame("tool", "panel", "Tooling account · shared services", cols=(2, 2), rows=(1, 3))
    b.mark("ecr", "vendor:aws/compute/ec2-container-registry", "Amazon ECR", "images", cell=(2, 2))
    b.gate("g1", "quality", "tests and SAST clean", cell=(1, 2))
    b.edge("actions", "g1", "build image", step=2)
    b.steps({2: "Build and scan"})
    metrics = b.render(slide, name="cicd")

What it refuses (each a GeometryError or Overflows, or listed under draft=True):
  * a caption over two lines per part, a label over one line or 1.30in, type under the 8pt floor;
  * a node that overlaps another node or caption, or leaves the board, or its frame (spec 1.1: 0.10in inset);
  * an edge with no clear route: every route is orthogonal, at most two bends, lands on a node's edge and never on
    its caption side, keeps off every other node, caption and header, never runs along a frame border or another
    edge, and crosses no other edge (P26.h). The router tries straight, Z, L, C and U routes on every free side
    and port and keeps the clear one with the fewest bends;
  * a label with no clear place beside its own segments (it is never wrapped, never shrunk);
  * an unlabelled outer boundary, or one whose label states no fact after a middot or colon (P26.k).

Kinds of edge (spec 1.4, one dash per kind, keyed in the legend whenever more than one is drawn):
  data solid, async dash, control sysDot, conditional sysDash, feedback lgDash in accent-deep (retrain, rollback,
  revise; routed on the perimeter through a lane row), blocked dashDot with a no-entry glyph before the target (the
  forbidden path: a manual console deploy).

Kinds of node: mark (a product mark with its caption), glyph (an actor glyph with its caption), gate (quality
diamond, approval, health or traffic disc in the accent, criterion as its caption, spec 3.6), stop (a no-entry
glyph), activity (a dashed text box with no icon, spec 3.7), state (a LangGraph node: rounded box, name and role
inside, interrupt variant dashed in accent-deep), terminal (START and END pills), chip (an event type, a dataset,
a digest token, or a +N more count).

The five type builders below (cicd, mlops, medallion, events, state_graph) each lay out one anatomy from a content
dict and return the Board; scripts/example_arch_flow.py builds one slide of each.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from . import arch, glyphs, icons, measure, ooxml, prims
from . import text as txt
from .canvas import Box
from .errors import GeometryError, Overflows
from .text import Para, Run


def _c(name, default):
    """arch's notation constant, so one change there carries to these types."""
    return getattr(arch, name, default)


ICON = _c("ICON", 0.42)
NAME_PT, ROLE_PT = _c("NAME_PT", 9.0), _c("ROLE_PT", 8.0)
LABEL_PT = _c("LABEL_PT", 8.0)
LABEL_MAX_W = _c("LABEL_MAX_W", 1.30)
LABEL_INS = _c("LABEL_INS", measure.Insets(0.03, 0.01, 0.03, 0.01))
CLEAR = _c("CLEAR", 0.03)
FRAME_CLEAR = _c("FRAME_CLEAR", 0.05)
FRAME_POKE = _c("FRAME_POKE", 0.08)
CAP_GAP = _c("CAP_GAP", 0.05)
CAP_MAX_W = _c("CAP_MAX_W", 1.45)
CAP_GUTTER = _c("CAP_GUTTER", 0.12)
BAR_H, BAR_PT = _c("BAR_H", 0.30), _c("BAR_PT", 10.0)
GROUP_PT = _c("GROUP_PT", 9.0)
RADIUS, TAB_RADIUS = _c("HOUSE_RADIUS", 0.05), _c("TAB_RADIUS", 0.06)
LEGEND_PT, MORE_PT = _c("LEGEND_PT", 9.0), _c("MORE_PT", 9.0)
LAST_LEG = _c("LAST_LEG", 0.15)
BADGE, BADGE_PT = _c("BADGE_BY", {}).get("house", (0.22, 8.0))
BADGE_FILL = _c("BADGE_FILL", {}).get("house", "accent")
LINE_ROLE, LINE_PT = _c("FLOW_BY", {}).get("house", ("ink-muted", 1.0))[:2]

HEAD_BAR = BAR_H + 0.14        # a head row for a frame with a navy bar
HEAD_LABEL = 0.30              # a head row for a frame with a label tab (boundary, zone, panel)
HEAD_SECTION = 0.28            # a head row for a section (hairline rule and bold head)
INSET = 0.12                   # a nested frame inside its parent, each side (spec 1.1: 0.10in minimum)
EDGE_IN = 0.06                 # a top-level frame inside its column span
PAD = 0.08                     # a frame's content inside its edges
VPAD = 0.04                    # above and below a row's content
PORT = 0.125                   # port pitch along one side (spec 1.4)
GATE = 0.30                    # a gate glyph (spec 3.6: 0.24 to 0.30in)
STOP = 0.26
BLOCK_GLYPH = 0.18             # the no-entry glyph on a blocked edge (spec 1.4: 0.16in)

EDGE_KINDS = {
    "data": {"dash": None, "role": LINE_ROLE, "key": "Request or data"},
    "async": {"dash": "dash", "role": LINE_ROLE, "key": "Event, asynchronous"},
    "control": {"dash": "sysDot", "role": LINE_ROLE, "key": "Control or configuration"},
    "conditional": {"dash": "sysDash", "role": LINE_ROLE, "key": "Conditional edge"},
    "feedback": {"dash": "lgDash", "role": "accent-deep", "key": "Feedback loop"},
    "blocked": {"dash": "dashDot", "role": LINE_ROLE, "key": "Blocked path"},     # async holds dash (as arch.py)
}
GATE_KINDS = {"quality": ("DIAMOND", "check"), "approval": ("OVAL", "user-check"), "health": ("OVAL", "clock"),
              "traffic": ("OVAL", "bar-chart-3")}
FRAME_KINDS = ("region", "boundary", "zone", "panel", "band", "section", "segmented", "lane")
SIDES = ("t", "b", "l", "r")
DIR = {"r": (1, 0), "l": (-1, 0), "t": (0, -1), "b": (0, 1)}
CAP_SIDE = {"below": "b", "above": "t", "right": "r", "left": "l"}
_ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,40}")


def _check_id(what, v):
    if not isinstance(v, str) or not _ID.fullmatch(v):
        raise GeometryError("%s id" % what, need="lower-case letters, digits, - and _", have=repr(v))
    return v


def _inter(a: Box, b: Box, pad: float = 0.0) -> bool:
    return a.x < b.r + pad and b.x < a.r + pad and a.y < b.b + pad and b.y < a.b + pad


def _seg_hits(p, q, b: Box, pad: float = 0.02) -> bool:
    (x1, y1), (x2, y2) = p, q
    if abs(y1 - y2) < 1e-9:
        lo, hi = sorted((x1, x2))
        return b.y - pad < y1 < b.b + pad and lo < b.r + pad and hi > b.x - pad
    lo, hi = sorted((y1, y2))
    return b.x - pad < x1 < b.r + pad and lo < b.b + pad and hi > b.y - pad


def _cross(p, q, e1, e2, eps: float = 0.005) -> bool:
    ph, eh = abs(p[1] - q[1]) < 1e-9, abs(e1[1] - e2[1]) < 1e-9
    if ph == eh:
        return False
    (h1, h2), (v1, v2) = ((p, q), (e1, e2)) if ph else ((e1, e2), (p, q))
    y, x = h1[1], v1[0]
    hx0, hx1 = sorted((h1[0], h2[0]))
    vy0, vy1 = sorted((v1[1], v2[1]))
    return hx0 + eps < x < hx1 - eps and vy0 + eps < y < vy1 - eps


def _along(p, q, e1, e2, tol) -> bool:
    """Segment p-q runs parallel to e1-e2 within tol, overlapping along their length."""
    ph, eh = abs(p[1] - q[1]) < 1e-9, abs(e1[1] - e2[1]) < 1e-9
    if ph != eh:
        return False
    if ph:
        if abs(p[1] - e1[1]) > tol:
            return False
        lo, hi = sorted((p[0], q[0]))
        elo, ehi = sorted((e1[0], e2[0]))
    else:
        if abs(p[0] - e1[0]) > tol:
            return False
        lo, hi = sorted((p[1], q[1]))
        elo, ehi = sorted((e1[1], e2[1]))
    return min(hi, ehi) - max(lo, elo) > 0.02


def _clean(pts) -> list:
    out = []
    for x, y in pts:
        pt = (round(x, 4), round(y, 4))
        if out and abs(out[-1][0] - pt[0]) < 1e-4 and abs(out[-1][1] - pt[1]) < 1e-4:
            continue
        out.append(pt)
    k = 1
    while k < len(out) - 1:
        (ax, ay), (bx_, by), (cx, cy) = out[k - 1], out[k], out[k + 1]
        if (abs(ax - bx_) < 1e-4 and abs(bx_ - cx) < 1e-4) or (abs(ay - by) < 1e-4 and abs(by - cy) < 1e-4):
            out.pop(k)
        else:
            k += 1
    return out


def _dist_pt_seg(pt, p, q) -> float:
    (x, y), (x1, y1), (x2, y2) = pt, p, q
    cx = min(max(x, min(x1, x2)), max(x1, x2))
    cy = min(max(y, min(y1, y2)), max(y1, y2))
    return math.hypot(x - cx, y - cy)


def _seglen(p, q) -> float:
    return abs(p[0] - q[0]) + abs(p[1] - q[1])


def _face(th, bold=False):
    return measure.face_for(txt._default_face(th), bold)


def _tw(text, pt, th, bold=False) -> float:
    return measure.width_in(text, pt, _face(th, bold)) * measure.SLACK


@dataclass
class Node:
    id: str
    kind: str
    body: Box
    name: str = ""
    role: str | None = None
    mark: str | None = None
    cap: Box | None = None
    paras: list = field(default_factory=list)
    capside: str | None = None
    frame: str | None = None
    opt: dict = field(default_factory=dict)

    def closed(self) -> set:
        """Sides an edge may not use: the caption's side, and any the node declares closed."""
        out = set(self.opt.get("closed", ()))
        if self.cap is not None and self.capside:
            out.add(CAP_SIDE[self.capside])
        return out


@dataclass
class Frame:
    id: str
    kind: str
    label: str
    cols: tuple
    rows: tuple
    depth: int = 0
    box: Box | None = None
    head: Box | None = None          # what its header occupies (bar or label), kept clear of edges and labels
    words: Box | None = None         # the label's own words (a flow may cross a bar, never its words)
    cells: list = field(default_factory=list)
    opt: dict = field(default_factory=dict)


@dataclass
class Edge:
    a: str
    b: str
    label: str | None
    kind: str
    step: int | None
    sides: tuple
    lane: tuple | None
    via: list | None
    ports: tuple
    label_seg: int | None
    pts: list = field(default_factory=list)
    label_box: Box | None = None
    badge: Box | None = None
    glyph: Box | None = None


class Board:
    """A measured grid of columns and rows on which frames, nodes and edges are declared, then drawn by render().

    cols: relative column widths. rows: per row a fixed height in inches, "auto" (sized by its content) or
    ("auto", w) (auto, and takes a w share of the height left over; by default the leftover goes evenly between the
    auto rows, as air above and below their content). A cell is (col, row); a node centres in its cell, n nodes of one
    cell share it left to right (slot=(k, n)). A frame spans cols=(c0, c1) and rows=(r0, r1), both inclusive; its first
    row is its head row (HEAD_BAR, HEAD_LABEL or HEAD_SECTION tall), and it hugs its content at the foot."""

    def __init__(self, box: Box, theme=None, *, cols, rows, name: str = "flow", keys=None, draft: bool = False):
        self.th = prims.theme_of(theme)
        self.box = box
        self.name = str(name)
        if not re.fullmatch(r"[A-Za-z0-9_-]+", self.name):
            raise GeometryError("board name", need="letters, digits, - and _", have=name)
        w = [float(v) for v in cols]
        if not w or any(v <= 0 for v in w):
            raise GeometryError("board cols", need="positive weights", have=cols)
        self.cols = w
        self.rows = []
        for r in rows:
            if r == "auto":
                self.rows.append(("auto", None))
            elif isinstance(r, (tuple, list)) and len(r) == 2 and r[0] == "auto":
                self.rows.append(("auto", float(r[1])))
            elif isinstance(r, (int, float)) and r >= 0:
                self.rows.append(("fixed", float(r)))
            else:
                raise GeometryError("board row", need='inches, "auto" or ("auto", weight)', have=r)
        t = sum(w)
        self.colx = [box.x]
        for v in w:
            self.colx.append(self.colx[-1] + box.w * v / t)
        self.nodes: dict[str, Node] = {}
        self.frames: dict[str, Frame] = {}
        self.edges: list[Edge] = []
        self.legend: dict[int, str] = {}
        self.keys = dict(keys or {})
        self.draft = bool(draft)
        self.problems: list[str] = []
        self._pending = []                # nodes declared by cell, placed when rows are measured
        self.overlays = []                # (kind, data) drawn after frames: rails, dividers
        self.buses = []                   # fan-in trunks, routed before the edges
        self._laid = False

    # ------------------------------------------------------------------ problems
    def _problem(self, err):
        if not self.draft:
            raise err
        self.problems.append(str(err))

    # ------------------------------------------------------------------ frames
    def frame(self, id, kind, label, *, cols, rows, fact=None, cells=None, fill=None, icon=None):
        """A frame around a span of cells. kind: region (navy header bar, rule-strong frame), boundary (dashed
        rule-strong, label tab: an account or platform boundary), zone (dashed accent-deep: a trust zone), panel (a
        flat card with a label tab: a shared tooling panel), band (a card with a navy bar; its marks may carry no
        flow, P26.r), section (a hairline and a bold head, no frame), segmented (one frame of adjoining cells, each with
        its own head: the medallion; cells is the list of cell labels, one per column of the span), lane (a muted bold
        label and no frame: actors or SaaS outside every boundary, as arch draws its lanes). fact, when given,
        is appended after a middot: an outer boundary states a fact (spec 1.6)."""
        _check_id("frame", id)
        if id in self.frames:
            raise GeometryError("frame %s" % id, need="a unique id", have="duplicate")
        if kind not in FRAME_KINDS:
            raise GeometryError("frame %s kind" % id, need=" / ".join(FRAME_KINDS), have=kind)
        lab = str(label or "").strip()
        if fact:
            lab = "%s · %s" % (lab, str(fact).strip())
        if not lab:
            raise GeometryError("frame %s label" % id, need="a label", have=repr(label),
                                hint="an unlabelled zone is decoration (spec 1.6)")
        c0, c1 = cols
        r0, r1 = rows
        if not (0 <= c0 <= c1 < len(self.cols) and 0 <= r0 <= r1 < len(self.rows)):
            raise GeometryError("frame %s span" % id, need="inside the %dx%d grid" % (len(self.cols), len(self.rows)),
                                have=(cols, rows))
        if kind == "segmented":
            cells = [(c, 1) if isinstance(c, str) else (str(c[0]), int(c[1])) for c in (cells or [])]
            if sum(n for _c, n in cells) != c1 - c0 + 1 or not all(str(c).strip() for c, _n in cells):
                raise GeometryError("frame %s cells" % id, need="labels whose spans cover the %d columns"
                                    % (c1 - c0 + 1), have=cells, hint="a cell is a label (one column) or "
                                    "(label, columns)")
        if fill not in (None, "card") or (fill and kind != "region"):
            raise GeometryError("frame %s fill" % id, need="None, or 'card' on a region (a shared tooling account: a "
                                "card with a hairline under its bar, a second boundary kind beside the regions)",
                                have=fill)
        if icon is not None:
            ik, _, key = str(icon).partition(":")
            ok = (ik == "vendor" and icons.vendor_resolves(key)) or (ik == "mark" and key in icons.mark_registry())
            if not ok or kind not in ("boundary", "zone", "panel"):
                raise GeometryError("frame %s icon" % id, need="vendor:<key> on a boundary, zone or panel (the broker's "
                                    "mark on its corner, spec 3.11)", have=icon)
        self.frames[id] = Frame(id, kind, lab, (c0, c1), (r0, r1), cells=list(cells or []),
                                opt={"fill": fill, "icon": icon})
        return id

    def _covering(self, c, r):
        return [f for f in self.frames.values() if f.cols[0] <= c <= f.cols[1] and f.rows[0] <= r <= f.rows[1]
                and f.kind not in ("section", "lane")]

    def _depths(self):
        fs = list(self.frames.values())
        for f in fs:
            f.depth = sum(1 for g in fs if g is not f and g.kind not in ("section", "lane") and g.cols[0] <= f.cols[0]
                          and f.cols[1] <= g.cols[1] and g.rows[0] <= f.rows[0] and f.rows[1] <= g.rows[1]
                          and (g.cols, g.rows) != (f.cols, f.rows))

    def _span_x(self, c, r):
        """(x0, x1) a node in cell (c, r) may use: the column inside every frame that covers the cell."""
        x0, x1 = self.colx[c], self.colx[c + 1]
        cov = self._covering(c, r)
        for f in cov:
            fx0 = self.colx[f.cols[0]] + EDGE_IN + INSET * f.depth
            fx1 = self.colx[f.cols[1] + 1] - EDGE_IN - INSET * f.depth
            if f.cols[0] == c:
                x0 = max(x0, fx0 + PAD)
            if f.cols[1] == c:
                x1 = min(x1, fx1 - PAD)
            if f.kind == "segmented":                        # a cell's content keeps clear of the dividers
                k = f.cols[0]
                for _lab, span in f.cells[:-1]:
                    k += span
                    if k == c:
                        x0 = max(x0, self.colx[k] + PAD)
                    if k == c + 1:
                        x1 = min(x1, self.colx[k] - PAD)
        return x0, x1

    # ------------------------------------------------------------------ nodes
    def _declare(self, id, kind, cell, slot, **kw):
        _check_id("node", id)
        if id in self.nodes or any(p[0] == id for p in self._pending):
            raise GeometryError("node %s" % id, need="a unique id", have="duplicate")
        c, r = cell
        if not (0 <= c < len(self.cols) and 0 <= r < len(self.rows)):
            raise GeometryError("node %s cell" % id, need="inside the grid", have=cell)
        k, n = slot
        if not (0 <= k < n):
            raise GeometryError("node %s slot" % id, need="(k, n) with 0 <= k < n", have=slot)
        self._pending.append((id, kind, (c, r), (k, n), kw))
        return id

    def mark(self, id, mark, name, role=None, *, cell, slot=(0, 1), size=ICON, caption="below", cap_w=None, dx=0.0,
             span=None, align="center", hinge=None):
        """A product mark ('vendor:<key>' or 'mark:<key>') or an actor glyph ('glyph:<name>') with its caption.
        align ('center', 'left', 'right') sets it in its slot; span=(c0, c1) centres it across columns; hinge=c centres
        it on the line between columns c-1 and c (a registry on the boundary of two zones, spec 3.7)."""
        kind, _, key = str(mark).partition(":")
        if kind not in ("vendor", "mark", "glyph") or not key:
            raise GeometryError("node %s mark" % id, need="vendor:<key>, mark:<key> or glyph:<name>", have=mark)
        if kind == "vendor" and not icons.vendor_resolves(key):
            raise GeometryError("node %s mark" % id, need="a vendor key (deckkit.icons.vendor_keys)", have=key)
        if kind == "mark" and key not in icons.mark_registry():
            raise GeometryError("node %s mark" % id, need="a key in the mark registry (ruling 19)", have=key)
        if kind == "glyph":
            try:
                glyphs.resolve(key)
            except Exception as err:                         # noqa: BLE001 (UnknownGlyph carries the closest names)
                raise GeometryError("node %s glyph" % id, need="a curated glyph", have=key, hint=str(err)) from None
        if not str(name or "").strip():
            raise GeometryError("node %s name" % id, need="a caption name", have=repr(name))
        if caption not in CAP_SIDE:
            raise GeometryError("node %s caption" % id, need="below, above, right or left", have=caption)
        return self._declare(id, "mark", cell, slot, mark=str(mark), name=str(name).strip(),
                             role=(str(role).strip() or None) if role else None, size=float(size), caption=caption,
                             cap_w=cap_w, dx=float(dx), span=span, align=align, hinge=hinge)

    def gate(self, id, kind, label, *, cell, slot=(0, 1), caption="below", cap_w=None, dx=0.0, span=None):
        """A gate on the path (spec 3.6): quality (diamond), approval, health (bake or alarms) or traffic (a staged
        rollout). label carries the criterion (a number, a role or a check name), at most 4 words before any middot."""
        if kind not in GATE_KINDS:
            raise GeometryError("gate %s kind" % id, need=" / ".join(GATE_KINDS), have=kind)
        crit = str(label or "").strip()
        if not crit or len(crit.split("·")[0].split()) > 4:
            raise GeometryError("gate %s label" % id, need="a criterion of 1 to 4 words", have=label)
        return self._declare(id, "gate", cell, slot, gate=kind, name=crit, caption=caption, cap_w=cap_w, dx=float(dx),
                             size=GATE, span=span)

    def stop(self, id, label, *, cell, slot=(0, 1), caption="above", cap_w=None, dx=0.0, span=None):
        """Where a failed gate stops the path: a no-entry glyph and what happens (spec 3.6)."""
        return self._declare(id, "stop", cell, slot, name=str(label).strip(), caption=caption, cap_w=cap_w,
                             dx=float(dx), size=STOP, span=span)

    def activity(self, id, text, *, cell, slot=(0, 1), w=None, dx=0.0, span=None):
        """An activity: a dashed text box with no icon, one line (spec 3.7)."""
        return self._declare(id, "activity", cell, slot, name=str(text).strip(), w=w, dx=float(dx), span=span)

    def state(self, id, name, role=None, *, cell, slot=(0, 1), w=None, interrupt=False, glyph=None, dx=0.0,
              span=None):
        """A graph node (LangGraph style): a rounded box with its name (bold) and an optional role line inside.
        interrupt=True draws the human-in-the-loop node: a dashed accent-deep outline and a person glyph."""
        return self._declare(id, "state", cell, slot, name=str(name).strip(), role=role, w=w,
                             interrupt=bool(interrupt), glyph=glyph or ("user-check" if interrupt else None),
                             dx=float(dx), span=span)

    def terminal(self, id, text, *, cell, slot=(0, 1), dx=0.0, span=None):
        """A START or END pill."""
        return self._declare(id, "terminal", cell, slot, name=str(text).strip(), dx=float(dx), span=span)

    def chip(self, id, text, *, cell, slot=(0, 1), kind="event", prefix=None, w=None, dx=0.0, span=None):
        """A chip: kind event (an event type on a bus: 'domain.event', past tense), dataset (a table: prefix is its
        schema, drawn muted), token (an artifact digest on a rail, near-black) or more (a measured '+N more')."""
        if kind not in ("event", "dataset", "token", "more"):
            raise GeometryError("chip %s kind" % id, need="event, dataset, token or more", have=kind)
        if kind == "event" and not re.fullmatch(r"[a-z]+(\.[a-z_]+){1,2}", str(text)):
            raise GeometryError("chip %s event name" % id, need="domain.event or domain.entity.event, lower case",
                                have=text)
        return self._declare(id, "chip", cell, slot, name=str(text).strip(), chip=kind, prefix=prefix, w=w,
                             dx=float(dx), span=span)

    # ------------------------------------------------------------------ edges
    def edge(self, a, b, label=None, kind="data", *, step=None, sides=(None, None), lane=None, via=None,
             ports=(None, None), label_seg=None):
        """An edge from node a to node b. sides=(sa, sb) pins the side it leaves and the side it lands on ('t', 'b',
        'l', 'r'); lane=('y', inches) or ('row', r) runs its middle segment along a perimeter lane (a U or C route);
        via lists explicit corner points; ports=(oa, ob) pins the offsets along the sides (multiples of 0.125in).
        label is what moves, 1 to 4 words before any middot, on one line. label_seg picks the segment for it."""
        if kind not in EDGE_KINDS:
            raise GeometryError("edge kind", need=" / ".join(EDGE_KINDS), have=kind)
        if step is not None and not (isinstance(step, int) and 1 <= step <= 12):
            raise GeometryError("edge step", need="an int 1..12", have=step)
        if label is not None:
            label = str(label).strip()
            if not label or len(label.split("·")[0].split()) > 4:
                raise GeometryError("edge %s to %s label" % (a, b), need="1 to 4 words: what moves", have=label)
        for s in sides:
            if s not in (None,) + SIDES:
                raise GeometryError("edge sides", need="t, b, l, r or None", have=sides)
        if a == b:
            raise GeometryError("edge %s" % a, need="two different nodes", have="the same node twice")
        self.edges.append(Edge(a, b, label, kind, step, tuple(sides), lane, list(via) if via else None, tuple(ports),
                               label_seg))
        return len(self.edges)

    def steps(self, mapping):
        """The legend text for each numbered step (8 to 12 words at most; the spoken sentence lives elsewhere)."""
        for k, v in dict(mapping).items():
            if not (isinstance(k, int) and 1 <= k <= 12) or not str(v or "").strip():
                raise GeometryError("step %r" % (k,), need="an int 1..12 and its text", have=v)
            self.legend[k] = str(v).strip()

    def rail(self, id, label, *, row, cols, chips=(), drops=True):
        """A token rail (spec 3.6): the artifact's name, then a rule along row from col cols[0] to cols[1], with one
        token chip per (id, text, col) riding it: the same digest in every account, promoted, never rebuilt. drops=True
        joins each chip to the bottom of the frame above it with a short rule. The label sits left of the first column
        and must fit the free room there."""
        self.overlays.append(("rail", {"id": _check_id("rail", id), "label": str(label), "row": row, "cols": cols,
                                       "chips": [c[0] for c in chips], "drops": bool(drops)}))
        for cid, text, col in chips:
            span = col if isinstance(col, tuple) else None
            self.chip(cid, text, cell=(col[0] if span else col, row), kind="token", span=span)

    def stack(self, entries, *, cell, rows, size=0.30, caption="left", gap=0.10, cap_w=None):
        """A stacked list in one column across rows=(r0, r1): actors or sources one under another, each a mark with its
        caption beside it (spec 3.9: sources as a stacked list). entries are (id, mark, name, role). The stack centres on
        the span and does not size the rows it crosses; it is refused when it is taller than they are."""
        c, r0 = cell
        r1 = rows[1]
        n = len(entries)
        if not (r0 == rows[0] <= r1) or n < 1:
            raise GeometryError("stack", need="cell=(c, r0) and rows=(r0, r1) with entries", have=(cell, rows, n))
        for k, (nid, mark, name, role) in enumerate(entries):
            self.mark(nid, mark, name, role, cell=(c, r0), size=size, caption=caption, cap_w=cap_w,
                      align="right" if caption == "left" else "left")
            self._pending[-1][4]["stack"] = (r0, r1, k, n, float(gap))
        return [e[0] for e in entries]

    def bus(self, sources, target, label=None, kind="data", *, x=None):
        """Fan-in (spec E9): each source joins one vertical trunk by a short unheaded feeder, and one headed segment
        carries the merged flow into the target's left side. x pins the trunk; by default it sits midway between the
        sources' right edges and the target. Sources must lie left of the target."""
        if kind not in EDGE_KINDS:
            raise GeometryError("bus kind", need=" / ".join(EDGE_KINDS), have=kind)
        if len(sources) < 2:
            raise GeometryError("bus", need="two or more sources", have=len(sources))
        if label is not None and (not str(label).strip() or len(str(label).split("·")[0].split()) > 4):
            raise GeometryError("bus label", need="1 to 4 words: what moves", have=label)
        self.buses.append({"sources": list(sources), "target": target, "label": label, "kind": kind, "x": x})

    # ------------------------------------------------------------------ layout
    def _caption(self, n: Node, cap_w):
        th = self.th
        al = {"below": "center", "above": "center", "right": "left", "left": "right"}[n.capside]
        if n.kind == "gate":
            paras = [Para((Run(n.name, role="ink-deep", bold=True, size=ROLE_PT),), align=al)]
        elif n.kind == "stop":
            paras = [Para((Run(n.name, role="ink-muted", size=ROLE_PT),), align=al)]
        else:
            paras = [Para((Run(n.name, role="ink-deep", bold=True, size=NAME_PT),), align=al)]
            if n.role:
                paras.append(Para((Run(n.role, role="ink-muted", size=ROLE_PT),), align=al))
        w = max(0.3, min(cap_w, CAP_MAX_W))
        widest = 0.0
        for p in paras:
            try:
                fit = txt.check_fit("node %s caption" % n.id, [p], (w, 100.0), th)
            except Overflows as err:
                self._problem(err)
                w = 1.45
                fit = txt.check_fit("node %s caption" % n.id, [p], (w, 100.0), th)
            if fit.n_lines > 2:
                self._problem(Overflows("node %s caption %r" % (n.id, p.runs[0].text), need=fit.n_lines, have=2,
                                        unit="lines", hint="at %.2fin it wraps to %d lines; cut words or widen the "
                                        "column, never smaller type" % (w, fit.n_lines)))
            elif p is paras[0] and n.kind == "mark" and fit.n_lines > 1 and len(n.name.split()) <= 3:
                self._problem(Overflows("node %s name %r" % (n.id, n.name), need=round(_tw(n.name, NAME_PT, th, True)
                                        + 0.02, 3), have=round(w, 3), unit="in", hint="a name of 3 words or fewer "
                                        "sits on one line (as in arch's house grammar): widen its column"))
            r = p.runs[0]
            for line in fit.lines:
                widest = max(widest, _tw(line, r.size, th, r.bold))
        tight = min(w, math.ceil((widest + 0.02) * 1000) / 1000.0)
        lines = [txt.check_fit("c", [p], (tight, 100.0), th).n_lines for p in paras]
        full = [txt.check_fit("c", [p], (w, 100.0), th).n_lines for p in paras]
        if lines == full:
            w = tight
        h = math.ceil(txt.need_height(paras, w, th) * 10000 + 1) / 10000.0
        n.paras = paras
        return w, h

    def _inside_paras(self, n: Node):
        """The text written inside a state, activity, terminal or chip, and the box size it needs."""
        th = self.th
        o = n.opt
        if n.kind == "state":
            ps = [Para((Run(n.name, role="ink-deep", bold=True, size=NAME_PT),), align="center")]
            if n.role:
                ps.append(Para((Run(n.role, role="ink-muted", size=ROLE_PT),), align="center"))
            lead = 0.24 if o.get("glyph") else 0.0
            need_w = max(_tw(n.name, NAME_PT, th, True), _tw(n.role or "", ROLE_PT, th)) + 0.20 + lead
            return ps, max(need_w, o.get("w") or 0.0), 0.50 if n.role else 0.36
        if n.kind == "activity":
            ps = [Para((Run(n.name, role="ink", size=ROLE_PT),), align="center")]
            return ps, max(_tw(n.name, ROLE_PT, th) + 0.18, o.get("w") or 0.0), 0.28
        if n.kind == "terminal":
            ps = [Para((Run(n.name, role="paper", bold=True, size=ROLE_PT),), align="center")]
            return ps, _tw(n.name, ROLE_PT, th, True) + 0.24, 0.24
        k = o["chip"]
        if k == "dataset":
            runs = []
            if o.get("prefix"):
                runs.append(Run(o["prefix"], role="ink-muted", size=ROLE_PT))
            runs.append(Run(n.name, role="ink-deep", bold=True, size=ROLE_PT))
            ps = [Para(tuple(runs), align="center")]
            need = _tw(o.get("prefix") or "", ROLE_PT, th) + _tw(n.name, ROLE_PT, th, True) + 0.18
            return ps, max(need, o.get("w") or 0.0), 0.26
        if k == "token":
            ps = [Para((Run(n.name, role="paper", bold=True, size=ROLE_PT),), align="center")]
            return ps, max(_tw(n.name, ROLE_PT, th, True) + 0.24, o.get("w") or 0.0), 0.24
        if k == "more":
            ps = [Para((Run(n.name, role="ink-muted", size=MORE_PT),), align="center")]
            return ps, _tw(n.name, MORE_PT, th) + 0.26, 0.28
        ps = [Para((Run(n.name, role="ink-deep", size=ROLE_PT),), align="center")]
        return ps, max(_tw(n.name, ROLE_PT, th) + 0.18, o.get("w") or 0.0), 0.26

    def _layout(self):
        if self._laid:
            return
        self._laid = True
        self._depths()
        th = self.th
        # 1. bodies and captions by cell (x known), heights per node
        cellcount = {}
        for nid, kind, (c, r), (k, n_), kw in self._pending:
            cellcount[(c, r)] = max(cellcount.get((c, r), 0), n_)
        made = []
        for nid, kind, (c, r), (k, n_), kw in self._pending:
            x0, x1 = self._span_x(c, r)
            if kw.get("span"):                              # a node centred across several columns
                x0, x1 = self._span_x(kw["span"][0], r)[0], self._span_x(kw["span"][1], r)[1]
            if kw.get("hinge") is not None:                 # centred on the line between two columns (spec 3.7)
                hx = self.colx[kw["hinge"]]
                half = min(self.colx[kw["hinge"]] - self.colx[kw["hinge"] - 1],
                           self.colx[kw["hinge"] + 1] - self.colx[kw["hinge"]])
                x0, x1 = hx - half, hx + half
            slot_w = (x1 - x0) / n_
            sx0 = x0 + slot_w * k
            cx = sx0 + slot_w / 2 + kw.get("dx", 0.0)
            n = Node(nid, kind, Box(0, 0, 1, 1), name=kw.get("name", ""), role=kw.get("role"), mark=kw.get("mark"),
                     capside=kw.get("caption"), opt=dict(kw))
            n.cell = (c, r)
            n.slot_x = (sx0, sx0 + slot_w)
            if kind in ("mark", "gate", "stop"):
                side = kw["size"]
                gut = 0.04 if kind in ("gate", "stop") else -CAP_GUTTER    # a gate's gutter column ends at frames
                cap_w = kw.get("cap_w") or (slot_w + gut if n.capside in ("below", "above") else 1.0)
                cw, ch = self._caption(n, cap_w)
                n.cap_wh = (cw, ch)
                n.side = side
                if n.capside == "below":
                    above, below = side / 2, side / 2 + CAP_GAP + ch
                elif n.capside == "above":
                    above, below = side / 2 + CAP_GAP + ch, side / 2
                else:
                    above = below = max(side, ch) / 2
                n.bw, n.bh = side, side
                if kind == "mark":
                    self._ink_shape(n, cw)
                unit = max(n.bw, cw) if n.capside in ("below", "above") else n.bw + 0.06 + cw
                al = kw.get("align", "center")
                if al == "left":
                    cx = sx0 + unit / 2 + (0.0 if n.capside in ("below", "above") else 0.0) + kw.get("dx", 0.0)
                    if n.capside == "right":
                        cx = sx0 + n.bw / 2 + kw.get("dx", 0.0)
                elif al == "right":
                    cx = sx0 + slot_w - unit / 2 + kw.get("dx", 0.0)
                    if n.capside == "right":
                        cx = sx0 + slot_w - unit + n.bw / 2 + kw.get("dx", 0.0)
            else:
                ps, w, h = self._inside_paras(n)
                if w > slot_w - 0.04 + 1e-6:
                    self._problem(Overflows("node %s width" % nid, need=round(w, 3), have=round(slot_w - 0.04, 3),
                                            unit="in", hint="a wider column, fewer nodes in the cell, or fewer words"))
                n.paras = ps
                n.bw, n.bh = w, h
                above = below = h / 2
            n.ext = (above, below)
            n.cx = cx
            made.append(n)
        # 2. row heights
        heights = []
        for ri, (mode, val) in enumerate(self.rows):
            if mode == "fixed":
                heights.append(val)
                continue
            ab = [n.ext[0] for n in made if n.cell[1] == ri and not n.opt.get("stack")]
            be = [n.ext[1] for n in made if n.cell[1] == ri and not n.opt.get("stack")]
            heights.append((max(ab) + max(be) + 2 * VPAD) if ab else 2 * VPAD)
        spare = self.box.h - sum(heights)
        if spare < -1e-6:
            self._problem(Overflows("board height", need=round(sum(heights), 3), have=round(self.box.h, 3), unit="in",
                                    hint="fewer rows, fewer caption lines, or a taller box"))
            spare = 0.0
        autos = [i for i, (m, v) in enumerate(self.rows) if m == "auto"]
        weighted = [i for i in autos if self.rows[i][1]]
        grow = {}
        if weighted:
            t = sum(self.rows[i][1] for i in weighted)
            for i in weighted:
                grow[i] = spare * self.rows[i][1] / t
        elif autos:
            for i in autos:
                grow[i] = spare / len(autos)
        self.rowy, y = [], self.box.y
        self.rowh = []
        for i, h in enumerate(heights):
            hh = h + grow.get(i, 0.0)
            self.rowy.append(y)
            self.rowh.append(hh)
            y += hh
        # 3. place: one body centre line per row
        stacks = {}
        for n in made:
            if n.opt.get("stack"):
                r0, r1, k, cnt, gap = n.opt["stack"]
                stacks.setdefault((n.cell[0], r0, r1, gap), []).append((k, n))
        for (c, r0, r1, gap), lst in stacks.items():
            lst.sort(key=lambda t: t[0])
            units = [n.ext[0] + n.ext[1] for _k, n in lst]
            total = sum(units) + gap * (len(units) - 1)
            y0, y1 = self.rowy[r0], self.rowy[r1] + self.rowh[r1]
            if total > y1 - y0 + 1e-6:
                self._problem(Overflows("stack in column %d" % c, need=round(total, 3), have=round(y1 - y0, 3),
                                        unit="in", hint="fewer entries, or span more rows"))
            y = (y0 + y1) / 2 - total / 2
            for (_k, n), u in zip(lst, units):
                n.stack_cy = y + n.ext[0]
                y += u + gap
        for ri in range(len(self.rows)):
            row = [n for n in made if n.cell[1] == ri]
            if not row:
                continue
            flat = [n for n in row if not n.opt.get("stack")] or row
            ab = max(n.ext[0] for n in flat)
            be = max(n.ext[1] for n in flat)
            cy0 = self.rowy[ri] + (self.rowh[ri] - (ab + be)) / 2 + ab
            for n in row:
                cy = getattr(n, "stack_cy", cy0)
                n.body = Box(n.cx - n.bw / 2, cy - n.bh / 2, n.bw, n.bh)
                if getattr(n, "ink_wh", None):                  # a mark's box shrinks to its ink's aspect
                    w_, h_ = n.ink_wh
                    n.body = Box(n.cx - w_ / 2, cy - h_ / 2, w_, h_)
                if n.kind in ("mark", "gate", "stop"):
                    cw, ch = n.cap_wh
                    if n.capside == "below":
                        n.cap = Box(n.cx - cw / 2, n.body.b + CAP_GAP, cw, ch)
                    elif n.capside == "above":
                        n.cap = Box(n.cx - cw / 2, n.body.y - CAP_GAP - ch, cw, ch)
                    elif n.capside == "right":
                        n.cap = Box(n.body.r + 0.06, cy - ch / 2, cw, ch)
                    else:
                        n.cap = Box(n.body.x - 0.06 - cw, cy - ch / 2, cw, ch)
                self.nodes[n.id] = n
        # 4. frames, deepest first: x from columns and depth, y from the head row to the content they hold; frames of
        #    one depth that span the same rows end on one foot line (a row of accounts reads as instances)
        for d in sorted({f.depth for f in self.frames.values()}, reverse=True):
            level = [f for f in self.frames.values() if f.depth == d]
            for f in level:
                x0 = self.colx[f.cols[0]] + EDGE_IN + INSET * f.depth
                x1 = self.colx[f.cols[1] + 1] - EDGE_IN - INSET * f.depth
                y0 = self.rowy[f.rows[0]] + (0.02 if f.depth else 0.0)
                inner = [n for n in self.nodes.values() if f.cols[0] <= n.cell[0] <= f.cols[1]
                         and f.rows[0] <= n.cell[1] <= f.rows[1]]
                low = max([max(n.body.b, n.cap.b if n.cap else n.body.b) for n in inner] +
                          [g.box.b for g in self.frames.values() if g is not f and g.box is not None
                           and g.depth > f.depth and f.cols[0] <= g.cols[0] and g.cols[1] <= f.cols[1]
                           and f.rows[0] <= g.rows[0] and g.rows[1] <= f.rows[1]] + [y0 + 0.4])
                if f.kind in ("section", "lane"):
                    f.box = Box(x0, y0, x1 - x0, max(0.3, low - y0))
                else:
                    f.box = Box(x0, y0, x1 - x0, low + PAD + 0.02 - y0)
            spans = {}
            for f in level:
                if f.kind not in ("section", "lane"):
                    spans.setdefault((f.rows[0], f.rows[1]), []).append(f)
            for fs in spans.values():
                low = max(f.box.b for f in fs)
                for f in fs:
                    f.box = Box(f.box.x, f.box.y, f.box.w, low - f.box.y)
        for f in self.frames.values():
            self._head(f)

    def _ink_shape(self, n: Node, cap_w):
        """The mark's drawn size: its ink's aspect inside the tier's square (a wordmark as wide as its caption), set
        before placement so alignment and routing see the artwork, not a transparent margin."""
        kind, _, key = n.mark.partition(":")
        ink = None
        try:
            if kind == "vendor":
                ink = arch._ink_box(str(icons.vendor_path(key)), None)
            elif kind == "mark":
                e = icons.mark_registry().get(key)
                ink = arch._ink_box(str(icons.marks_dir() / e["file"]), e["sha256"])
        except Exception:                                   # noqa: BLE001 (no alpha: draw the box as it is)
            ink = None
        n.ink = ink
        n.ink_wh = None
        if ink is None:
            return
        l, t, r, b, pw, ph = ink
        ar = ((r - l) * pw) / max(1e-9, (b - t) * ph)
        side = n.bw
        if ar >= 1:
            w, h = side, side / ar
        else:
            w, h = side * ar, side
        if ar > 1.6:                                          # a wordmark: as wide as its caption allows
            w = min(max(cap_w, side), side * ar)
            h = w / ar
        n.ink_wh = (w, h)
        n.bw = w

    def _head(self, f: Frame):
        th = self.th
        b = f.box
        if f.kind in ("region", "band"):
            f.head = Box(b.x, b.y, b.w, BAR_H)
            tw = min(b.w - 0.2, _tw(f.label, BAR_PT, th, True) + 0.1)
            f.words = Box(b.cx - tw / 2, b.y, tw, BAR_H)
            if _tw(f.label, BAR_PT, th, True) > b.w - 0.2:
                self._problem(Overflows("frame %s label %r" % (f.id, f.label), need=1, have=0, unit="lines",
                                        hint="a header names the region in a few words"))
            return
        if f.kind == "segmented":
            f.head = Box(b.x, b.y, b.w, HEAD_SECTION)
            xs, c = [b.x], f.cols[0]
            for _lab, span in f.cells[:-1]:
                c += span
                xs.append(self.colx[c])
            xs.append(b.r)
            f.cell_words = []
            for k, (lab, _span) in enumerate(f.cells):
                tw = _tw(lab, GROUP_PT, th, True) + 0.06
                cx = (xs[k] + xs[k + 1]) / 2
                if tw > xs[k + 1] - xs[k] - 0.16:
                    self._problem(Overflows("segment %s cell %r" % (f.id, lab), need=round(tw, 3),
                                            have=round(xs[k + 1] - xs[k] - 0.16, 3), unit="in"))
                f.cell_words.append(Box(cx - tw / 2, b.y + 0.04, tw, HEAD_SECTION - 0.08))
            f.words = None
            return
        bold = True
        lw = _tw(f.label, GROUP_PT, th, bold) + 0.02
        lead = 0.08 if f.kind not in ("section", "lane") else 0.0
        if f.opt.get("icon") and self._icon_w(f) <= 0.3:     # a square mark leads the label; a wordmark follows it
            lead = 0.06 + self._icon_w(f) + 0.06
        if lw > b.w - lead - 0.08:
            self._problem(Overflows("frame %s label %r" % (f.id, f.label), need=round(lw, 3),
                                    have=round(b.w - lead - 0.08, 3), unit="in", hint="a shorter label or a wider span"))
        lh = measure.line_in(GROUP_PT, _face(th, bold)) * measure.SLACK + 0.02
        y = b.y + (0.07 if f.kind in ("section", "lane") else 0.06)
        f.words = Box(b.x + lead, y, lw, lh)
        f.head = Box(b.x, b.y, lead + lw + 0.04, y + lh - b.y)
        if f.opt.get("icon") and self._icon_w(f) > 0.3:     # the trailing wordmark is part of the header
            iw = self._icon_w(f)
            if lead + lw + 0.10 + iw > b.w - 0.08:
                self._problem(Overflows("frame %s label and mark" % f.id, need=round(lead + lw + 0.10 + iw, 3),
                                        have=round(b.w - 0.08, 3), unit="in"))
            f.head = Box(b.x, b.y, lead + lw + 0.10 + iw + 0.04, max(y + lh, b.y + 0.05 + 0.24) - b.y)
            f.words = Box(b.x + lead, y, lw + 0.10 + iw, max(lh, 0.24))

    # ------------------------------------------------------------------ checks before routing
    def _check_nodes(self):
        ns = list(self.nodes.values())
        for n in ns:
            for bx_ in (n.body, n.cap):
                if bx_ is not None and not self.box.contains(bx_, tol=1e-6):
                    self._problem(Overflows("node %s" % n.id, need="inside the board", have="crossing its edge",
                                            hint="a narrower caption, fewer nodes in the column, or a wider column"))
        for i, a in enumerate(ns):
            for b in ns[i + 1:]:
                for p in (a.body, a.cap):
                    for q in (b.body, b.cap):
                        if p is not None and q is not None and _inter(p, q, CLEAR):
                            self._problem(GeometryError("nodes %s and %s" % (a.id, b.id), need="apart",
                                                        have="overlapping", hint="give one its own cell or slot"))
        for f in self.frames.values():
            if f.kind in ("section", "lane"):
                continue
            inner = f.box.inset(0.04)
            for n in ns:
                if f.cols[0] <= n.cell[0] <= f.cols[1] and f.rows[0] <= n.cell[1] <= f.rows[1]:
                    for bx_ in (n.body, n.cap):
                        if bx_ is not None and not inner.contains(bx_, tol=1e-6):
                            self._problem(GeometryError("node %s" % n.id, need="inside frame %s" % f.id,
                                                        have="crossing its edge", hint="a wider span or a shorter "
                                                        "caption"))
                        if bx_ is not None and f.head is not None and _inter(bx_, f.head, 0.02):
                            self._problem(GeometryError("node %s" % n.id, need="clear of frame %s's header" % f.id,
                                                        have="on it", hint="a taller head row"))
        for f in self.frames.values():                    # spec 1.6: the outer two levels state a fact
            if f.kind in ("boundary", "zone") and f.depth <= 1 and not re.search(r"[·:]\s*\S", f.label):
                self._problem(GeometryError("frame %s label" % f.id, need="a fact after a middot or colon",
                                            have=f.label, hint="'Prod account · 2 waves' (spec 1.6, gate P26.k)"))

    # ------------------------------------------------------------------ routing
    def _obstacles(self):
        out = []
        for n in self.nodes.values():
            out.append((n.body, "body", n.id))
            if n.cap is not None:
                out.append((n.cap, "caption", n.id))
        for f in self.frames.values():
            if f.words is not None:
                out.append((f.words, "header", None))
            for w in getattr(f, "cell_words", None) or []:
                out.append((w, "header", None))
        for kind, d in self.overlays:
            if kind != "rail":
                continue
            lab, _p, p, q, drops = self._rail_geom(d)
            out.append((lab, "rail", None))
            if q[0] - p[0] > 0.05:
                out.append((Box(p[0], p[1] - 0.01, q[0] - p[0], 0.02), "rail", None))
            for a, b in drops:
                out.append((Box(a[0] - 0.01, a[1], 0.02, b[1] - a[1]), "rail", None))
        return out

    def _frame_segs(self):
        out = []
        for f in self.frames.values():
            if f.kind in ("section", "lane"):
                continue
            b = f.box
            out += [((b.x, b.y), (b.r, b.y)), ((b.x, b.b), (b.r, b.b)), ((b.x, b.y), (b.x, b.b)),
                    ((b.r, b.y), (b.r, b.b))]
            if f.kind in ("region", "band"):
                out.append(((b.x, b.y + BAR_H), (b.r, b.y + BAR_H)))
        return out

    def _port(self, n: Node, side, off):
        b = n.body
        if n.kind == "gate" and n.opt.get("gate") == "quality":     # a diamond's points
            off = 0.0
        if side == "r":
            return (b.r, b.cy + off)
        if side == "l":
            return (b.x, b.cy + off)
        if side == "b":
            return (b.cx + off, b.b)
        return (b.cx + off, b.y)

    def _offsets(self, n: Node, side, fixed):
        if fixed is not None:
            return [float(fixed)]
        b = n.body
        half = (b.h if side in ("l", "r") else b.w) / 2 - 0.05
        if n.kind == "gate" and n.opt.get("gate") == "quality":
            return [0.0]
        out = [0.0]
        k = 1
        while k * PORT <= half + 1e-9 and k <= 3:
            out += [-k * PORT, k * PORT]
            k += 1
        return out

    def _sides(self, n: Node, other: Node):
        dx, dy = other.body.cx - n.body.cx, other.body.cy - n.body.cy
        h = "r" if dx > 0 else "l"
        v = "b" if dy > 0 else "t"
        order = [h, v, {"t": "b", "b": "t"}[v], {"r": "l", "l": "r"}[h]] if abs(dx) >= abs(dy) else \
            [v, h, {"r": "l", "l": "r"}[h], {"t": "b", "b": "t"}[v]]
        bad = n.closed()
        return [s for s in order if s not in bad]

    def _lane_value(self, lane):
        if lane is None:
            return None
        ax, v = lane
        if ax == "row":
            return ("y", self.rowy[v] + self.rowh[v] / 2)
        if ax == "col":
            return ("x", (self.colx[v] + self.colx[v + 1]) / 2)
        return (ax, float(v))

    def _free(self, lo, hi, a0, a1, axis, obstacles, own):
        """Middles of the free gaps for a cross leg along axis ('x': a vertical leg at x in lo..hi spanning y a0..a1)."""
        bad = []
        for b, what, nid in obstacles:
            if axis == "x" and b.y < a1 + 0.02 and b.b > a0 - 0.02:
                bad.append((b.x - 0.04, b.r + 0.04))
            if axis == "y" and b.x < a1 + 0.02 and b.r > a0 - 0.02:
                bad.append((b.y - 0.04, b.b + 0.04))
        for e1, e2 in self._frame_segs():
            if axis == "x" and abs(e1[0] - e2[0]) < 1e-9 and min(e1[1], e2[1]) < a1 and max(e1[1], e2[1]) > a0:
                bad.append((e1[0] - 0.07, e1[0] + 0.07))
            if axis == "y" and abs(e1[1] - e2[1]) < 1e-9 and min(e1[0], e2[0]) < a1 and max(e1[0], e2[0]) > a0:
                bad.append((e1[1] - 0.07, e1[1] + 0.07))
        bad.sort()
        free, x = [], lo + 0.08
        for b0, b1 in bad:
            if b0 > x:
                free.append((x, min(b0, hi - 0.08)))
            x = max(x, b1)
        if x < hi - 0.08:
            free.append((x, hi - 0.08))
        free = [(u, v) for u, v in free if v - u > 0.0]
        free.sort(key=lambda t: -(t[1] - t[0]))
        return [(u + v) / 2 for u, v in free] + [lo + (hi - lo) * f for f in (0.5, 0.35, 0.65)]

    def _shapes(self, p, sa, q, sb, e, obstacles):
        lane = self._lane_value(e.lane)
        out = []
        ha, hb = sa in ("l", "r"), sb in ("l", "r")
        da, db = DIR[sa], DIR[sb]
        if e.via:
            return [[p] + [tuple(v) for v in e.via] + [q]]
        if ha and hb:
            if sa != sb:                                       # facing: straight or Z
                fwd = (q[0] - p[0]) * da[0] > 0.2
                if fwd and abs(p[1] - q[1]) < 1e-6:
                    out.append([p, q])
                if fwd:
                    lo, hi = sorted((p[0], q[0]))
                    a0, a1 = sorted((p[1], q[1]))
                    xs = [lane[1]] if lane and lane[0] == "x" else self._free(lo, hi, a0, a1, "x", obstacles, e)
                    for xm in xs[:6]:
                        out.append([p, (xm, p[1]), (xm, q[1]), q])
            else:                                              # C round the outside of both
                ext = max(p[0], q[0]) if sa == "r" else min(p[0], q[0])
                xs = [lane[1]] if lane and lane[0] == "x" else [ext + da[0] * d for d in (0.2, 0.3, 0.45, 0.6)]
                out += [[p, (xl, p[1]), (xl, q[1]), q] for xl in xs]
        elif not ha and not hb:
            if sa != sb:
                fwd = (q[1] - p[1]) * da[1] > 0.2
                if fwd and abs(p[0] - q[0]) < 1e-6:
                    out.append([p, q])
                if fwd:
                    lo, hi = sorted((p[1], q[1]))
                    a0, a1 = sorted((p[0], q[0]))
                    ys = [lane[1]] if lane and lane[0] == "y" else self._free(lo, hi, a0, a1, "y", obstacles, e)
                    for ym in ys[:6]:
                        out.append([p, (p[0], ym), (q[0], ym), q])
            else:                                              # U over or under both
                ext = max(p[1], q[1]) if sa == "b" else min(p[1], q[1])
                ys = [lane[1]] if lane and lane[0] == "y" else [ext + da[1] * d for d in (0.2, 0.3, 0.45, 0.6)]
                out += [[p, (p[0], yl), (q[0], yl), q] for yl in ys]
        elif ha and not hb:                                    # L: across, then into a top or bottom
            if (q[0] - p[0]) * da[0] > 0.1 and (q[1] - p[1]) * (-db[1]) > LAST_LEG - 1e-6:
                out.append([p, (q[0], p[1]), q])
        else:                                                  # L: up or down, then into a side
            if (q[1] - p[1]) * da[1] > 0.1 and (q[0] - p[0]) * (-db[0]) > LAST_LEG - 1e-6:
                out.append([p, (p[0], q[1]), q])
        return out

    def _why(self, pts, e, obstacles, taken, fsegs):
        own = (e.a, e.b)
        for i, (p, q) in enumerate(zip(pts, pts[1:])):
            if abs(p[0] - q[0]) > 1e-6 and abs(p[1] - q[1]) > 1e-6:
                return "a diagonal segment"
            for b, what, nid in obstacles:
                if nid in own and what == "body":
                    if _seg_hits(p, q, b.inset(0.012), pad=0.0):
                        return "its own node"
                    continue
                if _seg_hits(p, q, b):
                    return "%s %s" % (what, nid or "")
            for e1, e2 in fsegs:
                if _along(p, q, e1, e2, 0.05):
                    return "a frame border"
            for e1, e2 in taken:
                if _along(p, q, e1, e2, 0.07):
                    return "another edge"
            if not (self.box.x - 1e-6 <= min(p[0], q[0]) and max(p[0], q[0]) <= self.box.r + 1e-6 and
                    self.box.y - 1e-6 <= min(p[1], q[1]) and max(p[1], q[1]) <= self.box.b + 1e-6):
                return "the board's edge"
        if _seglen(*pts[-2:]) < LAST_LEG - 1e-6:
            return "a final leg under %.2fin" % LAST_LEG
        if _seglen(*pts[:2]) < 0.08:
            return "a first leg under 0.08in"
        if len(pts) - 2 > 2:
            return "more than two bends"
        return None

    def _route(self, e: Edge, obstacles, taken, used):
        A, B = self.nodes[e.a], self.nodes[e.b]
        sas = [e.sides[0]] if e.sides[0] else self._sides(A, B)
        sbs = [e.sides[1]] if e.sides[1] else self._sides(B, A)
        fsegs = self._frame_segs()
        whys = []
        best = None
        for i, sa in enumerate(sas):
            for j, sb in enumerate(sbs):
                for oa in self._offsets(A, sa, e.ports[0]):
                    if e.ports[0] is None and any(abs(oa - u) < 0.09 for u in used.get((e.a, sa), [])):
                        continue
                    for ob in self._offsets(B, sb, e.ports[1]):
                        if e.ports[1] is None and any(abs(ob - u) < 0.09 for u in used.get((e.b, sb), [])):
                            continue
                        p, q = self._port(A, sa, oa), self._port(B, sb, ob)
                        for k, pts in enumerate(self._shapes(p, sa, q, sb, e, obstacles)):
                            pts = _clean(pts)
                            if len(pts) < 2:
                                continue
                            why = self._why(pts, e, obstacles, taken, fsegs)
                            if why:
                                if why not in whys:
                                    whys.append(why)
                                continue
                            cross = sum(1 for s_ in zip(pts, pts[1:]) for t in taken if _cross(*s_, *t))
                            cost = (cross, len(pts), round(abs(oa) + abs(ob), 3), i + j, k,
                                    round(sum(_seglen(a, b) for a, b in zip(pts, pts[1:])), 3))
                            if best is None or cost < best[0]:
                                best = (cost, pts, (sa, oa), (sb, ob))
        if best is None or best[0][0] > 0:
            what = "a route crossing %d other edge(s)" % best[0][0] if best else \
                "every route blocked: %s" % ", ".join(whys[:4])
            raise GeometryError("edge %s to %s" % (e.a, e.b), need="a clear route with no crossing", have=what,
                                hint="pin sides=, give a lane=, move a node, or declare the edge earlier")
        (_c0, pts, (sa, oa), (sb, ob)) = best
        used.setdefault((e.a, sa), []).append(oa)
        used.setdefault((e.b, sb), []).append(ob)
        return pts

    # ------------------------------------------------------------------ labels and badges
    def _label_size(self, e: Edge):
        w = _tw(e.label, LABEL_PT, self.th) + LABEL_INS.l + LABEL_INS.r + 0.01
        if w > LABEL_MAX_W:
            self._problem(Overflows("edge %s to %s label %r" % (e.a, e.b, e.label), need=round(w, 3),
                                    have=LABEL_MAX_W, unit="in", hint="name what moves in a few words"))
        e.label_paras = [Para((Run(e.label, role="ink", size=LABEL_PT),), align="center")]
        h = math.ceil(txt.need_height(e.label_paras, w, self.th, LABEL_INS) * 10000 + 1) / 10000.0
        return min(w, LABEL_MAX_W), h

    def _ok(self, b: Box, hard, segs, poke=True):
        if not self.box.contains(b, tol=0.002):
            return False
        for o in hard:
            if _inter(b, o, CLEAR):
                return False
        for f in self.frames.values():
            if f.kind in ("section", "lane"):
                continue
            fr = f.box
            inside = fr.x + FRAME_CLEAR <= b.x and b.r <= fr.r - FRAME_CLEAR and fr.y + FRAME_CLEAR <= b.y and \
                b.b <= fr.b - FRAME_CLEAR
            apart = not _inter(b, fr, CLEAR)
            ow = min(b.r, fr.r) - max(b.x, fr.x)
            oh = min(b.b, fr.b) - max(b.y, fr.y)
            starts_out = b.x < fr.x - 0.025 or b.y < fr.y - 0.025     # gate P04 reads it as no child of the frame
            shallow = poke and starts_out and (0 < ow <= FRAME_POKE or 0 < oh <= FRAME_POKE)
            if not (inside or apart or shallow):
                return False
            if inside and fr.w <= 2.4 and fr.h <= 2.4 and f.kind not in ("segmented",):
                return False                               # a label inside a small frame reads as the frame's text
        for p, q in segs:
            if _seg_hits(p, q, b, pad=0.01):
                return False
        for n in self.nodes.values():                       # never where it reads as a mark's caption (P26.e)
            if n.kind != "mark":
                continue
            m = n.body
            if m.b - 0.05 <= b.y <= m.b + 0.36 and m.x <= b.cx <= m.r:
                return False
            if min(m.b, b.b) - max(m.y, b.y) > 0 and b.y <= m.cy <= b.b and \
                    (0 <= b.x - m.r <= 0.36 or 0 <= m.x - b.r <= 0.36):
                return False
        return True

    def _place_labels(self):
        hard = [b for b, what, nid in self._obstacles()]
        all_segs = [(e, list(zip(e.pts, e.pts[1:]))) for e in self.edges]
        segs_all = [s for _e, ss in all_segs for s in ss]
        for e in self.edges:
            if e.glyph is not None:
                hard.append(e.glyph)
        for e in self.edges:
            if e.step is None:
                continue
            e.badge = self._badge_place(e, hard, segs_all)
            if e.badge is not None:
                hard.append(e.badge)
        for e in self.edges:
            if e.label is None:
                continue
            w, h = self._label_size(e)
            mine = list(zip(e.pts, e.pts[1:]))
            others = [s for g, ss in all_segs if g is not e for s in ss]

            def horiz(sg):
                return abs(sg[0][1] - sg[1][1]) < 1e-9

            def near(b):
                return min((_dist_pt_seg((b.cx, b.cy), p, q) for p, q in others), default=9.0)

            order = sorted(range(len(mine)), key=lambda k: -_seglen(*mine[k]))
            if e.label_seg is not None:
                k0 = e.label_seg if e.label_seg >= 0 else len(mine) + e.label_seg
                order = [k0] + [k for k in order if k != k0]
            placed = None
            for apart, poke in ((0.25, False), (0.0, False), (0.0, True)):
                for k in order:
                    p, q = mine[k]
                    hz = horiz((p, q))
                    L = _seglen(p, q)
                    ext = w if hz else h
                    if L < ext + 0.12 and hz:
                        continue
                    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
                    half = max(0.0, L / 2 - ext / 2 - 0.04)
                    shifts, s = [0.0], 0.1
                    while s <= half + 1e-9:
                        shifts += [-s, s]
                        s += 0.1
                    for sh in shifts:
                        if hz:
                            cx = mx + sh
                            opts = [Box(cx - w / 2, my - CLEAR - h, w, h), Box(cx - w / 2, my + CLEAR, w, h)]
                        else:
                            cy = my + sh
                            opts = [Box(mx + CLEAR + 0.01, cy - h / 2, w, h),
                                    Box(mx - CLEAR - 0.01 - w, cy - h / 2, w, h)]
                        opts.sort(key=lambda b: -near(b))
                        for b in opts:
                            if apart and near(b) < apart:
                                continue
                            if self._ok(b, hard, segs_all, poke=poke):
                                placed = b
                                break
                        if placed:
                            break
                    if placed:
                        break
                if placed:
                    break
            if placed is None:                           # knocked out on its own line (spec 1.5)
                for k in order:
                    p, q = mine[k]
                    hz = horiz((p, q))
                    if _seglen(p, q) < (w if hz else h) + 0.2:
                        continue
                    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
                    for sh in (0.0, -0.1, 0.1, -0.2, 0.2, -0.3, 0.3):
                        cx, cy = (mx + sh, my) if hz else (mx, my + sh)
                        b = Box(cx - w / 2, cy - h / 2, w, h)
                        rest = [sg for sg in segs_all if sg != (p, q)]
                        if _seglen(p, q) / 2 - abs(sh) - (w if hz else h) / 2 < 0.05:
                            continue
                        if self._ok(b, hard, rest, poke=True):
                            placed = b
                            break
                    if placed:
                        break
            if placed is None:
                self._problem(Overflows("edge %s to %s label %r" % (e.a, e.b, e.label), need="%.2f x %.2fin" % (w, h),
                                        have="no clear place beside its segments",
                                        hint="shorten it, move a node, or give the edge a lane"))
                continue
            e.label_box = placed
            hard.append(placed)

    def _badge_place(self, e: Edge, hard, segs):
        B = BADGE
        off = B / 2 + CLEAR + 0.01
        p0, p1 = e.pts[0], e.pts[1]
        ln = _seglen(p0, p1) or 1.0
        ux, uy = (p1[0] - p0[0]) / ln, (p1[1] - p0[1]) / ln
        nx, ny = -uy, ux
        for along in (B / 2 + 0.06, 0.18 + B / 2, 0.3 + B / 2, 0.45 + B / 2, 0.6 + B / 2):
            if along + B / 2 > ln - 0.04:
                break
            for sgn in (-1, 1):
                cx, cy = p0[0] + ux * along + nx * off * sgn, p0[1] + uy * along + ny * off * sgn
                b = Box(cx - B / 2, cy - B / 2, B, B)
                if self._ok(b, hard, segs):
                    return b
        S = self.nodes[e.a].body
        for gap in (0.04, 0.08):
            for cx, cy in ((S.x - gap - B / 2, S.y + B / 2 - 0.04), (S.r + gap + B / 2, S.y + B / 2 - 0.04),
                           (S.x + B / 2 - 0.04, S.y - gap - B / 2), (S.r - B / 2 + 0.04, S.y - gap - B / 2),
                           (S.x - gap - B / 2, S.b - B / 2 + 0.04), (S.r + gap + B / 2, S.b - B / 2 + 0.04)):
                b = Box(cx - B / 2, cy - B / 2, B, B)
                if math.hypot(b.cx - p0[0], b.cy - p0[1]) <= 0.40 and self._ok(b, hard, segs):
                    return b
        self._problem(Overflows("edge %s to %s step %d badge" % (e.a, e.b, e.step), need=B,
                                have="no clear place beside its source end", hint="move a node or pin a side"))
        return None

    def _block_glyph(self, e: Edge):
        """The no-entry glyph on a blocked edge, on its last segment, 0.16in before the target (spec 1.4)."""
        p, q = e.pts[-2], e.pts[-1]
        ln = _seglen(p, q)
        if ln < BLOCK_GLYPH + 0.30:
            self._problem(Overflows("blocked edge %s to %s" % (e.a, e.b), need=BLOCK_GLYPH + 0.30, have=round(ln, 3),
                                    unit="in", hint="a longer final segment holds the no-entry glyph"))
        ux, uy = (q[0] - p[0]) / max(ln, 1e-9), (q[1] - p[1]) / max(ln, 1e-9)
        d = 0.16 + BLOCK_GLYPH / 2 + 0.10
        cx, cy = q[0] - ux * d, q[1] - uy * d
        e.glyph = Box(cx - BLOCK_GLYPH / 2, cy - BLOCK_GLYPH / 2, BLOCK_GLYPH, BLOCK_GLYPH)

    # ------------------------------------------------------------------ render
    def render(self, slide, *, legend: str | None = "auto", legend_rows: int = 1) -> dict:
        """Lay out, route, place labels and badges, check, then draw. legend 'auto' draws a legend row along the foot of
        the board whenever there are steps or more than one edge kind (its row must be the board's last, empty row:
        the builder reserves it); None draws none. Returns metrics: marks, actors, nodes, edges, labelled, steps,
        crossings, kinds, frames, problems."""
        th = self.th
        with prims.use(th):
            self._layout()
            self._check_nodes()
            obstacles = self._obstacles()
            taken, used = [], {}
            for bus in self.buses:
                self._route_bus(bus, obstacles, taken, used)
            for e in self.edges:
                for nid in (e.a, e.b):
                    if nid not in self.nodes:
                        raise GeometryError("edge %s to %s" % (e.a, e.b), need="declared nodes", have=nid)
            for e in self.edges:
                if getattr(e, "bus", None):
                    continue
                try:
                    e.pts = self._route(e, obstacles, taken, used)
                except GeometryError as err:
                    if not self.draft:
                        raise
                    self.problems.append(str(err))
                    A, B = self.nodes[e.a], self.nodes[e.b]
                    e.pts = _clean([(A.body.r, A.body.cy), (B.body.x, A.body.cy), (B.body.x, B.body.cy + 0.01)])
                    if len(e.pts) < 2:
                        e.pts = [(A.body.r, A.body.cy), (A.body.r + 0.2, A.body.cy)]
                taken += list(zip(e.pts, e.pts[1:]))
                if e.kind == "blocked":
                    self._block_glyph(e)
            bus_edges = getattr(self, "bus_edges", [])
            self.edges = bus_edges + [e for e in self.edges if e not in bus_edges]
            self._validate_steps()
            self._place_labels()
            nm = self.name
            for f in sorted(self.frames.values(), key=lambda f: f.depth):
                self._draw_frame(slide, f, nm)
            for kind, data in self.overlays:
                if kind == "rail":
                    self._draw_rail(slide, data, nm)
            for i, e in enumerate(self.edges, start=1):
                self._draw_edge(slide, e, "%s.f.%d" % (nm, i))
            for n in self.nodes.values():
                self._draw_node(slide, n, nm)
            for i, e in enumerate(self.edges, start=1):
                if e.glyph is not None:
                    self._draw_block(slide, e.glyph, "%s.f.%d.block" % (nm, i))
                if e.label_box is not None:
                    gr = self._ground(e.label_box)
                    sh = txt.textbox(slide, e.label_box, e.label_paras, "%s.f.%d.label" % (nm, i), th,
                                     insets=LABEL_INS, anchor="middle", background=gr)
                    prims.set_fill(sh, gr, theme=th)
                if e.badge is not None:
                    self._badge(slide, e.badge, e.step, "%s.f.%d.step" % (nm, i))
            ks = self._kinds()
            if legend == "auto" and (self.legend or len(ks) > 1 or (ks and ks[0] != "data")):
                self._legend(slide, nm, legend_rows)
        return self.metrics()

    def _route_bus(self, bus, obstacles, taken, used):
        T = self.nodes[bus["target"]]
        S = [self.nodes[i] for i in bus["sources"]]
        right = max(max(n.body.r, n.cap.r if n.cap is not None and n.capside == "right" else n.body.r) for n in S)
        if T.body.x <= right + 0.4:
            self._problem(GeometryError("bus to %s" % T.id, need="sources left of the target by 0.40in", have="closer"))
        x = bus["x"] if bus["x"] is not None else (max(n.body.r for n in S) + T.body.x) / 2
        ys = [n.body.cy for n in S]
        lo, hi = min(ys + [T.body.cy]), max(ys + [T.body.cy])
        feeders = [((n.body.r, n.body.cy), (x, n.body.cy)) for n in S]
        trunk = ((x, lo), (x, hi))
        head = [(x, T.body.cy), (T.body.x, T.body.cy)]
        e = Edge(bus["sources"][0], bus["target"], bus["label"], bus["kind"], None, ("r", "l"), None, None, (None, 0.0),
                 None)
        fsegs = self._frame_segs()
        for seg in feeders + [trunk]:
            for b, what, nid in obstacles:
                if what == "body" and nid in bus["sources"] and seg in feeders and nid == \
                        bus["sources"][feeders.index(seg)]:
                    continue
                if _seg_hits(seg[0], seg[1], b) and not (what == "body" and nid == T.id):
                    self._problem(GeometryError("bus to %s" % T.id, need="feeders and trunk clear", have="%s %s"
                                                % (what, nid or ""), hint="pin x= between the sources and the target"))
                    break
        why = self._why(head, e, obstacles, taken, fsegs)
        if why:
            self._problem(GeometryError("bus to %s" % T.id, need="a clear headed segment", have=why))
        e.pts = head
        e.bus = {"feeders": feeders, "trunk": trunk}
        used.setdefault((T.id, "l"), []).append(0.0)
        taken += feeders + [trunk] + [tuple(head)]
        self.bus_edges = getattr(self, "bus_edges", []) + [e]

    def _validate_steps(self):
        used = sorted(e.step for e in self.edges if e.step is not None)
        if len(used) != len(set(used)):
            raise GeometryError("steps", need="each step number once", have=used)
        if used != list(range(1, len(used) + 1)):
            raise GeometryError("steps", need="1..N without a gap (P26.j)", have=used)
        if set(used) != set(self.legend):
            raise GeometryError("steps", need="a legend line for every numbered edge and no other",
                                have="edges %s, legend %s" % (used, sorted(self.legend)))

    def _ground(self, b: Box) -> str:
        best = None
        for f in self.frames.values():
            fill = {"panel": "card", "band": "card"}.get(f.kind) or f.opt.get("fill")
            if fill and f.box.contains(b, tol=1e-6):
                if best is None or f.box.w * f.box.h < best[0]:
                    best = (f.box.w * f.box.h, fill)
        return best[1] if best else "paper"

    def _kinds(self) -> list:
        return [k for k in EDGE_KINDS if any(e.kind == k for e in self.edges)]

    # ------------------------------------------------------------------ drawing
    def _shape(self, slide, prst, box, name, *, fill=None, line=None, weight=0.75, dash=None, radius=None):
        th = self.th
        sh = prims._add(slide, prst, box, name)
        if radius is not None:
            sh.adjustments[0] = prims._adj(radius, box)
        prims.set_fill(sh, fill, theme=th)
        if line is None:
            prims.set_line(sh, None, theme=th)
        else:
            prims.set_line(sh, line, weight, theme=th, dash=dash)
        return sh

    def _draw_frame(self, slide, f: Frame, nm):
        th = self.th
        b = f.box
        base = "%s.g.%s" % (nm, f.id)
        if f.kind == "section":
            prims.hairline(slide, (b.x, b.y + 0.02), (b.r, b.y + 0.02), role="hairline", name=base + ".rule", theme=th)
            self._frame_label(slide, f, base, "paper")
            return
        if f.kind == "lane":
            paras = [Para((Run(f.label, role="ink-muted", bold=True, size=GROUP_PT),))]
            txt.textbox(slide, f.words, paras, base + ".label", th, background="paper")
            return
        fill = {"panel": "card", "band": "card"}.get(f.kind) or f.opt.get("fill")
        line, weight, dash = {"region": ("hairline" if fill else "rule-strong", 0.75, None),
                              "boundary": ("rule-strong", 0.75, "dash"),
                              "zone": ("accent-deep", 1.0, "dash"), "panel": ("hairline", 0.75, None),
                              "band": ("rule-strong", 0.75, None), "segmented": ("rule-strong", 0.75, None)}[f.kind]
        rounded = f.kind in ("region", "panel", "band", "segmented")
        sh = self._shape(slide, "ROUNDED_RECTANGLE" if rounded else "RECTANGLE", b,
                         "%s.%s" % (base, "band" if f.kind == "band" else "frame"), fill=fill, line=line,
                         weight=weight, dash=dash, radius=RADIUS if rounded else None)
        prims._drop_text(sh)
        ooxml.finish(sh)
        if f.kind in ("region", "band"):
            bar = Box(b.x, b.y, b.w, BAR_H)
            sh = prims._add(slide, "ROUND_2_SAME_RECTANGLE", bar, base + ".bar")
            sh.adjustments[0] = prims._adj(TAB_RADIUS, bar)
            sh.adjustments[1] = 0.0
            prims.set_fill(sh, "navy", theme=th)
            prims.set_line(sh, None, theme=th)
            prims._drop_text(sh)
            ooxml.finish(sh)
            paras = [Para((Run(f.label, role=prims.ON_FILL["navy"], bold=True, size=BAR_PT),), align="center")]
            lh = math.ceil(txt.need_height(paras, b.w - 0.2, th) * 10000 + 1) / 10000.0
            txt.textbox(slide, Box(b.x + 0.1, b.y + BAR_H / 2 - lh / 2, b.w - 0.2, lh), paras, base + ".label", th,
                        background="navy")
            return
        if f.kind == "segmented":
            n = len(f.cells)
            xs, c = [b.x], f.cols[0]
            for _lab, span in f.cells[:-1]:
                c += span
                xs.append(self.colx[c])
            xs.append(b.r)
            for k in range(1, n):
                # the divider breaks round a node centred on it (the registry hinge) and round its caption
                cuts = sorted((max(b.y, min(bx_.y for bx_ in (nd.body, nd.cap) if bx_ is not None) - 0.05),
                               min(b.b, max(bx_.b for bx_ in (nd.body, nd.cap) if bx_ is not None) + 0.05))
                              for nd in self.nodes.values()
                              if any(bx_ is not None and bx_.x < xs[k] < bx_.r and bx_.y < b.b and bx_.b > b.y
                                     for bx_ in (nd.body, nd.cap)))
                y, part = b.y, 0
                for c0, c1 in cuts + [(b.b, b.b)]:
                    if c0 - y > 0.06:
                        prims.hairline(slide, (xs[k], y), (xs[k], c0), role="rule-strong",
                                       name="%s.cell.%d.rule.%d" % (base, k, part), theme=th)
                        part += 1
                    y = max(y, c1)
            prims.hairline(slide, (b.x, b.y + HEAD_SECTION), (b.r, b.y + HEAD_SECTION), role="hairline",
                           name=base + ".head.rule", theme=th)
            for k, (lab, _span) in enumerate(f.cells):
                paras = [Para((Run(lab, role="ink-deep", bold=True, size=GROUP_PT),), align="center")]
                w = xs[k + 1] - xs[k] - 0.16
                lh = math.ceil(txt.need_height(paras, w, th) * 10000 + 1) / 10000.0
                if lh > HEAD_SECTION - 0.04:
                    self._problem(Overflows("segment %s cell %r" % (f.id, lab), need=1, have=2, unit="lines"))
                txt.textbox(slide, Box(xs[k] + 0.08, b.y + (HEAD_SECTION - lh) / 2, w, lh), paras,
                            "%s.cell.%d.label" % (base, k), th)
            return
        self._frame_label(slide, f, base, fill or "paper")

    def _icon_w(self, f: Frame) -> float:
        """A corner mark's width at 0.24in tall: square for a service icon, its own aspect for a wordmark (to 1.2in)."""
        ik, _, key = f.opt["icon"].partition(":")
        if ik != "mark":
            return 0.24
        e = icons.mark_registry()[key]
        blob = (icons.marks_dir() / e["file"]).read_bytes()
        w, h = icons.svg_size(blob) if e["file"].lower().endswith(".svg") else icons._png_size(blob)
        return min(1.2, 0.24 * (w / h if h else 1.0))

    def _frame_label(self, slide, f: Frame, base, bg):
        paras = [Para((Run(f.label, role="ink-deep", bold=True, size=GROUP_PT),))]
        iw = self._icon_w(f) if f.opt.get("icon") else 0.0
        words = f.words if iw <= 0.3 else Box(f.words.x, f.words.y, f.words.w - 0.10 - iw,
                                              measure.line_in(GROUP_PT, _face(self.th, True)) * measure.SLACK + 0.02)
        txt.textbox(slide, words, paras, base + ".label", self.th, background=bg)
        if f.opt.get("icon"):                                # the product's mark on the corner: notation, *-tab
            ik, _, key = f.opt["icon"].partition(":")
            if iw <= 0.3:
                ib = Box(f.box.x + 0.06, max(f.box.y + 0.05, words.cy - 0.12), iw, 0.24)
            else:
                ib = Box(words.r + 0.10, max(f.box.y + 0.05, words.cy - 0.12), iw, 0.24)
            if ik == "vendor":
                icons.vendor(slide, key, ib, name="%s-tab" % base.replace(".", "-"),
                             alt=f.label.split("·")[0].strip(), theme=self.th)
            else:
                icons.mark(slide, key, ib, name="%s-tab" % base.replace(".", "-"))

    def _rail_geom(self, d):
        """(label box, rule from, rule to, drops) of a rail, measured: the label right-aligned before the first chip's
        column, the rule from the first chip to the last, one drop per chip up to the frame above it."""
        th = self.th
        y = self.rowy[d["row"]] + self.rowh[d["row"]] / 2
        chips = [self.nodes[c] for c in d["chips"]]
        c0, c1 = d["cols"]
        x0 = chips[0].body.cx if chips else self.colx[c0] + EDGE_IN
        x1 = chips[-1].body.cx if chips else self.colx[c1 + 1] - EDGE_IN
        paras = [Para((Run(d["label"], role="ink-muted", bold=True, size=ROLE_PT),), align="right")]
        lw = _tw(d["label"], ROLE_PT, th, True) + 0.04
        lh = math.ceil(txt.need_height(paras, lw, th) * 10000 + 1) / 10000.0
        lx = (chips[0].body.x if chips else x0) - 0.10 - lw
        if lx < self.box.x:
            self._problem(Overflows("rail %s label" % d["id"], need=round(self.box.x - lx, 3), have=0, unit="in",
                                    hint="the rail's label needs free room left of its first chip"))
        drops = []
        if d["drops"]:
            for n in chips:
                above = [f for f in self.frames.values() if f.kind not in ("section", "lane")
                         and f.box.x < n.body.cx < f.box.r
                         and f.box.b <= n.body.y + 1e-6]
                if above:
                    f = max(above, key=lambda f: f.box.b)
                    if n.body.y - f.box.b > 0.04:
                        drops.append(((n.body.cx, f.box.b), (n.body.cx, n.body.y)))
        return Box(lx, y - lh / 2, lw, lh), paras, (x0, y), (x1, y), drops

    def _draw_rail(self, slide, d, nm):
        th = self.th
        lab, paras, p, q, drops = self._rail_geom(d)
        txt.textbox(slide, lab, paras, "%s.rail.%s.label" % (nm, d["id"]), th)
        if q[0] - p[0] > 0.05:
            prims.hairline(slide, p, q, role="rule-strong", weight_pt=1.0, name="%s.rail.%s" % (nm, d["id"]), theme=th)
        for k, (a, b) in enumerate(drops):
            prims.hairline(slide, a, b, role="rule-strong", weight_pt=1.0, name="%s.rail.%s.drop.%d" % (nm, d["id"], k),
                           theme=th)

    def _draw_edge(self, slide, e: Edge, name):
        th = self.th
        k = EDGE_KINDS[e.kind]
        if getattr(e, "bus", None):                           # unheaded feeders and trunk, in the line's role
            for j, (a, b) in enumerate(e.bus["feeders"] + [e.bus["trunk"]]):
                if _seglen(a, b) > 0.01:
                    sh = prims._connector(slide, a, b, "%s.bus.%d" % (name, j))
                    prims.set_line(sh, LINE_ROLE, LINE_PT, theme=th, dash=k["dash"])
                    ooxml.finish(sh)
        if len(e.pts) == 2:
            sh = prims.connect(slide, e.pts[0], e.pts[1], head="end", dash=k["dash"], role=k["role"], weight_pt=LINE_PT,
                               name=name, theme=th)
        else:
            sh = prims.elbow(slide, e.pts, head="end", dash=k["dash"], role=k["role"], weight_pt=LINE_PT, name=name,
                             theme=th)
        return sh

    def _draw_block(self, slide, box: Box, name):
        th = self.th
        sh = self._shape(slide, "OVAL", box.inset(-0.01), name + ".ground", fill="paper")
        prims._drop_text(sh)
        ooxml.finish(sh)
        glyphs.glyph(slide, "ban", box, role="accent", shape_name=name, theme=th)

    def _badge(self, slide, box: Box, n: int, name):
        th = self.th
        ink = prims.ON_FILL.get(BADGE_FILL, "paper")
        paras = [Para((Run(str(n), role=ink, bold=True, size=BADGE_PT),), align="center")]
        txt.check_contrast(name, paras, th, BADGE_FILL)
        sh = prims._add(slide, "OVAL", box, name)
        prims.set_fill(sh, BADGE_FILL, theme=th)
        prims.set_line(sh, None, theme=th)
        txt.write(sh.text_frame, paras, th, measure.ZERO, anchor="middle", background=BADGE_FILL)
        ooxml.finish(sh)
        return sh

    def _text_shape(self, slide, prst, box, name, paras, *, fill, line=None, weight=0.75, dash=None, radius=None,
                    ins=0.04, lead=0.0):
        th = self.th
        txt.check_fit(name, paras, (box.w - 2 * ins - lead, box.h), th)
        sh = self._shape(slide, prst, box, name, fill=fill, line=line, weight=weight, dash=dash, radius=radius)
        txt.write(sh.text_frame, paras, th, measure.Insets(ins + lead, 0.0, ins, 0.0), anchor="middle",
                  background=fill)
        ooxml.finish(sh)
        return sh

    def _draw_node(self, slide, n: Node, nm):
        th = self.th
        base = "%s.n.%s" % (nm, n.id)
        b = n.body
        if n.kind == "mark":
            kind, _, key = n.mark.partition(":")
            if kind == "vendor":
                pic = icons.vendor(slide, key, b, name="%s-n-%s" % (nm, n.id), alt=n.name, theme=th)
            elif kind == "mark":
                big = b
                ink = getattr(n, "ink", None)
                if ink is not None:
                    l, t, r, bb = ink[:4]
                    big = Box(b.x, b.y, b.w / max(0.05, r - l), b.h / max(0.05, bb - t))
                pic = icons.mark(slide, key, big, name="%s-n-%s" % (nm, n.id))
            else:
                pic = None
                glyphs.glyph(slide, key, b, role="ink-strong", shape_name=base + ".icon", theme=th)
            ink = getattr(n, "ink", None)
            if pic is not None and ink is not None:
                arch._crop_to_ink(pic, ink, b)
        elif n.kind == "gate":
            prst, gl = GATE_KINDS[n.opt["gate"]]
            sh = self._shape(slide, prst, b, base + ".gate", fill="accent")
            prims._drop_text(sh)
            ooxml.finish(sh)
            s = 0.15 if prst == "DIAMOND" else 0.18
            glyphs.glyph(slide, gl, Box(b.cx - s / 2, b.cy - s / 2, s, s), role="on-accent",
                         shape_name=base + ".gate.icon", theme=th)
        elif n.kind == "stop":
            glyphs.glyph(slide, "ban", b, role="accent", shape_name=base + ".stop", theme=th)
        elif n.kind == "activity":
            self._text_shape(slide, "ROUNDED_RECTANGLE", b, base + ".activity", n.paras, fill="paper", line="ink-muted",
                             dash="dash", radius=RADIUS)
        elif n.kind == "terminal":
            self._text_shape(slide, "ROUNDED_RECTANGLE", b, base + ".terminal", n.paras, fill="ink-deep", radius=b.h / 2)
        elif n.kind == "state":
            intr = n.opt.get("interrupt")
            lead = 0.24 if n.opt.get("glyph") else 0.0
            self._text_shape(slide, "ROUNDED_RECTANGLE", b, base + ".state", n.paras, fill="paper",
                             line="accent-deep" if intr else "rule-strong", weight=1.0, dash="dash" if intr else None,
                             radius=RADIUS, lead=lead)
            if lead:
                s = 0.18
                glyphs.glyph(slide, n.opt["glyph"], Box(b.x + 0.08, b.cy - s / 2, s, s),
                             role="accent-deep" if intr else "ink-strong", shape_name=base + ".state.icon", theme=th)
        elif n.kind == "chip":
            k = n.opt["chip"]
            if k == "token":
                self._text_shape(slide, "ROUNDED_RECTANGLE", b, base + ".token", n.paras, fill="ink-deep",
                                 radius=b.h / 2)
            elif k == "more":
                self._text_shape(slide, "ROUNDED_RECTANGLE", b, base + ".more", n.paras, fill="card", line="hairline",
                                 radius=b.h / 2)
            elif k == "dataset":
                self._text_shape(slide, "RECTANGLE", b, base + ".dataset", n.paras, fill="paper", line="rule-strong")
            else:
                self._text_shape(slide, "ROUNDED_RECTANGLE", b, base + ".event", n.paras, fill="card",
                                 line="rule-strong", radius=0.04)
        if n.cap is not None:
            txt.textbox(slide, n.cap, n.paras, base + ".caption", th, background=self._ground(n.cap))

    def _legend(self, slide, nm, rows):
        """One row along the board's foot: the numbered steps, then the edge-kind key. The board's last row must be
        free of nodes; it holds the legend."""
        th = self.th
        ri = len(self.rows) - 1
        if any(n.cell[1] == ri for n in self.nodes.values()):
            self._problem(GeometryError("legend", need="the board's last row free of nodes", have="nodes in it",
                                        hint="add a fixed row of about 0.32in per legend line at the foot"))
        y0 = self.rowy[ri]
        hrow = self.rowh[ri]
        items = sorted(self.legend.items())
        kinds = self._kinds() if len(self._kinds()) > 1 or (self._kinds() and self._kinds()[0] != "data") else []
        face = _face(th)
        entries = [("step", n, t) for n, t in items] + [("key", k, self.keys.get(k, EDGE_KINDS[k]["key"]))
                                                         for k in kinds]
        # greedy lines: steps first, the key after them; a new line when the next entry would cross the board
        lines, cur, x = [[]], None, self.box.x + EDGE_IN
        for kind, k, t in entries:
            tw = measure.width_in(t, LEGEND_PT, face) * measure.SLACK + 0.04
            lead = BADGE + 0.08 if kind == "step" else 0.50
            if lines[-1] and x + lead + tw > self.box.r + 1e-6:
                lines.append([])
                x = self.box.x + EDGE_IN
            lines[-1].append((kind, k, t, tw, lead))
            x += lead + tw + 0.30
        rows = max(rows, len(lines))
        lh = hrow / len(lines)
        if lh < 0.24:
            self._problem(Overflows("legend", need=round(0.26 * len(lines), 3), have=round(hrow, 3), unit="in",
                                    hint="a taller legend row (about 0.28in a line), or shorter step texts"))
        for li, line in enumerate(lines):
            yc = y0 + lh * li + lh / 2
            x = self.box.x + EDGE_IN
            for kind, k, t, tw, lead in line:
                paras = [Para((Run(t, role="ink" if kind == "step" else "ink-muted", size=LEGEND_PT),))]
                h = math.ceil(txt.need_height(paras, tw, th) * 10000 + 1) / 10000.0
                if kind == "step":
                    self._badge(slide, Box(x, yc - BADGE / 2, BADGE, BADGE), k, "%s.legend.%d.step" % (nm, k))
                    txt.textbox(slide, Box(x + lead, yc - h / 2, tw, h), paras, "%s.legend.%d.text" % (nm, k), th)
                else:
                    ek = EDGE_KINDS[k]
                    sh = prims._connector(slide, (x, yc), (x + 0.40, yc), "state.%s.legend.key.%s" % (nm, k))
                    prims.set_line(sh, ek["role"], LINE_PT, theme=th, dash=ek["dash"])
                    ooxml.finish(sh)
                    if k == "blocked":
                        self._draw_block(slide, Box(x + 0.20 - 0.08, yc - 0.08, 0.16, 0.16),
                                         "state.%s.legend.key.%s.glyph" % (nm, k))
                    txt.textbox(slide, Box(x + lead, yc - h / 2, tw, h), paras, "%s.legend.key.%s.text" % (nm, k), th)
                x += lead + tw + 0.30

    # ------------------------------------------------------------------ metrics
    def metrics(self) -> dict:
        ns = list(self.nodes.values())
        marks = [n for n in ns if n.kind == "mark" and n.mark.split(":")[0] in ("vendor", "mark")
                 and not arch.Diagram.is_actor(n.mark)]
        segs = [list(zip(e.pts, e.pts[1:])) for e in self.edges]
        crossings = 0
        for i in range(len(segs)):
            for j in range(i + 1, len(segs)):
                crossings += sum(1 for s in segs[i] for t in segs[j] if _cross(*s, *t))
        return {"marks": len(marks), "actors": sum(1 for n in ns if n.kind == "mark" and arch.Diagram.is_actor(n.mark)),
                "nodes": len(ns), "edges": len(self.edges),
                "labelled": sum(1 for e in self.edges if e.label_box is not None),
                "steps": len(self.legend), "crossings": crossings, "kinds": self._kinds(),
                "gates": sum(1 for n in ns if n.kind == "gate"), "frames": len(self.frames),
                "problems": list(self.problems)}


# =============================================================================================== the five types
# Each builder lays one anatomy out on a Board from a content dict and returns the Board, unrendered: call
# b.render(slide). A node is a tuple (id, mark, name, role) with mark 'vendor:<key>' or 'mark:<key>' (role may be
# None). Step texts are listed in path order; the builder numbers the path. Labels name what moves (1 to 4 words).

def _need(node, th, side=ICON, bold=True) -> float:
    """The width a below-captioned node needs: its widest caption line on one line, plus the gutter."""
    _id, _mk, name, role = node
    return max(side, _tw(name, NAME_PT, th, bold) + 0.04, _tw(role or "", ROLE_PT, th) + 0.04) + CAP_GUTTER


def _put(b, node, cell, **kw):
    nid, mark, name, role = node
    return b.mark(nid, mark, name, role, cell=cell, **kw)


def cicd(box: Box, theme, spec: dict, *, name: str = "cicd", draft: bool = False) -> Board:
    """CI/CD and release (spec 3.6): accounts as columns, gates as nodes on the promotion path with their fail exits,
    one digest riding a rail under every account, a rollback loop over the prod waves, a blocked manual path.

    spec: source {label, repo, ci, push}; ci_gate {label, fail}; tooling {label, fact, registry, pipeline, signer?,
    sign, handoff}; envs [{id, label, service, evidence?, evidence_label?, deploy?}] (1 to 3); gates [{kind:
    quality|approval, label, fail}] one per env (the last leads to prod); prod {label, fact, waves [node, ...] (1 to
    3), bake {label, fail}, monitor?, monitor_label}; blocked (node)?; digest {label, text}; steps [text, ...];
    keys {kind: legend text}?"""
    th = prims.theme_of(theme)
    envs, gates, prod = spec["envs"], spec["gates"], spec["prod"]
    waves = prod["waves"]
    if not (1 <= len(envs) <= 3) or len(gates) != len(envs) or not (1 <= len(waves) <= 3):
        raise GeometryError("cicd", need="1 to 3 envs, one gate per env, 1 to 3 prod waves",
                            have=(len(envs), len(gates), len(waves)))
    G = 0.56
    src, tool = spec["source"], spec["tooling"]
    cols = [max(1.48, _need(src["ci"], th) + 0.28), G,
            max(2.36, 2 * max(_need(tool["registry"], th), _need(tool["pipeline"], th)) + 0.28)]
    env_c = []
    for k, e in enumerate(envs):
        env_c.append(len(cols))
        bar = _tw(e["label"] + (" · " + e["fact"] if e.get("fact") else ""), BAR_PT, th, True) + 0.36
        cols.append(max(1.5 if e.get("evidence") else 1.3, _need(e["service"], th) + 0.28, bar))
        cols.append(G)
    wave_c = []
    for k, w in enumerate(waves):
        wave_c.append(len(cols))
        cols.append(max(1.15, _need(w, th) + 0.14))
        if k < len(waves) - 1:
            cols.append(G)
    if spec.get("blocked"):
        cols.append(max(1.08, _need(spec["blocked"], th)))
    if sum(cols) > box.w + 0.01:                              # columns are measured minimums: refuse, never shrink
        err = Overflows("cicd width", need=round(sum(cols), 2), have=round(box.w, 2), unit="in",
                        hint="two environments and two waves fit a wide slide; drop the blocked path, an environment "
                             "or a wave, or split promotion and release onto two slides")
        if not draft:
            raise err
    rows = [HEAD_BAR, ("auto", 0.3), "auto", ("auto", 1), "auto", 0.08, 0.40, 0.56]
    b = Board(box, th, cols=cols, rows=rows, name=name, draft=draft, keys=spec.get("keys"))
    SUP, MAIN, RAIL = 2, 4, 6
    b.frame("src", "lane", src["label"], cols=(0, 0), rows=(0, 4))
    b.frame("tool", "region", tool["label"], fact=tool.get("fact"), cols=(2, 2), rows=(0, 4), fill="card")
    for k, e in enumerate(envs):
        b.frame(e["id"], "region", e["label"], fact=e.get("fact"), cols=(env_c[k], env_c[k]), rows=(0, 4))
    b.frame("prod", "region", prod["label"], fact=prod.get("fact"), cols=(wave_c[0], wave_c[-1]), rows=(0, 4))
    repo, ci = src["repo"], src["ci"]
    _put(b, repo, (0, SUP), align="left")
    _put(b, ci, (0, MAIN), align="right")
    b.gate("cigate", "quality", spec["ci_gate"]["label"], cell=(1, MAIN))
    b.stop("cistop", spec["ci_gate"]["fail"], cell=(1, SUP))
    reg, pipe = tool["registry"], tool["pipeline"]
    _put(b, reg, (2, MAIN), slot=(0, 2))
    _put(b, pipe, (2, MAIN), slot=(1, 2))
    if tool.get("signer"):
        _put(b, tool["signer"], (2, SUP), slot=(1, 2))
    for k, e in enumerate(envs):
        _put(b, e["service"], (env_c[k], MAIN), align="right" if e.get("evidence") else "center")
        if e.get("evidence"):
            _put(b, e["evidence"], (env_c[k], SUP), align="left")
        g = gates[k]
        gid = "gate%d" % (k + 1)
        b.gate(gid, g["kind"], g["label"], cell=(env_c[k] + 1, MAIN))
        if g["kind"] == "quality":
            b.stop("stop%d" % (k + 1), g["fail"], cell=(env_c[k] + 1, SUP))
    for k, w in enumerate(waves):
        _put(b, w, (wave_c[k], MAIN))
        if k < len(waves) - 1:
            b.gate("bake%d" % (k + 1), "health", prod["bake"]["label"], cell=(wave_c[k] + 1, MAIN))
    if prod.get("monitor"):
        mc = wave_c[0] + 1 if len(waves) > 1 else wave_c[0]
        _put(b, prod["monitor"], (mc, SUP), span=(wave_c[0], wave_c[-1]))
    if spec.get("blocked"):
        _put(b, spec["blocked"], (len(cols) - 1, SUP))
    chips = [("t-tool", spec["digest"]["text"], 2)] + [("t-%s" % e["id"], spec["digest"]["text"], env_c[k])
                                                       for k, e in enumerate(envs)]
    chips.append(("t-prod", spec["digest"]["text"], (wave_c[0], wave_c[-1])))
    b.rail("digest", spec["digest"]["label"], row=RAIL, cols=(2, wave_c[-1]), chips=chips)
    step = iter(range(1, 13))
    b.edge(repo[0], ci[0], src.get("push"), step=next(step))
    b.edge(ci[0], "cigate")
    b.edge("cigate", reg[0], step=next(step))
    b.edge("cigate", "cistop", "fail", kind="feedback")
    if tool.get("signer"):
        b.edge(tool["signer"][0], reg[0], tool.get("sign"))
    b.edge(reg[0], pipe[0], tool.get("handoff"))
    b.edge(pipe[0], envs[0]["service"][0], envs[0].get("deploy", "deploy"), step=next(step))
    for k, e in enumerate(envs):
        svc = e["service"][0]
        if e.get("evidence"):
            b.edge(svc, e["evidence"][0], e.get("evidence_label"), sides=("t", "r"))
        gid = "gate%d" % (k + 1)
        b.edge(svc, gid)
        nxt = envs[k + 1]["service"][0] if k + 1 < len(envs) else waves[0][0]
        b.edge(gid, nxt, step=next(step))
        if gates[k]["kind"] == "quality":
            b.edge(gid, "stop%d" % (k + 1), "fail", kind="feedback")
        else:
            b.edge(gid, svc, gates[k]["fail"], kind="feedback", sides=("t", "t"))
    for k in range(len(waves) - 1):
        bid = "bake%d" % (k + 1)
        b.edge(waves[k][0], bid)
        b.edge(bid, waves[k + 1][0], step=next(step))
        b.edge(bid, waves[k][0], prod["bake"]["fail"], kind="feedback", sides=("t", "t"))
    if prod.get("monitor"):
        b.edge(waves[-1][0], prod["monitor"][0], prod.get("monitor_label"))
    if spec.get("blocked"):
        b.edge(spec["blocked"][0], waves[-1][0], kind="blocked", sides=("l", "t"))
    texts = list(spec["steps"])
    n = sum(1 for e in b.edges if e.step)
    if len(texts) != n:
        raise GeometryError("cicd steps", need="%d step texts in path order" % n, have=len(texts))
    b.steps({k + 1: t for k, t in enumerate(texts)})
    return b


def mlops(box: Box, theme, spec: dict, *, name: str = "mlops", draft: bool = False) -> Board:
    """MLOps and LLMOps (spec 3.7): one platform frame of two zones, the registry hinged on the line between them, an
    offline eval panel feeding a quality gate with its revise exit, approval and a canary gate on the release path, and
    online eval sampling traces back to the dataset on the perimeter.

    spec: build {label, activity, repo, runner}; eval {label, fact, dataset, dataset_label, judge, judge_label,
    candidate?, candidate_label, scores?}; gate {label, revise}; registry (node), register?; release {label, pipeline,
    promote, notify? (node), notify_label, approver? (node), approve_label, approval (gate label), flag, monitor?,
    monitor_label, canary (gate label), service, online, online_label, loop_label}; steps [7 texts]; keys?"""
    th = prims.theme_of(theme)
    bd, ev, rel = spec["build"], spec["eval"], spec["release"]
    cols = [1.0, 1.05, 1.15, 1.2, 0.62, 0.6, 0.6, 1.15, 0.62, 1.15, 0.62, 1.15]
    rows = [0.40, HEAD_SECTION, ("auto", 0.15), HEAD_LABEL, "auto", "auto", "auto", ("auto", 1), "auto", 0.42, 0.56]
    b = Board(box, th, cols=cols, rows=rows, name=name, draft=draft, keys=spec.get("keys"))
    MAIN = 8
    b.frame("ops", "segmented", "platform", cols=(0, 11), rows=(1, 9), cells=[(bd["label"], 6), (rel["label"], 6)])
    b.frame("eval", "panel", ev["label"], fact=ev.get("fact"), cols=(2, 5), rows=(3, 6))
    b.activity("edit", bd["activity"], cell=(0, MAIN))
    _put(b, bd["repo"], (1, MAIN))
    _put(b, ev["dataset"], (1, 4))
    _put(b, bd["runner"], (2, MAIN))
    _put(b, ev["judge"], (3, 5))
    if ev.get("candidate"):
        _put(b, ev["candidate"], (3, 6))
    if ev.get("scores"):
        _put(b, ev["scores"], (4, 5), span=(4, 5))
    b.gate("evalgate", "quality", spec["gate"]["label"], cell=(4, MAIN), caption="above")
    _put(b, spec["registry"], (6, MAIN), hinge=6)
    _put(b, rel["pipeline"], (7, MAIN))
    if rel.get("notify"):
        _put(b, rel["notify"], (7, 6), caption="left")
    if rel.get("approver"):
        _put(b, rel["approver"], (8, 4), caption="right")
    b.gate("approval", "approval", rel["approval"], cell=(8, MAIN))
    _put(b, rel["flag"], (9, MAIN))
    if rel.get("monitor"):
        _put(b, rel["monitor"], (10, 6), caption="left")
    b.gate("canary", "traffic", rel["canary"], cell=(10, MAIN))
    _put(b, rel["service"], (11, MAIN))
    _put(b, rel["online"], (10, 4), span=(10, 11))
    run, svc, reg = bd["runner"][0], rel["service"][0], spec["registry"][0]
    b.edge("edit", bd["repo"][0], step=1)
    b.edge(bd["repo"][0], run, step=2)
    b.edge(ev["dataset"][0], run, ev.get("dataset_label"), ports=(0, -0.125))
    b.edge(run, ev["judge"][0], ev.get("judge_label"), ports=(0, None))
    if ev.get("candidate"):
        b.edge(run, ev["candidate"][0], ev.get("candidate_label"), ports=(0.125, None))
    if ev.get("scores"):
        b.edge(ev["judge"][0], ev["scores"][0])
    b.edge(run, "evalgate")
    b.edge("evalgate", reg, step=3)
    b.edge("evalgate", "edit", spec["gate"]["revise"], kind="feedback", sides=("b", "b"))
    b.edge(reg, rel["pipeline"][0], rel.get("promote"), step=4)
    if rel.get("notify"):
        b.edge(rel["pipeline"][0], rel["notify"][0], rel.get("notify_label"))
        if rel.get("approver"):
            b.edge(rel["notify"][0], rel["approver"][0], rel.get("relay_label"))
    if rel.get("approver"):
        b.edge(rel["approver"][0], "approval", rel.get("approve_label"))
    b.edge(rel["pipeline"][0], "approval")
    b.edge("approval", rel["flag"][0], step=5)
    b.edge(rel["flag"][0], "canary")
    if rel.get("monitor"):
        b.edge(rel["monitor"][0], "canary", rel.get("monitor_label"))
    b.edge("canary", svc, step=6)
    b.edge(svc, rel["online"][0], rel.get("online_label"), step=7)
    b.edge(rel["online"][0], ev["dataset"][0], rel.get("loop_label"), kind="feedback", sides=("t", "t"),
           lane=("row", 0))
    texts = list(spec["steps"])
    if len(texts) != 7:
        raise GeometryError("mlops steps", need="7 step texts in path order", have=len(texts))
    b.steps({k + 1: t for k, t in enumerate(texts)})
    return b


def medallion(box: Box, theme, spec: dict, *, name: str = "medallion", draft: bool = False) -> Board:
    """Data flow and lineage (spec 3.9): sources as a stacked list, ingest by stream and by batch, the medallion as one
    container of three adjoining cells, the stream path above the batch path landing on Serve, one excluded record at
    Silver, a processing and governance band, and a lineage inset of datasets named by job with a +N more chip.

    spec: platform {label, fact}; sources [node, ...] (the first is the stream source); stream_label?; ingest {stream,
    batch, batch_label?}; stream_hop (node, captioned beside it); hops {stream, archive, index, append, refine,
    certify}; cells [3 labels]; stores [bronze, silver, gold nodes]; excluded {label, edge}; serve {index, ledger,
    query} nodes with labels {index, ledger, query}; consume [3 nodes] with labels; band {label, marks [8 nodes]};
    lineage {fact, datasets [(id, prefix, name, row, col)], edges [(a, b, job)], more}; keys?"""
    th = prims.theme_of(theme)
    cols = [1.72, 1.25, 1.42, 1.6, 1.42, 1.3, 1.4]
    rows = [HEAD_LABEL, HEAD_SECTION, 0.24, "auto", "auto", "auto", ("auto", 1), BAR_H + 0.08, "auto", "auto", 0.22,
            0.26, "auto", "auto", 0.26]
    b = Board(box, th, cols=cols, rows=rows, name=name, draft=draft, keys=spec.get("keys"))
    S, B_, L = 3, 4, 5
    b.frame("src", "lane", spec.get("sources_label", "Sources"), cols=(0, 0), rows=(0, 5))
    b.frame("use", "lane", spec.get("consume_label", "Consume"), cols=(6, 6), rows=(0, 5))
    pl = spec["platform"]
    b.frame("plat", "boundary", pl["label"], fact=pl.get("fact"), cols=(1, 5), rows=(0, 9))
    b.frame("ing", "lane", spec.get("ingest_label", "Ingest"), cols=(1, 1), rows=(1, 5))
    b.frame("srv", "lane", spec.get("serve_label", "Serve"), cols=(5, 5), rows=(1, 5))
    b.frame("med", "segmented", "medallion", cols=(2, 4), rows=(1, 5), cells=list(spec["cells"]))
    band = spec["band"]
    b.frame("ops", "band", band["label"], cols=(1, 5), rows=(7, 9))
    srcs = spec["sources"]
    b.stack(srcs, cell=(0, S), rows=(S, L), cap_w=1.18)
    ing, hops, sv, use = spec["ingest"], spec["hops"], spec["serve"], spec["consume"]
    _put(b, ing["stream"], (1, S))
    _put(b, ing["batch"], (1, B_))
    _put(b, spec["stream_hop"], (2, S), caption="right", align="left")
    bronze, silver, gold = spec["stores"]
    _put(b, bronze, (2, B_))
    _put(b, silver, (3, B_))
    b.stop("excluded", spec["excluded"]["label"], cell=(3, L), caption="right", cap_w=1.1)
    _put(b, gold, (4, B_))
    _put(b, sv["index"], (5, S))
    _put(b, sv["ledger"], (5, B_))
    _put(b, sv["query"], (5, L))
    for k, nd in enumerate(use):
        _put(b, nd, (6, (S, B_, L)[k]))
    marks = band["marks"]
    if len(marks) > 8:
        raise GeometryError("medallion band", need="at most 8 marks", have=len(marks))
    for k, nd in enumerate(marks):                         # four to a row, one per column of the platform
        _put(b, nd, (1 + k % 4, 8 + k // 4), size=0.30, caption="right", cap_w=1.15, align="left")
    lin = spec["lineage"]
    b.frame("lin", "panel", "Lineage", fact=lin["fact"], cols=(1, 5), rows=(11, 13))
    for did, prefix, dname, r, c in lin["datasets"]:
        b.chip(did, dname, kind="dataset", prefix=prefix, cell=(c, 12 + r), span=(c, c + 1) if c == 1 else None)
    last = lin["datasets"][-1]
    b.chip("more", lin["more"], kind="more", cell=(5, 12))
    b.edge(srcs[0][0], ing["stream"][0], kind="async")
    b.bus([e[0] for e in srcs[1:]], ing["batch"][0])
    b.edge(ing["stream"][0], spec["stream_hop"][0], hops.get("stream"), kind="async")
    b.edge(spec["stream_hop"][0], bronze[0], hops.get("archive"), kind="async")
    b.edge(spec["stream_hop"][0], sv["index"][0], hops.get("index"), kind="async", sides=("t", "t"), lane=("row", 2))
    b.edge(ing["batch"][0], bronze[0], hops.get("append"))
    b.edge(bronze[0], silver[0], hops.get("refine"))
    b.edge(bronze[0], "excluded", spec["excluded"].get("edge"))
    b.edge(silver[0], gold[0], hops.get("certify"))
    lab = spec.get("serve_labels", {})
    b.edge(gold[0], sv["index"][0], lab.get("index"))
    b.edge(gold[0], sv["ledger"][0], lab.get("ledger"))
    b.edge(gold[0], sv["query"][0], lab.get("query"), sides=("r", "l"))
    ul = spec.get("consume_labels", [None, None, None])
    for k, key in enumerate(("index", "ledger", "query")):
        if k < len(use):
            b.edge(sv[key][0], use[k][0], ul[k])
    for a, c, job in lin["edges"]:
        b.edge(a, c, job)
    b.edge(last[0], "more")
    return b


def events(box: Box, theme, spec: dict, *, name: str = "events", draft: bool = False) -> Board:
    """Event-driven integration on a router (spec 3.11, EventBridge): producers publish event types (chips on the bus,
    one row each), one rule per event type to its target, follow-on targets beside it, a schema registry over the bus
    with control lines to the first producer and the first target, and one dead-letter queue on a failing target.

    spec: bus {label, fact, mark}; schema (node), schema_labels (to producer, to target); producers [{node, events
    [(event, label)]}]; rules {event: {label, target (node), then [(node, label)]}}; dlq {event, node, label};
    keys?. The chips' rows follow the producers' events in order; a producer sits on its last event's row."""
    th = prims.theme_of(theme)
    order = [ev for p in spec["producers"] for ev, _l in p["events"]]
    if not (2 <= len(order) <= 6):
        raise GeometryError("events", need="2 to 6 event types", have=len(order))
    cols = [1.7, 0.9, 2.2, 1.9, 1.55, 1.5]
    n = len(order)
    rows = [HEAD_LABEL, ("auto", 0.3), HEAD_LABEL] + ["auto"] * (n + 1) + [("auto", 1), 0.30]
    b = Board(box, th, cols=cols, rows=rows, name=name, draft=draft, keys=spec.get("keys"))
    R0 = 3
    last = R0 + n
    b.frame("prod", "panel", spec.get("producers_label", "Producers"), cols=(0, 0), rows=(0, last))
    b.frame("cons", "panel", spec.get("consumers_label", "Consumers by rule"), cols=(4, 5), rows=(0, last))
    bus = spec["bus"]
    b.frame("bus", "boundary", bus["label"], fact=bus.get("fact"), cols=(2, 2), rows=(2, last), icon=bus.get("mark"))
    _put(b, spec["schema"], (2, 1))
    row_of = {ev: R0 + k for k, ev in enumerate(order)}
    for p in spec["producers"]:
        _put(b, p["node"], (0, row_of[p["events"][-1][0]] if len(p["events"]) > 1 else row_of[p["events"][0][0]]))
    for ev in order:
        b.chip("ev-" + ev.replace(".", "-").replace("_", "-"), ev, cell=(2, row_of[ev]))
    cid = lambda ev: "ev-" + ev.replace(".", "-").replace("_", "-")  # noqa: E731
    second = 0
    for ev in order:
        rule = spec["rules"][ev]
        _put(b, rule["target"], (4, row_of[ev]))
        for k, (nd, _lab) in enumerate(rule.get("then", [])):
            r = row_of[ev] + k
            if k and r > last:
                raise GeometryError("events then", need="a free row under %s" % ev, have="none")
            _put(b, nd, (5, r))
    d = spec["dlq"]
    _put(b, d["node"], (3, last))
    for p in spec["producers"]:
        for ev, lab in p["events"]:
            b.edge(p["node"][0], cid(ev), lab)
    for ev in order:
        rule = spec["rules"][ev]
        b.edge(cid(ev), rule["target"][0], rule["label"], kind="async")
        for nd, lab in rule.get("then", []):
            b.edge(rule["target"][0], nd[0], lab)
    b.edge(cid(d["event"]), d["node"][0], d["label"], kind="feedback")
    sl = spec.get("schema_labels", (None, None))
    b.edge(spec["schema"][0], spec["producers"][0]["node"][0], sl[0], kind="control")
    b.edge(spec["schema"][0], spec["rules"][order[0]]["target"][0], sl[1], kind="control")
    return b


def state_graph(box: Box, theme, spec: dict, *, name: str = "graph", draft: bool = False) -> Board:
    """An agent state machine (LangGraph style, ruling 21): START, the node path and END on one row inside the graph
    boundary, branch nodes (retry, a human-in-the-loop interrupt, a failure END) on a row under it, conditional
    edges dashed and labelled with their condition, the services the nodes call above the graph and the queue,
    checkpointer and human app below it.

    spec: graph {label, fact, mark?}; path [(id, kind 'terminal'|'state', name, role)] left to right; path_labels
    [label per hop]; branch [(id, kind 'terminal'|'state'|'interrupt', name, role, col)]; edges [(a, b, label, kind,
    sides?, ports?)] for every edge off the path; above [(node, col, from_id, label)]; below [(node, col, side 'left'|
    'right', edge (a, b, label, kind, sides?, ports?))]; keys?."""
    th = prims.theme_of(theme)
    path = spec["path"]
    widths = []
    for _id, kind, nm, role in path:
        widths.append(1.22 if kind == "terminal" else max(1.82, _tw(nm, NAME_PT, th, True) + 0.6))
    rows = ["auto", ("auto", 0.55), HEAD_LABEL, "auto", ("auto", 0.9), "auto", ("auto", 0.18), "auto", 0.30]
    b = Board(box, th, cols=widths, rows=rows, name=name, draft=draft, keys=spec.get("keys"))
    g = spec["graph"]
    b.frame("graph", "boundary", g["label"], fact=g.get("fact"), cols=(0, len(path) - 1), rows=(2, 5),
            icon=g.get("mark"))
    for c, (sid, kind, nm, role) in enumerate(path):
        if kind == "terminal":
            b.terminal(sid, nm, cell=(c, 3))
        else:
            b.state(sid, nm, role, cell=(c, 3))
    for sid, kind, nm, role, c in spec.get("branch", []):
        if kind == "terminal":
            b.terminal(sid, nm, cell=(c, 5))
        else:
            b.state(sid, nm, role, cell=(c, 5), interrupt=kind == "interrupt")
    for nd, c, _frm, _lab in spec.get("above", []):
        _put(b, nd, (c, 0), caption="right", align="left")
    for item in spec.get("below", []):
        nd, c, side = item[:3]
        al = item[4] if len(item) > 4 else ("right" if side == "left" else "left")
        _put(b, nd, (c, 7), caption=side, align=al)
    for k in range(len(path) - 1):
        lab = spec["path_labels"][k]
        kind = "conditional" if isinstance(lab, tuple) else "data"
        b.edge(path[k][0], path[k + 1][0], lab[0] if isinstance(lab, tuple) else lab, kind=kind)
    for e in spec.get("edges", []):
        a, c, lab, kind = e[:4]
        b.edge(a, c, lab, kind=kind, sides=e[4] if len(e) > 4 and e[4] else (None, None),
               ports=e[5] if len(e) > 5 and e[5] else (None, None))
    for nd, _c, frm, lab in spec.get("above", []):
        b.edge(frm, nd[0], lab)
    for item in spec.get("below", []):
        a, c, lab, kind = item[3][:4]
        e = item[3]
        b.edge(a, c, lab, kind=kind, sides=e[4] if len(e) > 4 and e[4] else (None, None),
               ports=e[5] if len(e) > 5 and e[5] else (None, None))
    return b


__all__ = ["Board", "EDGE_KINDS", "GATE_KINDS", "FRAME_KINDS", "HEAD_BAR", "HEAD_LABEL", "HEAD_SECTION",
           "cicd", "mlops", "medallion", "events", "state_graph"]

