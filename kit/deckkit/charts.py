"""deckkit.charts: native charts under the house rules (ruling 22; library/design/final-review/charts-spec.md).

The data marks are a native python-pptx chart, so a deck opened in PowerPoint carries Edit Data and a theme swap
re-skins the chart with the deck (every colour is a schemeClr from Theme.spec_xml). Everything the gates must see is a
kit shape drawn on exact data coordinates: category names, value labels, end labels, the basis label and every
annotation. The plot area is pinned with c:manualLayout (inner, edge mode) and the value axis is fixed, so
Plot.val / Plot.cat / Plot.xy turn a data value into slide inches.

House styling on every chart (_space and the per-type writers): flat solid fills in theme roles, no 3D, no gradient,
no shadow, no c:style, roundedCorners 0, no chart title (the slide title carries the claim), no legend (direct
labels), tick text 10pt ink-muted, gridlines hairline-soft 0.75pt solid or none, tick marks none, varyColors 0,
fixed axis ids. Exactly one subject per chart in `accent`; the rest is navy (`series-1`), grey (`rule-strong`) or
grey context (`hairline`). A negative waterfall step is `ink-muted`, never accent: on the Sigmoid theme the accent
is the RAG red's hex, so a red loss would read as a status. Status colours (the RAG identities) never ride a chart.

Every chart states its kind (prims.STAT_KINDS). A planning kind (illustrative, target, benchmark) draws one basis
label per slide, text exactly "Illustrative figures" (or Target, Benchmark), unless the slide already carries it.
The frame's alt text ends "(chart kind <kind>)", which gate P27 reads. records(prs) returns every chart's data and
label texts for manifest["charts"]; P27 fails a chart whose data or labels changed after the build.

    plot = charts.bar(s, box, ["Collect", "Rewrite", "Review", "Send"], [1, 2, 1, 1], subject="Rewrite",
                      fmt="{:g} days", kind="illustrative", name="days")
    charts.annotate(plot, "Rewrite", "Six rewrites, two days", kind="callout")
    package.save(prs, out, ..., manifest={"numbers": numbers, "charts": charts.records(prs)})

A label that does not fit raises Overflows with what it needs. Type never shrinks below its role and category names
never rotate.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Callable

from lxml import etree

from . import measure, ooxml, prims
from . import text as txt
from .canvas import Box
from .errors import DeckkitError, GeometryError, Overflows
from .read.colour import contrast, hex2rgb, s2l
from .read.ns import NS
from .text import Para, Run

C_NS, A_NS, R_NS, P_NS = NS["c"], NS["a"], NS["r"], NS["p"]
_C, _A, _R, _P = ("{%s}" % C_NS), ("{%s}" % A_NS), ("{%s}" % R_NS), ("{%s}" % P_NS)
CHART_URI = C_NS
NSDECL = 'xmlns:c="%s" xmlns:a="%s" xmlns:r="%s"' % (C_NS, A_NS, R_NS)


class ChartError(DeckkitError):
    """A chart the house rules refuse: two subjects, too many series, a negative bar, a status colour."""


KINDS = tuple(prims.STAT_KINDS)
BASIS = {k: v for k in KINDS for v in [(prims.basis_label(k) if hasattr(prims, "basis_label")
                                         else {"illustrative": "Illustrative figures", "target": "Target figures",
                                               "benchmark": "Benchmark figures"}.get(k))] if v}
KIND_RE = re.compile(r"\(chart kind ([a-z]+)\)\s*$")

# chart roles: a job, never a hex
SUBJECT = "accent"                       # the one mark the title is about
OTHERS = ("series-1", "rule-strong", "series-2")   # navy, then grey, then the deck blue, for the other series
CONTEXT = "hairline"                     # every other bar when one is the subject
NEGATIVE = "ink-muted"                   # a negative waterfall step
WASH = "accent-wash"                     # an area under its line, a tolerance band
GRID = "hairline-soft"
AXIS = "hairline"
CATEGORICAL_MAX = 3

TICK_PT = 10.0           # native tick numbers and category names under a plot
CAT_PT = 11.0            # bar-row category names
LABEL_PT = 11.0          # value labels
SUBJECT_PT = 12.0        # the subject's value label, bold
NOTE_PT = 11.0           # annotation callouts, bold
BASIS_PT = 9.0
LINE_PT = 2.25
GRID_PT = 0.75
MARKER = 7
DOT_IN = 0.14            # an annotation dot
PAD = 0.06               # kit text stays this far inside the chart frame
BAR_MAX_IN = 0.55        # thicker bars read as blocks: the gap widens instead
GAP_MIN, GAP_MAX = 60, 500
TRACK_IN = 0.16          # bullet and progress bars: thicker than the 0.10in accent-strip line
AX_CAT, AX_VAL, AX_X, AX_Y = 50010, 50020, 50030, 50040
MAX_CATEGORIES = 16
CVD_MIN = 8.0            # OKLab x100, adjacent chart-order roles under every Machado simulation
PAPER_MIN = 15.0         # OKLab x100, a chart-order role against paper


# ------------------------------------------------------------------ small helpers

def _th(theme):
    return prims.theme_of(theme)


def _named(name: str, what: str):
    if not name or not str(name).strip() or any(c.isspace() for c in str(name)):
        raise GeometryError("chart %s" % what, need="a role name without spaces", have=repr(name),
                            hint="every kit shape is named; labels are named <name>.cat.<i>, <name>.value.<i>")


def _kind(kind: str, name: str):
    if kind not in KINDS:
        raise GeometryError("chart %s kind" % name, need=" / ".join(KINDS), have=kind,
                            hint="every number states what it is; separate delivered from targeted")


def _face(th, bold=False):
    return measure.face_for(th.fonts.get("minor") or "Arial", bold)


def _tw(text: str, pt: float, th, bold=False) -> float:
    """Measured width with the kit's PowerPoint slack."""
    return measure.width_in(text, pt, _face(th, bold)) * measure.SLACK


def _lh(pt: float, th) -> float:
    return measure.line_in(pt, _face(th))


def _fmt(fmt, v) -> str:
    return fmt(v) if callable(fmt) else str(fmt).format(v)


def _num(v) -> str:
    return ("%.10g" % float(v)).replace("e+", "E").replace("e-", "E-")


def _esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def nice_ceiling(v: float, ticks: int = 4, headroom: float = 0.0) -> tuple[float, float]:
    """(axis max, major unit): the smallest top of the form k x step (k = ticks - 1 to ticks + 1, step 1, 2, 2.5, 4 or
    5 x 10^n) at or above v x (1 + headroom). The requested tick count wins a tie."""
    need = v * (1.0 + headroom)
    if need <= 0:
        return 1.0, 1.0 / max(1, ticks)
    best = None
    for k in (ticks, ticks - 1, ticks + 1):
        if k < 2:
            continue
        mag = 10 ** math.floor(math.log10(need / k))
        for m in (1, 2, 2.5, 4, 5, 10):
            step = m * mag
            if step * k >= need - 1e-9:
                cand = (round(step * k, 9), k != ticks, step * k, step)
                if best is None or cand < best:
                    best = cand
                break
    return best[2], best[3]


def _para(text, role, pt, bold=False, align="left"):
    return [Para((Run(text, role, bold=bold, size=pt),), align=align)]


def _text(slide, box: Box, text, *, role="ink", pt=LABEL_PT, bold=False, align="left", anchor="middle", name, th,
          background="paper"):
    return txt.textbox(slide, box, _para(text, role, pt, bold, align), name, th, anchor=anchor, background=background)


def _need_h(text, width, pt, th, bold=False) -> float:
    return txt.need_height(_para(text, "ink", pt, bold), width, th)


def _oklab(h):
    r, g, b = (s2l(c) for c in hex2rgb(h))
    l_ = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m_ = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s_ = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = (max(x, 0.0) ** (1 / 3) for x in (l_, m_, s_))
    return (0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
            1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
            0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_)


def _dok(a, b) -> float:
    return 100 * math.dist(_oklab(a), _oklab(b))


def check_theme(theme=None, roles=(SUBJECT,) + OTHERS) -> list[str]:
    """Why the theme cannot carry a chart in `roles` (the chart order): adjacent roles must clear CVD_MIN (OKLab x100)
    in normal vision and under the three Machado simulations, and each must clear PAPER_MIN against paper. Empty
    when it can. RAG identity colours are refused as chart roles whatever the distances."""
    from .theme import MACHADO, _simulate
    th = _th(theme)
    out = []
    hexes = [(r, th.hex(r)) for r in roles]
    for r, h in hexes:
        d = _dok(h, th.hex("paper"))
        if d < PAPER_MIN:
            out.append("%s %s is %.1f from paper (min %.0f)" % (r, h, d, PAPER_MIN))
    for (ra, a), (rb, b) in zip(hexes, hexes[1:]):
        for kind in ("normal",) + tuple(MACHADO):
            sa, sb = (a, b) if kind == "normal" else (_simulate(a, kind), _simulate(b, kind))
            d = _dok(sa, sb)
            if d < CVD_MIN:
                out.append("%s %s and %s %s are %.1f apart under %s (min %.0f)" % (ra, a, rb, b, d, kind, CVD_MIN))
    return out


def _theme_ok(th, roles):
    bad = check_theme(th, roles)
    if bad:
        raise ChartError("theme %s chart colours" % th.name, need="separable chart roles", have="; ".join(bad[:3]),
                         hint="the series slots cannot carry %d series on this theme; plot fewer series or give the "
                              "theme separable accent2 and accent3" % len(roles))


# ------------------------------------------------------------------ chart XML

def _solid(th, role) -> str:
    return "<a:solidFill>%s</a:solidFill>" % th.spec_xml(role)


def _ln(th, role=None, pt=None, *, dash=None, round_=False) -> str:
    if role is None:
        return "<a:ln><a:noFill/></a:ln>"
    w = ' w="%d"' % round(pt * 12700) if pt else ""
    cap = ' cap="rnd"' if round_ else ""
    return "<a:ln%s%s>%s%s%s</a:ln>" % (w, cap, _solid(th, role), '<a:prstDash val="%s"/>' % dash if dash else "",
                                       "<a:round/>" if round_ else "")


def _sppr(th, fill=None, line=None, line_pt=None, **kw) -> str:
    return "<c:spPr>%s%s</c:spPr>" % (_solid(th, fill) if fill else "<a:noFill/>", _ln(th, line, line_pt, **kw))


