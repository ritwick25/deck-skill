"""Primitives: the drawn atoms every composer and device fill is built from.

Lifted, with the banned devices stripped (CLAUDE.md sections 4 and 6, engineering.md (a)):
  * pptxlib rect / card / arrow / hairline: the radius-on-a-rect refusal, the p:style strip.
    Its CARD_SHADOW and add_card_shadow are gone: a card carries no shadow at all.
  * the fabric _prim rect / connect / elbow / coin / chip / zone. Gone: add_shadow, grad_fill,
    feature_band, band, ribbon, the card's accent_top / accent_left bars, the mono kicker.
  * the fabric _pfz title underline, foot band, gradient pill and footer: none has a counterpart here.
  * the PMR kpi (hairline above the label, never a coloured left border) and quote (a left bar that says
    the words are somebody's own: the one left bar the house rules allow, named state.quote here).

Contract for every creator:
  * colours are theme roles, written as schemeClr expressions through Theme.spec; never a hex
  * ooxml.finish() runs on every shape: no <p:style>, exactly one empty effectLst
  * the caller names the shape (semantic, e.g. "pillar.2.card"); parts of a compound get name.part
  * text is measured with deckkit.measure before it is written; it never shrinks, never autofits,
    never drops below 8.0pt (BelowFloor), and refuses with Overflows when it does not fit
  * geometry the kit will not draw raises GeometryError: a radius on a non-rounded preset, an accent
    bar on a card edge (only state.* shapes may carry one), a chevron point outside 31-35% of its height

The theme is bound once with use(theme) (a context manager) or passed per call as theme=.
"""
from __future__ import annotations

import contextlib
import math
from dataclasses import dataclass

from lxml import etree

from . import measure, ooxml
from .canvas import EMU_PER_IN, FLOOR, Box, Canvas, canvas_of
from .errors import BelowFloor, GeometryError, ThemeInvariant
from .read.ns import NS

_A = "{%s}" % NS["a"]
_P = "{%s}" % NS["p"]
EMU_PT = 12700

# ------------------------------------------------------------------ theme binding

_ACTIVE = []


@contextlib.contextmanager
def use(theme):
    """Bind a Theme for the creators in this block: `with prims.use(Theme.load(...)):`."""
    _ACTIVE.append(theme)
    try:
        yield theme
    finally:
        _ACTIVE.pop()


def bind(theme):
    """Bind a Theme until the next bind (for scripts that build one deck per process)."""
    _ACTIVE[:] = [theme]
    return theme


def theme_of(theme=None):
    if theme is not None:
        return theme
    if _ACTIVE:
        return _ACTIVE[-1]
    raise ThemeInvariant("no theme bound", need="prims.use(theme) or theme=", have="none",
                         hint="roles resolve per theme (accent-ink and on-accent are solved), so a creator never guesses")


def canvas_for(slide) -> Canvas:
    """The canvas profile of the presentation a slide belongs to."""
    prs = slide.part.package.presentation_part.presentation
    return canvas_of(prs)


# ------------------------------------------------------------------ roles on text and fills

# The text role that reads on each fill role (contrast pairs are gated in theme.CONTRAST_PAIRS).
ON_FILL = {
    "paper": "ink", "card": "ink", "accent-tint": "ink", "accent-wash": "ink", "hairline-soft": "ink",
    "ink-strong": "paper", "ink-deep": "paper", "navy": "paper",
    "accent": "on-accent", "accent-deep": "on-accent",
}
CARD_FILLS = ("paper", "card", "accent-tint")
CARD_LINES = ("hairline", "rule-strong", None)
ZONE_FILLS = ("accent-tint", "accent-wash", "card")
ACCENT_FAMILY = ("accent", "accent-deep", "accent-ink", "navy", "ink-strong", "ink-deep", "series-1", "series-2",
                 "series-3", "series-4", "series-5")
STAT_KINDS = {"measured": None, "delivered": None, "illustrative": "Illustrative", "target": "Target",
              "benchmark": "Benchmark"}
DASHES = ("dash", "sysDash", "sysDot", "lgDash", "dashDot")
HEADS = (None, "none", "end", "start", "both")
BAR_MAX_IN = 0.08            # a filled strip this thin and 6x as long is a bar
CHEVRON_DEPTH = (0.31, 0.35)  # point depth as a share of the step's height


def _name(name, what):
    if not isinstance(name, str) or not name.strip():
        raise GeometryError("%s name" % what, need="a semantic shape name", have=repr(name),
                            hint="every kit shape is named by its role, e.g. 'pillar.2.card'")
    return name


