"""Measured fit: the one place the kit and the gates decide how much room text needs.

Lifted from the PMR deck engine's width_of / lines_of / text_height / fits, with its two defects fixed:
  1. it grew sub-floor sizes to the floor silently (Pt(max(FLOOR, size))); here a run under FLOOR
     raises BelowFloor, and nothing is ever grown, shrunk, clamped or truncated;
  2. it measured every run with Arial Regular; here every run is measured with its own cut
     (Arial Bold for bold, Montserrat 600 for SemiBold numerals), looked up by (family, bold, italic).

Widths are advance-width sums from the font files (fontTools hmtx, no kerning: PowerPoint does not
kern unless a run asks for it). Line height is the font's own hhea ascender + descender + lineGap,
or its usWin ascent + descent where that is taller (Windows PowerPoint lays lines from the win
metrics). Both are multiplied by the LibreOffice calibration recorded in kit/assets/metrics.json by
scripts/calibrate_metrics.py; a fitted factor below 1.0 is not applied (the font's design metric is
the floor of the estimate, never a ceiling).

SLACK multiplies every width at wrap time, because PowerPoint sets text wider than LibreOffice
renders it. It is read from this module at call time, so a test can patch it (the builder negative
"SLACK=0.5 must produce a deck that P02 fails").

Paragraph protocol (duck-typed so text.Para / text.Run need not be imported here):
  a paragraph is an MPara, a (text, pt, face) tuple, or any object with .runs and optionally
  .line_spacing (multiple), .line_pt (exact points), .space_before_pt, .space_after_pt, .pt (the
  size of an empty paragraph). A run is an MRun or any object with .text, .pt (or .size) and either
  .face or .family/.font with .bold/.italic. A run with no size is refused: sizes are explicit.
A box is anything with .w and .h in inches, or a (w, h) tuple.
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from .errors import BelowFloor, Overflows, UnknownFace
from .read.textmetrics import token_spans, words

SLACK = 1.15
FLOOR = 8.0

KIT = Path(__file__).resolve().parent.parent
METRICS_JSON = KIT / "assets" / "metrics.json"

_SUPP = "/System/Library/Fonts/Supplemental"
_USER = os.path.expanduser("~/Library/Fonts")

# Business prose used only to estimate words per inch for capacity_words. Fictional and neutral.
CAPACITY_SAMPLE = ("Regional teams review the quarterly plan and agree which accounts move first, "
                   "then the platform team publishes one shared view of demand, supply and margin "
                   "so every market reads the same numbers before the review meeting.")


# --------------------------------------------------------------------------------------- faces

@dataclass(frozen=True)
class Face:
    key: str                     # registry key, e.g. "Arial Bold"
    family: str                  # family as a run names it, e.g. "Arial"
    bold: bool
    italic: bool
    weight: int
    path: str
    fallback: str | None = None  # the face a client machine may substitute; widths and lines take the max


def _arial(key, bold, italic, file):
    return Face(key, "Arial", bold, italic, 700 if bold else 400, f"{_SUPP}/{file}")


def _mont(key, weight):
    return Face(key, "Montserrat", weight >= 700, False, weight, f"{_USER}/Montserrat-{weight}.ttf",
                fallback="Arial Bold")


FACES: dict[str, Face] = {f.key: f for f in (
    _arial("Arial", False, False, "Arial.ttf"),
    _arial("Arial Bold", True, False, "Arial Bold.ttf"),
    _arial("Arial Italic", False, True, "Arial Italic.ttf"),
    _arial("Arial Bold Italic", True, True, "Arial Bold Italic.ttf"),
    _mont("Montserrat", 400),
    _mont("Montserrat Medium", 500),
    _mont("Montserrat SemiBold", 600),
    _mont("Montserrat Bold", 700),
)}

# (family as written in a run, bold, italic) -> face key.
# Montserrat ships no italic cut: PowerPoint obliques the upright, which keeps its advance widths,
# so an italic Montserrat run is measured with the upright face. Bold on a Medium or SemiBold
# family is measured with the Bold cut (synthetic emboldening only ever widens).
_INDEX: dict[tuple[str, bool, bool], str] = {}
for _b in (False, True):
    for _i in (False, True):
        _INDEX[("arial", _b, _i)] = {(0, 0): "Arial", (1, 0): "Arial Bold",
                                     (0, 1): "Arial Italic", (1, 1): "Arial Bold Italic"}[(_b, _i)]
        _INDEX[("montserrat", _b, _i)] = "Montserrat Bold" if _b else "Montserrat"
        _INDEX[("montserrat medium", _b, _i)] = "Montserrat Bold" if _b else "Montserrat Medium"
        _INDEX[("montserrat semibold", _b, _i)] = "Montserrat Bold" if _b else "Montserrat SemiBold"
        _INDEX[("montserrat bold", _b, _i)] = "Montserrat Bold"


def face_for(family: str, bold: bool = False, italic: bool = False) -> Face:
    """Face lookup by (family, bold, italic). An unknown family raises, it is never guessed."""
    key = _INDEX.get(((family or "").strip().lower(), bool(bold), bool(italic)))
    if key is None:
        raise UnknownFace(f"font family {family!r}", need="a measured face", have="no metrics",
                          hint="the kit measures Arial (four cuts) and Montserrat 400/500/600/700; "
                               "resolve theme fonts (+mn-lt) and map other faces before measuring")
    return FACES[key]


def get_face(face) -> Face:
    if isinstance(face, Face):
        return face
    if isinstance(face, str) and face in FACES:
        return FACES[face]
    if isinstance(face, str):
        return face_for(face)
    raise TypeError(f"face must be a Face or a registry key, got {type(face).__name__}")


# ------------------------------------------------------------------------------------- metrics

@dataclass
class _FontMetrics:
    upm: int
    adv: dict[int, int]
    line_factor: float           # line height as a multiple of the point size, before calibration


_FONT_CACHE: dict[str, _FontMetrics] = {}
_CAL: dict | None = None


def _font_metrics(face: Face) -> _FontMetrics:
    m = _FONT_CACHE.get(face.key)
    if m is not None:
        return m
    if not os.path.exists(face.path):
        raise UnknownFace(f"face {face.key!r}", need=face.path, have="missing file",
                          hint="install the font file; the measurer never substitutes a face")
    from fontTools.ttLib import TTFont
    f = TTFont(face.path, lazy=True)
    upm = f["head"].unitsPerEm
    hmtx = f["hmtx"].metrics
    cmap = f.getBestCmap() or {}
    adv = {cp: hmtx[g][0] for cp, g in cmap.items() if g in hmtx}
    hh = f["hhea"]
    os2 = f["OS/2"]
    hhea_total = hh.ascent - hh.descent + hh.lineGap
    win_total = os2.usWinAscent + os2.usWinDescent
    m = _FontMetrics(upm=upm, adv=adv, line_factor=max(hhea_total, win_total) / upm)
    f.close()
    _FONT_CACHE[face.key] = m
    return m


def _calibration() -> dict:
    global _CAL
    if _CAL is None:
        try:
            _CAL = json.loads(METRICS_JSON.read_text())
        except FileNotFoundError:
            _CAL = {"faces": {}, "status": "uncalibrated: kit/assets/metrics.json is missing"}
    return _CAL


def calibration_factor(face: Face, kind: str) -> float:
    """The fitted LibreOffice multiplier for a face ('width' or 'line'), never below 1.0."""
    rec = _calibration().get("faces", {}).get(face.key, {})
    return max(1.0, float(rec.get(kind, 1.0)))


def metrics_info() -> dict:
    """Provenance of the numbers in use, for gate reports."""
    cal = _calibration()
    return {"metrics_json": str(METRICS_JSON), "status": cal.get("status", "calibrated"),
            "calibrated_faces": sorted(cal.get("faces", {}))}


@lru_cache(maxsize=65536)
def _units(text: str, key: str) -> float:
    """Advance-width sum in font units. A character the font lacks counts one full em."""
    m = _font_metrics(FACES[key])
    adv, em = m.adv, m.upm
    total = 0
    for ch in text:
        cp = ord(ch)
        if ch == "\t":
            total += 4 * adv.get(32, em // 4)
        else:
            total += adv.get(cp, em)
    return total / em


def _check_pt(pt) -> float:
    if pt is None:
        raise ValueError("a run needs an explicit point size")
    pt = float(pt)
    if not pt > 0:
        raise ValueError(f"point size must be positive, got {pt}")
    return pt


def _width_one(text: str, pt: float, face: Face) -> float:
    return _units(text, face.key) * pt / 72.0 * calibration_factor(face, "width")


def width_in(text: str, pt: float, face) -> float:
    """Inches one line of text occupies at pt in face, before SLACK. A newline starts a new line;
    the widest line is returned. A dual-metric face returns the wider of itself and its fallback."""
    pt = _check_pt(pt)
    f = get_face(face)
    lines = str(text).split("\n")
    w = max(_width_one(ln, pt, f) for ln in lines)
    if f.fallback:
        fb = FACES[f.fallback]
        w = max(w, max(_width_one(ln, pt, fb) for ln in lines))
    return w


def line_in(pt: float, face, line_spacing: float = 1.0) -> float:
    """Inches one line takes at pt in face: the font's ascender + descender + lineGap (or win
    ascent + descent where taller), times the calibration, times the paragraph's line multiple."""
    pt = _check_pt(pt)
    f = get_face(face)
    factors = [_font_metrics(f).line_factor * calibration_factor(f, "line")]
    if f.fallback:
        fb = FACES[f.fallback]
        factors.append(_font_metrics(fb).line_factor * calibration_factor(fb, "line"))
    return pt * max(factors) * float(line_spacing) / 72.0