def _txpr(th, pt=TICK_PT, role="ink-muted", bold=False) -> str:
    return ('<c:txPr><a:bodyPr rot="0" vert="horz"/><a:lstStyle/><a:p><a:pPr><a:defRPr sz="%d" b="%d">%s'
            '<a:latin typeface="+mn-lt"/></a:defRPr></a:pPr><a:endParaRPr lang="en-US"/></a:p></c:txPr>'
            % (round(pt * 100), 1 if bold else 0, _solid(th, role)))


def _cat_ax(th, ax, cross, pos, *, reverse=False, line=True) -> str:
    return ('<c:catAx><c:axId val="%d"/><c:scaling><c:orientation val="%s"/></c:scaling><c:delete val="0"/>'
            '<c:axPos val="%s"/><c:numFmt formatCode="General" sourceLinked="1"/><c:majorTickMark val="none"/>'
            '<c:minorTickMark val="none"/><c:tickLblPos val="none"/>%s%s<c:crossAx val="%d"/>'
            '<c:crosses val="autoZero"/><c:auto val="1"/><c:lblAlgn val="ctr"/><c:lblOffset val="100"/>'
            '<c:noMultiLvlLbl val="1"/></c:catAx>'
            % (ax, "maxMin" if reverse else "minMax", pos, _sppr(th, None, AXIS if line else None, GRID_PT),
               _txpr(th), cross))


def _val_ax(th, ax, cross, pos, vmin, vmax, *, delete, grid=False, fmt="#,##0", unit=None, between=True,
            line=None) -> str:
    s = ('<c:valAx><c:axId val="%d"/><c:scaling><c:orientation val="minMax"/><c:max val="%s"/><c:min val="%s"/>'
         '</c:scaling><c:delete val="%d"/><c:axPos val="%s"/>' % (ax, _num(vmax), _num(vmin), 1 if delete else 0, pos))
    if grid:
        s += "<c:majorGridlines>%s</c:majorGridlines>" % _sppr(th, None, GRID, GRID_PT)
    s += ('<c:numFmt formatCode="%s" sourceLinked="0"/><c:majorTickMark val="none"/><c:minorTickMark val="none"/>'
          '<c:tickLblPos val="%s"/>%s%s<c:crossAx val="%d"/><c:crosses val="autoZero"/><c:crossBetween val="%s"/>'
          % (_esc(fmt), "none" if delete else "nextTo", _sppr(th, None, line, GRID_PT if line else None), _txpr(th),
             cross, "between" if between else "midCat"))
    if unit:
        s += '<c:majorUnit val="%s"/>' % _num(unit)
    return s + "</c:valAx>"


def _harvest(cs) -> list[dict]:
    """The series references python-pptx wrote (name, categories, values with their caches and sheet ranges)."""
    out = []
    for ser in cs.iter(_C + "ser"):
        d = {}
        for tag in ("tx", "cat", "val", "xVal", "yVal", "bubbleSize"):
            e = ser.find(_C + tag)
            d[tag] = etree.tostring(e, encoding="unicode") if e is not None else ""
        out.append(d)
    return out


def _dpts(th, roles, default, *, outline=None, bubble=False) -> str:
    out = []
    for i, r in enumerate(roles or ()):
        if r == default:
            continue
        out.append('<c:dPt><c:idx val="%d"/><c:invertIfNegative val="0"/><c:bubble3D val="0"/>%s</c:dPt>'
                   % (i, _sppr(th, r, outline, 1.5 if outline else None)))
    return "".join(out)


def _bar_ser(th, idx, refs, role, points=None, *, outline=None) -> str:
    return ('<c:ser><c:idx val="%d"/><c:order val="%d"/>%s%s<c:invertIfNegative val="0"/>%s%s%s</c:ser>'
            % (idx, idx, refs["tx"], _sppr(th, role, outline, 1.5 if outline else None),
               _dpts(th, points, role, outline=outline), refs["cat"], refs["val"]))


def _marker(th, role, size=MARKER) -> str:
    if role is None:
        return '<c:marker><c:symbol val="none"/></c:marker>'
    return ('<c:marker><c:symbol val="circle"/><c:size val="%d"/>%s</c:marker>'
            % (size, _sppr(th, role, role, 0.75)))


def _space(cs, th, plot_xml: str, frac):
    """Rebuild the chartSpace in schema order around plot_xml (chart groups then axes), keeping the workbook link."""
    ext = cs.find(_C + "externalData")
    rid = ext.get(_R + "id") if ext is not None else None
    if not rid:
        raise ChartError("chart part", need="an embedded workbook", have="no externalData")
    x, y, w, h = frac
    xml = ('<c:chartSpace %s><c:date1904 val="0"/><c:roundedCorners val="0"/><c:chart><c:autoTitleDeleted val="1"/>'
           '<c:plotArea><c:layout><c:manualLayout><c:layoutTarget val="inner"/><c:xMode val="edge"/>'
           '<c:yMode val="edge"/><c:x val="%.5f"/><c:y val="%.5f"/><c:w val="%.5f"/><c:h val="%.5f"/></c:manualLayout>'
           '</c:layout>%s%s</c:plotArea><c:plotVisOnly val="1"/><c:dispBlanksAs val="gap"/></c:chart>%s%s'
           '<c:externalData r:id="%s"><c:autoUpdate val="0"/></c:externalData></c:chartSpace>'
           % (NSDECL, x, y, w, h, plot_xml, _sppr(th), _sppr(th), _txpr(th), rid))
    new = etree.fromstring(xml)
    for c in list(cs):
        cs.remove(c)
    for c in list(new):
        cs.append(c)
    etree.cleanup_namespaces(cs)


def _frac(frame: Box, pb: Box):
    return ((pb.x - frame.x) / frame.w, (pb.y - frame.y) / frame.h, pb.w / frame.w, pb.h / frame.h)


def _frame(slide, box: Box, xl_type, data, name, alt, kind):
    gf = slide.shapes.add_chart(xl_type, *box.emu, data)
    gf.name = name
    c = gf._element.find(".//" + _P + "cNvPr")
    c.set("descr", "%s (chart kind %s)" % (" ".join(str(alt).split())[:88], kind))
    return gf, gf.chart._chartSpace


def _cat_data(categories, series: dict):
    from pptx.chart.data import CategoryChartData
    cd = CategoryChartData(number_format="General")
    cd.categories = list(categories)
    for k, v in series.items():
        cd.add_series(str(k), [float(x) for x in v])
    return cd


def _xl(name):
    from pptx.enum.chart import XL_CHART_TYPE
    return getattr(XL_CHART_TYPE, name)


# ------------------------------------------------------------------ the plot

@dataclass
class Plot:
    """A chart on its slide. box is the pinned inner plot area in slide inches; val, cat, point and xy turn data
    into inches. marks lists the kit shapes drawn for it, by name."""
    slide: object
    name: str
    theme: object
    type: str
    frame: Box
    box: Box
    kind: str
    categories: tuple = ()
    series: dict = field(default_factory=dict)
    horizontal: bool = False
    vmin: float = 0.0
    vmax: float = 1.0
    xmin: float = 0.0
    xmax: float = 1.0
    bar_in: float = 0.0
    subject: object = None
    marks: list = field(default_factory=list)
    notes: int = 0

    def val(self, v: float) -> float:
        f = (float(v) - self.vmin) / (self.vmax - self.vmin)
        return self.box.x + self.box.w * f if self.horizontal else self.box.b - self.box.h * f

    def cat(self, i: int) -> float:
        n = max(1, len(self.categories))
        if self.horizontal:
            return self.box.y + self.box.h * (i + 0.5) / n
        return self.box.x + self.box.w * (i + 0.5) / n

    def point(self, i: int, v: float) -> tuple[float, float]:
        return (self.val(v), self.cat(i)) if self.horizontal else (self.cat(i), self.val(v))

    def xy(self, x: float, y: float) -> tuple[float, float]:
        fx = (float(x) - self.xmin) / (self.xmax - self.xmin)
        fy = (float(y) - self.vmin) / (self.vmax - self.vmin)
        return self.box.x + self.box.w * fx, self.box.b - self.box.h * fy

    @property
    def numbers(self) -> dict:
        return {k: list(v) if not isinstance(v, dict) else dict(v) for k, v in self.series.items()}

    def _mark(self, shape):
        self.marks.append(shape.name)
        return shape


def _basis_present(slide, text: str) -> bool:
    for sh in slide.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip() == text:
            return True
    return False


def _basis_h(th) -> float:
    return _lh(BASIS_PT, th) + 0.02


def _wants_basis(slide, kind, basis) -> bool:
    return bool(basis) and kind in BASIS and not _basis_present(slide, BASIS[kind])


def _draw_basis(slide, frame: Box, kind, name, th):
    t = BASIS[kind]
    w = _tw(t, BASIS_PT, th) + 0.04
    return _text(slide, Box(frame.r - PAD - w, frame.y + PAD, w, _basis_h(th)), t, role="ink-muted", pt=BASIS_PT,
                 align="right", anchor="top", name="%s.basis" % name, th=th)


def _clean(name, categories, values, *, negative=False):
    cats = [str(c) for c in categories]
    vals = [float(v) for v in values]
    if not cats or len(cats) != len(vals):
        raise ChartError("chart %s data" % name, need="one value per category", have="%d categories, %d values"
                         % (len(cats), len(vals)))
    if len(cats) > MAX_CATEGORIES:
        raise ChartError("chart %s categories" % name, need="at most %d" % MAX_CATEGORIES, have=len(cats),
                         hint="a chart that needs more rows is a table")
    if not negative and any(v < 0 for v in vals):
        raise ChartError("chart %s values" % name, need="values >= 0", have=min(vals),
                         hint="a bar starts at zero; show a negative step with waterfall()")
    return cats, vals


def _subject_index(name, cats, subject):
    if subject is None:
        return None
    if isinstance(subject, int) and not isinstance(subject, bool):
        if not 0 <= subject < len(cats):
            raise ChartError("chart %s subject" % name, need="0..%d" % (len(cats) - 1), have=subject)
        return subject
    if str(subject) not in cats:
        raise ChartError("chart %s subject" % name, need="one of " + ", ".join(cats), have=subject)
    if cats.count(str(subject)) > 1:
        raise ChartError("chart %s subject" % name, need="one subject per chart", have="%r twice" % subject)
    return cats.index(str(subject))


