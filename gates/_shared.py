"""Shared plumbing for the static pptx gates (P01 to P23). No assertion lives here.

Everything a gate reads comes through deckkit: geometry, colour, type inheritance and word counting from
deckkit.read (read_slide, words), absolute boxes from deckkit.geom.iter_abs, fit from deckkit.measure,
archetype tags from deckkit.tag. This module only loads context, caches the reads, and reports.

Context (Ctx), loaded once per deck:
  * deck.json in the DECK'S OWN FOLDER, never a parent (the per-folder authority). Its "overrides" map a
    rule key to the source that grants it ({"P09:subtitle": "DESIGN.md#R36"}); an override without a
    source is refused. The aliases R-NOSUB and R-NOFOOT map to P09:subtitle and P09:foot. "budgets",
    "series", "client", "theme", "build", "notes_deck" and "media_allow" are read by the gates that
    need them, inside that folder and nowhere else.
  * <stem>.manifest.json beside the deck (written by deckkit.package.save).
  * the theme: deck.json "theme" (a path, relative to the deck folder), else the manifest's theme name
    under themes/.
  * refs_dir (P18) and the fingerprints file (P17), overridable per run so a negative can point a gate
    at an empty rules file or a test-registered image hash without touching the real ones.

A missing input raises InputMissing; the gate exits 2 and the runner counts it as FAIL. A missing input
never reads as a pass.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import traceback
from dataclasses import asdict, dataclass, field
from pathlib import Path

GATES_DIR = Path(__file__).resolve().parent
SKILL = GATES_DIR.parent
if str(SKILL / "kit") not in sys.path:
    sys.path.insert(0, str(SKILL / "kit"))

from deckkit import geom, measure  # noqa: E402
from deckkit import tag as tagmod  # noqa: E402
from deckkit.canvas import PROFILES  # noqa: E402
from deckkit.errors import DeckkitError, UnknownFace  # noqa: E402
from deckkit.read import open_deck, read_slide, words  # noqa: E402
from deckkit.read.ns import A, P, local  # noqa: E402
from deckkit.read.zones import contains, is_rect_like  # noqa: E402

DEFAULT_REFS = SKILL / "devices" / "refs"
DEFAULT_FINGERPRINTS = Path(os.path.expanduser("~/.claude/hooks/fingerprints.json"))
ARCHETYPES_JSON = SKILL / "archetypes" / "archetypes.json"
FAMILIES_JSON = GATES_DIR / "families.json"
DEVICES_JSON = SKILL / "devices" / "devices.json"
THEMES = SKILL / "themes"
ALIASES = {"R-NOSUB": "P09:subtitle", "R-NOFOOT": "P09:foot"}
CEILING = 250                       # words per slide, hard (ruling 2)
CARD_ROLES = ("paper", "card", "accent-tint", "accent-wash")
FRAME_FAMILY = "Frame"

FAIL, ADVISORY, NOTE = "fail", "advisory", "note"


class InputMissing(Exception):
    """A gate input is missing or malformed. Exit 2, counted as FAIL."""


@dataclass
class Finding:
    gate: str
    level: str
    slide: int | None
    where: str
    msg: str

    def line(self) -> str:
        loc = ("s%-3d" % self.slide) if self.slide is not None else "    "
        lvl = {"fail": "FAIL", "advisory": "adv ", "note": "note"}[self.level]
        w = (" %s:" % self.where) if self.where else ""
        return "  %s %s%s %s" % (lvl, loc, w, self.msg)


# ------------------------------------------------------------------ context

def _load_json(p: Path, what: str):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise InputMissing("%s is missing: %s" % (what, p)) from None
    except ValueError as e:
        raise InputMissing("%s is not valid JSON (%s): %s" % (what, e, p)) from None


class Ctx:
    """Everything a gate needs about one deck, loaded lazily and cached."""

    def __init__(self, deck_path, *, refs_dir=None, fingerprints=None, theme=None, extra: dict | None = None):
        self.deck_path = Path(deck_path).resolve()
        if not self.deck_path.is_file():
            raise InputMissing("deck not found: %s" % self.deck_path)
        self.folder = self.deck_path.parent
        self.extra = dict(extra or {})
        self._refs = refs_dir or self.extra.get("refs_dir")
        self._fp = fingerprints or self.extra.get("fingerprints")
        self._theme_arg = theme or self.extra.get("theme")
        self._cache: dict = {}

    # -- files beside the deck
    @property
    def deck_json(self) -> dict:
        if "deck_json" not in self._cache:
            p = self.folder / "deck.json"
            self._cache["deck_json"] = _load_json(p, "deck.json") if p.is_file() else {}
        return self._cache["deck_json"]

    @property
    def manifest(self) -> dict | None:
        if "manifest" not in self._cache:
            p = self.deck_path.with_name(self.deck_path.stem + ".manifest.json")
            self._cache["manifest"] = _load_json(p, "manifest") if p.is_file() else None
        return self._cache["manifest"]

    @property
    def overrides(self) -> dict:
        if "overrides" not in self._cache:
            raw = self.deck_json.get("overrides") or {}
            if not isinstance(raw, dict):
                raise InputMissing("deck.json overrides must be an object of rule: source")
            out = {}
            for k, src in raw.items():
                if not isinstance(src, str) or not src.strip():
                    raise InputMissing("deck.json override %r has no source; every override names where it "
                                       "was granted (e.g. DESIGN.md#R36)" % k)
                out[ALIASES.get(k, k)] = src.strip()
            self._cache["overrides"] = out
        return self._cache["overrides"]

    def overridden(self, key: str) -> str | None:
        """The source of an override for key ('P09:subtitle') or its whole gate ('P09'), else None."""
        o = self.overrides
        return o.get(key) or o.get(key.split(":", 1)[0])

    @property
    def refs_dir(self) -> Path:
        return Path(self._refs) if self._refs else DEFAULT_REFS

    @property
    def fingerprints(self) -> Path:
        return Path(self._fp) if self._fp else DEFAULT_FINGERPRINTS

    @property
    def theme(self):
        if "theme" not in self._cache:
            from deckkit.theme import Theme
            src = self._theme_arg or self.deck_json.get("theme")
            if src:
                p = Path(src)
                if not p.is_absolute():
                    p = self.folder / p
            elif self.manifest and self.manifest.get("theme"):
                p = THEMES / ("%s.json" % self.manifest["theme"])
            else:
                raise InputMissing("no theme: deck.json has no 'theme' and there is no manifest naming one")
            if not p.is_file():
                raise InputMissing("theme file not found: %s" % p)
            try:
                self._cache["theme"] = Theme.load(p)
            except DeckkitError as e:
                raise InputMissing("theme refused: %s" % e) from None
        return self._cache["theme"]

    # -- the deck
    @property
    def dr(self):
        if "dr" not in self._cache:
            self._cache["dr"] = open_deck(str(self.deck_path))
        return self._cache["dr"]

    def close(self):
        d = self._cache.pop("dr", None)
        if d is not None:
            d.close()

    @property
    def n(self) -> int:
        return self.dr.n_slides

    @property
    def canvas(self):
        if "canvas" not in self._cache:
            from deckkit.canvas import canvas_of
            try:
                self._cache["canvas"] = canvas_of((self.dr.cx, self.dr.cy))
            except DeckkitError as e:
                raise InputMissing("canvas: %s" % e) from None
        return self._cache["canvas"]

    @property
    def k(self) -> float:
        return self.canvas.k

    @property
    def W(self) -> float:
        return self.dr.w_in

    @property
    def H(self) -> float:
        return self.dr.h_in

    def slide(self, i: int) -> dict:
        """read_slide for 1-based slide i, cached."""
        key = ("slide", i)
        if key not in self._cache:
            if "dom" not in self._cache:
                from deckkit.read.deckinfo import dominant_face
                self._cache["dom"] = dominant_face(self.dr)
            self._cache[key] = read_slide(self.dr, i, dominant_face=self._cache["dom"])
        return self._cache[key]

    def slides(self):
        return [self.slide(i) for i in range(1, self.n + 1)]

    def slide_root(self, i: int):
        return self.dr.xml(self.dr.slide_part(i))

    def element(self, i: int, shape_id: int):
        """The shape element whose cNvPr id is shape_id on slide i (None when absent)."""
        key = ("ids", i)
        if key not in self._cache:
            m = {}
            for c in self.slide_root(i).iter(P("cNvPr")):
                try:
                    m.setdefault(int(c.get("id", "0")), c.getparent().getparent())
                except ValueError:
                    pass
            self._cache[key] = m
        return self._cache[key].get(shape_id)

    def prs(self):
        if "prs" not in self._cache:
            from pptx import Presentation
            self._cache["prs"] = Presentation(str(self.deck_path))
        return self._cache["prs"]

    def tags(self) -> list[dict]:
        if "tags" not in self._cache:
            self._cache["tags"] = tagmod.read(self.dr)
        return self._cache["tags"]

    # -- taxonomy
    @property
    def archetypes(self) -> dict:
        """{archetype: {"family": F, "budget": {canvas: {"budget": n, "floor": m}}}}, from
        archetypes/archetypes.json when the library has published it, else families only."""
        if "arch" not in self._cache:
            out = {}
            if ARCHETYPES_JSON.is_file():
                d = _load_json(ARCHETYPES_JSON, "archetypes.json")
                items = d.get("archetypes", d)
                for aid, rec in items.items():
                    if isinstance(rec, dict):
                        out[aid] = {"family": rec.get("family"), "budget": rec.get("budget") or rec.get("budgets") or {}}
                self._cache["arch_source"] = str(ARCHETYPES_JSON)
            else:
                fam = _load_json(FAMILIES_JSON, "gates/families.json")
                for f, ids in fam["families"].items():
                    for aid in ids:
                        out[aid] = {"family": f, "budget": {}}
                self._cache["arch_source"] = str(FAMILIES_JSON)
            self._cache["arch"] = out
        return self._cache["arch"]

    def family(self, archetype: str | None) -> str | None:
        if not archetype:
            return None
        rec = self.archetypes.get(archetype)
        return rec["family"] if rec else None

    def slide_family(self, i: int) -> str | None:
        return self.family(self.tags()[i - 1]["archetype"])

    def is_frame(self, i: int) -> bool:
        """Cover, agenda, divider and closing: the Frame family carries no content device."""
        return self.slide_family(i) == FRAME_FAMILY


# ------------------------------------------------------------------ leaf helpers

def bx(L) -> tuple[float, float, float, float]:
    b = L["bbox"]
    return b["x_in"], b["y_in"], b["x_in"] + b["w_in"], b["y_in"] + b["h_in"]


def has_text(L) -> bool:
    t = L.get("text")
    return bool(t and t["text"].strip() and t["words"] > 0)


def text_of(L) -> str:
    t = L.get("text")
    return t["text"] if t else ""


def is_filled(L) -> bool:
    return (L.get("fill") or {}).get("type", "none") not in ("none", None)


def is_lined(L) -> bool:
    return (L.get("line") or {}).get("type", "none") not in ("none", None)


def is_drawn(L) -> bool:
    """Something the eye sees: a fill, an outline, text, a picture or an icon."""
    return is_filled(L) or is_lined(L) or has_text(L) or L["kind"] == "pic" or L.get("icon_like")


def is_state(L) -> bool:
    return (L.get("name") or "").startswith("state.")


def is_bleed(L) -> bool:
    return (L.get("name") or "").startswith("bleed.")


def full_bleed(L, ctx) -> bool:
    b = L["bbox"]
    return b["w_in"] * b["h_in"] >= 0.9 * ctx.W * ctx.H


def fill_role(L, theme) -> str | None:
    """The card role whose resolved hex this leaf's solid fill carries, else None."""
    f = L.get("fill") or {}
    if f.get("type") != "solid":
        return None
    for r in CARD_ROLES:
        if f.get("hex") == theme.hex(r):
            return r
    return None


