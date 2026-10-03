"""Client brand intake (ruling 23): a contrast-solved client theme from a few hexes, the colour candidates a client's
production CSS carries, and the cover or closing logo lockup.

    make_theme(name, primary, secondary=None, accents=(), font=None, verified=None, logo=None, house=SIGMOID)
        returns (theme data, notes). The client primary goes into accent1; dk2 and lt2 are derived from its hue; the
        series (accent2 to accent6) are the secondaries in the order given, then the house slates; the identity and
        vendors blocks are copied verbatim from the house theme so notation and vendor colours survive the swap.
        accent-ink is solved to 4.5:1 against paper and card (Theme.solve), on-accent is picked (white or black),
        and both are recorded. A theme that fails `theme check` raises BrandRefused with the failing pairs.
    css_candidates(css_texts) returns ranked candidate colours: custom properties first, then the most-used non-neutral
        colours, each with its count and the property names that carry it. Nothing is picked: the user confirms.
    fetch_css(url) returns (stylesheet texts, urls read). Reads the page, its <style> blocks and linked stylesheets.
    font_choice(name) returns (font used, note). A face the kit cannot measure, or one not installed, falls back to
        Arial.
    lockup(slide, box, client_logo, firm_logo=None, *, theme, name, firm_name="Sigmoid")
        the client logo, with the firm logo after a hairline divider when given, on a slide tagged cover or closing
        only (DECISIONS structure: a client logo belongs on the cover lockup). Aspect kept; SVG with a PNG fallback;
        PNG as is (refused under 2x its displayed size). Shapes logo.client, logo.divider, logo.firm.
    logo_path(theme) returns the logo file recorded in a client theme's "brand" block, verified by its sha256.
"""
from __future__ import annotations

import colorsys
import copy
import datetime as _dt
import hashlib
import io
import json
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

from . import ooxml
from .canvas import Box
from .errors import DeckkitError, GeometryError, ThemeInvariant, UnknownFace, UnsupportedPart
from .read.colour import contrast, hex2rgb, is_neutral, rgb2hex
from .theme import Theme

SKILL = Path(__file__).resolve().parent.parent.parent
SIGMOID = SKILL / "themes" / "sigmoid.json"

# House slates that pad the series when the client gives fewer than five secondaries (the neutral theme's set,
# spread by lightness so no pair falls under the colour-vision line).
HOUSE_SERIES = ("4B5960", "6B7983", "A6A6A6", "D9D9D9", "1E3C7D")
FOLLOWED = "6B7983"
DK2_TARGET = 8.0          # navy (tx2 = dk2) is an alternate strong ink and a strong fill under white text
LT2_L = 0.94
TEXT_MIN = 4.5
LOCKUP_TAGS = ("cover", "closing")
LOGO_EXT = {".svg": "svg", ".png": "png"}
MAX_SERIES = 5


class BrandRefused(DeckkitError):
    """A client theme that fails the contrast check, or a brand input the kit cannot use."""


# ------------------------------------------------------------------ colour helpers

def norm_hex(v: str, what: str = "colour") -> str:
    """'#0b6e4f', '0B6E4F' or '#0b5' to '0B6E4F'. Anything else raises."""
    s = str(v or "").strip().lstrip("#")
    if re.fullmatch(r"[0-9A-Fa-f]{3}", s):
        s = "".join(c * 2 for c in s)
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", s):
        raise BrandRefused(what, need="a hex colour such as #0B6E4F", have=repr(v))
    return s.upper()


def _hls(hex_: str):
    return colorsys.rgb_to_hls(*hex2rgb(hex_))


def _from_hls(h, l, s) -> str:
    return rgb2hex(colorsys.hls_to_rgb(h, l, s))