def _row_roles(n, si):
    return [SUBJECT if i == si else (CONTEXT if si is not None else "series-1") for i in range(n)]


def _gap(band, n_bars=1) -> tuple[int, float]:
    bar = min(band / (n_bars + GAP_MIN / 100.0), BAR_MAX_IN)
    gap = int(round((band / bar - n_bars) * 100))
    gap = max(GAP_MIN, min(GAP_MAX, gap))
    return gap, band / (n_bars + gap / 100.0)


def _too_small(name, pb: Box, need_w=0.8, need_h=0.6):
    if pb.w < need_w or pb.h < need_h:
        raise Overflows("chart %s plot area" % name, need="%.2f x %.2f in" % (need_w, need_h),
                        have="%.2f x %.2f in" % (pb.w, pb.h), hint="give the chart a larger box or shorter labels")


# ------------------------------------------------------------------ bar and column

@ooxml.transactional
def bar(slide, box: Box, categories, values, *, kind: str, name: str, subject=None, fmt="{:,.0f}", vmax=None,
        sort=None, cat_pt=CAT_PT, label_pt=LABEL_PT, alt=None, basis=True, theme=None) -> Plot:
    """Horizontal bars, one series, categories top to bottom. subject (a category or its index) is the one bar in
    accent, the rest grey context; with no subject every bar is navy. Category names right-aligned left of the plot
    (wrapping to two lines at most), values at each tip, the subject's bold. sort='desc' for magnitudes."""
    th = _th(theme)
    _named(name, "name")
    _kind(kind, name)
    cats, vals = _clean(name, categories, values)
    if sort == "desc":
        order = sorted(range(len(cats)), key=lambda i: -vals[i])
        cats, vals = [cats[i] for i in order], [vals[i] for i in order]
    elif sort not in (None, "none"):
        raise ChartError("chart %s sort" % name, need="None or 'desc'", have=sort)
    n = len(cats)
    si = _subject_index(name, cats, subject)
    labels = [_fmt(fmt, v) for v in vals]
    lw = [_tw(t, SUBJECT_PT if i == si else label_pt, th, bold=(i == si)) + 0.04 for i, t in enumerate(labels)]
    cw = max(_tw(c, cat_pt, th) for c in cats) + 0.04
    L = min(cw + 0.14, 0.40 * box.w) + PAD
    R = max(lw) + 0.10 + PAD
    want_basis = _wants_basis(slide, kind, basis)
    T = PAD + (_basis_h(th) + 0.06 if want_basis else 0.0)
    pb = Box(box.x + L, box.y + T, box.w - L - R, box.h - T - PAD)
    _too_small(name, pb, need_h=0.32 * n)
    band = pb.h / n
    top = max(vals) if vmax is None else float(vmax)
    if top < max(vals) or top <= 0:
        raise ChartError("chart %s vmax" % name, need=">= the largest value and > 0", have=top)
    gap, bar_in = _gap(band)
    roles = _row_roles(n, si)
    gf, cs = _frame(slide, box, _xl("BAR_CLUSTERED"), _cat_data(cats, {"value": vals}), name,
                    alt or "Bar chart: " + ", ".join("%s %s" % (c, t) for c, t in zip(cats, labels)), kind)
    refs = _harvest(cs)[0]
    base = CONTEXT if si is not None else "series-1"
    xml = ('<c:barChart><c:barDir val="bar"/><c:grouping val="clustered"/><c:varyColors val="0"/>%s'
           '<c:gapWidth val="%d"/><c:axId val="%d"/><c:axId val="%d"/></c:barChart>'
           % (_bar_ser(th, 0, refs, base, roles), gap, AX_CAT, AX_VAL)
           + _cat_ax(th, AX_CAT, AX_VAL, "l", reverse=True) + _val_ax(th, AX_VAL, AX_CAT, "b", 0, top, delete=True))
    _space(cs, th, xml, _frac(box, pb))
    plot = Plot(slide, name, th, "bar", box, pb, kind, tuple(cats), {"value": vals}, horizontal=True, vmin=0.0,
                vmax=top, bar_in=bar_in, subject=si)
    cat_w = L - PAD - 0.12
    for i, c in enumerate(cats):
        h = _need_h(c, cat_w, cat_pt, th) + 0.02
        if h > band + 1e-6:
            raise Overflows("chart %s category %r" % (name, c), need=round(h, 3), have=round(band, 3),
                            hint="shorten the category name or give the chart more height")
        cy = plot.cat(i)
        plot._mark(_text(slide, Box(box.x + PAD, cy - h / 2, cat_w, h), c, role="ink", pt=cat_pt, align="right",
                         name="%s.cat.%d" % (name, i + 1), th=th))
    for i, t in enumerate(labels):
        pt = SUBJECT_PT if i == si else label_pt
        h = _lh(pt, th) + 0.04
        cy = plot.cat(i)
        plot._mark(_text(slide, Box(plot.val(vals[i]) + 0.08, cy - h / 2, lw[i], h), t, role="ink-deep", pt=pt,
                         bold=(i == si), name="%s.value.%d" % (name, i + 1), th=th))
    if want_basis:
        plot._mark(_draw_basis(slide, box, kind, name, th))
    return plot


@ooxml.transactional
def column(slide, box: Box, categories, values, *, kind: str, name: str, subject=None, fmt="{:,.0f}", vmax=None,
           cat_pt=TICK_PT, label_pt=LABEL_PT, alt=None, basis=True, theme=None) -> Plot:
    """Vertical columns, one series, categories left to right (time order). subject as for bar(). Category names
    centred under each column (two lines at most, never rotated), values above each cap."""
    th = _th(theme)
    _named(name, "name")
    _kind(kind, name)
    cats, vals = _clean(name, categories, values)
    n = len(cats)
    si = _subject_index(name, cats, subject)
    labels = [_fmt(fmt, v) for v in vals]
    want_basis = _wants_basis(slide, kind, basis)
    vh = _lh(SUBJECT_PT, th) + 0.04
    T = PAD + vh + 0.06 + (_basis_h(th) + 0.04 if want_basis else 0.0)
    band0 = (box.w - 2 * PAD) / n
    ch = max(_need_h(c, band0 - 0.08, cat_pt, th) for c in cats) + 0.02
    if ch > 2 * _lh(cat_pt, th) + 0.05:
        raise Overflows("chart %s category names" % name, need="two lines at %.2fin" % (band0 - 0.08),
                        have="%.2fin of text" % ch, hint="shorten the category names; they never rotate")
    B = PAD + ch + 0.06
    pb = Box(box.x + PAD, box.y + T, box.w - 2 * PAD, box.h - T - B)
    _too_small(name, pb)
    band = pb.w / n
    top = max(vals) if vmax is None else float(vmax)
    if top < max(vals) or top <= 0:
        raise ChartError("chart %s vmax" % name, need=">= the largest value and > 0", have=top)
    for i, t in enumerate(labels):
        w = _tw(t, SUBJECT_PT if i == si else label_pt, th, bold=(i == si))
        if w > band - 0.04:
            raise Overflows("chart %s value %r" % (name, t), need=round(w, 3), have=round(band - 0.04, 3),
                            hint="a shorter format, fewer columns or a wider chart")
    gap, bar_in = _gap(band)
    roles = _row_roles(n, si)
    gf, cs = _frame(slide, box, _xl("COLUMN_CLUSTERED"), _cat_data(cats, {"value": vals}), name,
                    alt or "Column chart: " + ", ".join("%s %s" % (c, t) for c, t in zip(cats, labels)), kind)
    refs = _harvest(cs)[0]
    base = CONTEXT if si is not None else "series-1"
    xml = ('<c:barChart><c:barDir val="col"/><c:grouping val="clustered"/><c:varyColors val="0"/>%s'
           '<c:gapWidth val="%d"/><c:axId val="%d"/><c:axId val="%d"/></c:barChart>'
           % (_bar_ser(th, 0, refs, base, roles), gap, AX_CAT, AX_VAL)
           + _cat_ax(th, AX_CAT, AX_VAL, "b") + _val_ax(th, AX_VAL, AX_CAT, "l", 0, top, delete=True))
    _space(cs, th, xml, _frac(box, pb))
    plot = Plot(slide, name, th, "column", box, pb, kind, tuple(cats), {"value": vals}, vmin=0.0, vmax=top,
                bar_in=bar_in, subject=si)
    for i, c in enumerate(cats):
        cx = plot.cat(i)
        plot._mark(_text(slide, Box(cx - band / 2 + 0.04, pb.b + 0.06, band - 0.08, ch), c, role="ink-muted",
                         pt=cat_pt, align="center", anchor="top", name="%s.cat.%d" % (name, i + 1), th=th))
    for i, t in enumerate(labels):
        pt = SUBJECT_PT if i == si else label_pt
        h = _lh(pt, th) + 0.04
        cx = plot.cat(i)
        plot._mark(_text(slide, Box(cx - band / 2 + 0.02, plot.val(vals[i]) - 0.05 - h, band - 0.04, h), t,
                         role="ink-deep", pt=pt, bold=(i == si), align="center", anchor="bottom",
                         name="%s.value.%d" % (name, i + 1), th=th))
    if want_basis:
        plot._mark(_draw_basis(slide, box, kind, name, th))
    return plot


# ------------------------------------------------------------------ stacked

def _on(th, fill) -> str | None:
    """The darker ink role that reads on fill at 4.5:1, or None when no ink role does."""
    for role in ("ink-deep", "paper"):
        if contrast(th.hex(role), th.hex(fill)) >= 4.5:
            return role
    return None