def _role_el(role, th):
    return th.spec(role)


_FILL_TAGS = {"noFill", "solidFill", "gradFill", "blipFill", "pattFill", "grpFill"}
_GEOM_TAGS = {"xfrm", "custGeom", "prstGeom"}


def _sppr(shape):
    el = getattr(shape, "_element", shape)
    sp = el.find(_P + "spPr")
    if sp is None:
        raise GeometryError("shape properties", need="p:spPr", have=etree.QName(el).localname)
    return sp


def _insert_after(sp, new, kinds):
    pos = 0
    for i, c in enumerate(sp):
        if etree.QName(c).localname in kinds:
            pos = i + 1
    sp.insert(pos, new)


def set_fill(shape, role, *, theme=None):
    """Solid fill in a role, or noFill when role is None. Replaces any fill already there."""
    th = theme_of(theme)
    sp = _sppr(shape)
    for c in [c for c in sp if etree.QName(c).localname in _FILL_TAGS]:
        sp.remove(c)
    if role is None:
        new = etree.Element(_A + "noFill")
    else:
        new = etree.Element(_A + "solidFill")
        new.append(_role_el(role, th))
    _insert_after(sp, new, _GEOM_TAGS)
    return shape


def set_line(shape, role, weight_pt: float | None = None, *, theme=None, dash=None, head=None, cap=None,
             join=None):
    """The shape's a:ln: a role colour at weight_pt, or noFill when role is None.

    head: None/'none', 'end' (tailEnd at the line's end point), 'start' (headEnd), 'both'."""
    th = theme_of(theme)
    sp = _sppr(shape)
    for c in sp.findall(_A + "ln"):
        sp.remove(c)
    ln = etree.Element(_A + "ln")
    if role is None:
        etree.SubElement(ln, _A + "noFill")
    else:
        if weight_pt is None or weight_pt <= 0:
            raise GeometryError("line weight", need="> 0pt", have=weight_pt, unit="pt")
        ln.set("w", str(int(round(weight_pt * EMU_PT))))
        if cap:
            ln.set("cap", cap)
        sf = etree.SubElement(ln, _A + "solidFill")
        sf.append(_role_el(role, th))
        if dash is not None:
            if dash not in DASHES:
                raise GeometryError("line dash", need=" or ".join(DASHES), have=dash)
            etree.SubElement(ln, _A + "prstDash", val=dash)
        if join == "round":
            etree.SubElement(ln, _A + "round")
        elif join == "miter":
            etree.SubElement(ln, _A + "miter", lim="800000")
        if head not in HEADS:
            raise GeometryError("arrow head", need="none, end, start or both", have=head)
        if head in ("start", "both"):
            etree.SubElement(ln, _A + "headEnd", type="triangle", w="med", len="med")
        if head in ("end", "both"):
            etree.SubElement(ln, _A + "tailEnd", type="triangle", w="med", len="med")
    _insert_after(sp, ln, _GEOM_TAGS | _FILL_TAGS)
    return shape


# ------------------------------------------------------------------ text

@dataclass(frozen=True)
class R:
    """One run: explicit size, role colour and face. Nothing is inherited."""
    text: str
    pt: float
    role: str = "ink"
    bold: bool = False
    italic: bool = False
    family: str = "Arial"


def check_pt(pt, what="run") -> float:
    pt = float(pt)
    if pt < FLOOR - 1e-9:
        raise BelowFloor(what, need=FLOOR, have=pt, hint="the floor is 8.0pt; make the box larger, never the type smaller")
    if abs(pt * 2 - round(pt * 2)) > 1e-6:
        raise GeometryError("%s size" % what, need="a half-point step", have=pt, unit="pt",
                            hint="the type ramp is on the half-point ladder")
    return pt


def _mparas(paras):
    out = []
    for runs, _align, sa in paras:
        out.append(measure.MPara(tuple(measure.MRun(r.text, r.pt, measure.face_for(r.family, r.bold, r.italic))
                                       for r in runs), space_after_pt=sa))
    return out


_ANCHOR = {"t": "t", "top": "t", "m": "ctr", "ctr": "ctr", "middle": "ctr", "b": "b", "bottom": "b"}
_ALIGN = {"l": "l", "left": "l", "c": "ctr", "ctr": "ctr", "center": "ctr", "r": "r", "right": "r"}


