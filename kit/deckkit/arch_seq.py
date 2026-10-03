"""Sequence, DFD and threat model, and C4 diagrams in the house grammar (spec 3.8, 3.10 and the C4 notes; rulings
20 and 21). Built on deckkit.arch's public notation (FLOW_BY, BADGE_BY, BADGE_FILL, the 9pt and 8pt caption sizes,
CLEAR, LAST_LEG, LABEL_INS), so a sequence, a DFD, a C4 view and an architecture slide draw one line vocabulary.

    q = arch_seq.Sequence()
    q.participant("app", "vendor:programming/framework/react", "Field app", "React Native")
    q.participant("api", "vendor:aws/network/api-gateway", "API Gateway", "brief API")
    q.band("Agent zone · private subnets", "api", "api")
    n = q.message("app", "api", "POST /briefs {account_id}")            # a call, numbered 1
    q.message("api", "app", "200 {brief_id}", kind="reply")
    q.fragment("alt", "claim has no source", 1, 2)
    q.render(slide, WIDE.content, theme)

    d = arch_seq.DFD(grid=(5, 3))
    d.boundary("acct", "AWS account · production", at=(1, 0, 3, 3))
    d.entity("web", "Public web", "press, registries", at=(0, 1), mark="glyph:globe")
    d.process("collect", "1", "Collect signals", at=(1, 1), tech="AWS Lambda")
    d.flow("web", "collect", "press pages", control="HTTPS · TLS 1.3")
    d.render(slide, WIDE.content, theme)

    c = arch_seq.C4("context", grid=(4, 3))
    c.person("rep", "Field rep", "Reads the Monday brief", at=(3, 0))
    c.system("svc", "Field brief service", "Drafts a cited weekly brief", at=(2, 1))
    c.rel("rep", "svc", "reads briefs · HTTPS")

What the engines refuse, in the house rules' terms:
  * every message, flow and relationship carries a label (what moves, at most five words); a sequence message is
    numbered 1..N at its label start, a DFD flow by a step badge beside its source end (spec 1.5, P26.e and j);
  * every line runs orthogonally from one shape's edge to another's, never through a box, a label or another line,
    and never along a boundary (P06, P26.h); a route that cannot be found raises, nothing is drawn crossed;
  * every label, badge, chip and caption is measured before it is drawn; a box that cannot hold its text raises
    Overflows (type is never shrunk, nothing is clamped);
  * a sequence call needs its reply unless it sits in a break fragment; a fragment encloses exactly the messages it
    declares and lies wholly inside or wholly outside the trust band (a frame that straddles the band reads as two
    regions fighting, and gate P05 fails it);
  * a DFD flow has a process at one end at least (no entity to store, no store to store); a flow that crosses a
    trust boundary carries a crossing marker on every intercept and one control chip ("HTTPS · OIDC · TLS 1.3");
    a context-level DFD has one process and no store;
  * a boundary label states a fact after a middot ("AWS account · production"): an unlabelled dashed zone is
    decoration (spec 1.6).

Notation, house-adapted:
  sequence  participant heads are light cards with the product mark and a two-line caption; lifelines rule-strong
            sysDash; activations 0.10in card bars (named state.*: a bar encodes "this participant is executing");
            calls solid with a filled head, replies sysDash 0.75pt with an open head, events dash with an open head
            (spec 1.4: no two kinds differ by colour or weight alone); fragment frames 0.75pt ink with the operator
            on a navy tab riding the frame's top-left corner (the house header tab), the guard beside it; the trust
            band is the house trust zone (accent-deep dash) behind the lifelines it encloses.
  DFD       Gane-Sarson: processes are rounded paper cards with an id band over a hairline; external entities square
            card tiles; stores open on the right with a D-id cell; trust boundaries dashed (the outer in ink-muted,
            a nested zone in accent-deep); crossing markers 0.12in ink-strong squares on the intercept (state.*);
            out of scope dashed in ink-muted. Red threat colour stays off (spec 3.8: an accent the user has not
            introduced).
  C4        people navy blocks with the person glyph, the software system in focus a solid brand block, external
            systems card tiles, containers paper cards with a product mark and a "Container · technology" line;
            relationships labelled "intent · protocol"; system and enterprise boundaries dashed with their fact.
            Technology is a line beside the mark, never a pill on every tile (CLAUDE.md section 4).
"""
from __future__ import annotations

import io
import math
import re
from dataclasses import dataclass, field

from . import arch, glyphs, icons, measure, ooxml, prims
from . import text as txt
from .canvas import Box
from .errors import Capacity, GeometryError, Overflows
from .text import Para, Run

# ---------------------------------------------------------------------------------------------- shared notation

LINE_ROLE, LINE_PT, _HEAD, _HLEN = arch.FLOW_BY["house"]
NAME_PT, ROLE_PT, LABEL_PT, LEGEND_PT = arch.NAME_PT, arch.ROLE_PT, arch.LABEL_PT, arch.LEGEND_PT
BADGE, BADGE_PT = arch.BADGE_BY["house"]
BADGE_FILL = arch.BADGE_FILL["house"]
CLEAR, LAST_LEG, LABEL_INS = arch.CLEAR, arch.LAST_LEG, arch.LABEL_INS
GROUP_PT = arch.GROUP_PT

# kind: (prstDash, weight pt, head type, head length). Spec 1.4: every kind its own dash.
KINDS = {
    "call": (None, LINE_PT, "triangle", "med"),
    "data": (None, LINE_PT, "triangle", "med"),
    "reply": ("sysDash", 0.75, "arrow", "med"),
    "async": ("dash", LINE_PT, "arrow", "med"),
    "control": ("sysDot", LINE_PT, "arrow", "med"),
}
KEY_TEXT = {"call": "Call", "data": "Data flow", "reply": "Reply", "async": "Event, asynchronous",
            "control": "Control or configuration"}
LABEL_WORDS = 5            # a message or flow label, before its number (gate P26 reads labels of 1 to 6 words)
LEG_H = 0.24               # the legend row
KEY_W = 0.45               # a key sample line
_AQ = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
_ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,40}")


def _check_id(what, v):
    if not isinstance(v, str) or not _ID.fullmatch(v):
        raise GeometryError(what, need="a lower-case id (a-z, 0-9, - and _)", have=v)
    return v


def _family(th) -> str:
    return (getattr(th, "fonts", None) or {}).get("minor") or "Arial"


def _run_w(r: Run, th, pt) -> float:
    return measure.width_in(r.text, r.size or pt, measure.face_for(_family(th), r.bold))


def _line_w(runs, th, pt=LABEL_PT) -> float:
    """One unwrapped line of runs, in inches, with the kit's PowerPoint slack."""
    return sum(_run_w(r, th, pt) for r in runs) * measure.SLACK


def _need_h(paras, w, th, insets=measure.ZERO) -> float:
    return math.ceil(txt.need_height(paras, w, th, insets) * 10000 + 1) / 10000.0


def _words(s: str) -> int:
    return len([w for w in re.split(r"\s+", str(s).strip()) if w and w != "·"])


def _check_label(what, label):
    if not isinstance(label, str) or not label.strip():
        raise GeometryError(what, need="a label: what moves (spec 1.5)", have=label,
                            hint="an unlabelled arrow is the look the user rejected")
    if _words(label) > LABEL_WORDS:
        raise Overflows(what, need=_words(label), have=LABEL_WORDS, unit="words",
                        hint="a label names what moves in at most %d words; the detail goes to the notes"
                             % LABEL_WORDS)
    return label.strip()


def _inter(a: Box, b: Box, pad: float = 0.0) -> bool:
    return a.x - pad < b.r and b.x - pad < a.r and a.y - pad < b.b and b.y - pad < a.b


def _inside(a: Box, b: Box, tol: float = 0.0) -> bool:
    return a.x >= b.x - tol and a.y >= b.y - tol and a.r <= b.r + tol and a.b <= b.b + tol


def _seg_hits(p, q, b: Box, pad: float = 0.0) -> bool:
    x0, x1 = sorted((p[0], q[0]))
    y0, y1 = sorted((p[1], q[1]))
    return x0 < b.r + pad and x1 > b.x - pad and y0 < b.b + pad and y1 > b.y - pad


def _horiz(p, q) -> bool:
    return abs(p[1] - q[1]) < 1e-6


def _cross(p, q, e1, e2, eps: float = 0.005) -> bool:
    """Two orthogonal segments cross strictly inside both."""
    if _horiz(p, q) == _horiz(e1, e2):
        return False
    (h1, h2), (v1, v2) = ((p, q), (e1, e2)) if _horiz(p, q) else ((e1, e2), (p, q))
    hx0, hx1 = sorted((h1[0], h2[0]))
    vy0, vy1 = sorted((v1[1], v2[1]))
    return hx0 + eps < v1[0] < hx1 - eps and vy0 + eps < h1[1] < vy1 - eps


def _along(p, q, e1, e2, tol: float) -> bool:
    """Two parallel segments run side by side closer than tol over a shared stretch."""
    if _horiz(p, q) != _horiz(e1, e2):
        return False
    a = 0 if _horiz(p, q) else 1
    b = 1 - a
    if abs(p[b] - e1[b]) >= tol:
        return False
    lo1, hi1 = sorted((p[a], q[a]))
    lo2, hi2 = sorted((e1[a], e2[a]))
    return min(hi1, hi2) - max(lo1, lo2) > 0.01


def _edges(b: Box):
    return [((b.x, b.y), (b.r, b.y)), ((b.r, b.y), (b.r, b.b)), ((b.x, b.b), (b.r, b.b)), ((b.x, b.y), (b.x, b.b))]


def _clean(pts) -> list:
    out = []
    for p in pts:
        p = (round(p[0], 4), round(p[1], 4))
        if out and abs(out[-1][0] - p[0]) < 1e-6 and abs(out[-1][1] - p[1]) < 1e-6:
            continue
        out.append(p)
    k = 1
    while k < len(out) - 1:                         # drop collinear midpoints
        a, b, c = out[k - 1], out[k], out[k + 1]
        if (abs(a[0] - b[0]) < 1e-6 and abs(b[0] - c[0]) < 1e-6) or (abs(a[1] - b[1]) < 1e-6 and abs(b[1] - c[1]) < 1e-6):
            out.pop(k)
        else:
            k += 1
    return out


def _length(pts) -> float:
    return sum(abs(p[0] - q[0]) + abs(p[1] - q[1]) for p, q in zip(pts, pts[1:]))


# ---------------------------------------------------------------------------------------------- marks

_INK: dict = {}


