"""Theme slots, roles, contrast and colour-vision checks, and the theme-part swap.

The kit never writes a hex for a theme colour. It writes a role, and a role is an expression over a
scheme slot: `schemeClr` plus lumMod/lumOff. A client cut is then a clrScheme swap.

Slot model (DECISIONS 2026-10-03, engineering.md (b)):
  * dk1 000000 and lt1 FFFFFF are fixed in every theme. Light backgrounds always.
  * A theme may set dk2, lt2, accent1 to accent6, hlink and folHlink. Anything else raises.
  * The master clrMap is standard: bg1=lt1, tx1=dk1, bg2=lt2, tx2=dk2.
  * fmtScheme is flat: three solid phClr fills, three solid background fills, three EMPTY effect
    styles, lines 0.75 / 1.0 / 1.5pt solid. No gradient and no shadow can arrive through a style ref.

Colour maths (apply_mods, contrast) is deckkit.read.colour: one implementation for reader and writer.
"""
from __future__ import annotations

import itertools
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from .errors import ThemeInvariant
from .read.colour import apply_mods, contrast, hex2rgb, l2s, rgb2hex, s2l
from .read.ns import NS

A_NS = NS["a"]
_A = "{%s}" % A_NS

FIXED = {"dk1": "000000", "lt1": "FFFFFF"}
OPEN_SLOTS = ("dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink",
              "folHlink")
SLOT_ORDER = ("dk1", "lt1") + OPEN_SLOTS
CLRMAP = {"bg1": "lt1", "tx1": "dk1", "bg2": "lt2", "tx2": "dk2", **{s: s for s in OPEN_SLOTS[2:]}}
EXPR_SLOTS = tuple(CLRMAP)            # what a role may name in a schemeClr (mapped names, never dk1/lt1)
MODS = ("lumMod", "lumOff")
VENDOR_SOURCES = ("diagrams",)        # the diagrams package's resources tree, the kit's one vendor-mark source

# Roles, as expressions. Contrast figures against white are in engineering.md (b).
ROLE_DEFAULTS = {
    "paper": "bg1",
    "card": "bg1 lumMod 95000",
    "hairline-soft": "bg1 lumMod 85000",
    "hairline": "bg1 lumMod 75000",
    "rule-strong": "bg1 lumMod 55000",
    "ink-deep": "tx1 lumMod 90000 lumOff 10000",
    "ink": "tx1 lumMod 80000 lumOff 20000",
    "ink-strong": "tx1 lumMod 75000 lumOff 25000",
    "ink-muted": "tx1 lumMod 65000 lumOff 35000",
    "accent": "accent1",
    "accent-tint": "accent1 lumMod 20000 lumOff 80000",
    "accent-wash": "accent1 lumMod 10000 lumOff 90000",
    "accent-deep": "accent1 lumMod 75000",
    "accent-ink": "accent1",          # solved per theme: lumMod lowered until text clears 4.5
    "on-accent": "bg1",               # solved per theme: bg1 or tx1, whichever contrasts more
    "navy": "tx2",
    "series-1": "accent2",
    "series-2": "accent3",
    "series-3": "accent4",
    "series-4": "accent5",
    "series-5": "accent6",
}
ROLES = tuple(ROLE_DEFAULTS)
TEXT_ROLES = ("ink-deep", "ink", "ink-strong", "ink-muted", "accent-ink", "on-accent", "navy")
SERIES = tuple("series-%d" % i for i in range(1, 6))

HAIRLINE_EXEMPT = ("decorative: card borders and dividers on spaced or filled cards. WCAG 1.4.11 scopes 3:1 "
                   "to boundaries needed to identify a component (hospital tokens precedent, DECISIONS "
                   "2026-10-03 hairline scoping). An outline-only card on white uses rule-strong.")