def write_text(shape, paras, *, what: str, measure_box, insets=(0.0, 0.0, 0.0, 0.0), anchor="t", theme=None):
    """Measure, then write paragraphs into a shape's own text body.

    paras: [([R, ...], align, space_after_pt), ...]. measure_box is the (w, h) the text actually gets
    (the preset's text rectangle, before insets); insets are (l, t, r, b) inches written to bodyPr.
    Raises BelowFloor or Overflows; never autofits, never shrinks."""
    th = theme_of(theme)
    for runs, _a, _s in paras:
        for r in runs:
            check_pt(r.pt, "%s run %r" % (what, r.text[:24]))
            th.spec(r.role)
    l, t, r_, b = insets
    measure.require_fit(what, _mparas(paras), measure_box, measure.Insets(l, t, r_, b))
    tf = shape.text_frame
    body = tf._txBody
    bp = body.find(_A + "bodyPr")
    for k, v in (("lIns", l), ("tIns", t), ("rIns", r_), ("bIns", b)):
        bp.set(k, str(int(round(v * EMU_PER_IN))))
    bp.set("anchor", _ANCHOR[anchor])
    bp.set("rtlCol", "0")
    ooxml.no_autofit(tf)
    for p in body.findall(_A + "p"):
        body.remove(p)
    for runs, align, sa in paras:
        p = etree.SubElement(body, _A + "p")
        ppr = etree.SubElement(p, _A + "pPr", algn=_ALIGN[align], marL="0", indent="0")
        etree.SubElement(etree.SubElement(ppr, _A + "lnSpc"), _A + "spcPct", val="100000")
        etree.SubElement(etree.SubElement(ppr, _A + "spcBef"), _A + "spcPts", val="0")
        etree.SubElement(etree.SubElement(ppr, _A + "spcAft"), _A + "spcPts", val=str(int(round(sa * 100))))
        etree.SubElement(ppr, _A + "buNone")
        for run in runs:
            re_ = etree.SubElement(p, _A + "r")
            rpr = etree.SubElement(re_, _A + "rPr", lang="en-US", sz=str(int(round(run.pt * 100))),
                                   b="1" if run.bold else "0", i="1" if run.italic else "0", dirty="0")
            sf = etree.SubElement(rpr, _A + "solidFill")
            sf.append(th.spec(run.role))
            etree.SubElement(rpr, _A + "latin", typeface=run.family)
            etree.SubElement(rpr, _A + "cs", typeface=run.family)
            etree.SubElement(re_, _A + "t").text = run.text
        last = runs[-1] if runs else None
        etree.SubElement(p, _A + "endParaRPr", lang="en-US",
                         sz=str(int(round((last.pt if last else FLOOR) * 100))), dirty="0")
    return shape


def textbox(slide, box: Box, paras, *, name: str, what: str | None = None, insets=(0.0, 0.0, 0.0, 0.0),
            anchor="t", theme=None):
    """A named text box holding measured paragraphs (see write_text). Returns the shape."""
    _name(name, "textbox")
    x, y, w, h = box.emu
    sh = slide.shapes.add_textbox(x, y, w, h)
    sh.name = name
    write_text(sh, paras, what=what or name, measure_box=(box.w, box.h), insets=insets, anchor=anchor, theme=theme)
    ooxml.finish(sh)
    return sh


# ------------------------------------------------------------------ shape creation

def _add(slide, prst, box: Box, name: str):
    from pptx.enum.shapes import MSO_SHAPE
    x, y, w, h = box.emu
    sh = slide.shapes.add_shape(getattr(MSO_SHAPE, prst), x, y, w, h)
    sh.name = name
    return sh


def _drop_text(sh):
    tx = sh._element.find(_P + "txBody")
    if tx is not None:
        sh._element.remove(tx)


def _adj(radius_in: float, box: Box) -> float:
    if radius_in < 0:
        raise GeometryError("corner radius", need=">= 0in", have=radius_in, unit="in")
    return min(0.5, radius_in / min(box.w, box.h))


def _bar_check(box: Box, fill, name: str, what: str):
    """An accent-coloured strip on its own is the left/top accent bar: banned unless it encodes state."""
    if fill not in ACCENT_FAMILY or name.startswith("state."):
        return
    thin, long_ = min(box.w, box.h), max(box.w, box.h)
    if thin <= BAR_MAX_IN and long_ >= 6 * thin:
        raise GeometryError("%s %s" % (what, name), need="not an accent bar", have="%.3f x %.3f in %s strip"
                            % (box.w, box.h, fill),
                            hint="a coloured edge bar is allowed only where it encodes a state; name it state.<what>")