# ----------------------------------------------------------------------------- paragraph model

@dataclass(frozen=True)
class MRun:
    text: str
    pt: float
    face: Face


@dataclass(frozen=True)
class MPara:
    runs: tuple[MRun, ...]
    line_spacing: float = 1.0
    line_pt: float | None = None
    space_before_pt: float = 0.0
    space_after_pt: float = 0.0
    pt: float | None = None          # size of an empty paragraph (its endParaRPr)


@dataclass(frozen=True)
class Insets:
    l: float = 0.0
    t: float = 0.0
    r: float = 0.0
    b: float = 0.0


ZERO = Insets()
PPTX_DEFAULT = Insets(0.1, 0.05, 0.1, 0.05)   # PowerPoint's bodyPr defaults, for reading foreign boxes


@dataclass(frozen=True)
class Fit:
    lines: tuple[str, ...]           # every wrapped line, paragraphs flattened in order
    need_in: float
    have_in: float
    ok: bool

    @property
    def n_lines(self) -> int:
        return len(self.lines)

    @property
    def short_in(self) -> float:
        return max(0.0, self.need_in - self.have_in)


def _attr(o, *names, default=None):
    for n in names:
        if hasattr(o, n):
            v = getattr(o, n)
            if v is not None:
                return v
    return default