# (foreground, background, minimum, reason). minimum None means EXEMPT, recorded with its reason.
CONTRAST_PAIRS = (
    ("ink-deep", "paper", 7.0, "titles"),
    ("ink", "paper", 7.0, "body copy on the page"),
    ("ink", "card", 7.0, "body copy on a filled card"),
    ("ink-strong", "paper", 7.0, "strong copy on the page"),
    ("ink-muted", "paper", 4.5, "labels and secondary copy"),
    ("ink-muted", "card", 4.5, "labels on a filled card"),
    ("navy", "paper", 4.5, "alternate strong ink"),
    ("accent-ink", "paper", 4.5, "title keywords and labels in the brand colour"),
    ("accent-ink", "card", 4.5, "brand-colour labels on a filled card"),
    ("ink", "accent-tint", 4.5, "copy inside a grouping container"),
    ("ink", "accent-wash", 4.5, "copy inside a tinted zone"),
    ("on-accent", "accent", 4.5, "text on accent fills (discs, tabs)"),
    ("on-accent", "accent-deep", 4.5, "text on emphasis fills"),
    ("paper", "ink-strong", 4.5, "white caps text on a header pill"),
    ("rule-strong", "paper", 3.0, "outline-only card boundary on white (WCAG 1.4.11)"),
    ("hairline", "paper", None, HAIRLINE_EXEMPT),
    ("hairline-soft", "paper", None, HAIRLINE_EXEMPT),
)

# Machado, Oliveira and Fernandes 2009, severity 1.0, applied in LINEAR RGB as the paper specifies.
MACHADO = {
    "protan": ((0.152286, 1.052583, -0.204868),
               (0.114503, 0.786281, 0.099216),
               (-0.003882, -0.048116, 1.051998)),
    "deutan": ((0.367322, 0.860646, -0.227968),
               (0.280085, 0.672501, 0.047413),
               (-0.011820, 0.042940, 0.968881)),
    "tritan": ((1.255528, -0.076749, -0.178779),
               (-0.078411, 0.930809, 0.147602),
               (0.004733, 0.691367, 0.303900)),
}
# A pair whose CIEDE2000 distance falls below this, under any simulation (or normal vision), is
# reported. 2.3 is a just-noticeable difference on large patches; series marks are small (legend
# swatches, thin bars, discs), where separation needs several times that. 10 is the working line.
# Reported, not failed: the kit carries every series with a label, a glyph or a position, so identity
# never rests on hue alone (CLAUDE.md section 4).
CVD_DELTA_E = 10.0


# ------------------------------------------------------------------ expressions

@dataclass(frozen=True)
class Expr:
    slot: str
    mods: tuple = ()          # ((name, int), ...) in document order

    def __str__(self) -> str:
        return " ".join([self.slot] + ["%s %d" % m for m in self.mods])

    def lum_mod(self) -> int:
        for n, v in self.mods:
            if n == "lumMod":
                return v
        return 100000

    def with_lum_mod(self, v: int) -> "Expr":
        rest = tuple(m for m in self.mods if m[0] != "lumMod")
        return Expr(self.slot, (("lumMod", int(v)),) + rest)


def parse_expr(text: str, what: str = "role") -> Expr:
    toks = str(text).split()
    if not toks or toks[0] not in EXPR_SLOTS:
        raise ThemeInvariant("%s expression %r" % (what, text), need="one of " + ", ".join(EXPR_SLOTS),
                             have=toks[0] if toks else "", hint="write roles over mapped slot names")
    if len(toks) % 2 != 1:
        raise ThemeInvariant("%s expression %r" % (what, text), need="slot then name value pairs",
                             have=len(toks))
    mods = []
    for n, v in zip(toks[1::2], toks[2::2]):
        if n not in MODS or not re.fullmatch(r"\d{1,6}", v) or int(v) > 100000:
            raise ThemeInvariant("%s expression %r" % (what, text), need="lumMod/lumOff 0..100000",
                                 have="%s %s" % (n, v))
        mods.append((n, int(v)))
    names = [m[0] for m in mods]
    if names not in ([], ["lumMod"], ["lumOff"], ["lumMod", "lumOff"]):
        raise ThemeInvariant("%s expression %r" % (what, text), need="lumMod before lumOff, once each",
                             have=names)
    return Expr(toks[0], tuple(mods))