def _ink(mark: str):
    """(l, t, r, b, px_w, px_h) of a picture mark's ink (alpha above 16) as fractions, or None (a glyph)."""
    if mark in _INK:
        return _INK[mark]
    kind, _, key = mark.partition(":")
    if kind == "vendor":
        path = icons.vendor_path(key)
    elif kind == "mark":
        entry = icons.mark_registry().get(key)
        if entry is None:
            return None
        path = icons.marks_dir() / entry["file"]
    else:
        return None
    from PIL import Image
    blob = path.read_bytes()
    size = None
    if str(path).lower().endswith(".svg"):
        w, h = icons.svg_size(blob)
        size = (w, h)
        blob = icons.rasterise(blob, 256, max(1, round(256 * h / w)) if w else 256)
    with Image.open(io.BytesIO(blob)) as im:
        im = im.convert("RGBA")
        W, H = im.size
        bb = im.getchannel("A").point(lambda a: 255 if a > 16 else 0).getbbox()
    sw, sh = size or (W, H)
    out = None if bb is None else (bb[0] / W, bb[1] / H, bb[2] / W, bb[3] / H, sw, sh)
    _INK[mark] = out
    return out


def check_mark(mark: str):
    """Refuse a mark the kit cannot draw, before anything is laid out."""
    kind, _, key = str(mark or "").partition(":")
    if kind == "vendor":
        if key not in set(icons.vendor_keys()):
            raise GeometryError("mark %s" % mark, need="a vendor key (icons.vendor_keys())", have=key)
    elif kind == "mark":
        if key not in icons.mark_registry():
            raise GeometryError("mark %s" % mark, need="a key in kit/assets/marks/registry.json", have=key)
    elif kind == "glyph":
        glyphs.resolve(key)
    else:
        raise GeometryError("mark %s" % mark, need="vendor:<key>, mark:<key> or glyph:<name>", have=mark)
    return mark


def draw_mark(slide, mark: str, box: Box, name: str, alt: str, th, role: str = "ink-strong"):
    """A product mark centred in box, cropped to its ink (a:srcRect, bytes untouched) so marks share one optical
    size; a glyph mark (glyph:<name>) is stroked in role. Returns the drawn box."""
    kind, _, key = mark.partition(":")
    if kind == "glyph":
        glyphs.glyph(slide, key, box, role=role, shape_name=name + ".icon", theme=th)
        return box
    ink = _ink(mark)
    ib = box
    if ink is not None:
        l, t, r, b, pw, ph = ink
        ar = ((r - l) * pw) / max(1e-9, (b - t) * ph)
        w, h = (box.w, box.w / ar) if ar >= box.w / box.h else (box.h * ar, box.h)
        ib = Box(box.cx - w / 2, box.cy - h / 2, w, h)
    suffix = name.replace(".", "-")
    if kind == "vendor":
        pic = icons.vendor(slide, key, ib, name=suffix, alt=alt, theme=th)
    else:
        big = ib
        if ink is not None:
            big = Box(ib.x, ib.y, ib.w / max(0.05, ink[2] - ink[0]), ib.h / max(0.05, ink[3] - ink[1]))
        pic = icons.mark(slide, key, big, name=suffix, alt=alt)
    if ink is not None:
        l, t, r, b = ink[:4]
        if not (l < 0.02 and t < 0.02 and r > 0.98 and b > 0.98):
            bf = pic._element.find(".//{http://schemas.openxmlformats.org/presentationml/2006/main}blipFill")
            blip = bf.find(_AQ + "blip")
            old = bf.find(_AQ + "srcRect")
            if old is not None:
                bf.remove(old)
            from lxml import etree
            sr = etree.Element(_AQ + "srcRect")
            for k_, v in (("l", l), ("t", t), ("r", 1 - r), ("b", 1 - b)):
                if v > 0:
                    sr.set(k_, str(int(round(v * 100000))))
            blip.addnext(sr)
        pic.left, pic.top, pic.width, pic.height = (int(round(v)) for v in ib.emu)
    return ib


# ---------------------------------------------------------------------------------------------- lines

def draw_line(slide, pts, kind: str, name: str, th):
    """One headed line in the house flow notation for its kind (KINDS)."""
    dash, wt, head, hlen = KINDS[kind]
    if len(pts) == 2:
        sh = prims.connect(slide, pts[0], pts[1], head="end", dash=dash, role=LINE_ROLE, weight_pt=wt, name=name,
                           theme=th)
    else:
        sh = prims.elbow(slide, pts, head="end", dash=dash, role=LINE_ROLE, weight_pt=wt, name=name, theme=th)
    tail = sh._element.find(".//" + _AQ + "ln/" + _AQ + "tailEnd")
    if tail is not None:
        tail.set("type", head)
        tail.set("w", "med")
        tail.set("len", hlen)
    return sh


def _dashed(slide, p1, p2, name, th, role="rule-strong", wt=0.75, dash="sysDash"):
    """An undirected dashed rule (a lifeline, an operand divider): a strip role, never an arrow."""
    sh = prims.hairline(slide, p1, p2, role=role, weight_pt=wt, name=name, theme=th)
    prims.set_line(sh, role, wt, theme=th, dash=dash)
    return sh


def _key_row(slide, x, y, items, nm, th, right: float):
    """A legend row: (key, sample-drawer, text) per entry, left to right; the sample is named
    state.<nm>.legend.key.<key> and its text <nm>.legend.key.<key>.text, so a gate counts one entry per key.
    Raises when the row runs past right."""
    for key, draw, text in items:
        paras = [Para((Run(text, role="ink-muted", size=LEGEND_PT),))]
        tw = _line_w(paras[0].runs, th, LEGEND_PT) + 0.04
        h = _need_h(paras, tw, th)
        sw = draw(x, y + h / 2, key)
        if x + sw + 0.08 + tw > right + 1e-6:
            raise Overflows("legend %s" % nm, need=round(x + sw + 0.08 + tw, 3), have=round(right, 3))
        txt.textbox(slide, Box(x + sw + 0.08, y, tw, h), paras, "%s.legend.key.%s.text" % (nm, key), th)
        x += sw + 0.08 + tw + 0.30
    return x


def _knockout(slide, box: Box, paras, name, th, ground="paper", anchor="middle"):
    sh = txt.textbox(slide, box, paras, name, th, insets=LABEL_INS, background=ground, anchor=anchor)
    prims.set_fill(sh, ground, theme=th)
    return sh


def _label_box(paras, th, pt=LABEL_PT):
    w = _line_w(paras[0].runs, th, pt) + LABEL_INS.l + LABEL_INS.r + 0.02
    return w, _need_h(paras, w, th, LABEL_INS)


# ============================================================================================== sequence

HEAD_H = 0.50
HEAD_MARK = 0.30
BAR_W = 0.10               # an activation bar (spec 3.10); nested bars offset +0.05in
BAR_STEP = 0.05
PITCH_MIN, PITCH_MAX = 1.40, 1.90     # lifeline pitch (spec 3.10)
MSG_MIN, MSG_MAX = 0.28, 0.40          # message pitch: 0.28 to 0.34 in the spec; stretched to fill, never past 0.40
FRAG_HEAD = 0.24           # room above a fragment frame for its operator tab
FRAG_PAD = 0.06            # inside a frame, above its first label and below its last line
TAB_H = 0.20
ELSE_H = 0.22
BAND_HEAD = 0.27           # the band's label row above the heads
HEAD_GAP = 0.16            # between two heads, so a band edge can pass between them
BAND_IN = 0.08             # a band edge outside the heads it encloses
OPS = ("alt", "opt", "loop", "par", "break", "critical")
SEQ_KINDS = ("call", "reply", "async")
MAX_PARTS, MAX_MSGS = 8, 16


@dataclass
class _Part:
    id: str
    mark: str
    name: str
    role: str | None
    x: float = 0.0


@dataclass
class _Msg:
    n: int
    src: str
    dst: str
    label: str
    kind: str
    top: float = 0.0          # label top
    y: float = 0.0            # line
    x0: float = 0.0
    x1: float = 0.0
    lbox: Box | None = None
    paras: list | None = None


@dataclass
class _Frag:
    op: str
    guard: str
    first: int
    last: int
    else_at: int | None = None
    else_guard: str | None = None
    top: float = 0.0
    bottom: float = 0.0
    else_y: float = 0.0
    box: Box | None = None
    depth: int = 0


@dataclass
class _Bar:
    pid: str
    y0: float
    y1: float | None
    depth: int
    caller: str | None
    msg: int

    def box(self, x) -> Box:
        return Box(x - BAR_W / 2 + BAR_STEP * self.depth, self.y0, BAR_W, self.y1 - self.y0)