def derive_dk2(primary: str) -> str:
    """A deep shade of the primary's hue that clears DK2_TARGET on white (the navy role and hyperlink ink)."""
    h, _l, s = _hls(primary)
    s = min(s, 0.55)
    l = 0.40
    while l > 0.02:
        c = _from_hls(h, l, s)
        if contrast(c, "FFFFFF") >= DK2_TARGET:
            return c
        l -= 0.01
    return _from_hls(h, 0.10, s)


def deeper(hex_: str, minimum: float = TEXT_MIN + 0.1) -> str:
    """The same hue and saturation, darkened until white text clears `minimum` on it."""
    h, l, s = _hls(hex_)
    while l > 0.02:
        c = _from_hls(h, l, s)
        if contrast(c, "FFFFFF") >= minimum:
            return c
        l -= 0.005
    return _from_hls(h, 0.02, s)


def derive_lt2(primary: str) -> str:
    """A near-white tint of the primary's hue (bg2)."""
    h, _l, s = _hls(primary)
    return _from_hls(h, LT2_L, min(s, 0.35))


# ------------------------------------------------------------------ fonts

def font_installed(name: str) -> bool:
    """True when fontconfig lists the family (fc-list), else when a font file named after it is on disk."""
    n = (name or "").strip().lower()
    if not n:
        return False
    try:
        out = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True, timeout=30).stdout
        fams = {f.strip().lower() for line in out.splitlines() for f in line.split(",")}
        if n in fams:
            return True
    except (OSError, subprocess.SubprocessError):
        pass
    squash = n.replace(" ", "")
    for d in (Path("/System/Library/Fonts"), Path("/System/Library/Fonts/Supplemental"), Path("/Library/Fonts"),
              Path.home() / "Library" / "Fonts"):
        if d.is_dir() and any(p.stem.lower().replace(" ", "").replace("-", "").startswith(squash)
                              for p in d.iterdir()):
            return True
    return False


def font_choice(name: str | None) -> tuple[str, str]:
    """(font the theme uses, note). The kit measures every run before it places it, so a face is used only when it is
    installed AND the measurer has metrics for it; anything else falls back to Arial and the note says why."""
    if not name or not str(name).strip():
        return "Arial", "no font given; Arial"
    want = " ".join(str(name).split())
    if want.lower() == "arial":
        return "Arial", "Arial"
    if not font_installed(want):
        return "Arial", ("font %r is not installed on this machine, so the theme uses Arial; install it and rerun "
                         "to use it" % want)
    from . import measure
    try:
        face = measure.face_for(want)
    except UnknownFace:
        return "Arial", ("font %r is installed but the kit has no metrics for it, so no text box could be measured; "
                         "the theme uses Arial (the kit measures Arial and Montserrat)" % want)
    if not Path(face.path).is_file():
        return "Arial", "font %r has metrics but its file %s is missing, so the theme uses Arial" % (want, face.path)
    return face.family, "font %r installed and measured" % want


# ------------------------------------------------------------------ the theme

def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", str(name or "").lower()).strip("-")
    s = re.sub(r"^[^a-z]+", "", s)[:41].rstrip("-")
    if not s:
        raise BrandRefused("client name", need="letters (the theme id is made from them)", have=repr(name))
    return s


def _fill_only_reason(hex_: str) -> str:
    return "%s is %.2f:1 on white, a fill or mark, never text" % (hex_, contrast(hex_, "FFFFFF"))