def _coerce_run(r) -> MRun:
    if isinstance(r, MRun):
        return r
    if isinstance(r, (tuple, list)) and len(r) == 3:
        return MRun(str(r[0]), _check_pt(r[1]), get_face(r[2]))
    text = _attr(r, "text", default="")
    pt = _attr(r, "pt", "size")
    if pt is None:
        raise ValueError(f"run {str(text)[:30]!r} has no explicit size")
    face = _attr(r, "face")
    if face is None:
        face = face_for(_attr(r, "family", "font", default="Arial"),
                        bool(_attr(r, "bold", default=False)), bool(_attr(r, "italic", default=False)))
    return MRun(str(text), _check_pt(pt), get_face(face))


def coerce_para(p) -> MPara:
    """Normalise one paragraph to an MPara (see the protocol in the module docstring)."""
    if isinstance(p, MPara):
        return p
    if isinstance(p, str):
        raise TypeError("a bare string has no size or face; pass (text, pt, face) or an MPara")
    if isinstance(p, tuple) and len(p) == 3 and isinstance(p[0], str):
        return MPara((_coerce_run(p),))
    runs = _attr(p, "runs")
    if runs is None:
        raise TypeError(f"cannot measure a {type(p).__name__}: it has no .runs")
    return MPara(tuple(_coerce_run(r) for r in runs),
                 line_spacing=float(_attr(p, "line_spacing", "line", default=1.0)),
                 line_pt=_attr(p, "line_pt"),
                 space_before_pt=float(_attr(p, "space_before_pt", "space_before", default=0.0)),
                 space_after_pt=float(_attr(p, "space_after_pt", "space_after", default=0.0)),
                 pt=_attr(p, "pt", "size"))