def cards(slide: dict, ctx) -> list[dict]:
    """Card-like containers: rect-like shapes filled in a card role (or outlined on no fill), at least
    1.2 x 0.45 in (times canvas k), not full-bleed, not a state mark. Each gets a depth (how many other
    cards contain it) for sibling pairing."""
    k = ctx.k
    th = ctx.theme
    out = []
    for L in slide["shapes"]:
        if L["kind"] != "sp" or not is_rect_like(L) or is_state(L) or full_bleed(L, ctx):
            continue
        b = L["bbox"]
        if b["w_in"] < 1.2 * k or b["h_in"] < 0.45 * k:
            continue
        if not (fill_role(L, th) or (not is_filled(L) and is_lined(L))):
            continue
        out.append({"L": L, "box": bx(L), "depth": 0})
    for c in out:
        for o in out:
            if o is not c and contains(o["L"], c["L"], 0.01) and \
                    (o["box"][2] - o["box"][0]) * (o["box"][3] - o["box"][1]) > \
                    (c["box"][2] - c["box"][0]) * (c["box"][3] - c["box"][1]):
                c["depth"] += 1
    return out


def kids_of(card: dict, slide: dict, eps: float = 0.01, any_z: bool = False, full_width: bool = False) -> list[dict]:
    """Drawn leaves wholly inside a card and painted above it, narrower than the card itself. any_z=True takes
    every drawn leaf the card's box contains, whatever its z-order (an outline card drawn over its own text).
    full_width=True keeps a leaf as wide as the card (a header bar across its top) instead of leaving it out."""
    C = card["L"]
    l, t, r, b = card["box"]
    out = []
    for L in slide["shapes"]:
        if L is C or (not any_z and L.get("z", 0) <= C.get("z", 0)) or not is_drawn(L) or L.get("line_like"):
            continue
        x0, y0, x1, y1 = bx(L)
        if x0 >= l - eps and x1 <= r + eps and y0 >= t - eps and y1 <= b + eps and \
                (full_width or (x1 - x0) < 0.99 * (r - l)):
            out.append(L)
    return out