def make_theme(name: str, primary: str, secondary: str | None = None, accents=(), *, font: str | None = None,
               verified: dict | None = None, logo: dict | None = None, house=SIGMOID, date: str | None = None):
    """(theme data in the sigmoid.json schema, notes). Raises BrandRefused when the theme fails `theme check`."""
    date = date or _dt.date.today().isoformat()
    house_data = json.loads(Path(house).read_text(encoding="utf-8"))
    p = norm_hex(primary, "primary")
    sec = [norm_hex(secondary, "secondary")] if secondary else []
    acc = [norm_hex(a, "accent") for a in (accents or ())]
    given = sec + acc
    series, seen = [], {p}
    for c in given:
        if c not in seen:
            series.append(c)
            seen.add(c)
    if len(series) > MAX_SERIES:
        raise BrandRefused("series colours", need="at most %d (accent2 to accent6)" % MAX_SERIES, have=len(series),
                           hint="pass the five the deck's charts and series need most")
    n_client = len(series)
    for c in HOUSE_SERIES:
        if len(series) >= MAX_SERIES:
            break
        if c not in seen:
            series.append(c)
            seen.add(c)
    dk2, lt2 = derive_dk2(p), derive_lt2(p)
    slots = {"dk2": dk2, "lt2": lt2, "accent1": p}
    for i, c in enumerate(series, start=2):
        slots["accent%d" % i] = c
    slots["hlink"] = dk2
    slots["folHlink"] = FOLLOWED
    fill_only = {"accent%d" % i: _fill_only_reason(c) for i, c in enumerate(series, start=2)
                 if contrast(c, "FFFFFF") < TEXT_MIN}
    face, font_note = font_choice(font)
    fonts = {"major": face, "minor": face}
    if (house_data.get("fonts") or {}).get("numerals"):
        fonts["numerals"] = copy.deepcopy(house_data["fonts"]["numerals"])
    roles = {"accent-ink": {"solve": {"from": "accent1", "against": ["paper", "card"], "min": TEXT_MIN}},
             "on-accent": {"pick": {"from": ["bg1", "tx1"], "against": ["accent", "accent-deep"]}}}
    if verified:
        source = "client brand from %s production CSS, fetched %s; primary %s confirmed by the user" % (
            verified.get("url"), verified.get("fetched"), p)
    else:
        source = "client brand: primary %s given by the user, %s" % (p, date)
    notes = [
        "accent1 is the client primary %s, so every accent role reads the brand." % p,
        "dk2 %s is the primary's hue deepened to %.2f:1 on white (navy, hyperlinks); lt2 %s is its near-white tint."
        % (dk2, contrast(dk2, "FFFFFF"), lt2),
        ("series accent2 to accent6: %d client colour(s) in the order given, then house slates"
         % n_client) if n_client else "series accent2 to accent6: no client secondary given, so house slates",
        font_note,
    ]
    data = {"name": _slug(name), "source": source, "source_notes": notes, "slots": slots, "fonts": fonts,
            "roles": roles, "fill_only": fill_only,
            "vendors": copy.deepcopy(house_data.get("vendors") or {}),
            "identity": copy.deepcopy(house_data.get("identity") or {})}
    try:
        th = Theme(copy.deepcopy(data))
    except ThemeInvariant as e:
        raise BrandRefused("client theme %s" % data["name"], need="a theme the kit can solve", have=str(e),
                           hint=_mid_hint(p)) from None
    for role in ("accent-ink", "on-accent"):
        s = th.solved[role]
        data["roles"][role]["record"] = s["expr"]
        data["roles"][role]["note"] = ("%s, worst %.2f:1 against %s" % (s["expr"], s["ratio"], ", ".join(s["against"])))
    if th.solved["accent-ink"]["expr"] != "accent1":
        data["roles"]["accent-ink"]["note"] += "; the primary is lowered for text only, fills keep %s" % p
    fails = th.failures()
    if fails:
        raise BrandRefused("client theme %s" % data["name"], need="every gated contrast pair to pass",
                           have="; ".join("%s on %s %.2f < %.1f" % (r["fg"], r["bg"], r["ratio"] or 0, r["min"] or 0)
                                          if r["ratio"] is not None else r["reason"] for r in fails),
                           hint=_mid_hint(p))
    data["brand"] = {"client": " ".join(str(name).split()), "primary": p, "secondary": sec[0] if sec else None,
                     "accents": acc, "font": {"requested": font or None, "used": face, "note": font_note},
                     "logo": logo, "verified": verified, "made": date}
    return data, notes