def _paras(paras) -> list[MPara]:
    if isinstance(paras, (MPara, str)) or (isinstance(paras, tuple) and len(paras) == 3
                                          and isinstance(paras[0], str)):
        paras = [paras]
    return [coerce_para(p) for p in paras]


def _box_wh(box) -> tuple[float, float]:
    if isinstance(box, (tuple, list)) and len(box) == 2:
        return float(box[0]), float(box[1])
    return float(box.w), float(box.h)


def _floor_check(para: MPara, floor: float) -> None:
    sizes = [(r.pt, r.text) for r in para.runs] or [(para.pt, "")]
    for pt, text in sizes:
        if pt is not None and pt < floor:
            raise BelowFloor(f"run {text[:40]!r}", need=floor, have=pt,
                             hint=f"set it at {floor:g}pt or larger, or move the text to the notes; "
                                  "the kit never grows a size to the floor")


# ------------------------------------------------------------------------------------ wrapping

# A segment is (text, pt, face). A word is a list of segments with no whitespace inside.

def _seg_w(segs, slack) -> float:
    return sum(width_in(t, pt, f) for t, pt, f in segs if t) * slack


def _tokens(runs: tuple[MRun, ...]):
    """Split runs into hard lines, each a list of ('w'|'s', [segments]) tokens. A word may span
    runs (a two-tone keyword inside a word is still one word)."""
    lines, cur, kind, segs = [], [], None, []

    def flush():
        nonlocal kind, segs
        if segs:
            cur.append((kind, segs))
        kind, segs = None, []

    for r in runs:
        for ch in r.text:
            if ch in "\n\v":
                flush()
                lines.append(cur)
                cur = []
                continue
            k = "s" if ch.isspace() else "w"
            if k != kind:
                flush()
                kind = k
            if segs and segs[-1][1] == r.pt and segs[-1][2] is r.face:
                segs[-1] = (segs[-1][0] + ch, r.pt, r.face)
            else:
                segs.append((ch, r.pt, r.face))
    flush()
    lines.append(cur)
    return lines


def _split_soft(word):
    """Break opportunities inside one word: after a hyphen or a slash, as PowerPoint allows."""
    text = "".join(t for t, _, _ in word)
    cuts = [i + 1 for i, ch in enumerate(text[:-1]) if ch in "-/"]
    if not cuts:
        return [word]
    out, start = [], 0
    for end in cuts + [len(text)]:
        piece, pos = [], 0
        for t, pt, f in word:
            a, b = max(start, pos), min(end, pos + len(t))
            if a < b:
                piece.append((t[a - pos:b - pos], pt, f))
            pos += len(t)
        out.append(piece)
        start = end
    return out


def _text(segs) -> str:
    return "".join(t for t, _, _ in segs)