# ------------------------------------------------------------------ text model for measurement

SQRT_HALF = math.sqrt(0.5)


def text_rect(L) -> tuple[float, float]:
    """(w, h) in inches of the shape's text rectangle before insets, for the presets the kit draws text
    in; the full frame otherwise. Matches what the kit measured at build time."""
    fr = L["frame"]
    w, h = fr["w_in"], fr["h_in"]
    g = L.get("geom") or {}
    prst, adj = g.get("prst"), g.get("adj") or {}
    ss = min(w, h)
    if prst == "roundRect":
        i = ss * adj.get("adj", 16667) / 1e5 * 0.29289
        return w - 2 * i, h - 2 * i
    if prst in ("ellipse", "flowChartConnector"):
        return w * SQRT_HALF, h * SQRT_HALF
    if prst == "homePlate":
        return w - ss * adj.get("adj", 50000) / 1e5, h
    if prst == "chevron":
        return w - 2 * ss * adj.get("adj", 50000) / 1e5, h
    return w, h


def paragraph_elements(ctx, i: int, L) -> list:
    """The a:p elements behind a leaf's text, in order (sp: its txBody; cell: its a:tc)."""
    if L["kind"] == "cell":
        cell = L.get("cell") or {}
        gf = ctx.element(i, cell.get("table_id"))
        if gf is None:
            return []
        tbl = gf.find(".//" + A("tbl"))
        try:
            tc = tbl.findall(A("tr"))[cell["row"] - 1].findall(A("tc"))[cell["col"] - 1]
        except (IndexError, AttributeError):
            return []
        tx = tc.find(A("txBody"))
    else:
        el = ctx.element(i, L["id"])
        tx = el.find(P("txBody")) if el is not None else None
    return tx.findall(A("p")) if tx is not None else []