def _hex_ok(v) -> bool:
    return isinstance(v, str) and re.fullmatch(r"[0-9A-Fa-f]{6}", v) is not None


# ------------------------------------------------------------------ colour vision

def _simulate(hex_: str, kind: str) -> str:
    lin = [s2l(c) for c in hex2rgb(hex_)]
    m = MACHADO[kind]
    out = [sum(m[i][j] * lin[j] for j in range(3)) for i in range(3)]
    return rgb2hex([l2s(min(1.0, max(0.0, c))) for c in out])


def _lab(hex_: str) -> tuple[float, float, float]:
    r, g, b = (s2l(c) for c in hex2rgb(hex_))
    x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > (6 / 29) ** 3 else t / (3 * (6 / 29) ** 2) + 4 / 29
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e00(h1: str, h2: str) -> float:
    """CIEDE2000 between two hex colours (Sharma, Wu and Dalal 2005 formulation)."""
    L1, a1, b1 = _lab(h1)
    L2, a2, b2 = _lab(h2)
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360 if C1p else 0.0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360 if C2p else 0.0
    dLp, dCp = L2 - L1, C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    else:
        dhp = h2p - h1p - 360 if h2p > h1p else h2p - h1p + 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp / 2))
    Lbp, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0:
        hbp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbp = (h1p + h2p) / 2
    else:
        hbp = (h1p + h2p + 360) / 2 if h1p + h2p < 360 else (h1p + h2p - 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hbp - 30)) + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6)) - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    dtheta = 30 * math.exp(-(((hbp - 275) / 25) ** 2))
    Rc = 2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7))
    Sl = 1 + 0.015 * (Lbp - 50) ** 2 / math.sqrt(20 + (Lbp - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cbp, 1 + 0.015 * Cbp * T
    Rt = -math.sin(math.radians(2 * dtheta)) * Rc
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))


# ------------------------------------------------------------------ the theme