class Sequence:
    """A sequence diagram (spec 3.10): participants ordered by trust, numbered and labelled messages, activations,
    fragments and one trust band, laid out in a box and drawn by render()."""

    def __init__(self, *, head_w: float | None = None, mark: float = HEAD_MARK):
        self.parts: dict[str, _Part] = {}
        self.msgs: list[_Msg] = []
        self.frags: list[_Frag] = []
        self.bands: list[tuple] = []
        self.head_w = head_w
        self.mark = mark
        self._metrics: dict = {}

    # ---- declaration
    def participant(self, id, mark, name, role=None):
        _check_id("participant id", id)
        if id in self.parts:
            raise GeometryError("participant %s" % id, need="a new id", have="declared twice")
        if len(self.parts) >= MAX_PARTS:
            raise Capacity("participants", need=len(self.parts) + 1, have=MAX_PARTS,
                           hint="spec 3.10: 4 to 7 participants, 8 at most; split the sequence")
        self.parts[id] = _Part(id, check_mark(mark), name, role)
        return self

    def band(self, label, first, last):
        """A trust band behind the lifelines first..last (participant ids, in order). One per diagram."""
        if self.bands:
            raise Capacity("trust band", need=2, have=1, hint="a sequence carries one region at most (spec 3.10)")
        for p in (first, last):
            if p not in self.parts:
                raise GeometryError("band %s" % label, need="a declared participant", have=p)
        if "·" not in label and ":" not in label:
            raise GeometryError("band label %r" % label, need="a fact after a middot ('Agent zone · private')",
                                have="a bare name", hint="spec 1.6: a boundary states a fact")
        self.bands.append((label, first, last))
        return self

    def message(self, src, dst, label, kind="call") -> int:
        """A message; returns its number (1..N in declaration order). kind call (solid, filled head), reply
        (sysDash, open head; it closes the activation its call opened) or async (dash, open head). src == dst is a
        self call: a loop to a nested activation."""
        for p in (src, dst):
            if p not in self.parts:
                raise GeometryError("message %s to %s" % (src, dst), need="declared participants", have=p)
        if kind not in SEQ_KINDS:
            raise GeometryError("message kind", need=" / ".join(SEQ_KINDS), have=kind)
        if src == dst and kind != "call":
            raise GeometryError("self message", need="kind call", have=kind)
        if len(self.msgs) >= MAX_MSGS:
            raise Capacity("messages", need=len(self.msgs) + 1, have=MAX_MSGS,
                           hint="spec 3.10: 8 to 16 messages; split the sequence")
        n = len(self.msgs) + 1
        self.msgs.append(_Msg(n, src, dst, _check_label("message %d label" % n, label), kind))
        return n

    def fragment(self, op, guard, first, last, *, else_at=None, else_guard=None):
        """A combined fragment around messages first..last (numbers). alt takes else_at (the first message of the
        second operand) and else_guard."""
        if op not in OPS:
            raise GeometryError("fragment operator", need=" / ".join(OPS), have=op)
        if not (1 <= first <= last <= len(self.msgs)):
            raise GeometryError("fragment %s" % op, need="declared message numbers first <= last",
                                have=(first, last), hint="declare the messages before the fragment")
        if (else_at is None) != (else_guard is None) or (else_at is not None and op not in ("alt", "par")):
            raise GeometryError("fragment %s else" % op, need="else_at and else_guard together, on alt or par",
                                have=(else_at, else_guard))
        if else_at is not None and not first < else_at <= last:
            raise GeometryError("fragment %s else_at" % op, need="inside (first, last]", have=else_at)
        for f in self.frags:
            disjoint = last < f.first or first > f.last
            nested = (f.first <= first and last <= f.last) or (first <= f.first and f.last <= last)
            if not (disjoint or nested) or (f.first, f.last) == (first, last):
                raise GeometryError("fragment %s %d..%d" % (op, first, last), need="nested in or apart from every "
                                    "other fragment", have="%s %d..%d" % (f.op, f.first, f.last))
        self.frags.append(_Frag(op, guard.strip().strip("[]"), first, last, else_at, else_guard and
                                else_guard.strip().strip("[]")))
        return self

    # ---- layout
    def _order(self):
        return list(self.parts)

    def _head_paras(self, p: _Part):
        paras = [Para((Run(p.name, role="ink", bold=True, size=NAME_PT),))]
        if p.role:
            paras.append(Para((Run(p.role, role="ink-muted", size=ROLE_PT),)))
        return paras

    def _msg_paras(self, m: _Msg):
        return [Para((Run(str(m.n), role="ink", bold=True, size=LABEL_PT), Run("  " + m.label, role="ink",
                                                                                 size=LABEL_PT)))]

    def _rows(self, top, pitch, th):
        """Every message's label top and line y, fragment tops and bottoms, at one message pitch; returns the y
        below the last row."""
        y = top
        opening = {}
        for f in self.frags:
            opening.setdefault(f.first, []).append(f)
        closing = {}
        for f in self.frags:
            closing.setdefault(f.last, []).append(f)
        for m in self.msgs:
            for f in sorted(opening.get(m.n, []), key=lambda f: -(f.last - f.first)):   # outer first
                y += FRAG_HEAD
                f.top = y
                y += FRAG_PAD
            for f in self.frags:
                if f.else_at == m.n:
                    y += 0.04
                    f.else_y = y
                    y += ELSE_H
            m.paras = self._msg_paras(m)
            lw, lh = _label_box(m.paras, th)
            m.lbox = Box(0, 0, lw, lh)
            m.top = y
            m.y = y + lh + 0.02
            y += max(pitch, lh + 0.10)
            if m.src == m.dst:
                y += 0.20
            closers = sorted(closing.get(m.n, []), key=lambda f: f.last - f.first)        # inner first
            b = m.y + 0.10 + (0.20 if m.src == m.dst else 0.0)
            for f in closers:
                f.bottom = b
                b += 0.07
            if closers:
                y = max(y, b)
        return y

    def _activations(self):
        bars: list[_Bar] = []
        open_: dict[str, list[_Bar]] = {p: [] for p in self.parts}
        last_y = {}
        for m in self.msgs:
            last_y[m.src] = m.y
            last_y[m.dst] = m.y + (0.20 if m.src == m.dst else 0)
        brk = [f for f in self.frags if f.op == "break"]
        alts = [f for f in self.frags if f.else_at is not None]
        snap: dict = {}
        for m in self.msgs:
            for f in alts:                    # alt operands are alternatives: each starts from the same open calls
                if f.first == m.n:
                    snap[id(f)] = ({p: list(st) for p, st in open_.items()}, len(bars))
                if f.else_at == m.n:
                    before, nb = snap[id(f)]
                    for p, st in before.items():
                        for b in st:
                            if b not in open_[p]:
                                b.y1 = None
                                open_[p].append(b)
                        open_[p].sort(key=lambda b: b.depth)
            if m.kind != "reply" and not open_[m.src]:
                b = _Bar(m.src, m.y - 0.04, None, 0, None, m.n)          # the initiator: active to its last message
                bars.append(b)
                open_[m.src].append(b)
            if m.src == m.dst:
                b = _Bar(m.dst, m.y + 0.12, m.y + 0.36, len(open_[m.dst]), m.src, m.n)
                bars.append(b)
                continue
            if m.kind == "call":
                b = _Bar(m.dst, m.y - 0.04, None, len(open_[m.dst]), m.src, m.n)
                bars.append(b)
                open_[m.dst].append(b)
            elif m.kind == "reply":
                stack = open_[m.src]
                hit = next((b for b in reversed(stack) if b.caller == m.dst), None)
                if hit is None:
                    raise GeometryError("message %d reply" % m.n, need="an open call from %s to %s" % (m.dst, m.src),
                                        have="none", hint="a reply closes the activation its call opened")
                hit.y1 = m.y + 0.04
                stack.remove(hit)
            else:
                if not open_[m.dst]:
                    bars.append(_Bar(m.dst, m.y - 0.04, m.y + 0.22, 0, m.src, m.n))
        for p, stack in open_.items():
            for b in stack:
                if b.caller is None:
                    b.y1 = last_y.get(p, b.y0) + 0.04
                    continue
                inside = [f for f in brk if f.first <= b.msg <= f.last]
                if not inside:
                    raise GeometryError("message %d call" % b.msg, need="a reply, or a break fragment around it",
                                        have="no reply", hint="spec 3.10: every sync call has a reply or sits "
                                                              "inside a break")
                b.y1 = inside[0].bottom - 0.04
        for b in bars:
            if b.y1 is None or b.y1 - b.y0 < 0.12:
                b.y1 = b.y0 + 0.12 if b.y1 is None else max(b.y1, b.y0 + 0.12)
        return bars

    @staticmethod
    def _stretches(a, b, ly0, ly1, bars, X, vlines):
        """The free stretches of [a, b] at the height ly0..ly1: clear of every activation bar there and of every
        frame or band edge (a lifeline with no bar may sit under a knock-out)."""
        obst = []
        for bar in bars:
            if bar.y0 < ly1 + CLEAR and bar.y1 > ly0 - CLEAR:
                bb = bar.box(X[bar.pid])
                obst.append((bb.x - 0.04, bb.r + 0.04))
        for vx, vy0, vy1 in vlines:
            if vy0 < ly1 and vy1 > ly0:
                obst.append((vx - 0.05, vx + 0.05))
        free, cur = [], a
        for o0, o1 in sorted(obst):
            if o1 <= cur or o0 >= b:
                continue
            if o0 > cur:
                free.append((cur, o0))
            cur = max(cur, o1)
        if cur < b:
            free.append((cur, b))
        return free

    def _bar_at(self, bars, pid, y, x):
        """The innermost bar of pid active at y (or None)."""
        live = [b for b in bars if b.pid == pid and b.y0 - 1e-6 <= y <= b.y1 + 1e-6]
        return max(live, key=lambda b: b.depth).box(x) if live else None

    def render(self, slide, box: Box, theme=None, name: str = "seq", *, legend: bool = True) -> dict:
        th = prims.theme_of(theme)
        if len(self.parts) < 2 or not self.msgs:
            raise GeometryError("sequence %s" % name, need="2 participants and a message", have=len(self.parts))
        order = self._order()
        n = len(order)
        idx = {p: i for i, p in enumerate(order)}
        band = self.bands[0] if self.bands else None
        # equal pitch; heads as wide as the pitch allows (a band edge sits BAND_IN outside the head it encloses)
        # equal pitch; heads as wide as the pitch allows. A gap a band edge falls in widens until the longest label
        # of a message crossing it fits on one side of the edge (a label never straddles the band: P05)
        head_w = self.head_w or min(1.70, (box.w + HEAD_GAP) / n - HEAD_GAP)
        edge_gaps = {}
        if band:
            ia, ib = idx[band[1]], idx[band[2]]
            for g in (ia - 1, ib):
                if 0 <= g < n - 1:
                    need = 0.0
                    for m in self.msgs:
                        lo, hi = sorted((idx[m.src], idx[m.dst]))
                        if lo <= g < hi:
                            lw, _lh = _label_box(self._msg_paras(m), th)
                            need = max(need, lw)
                    edge_gaps[g] = need
        pitch = 0.0
        for _ in range(4):
            gaps = {g: max(head_w / 2 + BAND_IN + 0.05 + need + 0.08 + BAR_W / 2, 0.0)
                    for g, need in edge_gaps.items()}
            rest = n - 1 - len(gaps)
            pitch = min(PITCH_MAX, (box.w - head_w - sum(gaps.values())) / rest) if rest else 0.0
            for g in gaps:
                gaps[g] = max(gaps[g], pitch)
            if rest and pitch - head_w < HEAD_GAP - 1e-6 and not self.head_w:
                head_w = pitch - HEAD_GAP
                continue
            break
        if (rest and pitch < PITCH_MIN - 1e-6) or head_w < 1.2 or (rest and pitch - head_w < HEAD_GAP - 1e-6):
            raise Overflows("sequence %s lifelines" % name, need=round(PITCH_MIN * (n - 1) + 1.2, 2),
                            have=round(box.w, 2), hint="fewer participants (spec 3.10: 4 to 7), or a shorter "
                                                       "label on a message that crosses the band")
        steps = [gaps.get(g, pitch) for g in range(n - 1)]
        span = head_w + sum(steps)
        lm = BAND_IN + 0.06 if band and idx[band[1]] == 0 else 0.0          # a band around an end head
        rm = BAND_IN + 0.06 if band and idx[band[2]] == n - 1 else 0.0      # keeps its edge inside the box
        if span + lm + rm > box.w + 1e-6:
            shrink = (span + lm + rm - box.w) / max(1, n - 1 - len(gaps))
            steps = [st if g in gaps else st - shrink for g, st in enumerate(steps)]
            pitch -= shrink
            span = head_w + sum(steps)
            if pitch < PITCH_MIN - 1e-6 or pitch - head_w < HEAD_GAP - 1e-6:
                raise Overflows("sequence %s lifelines" % name, need=round(span + lm + rm, 2), have=round(box.w, 2),
                                hint="fewer participants, or a narrower head")
        x = box.x + lm + (box.w - lm - rm - span) / 2 + head_w / 2
        for i, p in enumerate(order):
            self.parts[p].x = x
            if i < n - 1:
                x += steps[i]
        # heads: one size, measured
        tw = head_w - 0.06 - self.mark - 0.06 - 0.03
        for p in self.parts.values():
            need = _need_h(self._head_paras(p), tw, th)
            if need > HEAD_H - 0.08:
                raise Overflows("participant %s caption" % p.id, need=round(need, 3), have=HEAD_H - 0.08,
                                hint="a shorter name or role; heads hold two lines")
        head_y = box.y + (BAND_HEAD if band else 0.0)
        top = head_y + HEAD_H + 0.12
        limit = box.b - (LEG_H + 0.04 if legend else 0.0) - 0.10
        bottom0 = self._rows(top, MSG_MIN, th)
        if bottom0 > limit + 1e-6:
            raise Overflows("sequence %s height" % name, need=round(bottom0 + (box.b - limit) - box.y, 3),
                            have=round(box.h, 3), hint="fewer messages or fragments (spec 3.10: 8 to 16)")
        rows = len(self.msgs)
        pitch_m = min(MSG_MAX, MSG_MIN + (limit - bottom0) / rows)
        end = self._rows(top, pitch_m, th)
        bars = self._activations()
        low = max([b.y1 for b in bars] + [m.y for m in self.msgs] + [f.bottom for f in self.frags])
        life_end = low + 0.08                     # the lifelines stop just below the last thing drawn on them
        X = {p: self.parts[p].x for p in order}
        # message ends: on a bar edge (or the lifeline when idle)
        for m in self.msgs:
            if m.src == m.dst:
                b = self._bar_at(bars, m.src, m.y, X[m.src])
                m.x0 = b.r if b else X[m.src]
                continue
            right = idx[m.dst] > idx[m.src]
            sb = self._bar_at(bars, m.src, m.y, X[m.src])
            db = self._bar_at(bars, m.dst, m.y, X[m.dst])
            m.x0 = (sb.r if right else sb.x) if sb else X[m.src]
            m.x1 = (db.x if right else db.r) if db else X[m.dst]
        # fragment frames
        def parts_of(f):
            ps = set()
            for m in self.msgs[f.first - 1:f.last]:
                ps.update((m.src, m.dst))
            return ps
        for f in self.frags:
            f.depth = sum(1 for g in self.frags if g is not f and f.first <= g.first and g.last <= f.last)
        for f in sorted(self.frags, key=lambda f: f.depth):                 # inner frames first
            ps = parts_of(f)
            mx = 0.30 + 0.12 * f.depth
            x_lo, x_hi = min(X[p] for p in ps) - mx, max(X[p] for p in ps) + mx
            for m in self.msgs[f.first - 1:f.last]:
                if m.src == m.dst:
                    x_hi = max(x_hi, m.x0 + 0.30 + 0.08 + m.lbox.w + 0.10)
            for g in self.frags:
                if g is not f and f.first <= g.first and g.last <= f.last and g.box is not None:
                    x_lo, x_hi = min(x_lo, g.box.x - 0.12), max(x_hi, g.box.r + 0.12)
            f.box = Box(x_lo, f.top, x_hi - x_lo, f.bottom - f.top)
            if f.box.x < box.x - 1e-6 or f.box.r > box.r + 1e-6:
                raise Overflows("fragment %s %d..%d width" % (f.op, f.first, f.last), need=round(f.box.w, 3),
                                have=round(box.w, 3), hint="widen the slide box or move the fragment's messages")
        bandbox = None
        if band:
            label, a, b = band
            bl = X[a] - head_w / 2 - BAND_IN
            br = X[b] + head_w / 2 + BAND_IN
            bl, br = max(bl, box.x), min(br, box.r)
            bandbox = Box(bl, box.y, br - bl, life_end + 0.04 - box.y)
            for f in self.frags:
                inside = _inside(f.box, bandbox, 1e-6) and f.box.x >= bandbox.x + 0.10 and f.box.r <= bandbox.r - 0.10
                apart = f.box.r <= bandbox.x - 0.02 or f.box.x >= bandbox.r + 0.02
                if not (inside or apart):
                    raise GeometryError("fragment %s %d..%d" % (f.op, f.first, f.last), need="wholly inside or "
                                        "outside the trust band", have="straddles it",
                                        hint="move the band's edge or the fragment's messages; a frame across "
                                             "a band reads as two regions fighting")
        # message labels: on free stretches of the line, by the sender
        vlines = []
        for f in self.frags:
            vlines.append((f.box.x, f.box.y, f.box.b))
            vlines.append((f.box.r, f.box.y, f.box.b))
        if bandbox:
            vlines.append((bandbox.x, bandbox.y, bandbox.b))
            vlines.append((bandbox.r, bandbox.y, bandbox.b))
        for m in self.msgs:
            w, h = m.lbox.w, m.lbox.h
            ly0, ly1 = m.top, m.top + h
            if m.src == m.dst:
                lx = m.x0 + 0.30 + 0.08
                m.lbox = Box(lx, m.y + 0.10 - h / 2, w, h)
                continue
            a, b = sorted((m.x0, m.x1))
            free = self._stretches(a + 0.08, b - 0.08, ly0, ly1, bars, X, vlines)
            fits = [(s, e) for s, e in free if e - s >= w - 1e-6]
            if not fits:
                raise Overflows("message %d label %r" % (m.n, m.label), need=round(w, 3),
                                have=round(max((e - s for s, e in free), default=0.0), 3),
                                hint="cut words; a label sits on a free stretch between two activations")
            rightward = m.x1 > m.x0
            s, e = fits[0] if rightward else fits[-1]
            lx = s if rightward else e - w
            m.lbox = Box(lx, m.top, w, h)
        # ---- draw
        nm = name
        if bandbox:
            sh = prims.rect(slide, bandbox, fill=None, line="accent-deep", weight_pt=1.0, name="%s.band" % nm,
                            theme=th)
            prims.set_line(sh, "accent-deep", 1.0, theme=th, dash="dash")
        for k, f in enumerate(sorted(self.frags, key=lambda f: -f.depth)):
            prims.rect(slide, f.box, fill=None, line="ink", weight_pt=0.75, name="%s.frag.%d" % (nm, k), theme=th)
            if f.else_at is not None:
                _dashed(slide, (f.box.x, f.else_y), (f.box.r, f.else_y), "%s.frag.%d.else" % (nm, k), th)
                gp = [Para((Run("[%s]" % f.else_guard, role="ink", size=LABEL_PT),))]
                gw, gh = _label_box(gp, th)
                gy = f.else_y + 0.04
                inner = [v for v in vlines if not (abs(v[0] - f.box.x) < 1e-6 or abs(v[0] - f.box.r) < 1e-6)]
                fits = [(a_, b_) for a_, b_ in self._stretches(f.box.x + 0.08, f.box.r - 0.08, gy, gy + gh, bars,
                                                                 X, inner) if b_ - a_ >= gw - 1e-6]
                if not fits:
                    raise Overflows("fragment %s else guard" % f.op, need=round(gw, 3), have="no free stretch",
                                    hint="a shorter guard")
                _knockout(slide, Box(fits[0][0], gy, gw, gh), gp, "%s.frag.%d.else.guard" % (nm, k), th,
                          anchor="top")
        for p in order:
            _dashed(slide, (X[p], head_y + HEAD_H), (X[p], life_end), "%s.life.%s" % (nm, p), th)
        for k, b in enumerate(sorted(bars, key=lambda b: (b.depth, b.y0))):
            prims.rect(slide, b.box(X[b.pid]), fill="card", line="rule-strong", weight_pt=0.75,
                       name="state.%s.act.%s.%d" % (nm, b.pid, k), theme=th)
        for m in self.msgs:
            if m.src == m.dst:
                nb = next(bb for bb in bars if bb.msg == m.n and bb.pid == m.dst and bb.y0 > m.y)
                tgt = nb.box(X[m.dst])
                pts = [(m.x0, m.y), (m.x0 + 0.30, m.y), (m.x0 + 0.30, tgt.y + 0.06), (tgt.r, tgt.y + 0.06)]
            else:
                pts = [(m.x0, m.y), (m.x1, m.y)]
            draw_line(slide, pts, m.kind, "%s.msg.%d" % (nm, m.n), th)
            _knockout(slide, m.lbox, m.paras, "%s.msg.%d.label" % (nm, m.n), th)
        for k, f in enumerate(sorted(self.frags, key=lambda f: -f.depth)):
            tp = [Para((Run(f.op, role="paper", bold=True, size=LABEL_PT),), align="center")]
            tw_ = _line_w(tp[0].runs, th) + 0.14
            tab = Box(f.box.x, f.box.y - TAB_H, tw_, TAB_H)
            sh = prims.rect(slide, tab, fill="navy", name="%s.frag.%d.tab" % (nm, k), theme=th)
            txt.write(sh.text_frame, tp, th, measure.ZERO, anchor="middle", background="navy")
            gp = [Para((Run("[%s]" % f.guard, role="ink", size=LABEL_PT),))]
            gw, gh = _label_box(gp, th)
            if tab.r + 0.06 + gw > f.box.r:
                raise Overflows("fragment %s guard" % f.op, need=round(gw, 3), have=round(f.box.r - tab.r - 0.06, 3))
            txt.textbox(slide, Box(tab.r + 0.06, tab.b - gh - 0.01, gw, gh), gp, "%s.frag.%d.guard" % (nm, k), th,
                        insets=LABEL_INS, anchor="bottom")
        marks = 0
        for p in order:
            P = self.parts[p]
            hb = Box(X[p] - head_w / 2, head_y, head_w, HEAD_H)
            prims.card(slide, hb, fill="card", line="hairline", name="%s.head.%s" % (nm, p), theme=th)
            mb = Box(hb.x + 0.06, hb.cy - self.mark / 2, self.mark, self.mark)
            draw_mark(slide, P.mark, mb, "%s.head.%s.mark" % (nm, p), P.name, th)
            marks += 1
            tb = Box(mb.r + 0.06, hb.y + 0.04, hb.r - 0.03 - mb.r - 0.06, HEAD_H - 0.08)
            txt.textbox(slide, tb, self._head_paras(P), "%s.head.%s.caption" % (nm, p), th, background="card",
                        anchor="middle")
        if bandbox:
            label = band[0]
            bp = [Para((Run(label, role="ink", bold=True, size=GROUP_PT),))]
            bw = _line_w(bp[0].runs, th, GROUP_PT) + 0.04
            if bw > bandbox.w - 0.20:
                raise Overflows("band label", need=round(bw, 3), have=round(bandbox.w - 0.20, 3))
            txt.textbox(slide, Box(bandbox.x + 0.10, bandbox.y + 0.05, bw, _need_h(bp, bw, th)), bp,
                        "%s.band.label" % nm, th)
        if legend:
            kinds = [k for k in SEQ_KINDS if any(m.kind == k for m in self.msgs)]
            y = box.b - LEG_H

            def sample(kind):
                def draw(x, yc, k):
                    dash, wt, _h, _l = KINDS[kind]
                    sh = prims.hairline(slide, (x, yc), (x + KEY_W, yc), role=LINE_ROLE, weight_pt=wt,
                                        name="state.%s.legend.key.%s" % (nm, kind), theme=th)
                    if dash:
                        prims.set_line(sh, LINE_ROLE, wt, theme=th, dash=dash)
                    return KEY_W
                return draw
            _key_row(slide, box.x, y, [(k, sample(k), KEY_TEXT[k]) for k in kinds], nm, th, box.r)
        self._metrics = {"participants": n, "messages": len(self.msgs), "labelled": len(self.msgs),
                         "fragments": len(self.frags), "bands": len(self.bands), "marks": marks,
                         "activations": len(bars), "pitch": round(pitch, 3), "message_pitch": round(pitch_m, 3)}
        return dict(self._metrics)

    def metrics(self) -> dict:
        return dict(self._metrics)