@ooxml.transactional
def stacked(slide, box: Box, categories, series: dict, *, kind: str, name: str, subject=None, fmt="{:,.0f}",
            total_fmt=None, vmax=None, cat_pt=CAT_PT, label_pt=LABEL_PT, alt=None, basis=True, theme=None) -> Plot:
    """Horizontal stacked bars: one bar per category, up to three named segments plus an optional 'Other' in grey
    context. subject (a series name) is the accent segment; the others navy, then grey. Segment names sit above the
    first bar's segments (a direct key, never a legend box); a segment value is written inside when it fits and its
    fill takes an ink role at 4.5:1, else the bar's total at its end carries the number. Segments are outlined 1.5pt
    in paper, the gap between them."""
    th = _th(theme)
    _named(name, "name")
    _kind(kind, name)
    names = [str(k) for k in series]
    named = [k for k in names if k != "Other"]
    if not 1 <= len(named) <= CATEGORICAL_MAX:
        raise ChartError("chart %s series" % name, need="1 to %d named segments (+ Other)" % CATEGORICAL_MAX,
                         have=len(named), hint="merge the small segments into 'Other'")
    cats = [str(c) for c in categories]
    data = {k: [float(v) for v in series[k]] for k in names}
    for k, v in data.items():
        _clean(name, cats, v)
    if subject is not None and str(subject) not in named:
        raise ChartError("chart %s subject" % name, need="one of " + ", ".join(named), have=subject)
    others = iter(OTHERS)
    roles = {}
    for k in names:
        roles[k] = CONTEXT if k == "Other" else (SUBJECT if k == str(subject) else next(others))
    _theme_ok(th, [r for r in roles.values() if r != CONTEXT])
    n = len(cats)
    totals = [sum(data[k][i] for k in names) for i in range(n)]
    tfmt = total_fmt or fmt
    tlab = [_fmt(tfmt, t) for t in totals]
    want_basis = _wants_basis(slide, kind, basis)
    key_h = _lh(TICK_PT, th) + 0.04
    T = PAD + key_h + 0.06 + (_basis_h(th) + 0.04 if want_basis else 0.0)
    cw = max(_tw(c, cat_pt, th) for c in cats) + 0.04
    L = min(cw + 0.14, 0.40 * box.w) + PAD
    R = max(_tw(t, label_pt, th, bold=True) for t in tlab) + 0.14 + PAD
    pb = Box(box.x + L, box.y + T, box.w - L - R, box.h - T - PAD)
    _too_small(name, pb, need_h=0.32 * n)
    top = max(totals) if vmax is None else float(vmax)
    if top < max(totals):
        raise ChartError("chart %s vmax" % name, need=">= the largest total", have=top)
    band = pb.h / n
    gap, bar_in = _gap(band)
    gf, cs = _frame(slide, box, _xl("BAR_STACKED"), _cat_data(cats, data), name,
                    alt or "Stacked bar chart of %s by %s" % (", ".join(named), ", ".join(cats)), kind)
    refs = _harvest(cs)
    sers = "".join(_bar_ser(th, i, refs[i], roles[k], outline="paper") for i, k in enumerate(names))
    xml = ('<c:barChart><c:barDir val="bar"/><c:grouping val="stacked"/><c:varyColors val="0"/>%s'
           '<c:gapWidth val="%d"/><c:overlap val="100"/><c:axId val="%d"/><c:axId val="%d"/></c:barChart>'
           % (sers, gap, AX_CAT, AX_VAL)
           + _cat_ax(th, AX_CAT, AX_VAL, "l", reverse=True) + _val_ax(th, AX_VAL, AX_CAT, "b", 0, top, delete=True))
    _space(cs, th, xml, _frac(box, pb))
    plot = Plot(slide, name, th, "stacked", box, pb, kind, tuple(cats), data, horizontal=True, vmax=top,
                bar_in=bar_in, subject=subject)
    cat_w = L - PAD - 0.12
    for i, c in enumerate(cats):
        h = _need_h(c, cat_w, cat_pt, th) + 0.02
        if h > band + 1e-6:
            raise Overflows("chart %s category %r" % (name, c), need=round(h, 3), have=round(band, 3))
        cy = plot.cat(i)
        plot._mark(_text(slide, Box(box.x + PAD, cy - h / 2, cat_w, h), c, role="ink", pt=cat_pt, align="right",
                         name="%s.cat.%d" % (name, i + 1), th=th))
    # the key: segment names over the first bar's segments
    run = 0.0
    y_key = pb.y - 0.06 - key_h
    for j, k in enumerate(names):
        a, b = plot.val(run), plot.val(run + data[k][0])
        run += data[k][0]
        w = _tw(k, TICK_PT, th, bold=(k == str(subject))) + 0.04
        if w > (b - a) + 0.02:
            raise Overflows("chart %s key %r" % (name, k), need=round(w, 3), have=round(b - a, 3),
                            hint="a shorter segment name, or order the segments so the first bar's are wide enough")
        plot._mark(_text(slide, Box((a + b) / 2 - w / 2, y_key, w, key_h), k, role="ink-deep" if k == str(subject)
                         else "ink-muted", pt=TICK_PT, bold=(k == str(subject)), align="center", anchor="bottom",
                         name="%s.key.%d" % (name, j + 1), th=th))
    for i in range(n):
        run = 0.0
        cy = plot.cat(i)
        for j, k in enumerate(names):
            v = data[k][i]
            a, b = plot.val(run), plot.val(run + v)
            run += v
            t = _fmt(fmt, v)
            ink = _on(th, roles[k])
            w = _tw(t, label_pt, th) + 0.04
            h = _lh(label_pt, th) + 0.04
            if v > 0 and ink and w + 0.16 <= (b - a) and h <= bar_in:
                chip = _text(slide, Box((a + b) / 2 - w / 2, cy - h / 2, w, h), t, role=ink, pt=label_pt,
                             align="center", name="%s.seg.%d.%d" % (name, i + 1, j + 1), th=th, background=roles[k])
                prims.set_fill(chip, roles[k], theme=th)     # painted in its segment's role: what P25 reads is true
                plot._mark(chip)
        w = _tw(tlab[i], label_pt, th, bold=True) + 0.04
        h = _lh(label_pt, th) + 0.04
        plot._mark(_text(slide, Box(plot.val(totals[i]) + 0.08, cy - h / 2, w, h), tlab[i], role="ink-deep",
                         pt=label_pt, bold=True, name="%s.value.%d" % (name, i + 1), th=th))
    if want_basis:
        plot._mark(_draw_basis(slide, box, kind, name, th))
    return plot


# ------------------------------------------------------------------ line and area

def _end_labels(plot, items, th, label_pt, x0, right):
    """items: [(text, y, bold, role)]; de-collided top to bottom inside the frame; returns [(text, y_label, ...)]."""
    h = _lh(label_pt, th) + 0.04
    placed = sorted(items, key=lambda t: t[1])
    ys = []
    lo, hi = plot.frame.y + PAD, plot.frame.b - PAD - h
    for _t, y, *_ in placed:
        top = min(max(y - h / 2, lo), hi)
        if ys and top < ys[-1] + h:
            top = ys[-1] + h
        ys.append(top)
    if ys and ys[-1] > hi:                       # pushed past the foot: shift the stack up
        d = ys[-1] - hi
        ys = [max(lo, t - d) for t in ys]
    return [(it, top, h) for it, top in zip(placed, ys)]


@ooxml.transactional
def line(slide, box: Box, categories, series: dict, *, kind: str, name: str, subject=None, vmin=0.0, vmax=None,
         fmt="{:,.0f}", axis_format="#,##0", tick_fmt=None, ticks=4, end_labels=True, area=False, cat_pt=TICK_PT,
         label_pt=LABEL_PT, alt=None, basis=True, theme=None) -> Plot:
    """Lines over ordered categories, up to three series. subject (a series name; the only series by default) is the
    accent line with solid markers; the others navy, then grey, without markers. The value axis is native (ticks at
    `ticks` nice steps, `axis_format` an Excel number format, `tick_fmt` its Python twin for measuring) with
    hairline-soft gridlines; category names sit under each point; each series ends in a direct label (name and last
    value), never a legend. area=True washes the area under a single series in accent-wash."""
    th = _th(theme)
    _named(name, "name")
    _kind(kind, name)
    names = [str(k) for k in series]
    if not 1 <= len(names) <= CATEGORICAL_MAX:
        raise ChartError("chart %s series" % name, need="1 to %d" % CATEGORICAL_MAX, have=len(names),
                         hint="more lines than three is small multiples, or a table")
    if area and len(names) != 1:
        raise ChartError("chart %s area" % name, need="one series under an area wash", have=len(names),
                         hint="stacked areas are refused: use stacked()")
    cats = [str(c) for c in categories]
    data = {k: [float(v) for v in series[k]] for k in names}
    for k, v in data.items():
        _clean(name, cats, v, negative=True)
    subject = names[0] if (subject is None and len(names) == 1) else subject
    if subject is not None and str(subject) not in names:
        raise ChartError("chart %s subject" % name, need="one of " + ", ".join(names), have=subject)
    others = iter(OTHERS)
    roles = {k: (SUBJECT if k == str(subject) else next(others)) for k in names}
    _theme_ok(th, list(roles.values()))
    lo_data = min(min(v) for v in data.values())
    if vmin is None or lo_data < float(vmin):
        raise ChartError("chart %s vmin" % name, need="<= the smallest value (%s)" % _num(lo_data), have=vmin)
    vmin = float(vmin)
    if vmax is None:
        span, unit = nice_ceiling(max(max(v) for v in data.values()) - vmin, ticks, headroom=0.08)
        top = vmin + span
    else:
        top = float(vmax)
        unit = (top - vmin) / ticks
    if top < max(max(v) for v in data.values()):
        raise ChartError("chart %s vmax" % name, need=">= the largest value", have=top)
    tf = tick_fmt or (lambda v: "{:,.0f}".format(v))
    tick_labels = [_fmt(tf, vmin + unit * k) for k in range(int(round((top - vmin) / unit)) + 1)]
    n = len(cats)
    want_basis = _wants_basis(slide, kind, basis)
    th_tick = _lh(TICK_PT, th)
    L = PAD + max(_tw(t, TICK_PT, th) for t in tick_labels) + 0.10
    T = PAD + th_tick / 2 + 0.04 + (_basis_h(th) + 0.04 if want_basis else 0.0)
    end_text = {k: "%s %s" % (k, _fmt(fmt, data[k][-1])) for k in names}
    ew = {k: _tw(end_text[k], label_pt, th, bold=(k == str(subject))) + 0.04 for k in names}
    R = PAD + 0.04
    if end_labels:               # the last point sits half a band inside the plot: solve R so its label still fits
        k2 = 1.0 / (2 * n)
        R = max(R, (max(ew.values()) + 0.16 + PAD - (box.w - L) * k2) / (1 - k2))
    band0 = (box.w - L - R) / n
    ch = max(_need_h(c, band0 - 0.08, cat_pt, th) for c in cats) + 0.02
    if ch > 2 * _lh(cat_pt, th) + 0.05:
        raise Overflows("chart %s category names" % name, need="two lines at %.2fin" % (band0 - 0.08),
                        have="%.2fin of text" % ch, hint="shorten the category names; they never rotate")
    B = PAD + ch + 0.08
    pb = Box(box.x + L, box.y + T, box.w - L - R, box.h - T - B)
    _too_small(name, pb)
    band = pb.w / n
    xl = "AREA" if area else "LINE"
    gf, cs = _frame(slide, box, _xl(xl), _cat_data(cats, data), name,
                    alt or "Line chart of %s over %s" % (", ".join(names), ", ".join(cats)), kind)
    refs = _harvest(cs)
    parts = []
    idx = 0
    if area:
        parts.append('<c:areaChart><c:grouping val="standard"/><c:varyColors val="0"/><c:ser><c:idx val="0"/>'
                     '<c:order val="0"/>%s%s%s%s</c:ser><c:axId val="%d"/><c:axId val="%d"/></c:areaChart>'
                     % (refs[0]["tx"], _sppr(th, WASH, None), refs[0]["cat"], refs[0]["val"], AX_CAT, AX_VAL))
        idx = 1
    sers = []
    for j, k in enumerate(names):
        r = roles[k]
        sers.append('<c:ser><c:idx val="%d"/><c:order val="%d"/>%s%s%s%s%s<c:smooth val="0"/></c:ser>'
                    % (idx + j, idx + j, refs[j]["tx"], "<c:spPr>%s</c:spPr>" % _ln(th, r, LINE_PT, round_=True),
                       _marker(th, r if r == SUBJECT else None), refs[j]["cat"], refs[j]["val"]))
    parts.append('<c:lineChart><c:grouping val="standard"/><c:varyColors val="0"/>%s<c:marker val="1"/>'
                 '<c:axId val="%d"/><c:axId val="%d"/></c:lineChart>' % ("".join(sers), AX_CAT, AX_VAL))
    xml = "".join(parts) + _cat_ax(th, AX_CAT, AX_VAL, "b") + _val_ax(
        th, AX_VAL, AX_CAT, "l", vmin, top, delete=False, grid=True, fmt=axis_format, unit=unit)
    _space(cs, th, xml, _frac(box, pb))
    plot = Plot(slide, name, th, "area" if area else "line", box, pb, kind, tuple(cats), data, vmin=vmin, vmax=top,
                subject=subject)
    for i, c in enumerate(cats):
        cx = plot.cat(i)
        plot._mark(_text(slide, Box(cx - band / 2 + 0.04, pb.b + 0.08, band - 0.08, ch), c, role="ink-muted",
                         pt=cat_pt, align="center", anchor="top", name="%s.cat.%d" % (name, i + 1), th=th))
    if end_labels:
        x_end = plot.cat(n - 1)
        items = [(end_text[k], plot.val(data[k][-1]), k == str(subject), k) for k in names]
        for (t, y, bold, k), top_y, h in _end_labels(plot, items, th, label_pt, x_end, box.r):
            x = x_end + 0.14
            plot._mark(_text(slide, Box(x, top_y, min(ew[k], box.r - PAD - x), h), t, role="ink-deep", pt=label_pt,
                             bold=bold, name="%s.end.%d" % (name, names.index(k) + 1), th=th))
            if abs((top_y + h / 2) - y) > 0.08:
                plot._mark(prims.connect(slide, (x_end + 0.05, y), (x - 0.02, top_y + h / 2), head="none",
                                         role="rule-strong", name="%s.leader.%d" % (name, names.index(k) + 1),
                                         theme=th))
    if want_basis:
        plot._mark(_draw_basis(slide, box, kind, name, th))
    return plot