class Theme:
    """A loaded theme: slots, role expressions, fonts, fill-only slots and the identity registry."""

    def __init__(self, data: dict, path: str | None = None):
        self.path = path
        self.data = data
        self.name = str(data.get("name") or "")
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,40}", self.name):
            raise ThemeInvariant("theme name", need="lower-case id", have=self.name)
        self.source = str(data.get("source") or "")
        self.slots = self._load_slots(data.get("slots") or {})
        f = data.get("fonts") or {}
        self.fonts = {"major": f.get("major") or "Arial", "minor": f.get("minor") or "Arial",
                      "numerals": f.get("numerals")}
        self.fill_only = dict(data.get("fill_only") or {})
        for s in self.fill_only:
            if s not in OPEN_SLOTS:
                raise ThemeInvariant("fill_only slot %r" % s, need="one of " + ", ".join(OPEN_SLOTS), have=s)
        self.identity = {}
        for k, v in (data.get("identity") or {}).items():
            if not (isinstance(v, dict) and _hex_ok(v.get("hex")) and v.get("reason")):
                raise ThemeInvariant("identity %r" % k, need="{hex, reason}", have=v,
                                     hint="every identity colour states why it keeps its hue")
            self.identity[k] = {"hex": v["hex"].upper(), "reason": v["reason"]}
        # Vendor registry: the vendors whose service marks keep their own artwork and hue on this theme.
        # A key ('aws/compute/ec2') resolves when its first segment is registered here and the mark file
        # exists in the source (deckkit.icons.vendor_resolves); gate P22 checks that instead of a hue.
        self.vendors = {}
        for k, v in (data.get("vendors") or {}).items():
            if not (re.fullmatch(r"[a-z][a-z0-9-]{0,20}", str(k)) and isinstance(v, dict)
                    and v.get("source") in VENDOR_SOURCES and v.get("reason")):
                raise ThemeInvariant("vendor %r" % k, need="{source: %s, reason}" % " / ".join(VENDOR_SOURCES),
                                     have=v, hint="every vendor states where its marks come from and why they keep "
                                                  "their hue")
            self.vendors[k] = {"source": v["source"], "reason": v["reason"]}
        self.roles: dict[str, Expr] = {}
        self.solved: dict[str, dict] = {}
        self._load_roles(data.get("roles") or {})

    # --------------------------------------------------------------- loading
    @classmethod
    def load(cls, path) -> "Theme":
        p = Path(path)
        with open(p, encoding="utf-8") as fh:
            return cls(json.load(fh), str(p))

    @staticmethod
    def _load_slots(given: dict) -> dict:
        out = dict(FIXED)
        for k, v in given.items():
            if k in FIXED:
                if not _hex_ok(v) or v.upper() != FIXED[k]:
                    raise ThemeInvariant("slot %s" % k, need=FIXED[k], have=v,
                                         hint="dk1 and lt1 are fixed in every theme; change dk2/lt2 instead")
                continue
            if k not in OPEN_SLOTS:
                raise ThemeInvariant("slot %s" % k, need="one of " + ", ".join(OPEN_SLOTS), have=k)
            if not _hex_ok(v):
                raise ThemeInvariant("slot %s" % k, need="6-digit hex", have=v)
            out[k] = v.upper()
        missing = [s for s in OPEN_SLOTS if s not in out]
        if missing:
            raise ThemeInvariant("slots", need="all of " + ", ".join(OPEN_SLOTS), have="missing " + ", ".join(missing))
        return out

    def _load_roles(self, given: dict):
        unknown = [k for k in given if k not in ROLE_DEFAULTS]
        if unknown:
            raise ThemeInvariant("roles", need="known role names", have=unknown)
        derived = []
        for name, default in ROLE_DEFAULTS.items():
            spec = given.get(name)
            if spec is None:
                self.roles[name] = parse_expr(default, name)
            elif isinstance(spec, str):
                self.roles[name] = parse_expr(spec, name)
            elif isinstance(spec, dict) and "expr" in spec:
                self.roles[name] = parse_expr(spec["expr"], name)
            elif isinstance(spec, dict) and ("solve" in spec or "pick" in spec):
                self.roles[name] = parse_expr(default, name)     # placeholder until solved below
                derived.append((name, spec))
            else:
                raise ThemeInvariant("role %s" % name, need="expression, {expr}, {solve} or {pick}", have=spec)
        for name, spec in derived:
            if "solve" in spec:
                s = spec["solve"]
                against = s.get("against") or ["paper"]
                against = [against] if isinstance(against, str) else list(against)
                self._no_derived(name, against, derived)
                start = parse_expr(s.get("from") or ROLE_DEFAULTS[name], name)
                expr, ratio = self._solve_expr(name, start, against, float(s.get("min", 4.5)))
                self.solved[name] = {"method": "solve", "against": against, "min": float(s.get("min", 4.5)),
                                     "expr": str(expr), "ratio": ratio}
            else:
                p = spec["pick"]
                against = p.get("against") or "accent"
                against = [against] if isinstance(against, str) else list(against)
                self._no_derived(name, against, derived)
                cands = [parse_expr(c, name) for c in (p.get("from") or ["bg1", "tx1"])]
                expr, ratio = self._pick_expr(cands, against)
                self.solved[name] = {"method": "pick", "against": against, "expr": str(expr), "ratio": ratio}
            self.roles[name] = expr
            rec = spec.get("record")
            if rec is not None and str(parse_expr(rec, name)) != str(expr):
                raise ThemeInvariant("role %s record" % name, need=str(expr), have=rec,
                                     hint="the slots changed since the record was written; re-run theme check "
                                          "and update the record")

    @staticmethod
    def _no_derived(name, against, derived):
        bad = [a for a in against if a in {d[0] for d in derived} or a not in ROLE_DEFAULTS]
        if bad:
            raise ThemeInvariant("role %s solve" % name, need="against plain roles", have=bad)

    # --------------------------------------------------------------- values
    def slot_hex(self, name: str) -> str:
        slot = CLRMAP.get(name, name)
        if slot not in self.slots:
            raise ThemeInvariant("slot %s" % name, need="a scheme slot", have=name)
        return self.slots[slot]

    def expr_hex(self, expr: Expr) -> str:
        return apply_mods(self.slot_hex(expr.slot), list(expr.mods))

    def _role(self, role: str) -> Expr:
        e = self.roles.get(role)
        if e is None:
            raise ThemeInvariant("role %r" % role, need="one of " + ", ".join(ROLES), have=role)
        return e

    def hex(self, role: str) -> str:
        """The role's resolved hex, for gates, the twin and contrast. Never written to a slide."""
        return self.expr_hex(self._role(role))

    def expr(self, role: str) -> str:
        return str(self._role(role))

    def spec(self, role: str):
        """A fresh `<a:schemeClr>` element (with lumMod/lumOff children) for the role."""
        e = self._role(role)
        el = etree.Element(_A + "schemeClr", nsmap={"a": A_NS})
        el.set("val", e.slot)
        for n, v in e.mods:
            etree.SubElement(el, _A + n).set("val", str(v))
        return el

    def spec_xml(self, role: str) -> str:
        e = self._role(role)
        inner = "".join('<a:%s val="%d"/>' % m for m in e.mods)
        if inner:
            return '<a:schemeClr val="%s">%s</a:schemeClr>' % (e.slot, inner)
        return '<a:schemeClr val="%s"/>' % e.slot

    # --------------------------------------------------------------- theme part XML
    def clr_scheme_xml(self) -> str:
        body = "".join('<a:%s><a:srgbClr val="%s"/></a:%s>' % (s, self.slots[s], s) for s in SLOT_ORDER)
        return '<a:clrScheme xmlns:a="%s" name="%s">%s</a:clrScheme>' % (A_NS, self.name, body)

    def font_scheme_xml(self) -> str:
        def face(tag, tf):
            return '<a:%s><a:latin typeface="%s"/><a:ea typeface=""/><a:cs typeface=""/></a:%s>' % (tag, tf, tag)
        return ('<a:fontScheme xmlns:a="%s" name="%s">%s%s</a:fontScheme>'
                % (A_NS, self.name, face("majorFont", self.fonts["major"]), face("minorFont", self.fonts["minor"])))

    def fmt_scheme_xml(self) -> str:
        solid = '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
        line = ('<a:ln w="%d" cap="flat" cmpd="sng" algn="ctr">' + solid +
                '<a:prstDash val="solid"/><a:miter lim="800000"/></a:ln>')
        return ('<a:fmtScheme xmlns:a="%s" name="%s">'
                '<a:fillStyleLst>%s</a:fillStyleLst>'
                '<a:lnStyleLst>%s</a:lnStyleLst>'
                '<a:effectStyleLst>%s</a:effectStyleLst>'
                '<a:bgFillStyleLst>%s</a:bgFillStyleLst>'
                '</a:fmtScheme>'
                % (A_NS, self.name, solid * 3, "".join(line % w for w in (9525, 12700, 19050)),
                   "<a:effectStyle><a:effectLst/></a:effectStyle>" * 3, solid * 3))

    def theme_xml(self) -> bytes:
        """A complete theme part (ppt/theme/themeN.xml)."""
        x = ('<a:theme xmlns:a="%s" name="%s"><a:themeElements>%s%s%s</a:themeElements>'
             '<a:objectDefaults/><a:extraClrSchemeLst/></a:theme>'
             % (A_NS, self.name, self.clr_scheme_xml(), self.font_scheme_xml(), self.fmt_scheme_xml()))
        root = etree.fromstring(x)
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    def retheme_part(self, data: bytes) -> bytes:
        """An existing theme part with its clrScheme, fontScheme and fmtScheme replaced by this theme's."""
        root = etree.fromstring(data)
        te = root.find(_A + "themeElements")
        if te is None:
            raise ThemeInvariant("theme part", need="a:themeElements", have=etree.QName(root).localname)
        for tag, xml in (("clrScheme", self.clr_scheme_xml()), ("fontScheme", self.font_scheme_xml()),
                         ("fmtScheme", self.fmt_scheme_xml())):
            new = etree.fromstring(xml)
            old = te.find(_A + tag)
            if old is not None:
                te.replace(old, new)
            else:
                te.append(new)
        root.set("name", self.name)
        etree.cleanup_namespaces(root)
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    # --------------------------------------------------------------- contrast
    def contrast_table(self) -> list[dict]:
        rows = []
        for fg, bg, mn, reason in CONTRAST_PAIRS:
            fh, bh = self.hex(fg), self.hex(bg)
            r = contrast(fh, bh)
            status = "EXEMPT" if mn is None else ("PASS" if r >= mn else "FAIL")
            rows.append({"fg": fg, "bg": bg, "fg_hex": fh, "bg_hex": bh, "ratio": r, "min": mn,
                         "status": status, "reason": reason})
        for role in TEXT_ROLES:
            slot = CLRMAP.get(self.roles[role].slot, self.roles[role].slot)
            if slot in self.fill_only:
                rows.append({"fg": role, "bg": "-", "fg_hex": self.hex(role), "bg_hex": "", "ratio": None,
                             "min": None, "status": "FAIL",
                             "reason": "%s is fill-only (%s) and may not carry text" % (slot, self.fill_only[slot])})
        return rows

    def failures(self) -> list[dict]:
        return [r for r in self.contrast_table() if r["status"] == "FAIL"]

    def _ratio_all(self, hex_: str, against) -> float:
        return min(contrast(hex_, self.hex(a)) for a in against)

    def _solve_expr(self, what, start: Expr, against, minimum: float, step: int = 500):
        r = self._ratio_all(self.expr_hex(start), against)
        if r >= minimum:
            return start, r
        v = start.lum_mod()
        while v > 0:
            v -= step
            e = start.with_lum_mod(max(v, 0))
            r = self._ratio_all(self.expr_hex(e), against)
            if r >= minimum:
                return e, r
        raise ThemeInvariant("solve %s" % what, need=minimum, have=r,
                             hint="no lumMod reaches the minimum against %s; pick another slot" % ", ".join(against))

    def _pick_expr(self, cands, against):
        scored = [(self._ratio_all(self.expr_hex(c), against), i, c) for i, c in enumerate(cands)]
        r, _, c = max(scored, key=lambda t: (t[0], -t[1]))
        return c, r

    def solve(self, role: str, against, minimum: float = 4.5, step: int = 500) -> tuple[str, float]:
        """Lower the role's lumMod in steps until it clears `minimum` against every role in `against`.

        Returns (expression, worst ratio). Does not change the theme; record the result in the JSON.
        """
        against = [against] if isinstance(against, str) else list(against)
        e, r = self._solve_expr(role, self._role(role), against, minimum, step)
        return str(e), r

    # --------------------------------------------------------------- colour vision
    def cvd(self, roles=None, threshold: float = CVD_DELTA_E) -> list[dict]:
        """Pairs closer than `threshold` (CIEDE2000) in normal vision or under a Machado simulation."""
        roles = list(roles) if roles else ["accent"] + list(SERIES)
        hexes = {r: self.hex(r) for r in roles}
        out = []
        for kind in ("normal",) + tuple(MACHADO):
            sim = {r: (h if kind == "normal" else _simulate(h, kind)) for r, h in hexes.items()}
            for a, b in itertools.combinations(roles, 2):
                if hexes[a] == hexes[b]:
                    continue
                d = delta_e00(sim[a], sim[b])
                if d < threshold:
                    out.append({"kind": kind, "a": a, "b": b, "a_hex": hexes[a], "b_hex": hexes[b],
                                "delta_e": round(d, 2)})
        return out

    # --------------------------------------------------------------- report
    def report(self) -> tuple[str, int]:
        """(text, exit code). Exit 1 when any gated pair fails."""
        lines = ["theme %s  (%s)" % (self.name, self.path or "in memory"), ""]
        lines.append("%-14s %-12s %-7s %-7s %6s %5s  %s" % ("fg", "bg", "fg", "bg", "ratio", "min", "status"))
        rows = self.contrast_table()
        for r in rows:
            ratio = "%6.2f" % r["ratio"] if r["ratio"] is not None else "     -"
            mn = "%5.1f" % r["min"] if r["min"] is not None else "    -"
            lines.append("%-14s %-12s %-7s %-7s %s %s  %s  %s" % (r["fg"], r["bg"], r["fg_hex"], r["bg_hex"], ratio,
                                                               mn, r["status"], r["reason"] if r["status"] != "PASS" else ""))
        if self.solved:
            lines.append("")
            for name, s in self.solved.items():
                lines.append("derived %-11s %s = %s  worst %.2f against %s" % (name, s["method"], s["expr"], s["ratio"],
                                                                         ", ".join(s["against"])))
        col = self.cvd()
        lines.append("")
        lines.append("colour vision (Machado 2009, severity 1.0), accent and series, CIEDE2000 < %.0f:" % CVD_DELTA_E)
        if col:
            for c in col:
                lines.append("  %-7s %-9s %s ~ %-9s %s  dE %.2f" % (c["kind"], c["a"], c["a_hex"], c["b"], c["b_hex"],
                                                               c["delta_e"]))
            lines.append("  reported, not failed: series identity always travels with a label, glyph or position")
        else:
            lines.append("  no pair closer than the line")
        fails = [r for r in rows if r["status"] == "FAIL"]
        lines.append("")
        lines.append("FAIL: %d gated pair(s)" % len(fails) if fails else "PASS: every gated pair clears its minimum")
        return "\n".join(lines), (1 if fails else 0)