# ============================================================================================== DFD and C4 boards

@dataclass
class _Node:
    id: str
    kind: str
    name: str
    desc: str | None
    at: tuple
    span: tuple = (1, 1)
    mark: str | None = None
    ident: str | None = None
    tech: str | None = None
    scope: bool = True
    size: tuple | None = None
    box: Box | None = None


@dataclass
class _Bound:
    id: str
    label: str
    at: tuple
    kind: str
    parent: str | None
    box: Box | None = None
    lbox: Box | None = None
    depth: int = 0


@dataclass
class _Flow:
    src: str
    dst: str
    label: str
    kind: str = "data"
    step: int | None = None
    control: str | None = None
    route: str | None = None
    exit: float | None = None
    enter: float | None = None
    bend: float | None = None
    pts: list = field(default_factory=list)
    lbox: Box | None = None
    paras: list | None = None
    crossings: list = field(default_factory=list)


BOUND_STYLE = {          # kind: (line role, weight, dash)
    "trust": ("ink-muted", 1.25, "dash"),
    "zone": ("accent-deep", 1.0, "dash"),
    "enterprise": ("ink-muted", 1.0, "dash"),
    "system": ("accent-deep", 1.0, "dash"),
}
MARKER = 0.12              # a crossing marker (spec 3.8: 0.14in; 0.12 keeps it under P05's 0.10in half-overlap)
NODE_MARK = 0.24           # a mark beside a DFD name (spec 3.8: 0.24in, left of the process name)
C4_MARK = 0.28
TAB_ID = 0.22              # the process id band
HUG = 0.13                 # a boundary's foot below the lowest thing it holds
CHIP_OFF = 0.12            # a control chip off its line: a knock-out label (0.075in half height) passes beside it