def _mid_hint(p: str) -> str:
    w, b = contrast(p, "FFFFFF"), contrast(p, "000000")
    if w < TEXT_MIN and b < TEXT_MIN * 1.35:
        return ("%s sits at mid luminance (white %.2f, black %.2f): no text colour clears 4.5 on both the accent and "
                "its deeper fill; pass a deeper shade of the brand as --primary (for example #%s, white text %.2f:1) "
                "and the brand colour itself as --secondary" % (p, w, b, deeper(p), contrast(deeper(p), "FFFFFF")))
    return "pass a different --primary"


def check_text(data: dict, path: str | None = None) -> tuple[str, int]:
    """The `theme check` report and exit code for theme data (the CLI's logic: Theme.report)."""
    t = Theme(copy.deepcopy(data), path)
    return t.report()


# ------------------------------------------------------------------ CSS candidates

_HEX = re.compile(r"#([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b")
_RGB = re.compile(r"rgba?\(\s*([0-9.]+%?)[\s,]+([0-9.]+%?)[\s,]+([0-9.]+%?)(?:\s*[,/]\s*([0-9.]+%?))?\s*\)", re.I)
_PROP = re.compile(r"(--[A-Za-z0-9_-]+)\s*:\s*([^;}{]+)")
_LINK = re.compile(r"<link\b[^>]*>", re.I)
_STYLE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.I | re.S)
_ATTR = re.compile(r"""([a-zA-Z-]+)\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)""")
_IMPORT = re.compile(r"""@import\s+(?:url\()?\s*["']?([^"')\s;]+)""", re.I)


def _colours_in(text: str):
    """(hex, alpha) for every colour literal in a CSS value or sheet."""
    for m in _HEX.finditer(text):
        s = m.group(1)
        a = 1.0
        if len(s) in (3, 4):
            if len(s) == 4:
                a = int(s[3] * 2, 16) / 255
            s = "".join(c * 2 for c in s[:3])
        elif len(s) == 8:
            a = int(s[6:8], 16) / 255
            s = s[:6]
        yield s.upper(), a
    for m in _RGB.finditer(text):
        ch = []
        for v in m.groups()[:3]:
            ch.append(float(v[:-1]) * 2.55 if v.endswith("%") else float(v))
        a = m.group(4)
        alpha = 1.0 if a is None else (float(a[:-1]) / 100 if a.endswith("%") else float(a))
        if all(0 <= c <= 255 for c in ch):
            yield "%02X%02X%02X" % tuple(int(round(c)) for c in ch), alpha


def css_candidates(css_texts, limit: int = 12) -> list[dict]:
    """Ranked brand-colour candidates: colours named by custom properties first (by count), then the most-used
    non-neutral colours. Greys, near-white, near-black and mostly transparent colours are left out."""
    counts, props = Counter(), {}
    for css in css_texts:
        for hx, a in _colours_in(css):
            if a >= 0.5:
                counts[hx] += 1
        for m in _PROP.finditer(css):
            for hx, a in _colours_in(m.group(2)):
                if a >= 0.5:
                    props.setdefault(hx, set()).add(m.group(1))
    rows = []
    for hx, n in counts.items():
        if is_neutral(hx):
            continue
        rows.append({"hex": hx, "count": n, "properties": sorted(props.get(hx, ()))[:6],
                     "on_white": round(contrast(hx, "FFFFFF"), 2)})
    rows.sort(key=lambda r: (0 if r["properties"] else 1, -r["count"], r["hex"]))
    return rows[:limit]


def _get(url: str, timeout: float = 20.0, cap: int = 4_000_000) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (deck brand intake)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:          # noqa: S310 (user-given brand site)
        blob = r.read(cap)
    return blob.decode("utf-8", "replace")


