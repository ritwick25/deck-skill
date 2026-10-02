"""Text on glass: runs, paragraphs, measured text boxes, the two-tone action title, and re-texting.

Lifted from pptxlib `textbox`, the PMR deck engine's `text` / `action_title`, and clone_le_slide
`relabel_text_frame`, with these changes:
  * a run below 8.0pt raises BelowFloor; nothing is ever grown to the floor (PMR clamped silently);
  * every run carries an explicit size, an explicit typeface, kern 0 and a role colour written as a
    `schemeClr` from the theme, so a client cut is a theme swap and nothing inherits by accident;
  * every paragraph writes its own alignment, level, margins, line spacing, space before and after,
    and its bullet (or buNone), so no master or lstStyle value leaks in;
  * bodyPr is noAutofit, wrap square, explicit insets: no spAutoFit growth, no fontScale shrink;
  * textbox() measures with deckkit.measure BEFORE it creates the shape, and raises Overflows;
  * title() is two-tone (DECISIONS ruling 6): one to three keywords in the brand text role, the rest
    ink-deep. PMR's subtitle, accent_rule (the title underline), chip row and page furniture are gone;
  * retext() writes runs only, never paragraph-level text, and refuses rather than dropping content.

Colour words. A run names a TEXT role. The brand colour on text is `accent-ink` (the role each theme
solves to clear 4.5:1); `accent` is a fill role, and a run that names it is refused with that hint.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from lxml import etree

from . import measure, ooxml
from .canvas import EMU_PER_IN, FLOOR, Box, Canvas, canvas_of
from .errors import BelowFloor, Capacity, DeckkitError, OverBudget, Overflows, ThemeInvariant
from .read.ns import NS, local
from .read.textmetrics import words
from .theme import TEXT_ROLES

_A = "{%s}" % NS["a"]

# Roles a run may be set in. paper is white text on an ink-strong header pill (a contrast pair).
RUN_ROLES = tuple(TEXT_ROLES) + ("paper",)
TITLE_ROLE = "ink-deep"
KEYWORD_ROLE = "accent-ink"
TITLE_MAX_WORDS = 14
TITLE_MAX_KEYWORDS = 3
# The P02 fit tolerance (engineering.md (e)), in WIDE inches, scaled by canvas.k. Used only where a
# canvas slot is sized to the line it holds (the WIDE title box is one measured 21pt bold line).
FIT_TOL_IN = 0.035
BULLET_IN = 0.18       # hanging indent of a bulleted paragraph
LEVEL_IN = 0.25        # extra left margin per outline level

_ALIGN = {"left": "l", "l": "l", "center": "ctr", "centre": "ctr", "ctr": "ctr", "right": "r", "r": "r",
          "justify": "just", "just": "just"}
_ANCHOR = {"top": "t", "t": "t", "middle": "ctr", "ctr": "ctr", "bottom": "b", "b": "b"}
_BREAKS = re.compile(r"[\n\v]")
# Montserrat weights are separate families to PowerPoint; Arial cuts are one family with b/i flags.
_MONT_FAMILY = {400: "Montserrat", 500: "Montserrat Medium", 600: "Montserrat SemiBold", 700: "Montserrat"}


def _emu(inches: float) -> int:
    return int(round(float(inches) * EMU_PER_IN))


# ------------------------------------------------------------------------------- content model

@dataclass(frozen=True)
class Run:
    """One run. size None takes the size given to write()/textbox(); face None takes the theme's
    minor font (the title takes the major font). face is a family name ("Arial", "Montserrat
    SemiBold") or a measure.Face."""
    text: str
    role: str = "ink"
    bold: bool = False
    italic: bool = False
    size: float | None = None
    face: object = None


@dataclass(frozen=True)
class Para:
    """One paragraph. runs is a list of Run (a bare string is one ink run). Spacing in points,
    line_spacing a multiple of single. bullet is the bullet character, or None for buNone."""
    runs: tuple = ()
    align: str = "left"
    space_before: float = 0.0
    space_after: float = 0.0
    line_spacing: float = 1.0
    level: int = 0
    bullet: str | None = None

    def __post_init__(self):
        r = self.runs
        if isinstance(r, (str, Run)):
            r = [r]
        object.__setattr__(self, "runs", tuple(Run(x) if isinstance(x, str) else x for x in r))
        for x in self.runs:
            if not isinstance(x, Run):
                raise TypeError("Para runs must be Run or str, got %s" % type(x).__name__)
        if self.align not in _ALIGN:
            raise ValueError("align %r: use one of %s" % (self.align, ", ".join(sorted(set(_ALIGN)))))
        if not (0 <= int(self.level) <= 8):
            raise ValueError("level %r: 0 to 8" % (self.level,))
        if self.line_spacing <= 0 or self.space_before < 0 or self.space_after < 0:
            raise ValueError("line_spacing must be > 0 and spacing >= 0")

    @property
    def margin_in(self) -> float:
        """Left margin of the text (bullet hangs into it): what measurement subtracts from the width."""
        return self.level * LEVEL_IN + (BULLET_IN if self.bullet else 0.0)


def _paras(paras) -> list[Para]:
    if isinstance(paras, (str, Run, Para)):
        paras = [paras]
    out = []
    for p in paras:
        out.append(p if isinstance(p, Para) else Para(p))
    if not out:
        raise ValueError("no paragraphs to write")
    return out


# ------------------------------------------------------------------------------- resolution

@dataclass(frozen=True)
class _RRun:            # a run with everything decided
    text: str
    role: str
    bold: bool
    italic: bool
    pt: float
    typeface: str
    face: measure.Face


def _typeface(face) -> tuple[str, bool]:
    """(typeface to write, bold implied by the face) for a measure.Face."""
    if face.family == "Montserrat":
        return _MONT_FAMILY.get(face.weight, "Montserrat"), face.weight >= 700
    return face.family, face.bold


def _resolve(run: Run, theme, size, default_face: str) -> _RRun:
    pt = run.size if run.size is not None else size
    if pt is None:
        raise ValueError("run %r has no size: give the Run a size or pass size= to write/textbox"
                         % run.text[:40])
    pt = float(pt)
    if pt < FLOOR:
        raise BelowFloor("run %r" % run.text[:40], need=FLOOR, have=pt,
                         hint="set it at %gpt or larger, or move the text to the notes; the kit never "
                              "grows a size to the floor" % FLOOR)
    if run.role not in RUN_ROLES:
        hint = ("accent is a fill role; set brand-colour text in accent-ink" if run.role == "accent"
                else "text roles are " + ", ".join(RUN_ROLES))
        raise ThemeInvariant("run %r role" % run.text[:40], need="a text role", have=run.role, hint=hint)
    theme.hex(run.role)                      # an unknown role raises here, before any XML is touched
    bold = bool(run.bold)
    f = run.face if run.face is not None else default_face
    if isinstance(f, measure.Face):
        typeface, implied = _typeface(f)
        bold = bold or implied
    else:
        typeface = str(f)
    mface = measure.face_for(typeface, bold, bool(run.italic))       # UnknownFace for an unmeasured family
    return _RRun(run.text, run.role, bold, bool(run.italic), pt, typeface, mface)


def _mpara(p: Para, rruns: list[_RRun]) -> measure.MPara:
    mruns = tuple(measure.MRun(r.text, r.pt, r.face) for r in rruns)
    return measure.MPara(mruns, line_spacing=float(p.line_spacing), space_before_pt=float(p.space_before),
                         space_after_pt=float(p.space_after), pt=max(r.pt for r in rruns))


def _prepare(paras, theme, size, default_face):
    """[(Para, [_RRun], MPara)] with every refusal raised before anything is written."""
    out = []
    for p in _paras(paras):
        runs = p.runs or (Run(""),)
        rr = [_resolve(r, theme, size, default_face) for r in runs]
        out.append((p, rr, _mpara(p, rr)))
    return out


def _default_face(theme, which: str = "minor") -> str:
    return (getattr(theme, "fonts", None) or {}).get(which) or "Arial"


# ------------------------------------------------------------------------------- measuring

def _measure(prepped, box, insets) -> measure.Fit:
    """Fit of prepared paragraphs in box. Paragraphs with no left margin go straight to
    measure.require_fit (whose hint names the words to cut). With margins, each paragraph is
    measured at its own width."""
    if all(p.margin_in == 0 for p, _, _ in prepped):
        return measure.fits([m for _, _, m in prepped], box, insets)
    w, h = (box.w, box.h)
    need, lines = insets.t + insets.b, []
    for p, _, m in prepped:
        f = measure.fits([m], (w - insets.l - insets.r - p.margin_in, 1e9))
        need += f.need_in
        lines.extend(f.lines)
    return measure.Fit(tuple(lines), round(need, 4), round(h, 4), need <= h + 1e-9)


def check_fit(what: str, paras, box, theme, insets=measure.ZERO, *, size=None, face=None) -> measure.Fit:
    """require_fit for kit paragraphs: raises Overflows(what, need, have, hint) or returns the Fit."""
    return _require(what, _prepare(paras, theme, size, face or _default_face(theme)), box, insets)


def _require(what, prepped, box, insets) -> measure.Fit:
    if all(p.margin_in == 0 for p, _, _ in prepped):
        return measure.require_fit(what, [m for _, _, m in prepped], box, insets)
    f = _measure(prepped, box, insets)
    if not f.ok:
        raise Overflows(what, need=f.need_in, have=f.have_in,
                        hint="give it %.2fin more height, cut words, or drop a bullet level (%d lines at "
                             "the indented width)" % (f.short_in, f.n_lines))
    return f


# ------------------------------------------------------------------------------- writing XML

def _rpr(tag: str, r: _RRun, theme):
    el = etree.Element(_A + tag)
    el.set("lang", "en-US")
    el.set("sz", str(int(round(r.pt * 100))))
    el.set("b", "1" if r.bold else "0")
    el.set("i", "1" if r.italic else "0")
    el.set("kern", "0")
    el.set("dirty", "0")
    fill = etree.SubElement(el, _A + "solidFill")
    fill.append(theme.spec(r.role))
    etree.SubElement(el, _A + "latin").set("typeface", r.typeface)
    etree.SubElement(el, _A + "ea").set("typeface", r.typeface)
    etree.SubElement(el, _A + "cs").set("typeface", r.typeface)
    return el


def _ppr(p: Para):
    el = etree.Element(_A + "pPr")
    marl = p.margin_in
    el.set("marL", str(_emu(marl)))
    el.set("indent", str(-_emu(BULLET_IN) if p.bullet else 0))
    el.set("lvl", str(int(p.level)))
    el.set("algn", _ALIGN[p.align])
    lsp = etree.SubElement(el, _A + "lnSpc")
    etree.SubElement(lsp, _A + "spcPct").set("val", str(int(round(p.line_spacing * 100000))))
    for tag, v in (("spcBef", p.space_before), ("spcAft", p.space_after)):
        etree.SubElement(etree.SubElement(el, _A + tag), _A + "spcPts").set("val", str(int(round(v * 100))))
    if p.bullet:
        # the bullet follows its first run's colour, size and face (no value to drift or to fail
        # the strict ST_TextBulletSizePercent pattern the validator applies to buSzPct)
        for tag in ("buClrTx", "buSzTx", "buFontTx"):
            etree.SubElement(el, _A + tag)
        etree.SubElement(el, _A + "buChar").set("char", p.bullet)
    else:
        etree.SubElement(el, _A + "buNone")
    return el


def _para_el(p: Para, rruns: list[_RRun], theme):
    pe = etree.Element(_A + "p")
    pe.append(_ppr(p))
    for r in rruns:
        parts = _BREAKS.split(r.text)
        for i, part in enumerate(parts):
            if i:
                br = etree.SubElement(pe, _A + "br")
                br.append(_rpr("rPr", r, theme))
            if part:
                re_ = etree.SubElement(pe, _A + "r")
                re_.append(_rpr("rPr", r, theme))
                etree.SubElement(re_, _A + "t").text = part
    pe.append(_rpr("endParaRPr", rruns[-1], theme))
    return pe


def _write_prepped(text_frame, prepped, theme, insets, anchor):
    tx = ooxml._el(text_frame)
    if local(tx) != "txBody":
        raise TypeError("write() needs a text frame (or a txBody element), got %s" % local(tx))
    body = ooxml.no_autofit(tx)
    for attr, v in (("lIns", insets.l), ("tIns", insets.t), ("rIns", insets.r), ("bIns", insets.b)):
        body.set(attr, str(_emu(v)))
    body.set("anchor", _ANCHOR[anchor])
    body.set("rtlCol", "0")
    for old in tx.findall(_A + "p"):
        tx.remove(old)
    for p, rr, _ in prepped:
        tx.append(_para_el(p, rr, theme))
    return text_frame


def write(text_frame, paras, theme, insets=measure.ZERO, *, size=None, face=None, anchor="top"):
    """Replace every paragraph of text_frame with paras. Each run gets an explicit size, typeface,
    kern 0 and role colour; each paragraph its own spacing and bullet; bodyPr noAutofit, wrap
    square, explicit insets. Raises BelowFloor below 8.0pt. Does not measure (textbox() does)."""
    if anchor not in _ANCHOR:
        raise ValueError("anchor %r: top, middle or bottom" % (anchor,))
    prepped = _prepare(paras, theme, size, face or _default_face(theme))
    return _write_prepped(text_frame, prepped, theme, insets, anchor)


def _add_box(slide, box: Box, name: str):
    if not name or not str(name).strip():
        raise ValueError("every kit shape is named; pass name=")
    sh = slide.shapes.add_textbox(*box.emu)
    sh.name = str(name)
    ooxml.finish(sh)
    return sh


def textbox(slide, box: Box, paras, name: str, theme, require_fit: bool = True, *,
            insets=measure.ZERO, size=None, face=None, anchor="top"):
    """A named text box at box, measured BEFORE it is created: Overflows (with a cut-words hint)
    when require_fit and the text needs more height than the box offers."""
    if anchor not in _ANCHOR:
        raise ValueError("anchor %r: top, middle or bottom" % (anchor,))
    prepped = _prepare(paras, theme, size, face or _default_face(theme))
    if require_fit:
        _require(name, prepped, box, insets)
    sh = _add_box(slide, box, name)
    _write_prepped(sh.text_frame, prepped, theme, insets, anchor)
    return sh


# ------------------------------------------------------------------------------- the action title

def _keyword_spans(text: str, keywords) -> list[tuple[int, int]]:
    kws = list(keywords or ())
    if len(kws) > TITLE_MAX_KEYWORDS:
        raise Capacity("title keywords", need=len(kws), have=TITLE_MAX_KEYWORDS,
                       hint="one to three keywords of the claim carry the brand colour; drop %d"
                            % (len(kws) - TITLE_MAX_KEYWORDS))
    spans = []
    for k in kws:
        if not isinstance(k, str) or not k.strip() or k != k.strip():
            raise DeckkitError("title keyword %r" % (k,), need="a non-empty phrase without edge spaces",
                               have=repr(k))
        found = None
        for m in re.finditer(re.escape(k), text):
            a, b = m.span()
            if (a == 0 or not text[a - 1].isalnum()) and (b == len(text) or not text[b].isalnum()):
                found = (a, b)
                break
        if found is None:
            raise DeckkitError("title keyword %r" % k, need="an exact whole-word substring of the title",
                               have=text, hint="keywords are copied from the title verbatim, case included")
        for a, b in spans:
            if found[0] < b and a < found[1]:
                raise DeckkitError("title keyword %r" % k, need="keywords that do not overlap",
                                   have=text[a:b])
        spans.append(found)
    return sorted(spans)


def title_runs(text: str, keywords=()) -> list[Run]:
    """The two-tone run split: keyword spans in accent-ink, everything between in ink-deep, bold."""
    spans = _keyword_spans(text, keywords)
    runs, pos = [], 0
    for a, b in spans:
        if a > pos:
            runs.append(Run(text[pos:a], role=TITLE_ROLE, bold=True))
        runs.append(Run(text[a:b], role=KEYWORD_ROLE, bold=True))
        pos = b
    if pos < len(text):
        runs.append(Run(text[pos:], role=TITLE_ROLE, bold=True))
    return runs


def _canvas_for(slide) -> Canvas:
    prs = slide.part.package.presentation_part.presentation
    return canvas_of(prs)


def title(slide, text: str, keywords=(), canvas: Canvas | None = None, theme=None, *, name: str = "title"):
    """The action title in the canvas title box at the canvas title size, bold, in the theme's major
    font. keywords (0 to 3 exact whole-word substrings) are set in accent-ink, the rest in ink-deep.
    Raises Capacity for more than three keywords, OverBudget past 14 words, Overflows when the title
    wraps past canvas.title_max_lines or needs more height than the title box (P02 tolerance)."""
    if theme is None:
        raise TypeError("title() needs theme=")
    canvas = canvas or _canvas_for(slide)
    text = str(text or "")
    if not text.strip() or text != text.strip() or _BREAKS.search(text):
        raise DeckkitError("title", need="one line of text, no edge spaces or breaks", have=repr(text[:60]))
    n = words(text)
    if n > TITLE_MAX_WORDS:
        raise OverBudget("title", need=n, have=TITLE_MAX_WORDS,
                         hint="an action title is one claim; cut %d words" % (n - TITLE_MAX_WORDS))
    para = Para(title_runs(text, keywords))
    major = _default_face(theme, "major")
    prepped = _prepare([para], theme, canvas.title_pt, major)
    tb = canvas.title_box
    fit = measure.fits([prepped[0][2]], (tb.w, 1e9))
    if fit.n_lines > canvas.title_max_lines:
        raise Overflows("title", need=fit.n_lines, have=canvas.title_max_lines, unit="lines",
                        hint="the %s canvas holds %d title line(s) at %gpt; cut words (the title wraps "
                             "after %r)" % (canvas.name, canvas.title_max_lines, canvas.title_pt,
                                            fit.lines[0][-40:]))
    tol = FIT_TOL_IN * canvas.k
    if fit.need_in > tb.h + tol:
        raise Overflows("title", need=fit.need_in, have=tb.h,
                        hint="%d line(s) at %gpt need more than the %s title box" % (
                            fit.n_lines, canvas.title_pt, canvas.name))
    sh = _add_box(slide, tb, name)
    _write_prepped(sh.text_frame, prepped, theme, measure.ZERO, "top")
    return sh


# ------------------------------------------------------------------------------- retext

def _runs_of(p):
    return [c for c in p if local(c) == "r"]


def _sz_check(rpr, text):
    if rpr is None:
        return
    sz = rpr.get("sz")
    if sz is not None and int(sz) < FLOOR * 100:
        raise BelowFloor("run %r" % text[:40], need=FLOOR, have=int(sz) / 100.0,
                         hint="the source run is below the floor; resize it before re-texting")


def retext(shape, chunks):
    """Replace the text of an existing shape run by run, keeping every run's formatting.

    chunks has one entry per paragraph, in order:
      str          the paragraph's first run takes the text, its other runs and breaks are removed;
                   a paragraph with no run gets one formatted from its endParaRPr
      list of str  one string per existing run, same count (a two-tone line keeps its tones)
      None         the paragraph is removed
    The paragraph count must match: content is never silently dropped and slots never silently
    blanked. Fields (a:fld) are refused. Returns the shape.
    """
    el = ooxml._el(shape)
    tx = el if local(el) == "txBody" else next(
        (c for c in el.iter() if isinstance(c.tag, str) and local(c) == "txBody"), None)
    if tx is None:
        raise DeckkitError("retext", need="a shape with a text body", have=getattr(shape, "name", shape))
    what = getattr(shape, "name", "shape")
    paras = tx.findall(_A + "p")
    chunks = list(chunks)
    if len(chunks) != len(paras):
        raise Capacity("retext %s paragraphs" % what, need=len(chunks), have=len(paras),
                       hint="pass one chunk per paragraph; None removes a paragraph")
    plan = []
    for i, (p, ch) in enumerate(zip(paras, chunks)):
        if any(local(c) == "fld" for c in p):
            raise DeckkitError("retext %s paragraph %d" % (what, i), need="runs only", have="a field (a:fld)",
                               hint="fields (slide numbers, dates) are not re-texted")
        runs = _runs_of(p)
        if ch is None:
            plan.append(("drop", p, None))
            continue
        if isinstance(ch, str):
            if _BREAKS.search(ch):
                raise DeckkitError("retext %s paragraph %d" % (what, i), need="no line breaks", have=repr(ch[:40]),
                                   hint="one chunk per paragraph; split lines into paragraphs")
            src = runs[0].find(_A + "rPr") if runs else p.find(_A + "endParaRPr")
            if ch:
                _sz_check(src, ch)
            plan.append(("one", p, ch))
            continue
        ch = list(ch)
        if len(ch) != len(runs):
            raise Capacity("retext %s paragraph %d runs" % (what, i), need=len(ch), have=len(runs),
                           hint="a list chunk maps one string to each existing run")
        for r, s in zip(runs, ch):
            if not isinstance(s, str) or _BREAKS.search(s):
                raise DeckkitError("retext %s paragraph %d" % (what, i), need="strings without breaks",
                                   have=repr(s))
            if s:
                _sz_check(r.find(_A + "rPr"), s)
        plan.append(("many", p, ch))
    if all(kind == "drop" for kind, _, _ in plan):
        raise DeckkitError("retext %s" % what, need="at least one paragraph kept", have="every chunk None")
    for kind, p, ch in plan:                     # everything validated: now mutate
        if kind == "drop":
            tx.remove(p)
        elif kind == "one":
            runs = _runs_of(p)
            if not runs and ch:
                end = p.find(_A + "endParaRPr")
                r = etree.Element(_A + "r")
                if end is not None:
                    rpr = etree.fromstring(etree.tostring(end))
                    rpr.tag = _A + "rPr"
                    r.append(rpr)
                etree.SubElement(r, _A + "t").text = ch
                if end is not None:
                    end.addprevious(r)
                else:
                    p.append(r)
            elif runs:
                runs[0].find(_A + "t").text = ch
                for c in [c for c in p if local(c) == "br"] + runs[1:]:
                    p.remove(c)
                if not ch:
                    p.remove(runs[0])
        else:
            for r, s in zip(_runs_of(p), ch):
                r.find(_A + "t").text = s
            for r in _runs_of(p):
                if not r.find(_A + "t").text:
                    p.remove(r)
    return shape


__all__ = ["Run", "Para", "RUN_ROLES", "TITLE_MAX_WORDS", "TITLE_MAX_KEYWORDS", "write", "textbox",
           "check_fit", "title", "title_runs", "retext"]