def area(slide, box: Box, categories, values, *, series_name: str, kind: str, name: str, **kw) -> Plot:
    """One series as a line in accent over an accent-wash area (line(..., area=True))."""
    return line(slide, box, categories, {series_name: values}, kind=kind, name=name, area=True, **kw)


# ------------------------------------------------------------------ waterfall

@ooxml.transactional
def waterfall(slide, box: Box, steps, *, total: str, kind: str, name: str, fmt="{:,.0f}", signed=None,
              connectors=True, cat_pt=CAT_PT, label_pt=LABEL_PT, alt=None, basis=True, theme=None) -> Plot:
    """A horizontal bridge: each step (label, value) floats from the running total, the total bar (label `total`)
    starts at zero in accent. Positive steps navy, negative steps ink-muted (never accent). Values at each bar end,
    signed when any step is negative (or signed=True). connectors=True draws the dashed carry lines from each bar's
    end to the next bar, the one dash a chart allows (it means carried over). A stacked bar with an invisible base
    series underneath, so Edit Data still holds the arithmetic."""
    th = _th(theme)
    _named(name, "name")
    _kind(kind, name)
    steps = [(str(a), float(b)) for a, b in steps]
    if len(steps) < 2:
        raise ChartError("chart %s steps" % name, need="two or more steps", have=len(steps))
    cats = [a for a, _ in steps] + [str(total)]
    _clean(name, cats, [abs(b) for _, b in steps] + [0.0])
    sign = any(b < 0 for _, b in steps) if signed is None else bool(signed)
    base, length, roles, run, ends = [], [], [], 0.0, []
    for _, v in steps:
        if v >= 0:
            base.append(run)
            length.append(v)
            roles.append("series-1")
        else:
            base.append(run + v)
            length.append(-v)
            roles.append(NEGATIVE)
        run += v
        ends.append(run)
        if run < 0:
            raise ChartError("chart %s running total" % name, need=">= 0", have=run,
                             hint="a bridge that goes below zero needs a diverging axis; reorder the steps")
    base.append(0.0)
    length.append(run)
    roles.append(SUBJECT)
    labels = [(("+" if v >= 0 else "-") if sign else "") + _fmt(fmt, abs(v)) for _, v in steps] + [_fmt(fmt, run)]
    n = len(cats)
    lw = [_tw(t, SUBJECT_PT if i == n - 1 else label_pt, th, bold=(i == n - 1)) + 0.04 for i, t in enumerate(labels)]
    cw = max(_tw(c, cat_pt, th) for c in cats) + 0.04
    L = min(cw + 0.14, 0.40 * box.w) + PAD
    R = max(lw) + 0.10 + PAD
    want_basis = _wants_basis(slide, kind, basis)
    T = PAD + (_basis_h(th) + 0.06 if want_basis else 0.0)
    pb = Box(box.x + L, box.y + T, box.w - L - R, box.h - T - PAD)
    _too_small(name, pb, need_h=0.32 * n)
    top = max(max(b + ln for b, ln in zip(base, length)), run)
    band = pb.h / n
    gap, bar_in = _gap(band)
    gf, cs = _frame(slide, box, _xl("BAR_STACKED"), _cat_data(cats, {"base": base, "value": length}), name,
                    alt or "Waterfall: " + ", ".join("%s %s" % (c, t) for c, t in zip(cats, labels)), kind)
    refs = _harvest(cs)
    sers = ('<c:ser><c:idx val="0"/><c:order val="0"/>%s%s<c:invertIfNegative val="0"/>%s%s</c:ser>'
            % (refs[0]["tx"], _sppr(th), refs[0]["cat"], refs[0]["val"])) + _bar_ser(th, 1, refs[1], "series-1", roles)
    xml = ('<c:barChart><c:barDir val="bar"/><c:grouping val="stacked"/><c:varyColors val="0"/>%s'
           '<c:gapWidth val="%d"/><c:overlap val="100"/><c:axId val="%d"/><c:axId val="%d"/></c:barChart>'
           % (sers, gap, AX_CAT, AX_VAL)
           + _cat_ax(th, AX_CAT, AX_VAL, "l", reverse=True) + _val_ax(th, AX_VAL, AX_CAT, "b", 0, top, delete=True))
    _space(cs, th, xml, _frac(box, pb))
    plot = Plot(slide, name, th, "waterfall", box, pb, kind, tuple(cats), {"base": base, "value": length},
                horizontal=True, vmax=top, bar_in=bar_in, subject=n - 1)
    cat_w = L - PAD - 0.12
    for i, c in enumerate(cats):
        h = _need_h(c, cat_w, cat_pt, th) + 0.02
        if h > band + 1e-6:
            raise Overflows("chart %s category %r" % (name, c), need=round(h, 3), have=round(band, 3))
        cy = plot.cat(i)
        plot._mark(_text(slide, Box(box.x + PAD, cy - h / 2, cat_w, h), c, role="ink", pt=cat_pt, align="right",
                         bold=(i == n - 1), name="%s.cat.%d" % (name, i + 1), th=th))
    for i, t in enumerate(labels):
        pt = SUBJECT_PT if i == n - 1 else label_pt
        h = _lh(pt, th) + 0.04
        cy = plot.cat(i)
        plot._mark(_text(slide, Box(plot.val(base[i] + length[i]) + 0.08, cy - h / 2, lw[i], h), t, role="ink-deep",
                         pt=pt, bold=(i == n - 1), name="%s.value.%d" % (name, i + 1), th=th))
    if connectors:
        for i in range(n - 1):
            x = plot.val(ends[i] if i < n - 2 else run)
            y0 = plot.cat(i) + bar_in / 2
            y1 = plot.cat(i + 1) - bar_in / 2
            if y1 - y0 > 0.04:
                plot._mark(prims.connect(slide, (x, y0), (x, y1), head="none", dash="dash", role="rule-strong",
                                         name="%s.carry.%d" % (name, i + 1), theme=th))
    if want_basis:
        plot._mark(_draw_basis(slide, box, kind, name, th))
    return plot


# ------------------------------------------------------------------ scatter and bubble

def _overlaps(a, b, pad=0.02) -> bool:
    return not (a[2] + pad <= b[0] or b[2] + pad <= a[0] or a[3] + pad <= b[1] or b[3] + pad <= a[1])