def fetch_css(url: str, max_sheets: int = 15) -> tuple[list[str], list[str]]:
    """(css texts, urls read): the page's <style> blocks, inline style attributes, its linked stylesheets and their
    first-level @imports. A sheet that cannot be read is skipped and named in the urls list with '(failed)'."""
    html = _get(url)
    texts = [m.group(1) for m in _STYLE.finditer(html)]
    texts += re.findall(r"""style\s*=\s*"([^"]*)\"""", html, re.I)
    sheets = []
    for tag_ in _LINK.findall(html):
        attrs = {k.lower(): v.strip("'\"") for k, v in _ATTR.findall(tag_)}
        if "stylesheet" in attrs.get("rel", "").lower() and attrs.get("href"):
            sheets.append(urllib.parse.urljoin(url, attrs["href"]))
    for t in list(texts):
        sheets += [urllib.parse.urljoin(url, u) for u in _IMPORT.findall(t)]
    read, done = [url], set()
    for s in sheets:
        if s in done or len(done) >= max_sheets:
            continue
        done.add(s)
        try:
            css = _get(s)
        except Exception:                                            # noqa: BLE001 (report, never fail the intake)
            read.append(s + " (failed)")
            continue
        texts.append(css)
        read.append(s)
        for u in _IMPORT.findall(css):
            u = urllib.parse.urljoin(s, u)
            if u not in done and len(done) < max_sheets:
                done.add(u)
                try:
                    texts.append(_get(u))
                    read.append(u)
                except Exception:                                    # noqa: BLE001
                    read.append(u + " (failed)")
    return texts, read


# ------------------------------------------------------------------ logo

def copy_logo(src, out_dir) -> dict:
    """Copy an SVG or PNG logo into out_dir; return its record {file, sha256, format}."""
    p = Path(src).expanduser()
    if not p.is_file():
        raise BrandRefused("logo", need="an existing .svg or .png file", have=str(p))
    fmt = LOGO_EXT.get(p.suffix.lower())
    if fmt is None:
        raise BrandRefused("logo %s" % p.name, need="an .svg or .png file", have=p.suffix or "no extension",
                           hint="export the logo as SVG (preferred) or a PNG at least twice its displayed size")
    blob = p.read_bytes()
    if fmt == "svg":
        from .icons import svg_size
        svg_size(blob)                                   # refuses a malformed SVG now, not at build time
    elif blob[:8] != b"\x89PNG\r\n\x1a\n":
        raise BrandRefused("logo %s" % p.name, need="PNG bytes", have="not a PNG")
    out = Path(out_dir) / ("logo." + fmt)
    out.parent.mkdir(parents=True, exist_ok=True)
    if p.resolve() != out.resolve():
        shutil.copyfile(p, out)
    return {"file": out.name, "sha256": hashlib.sha256(blob).hexdigest(), "format": fmt, "source": p.name}


def logo_path(theme) -> Path:
    """The logo a client theme records (brand.logo), next to the theme file, verified by its sha256."""
    data = getattr(theme, "data", None) or {}
    rec = (data.get("brand") or {}).get("logo")
    if not rec or not getattr(theme, "path", None):
        raise BrandRefused("theme %s logo" % getattr(theme, "name", "?"), need="a brand.logo record and a theme file",
                           have="none", hint="run scripts/brand.py with --logo")
    p = Path(theme.path).resolve().parent / rec["file"]
    if not p.is_file():
        raise BrandRefused("logo %s" % p, need="the file", have="missing")
    got = hashlib.sha256(p.read_bytes()).hexdigest()
    if got != rec["sha256"]:
        raise BrandRefused("logo %s" % p.name, need="sha256 %s" % rec["sha256"][:12], have=got[:12],
                           hint="the logo changed since the theme was made; rerun scripts/brand.py --logo")
    return p


def _slide_archetype(slide) -> str | None:
    from .read.ns import NS
    from .tag import parse
    csld = slide._element.find("{%s}cSld" % NS["p"])
    pv = parse(csld.get("name") if csld is not None else None)
    return pv[0] if pv else None