class Board:
    """The shared engine of DFD and C4: boxes on a measured grid, dashed boundaries over cell spans, orthogonal
    labelled flows routed edge to edge, never crossed and never along a boundary."""

    notation = "board"
    SIZES: dict = {}
    KIND_SET: tuple = ()
    MARKERS = False            # crossing markers are threat-model notation (DFD only)

    def __init__(self, grid=(4, 3), *, weights=None, row_weights=None):
        self.cols, self.rows = grid
        self.weights = list(weights or [1.0] * self.cols)
        self.row_weights = list(row_weights or [1.0] * self.rows)
        if len(self.weights) != self.cols or len(self.row_weights) != self.rows:
            raise GeometryError("board weights", need=(self.cols, self.rows),
                                have=(len(self.weights), len(self.row_weights)))
        self.nodes: dict[str, _Node] = {}
        self.bounds: dict[str, _Bound] = {}
        self.flows: list[_Flow] = []
        self._metrics: dict = {}
        self.draft, self.problems = False, []

    # ---- declaration
    def boundary(self, id, label, at, *, kind=None, parent=None):
        """A dashed boundary over the grid span at=(col, row, cols, rows). Its label states a fact after a middot."""
        _check_id("boundary id", id)
        kind = kind or self._default_bound
        if kind not in BOUND_STYLE:
            raise GeometryError("boundary %s kind" % id, need=" / ".join(BOUND_STYLE), have=kind)
        if "·" not in label:
            raise GeometryError("boundary %s label %r" % (id, label), need="a fact after a middot "
                                "('AWS account · production')", have="a bare name",
                                hint="spec 1.6: an unlabelled or bare dashed zone is decoration")
        if parent is not None and parent not in self.bounds:
            raise GeometryError("boundary %s parent" % id, need="a declared boundary", have=parent)
        self._span_ok("boundary %s" % id, at)
        self.bounds[id] = _Bound(id, label, tuple(at), kind, parent)
        return self

    def _span_ok(self, what, at):
        c, r, cs, rs = at
        if c < 0 or r < 0 or cs <= 0 or rs <= 0 or c + cs > self.cols + 1e-9 or r + rs > self.rows + 1e-9:
            raise GeometryError(what, need="a span inside the %dx%d grid" % (self.cols, self.rows), have=at)

    def _node(self, id, kind, name, desc, at, *, span=(1, 1), mark=None, ident=None, tech=None, scope=True,
              size=None):
        _check_id("node id", id)
        if id in self.nodes:
            raise GeometryError("node %s" % id, need="a new id", have="declared twice")
        if kind not in self.KIND_SET:
            raise GeometryError("node %s kind" % id, need=" / ".join(self.KIND_SET), have=kind)
        self._span_ok("node %s" % id, (at[0], at[1], span[0], span[1]))
        if mark:
            check_mark(mark)
        self.nodes[id] = _Node(id, kind, name, desc, tuple(at), tuple(span), mark, ident, tech, scope, size)
        return self

    def flow(self, src, dst, label, *, kind="data", step=None, control=None, route=None, exit=None, enter=None,
             bend=None):
        """A labelled flow from src to dst. route forces a shape ('h', 'v', 'hv', 'vh', 'hvh', 'vhv'); exit and
        enter set the port as a fraction along the side (0 top or left, 1 bottom or right); bend places the middle
        leg of a Z as a fraction of the gap. control is the chip a boundary-crossing flow carries."""
        for p in (src, dst):
            if p not in self.nodes:
                raise GeometryError("flow %s to %s" % (src, dst), need="declared nodes", have=p)
        if src == dst:
            raise GeometryError("flow %s" % src, need="two different nodes", have="a loop")
        if kind not in ("data", "async", "control"):
            raise GeometryError("flow kind", need="data / async / control", have=kind)
        if route is not None and route not in ("h", "v", "hv", "vh", "hvh", "vhv"):
            raise GeometryError("flow route", need="h, v, hv, vh, hvh or vhv", have=route)
        self.flows.append(_Flow(src, dst, _check_label("flow %s to %s label" % (src, dst), label), kind, step,
                                control, route, exit, enter, bend))
        return self

    # ---- layout
    def _cells(self, area: Box):
        tw, th_ = sum(self.weights), sum(self.row_weights)
        xs, ys = [area.x], [area.y]
        for w in self.weights:
            xs.append(xs[-1] + area.w * w / tw)
        for h in self.row_weights:
            ys.append(ys[-1] + area.h * h / th_)
        return xs, ys

    def _bound_depth(self, b: _Bound) -> int:
        d, p = 0, b.parent
        while p is not None:
            d += 1
            p = self.bounds[p].parent
        return d

    def _node_paras(self, n: _Node, ink: str, muted: str):
        raise NotImplementedError

    @staticmethod
    def _at(edges, v: float) -> float:
        """A grid coordinate (an edge index, fractions allowed) to inches: 1.5 is the middle of column 1."""
        k = min(max(int(math.floor(v)), 0), len(edges) - 2)
        return edges[k] + (edges[k + 1] - edges[k]) * (v - k)

    def _layout(self, area: Box, th):
        xs, ys = self._cells(area)
        X = lambda v: self._at(xs, v)                     # noqa: E731
        Y = lambda v: self._at(ys, v)                     # noqa: E731
        for b in self.bounds.values():
            c, r, cs, rs = b.at
            b.depth = self._bound_depth(b)
            ins = 0.06 + 0.16 * b.depth
            b.box = Box(X(c) + ins, Y(r) + ins, X(c + cs) - X(c) - 2 * ins, Y(r + rs) - Y(r) - 2 * ins)
            lp = [Para((Run(b.label, role="ink", bold=True, size=GROUP_PT),))]
            lw = _line_w(lp[0].runs, th, GROUP_PT) + 0.04
            if lw > b.box.w - 0.20:
                raise Overflows("boundary %s label" % b.id, need=round(lw, 3), have=round(b.box.w - 0.20, 3))
            b.lbox = Box(b.box.x + 0.10, b.box.y + 0.05, lw, _need_h(lp, lw, th))
            b.lparas = lp
        for n in self.nodes.values():
            c, r = n.at
            cs, rs = n.span
            cx, cy = X(c + cs / 2.0), Y(r + rs / 2.0)
            w, h = self._size(n, th)
            n.box = Box(cx - w / 2, cy - h / 2, w, h)
            if not _inside(n.box, area, 1e-6):
                self._problem(Overflows("node %s" % n.id, need="inside the diagram area", have=n.box,
                                        hint="a wider column or a smaller node"))
        self._hug()
        self._check_layout()

    def _hug(self):
        """A boundary's foot hugs what it holds (HUG below the lowest node or nested boundary), so its label at the
        top and its content stay balanced (gate P08); the innermost boundaries first."""
        for b in sorted(self.bounds.values(), key=lambda b: -b.depth):
            low = [n.box.b for n in self.nodes.values() if _inside(n.box, b.box, 0.13)]
            low += [c.box.b for c in self.bounds.values() if c.parent == b.id]
            if low:
                foot = max(low) + HUG
                if foot < b.box.b:
                    b.box = Box(b.box.x, b.box.y, b.box.w, foot - b.box.y)

    def _size(self, n: _Node, th):
        w, h = n.size or self.SIZES[n.kind]
        need = self._text_need(n, w, th)
        return w, max(h, need)

    def _check_layout(self):
        P = self._problem
        ns = list(self.nodes.values())
        for i, a in enumerate(ns):
            for b in ns[i + 1:]:
                if _inter(a.box, b.box, 0.15):
                    P(GeometryError("nodes %s and %s" % (a.id, b.id), need="0.15in apart", have="overlapping",
                                    hint="another cell, or a wider grid column"))
            for bd in self.bounds.values():
                inside = _inside(a.box, bd.box.inset(0.12))
                apart = not _inter(a.box, bd.box, 0.12)
                if not (inside or apart):
                    P(GeometryError("node %s and boundary %s" % (a.id, bd.id), need="wholly inside (0.12in clear) "
                                    "or outside", have="on its edge", hint="a narrower node or a wider column"))
                if inside and _inter(a.box, bd.lbox, 0.06):
                    P(GeometryError("node %s" % a.id, need="clear of boundary %s's label" % bd.id, have="under it",
                                    hint="a lower row, or a taller first row"))
        bs = list(self.bounds.values())
        for i, a in enumerate(bs):
            for b in bs[i + 1:]:
                if _inter(a.box, b.box) and not (_inside(a.box, b.box) or _inside(b.box, a.box)):
                    P(GeometryError("boundaries %s and %s" % (a.id, b.id), need="nested or apart",
                                    have="overlapping"))

    # ---- routing
    def _ports(self, A: Box, side: str, frac: float):
        if side == "l":
            return (A.x, A.y + A.h * frac)
        if side == "r":
            return (A.r, A.y + A.h * frac)
        if side == "t":
            return (A.x + A.w * frac, A.y)
        return (A.x + A.w * frac, A.b)

    def _candidates(self, f: _Flow, A: Box, B: Box):
        out = []
        fr = (0.5, 0.3, 0.7, 0.2, 0.8)
        ex = (f.exit,) if f.exit is not None else fr
        en = (f.enter,) if f.enter is not None else fr
        bends = (f.bend,) if f.bend is not None else (0.5, 0.3, 0.7)
        hs = "r" if B.cx >= A.cx else "l"          # horizontal exit side toward B
        vs = "b" if B.cy >= A.cy else "t"
        hin = "l" if hs == "r" else "r"
        vin = "t" if vs == "b" else "b"
        # straight
        lo, hi = max(A.y, B.y) + 0.08, min(A.b, B.b) - 0.08
        if hi > lo and (B.x >= A.r + 0.2 or A.x >= B.r + 0.2):
            for t in ((f.exit,) if f.exit is not None else (0.5, 0.3, 0.7, 0.15, 0.85)):
                y = (A.y + A.h * t) if f.exit is not None else lo + (hi - lo) * t
                if lo - 1e-6 <= y <= hi + 1e-6:
                    out.append(("h", [(A.r if hs == "r" else A.x, y), (B.x if hs == "r" else B.r, y)]))
        lo, hi = max(A.x, B.x) + 0.08, min(A.r, B.r) - 0.08
        if hi > lo and (B.y >= A.b + 0.2 or A.y >= B.b + 0.2):
            for t in ((f.exit,) if f.exit is not None else (0.5, 0.3, 0.7, 0.15, 0.85)):
                x = (A.x + A.w * t) if f.exit is not None else lo + (hi - lo) * t
                if lo - 1e-6 <= x <= hi + 1e-6:
                    out.append(("v", [(x, A.b if vs == "b" else A.y), (x, B.y if vs == "b" else B.b)]))
        for a in ex:
            for b in en:
                # hv: leave A sideways, drop into B's top or bottom
                p = self._ports(A, hs, a)
                q = self._ports(B, vin, b)
                out.append(("hv", [p, (q[0], p[1]), q]))
                # vh: leave A's top or bottom, enter B's side
                p = self._ports(A, vs, a)
                q = self._ports(B, hin, b)
                out.append(("vh", [p, (p[0], q[1]), q]))
                for t in bends:
                    p = self._ports(A, hs, a)
                    q = self._ports(B, hin, b)
                    gx0, gx1 = (A.r, B.x) if hs == "r" else (B.r, A.x)
                    xm = gx0 + (gx1 - gx0) * t
                    out.append(("hvh", [p, (xm, p[1]), (xm, q[1]), q]))
                    p = self._ports(A, vs, a)
                    q = self._ports(B, vin, b)
                    gy0, gy1 = (A.b, B.y) if vs == "b" else (B.b, A.y)
                    ym = gy0 + (gy1 - gy0) * t
                    out.append(("vhv", [p, (p[0], ym), (q[0], ym), q]))
        if f.route:
            out = [o for o in out if o[0] == f.route]
        return out

    def _route_ok(self, f, pts, A, B, segs, ends):
        if len(pts) < 2:
            return False
        for p, q in zip(pts, pts[1:]):
            if abs(p[0] - q[0]) > 1e-6 and abs(p[1] - q[1]) > 1e-6:
                return False
        if _length(pts[-2:]) < LAST_LEG - 1e-6 or _length(pts[:2]) < 0.10 - 1e-6:
            return False
        sg = list(zip(pts, pts[1:]))
        for k, (p, q) in enumerate(sg):
            for n in self.nodes.values():
                if n.box is A or n.box is B:
                    inner = n.box.inset(0.01)
                    if _seg_hits(p, q, inner):
                        return False
                    continue
                if _seg_hits(p, q, n.box, 0.06):
                    return False
            for b in self.bounds.values():
                if _seg_hits(p, q, b.lbox, 0.03):
                    return False
                for e1, e2 in _edges(b.box):
                    if _along(p, q, e1, e2, 0.10):
                        return False
            for e1, e2 in segs:
                if _cross(p, q, e1, e2) or _along(p, q, e1, e2, 0.12):
                    return False
        for e in ends:
            for pt in (pts[0], pts[-1]):
                if math.hypot(pt[0] - e[0], pt[1] - e[1]) < 0.14:
                    return False
        return True

    def _route(self, th):
        segs, ends = [], []
        for f in self.flows:
            A, B = self.nodes[f.src].box, self.nodes[f.dst].box
            best = None
            for shape, pts in self._candidates(f, A, B):
                pts = _clean(pts)
                if not self._route_ok(f, pts, A, B, segs, ends):
                    continue
                score = (len(pts) - 2) * 1.5 + _length(pts) + (0.2 if shape in ("hvh", "vhv") else 0.0)
                if best is None or score < best[0] - 1e-9:
                    best = (score, pts)
            if best is None:
                self._problem(GeometryError("flow %s to %s" % (f.src, f.dst), need="a clear orthogonal route",
                                            have="none", hint="re-seat a node, or set route=, exit=, enter= or bend="))
                A_, B_ = A, B
                best = (0, [(A_.cx, A_.cy), (B_.cx, A_.cy), (B_.cx, B_.cy)] if abs(A_.cx - B_.cx) > 1e-6 and
                        abs(A_.cy - B_.cy) > 1e-6 else [(A_.cx, A_.cy), (B_.cx, B_.cy)])
            f.pts = best[1]
            segs.extend(zip(f.pts, f.pts[1:]))
            ends.extend((f.pts[0], f.pts[-1]))

    def _crossings(self):
        for f in self.flows:
            f.crossings = []
            for p, q in zip(f.pts, f.pts[1:]):
                for b in self.bounds.values():
                    for e1, e2 in _edges(b.box):
                        if _cross(p, q, e1, e2):
                            if _horiz(p, q):
                                pt = (e1[0], p[1])
                            else:
                                pt = (p[0], e1[1])
                            f.crossings.append((pt, (p, q), b.id))

    # ---- placement of labels, badges, markers and chips
    def _free(self, bx: Box, hard, segs, own=None, own_on=False):
        for h in hard:
            if _inter(bx, h, CLEAR):
                return False
        for (p, q), fid in segs:
            if own is not None and fid == own and own_on:
                continue
            if _seg_hits(p, q, bx, CLEAR):
                return False
        for b in self.bounds.values():
            if _inter(bx, b.box, 0.05) and not _inside(bx, b.box.inset(0.05)):
                return False                                # on or within 0.05in of a boundary edge
        return True

    def _place_labels(self, th, area: Box, hard, segs):
        """Each flow's label on its longest clear leg: knocked out on a horizontal leg (0.06in clear of the start,
        0.12in of an arrowhead), or beside a vertical one."""
        ts = (0.5, 0.4, 0.6, 0.3, 0.7, 0.2, 0.8, 0.1, 0.9, 0.0, 1.0)
        for k, f in enumerate(self.flows):
            f.paras = [Para((Run(f.label, role="ink", size=LABEL_PT),))]
            w, h = _label_box(f.paras, th)
            last = len(f.pts) - 2
            sg = sorted(enumerate(zip(f.pts, f.pts[1:])), key=lambda s_: -_length(s_[1]))
            placed = None
            for j, (p, q) in sg:
                L = _length((p, q))
                m0 = 0.10 if j == 0 and f.step is not None else 0.06    # the source end, and its badge
                m1 = 0.12 if j == last else 0.06
                if _horiz(p, q):
                    if L < w + m0 + m1:
                        continue
                    sgn = 1 if q[0] > p[0] else -1
                    for t in ts:
                        d = m0 + (L - m0 - m1 - w) * t
                        x = p[0] + d if sgn > 0 else p[0] - d - w
                        bx = Box(x, p[1] - h / 2, w, h)
                        if _inside(bx, area) and self._free(bx, hard, segs, k, own_on=True) and \
                                self._on_own_only(bx, f, segs, k):
                            placed = bx
                            break
                else:
                    if L < h + m0 + m1:
                        continue
                    sgn = 1 if q[1] > p[1] else -1
                    for t in ts:
                        d = m0 + (L - m0 - m1 - h) * t
                        y = p[1] + d if sgn > 0 else p[1] - d - h
                        for side in (1, -1):
                            x = p[0] + 0.05 if side > 0 else p[0] - 0.05 - w
                            bx = Box(x, y, w, h)
                            if _inside(bx, area) and self._free(bx, hard, segs):
                                placed = bx
                                break
                        if placed:
                            break
                if placed:
                    break
            if placed is None:
                self._problem(Overflows("flow %s to %s label %r" % (f.src, f.dst, f.label), need=round(w, 3),
                                        have="no clear segment", hint="cut words, or lengthen a leg (move a node)"))
                continue
            f.lbox = placed
            hard.append(placed)

    def _on_own_only(self, bx, f, segs, k):
        """A knock-out on its own line: it may cover only that line, not a turn of it."""
        for (p, q), fid in segs:
            if fid == k and not _horiz(p, q) and _seg_hits(p, q, bx, CLEAR):
                return False
        return True

    def _place_badges(self, hard, segs, area):
        out = []
        for k, f in enumerate(self.flows):
            if f.step is None:
                continue
            placed = None
            legs = [(f.pts[0], f.pts[1]), (f.pts[-1], f.pts[-2])]      # beside the source end, else the target end
            for p, q in legs:
                L = _length((p, q))
                dx = (q[0] - p[0]) / L if L else 0
                dy = (q[1] - p[1]) / L if L else 0
                for d in (0.06, 0.12, 0.20, 0.30):
                    if d + BADGE > L - 0.05:
                        break
                    for side in (-1, 1):
                        cx = p[0] + dx * (d + BADGE / 2)
                        cy = p[1] + dy * (d + BADGE / 2)
                        off = BADGE / 2 + 0.05
                        if _horiz(p, q):
                            cy += side * off
                        else:
                            cx += side * off
                        bx = Box(cx - BADGE / 2, cy - BADGE / 2, BADGE, BADGE)
                        if _inside(bx, area) and self._free(bx, hard, segs):
                            placed = bx
                            break
                    if placed:
                        break
                if placed:
                    break
            if placed is None:
                self._problem(GeometryError("flow %s to %s step badge" % (f.src, f.dst), need="room beside its "
                                            "first leg", have="none", hint="lengthen the first leg"))
                continue
            hard.append(placed)
            out.append((f, placed))
        return out

    def _place_chips(self, hard, segs, area, th):
        chips = []
        for k, f in enumerate(self.flows):
            if not f.crossings:
                continue
            if not f.control:
                continue
            cp = [Para((Run(f.control, role="ink", size=LABEL_PT),), align="center")]
            w = _line_w(cp[0].runs, th) + 0.16
            h = 0.20
            placed = None
            for (pt, (p, q), _b) in f.crossings:
                for c in self._chip_cands(pt, p, q, w, h):
                    if _inside(c, area) and self._free(c, hard, segs):
                        placed = c
                        break
                if placed:
                    break
            if placed is None:
                self._problem(GeometryError("flow %s to %s control chip %r" % (f.src, f.dst, f.control),
                                            need="room beside a crossing", have="none",
                                            hint="shorten the control, or move a node"))
                continue
            hard.append(placed)
            chips.append((f, placed, cp))
        return chips

    @staticmethod
    def _chip_cands(pt, p, q, w, h):
        """Chip boxes beside the crossing leg: at the intercept first, then sliding along the leg either way, on
        both sides of the line."""
        out = []
        if _horiz(p, q):
            lo, hi = sorted((p[0], q[0]))
            for d in (0.10, 0.30, 0.55, 0.85, 1.2):
                for sx in (1, -1):
                    x = pt[0] + d if sx > 0 else pt[0] - d - w
                    for sy in (-1, 1):                  # clear of a knock-out label on the same line
                        y = pt[1] - CHIP_OFF - h if sy < 0 else pt[1] + CHIP_OFF
                        out.append(Box(x, y, w, h))
        else:
            lo, hi = sorted((p[1], q[1]))
            for d in (0.10, 0.30, 0.55, 0.85, 1.2):
                for sy in (1, -1):
                    y = pt[1] + d if sy > 0 else pt[1] - d - h
                    for sx in (1, -1):
                        x = pt[0] + CHIP_OFF if sx > 0 else pt[0] - CHIP_OFF - w
                        out.append(Box(x, y, w, h))
        return out

    def _check_semantics(self):
        pass

    def _legend_items(self, slide, nm, th):
        return []

    def _number(self):
        pass

    def _problem(self, err):
        if not self.draft:
            raise err
        self.problems.append(str(err))

    def render(self, slide, box: Box, theme=None, name: str | None = None, *, legend: bool = True,
               draft: bool = False) -> dict:
        """Lay out, route and draw. draft=True lists what does not fit (metrics["problems"]) and draws the rest,
        for iterating on a layout; never for a slide that ships."""
        th = prims.theme_of(theme)
        nm = name or self.notation
        self.draft, self.problems = draft, []
        self._number()
        self._check_semantics()
        area = Box(box.x, box.y, box.w, box.h - (LEG_H + 0.06 if legend else 0.0))
        self._layout(area, th)
        self._route(th)
        self._crossings()
        self._check_crossings()
        hard = [n.box for n in self.nodes.values()] + [b.lbox for b in self.bounds.values()]
        segs = [((p, q), k) for k, f in enumerate(self.flows) for p, q in zip(f.pts, f.pts[1:])]
        markers = [(f, Box(pt[0] - MARKER / 2, pt[1] - MARKER / 2, MARKER, MARKER))
                   for f in self.flows for (pt, _sg, _b) in f.crossings] if self.MARKERS else []
        for f, mb in markers:
            for h in hard:
                if _inter(mb, h, 0.01):
                    self._problem(GeometryError("flow %s to %s crossing marker" % (f.src, f.dst), need="a clear intercept",
                                        have="under a node or a boundary label", hint="move the node or the route"))
                    break
        hard += [mb for _f, mb in markers]
        badges = self._place_badges(hard, segs, area)
        chips = self._place_chips(hard, segs, area, th)        # anchored at an intercept: before the labels slide
        self._place_labels(th, area, hard, segs)
        # ---- draw: boundaries, nodes, flows, labels, badges, markers, chips, legend
        for b in sorted(self.bounds.values(), key=lambda b: b.depth):
            role, wt, dash = BOUND_STYLE[b.kind]
            sh = prims.rect(slide, b.box, fill=None, line=role, weight_pt=wt, name="%s.bound.%s" % (nm, b.id),
                            theme=th)
            prims.set_line(sh, role, wt, theme=th, dash=dash)
        marks = 0
        for n in self.nodes.values():
            marks += self._draw_node(slide, n, nm, th)
        for b in self.bounds.values():
            txt.textbox(slide, b.lbox, b.lparas, "%s.bound.%s.label" % (nm, b.id), th)
        for k, f in enumerate(self.flows):
            draw_line(slide, f.pts, f.kind, "%s.flow.%d" % (nm, k + 1), th)
        for k, f in enumerate(self.flows):
            if f.lbox is not None:
                _knockout(slide, f.lbox, f.paras, "%s.flow.%d.label" % (nm, k + 1), th)
        for f, bx in badges:
            prims.disc(slide, bx, f.step, fill=BADGE_FILL, pt=BADGE_PT, name="%s.step.%d" % (nm, f.step), theme=th)
        for k, (f, mb) in enumerate(markers):
            prims.rect(slide, mb, fill="ink-strong", name="state.%s.cross.%d" % (nm, k + 1), theme=th)
        for k, (f, cb, cp) in enumerate(chips):
            prims.pill(slide, cb, f.control, fill="card", pt=LABEL_PT, name="%s.control.%d" % (nm, k + 1), theme=th)
        if legend:
            items = self._legend_items(slide, nm, th)
            if items:
                _key_row(slide, box.x, box.b - LEG_H, items, nm, th, box.r)
        cross = sum(1 for f in self.flows if f.crossings)
        self._metrics = {"nodes": len(self.nodes), "flows": len(self.flows), "labelled": len(self.flows),
                         "boundaries": len(self.bounds), "crossing_flows": cross, "markers": len(markers),
                         "chips": len(chips), "steps": len(badges), "marks": marks}
        if draft:
            self._metrics["problems"] = list(self.problems)
        return dict(self._metrics)

    def _check_crossings(self):
        pass

    def metrics(self) -> dict:
        return dict(self._metrics)

    # ---- node drawing helpers
    def _text_need(self, n, w, th) -> float:
        return 0.0

    def _text_in(self, slide, n: _Node, tb: Box, paras, nm, th, ground, anchor="middle"):
        need = _need_h(paras, tb.w, th)
        if need > tb.h + 1e-6:
            raise Overflows("%s %s text" % (n.kind, n.id), need=round(need, 3), have=round(tb.h, 3),
                            hint="cut words; a box holds a name and one or two short lines")
        return txt.textbox(slide, tb, paras, "%s.node.%s.text" % (nm, n.id), th, background=ground, anchor=anchor)