def _wrap_runs(runs: tuple[MRun, ...], avail: float, slack: float) -> list[tuple[str, float]]:
    """Greedy wrap. Returns [(line text, largest pt on the line)]. Trailing spaces hang (they never
    push a line over). An unbreakable word wider than the box raises Overflows."""
    out: list[tuple[str, float]] = []
    for hard in _tokens(runs):
        line: list = []          # segments on the current line
        line_w = 0.0
        pending: list = []       # the space run before the next word

        def close():
            nonlocal line, line_w
            pts = [pt for _, pt, _ in line] or [max((r.pt for r in runs), default=0.0)]
            out.append((_text(line), max(pts)))
            line, line_w = [], 0.0

        for idx, (kind, segs) in enumerate(hard):
            if kind == "s":
                if idx == 0:     # leading spaces of a hard line occupy room
                    line, line_w = list(segs), _seg_w(segs, slack)
                else:
                    pending = segs
                continue
            pieces = _split_soft(segs) if _seg_w(segs, slack) > avail + 1e-9 else [segs]
            for j, piece in enumerate(pieces):
                w = _seg_w(piece, slack)
                if w > avail + 1e-9:
                    raise Overflows(f"word {_text(segs)!r}", need=round(w, 3), have=round(avail, 3),
                                    hint="widen the box or shorten the word; a word never breaks "
                                         "mid-letter")
                sp = pending if (line and j == 0) else []
                sp_w = _seg_w(sp, slack)
                if line and line_w + sp_w + w > avail + 1e-9:
                    close()
                    sp, sp_w = [], 0.0
                line.extend(sp)
                line.extend(piece)
                line_w += sp_w + w
            pending = []
        close()
    return out


def wrap(text: str, pt: float, face, width_in: float, *, slack: float | None = None,
         floor: float | None = None) -> list[str]:
    """Lines text wraps to at pt in face inside width_in inches, widths taken at SLACK.
    Raises BelowFloor under the floor and Overflows on an unbreakable word wider than the box."""
    para = MPara((MRun(str(text), _check_pt(pt), get_face(face)),))
    _floor_check(para, FLOOR if floor is None else floor)
    return [t for t, _ in _wrap_runs(para.runs, float(width_in), SLACK if slack is None else slack)]


# -------------------------------------------------------------------------------------- height

def _layout(paras: list[MPara], width: float, slack: float, floor: float):
    lines: list[str] = []
    need = 0.0
    for p in paras:
        _floor_check(p, floor)
        if p.runs and any(r.text for r in p.runs):
            wrapped = _wrap_runs(p.runs, width, slack)
            faces = {r.face.key: r.face for r in p.runs}
            big = max(r.pt for r in p.runs)
        else:
            pt = p.pt if p.pt is not None else (max(r.pt for r in p.runs) if p.runs else None)
            if pt is None:
                raise ValueError("an empty paragraph needs a size (MPara.pt)")
            wrapped = [("", pt)]
            faces = {r.face.key: r.face for r in p.runs} or {"Arial": FACES["Arial"]}
            big = pt
        for text, pt in wrapped:
            if p.line_pt is not None:
                lh = float(p.line_pt) / 72.0
            else:
                lh = max(line_in(pt or big, f, p.line_spacing) for f in faces.values())
            need += lh
            lines.append(text)
        need += (p.space_before_pt + p.space_after_pt) / 72.0
    return lines, need


def need_height(paras, width_in: float, insets: Insets = ZERO, *, slack: float | None = None,
                floor: float | None = None) -> float:
    """Inches of height the paragraphs need in a box width_in wide, insets included.
    Space before and after count on every paragraph, the first and last included."""
    avail = float(width_in) - insets.l - insets.r
    _, need = _layout(_paras(paras), avail, SLACK if slack is None else slack,
                      FLOOR if floor is None else floor)
    return need + insets.t + insets.b


def fits(paras, box, insets: Insets = ZERO, *, slack: float | None = None,
         floor: float | None = None) -> Fit:
    """Measure paragraphs against a box. ok is strict (need <= have); the gate adds its tolerance."""
    w, h = _box_wh(box)
    lines, need = _layout(_paras(paras), w - insets.l - insets.r, SLACK if slack is None else slack,
                          FLOOR if floor is None else floor)
    need += insets.t + insets.b
    return Fit(tuple(lines), round(need, 4), round(h, 4), need <= h + 1e-9)