@ooxml.transactional
def scatter(slide, box: Box, points, *, x_range, y_range, x_label: str, y_label: str, kind: str, name: str,
            groups=None, subject=None, sizes=None, splits=None, quadrants=None, numbered=False, ticks=4,
            axis_format="0", tick_fmt=None, label_pt=10.0, alt=None, basis=True, theme=None) -> Plot:
    """Points (label, x, y) on two fixed native value axes. groups (a dict from point label to group name, up to three groups) colour
    the points: subject (a group name, or a point label when there are no groups) in accent, the others navy, then
    grey. Each point is labelled beside its marker (right, left, above, below, the first that collides with
    nothing), or by its 1-based number when numbered=True (the builder draws the key). splits (x, y) draws the
    quadrant rules as dashed grey lines and quadrants (top-left, top-right, bottom-left, bottom-right) names their
    corners. sizes turns it into a bubble chart whose bubble AREA maps the size. Axis names are kit text: y_label
    over the y axis, x_label under the x axis, never rotated."""
    th = _th(theme)
    _named(name, "name")
    _kind(kind, name)
    pts = [(str(a), float(x), float(y)) for a, x, y in points]
    if not pts:
        raise ChartError("chart %s points" % name, need="one or more points", have=0)
    (x0, x1), (y0, y1) = (float(x_range[0]), float(x_range[1])), (float(y_range[0]), float(y_range[1]))
    for lab, x, y in pts:
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            raise ChartError("chart %s point %r" % (name, lab), need="inside the axis ranges", have=(x, y))
    labels = [p[0] for p in pts]
    if len(set(labels)) != len(labels):
        raise ChartError("chart %s points" % name, need="unique point labels", have="duplicates")
    gmap = dict(groups or {})
    if gmap:
        order = []
        for lab in labels:
            g = gmap.get(lab)
            if g is None:
                raise ChartError("chart %s groups" % name, need="a group for every point", have="none for %r" % lab)
            if g not in order:
                order.append(g)
    else:
        order = ["Points"]
        gmap = {lab: "Points" for lab in labels}
    if len(order) > CATEGORICAL_MAX:
        raise ChartError("chart %s groups" % name, need="at most %d" % CATEGORICAL_MAX, have=len(order))
    if subject is not None and groups and subject not in order:
        raise ChartError("chart %s subject" % name, need="one of " + ", ".join(order), have=subject)
    if subject is not None and not groups and subject not in labels:
        raise ChartError("chart %s subject" % name, need="a point label", have=subject)
    others = iter(OTHERS)
    groles = {g: (SUBJECT if (groups and g == subject) else next(others)) for g in order}
    _theme_ok(th, [SUBJECT] + [r for r in groles.values() if r != SUBJECT] if (subject is not None) else
              list(groles.values()))
    if sizes is not None:
        sizes = [float(s) for s in sizes]
        if len(sizes) != len(pts) or min(sizes) <= 0:
            raise ChartError("chart %s sizes" % name, need="one positive size per point", have=len(sizes))
    want_basis = _wants_basis(slide, kind, basis)
    tf = tick_fmt or (lambda v: ("%g" % v))
    xs = [x0 + (x1 - x0) * k / ticks for k in range(ticks + 1)]
    ys = [y0 + (y1 - y0) * k / ticks for k in range(ticks + 1)]
    tick_h = _lh(TICK_PT, th)
    yl_h = _lh(TICK_PT, th) + 0.04
    L = PAD + max(_tw(_fmt(tf, v), TICK_PT, th) for v in ys) + 0.12
    T = PAD + yl_h + 0.06 + tick_h / 2 + (_basis_h(th) + 0.04 if want_basis else 0.0)
    B = PAD + tick_h + 0.10 + yl_h + 0.04
    R = PAD + _tw(_fmt(tf, xs[-1]), TICK_PT, th) / 2 + 0.04
    pb = Box(box.x + L, box.y + T, box.w - L - R, box.h - T - B)
    _too_small(name, pb, 2.0, 1.5)
    from pptx.chart.data import BubbleChartData, XyChartData
    cd = BubbleChartData() if sizes else XyChartData()
    for g in order:
        s = cd.add_series(g)
        for k, (lab, x, y) in enumerate(pts):
            if gmap[lab] == g:
                if sizes:
                    s.add_data_point(x, y, sizes[k])
                else:
                    s.add_data_point(x, y)
    gf, cs = _frame(slide, box, _xl("BUBBLE" if sizes else "XY_SCATTER"), cd, name,
                    alt or "Scatter of %d items, %s against %s" % (len(pts), y_label, x_label), kind)
    refs = _harvest(cs)
    sers = []
    for j, g in enumerate(order):
        members = [lab for lab in labels if gmap[lab] == g]
        point_roles = [SUBJECT if (not groups and lab == subject) else groles[g] for lab in members]
        role = groles[g]
        if sizes:
            sers.append('<c:ser><c:idx val="%d"/><c:order val="%d"/>%s%s<c:invertIfNegative val="0"/>%s%s%s%s'
                        '<c:bubble3D val="0"/></c:ser>'
                        % (j, j, refs[j]["tx"], _sppr(th, role, "paper", 1.0), _dpts(th, point_roles, role,
                                                                                       outline="paper"),
                           refs[j]["xVal"], refs[j]["yVal"], refs[j]["bubbleSize"]))
        else:
            dp = "".join('<c:dPt><c:idx val="%d"/>%s</c:dPt>' % (i, _marker(th, r, 9)) for i, r in
                         enumerate(point_roles) if r != role)
            sers.append('<c:ser><c:idx val="%d"/><c:order val="%d"/>%s<c:spPr>%s</c:spPr>%s%s%s%s'
                        '<c:smooth val="0"/></c:ser>'
                        % (j, j, refs[j]["tx"], _ln(th), _marker(th, role, 9), dp, refs[j]["xVal"], refs[j]["yVal"]))
    if sizes:
        group = ('<c:bubbleChart><c:varyColors val="0"/>%s<c:bubbleScale val="60"/><c:showNegBubbles val="0"/>'
                 '<c:sizeRepresents val="area"/><c:axId val="%d"/><c:axId val="%d"/></c:bubbleChart>'
                 % ("".join(sers), AX_X, AX_Y))
    else:
        group = ('<c:scatterChart><c:scatterStyle val="lineMarker"/><c:varyColors val="0"/>%s<c:axId val="%d"/>'
                 '<c:axId val="%d"/></c:scatterChart>' % ("".join(sers), AX_X, AX_Y))
    xml = group + _val_ax(th, AX_X, AX_Y, "b", x0, x1, delete=False, fmt=axis_format, unit=(x1 - x0) / ticks,
                          between=False, line=AXIS) \
        + _val_ax(th, AX_Y, AX_X, "l", y0, y1, delete=False, fmt=axis_format, unit=(y1 - y0) / ticks,
                  between=False, line=AXIS)
    _space(cs, th, xml, _frac(box, pb))
    plot = Plot(slide, name, th, "bubble" if sizes else "scatter", box, pb, kind, tuple(labels),
                {"x": [p[1] for p in pts], "y": [p[2] for p in pts]}, vmin=y0, vmax=y1, xmin=x0, xmax=x1,
                subject=subject)
    # axis names: never rotated
    w = _tw(y_label, TICK_PT, th, bold=True) + 0.04
    plot._mark(_text(slide, Box(box.x + PAD, pb.y - tick_h / 2 - 0.06 - yl_h, min(w, box.w - 2 * PAD), yl_h), y_label,
                     role="ink-muted", pt=TICK_PT, bold=True, anchor="bottom", name="%s.axis.y" % name, th=th))
    w = _tw(x_label, TICK_PT, th, bold=True) + 0.04
    plot._mark(_text(slide, Box(pb.r - min(w, pb.w), box.b - PAD - yl_h, min(w, pb.w), yl_h), x_label,
                     role="ink-muted", pt=TICK_PT, bold=True, align="right", anchor="top", name="%s.axis.x" % name,
                     th=th))
    taken = []
    if splits:
        sx, sy = plot.xy(splits[0], splits[1])
        plot._mark(prims.connect(slide, (sx, pb.y), (sx, pb.b), head="none", dash="dash", role="rule-strong",
                                 name="%s.split.x" % name, theme=th))
        plot._mark(prims.connect(slide, (pb.x, sy), (pb.r, sy), head="none", dash="dash", role="rule-strong",
                                 name="%s.split.y" % name, theme=th))
    if quadrants:
        qh = _lh(TICK_PT, th) + 0.04
        for k, (q, (ax, ay)) in enumerate(zip(quadrants, ((0, 0), (1, 0), (0, 1), (1, 1)))):
            if not q:
                continue
            w = _tw(q, TICK_PT, th, bold=True) + 0.04
            bx_ = pb.x + 0.08 if ax == 0 else pb.r - 0.08 - w
            by_ = pb.y + 0.06 if ay == 0 else pb.b - 0.06 - qh
            plot._mark(_text(slide, Box(bx_, by_, w, qh), q, role="ink-muted", pt=TICK_PT, bold=True,
                             align="left" if ax == 0 else "right", name="%s.quad.%d" % (name, k + 1), th=th))
            taken.append((bx_, by_, bx_ + w, by_ + qh))
    # marker radius in inches: a 9pt marker, or a bubble (PowerPoint: the largest bubble's diameter is 25% of the
    # plot's smaller side times bubbleScale)
    if sizes:
        dmax = 0.25 * min(pb.w, pb.h) * 0.60
        radii = [dmax / 2 * math.sqrt(s / max(sizes)) for s in sizes]
    else:
        radii = [9 / 72 / 2] * len(pts)
    centres = [plot.xy(x, y) for _, x, y in pts]
    for (cx, cy), r in zip(centres, radii):
        taken.append((cx - r, cy - r, cx + r, cy + r))
    lh = _lh(label_pt, th) + 0.02
    for k, ((lab, _x, _y), (cx, cy), r) in enumerate(zip(pts, centres, radii)):
        t = str(k + 1) if numbered else lab
        bold = (subject is not None and ((groups and gmap[lab] == subject) or (not groups and lab == subject)))
        w = _tw(t, label_pt, th, bold=bold) + 0.04
        cands = [(cx + r + 0.05, cy - lh / 2), (cx - r - 0.05 - w, cy - lh / 2), (cx - w / 2, cy - r - 0.03 - lh),
                 (cx - w / 2, cy + r + 0.03)]
        spot = None
        for bx_, by_ in cands:
            rect = (bx_, by_, bx_ + w, by_ + lh)
            mine = (cx - r, cy - r, cx + r, cy + r)
            if rect[0] < box.x + PAD or rect[2] > box.r - PAD or rect[1] < box.y + PAD or rect[3] > box.b - PAD:
                continue
            if any(_overlaps(rect, o) for o in taken if o != mine):
                continue
            spot = rect
            break
        if spot is None:
            raise Overflows("chart %s point label %r" % (name, t), need="a free side of its marker",
                            have="all four sides taken", hint="numbered=True, shorter labels, or a larger chart")
        taken.append(spot)
        plot._mark(_text(slide, Box(spot[0], spot[1], w, lh), t, role="ink-deep" if bold else "ink", pt=label_pt,
                         bold=bold, name="%s.point.%d" % (name, k + 1), th=th))
    if want_basis:
        plot._mark(_draw_basis(slide, box, kind, name, th))
    return plot