def _shape(slide, prst, box, *, fill, line, weight_pt, name, theme, keep_text=False):
    th = theme_of(theme)
    sh = _add(slide, prst, box, name)
    set_fill(sh, fill, theme=th)
    set_line(sh, line, weight_pt, theme=th)
    if not keep_text:
        _drop_text(sh)
    ooxml.finish(sh)
    return sh


def rect(slide, box: Box, *, fill=None, line=None, weight_pt=None, radius_in=None, name: str, theme=None):
    """A square-cornered rectangle. A radius here raises: use card() for a rounded box."""
    _name(name, "rect")
    if radius_in is not None:
        raise GeometryError("rect %s radius" % name, need="no radius on the rect preset", have=radius_in, unit="in",
                            hint="a radius would silently do nothing on a rect; use card(radius_in=...)")
    _bar_check(box, fill, name, "rect")
    if line is not None and weight_pt is None:
        weight_pt = canvas_for(slide).hairline_pt
    return _shape(slide, "RECTANGLE", box, fill=fill, line=line, weight_pt=weight_pt, name=name, theme=theme)


def card(slide, box: Box, *, fill="card", line="hairline", radius_in=None, name: str, theme=None):
    """A card: a flat fill, a hairline or rule-strong border, a physical corner radius, no shadow.

    radius_in None takes the canvas radius; 0 draws a square card. The radius is converted to the
    preset's normalised adjustment (adj = min(0.5, r / min(w, h))). An outline-only card on white
    (fill paper) uses rule-strong, never the decorative hairline (DECISIONS: hairline scoping)."""
    _name(name, "card")
    if fill not in CARD_FILLS:
        raise ThemeInvariant("card %s fill" % name, need=" / ".join(CARD_FILLS), have=fill)
    if line not in CARD_LINES:
        raise ThemeInvariant("card %s line" % name, need="hairline / rule-strong / None", have=line)
    if fill == "paper" and line == "hairline":
        raise ThemeInvariant("card %s" % name, need="rule-strong on an outline-only card", have="hairline on paper",
                             hint="hairline (1.84:1) is exempt only on filled or spaced cards; use line='rule-strong' "
                                  "or fill='card'")
    cv = canvas_for(slide)
    r = cv.radius_in if radius_in is None else float(radius_in)
    th = theme_of(theme)
    if r == 0:
        sh = _shape(slide, "RECTANGLE", box, fill=fill, line=line, weight_pt=cv.hairline_pt, name=name, theme=th)
        return sh
    sh = _add(slide, "ROUNDED_RECTANGLE", box, name)
    sh.adjustments[0] = _adj(r, box)
    set_fill(sh, fill, theme=th)
    set_line(sh, line, cv.hairline_pt, theme=th)
    _drop_text(sh)
    ooxml.finish(sh)
    return sh


def _label_paras(text, pt, role, bold=True, align="l"):
    return [([R(text, pt, role, bold=bold)], align, 0.0)]


def tab(slide, box: Box, label: str, *, fill="ink-strong", pt=None, radius_in=None, align="l", name: str, theme=None):
    """A header tab: top corners rounded (round2SameRect), the label inside in the fill's text role.
    Sits on top of a card body; the body is drawn separately by the caller."""
    _name(name, "tab")
    if fill not in ON_FILL:
        raise ThemeInvariant("tab %s fill" % name, need=" / ".join(ON_FILL), have=fill)
    th = theme_of(theme)
    cv = canvas_for(slide)
    pt = cv.ramp["label"] if pt is None else pt
    r = cv.radius_in if radius_in is None else float(radius_in)
    sh = _add(slide, "ROUND_2_SAME_RECTANGLE", box, name)
    sh.adjustments[0] = _adj(r, box)
    sh.adjustments[1] = 0.0
    set_fill(sh, fill, theme=th)
    set_line(sh, None, theme=th)
    ins = 0.10 * cv.k
    write_text(sh, _label_paras(label, pt, ON_FILL[fill], True, align), what="tab %s" % name,
               measure_box=(box.w, box.h), insets=(ins, 0.02, ins, 0.02), anchor="m", theme=th)
    ooxml.finish(sh)
    return sh