# ---------------------------------------------------------------------------------------------- DFD

class DFD(Board):
    """A data flow diagram and threat model (spec 3.8), Gane-Sarson: processes with an id band, external entities,
    stores open on the right, trust boundaries, numbered labelled flows, crossing markers and control chips.
    level='context' asserts one process and no store; threat=True (the default) requires a control on every flow
    that crosses a trust boundary."""

    notation = "dfd"
    KIND_SET = ("process", "entity", "store")
    SIZES = {"process": (1.35, 0.66), "entity": (1.45, 0.62), "store": (1.65, 0.44)}
    MARKERS = True
    _default_bound = "trust"

    def __init__(self, grid=(5, 3), *, weights=None, row_weights=None, level: str = "1", threat: bool = True):
        super().__init__(grid, weights=weights, row_weights=row_weights)
        if level not in ("context", "1", "2"):
            raise GeometryError("dfd level", need="context, 1 or 2", have=level)
        self.level = level
        self.threat = threat

    def process(self, id, ident, name, *, at, tech=None, mark=None, span=(1, 1), size=None):
        if not re.fullmatch(r"\d+(\.\d+)?", str(ident)):
            raise GeometryError("process %s id" % id, need="a number: 0, 1..n or 3.1", have=ident)
        return self._node(id, "process", name, None, at, span=span, mark=mark, ident=str(ident), tech=tech,
                          size=size)

    def entity(self, id, name, role=None, *, at, mark=None, out_of_scope=False, size=None):
        return self._node(id, "entity", name, role, at, mark=mark, scope=not out_of_scope, size=size)

    def store(self, id, ident, name, *, at, mark=None, size=None):
        if not re.fullmatch(r"D\d+", str(ident)):
            raise GeometryError("store %s id" % id, need="D1, D2, ...", have=ident)
        return self._node(id, "store", name, None, at, mark=mark, ident=str(ident), size=size)

    def _number(self):
        used = {f.step for f in self.flows if f.step is not None}
        n = 1
        for f in self.flows:
            if f.step is None:
                while n in used:
                    n += 1
                f.step = n
                used.add(n)
        steps = sorted(f.step for f in self.flows)
        if steps != list(range(1, len(steps) + 1)):
            raise GeometryError("dfd flow numbers", need="1..N without a gap or a repeat", have=steps)

    def _check_semantics(self):
        procs = [n for n in self.nodes.values() if n.kind == "process"]
        stores = [n for n in self.nodes.values() if n.kind == "store"]
        if self.level == "context" and (len(procs) != 1 or stores):
            raise GeometryError("context DFD", need="exactly 1 process and no store", have="%d processes, %d stores"
                                % (len(procs), len(stores)))
        if self.level != "context" and not 2 <= len(procs) <= 9:
            raise Capacity("dfd processes", need=len(procs), have="3 to 9 (7 target)",
                           hint="spec 3.8: merge processes past 9, decompose under 3")
        for f in self.flows:
            if "process" not in (self.nodes[f.src].kind, self.nodes[f.dst].kind):
                raise GeometryError("flow %s to %s" % (f.src, f.dst), need="a process at one end",
                                    have="%s to %s" % (self.nodes[f.src].kind, self.nodes[f.dst].kind),
                                    hint="DFD: no entity to entity, entity to store or store to store flow")

    def _check_crossings(self):
        if not self.threat:
            return
        for f in self.flows:
            if f.crossings and not f.control:
                raise GeometryError("flow %s to %s" % (f.src, f.dst), need="a control chip (control='HTTPS · OIDC')",
                                    have="crosses %d boundary edge(s) without one" % len(f.crossings),
                                    hint="spec 3.8: every flow that crosses a trust boundary carries its control")
            if f.control and not f.crossings:
                raise GeometryError("flow %s to %s control" % (f.src, f.dst), need="a boundary crossing",
                                    have="none", hint="a control chip belongs on a flow that crosses a boundary")

    def _paras(self, n: _Node, ground):
        ink = "ink" if n.scope else "ink-muted"
        out = [Para((Run(n.name, role=ink, bold=True, size=NAME_PT),))]
        if n.desc:
            out.append(Para((Run(n.desc, role="ink-muted", size=ROLE_PT),)))
        return out

    def _text_w(self, n: _Node, w):
        if n.kind == "store":
            return w - 0.42 - (NODE_MARK + 0.06 if n.mark else 0) - 0.08
        return w - 0.16 - (NODE_MARK + 0.06 if n.mark else 0)

    def _text_need(self, n, w, th):
        need = _need_h(self._paras(n, None), self._text_w(n, w), th)
        if n.kind == "process":
            return TAB_ID + 0.08 + need + 0.08
        return need + 0.14

    def _draw_node(self, slide, n: _Node, nm, th) -> int:
        b = n.box
        base = "%s.node.%s" % (nm, n.id)
        marks = 0
        if n.kind == "process":
            prims.card(slide, b, fill="paper", line="rule-strong", name=base, theme=th)
            prims.hairline(slide, (b.x, b.y + TAB_ID), (b.r, b.y + TAB_ID), role="hairline", name=base + ".rule",
                           theme=th)
            idp = [Para((Run(n.ident, role="ink", bold=True, size=NAME_PT),
                         *((Run("  " + n.tech, role="ink-muted", size=ROLE_PT),) if n.tech else ())))]
            iw = b.w - 0.16
            txt.textbox(slide, Box(b.x + 0.08, b.y + 0.045, iw, TAB_ID - 0.055), idp, base + ".id", th,
                        background="paper", anchor="middle")
            body = Box(b.x, b.y + TAB_ID, b.w, b.h - TAB_ID)
            ground = "paper"
        elif n.kind == "entity":
            if n.scope:
                prims.rect(slide, b, fill="card", name=base, theme=th)
                ground = "card"
            else:
                sh = prims.rect(slide, b, fill=None, line="ink-muted", weight_pt=1.0, name=base, theme=th)
                prims.set_line(sh, "ink-muted", 1.0, theme=th, dash="dash")
                ground = "paper"
            body = b
        else:
            prims.rect(slide, b, fill="paper", name=base, theme=th)
            for k, (p, q) in enumerate((((b.x, b.y), (b.r, b.y)), ((b.x, b.b), (b.r, b.b)), ((b.x, b.y), (b.x, b.b)),
                                        ((b.x + 0.42, b.y), (b.x + 0.42, b.b)))):
                prims.hairline(slide, p, q, role="rule-strong", name="%s.edge.%d" % (base, k), theme=th)
            sp = [Para((Run(n.ident, role="ink", bold=True, size=NAME_PT),), align="center")]
            txt.textbox(slide, Box(b.x + 0.03, b.y + 0.04, 0.36, b.h - 0.08), sp, base + ".id", th, anchor="middle")
            body = Box(b.x + 0.42, b.y, b.w - 0.42, b.h)
            ground = "paper"
        x = body.x + 0.08
        if n.mark:
            mb = Box(x, body.cy - NODE_MARK / 2, NODE_MARK, NODE_MARK)
            draw_mark(slide, n.mark, mb, base + ".mark", n.name, th, role="ink-strong" if n.scope else "ink-muted")
            marks += 1
            x = mb.r + 0.06
        tb = Box(x, body.y + 0.05, body.r - 0.08 - x, body.h - 0.10)
        self._text_in(slide, n, tb, self._paras(n, ground), nm, th, ground)
        return marks

    def _legend_items(self, slide, nm, th):
        items = []
        kinds = sorted({b.kind for b in self.bounds.values()}, key=list(BOUND_STYLE).index)
        for kind in kinds:
            def draw(x, yc, k, kind=kind):
                role, wt, dash = BOUND_STYLE[kind]
                sh = prims.hairline(slide, (x, yc), (x + KEY_W, yc), role="ink-muted", weight_pt=wt,
                                    name="state.%s.legend.key.%s" % (nm, kind), theme=th)
                prims.set_line(sh, role, wt, theme=th, dash=dash)
                return KEY_W
            items.append((kind, draw, "Trust boundary" if kind == "trust" else "Trust zone"))
        if any(f.crossings for f in self.flows):
            def drawx(x, yc, k):
                prims.rect(slide, Box(x + KEY_W / 2 - MARKER / 2, yc - MARKER / 2, MARKER, MARKER), fill="ink-strong",
                           name="state.%s.legend.key.cross" % nm, theme=th)
                prims.hairline(slide, (x, yc), (x + KEY_W, yc), role=LINE_ROLE, weight_pt=LINE_PT,
                               name="state.%s.legend.key.cross.line" % nm, theme=th)
                return KEY_W
            items.append(("cross", drawx, "Crossing, with its control"))
        if any(not n.scope for n in self.nodes.values()):
            def draws(x, yc, k):
                sh = prims.rect(slide, Box(x + 0.06, yc - 0.09, 0.33, 0.18), fill=None, line="ink-muted",
                                weight_pt=1.0, name="state.%s.legend.key.scope" % nm, theme=th)
                prims.set_line(sh, "ink-muted", 1.0, theme=th, dash="dash")
                return KEY_W
            items.append(("scope", draws, "Out of scope"))
        return items