# ------------------------------------------------------------------ package-level swap

THEME_CT = "application/vnd.openxmlformats-officedocument.theme+xml"


def theme_parts(names, content_types: bytes | None) -> list[str]:
    """Every theme part in a package, by content type Override, falling back to the part name."""
    out = set()
    if content_types:
        ct = etree.fromstring(content_types)
        for o in ct:
            if o.get("ContentType") == THEME_CT and o.get("PartName"):
                out.add(o.get("PartName").lstrip("/"))
    out |= {n for n in names if re.fullmatch(r"ppt/theme/theme\d+\.xml", n)}
    return sorted(n for n in out if n in set(names))


def apply_theme(pptx_path, theme: Theme, out_path=None) -> list[str]:
    """Swap clrScheme, fontScheme and fmtScheme in every theme part of a package (slide masters, notes
    and handout masters alike). Writes atomically, deterministically. Returns the parts swapped."""
    import zipfile
    from .package import write_members     # package imports theme; import here to stay acyclic
    with zipfile.ZipFile(pptx_path) as z:
        members = {i.filename: z.read(i.filename) for i in z.infolist()}
    parts = theme_parts(list(members), members.get("[Content_Types].xml"))
    if not parts:
        raise ThemeInvariant("apply_theme", need="at least one theme part", have=0)
    for n in parts:
        members[n] = theme.retheme_part(members[n])
    write_members(members, out_path or pptx_path)
    return parts


__all__ = ["Theme", "Expr", "parse_expr", "ROLES", "ROLE_DEFAULTS", "TEXT_ROLES", "SERIES", "CONTRAST_PAIRS",
           "FIXED", "OPEN_SLOTS", "CLRMAP", "MACHADO", "CVD_DELTA_E", "delta_e00", "apply_theme", "theme_parts"]