def pill(slide, box: Box, text: str, *, fill="card", line=None, role=None, pt=None, name: str, theme=None):
    """A tag: a fully rounded box around a short label. For tags only, never a state badge on every tile."""
    _name(name, "pill")
    if fill not in ON_FILL:
        raise ThemeInvariant("pill %s fill" % name, need=" / ".join(ON_FILL), have=fill)
    th = theme_of(theme)
    cv = canvas_for(slide)
    pt = cv.ramp["small"] if pt is None else pt
    sh = _add(slide, "ROUNDED_RECTANGLE", box, name)
    sh.adjustments[0] = 0.5
    set_fill(sh, fill, theme=th)
    set_line(sh, line, cv.hairline_pt, theme=th)
    side = min(box.w, box.h) / 2.0 * (1 - math.sqrt(0.5))   # the preset's text rectangle is inset by this
    ins = 0.04 * cv.k
    write_text(sh, _label_paras(text, pt, role or ON_FILL[fill], False, "c"), what="pill %s" % name,
               measure_box=(box.w - 2 * side, box.h), insets=(ins, 0.0, ins, 0.0), anchor="m", theme=th)
    ooxml.finish(sh)
    return sh


def step_header(slide, box: Box, labels, *, fill="ink-strong", active=None, depth=0.33, gap_in=0.04, pt=None,
                name: str, theme=None):
    """A process header: a homePlate then chevrons, nested, the point depth 31-35% of the height.

    active (0-based index) marks the current step in the accent fill: a state, not decoration.
    Returns the group named `name`; steps are name.1, name.2, ..."""
    from .geom import identity_group
    _name(name, "step_header")
    labels = list(labels)
    if not labels:
        raise GeometryError("step_header %s" % name, need=">= 1 step", have=0)
    if not (CHEVRON_DEPTH[0] - 1e-9 <= depth <= CHEVRON_DEPTH[1] + 1e-9):
        raise GeometryError("step_header %s point depth" % name, need="%.2f..%.2f of the height" % CHEVRON_DEPTH,
                            have=depth)
    if fill not in ON_FILL:
        raise ThemeInvariant("step_header %s fill" % name, need=" / ".join(ON_FILL), have=fill)
    if active is not None and not (0 <= active < len(labels)):
        raise GeometryError("step_header %s active" % name, need="0..%d" % (len(labels) - 1), have=active)
    th = theme_of(theme)
    cv = canvas_for(slide)
    pt = cv.ramp["label"] if pt is None else pt
    n = len(labels)
    d = depth * box.h
    sw = (box.w + (n - 1) * (d - gap_in)) / n
    if sw <= 2 * d + 0.1:
        raise GeometryError("step_header %s" % name, need="steps wider than their two points", have="%.2fin" % sw,
                            hint="fewer steps or a wider box")
    shapes = []
    for i, text in enumerate(labels):
        f = "accent" if active == i else fill
        b = Box(box.x + i * (sw - d + gap_in), box.y, sw, box.h)
        prst = "PENTAGON" if i == 0 else "CHEVRON"
        sh = _add(slide, prst, b, "%s.%d" % (name, i + 1))
        sh.adjustments[0] = d / min(b.w, b.h)
        set_fill(sh, f, theme=th)
        set_line(sh, None, theme=th)
        left = 0.0 if i == 0 else d
        ins = 0.06 * cv.k
        write_text(sh, _label_paras(text, pt, ON_FILL[f], True, "c"), what="step %d of %s" % (i + 1, name),
                   measure_box=(b.w - left - d, b.h), insets=(ins, 0.0, ins, 0.0), anchor="m", theme=th)
        ooxml.finish(sh)
        shapes.append(sh)
    g = identity_group(slide, shapes, name)
    ooxml.finish(g)
    return g


def disc(slide, box: Box, n, *, fill="accent", pt=None, name: str, theme=None):
    """A numbered disc: a circle (box must be square) with its number centred in the fill's text role."""
    _name(name, "disc")
    if abs(box.w - box.h) > 0.005:
        raise GeometryError("disc %s" % name, need="a square box", have="%.3f x %.3f in" % (box.w, box.h))
    if fill not in ON_FILL:
        raise ThemeInvariant("disc %s fill" % name, need=" / ".join(ON_FILL), have=fill)
    th = theme_of(theme)
    if pt is None:
        pt = math.floor(box.h * 72 * 0.42 * 2) / 2.0
    sh = _add(slide, "OVAL", box, name)
    set_fill(sh, fill, theme=th)
    set_line(sh, None, theme=th)
    inner = box.w * math.sqrt(0.5)                 # the ellipse preset's text rectangle
    write_text(sh, _label_paras(str(n), pt, ON_FILL[fill], True, "c"), what="disc %s" % name,
               measure_box=(inner, inner), anchor="m", theme=th)
    ooxml.finish(sh)
    return sh