# ---------------------------------------------------------------------------------------------- C4

class C4(Board):
    """C4 system context and container views (c4model.com notation) in the house: people navy, the system in
    focus solid brand, external systems card, containers paper with their technology beside a product mark, every
    relationship labelled 'intent · protocol', boundaries dashed with their fact."""

    notation = "c4"
    KIND_SET = ("person", "system", "external", "container")
    SIZES = {"person": (1.75, 0.70), "system": (2.70, 1.10), "external": (1.75, 0.70), "container": (1.90, 0.80)}
    _default_bound = "system"
    FILL = {"person": "navy", "system": "accent", "external": "card", "container": "paper"}
    TYPE = {"person": "Person", "system": "Software system", "external": "External system", "container": "Container"}

    def __init__(self, view: str = "context", grid=(4, 3), *, weights=None, row_weights=None):
        super().__init__(grid, weights=weights, row_weights=row_weights)
        if view not in ("context", "container"):
            raise GeometryError("c4 view", need="context or container", have=view)
        self.view = view

    def person(self, id, name, desc, *, at, size=None):
        return self._node(id, "person", name, desc, at, mark="glyph:user", size=size)

    PERSON_GLYPH = 0.26        # under 0.30in: notation, so the person block is not an icon boxed alone (P26 b)

    def system(self, id, name, desc, *, at, span=(1, 1), size=None, mark=None):
        return self._node(id, "system", name, desc, at, span=span, mark=mark, size=size)

    def external(self, id, name, desc, *, at, mark=None, size=None):
        return self._node(id, "external", name, desc, at, mark=mark, size=size)

    def container(self, id, name, tech, desc, *, at, mark=None, size=None):
        if self.view != "container":
            raise GeometryError("container %s" % id, need="a container view", have="a context view",
                                hint="C4: containers are drawn one level down, inside the system boundary")
        if not tech:
            raise GeometryError("container %s" % id, need="its technology", have=tech)
        return self._node(id, "container", name, desc, at, mark=mark, tech=tech, size=size)

    def rel(self, src, dst, label, **kw):
        """A relationship: what the source does to the target, and how ('reads briefs · HTTPS')."""
        return self.flow(src, dst, label, **kw)

    def _check_semantics(self):
        sys_ = [n for n in self.nodes.values() if n.kind == "system"]
        if self.view == "context" and len(sys_) != 1:
            raise GeometryError("C4 context", need="exactly one software system in focus", have=len(sys_))
        if self.view == "container" and not any(n.kind == "container" for n in self.nodes.values()):
            raise GeometryError("C4 container view", need="containers", have=0)
        if self.view == "container" and not self.bounds:
            raise GeometryError("C4 container view", need="the system boundary around its containers", have=0)

    def _ink(self, n):
        fill = self.FILL[n.kind]
        return fill, prims.ON_FILL[fill], ("ink-muted" if prims.ON_FILL[fill] == "ink" else prims.ON_FILL[fill])

    def _paras(self, n: _Node):
        fill, ink, muted = self._ink(n)
        big = 11.0 if n.kind == "system" else NAME_PT + 0.5
        kind = self.TYPE[n.kind] + (" · " + n.tech if n.tech else "")
        out = [Para((Run(n.name, role=ink, bold=True, size=big),)),
               Para((Run(kind, role=muted, size=ROLE_PT),))]
        if n.desc:
            out.append(Para((Run(n.desc, role=ink, size=ROLE_PT + (0.5 if n.kind == "system" else 0.0)),),
                            space_before=2.0))
        return out

    def _mark_side(self, n):
        return self.PERSON_GLYPH if n.kind == "person" else C4_MARK

    def _text_w(self, n, w):
        return w - 0.20 - ((self._mark_side(n) + 0.08) if n.mark else 0.0)

    def _text_need(self, n, w, th):
        return _need_h(self._paras(n), self._text_w(n, w), th) + 0.16

    def _draw_node(self, slide, n: _Node, nm, th) -> int:
        b = n.box
        base = "%s.node.%s" % (nm, n.id)
        fill, ink, muted = self._ink(n)
        if n.kind in ("person", "system"):
            prims.block(slide, b, fill=fill, name=base, theme=th)
        elif n.kind == "external":
            prims.card(slide, b, fill="card", line=None, name=base, theme=th)
        else:
            prims.card(slide, b, fill="paper", line="rule-strong", name=base, theme=th)
        x = b.x + 0.10
        marks = 0
        if n.mark:
            s = self._mark_side(n)
            mb = Box(x, b.cy - s / 2, s, s)
            draw_mark(slide, n.mark, mb, base + ".mark", n.name, th, role=ink if n.kind == "person" else "ink-strong")
            marks += 0 if n.mark.startswith("glyph:") else 1
            x = mb.r + 0.08
        tb = Box(x, b.y + 0.08, b.r - 0.10 - x, b.h - 0.16)
        self._text_in(slide, n, tb, self._paras(n), nm, th, fill)
        return marks

    def _legend_items(self, slide, nm, th):
        items = []
        for kind in self.KIND_SET:
            if not any(n.kind == kind for n in self.nodes.values()):
                continue

            def draw(x, yc, k, kind=kind):
                sb = Box(x + 0.06, yc - 0.09, 0.33, 0.18)
                if kind == "container":
                    prims.rect(slide, sb, fill="paper", line="rule-strong", name="state.%s.legend.key.%s" % (nm, kind),
                               theme=th)
                else:
                    prims.rect(slide, sb, fill=self.FILL[kind], name="state.%s.legend.key.%s" % (nm, kind), theme=th)
                return KEY_W
            items.append((kind, draw, self.TYPE[kind]))
        for kind in sorted({b.kind for b in self.bounds.values()}, key=list(BOUND_STYLE).index):
            def drawb(x, yc, k, kind=kind):
                role, wt, dash = BOUND_STYLE[kind]
                sh = prims.hairline(slide, (x, yc), (x + KEY_W, yc), role="ink-muted", weight_pt=wt,
                                    name="state.%s.legend.key.bound-%s" % (nm, kind), theme=th)
                prims.set_line(sh, role, wt, theme=th, dash=dash)
                return KEY_W
            items.append(("bound-" + kind, drawb, "System boundary" if kind == "system" else "Enterprise boundary"))
        return items


__all__ = ["Sequence", "DFD", "C4", "Board", "draw_mark", "draw_line", "check_mark", "KINDS", "OPS"]