def _keep_words(paras: list[MPara], k: int) -> list[MPara]:
    """The paragraphs cut down to their first k counted words (read.textmetrics tokenizer)."""
    out = []
    for p in paras:
        text = "".join(r.text for r in p.runs)
        spans = token_spans(text)
        if k >= len(spans):
            out.append(p)
            k -= len(spans)
            continue
        end = spans[k - 1][1] if k > 0 else 0
        runs, pos = [], 0
        for r in p.runs:
            a, b = pos, pos + len(r.text)
            if a < end:
                runs.append(MRun(r.text[:end - a], r.pt, r.face))
            pos = b
        out.append(MPara(tuple(runs), p.line_spacing, p.line_pt, p.space_before_pt, p.space_after_pt,
                         p.pt or max((r.pt for r in p.runs), default=None)))
        break
    return out


def require_fit(what: str, paras, box, insets: Insets = ZERO, *, slack: float | None = None,
                floor: float | None = None) -> Fit:
    """fits() or raise Overflows(what, need, have, hint). The hint names how many words to cut,
    found by re-measuring, not estimated."""
    ps = _paras(paras)
    try:
        f = fits(ps, box, insets, slack=slack, floor=floor)
    except Overflows as e:
        raise Overflows(f"{what}: {e.what}", need=e.need, have=e.have, hint=e.hint) from None
    if f.ok:
        return f
    total = sum(words("".join(r.text for r in p.runs)) for p in ps)
    lo, hi = 0, total            # largest k in [0, total) whose first-k-words cut fits
    best = None
    while lo <= hi:
        mid = (lo + hi) // 2
        try:
            ok = fits(_keep_words(ps, mid), box, insets, slack=slack, floor=floor).ok
        except Overflows:
            ok = False
        if ok:
            best, lo = mid, mid + 1
        else:
            hi = mid - 1
    head = " ".join("".join(r.text for r in ps[0].runs).split()[:6]) if ps and ps[0].runs else ""
    if best is None or best == 0:
        hint = (f"not even one line fits; make the box {f.short_in:.2f}in taller or use a smaller "
                f"ramp step (content starts {head!r})")
    else:
        hint = (f"cut {total - best} of {total} words, or give it {f.short_in:.2f}in more height "
                f"(content starts {head!r})")
    raise Overflows(what, need=f.need_in, have=f.have_in, hint=hint)


# ------------------------------------------------------------------------------------ capacity

def capacity_words(box, pt: float, face, insets: Insets = ZERO, line_spacing: float = 1.0, *,
                   slack: float | None = None, floor: float | None = None) -> int:
    """Estimate of how many words of ordinary prose a box holds at pt in face. An estimate for
    planning (budgets, device slot capacity), never a substitute for require_fit. Monotonic in box
    width and height."""
    pt = _check_pt(pt)
    fl = FLOOR if floor is None else floor
    if pt < fl:
        raise BelowFloor(f"capacity at {pt:g}pt", need=fl, have=pt, hint="plan capacity at the floor or above")
    s = SLACK if slack is None else slack
    w, h = _box_wh(box)
    aw, ah = w - insets.l - insets.r, h - insets.t - insets.b
    if aw <= 0 or ah <= 0:
        return 0
    per_word = width_in(CAPACITY_SAMPLE, pt, face) * s / words(CAPACITY_SAMPLE)
    n_lines = math.floor(ah / line_in(pt, face, line_spacing) + 1e-9)
    per_line = max(0.0, aw / per_word - 0.5)      # half a word lost to the ragged edge per line
    return max(0, math.floor(n_lines * per_line))


__all__ = ["SLACK", "FLOOR", "Face", "FACES", "face_for", "get_face", "width_in", "line_in", "wrap",
           "need_height", "fits", "require_fit", "capacity_words", "Fit", "Insets", "ZERO",
           "PPTX_DEFAULT", "MRun", "MPara", "coerce_para", "calibration_factor", "metrics_info"]