FALLBACK_FACE = "Arial"


def _face(r, unknown):
    """The measured face for a run. A face with no metrics raises UnknownFace, unless `unknown` is a list: then
    the face is recorded there and the run is measured in Arial of the same cut (a labelled fallback)."""
    try:
        return measure.face_for(r["font"] or FALLBACK_FACE, r["bold"], r["italic"])
    except UnknownFace:
        if unknown is None:
            raise
        if r["font"] not in unknown:
            unknown.append(r["font"])
        return measure.face_for(FALLBACK_FACE, r["bold"], r["italic"])


def measure_paras(ctx, i: int, L, unknown: list | None = None) -> list[tuple[measure.MPara, float]]:
    """(MPara, left margin in) per paragraph, rebuilt from the read layer's effective runs, with a:br as
    a hard line break inside the paragraph. The left margin (marL through the level chain) and the empty
    paragraph's size (endParaRPr) come from the read layer. Raises UnknownFace for a face the measurer has no
    metrics for, unless `unknown` is a list (see _face)."""
    tx = L["text"]
    ps = paragraph_elements(ctx, i, L)
    dom = (tx.get("size") or {}).get("dominant_pt") or 18.0
    out = []
    for p_el, p in zip(ps, tx["paragraphs"]):
        runs, k = [], 0
        for n in p_el:
            t = local(n)
            if t in ("r", "fld"):
                if k < len(p["runs"]):
                    r = p["runs"][k]
                    runs.append(measure.MRun(r["t"], r["size_rendered_pt"], _face(r, unknown)))
                k += 1
            elif t == "br" and runs:
                runs.append(measure.MRun("\n", runs[-1].pt, runs[-1].face))
        mar = p.get("mar_l_in") or 0.0
        pt = p.get("end_pt") or dom
        red = (tx["body"].get("ln_spc_reduction") or 0.0)
        ls = (p.get("ln_spc_pct") or 100.0) / 100.0 * (1.0 - red)
        out.append((measure.MPara(tuple(runs), line_spacing=ls, line_pt=p.get("ln_spc_pt"),
                                  space_before_pt=p.get("spc_bef_pt") or 0.0,
                                  space_after_pt=p.get("spc_aft_pt") or 0.0,
                                  pt=pt * (tx["body"].get("font_scale") or 1.0)), mar))
    return out