def _logo_size(blob: bytes, fmt: str) -> tuple[float, float]:
    if fmt == "svg":
        from .icons import svg_size
        return svg_size(blob)
    from .icons import _png_size
    return _png_size(blob)


def _read_logo(src) -> tuple[bytes, str]:
    if isinstance(src, (str, Path)):
        p = Path(src).expanduser()
        fmt = LOGO_EXT.get(p.suffix.lower())
        if fmt is None or not p.is_file():
            raise UnsupportedPart("logo %s" % p, need="an existing .svg or .png file", have=p.suffix or "missing")
        return p.read_bytes(), fmt
    raise UnsupportedPart("logo", need="a path to an .svg or .png", have=type(src).__name__)


def _place(slide, blob, fmt, box: Box, name: str, alt: str):
    from .icons import _check_raster, _fit, _png_size, _set_nv, svg_picture
    if fmt == "svg":
        return svg_picture(slide, blob, box, "auto", name=name, alt=alt)
    pw, ph = _png_size(blob)
    b = _fit(box, pw, ph)
    _check_raster("logo %s" % name, pw, b)
    x, y, w, h = b.emu
    pic = slide.shapes.add_picture(io.BytesIO(blob), x, y, w, h)
    _set_nv(pic, name, alt)
    ooxml.finish(pic)
    return pic


@ooxml.transactional
def lockup(slide, box: Box, client_logo, firm_logo=None, *, theme, name: str, firm_name: str = "Sigmoid"):
    """The client logo, optionally followed by the firm logo after a hairline divider, left-aligned in box and
    centred on its middle line. Each logo keeps its aspect at the box height (both shrink together when the pair is
    wider than the box). Refused unless the slide is tagged cover or closing. Returns {client, divider, firm, w}."""
    from . import prims
    arch = _slide_archetype(slide)
    if arch not in LOCKUP_TAGS:
        raise GeometryError("logo lockup", need="a slide tagged cover or closing", have=arch or "an untagged slide",
                            hint="a client logo belongs on the cover lockup only (DECISIONS structure); tag the "
                                 "slide first, and keep logos off content slides (gate P09 fails footer logos)")
    client = " ".join(str(name or "").split())
    if not client:
        raise GeometryError("logo lockup", need="the client's name for the alt text", have=repr(name))
    cb, cf = _read_logo(client_logo)
    cw, ch = _logo_size(cb, cf)
    parts = [(cb, cf, cw / ch)]
    if firm_logo is not None:
        fb, ff = _read_logo(firm_logo)
        fw, fh = _logo_size(fb, ff)
        parts.append((fb, ff, fw / fh))
    h = box.h
    gap = max(0.18, 0.4 * h)
    widths = [h * ar for _, _, ar in parts]
    total = sum(widths) + (2 * gap if len(parts) == 2 else 0)
    if total > box.w:
        k = box.w / total
        h, gap, widths = h * k, gap * k, [w * k for w in widths]
    y = box.y + (box.h - h) / 2
    out = {"client": None, "divider": None, "firm": None, "w": sum(widths) + (2 * gap if len(parts) == 2 else 0)}
    out["client"] = _place(slide, cb, cf, Box(box.x, y, widths[0], h), "logo.client", "%s logo" % client)
    if len(parts) == 2:
        dx = box.x + widths[0] + gap
        out["divider"] = prims.hairline(slide, (dx, box.y), (dx, box.b), role="hairline", name="logo.divider",
                                        theme=theme)
        fb, ff, _ = parts[1]
        out["firm"] = _place(slide, fb, ff, Box(dx + gap, y, widths[1], h), "logo.firm",
                             "%s logo" % " ".join(str(firm_name).split()))
    return out


__all__ = ["make_theme", "check_text", "css_candidates", "fetch_css", "font_choice", "font_installed", "copy_logo",
           "logo_path", "lockup", "norm_hex", "derive_dk2", "derive_lt2", "BrandRefused", "LOCKUP_TAGS", "SIGMOID"]