# ------------------------------------------------------------------ ring

@ooxml.transactional
def ring(slide, box: Box, value: float, of: float, *, kind: str, name: str, alt=None, basis=True,
         theme=None) -> Plot:
    """A share ring (dv38): a native doughnut of two points, the share in accent and the remainder in card, hole 78%.
    No labels on the ring: put the centre figure in the hole with prims.stat. Two slices only; a comparison of close
    values is a bar chart."""
    th = _th(theme)
    _named(name, "name")
    _kind(kind, name)
    value, of = float(value), float(of)
    if not 0 < value < of:
        raise ChartError("chart %s ring" % name, need="0 < value < of", have=(value, of))
    if abs(box.w - box.h) > 0.005:
        raise GeometryError("chart %s ring" % name, need="a square box", have="%.2f x %.2f" % (box.w, box.h))
    gf, cs = _frame(slide, box, _xl("DOUGHNUT"), _cat_data(["Share", "Rest"], {"share": [value, of - value]}), name,
                    alt or "Share ring: %s of %s" % (_num(value), _num(of)), kind)
    refs = _harvest(cs)[0]
    dp = "".join('<c:dPt><c:idx val="%d"/><c:bubble3D val="0"/>%s</c:dPt>' % (i, _sppr(th, r)) for i, r in
                 enumerate((SUBJECT, "card")))
    xml = ('<c:doughnutChart><c:varyColors val="1"/><c:ser><c:idx val="0"/><c:order val="0"/>%s%s%s%s</c:ser>'
           '<c:firstSliceAng val="0"/><c:holeSize val="78"/></c:doughnutChart>'
           % (refs["tx"], dp, refs["cat"], refs["val"]))
    _space(cs, th, xml, (0.02, 0.02, 0.96, 0.96))
    pb = Box(box.x + box.w * 0.02, box.y + box.h * 0.02, box.w * 0.96, box.h * 0.96)
    plot = Plot(slide, name, th, "ring", box, pb, kind, ("Share", "Rest"), {"share": [value, of - value]})
    if _wants_basis(slide, kind, basis):
        raise ChartError("chart %s ring basis" % name, need="the slide's basis label drawn first", have="none",
                         hint="a ring has no room for a label; draw the stat or stat band with its basis first, or "
                              "pass basis=False after drawing one")
    return plot


# ------------------------------------------------------------------ KPI bullet and progress (kit shapes)

@dataclass(frozen=True)
class Row:
    label: str
    value: float
    target: float | None = None


@dataclass
class Bullets:
    name: str
    box: Box
    rows: tuple
    scale_max: float
    kind: str
    marks: list = field(default_factory=list)

    def x(self, v: float) -> float:
        return self._x0 + (self._x1 - self._x0) * float(v) / self.scale_max


@ooxml.transactional
def bullet(slide, box: Box, rows, *, scale_max: float, kind: str, name: str, subject=None, fmt="{:,.0f}",
           label_pt=LABEL_PT, basis=True, theme=None) -> Bullets:
    """KPI rows drawn from kit shapes (the gates see every part): the label, a card-filled track the full scale, a
    0.16in measure bar (navy; the subject row in accent), a target tick in ink-muted, and the value at the right.
    The bars are 0.16in thick: 0.10in and under is the accent strip the house refuses."""
    th = _th(theme)
    _named(name, "name")
    _kind(kind, name)
    rows = [r if isinstance(r, Row) else Row(*r) for r in rows]
    if not rows:
        raise ChartError("chart %s rows" % name, need="one or more rows", have=0)
    scale_max = float(scale_max)
    for r in rows:
        if not 0 <= r.value <= scale_max or (r.target is not None and not 0 <= r.target <= scale_max):
            raise ChartError("chart %s row %r" % (name, r.label), need="0..scale_max", have=(r.value, r.target))
    labels = [r.label for r in rows]
    si = _subject_index(name, labels, subject)
    vals = [_fmt(fmt, r.value) for r in rows]
    want_basis = _wants_basis(slide, kind, basis)
    top = box.y + (_basis_h(th) + 0.06 if want_basis else 0.0)
    lw = min(max(_tw(t, label_pt, th) for t in labels) + 0.06, 0.38 * box.w)
    vw = max(_tw(t, label_pt, th, bold=True) for t in vals) + 0.06
    x0, x1 = box.x + lw + 0.12, box.r - vw - 0.12
    if x1 - x0 < 1.0:
        raise Overflows("chart %s track" % name, need=1.0, have=round(x1 - x0, 3), hint="a wider box or shorter labels")
    rh = (box.b - top) / len(rows)
    need = max(_need_h(t, lw, label_pt, th) for t in labels) + 0.04
    if rh < max(need, TRACK_IN + 0.14):
        raise Overflows("chart %s rows" % name, need=round(max(need, TRACK_IN + 0.14) * len(rows), 3),
                        have=round(box.b - top, 3))
    b = Bullets(name, box, tuple(rows), scale_max, kind)
    b._x0, b._x1 = x0, x1
    for i, r in enumerate(rows):
        cy = top + rh * (i + 0.5)
        h = _need_h(r.label, lw, label_pt, th) + 0.02
        b.marks.append(_text(slide, Box(box.x, cy - h / 2, lw, h), r.label, role="ink", pt=label_pt,
                             name="%s.%d.label" % (name, i + 1), th=th).name)
        b.marks.append(prims.rect(slide, Box(x0, cy - TRACK_IN / 2, x1 - x0, TRACK_IN), fill="card",
                                  name="%s.%d.track" % (name, i + 1), theme=th).name)
        if r.value > 0:
            b.marks.append(prims.rect(slide, Box(x0, cy - TRACK_IN / 2, max(0.02, b.x(r.value) - x0), TRACK_IN),
                                      fill=SUBJECT if i == si else "series-1", name="%s.%d.bar" % (name, i + 1),
                                      theme=th).name)
        if r.target is not None:
            tx = b.x(r.target)
            b.marks.append(prims.hairline(slide, (tx, cy - TRACK_IN / 2 - 0.07), (tx, cy + TRACK_IN / 2 + 0.07),
                                          role="ink-muted", weight_pt=2.0, name="%s.%d.target" % (name, i + 1),
                                          theme=th).name)
        hv = _lh(label_pt, th) + 0.04
        b.marks.append(_text(slide, Box(x1 + 0.12, cy - hv / 2, vw, hv), vals[i], role="ink-deep", pt=label_pt,
                             bold=True, align="right", name="%s.%d.value" % (name, i + 1), th=th).name)
    if want_basis:
        b.marks.append(_draw_basis(slide, box, kind, name, th).name)
    return b


def progress(slide, box: Box, value: float, of: float, *, label: str, kind: str, name: str, fmt="{:,.0f}",
             subject=True, **kw) -> Bullets:
    """One bullet row with no target: a single ratio against its limit."""
    return bullet(slide, box, [Row(label, value)], scale_max=of, kind=kind, name=name,
                  subject=label if subject else None, fmt=fmt, **kw)


# ------------------------------------------------------------------ annotations

ANNOTATIONS = ("callout", "drop", "crossover", "band")


def _at(plot: Plot, at):
    """(x, y) inches of a data point: a category name or index (the subject series' value), (index, value), or (x, y)
    on a scatter."""
    if plot.type in ("scatter", "bubble"):
        if isinstance(at, str):
            i = list(plot.categories).index(at)
            return plot.xy(plot.series["x"][i], plot.series["y"][i])
        return plot.xy(*at)
    if isinstance(at, tuple):
        i, v = at
    else:
        i = at if isinstance(at, int) else list(plot.categories).index(str(at))
        key = (str(plot.subject) if plot.type in ("line", "area") and plot.subject is not None
               else ("value" if "value" in plot.series else next(iter(plot.series))))
        if plot.type == "waterfall":
            v = plot.series["base"][i] + plot.series["value"][i]
        elif plot.type == "stacked":
            v = sum(s[i] for s in plot.series.values())
        else:
            v = plot.series[key][i]
    return plot.point(int(i), float(v))


def _mark_rects(plot: Plot, lines: bool = False) -> list:
    """The boxes of the kit text already drawn for the plot (labels, earlier callouts), and with lines=True of its
    kit lines too (carry lines, drops, leaders, quadrant rules), each widened to 0.04in."""
    out = []
    names = set(plot.marks)
    for sh in plot.slide.shapes:
        if sh.name not in names:
            continue
        x, y = sh.left / 914400, sh.top / 914400
        r, b = x + sh.width / 914400, y + sh.height / 914400
        if sh.has_text_frame and sh.text_frame.text.strip():
            out.append((x, y, r, b))
        elif lines and sh.shape_type is not None and "LINE" in str(sh.shape_type):
            out.append((min(x, r) - 0.02, min(y, b) - 0.02, max(x, r) + 0.02, max(y, b) + 0.02))
    return out


def _data_rects(plot: Plot) -> list:
    """Where the native marks paint: every bar, or a small box round every plotted point."""
    out = []
    t = plot.type
    half = plot.bar_in / 2
    if t in ("bar", "column", "waterfall", "stacked"):
        n = len(plot.categories)
        for i in range(n):
            if t == "waterfall":
                lo, hi = plot.series["base"][i], plot.series["base"][i] + plot.series["value"][i]
            elif t == "stacked":
                lo, hi = 0.0, sum(s[i] for s in plot.series.values())
            else:
                lo, hi = 0.0, plot.series["value"][i]
            c = plot.cat(i)
            a, b = sorted((plot.val(lo), plot.val(hi)))
            out.append((a, c - half, b, c + half) if plot.horizontal else (c - half, a, c + half, b))
    elif t in ("line", "area"):
        for vals in plot.series.values():
            for i, v in enumerate(vals):
                x, y = plot.point(i, v)
                out.append((x - 0.06, y - 0.06, x + 0.06, y + 0.06))
    elif t in ("scatter", "bubble"):
        for x, y in zip(plot.series["x"], plot.series["y"]):
            px, py = plot.xy(x, y)
            out.append((px - 0.07, py - 0.07, px + 0.07, py + 0.07))
    return out