def person(slide, box: Box, *, role="ink-muted", name: str, theme=None):
    """A person mark: an ellipse head over flowChartDelay shoulders (the D turned dome up). A group
    named `name` with name.head and name.body."""
    from .geom import identity_group
    _name(name, "person")
    th = theme_of(theme)
    d = min(box.w * 0.5, box.h * 0.42)
    gap = box.h * 0.05
    head = Box(box.cx - d / 2, box.y, d, d)
    bw = min(box.w, d * 1.9)
    bh = box.h - d - gap
    if bh <= 0.02:
        raise GeometryError("person %s" % name, need="a taller box", have="%.3fin" % box.h)
    h = _shape(slide, "OVAL", head, fill=role, line=None, weight_pt=None, name="%s.head" % name, theme=th)
    # the unrotated frame is (bh x bw) around the same centre; rot 270 turns the round side up
    cx, cy = box.cx, box.y + d + gap + bh / 2
    frame = Box(cx - bh / 2, cy - bw / 2, bh, bw)
    b = _add(slide, "FLOWCHART_DELAY", frame, "%s.body" % name)
    b.rotation = 270.0
    set_fill(b, role, theme=th)
    set_line(b, None, theme=th)
    _drop_text(b)
    ooxml.finish(b)
    g = identity_group(slide, [h, b], name)
    ooxml.finish(g)
    return g


def _connector(slide, p1, p2, name):
    from pptx.enum.shapes import MSO_CONNECTOR
    (x1, y1), (x2, y2) = p1, p2
    if abs(x1 - x2) < 1e-6 and abs(y1 - y2) < 1e-6:
        raise GeometryError("connector %s" % name, need="two distinct points", have=(p1, p2))
    e = lambda v: int(round(v * EMU_PER_IN))  # noqa: E731
    cx = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, e(x1), e(y1), e(x2), e(y2))
    cx.name = name
    return cx


def hairline(slide, p1, p2, *, role="hairline", weight_pt=None, name: str, theme=None):
    """A divider from p1 to p2 (inches), horizontal or vertical, no heads."""
    _name(name, "hairline")
    (x1, y1), (x2, y2) = p1, p2
    if abs(x1 - x2) > 1e-6 and abs(y1 - y2) > 1e-6:
        raise GeometryError("hairline %s" % name, need="horizontal or vertical", have=(p1, p2))
    th = theme_of(theme)
    w = canvas_for(slide).hairline_pt if weight_pt is None else weight_pt
    cx = _connector(slide, p1, p2, name)
    set_line(cx, role, w, theme=th)
    ooxml.finish(cx)
    return cx


def connect(slide, p1, p2, *, head="end", dash=None, role="ink-muted", weight_pt=0.75, name: str, theme=None):
    """A straight connector from p1 to p2 (inches), a triangle head at the end by default.

    Unglued on purpose (no stCxn/endCxn): LibreOffice re-routes glued connectors on import. Endpoints
    must sit on the boxes they join; gate P06 measures both."""
    _name(name, "connect")
    th = theme_of(theme)
    cx = _connector(slide, p1, p2, name)
    set_line(cx, role, weight_pt, theme=th, dash=dash, head=head)
    ooxml.finish(cx)
    return cx


def elbow(slide, points, *, head="end", dash=None, role="ink-muted", weight_pt=0.75, name: str, theme=None):
    """An orthogonal polyline through points (inches) as one open custGeom path, head at the last point.

    Every segment is horizontal or vertical. One shape, so its two ends are the only free ends."""
    _name(name, "elbow")
    pts = [(float(x), float(y)) for x, y in points]
    if len(pts) < 2:
        raise GeometryError("elbow %s" % name, need=">= 2 points", have=len(pts))
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        if abs(ax - bx) > 1e-6 and abs(ay - by) > 1e-6:
            raise GeometryError("elbow %s segment" % name, need="horizontal or vertical", have=((ax, ay), (bx, by)),
                                hint="use connect() for a diagonal")
        if abs(ax - bx) < 1e-6 and abs(ay - by) < 1e-6:
            raise GeometryError("elbow %s segment" % name, need="non-zero length", have=(ax, ay))
    th = theme_of(theme)
    e = lambda v: int(round(v * EMU_PER_IN))  # noqa: E731
    x0, y0 = min(p[0] for p in pts), min(p[1] for p in pts)
    w = max(1, e(max(p[0] for p in pts)) - e(x0))
    h = max(1, e(max(p[1] for p in pts)) - e(y0))
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, e(x0), e(y0), w, h)
    sh.name = name
    sp = _sppr(sh)
    g = etree.Element(_A + "custGeom")
    for t in ("avLst", "gdLst", "ahLst", "cxnLst"):
        etree.SubElement(g, _A + t)
    etree.SubElement(g, _A + "rect", l="l", t="t", r="r", b="b")
    path = etree.SubElement(etree.SubElement(g, _A + "pathLst"), _A + "path", w=str(w), h=str(h), fill="none")
    for i, (px, py) in enumerate(pts):
        op = etree.SubElement(path, _A + ("moveTo" if i == 0 else "lnTo"))
        etree.SubElement(op, _A + "pt", x=str(e(px) - e(x0)), y=str(e(py) - e(y0)))
    sp.replace(sp.find(_A + "prstGeom"), g)
    set_fill(sh, None, theme=th)
    set_line(sh, role, weight_pt, theme=th, dash=dash, head=head, join="miter")
    _drop_text(sh)
    ooxml.finish(sh)
    return sh