def need_in(ctx, i: int, L, slack: float, unknown: list | None = None) -> tuple[float, float, int]:
    """(need, have, lines) in inches for a text leaf, measured with deckkit.measure at `slack`. `unknown`: see
    measure_paras."""
    tx = L["text"]
    body = tx["body"]
    w, h = text_rect(L)
    il, it, ir, ib = body["insets_in"]
    avail = w - il - ir if body.get("wrap") != "none" else 1e9
    need, lines = it + ib, 0
    for mp, mar in measure_paras(ctx, i, L, unknown):
        f = measure.fits([mp], (max(0.01, avail - mar), 1e9), slack=slack, floor=0.01)
        need += f.need_in
        lines += f.n_lines
    return need, h, lines


def crash(gate: str, i: int | None, where: str, e: Exception) -> Finding:
    """A FAIL for one shape or slide a gate could not read: the gate goes on with the rest, and the crash is a
    finding, never a pass."""
    tb = traceback.extract_tb(e.__traceback__)
    at = ("%s:%d" % (Path(tb[-1].filename).name, tb[-1].lineno)) if tb else "?"
    return Finding(gate, FAIL, i, where, "could not check: %s: %s (%s)" % (type(e).__name__, str(e)[:160], at))


# ------------------------------------------------------------------ reporting and the CLI

def run_gate(mod, deck, ctx: Ctx | None = None) -> tuple[int, list[Finding]]:
    """(exit code, findings). 0 pass, 1 fail, 2 missing input (counted as FAIL by the runner)."""
    own = ctx is None
    try:
        ctx = ctx or Ctx(deck)
        src = ctx.overridden(mod.GATE)
        if src and ":" not in mod.GATE:
            return 0, [Finding(mod.GATE, NOTE, None, "", "OVERRIDDEN by deck.json (%s)" % src)]
        found = mod.run(deck, ctx)
    except InputMissing as e:
        return 2, [Finding(mod.GATE, FAIL, None, "input", str(e))]
    except Exception as e:  # a gate that crashes has not passed
        tb = traceback.format_exc().strip().splitlines()
        return 1, [Finding(mod.GATE, FAIL, None, "error", "%s: %s (%s)" % (type(e).__name__, e, tb[-3:-1]))]
    finally:
        if own and ctx is not None:
            ctx.close()
    return (1 if any(f.level == FAIL for f in found) else 0), found


def verdict(mod, code: int, found: list[Finding]) -> str:
    fails = sum(1 for f in found if f.level == FAIL)
    adv = sum(1 for f in found if f.level == ADVISORY)
    if code == 0:
        tail = ("  %d advisory" % adv) if adv else ""
        return "%s %s: PASS%s" % (mod.GATE, mod.TITLE, tail)
    if code == 2:
        return "%s %s: FAIL  missing input" % (mod.GATE, mod.TITLE)
    return "%s %s: FAIL  %d finding(s)" % (mod.GATE, mod.TITLE, fails)


def cli(mod, argv=None) -> int:
    ap = argparse.ArgumentParser(prog=Path(mod.__file__).name, description=(mod.__doc__ or "").splitlines()[0])
    ap.add_argument("deck")
    ap.add_argument("--refs", help="leak references folder (default devices/refs)")
    ap.add_argument("--fingerprints", help="fingerprints.json (default ~/.claude/hooks/fingerprints.json)")
    ap.add_argument("--theme", help="theme JSON (default: deck.json, else the manifest's theme)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("-q", "--quiet", action="store_true", help="verdict only")
    a = ap.parse_args(argv)
    try:
        ctx = Ctx(a.deck, refs_dir=a.refs, fingerprints=a.fingerprints, theme=a.theme)
    except InputMissing as e:
        print("%s %s: FAIL  missing input: %s" % (mod.GATE, mod.TITLE, e))
        return 2
    code, found = run_gate(mod, a.deck, ctx)
    ctx.close()
    if a.json:
        print(json.dumps({"gate": mod.GATE, "code": code, "findings": [asdict(f) for f in found]}, indent=1))
        return code
    if not a.quiet:
        for f in found:
            print(f.line())
    print(verdict(mod, code, found))
    return code


__all__ = ["Ctx", "Finding", "InputMissing", "FAIL", "ADVISORY", "NOTE", "run_gate", "verdict", "cli", "bx",
           "has_text", "text_of", "is_filled", "is_lined", "is_drawn", "is_state", "is_bleed", "full_bleed",
           "fill_role", "cards", "kids_of", "text_rect", "measure_paras", "need_in", "crash", "FALLBACK_FACE",
           "contains", "is_rect_like",
           "words", "geom", "measure", "CEILING", "SKILL", "GATES_DIR", "DEVICES_JSON"]