def _value_rect(plot: Plot, at):
    i = at if isinstance(at, int) else (list(plot.categories).index(str(at)) if not isinstance(at, tuple) else at[0])
    for sh in plot.slide.shapes:
        if sh.name == "%s.value.%d" % (plot.name, int(i) + 1):
            x, y = sh.left / 914400, sh.top / 914400
            return (x, y, x + sh.width / 914400, y + sh.height / 914400)
    return None


def annotate(plot: Plot, at, text: str = "", *, kind: str = "callout", side: str = "above", to=None, name=None):
    """The one named point that proves the title, drawn on data coordinates.

    callout    a short bold label (2 to 6 words, one line, no box) beside the point, 0.10in off it
    drop       a dashed grey line from the point to the category axis, and the callout above the point
    crossover  the drop plus a solid accent dot ringed in paper on the point
    band       a tolerance band: accent-wash behind the plot from value `at` to value `to`, named at its left edge
    Returns the shapes drawn. The text never repeats the title and never tells the reader where to look."""
    if kind not in ANNOTATIONS:
        raise ChartError("annotation kind", need=" / ".join(ANNOTATIONS), have=kind)
    th = plot.theme
    s = plot.slide
    plot.notes += 1
    nm = name or "%s.note.%d" % (plot.name, plot.notes)
    out = []
    if kind == "band":
        if plot.horizontal or plot.type in ("ring",):
            raise ChartError("band on %s" % plot.type, need="a vertical value axis", have=plot.type)
        lo, hi = sorted((float(at), float(to)))
        y_hi, y_lo = plot.val(hi), plot.val(lo)
        if plot.type in ("scatter", "bubble"):
            y_hi, y_lo = plot.xy(plot.xmin, hi)[1], plot.xy(plot.xmin, lo)[1]
        rb = (plot.box.x, y_hi, plot.box.r, y_lo)
        for o in _mark_rects(plot):                         # a label straddling the band's edge reads as cut
            inside = o[0] >= rb[0] and o[2] <= rb[2] and o[1] >= rb[1] and o[3] <= rb[3]
            if _overlaps(o, rb, pad=0.0) and not inside:
                raise Overflows("band %s" % nm, need="no label across its edge", have="a label at %.2f, %.2f in"
                                % (o[0], o[1]), hint="move the band, or draw the line with end_labels=False")
        rect = prims.rect(s, Box(plot.box.x, y_hi, plot.box.w, y_lo - y_hi), fill=WASH, name=nm + ".band", theme=th)
        frame = None
        for sh in s.shapes:
            if sh.name == plot.name and getattr(sh, "has_chart", False):
                frame = sh
        if frame is not None:                                # behind the chart, so the marks draw over it
            frame._element.addprevious(rect._element)
        out.append(rect)
        if text:
            w = _tw(text, TICK_PT, th) + 0.04
            h = _lh(TICK_PT, th) + 0.04
            if h > y_lo - y_hi - 0.12:
                raise Overflows("band label %r" % text, need=round(h + 0.12, 3), have=round(y_lo - y_hi, 3),
                                hint="a taller band or no label")
            out.append(_text(s, Box(plot.box.x + 0.08, (y_hi + y_lo) / 2 - h / 2, w, h), text, role="ink-muted",
                             pt=TICK_PT, name=nm + ".label", th=th, background=WASH))
        plot.marks += [o.name for o in out]
        return out
    px, py = _at(plot, at)
    if kind in ("drop", "crossover"):
        if plot.horizontal:
            raise ChartError("%s on a horizontal chart" % kind, need="a vertical value axis", have=plot.type)
        r = DOT_IN / 2 if kind == "crossover" else 0.0
        if plot.box.b - (py + r) > 0.05:
            out.append(prims.connect(s, (px, py + r + 0.02), (px, plot.box.b), head="none", dash="dash",
                                     role="rule-strong", name=nm + ".drop", theme=th))
        if kind == "crossover":
            dot = prims.circle(s, Box(px - DOT_IN / 2, py - DOT_IN / 2, DOT_IN, DOT_IN), fill=SUBJECT, line="paper",
                               name=nm + ".dot", theme=th)
            prims.set_line(dot, "paper", 1.5, theme=th)
            out.append(dot)
    if text:
        words = len(text.split())
        if not 1 <= words <= 8:
            raise ChartError("callout %r" % text, need="2 to 6 words", have=words)
        w = _tw(text, NOTE_PT, th, bold=True) + 0.04
        h = _lh(NOTE_PT, th) + 0.04
        off = 0.10 + (DOT_IN / 2 if kind == "crossover" else 0.05)
        ov = off + (plot.bar_in / 2 if plot.horizontal else 0.0)        # clear of the bar's own thickness
        oh = off + (plot.bar_in / 2 if not plot.horizontal else 0.0)
        spots = {"above": (px - w / 2, py - ov - h), "below": (px - w / 2, py + ov),
                 "right": (px + oh, py - h / 2), "left": (px - oh - w, py - h / 2)}
        if side not in spots:
            raise ChartError("callout side", need=" / ".join(spots), have=side)
        f = plot.frame
        if w > f.w - 2 * PAD:
            raise Overflows("callout %r" % text, need=round(w, 3), have=round(f.w - 2 * PAD, 3))
        taken = _mark_rects(plot, lines=True) + _data_rects(plot)
        spot = None
        for sd in [side] + [k for k in ("above", "right", "below", "left") if k != side]:
            bx_, by_ = spots[sd]
            if plot.horizontal and sd == "right":         # past the bar's own value label
                lab = _value_rect(plot, at)
                if lab is not None:
                    bx_ = max(bx_, lab[2] + 0.12)
            if not plot.horizontal and sd == "above":     # over the column's own value label
                lab = _value_rect(plot, at)
                if lab is not None:
                    by_ = min(by_, lab[1] - 0.06 - h)
            bx_ = min(max(bx_, f.x + PAD), f.r - PAD - w)
            by_ = min(max(by_, f.y + PAD), f.b - PAD - h)
            rect = (bx_, by_, bx_ + w, by_ + h)
            if not any(_overlaps(rect, o) for o in taken):
                spot = rect
                break
        if spot is None:
            raise Overflows("callout %r" % text, need="a free side of the point", have="all four sides taken",
                            hint="fewer words, or a larger chart")
        out.append(_text(s, Box(spot[0], spot[1], w, h), text, role="ink-deep", pt=NOTE_PT, bold=True,
                         align="center", name=nm + ".text", th=th))
    plot.marks += [o.name for o in out]
    return out


# ------------------------------------------------------------------ reading charts back (records, gate P27)

def _cache(el) -> list:
    if el is None:
        return []
    pts = {}
    for pt in el.iter(_C + "pt"):
        v = pt.find(_C + "v")
        pts[int(pt.get("idx", "0"))] = v.text if v is not None else None
    return [pts[k] for k in sorted(pts)]


def _floats(vals) -> list:
    out = []
    for v in vals:
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            out.append(None)
    return out


CHART_TYPES = ("barChart", "bar3DChart", "lineChart", "line3DChart", "areaChart", "area3DChart", "pieChart",
               "pie3DChart", "doughnutChart", "ofPieChart", "scatterChart", "bubbleChart", "radarChart",
               "stockChart", "surfaceChart", "surface3DChart")


def parse(root) -> dict:
    """A chart part's chart groups and series: {"groups": [tag], "series": [{"group", "name", "cat", "val", "x",
    "y", "size"}]}. Values are floats (None for a blank); categories are strings."""
    out = {"groups": [], "series": []}
    pa = root.find(_C + "chart/" + _C + "plotArea")
    if pa is None:
        return out
    for g in pa:
        tag = etree.QName(g).localname
        if tag not in CHART_TYPES:
            continue
        out["groups"].append(tag)
        for ser in g.findall(_C + "ser"):
            tx = ser.find(_C + "tx")
            nm = _cache(tx)
            out["series"].append({
                "group": tag, "name": nm[0] if nm else "",
                "cat": [str(c) for c in _cache(ser.find(_C + "cat"))],
                "val": _floats(_cache(ser.find(_C + "val"))),
                "x": _floats(_cache(ser.find(_C + "xVal"))), "y": _floats(_cache(ser.find(_C + "yVal"))),
                "size": _floats(_cache(ser.find(_C + "bubbleSize")))})
    return out


def frame_kind(descr: str | None) -> str | None:
    m = KIND_RE.search(descr or "")
    return m.group(1) if m else None


def _record(root, descr, label_texts) -> dict:
    d = parse(root)
    rec = {"groups": d["groups"], "kind": frame_kind(descr), "series": [], "labels": dict(sorted(label_texts.items()))}
    for s in d["series"]:
        item = {"name": s["name"]}
        for k in ("cat", "val", "x", "y", "size"):
            if s[k]:
                item[k] = s[k]
        rec["series"].append(item)
    return rec


def chart_frames(slide):
    """[(graphicFrame shape, chart part element)] on a python-pptx slide, in paint order."""
    out = []
    for sh in slide.shapes:
        if getattr(sh, "has_chart", False) and sh.has_chart:
            out.append((sh, sh.chart._chartSpace))
    return out


def records(prs) -> dict:
    """manifest["charts"]: {frame name: {"groups", "kind", "series", "labels"}} for every chart in the deck. labels
    holds the text of every kit shape named <frame name>.* on its slide, so P27 can tell when the chart's data or
    a label changed after the build."""
    out = {}
    for slide in prs.slides:
        texts = {sh.name: sh.text_frame.text for sh in slide.shapes if sh.has_text_frame}
        for sh, root in chart_frames(slide):
            if sh.name in out:
                raise ChartError("chart frame name %r" % sh.name, need="unique across the deck", have="twice")
            descr = sh._element.find(".//" + _P + "cNvPr").get("descr")
            labels = {k: v for k, v in texts.items() if k.startswith(sh.name + ".")}
            out[sh.name] = _record(root, descr, labels)
    return out


__all__ = ["bar", "column", "stacked", "line", "area", "waterfall", "scatter", "ring", "bullet", "progress", "Row",
           "annotate", "records", "parse", "chart_frames", "frame_kind", "check_theme", "nice_ceiling", "Plot",
           "Bullets", "ChartError", "KINDS", "BASIS", "SUBJECT", "OTHERS", "CONTEXT", "NEGATIVE", "WASH",
           "CATEGORICAL_MAX", "CHART_URI", "ANNOTATIONS", "CHART_TYPES"]