def caps_label(slide, box: Box, text: str, *, role="ink-muted", pt=None, align="l", name: str, theme=None):
    """An upper-case label in Arial Bold (never a mono face). The text is upper-cased in the file, so
    what is measured and what the gates read is what is drawn."""
    _name(name, "caps_label")
    pt = canvas_for(slide).ramp["small"] if pt is None else pt
    return textbox(slide, box, _label_paras(text.upper(), pt, role, True, align), name=name,
                   what="caps label %s" % name, theme=theme)


def stat(slide, box: Box, value: str, label: str, *, kind: str, role="accent-ink", pt=None, label_pt=None,
         numerals=False, name: str, theme=None):
    """A stat: the numeral, a hairline, then the label under it (the hairline sits above the label, a data
    sheet reading, never a coloured left border). kind is required: measured, delivered, illustrative,
    target or benchmark; the last three carry a basis chip so a planning figure never reads as delivered.

    Returns a group named `name` (name.value, name.rule, name.label, name.basis); the group's alt text
    records the kind for gate P23."""
    from .geom import identity_group
    _name(name, "stat")
    if kind not in STAT_KINDS:
        raise GeometryError("stat %s kind" % name, need=" / ".join(STAT_KINDS), have=kind,
                            hint="every number states what it is; separate delivered from targeted")
    th = theme_of(theme)
    cv = canvas_for(slide)
    pt = cv.ramp["numeral"] if pt is None else pt
    label_pt = cv.ramp["label"] if label_pt is None else label_pt
    if pt < cv.ramp["numeral_min"]:
        raise GeometryError("stat %s numeral" % name, need=cv.ramp["numeral_min"], have=pt, unit="pt",
                            hint="a numeral below the ramp's numeral minimum reads as body copy")
    family = "Arial"
    if numerals:
        nf = th.fonts.get("numerals") or {}
        if not nf:
            raise ThemeInvariant("stat %s numerals" % name, need="a numerals face in the theme", have="none")
        family = "%s %s" % (nf.get("face", "Montserrat"), nf.get("weight", "SemiBold"))
    numeral_bold = not numerals
    vh = measure.line_in(check_pt(pt, "stat numeral"), measure.face_for(family, numeral_bold)) * 1.02
    y = box.y
    vb = Box(box.x, y, box.w, vh)
    shapes = [textbox(slide, vb, [([R(value, pt, role, bold=numeral_bold, family=family)], "l", 0.0)],
                      name="%s.value" % name, what="stat %s value" % name, theme=th)]
    y += vh + 0.05 * cv.k
    shapes.append(hairline(slide, (box.x, y), (box.r, y), name="%s.rule" % name, theme=th))
    y += 0.06 * cv.k
    lparas = [([R(label, label_pt, "ink-muted")], "l", 0.0)]
    lh = measure.need_height(_mparas(lparas), box.w)
    chip = STAT_KINDS[kind]
    ch = 0.0
    if chip:
        cpt = cv.ramp["small"]
        ch = measure.line_in(cpt, measure.face_for("Arial")) + 0.08
    need = (y - box.y) + lh + ((0.06 * cv.k + ch) if chip else 0.0)
    if need > box.h + 1e-6:
        from .errors import Overflows
        raise Overflows("stat %s" % name, need=round(need, 3), have=round(box.h, 3),
                        hint="give the stat more height or a shorter label")
    shapes.append(textbox(slide, Box(box.x, y, box.w, lh), lparas, name="%s.label" % name,
                          what="stat %s label" % name, theme=th))
    y += lh + 0.06 * cv.k
    if chip:
        cw = measure.width_in(chip, cpt, measure.face_for("Arial")) * measure.SLACK + 0.24
        shapes.append(pill(slide, Box(box.x, y, min(cw, box.w), ch), chip, fill="card", line="hairline",
                           role="ink-muted", pt=cpt, name="%s.basis" % name, theme=th))
    g = identity_group(slide, shapes, name)
    g._element.find(".//" + _P + "cNvPr").set("descr", "stat kind %s" % kind)
    ooxml.finish(g)
    return g


def quote(slide, box: Box, text: str, attribution: str, *, fill="card", bar_role="accent", pt=None, name: str,
          theme=None):
    """A quotation: a tinted panel, a left bar named state.quote (the one left bar the house rules allow,
    because it says these are somebody's own words), the passage in italic, the attribution under it.
    Straight quotation marks: smart quotes are a banned glyph. Returns the group named `name`."""
    from .geom import identity_group
    _name(name, "quote")
    th = theme_of(theme)
    cv = canvas_for(slide)
    pt = cv.ramp["body"] if pt is None else pt
    body = text.strip().strip('"' + chr(0x201C) + chr(0x201D))     # curly marks are a banned glyph
    bar_w = 0.05 * cv.k
    pad = 0.14 * cv.k
    tx = box.x + bar_w + pad
    tw = box.r - pad - tx
    qp = [([R('"%s"' % body, pt, "ink", italic=True)], "l", 0.0)]
    ap = [([R(attribution, cv.ramp["label"], "ink-muted", bold=True)], "l", 0.0)]
    qh = measure.need_height(_mparas(qp), tw)
    ah = measure.need_height(_mparas(ap), tw)
    gap = 0.08 * cv.k
    need = 2 * pad + qh + gap + ah
    if need > box.h + 1e-6:
        from .errors import Overflows
        raise Overflows("quote %s" % name, need=round(need, 3), have=round(box.h, 3),
                        hint="cut the passage or give the quote more height")
    panel = _shape(slide, "RECTANGLE", box, fill=fill, line=None, weight_pt=None, name="%s.panel" % name, theme=th)
    bar = _shape(slide, "RECTANGLE", Box(box.x, box.y, bar_w, box.h), fill=bar_role, line=None, weight_pt=None,
                 name="state.quote", theme=th)
    q = textbox(slide, Box(tx, box.y + pad, tw, qh), qp, name="%s.text" % name, theme=th)
    a = textbox(slide, Box(tx, box.y + pad + qh + gap, tw, ah), ap, name="%s.by" % name, theme=th)
    g = identity_group(slide, [panel, bar, q, a], name)
    ooxml.finish(g)
    return g


def zone(slide, box: Box, *, fill="accent-tint", label=None, radius_in=None, name: str, theme=None):
    """A grouping container in a brand tint, no border. An optional caps label sits inside its top-left
    corner as name.label (a sibling shape). Returns the zone shape."""
    _name(name, "zone")
    if fill not in ZONE_FILLS:
        raise ThemeInvariant("zone %s fill" % name, need=" / ".join(ZONE_FILLS), have=fill)
    th = theme_of(theme)
    cv = canvas_for(slide)
    r = cv.radius_in if radius_in is None else float(radius_in)
    if r == 0:
        z = _shape(slide, "RECTANGLE", box, fill=fill, line=None, weight_pt=None, name=name, theme=th)
    else:
        z = _add(slide, "ROUNDED_RECTANGLE", box, name)
        z.adjustments[0] = _adj(r, box)
        set_fill(z, fill, theme=th)
        set_line(z, None, theme=th)
        _drop_text(z)
        ooxml.finish(z)
    if label:
        ins = 0.12 * cv.k
        lpt = cv.ramp["small"]
        lh = measure.line_in(lpt, measure.face_for("Arial", True)) * 1.05
        caps_label(slide, Box(box.x + ins, box.y + ins * 0.75, box.w - 2 * ins, lh), label, role="ink",
                   pt=lpt, name="%s.label" % name, theme=th)
    return z


__all__ = ["use", "bind", "theme_of", "canvas_for", "set_fill", "set_line", "R", "check_pt", "write_text", "textbox",
           "rect", "card", "tab", "pill", "step_header", "disc", "person", "hairline", "stat", "quote", "caps_label",
           "connect", "elbow", "zone", "ON_FILL", "STAT_KINDS", "CHEVRON_DEPTH"]
