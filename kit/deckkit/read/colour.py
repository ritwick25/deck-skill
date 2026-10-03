"""Colour resolution: theme slots through the effective clrMap, colour transforms, fills, lines, effects.

schemeClr resolves through the effective clrMap (slide override > layout override > master) into the
slide master's own theme. Colour modifiers apply in document order (lumMod precedes lumOff).
p:style fillRef/lnRef/effectRef index into the master theme's fmtScheme, with the reference's own
colour substituted for phClr.
"""
from __future__ import annotations

import colorsys
from dataclasses import dataclass, field

from .ns import A, P, first_child, local
from .xform import EMU_PT

SYS = {"windowText": "000000", "window": "FFFFFF", "btnFace": "F0F0F0", "btnText": "000000",
       "highlight": "0078D7", "highlightText": "FFFFFF", "menu": "F0F0F0", "menuText": "000000",
       "grayText": "6D6D6D", "3dDkShadow": "696969", "3dLight": "E3E3E3", "infoBk": "FFFFE1",
       "infoText": "000000", "scrollBar": "C8C8C8", "background": "000000", "captionText": "000000",
       "activeCaption": "99B4D1", "inactiveCaption": "BFCDDB", "windowFrame": "646464",
       "activeBorder": "B4B4B4", "inactiveBorder": "F4F7FC", "appWorkspace": "ABABAB",
       "btnHighlight": "FFFFFF", "btnShadow": "A0A0A0", "hotLight": "0066CC",
       "gradientActiveCaption": "B9D1EA", "gradientInactiveCaption": "D7E4F2",
       "menuBar": "F0F0F0", "menuHighlight": "3399FF", "inactiveCaptionText": "000000"}

# CSS colour names; OOXML preset names add dk/lt/med prefixes, mapped onto dark/light/medium below.
_CSS = {
    "aliceBlue": "F0F8FF", "antiqueWhite": "FAEBD7", "aqua": "00FFFF", "aquamarine": "7FFFD4", "azure": "F0FFFF",
    "beige": "F5F5DC", "bisque": "FFE4C4", "black": "000000", "blanchedAlmond": "FFEBCD", "blue": "0000FF",
    "blueViolet": "8A2BE2", "brown": "A52A2A", "burlyWood": "DEB887", "cadetBlue": "5F9EA0", "chartreuse": "7FFF00",
    "chocolate": "D2691E", "coral": "FF7F50", "cornflowerBlue": "6495ED", "cornsilk": "FFF8DC", "crimson": "DC143C",
    "cyan": "00FFFF", "darkBlue": "00008B", "darkCyan": "008B8B", "darkGoldenrod": "B8860B", "darkGray": "A9A9A9",
    "darkGrey": "A9A9A9", "darkGreen": "006400", "darkKhaki": "BDB76B", "darkMagenta": "8B008B",
    "darkOliveGreen": "556B2F", "darkOrange": "FF8C00", "darkOrchid": "9932CC", "darkRed": "8B0000",
    "darkSalmon": "E9967A", "darkSeaGreen": "8FBC8F", "darkSlateBlue": "483D8B", "darkSlateGray": "2F4F4F",
    "darkSlateGrey": "2F4F4F", "darkTurquoise": "00CED1", "darkViolet": "9400D3", "deepPink": "FF1493",
    "deepSkyBlue": "00BFFF", "dimGray": "696969", "dimGrey": "696969", "dodgerBlue": "1E90FF",
    "firebrick": "B22222", "floralWhite": "FFFAF0", "forestGreen": "228B22", "fuchsia": "FF00FF",
    "gainsboro": "DCDCDC", "ghostWhite": "F8F8FF", "gold": "FFD700", "goldenrod": "DAA520", "gray": "808080",
    "grey": "808080", "green": "008000", "greenYellow": "ADFF2F", "honeydew": "F0FFF0", "hotPink": "FF69B4",
    "indianRed": "CD5C5C", "indigo": "4B0082", "ivory": "FFFFF0", "khaki": "F0E68C", "lavender": "E6E6FA",
    "lavenderBlush": "FFF0F5", "lawnGreen": "7CFC00", "lemonChiffon": "FFFACD", "lightBlue": "ADD8E6",
    "lightCoral": "F08080", "lightCyan": "E0FFFF", "lightGoldenrodYellow": "FAFAD2", "lightGray": "D3D3D3",
    "lightGrey": "D3D3D3", "lightGreen": "90EE90", "lightPink": "FFB6C1", "lightSalmon": "FFA07A",
    "lightSeaGreen": "20B2AA", "lightSkyBlue": "87CEFA", "lightSlateGray": "778899", "lightSlateGrey": "778899",
    "lightSteelBlue": "B0C4DE", "lightYellow": "FFFFE0", "lime": "00FF00", "limeGreen": "32CD32",
    "linen": "FAF0E6", "magenta": "FF00FF", "maroon": "800000", "mediumAquamarine": "66CDAA",
    "mediumBlue": "0000CD", "mediumOrchid": "BA55D3", "mediumPurple": "9370DB", "mediumSeaGreen": "3CB371",
    "mediumSlateBlue": "7B68EE", "mediumSpringGreen": "00FA9A", "mediumTurquoise": "48D1CC",
    "mediumVioletRed": "C71585", "midnightBlue": "191970", "mintCream": "F5FFFA", "mistyRose": "FFE4E1",
    "moccasin": "FFE4B5", "navajoWhite": "FFDEAD", "navy": "000080", "oldLace": "FDF5E6", "olive": "808000",
    "oliveDrab": "6B8E23", "orange": "FFA500", "orangeRed": "FF4500", "orchid": "DA70D6",
    "paleGoldenrod": "EEE8AA", "paleGreen": "98FB98", "paleTurquoise": "AFEEEE", "paleVioletRed": "DB7093",
    "papayaWhip": "FFEFD5", "peachPuff": "FFDAB9", "peru": "CD853F", "pink": "FFC0CB", "plum": "DDA0DD",
    "powderBlue": "B0E0E6", "purple": "800080", "red": "FF0000", "rosyBrown": "BC8F8F", "royalBlue": "4169E1",
    "saddleBrown": "8B4513", "salmon": "FA8072", "sandyBrown": "F4A460", "seaGreen": "2E8B57",
    "seaShell": "FFF5EE", "sienna": "A0522D", "silver": "C0C0C0", "skyBlue": "87CEEB", "slateBlue": "6A5ACD",
    "slateGray": "708090", "slateGrey": "708090", "snow": "FFFAFA", "springGreen": "00FF7F",
    "steelBlue": "4682B4", "tan": "D2B48C", "teal": "008080", "thistle": "D8BFD8", "tomato": "FF6347",
    "turquoise": "40E0D0", "violet": "EE82EE", "wheat": "F5DEB3", "white": "FFFFFF", "whiteSmoke": "F5F5F5",
    "yellow": "FFFF00", "yellowGreen": "9ACD32",
}


def preset_hex(name: str) -> str | None:
    if name in _CSS:
        return _CSS[name]
    for short, long_ in (("dk", "dark"), ("lt", "light"), ("med", "medium")):
        if name.startswith(short) and name[len(short):len(short) + 1].isupper():
            return _CSS.get(long_ + name[len(short):])
    return None


SLOTS = ("dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6",
         "hlink", "folHlink")
DEFAULT_CLRMAP = {"bg1": "lt1", "tx1": "dk1", "bg2": "lt2", "tx2": "dk2", "accent1": "accent1",
                  "accent2": "accent2", "accent3": "accent3", "accent4": "accent4", "accent5": "accent5",
                  "accent6": "accent6", "hlink": "hlink", "folHlink": "folHlink"}

COLOUR_TAGS = ("srgbClr", "schemeClr", "sysClr", "prstClr", "scrgbClr", "hslClr")
FILL_TAGS = ("noFill", "solidFill", "gradFill", "blipFill", "pattFill", "grpFill")


# ---------------------------------------------------------------- primitives

def s2l(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def l2s(c: float) -> float:
    c = clamp(c)
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def clamp(v: float) -> float:
    return 0.0 if v < 0 else 1.0 if v > 1 else v


def hex2rgb(h: str) -> tuple[float, float, float]:
    h = (h or "000000").strip().lstrip("#")
    if len(h) != 6:
        h = "000000"
    return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0)


def rgb2hex(rgb) -> str:
    return "".join("%02X" % int(round(clamp(c) * 255)) for c in rgb)


def luminance(h: str) -> float:
    r, g, b = (s2l(c) for c in hex2rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


NEUTRAL_CHROMA = 0.10      # a colour whose channels spread less than this (0..1) reads as a grey


def chroma(h: str) -> float:
    """Colourfulness, 0..1: the largest sRGB channel minus the smallest (HSV saturation times value). A pale tint
    such as DDE4F6 sits near 0.1 even though its HSL saturation is high, which is how the eye reads it: grey."""
    rgb = hex2rgb(h)
    return round(max(rgb) - min(rgb), 4)


def is_neutral(h: str, limit: float = NEUTRAL_CHROMA) -> bool:
    """A grey: chroma below `limit`."""
    return bool(h) and chroma(h) < limit


def contrast(h1: str, h2: str) -> float:
    """WCAG 2.x contrast ratio between two hex colours."""
    l1, l2 = luminance(h1), luminance(h2)
    hi, lo = max(l1, l2), min(l1, l2)
    return round((hi + 0.05) / (lo + 0.05), 3)


def _apply(rgb, alpha: float, n: str, raw: int):
    """One modifier. Returns (rgb, alpha, approx)."""
    v = raw / 1e5
    approx = False
    if n == "alpha":
        alpha = v
    elif n == "alphaMod":
        alpha *= v
    elif n == "alphaOff":
        alpha = clamp(alpha + v)
    elif n in ("lumMod", "lumOff", "lum", "satMod", "satOff", "sat", "hueMod", "hueOff", "hue"):
        h, l, s = colorsys.rgb_to_hls(*rgb)
        if n == "lumMod":
            l *= v
        elif n == "lumOff":
            l += v
        elif n == "lum":
            l = v
        elif n == "satMod":
            s *= v
        elif n == "satOff":
            s += v
        elif n == "sat":
            s = v
        elif n == "hueMod":
            h = (h * v) % 1.0
        elif n == "hueOff":
            h = (h + raw / 21600000) % 1.0
        elif n == "hue":
            h = raw / 21600000
        rgb = colorsys.hls_to_rgb(h, clamp(l), clamp(s))
    elif n == "shade":   # toward black in linear light
        rgb = tuple(l2s(s2l(c) * v) for c in rgb)
        approx = True
    elif n == "tint":    # toward white in linear light
        rgb = tuple(l2s(1 - (1 - s2l(c)) * v) for c in rgb)
        approx = True
    elif n == "inv":
        rgb = tuple(1 - c for c in rgb)
    elif n == "gray":
        g = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
        rgb = (g, g, g)
    elif n in ("red", "green", "blue", "redMod", "greenMod", "blueMod", "redOff", "greenOff", "blueOff"):
        i = {"r": 0, "g": 1, "b": 2}[n[0]]
        lin = [s2l(c) for c in rgb]
        if n.endswith("Mod"):
            lin[i] *= v
        elif n.endswith("Off"):
            lin[i] += v
        else:
            lin[i] = v
        rgb = tuple(l2s(clamp(c)) for c in lin)
    elif n == "comp":
        h, l, s = colorsys.rgb_to_hls(*rgb)
        rgb = colorsys.hls_to_rgb((h + 0.5) % 1.0, l, s)
    else:            # gamma, invGamma: recorded, rare
        approx = True
    return rgb, alpha, approx


def apply_mods(hex_: str, mods) -> str:
    """Apply OOXML colour modifiers [(name, raw_val), ...] in order to a hex colour. Writer-side reuse."""
    rgb, alpha = hex2rgb(hex_), 1.0
    for n, raw in mods:
        rgb, alpha, _ = _apply(rgb, alpha, n, int(raw))
    return rgb2hex(rgb)


# ---------------------------------------------------------------- context

@dataclass
class ColourCtx:
    theme_colors: dict           # slot -> hex
    clrmap: dict = field(default_factory=lambda: dict(DEFAULT_CLRMAP))
    fmt: dict = field(default_factory=lambda: {"fill": [], "ln": [], "effect": [], "bgfill": []})
    fonts: dict = field(default_factory=lambda: {"major": None, "minor": None})

    def slot_hex(self, v: str) -> tuple[str, str]:
        slot = self.clrmap.get(v, v)
        h = self.theme_colors.get(slot)
        if h is None:
            h = self.theme_colors.get(v, "000000")
        return h, slot

    def with_clrmap(self, m: dict | None) -> "ColourCtx":
        if not m:
            return self
        return ColourCtx(self.theme_colors, dict(m), self.fmt, self.fonts)


def parse_theme(theme_root) -> dict:
    """Theme part root to {name, colors, fonts, fmt (element lists)}."""
    out = {"name": "", "colors": {}, "fonts": {"major": None, "minor": None},
           "fmt": {"fill": [], "ln": [], "effect": [], "bgfill": []}}
    if theme_root is None:
        return out
    out["name"] = theme_root.get("name", "")
    te = theme_root.find(A("themeElements"))
    if te is None:
        return out
    cs = te.find(A("clrScheme"))
    if cs is not None:
        out["colors_name"] = cs.get("name", "")
        for slot in cs:
            c = first_child(slot, COLOUR_TAGS)
            if c is None:
                continue
            tag = local(c)
            if tag == "srgbClr":
                out["colors"][local(slot)] = c.get("val", "000000").upper()
            elif tag == "sysClr":
                out["colors"][local(slot)] = (c.get("lastClr") or SYS.get(c.get("val"), "000000")).upper()
            else:
                out["colors"][local(slot)] = "000000"
    fs = te.find(A("fontScheme"))
    if fs is not None:
        for k in ("major", "minor"):
            f = fs.find(A(k + "Font"))
            lat = f.find(A("latin")) if f is not None else None
            out["fonts"][k] = lat.get("typeface") if lat is not None else None
    fm = te.find(A("fmtScheme"))
    if fm is not None:
        for key, tag in (("fill", "fillStyleLst"), ("ln", "lnStyleLst"), ("effect", "effectStyleLst"),
                         ("bgfill", "bgFillStyleLst")):
            lst = fm.find(A(tag))
            out["fmt"][key] = list(lst) if lst is not None else []
    return out


def parse_clrmap(el) -> dict | None:
    """p:clrMap, or p:clrMapOvr (overrideClrMapping wins; masterClrMapping means no override)."""
    if el is None:
        return None
    if local(el) == "clrMapOvr":
        o = el.find(A("overrideClrMapping"))
        if o is None:
            return None
        el = o
    m = dict(DEFAULT_CLRMAP)
    for k, v in el.attrib.items():
        m[k] = v
    return m


# ---------------------------------------------------------------- resolution

def resolve(el, ctx: ColourCtx, ph=None) -> dict:
    """A colour element (srgbClr, schemeClr, ...) to {hex, alpha, src, approx}.

    ph is the substituted phClr colour as an (r, g, b) tuple, inside style references.
    """
    tag = local(el)
    approx = False
    if tag == "srgbClr":
        rgb, src = hex2rgb(el.get("val")), "srgb:" + (el.get("val") or "").upper()
    elif tag == "schemeClr":
        v = el.get("val")
        if v == "phClr":
            if ph is None:
                rgb, src, approx = hex2rgb("000000"), "phClr-unbound", True
            else:
                rgb, src = ph, "phClr"
        else:
            h, slot = ctx.slot_hex(v)
            rgb, src = hex2rgb(h), "scheme:%s" % v if slot == v else "scheme:%s>%s" % (v, slot)
    elif tag == "sysClr":
        rgb, src = hex2rgb(el.get("lastClr") or SYS.get(el.get("val"), "000000")), "sys:" + (el.get("val") or "")
    elif tag == "prstClr":
        h = preset_hex(el.get("val", ""))
        approx = h is None
        rgb, src = hex2rgb(h or "000000"), "preset:" + (el.get("val") or "")
    elif tag == "scrgbClr":
        rgb, src = tuple(l2s(int(el.get(k, "0")) / 1e5) for k in "rgb"), "scrgb"
    elif tag == "hslClr":
        rgb = colorsys.hls_to_rgb(int(el.get("hue", "0")) / 21600000 % 1.0, int(el.get("lum", "0")) / 1e5,
                                  int(el.get("sat", "0")) / 1e5)
        src = "hsl"
    else:
        return dict(hex="000000", alpha=1.0, src="unknown:" + tag, approx=True)
    alpha, mods = 1.0, []
    for m in el:
        n = local(m)
        if not n:
            continue
        try:
            raw = int(m.get("val", "0"))
        except ValueError:
            raw = 0
        mods.append("%s:%d" % (n, raw) if m.get("val") is not None else n)
        rgb, alpha, ap_ = _apply(rgb, alpha, n, raw)
        approx = approx or ap_
    return dict(hex=rgb2hex(rgb), alpha=round(alpha, 3), src=" ".join([src] + mods), approx=approx)


def resolve_rgb(el, ctx: ColourCtx, ph=None):
    if el is None:
        return None
    return hex2rgb(resolve(el, ctx, ph)["hex"])


def first_colour(el):
    return first_child(el, COLOUR_TAGS) if el is not None else None


def fill_from(el, ctx: ColourCtx, via: str, ph=None, group_fill=None) -> dict:
    """A fill element (solidFill, gradFill, ...) to a fill record. Gradients carry a 'grad' block."""
    tag = local(el)
    if tag == "noFill":
        return {"type": "none", "via": via}
    if tag == "solidFill":
        c = first_colour(el)
        if c is None:
            return {"type": "solid", "hex": "000000", "alpha": 1.0, "via": via, "src": "empty", "approx": True}
        r = resolve(c, ctx, ph)
        return {"type": "solid", "hex": r["hex"], "alpha": r["alpha"], "via": via, "src": r["src"],
                "approx": r["approx"]}
    if tag == "gradFill":
        stops = []
        gs = el.find(A("gsLst"))
        for g in (gs if gs is not None else []):
            c = first_colour(g)
            if c is None:
                continue
            r = resolve(c, ctx, ph)
            stops.append([round(int(g.get("pos", "0")) / 1e5, 4), r["hex"], r["alpha"]])
        lin, path_ = el.find(A("lin")), el.find(A("path"))
        kind = "lin" if lin is not None or path_ is None else path_.get("path", "circle")
        angle = round(int(lin.get("ang", "0")) / 60000.0, 2) if lin is not None else None
        grad = {"kind": kind, "angle_deg": angle, "stops": stops}
        if stops:
            rgb = [sum(hex2rgb(s[1])[i] for s in stops) / len(stops) for i in range(3)]
            hx, al = rgb2hex(rgb), round(sum(s[2] for s in stops) / len(stops), 3)
        else:
            hx, al = "000000", 1.0
        return {"type": "grad", "hex": hx, "alpha": al, "via": via, "src": "gradient mean", "approx": True,
                "grad": grad}
    if tag == "blipFill":
        return {"type": "picture", "via": via}
    if tag == "pattFill":
        fg = el.find(A("fgClr"))
        bg = el.find(A("bgClr"))
        f = resolve(first_colour(fg), ctx, ph) if first_colour(fg) is not None else None
        b = resolve(first_colour(bg), ctx, ph) if first_colour(bg) is not None else None
        return {"type": "pattern", "prst": el.get("prst"), "hex": f["hex"] if f else "000000",
                "bg_hex": b["hex"] if b else None, "alpha": f["alpha"] if f else 1.0, "via": via,
                "src": "pattern", "approx": True}
    if tag == "grpFill":
        out = dict(group_fill or {"type": "none"})
        out["via"] = "group"
        return out
    return {"type": "none", "via": via}


def _style_ref(style, name: str):
    return style.find(A(name)) if style is not None else None


def resolve_fill(spPr, style, ctx: ColourCtx, group_fill=None) -> dict:
    el = first_child(spPr, FILL_TAGS) if spPr is not None else None
    if el is not None:
        return fill_from(el, ctx, "spPr", group_fill=group_fill)
    ref = _style_ref(style, "fillRef")
    if ref is None:
        return {"type": "none", "via": "default"}
    return fill_ref(ref, ctx)


def fill_ref(ref, ctx: ColourCtx) -> dict:
    """fillRef or bgRef: idx 1..999 into fillStyleLst, 1001.. into bgFillStyleLst; 0 is no fill."""
    try:
        idx = int(ref.get("idx", "0"))
    except ValueError:
        idx = 0
    if idx == 0:
        return {"type": "none", "via": "style:0"}
    ph = resolve_rgb(first_colour(ref), ctx)
    lst = ctx.fmt["fill"] if idx < 1000 else ctx.fmt["bgfill"]
    i = (idx if idx < 1000 else idx - 1000) - 1
    if i < 0 or i >= len(lst):
        return {"type": "none", "via": "style:%d-missing" % idx}
    return fill_from(lst[i], ctx, "style:%d" % idx, ph=ph)


def _ln_fill(ln, ctx, ph):
    return first_child(ln, ("noFill", "solidFill", "gradFill", "pattFill")) if ln is not None else None


def resolve_line(spPr, style, ctx: ColourCtx) -> dict:
    """Effective outline: the lnRef theme line, overridden child by child by spPr/a:ln."""
    ln = spPr.find(A("ln")) if spPr is not None else None
    ref = _style_ref(style, "lnRef")
    base, ph, via = None, None, "spPr"
    if ref is not None:
        try:
            idx = int(ref.get("idx", "0"))
        except ValueError:
            idx = 0
        if 0 < idx <= len(ctx.fmt["ln"]):
            base = ctx.fmt["ln"][idx - 1]
            ph = resolve_rgb(first_colour(ref), ctx)
            via = "style:%d" % idx
    if ln is None and base is None:
        return {"type": "none", "via": "default"}

    def pick_child(names):
        e = first_child(ln, names) if ln is not None else None
        if e is not None:
            return e, "spPr"
        e = first_child(base, names) if base is not None else None
        return (e, via) if e is not None else (None, None)

    fill_el, fill_via = pick_child(("noFill", "solidFill", "gradFill", "pattFill"))
    if fill_el is None or local(fill_el) == "noFill":
        return {"type": "none", "via": fill_via or via}
    f = fill_from(fill_el, ctx, fill_via, ph=ph)
    w = None
    if ln is not None and ln.get("w") is not None:
        w = int(ln.get("w"))
    elif base is not None and base.get("w") is not None:
        w = int(base.get("w"))
    cap = (ln.get("cap") if ln is not None and ln.get("cap") else (base.get("cap") if base is not None else None))
    dash_el, _ = pick_child(("prstDash", "custDash"))
    dash = "solid"
    if dash_el is not None:
        dash = dash_el.get("val", "solid") if local(dash_el) == "prstDash" else "custom"

    def end(name):
        e, _ = pick_child((name,))
        if e is None:
            return {"type": "none"}
        return {"type": e.get("type", "none"), "w": e.get("w", "med"), "len": e.get("len", "med")}

    any_spPr = ln is not None and len(ln) > 0
    return {"type": f["type"], "hex": f.get("hex"), "alpha": f.get("alpha", 1.0),
            "w_pt": round((w if w is not None else 9525) / EMU_PT, 3), "w_explicit": w is not None,
            "dash": dash, "cap": cap or "flat", "head": end("headEnd"), "tail": end("tailEnd"),
            "via": "spPr" if (any_spPr and fill_via == "spPr") else (fill_via or via), "src": f.get("src"),
            "grad": f.get("grad")}


def _effects_from(lst, ctx: ColourCtx, ph, via: str) -> dict:
    out = {"shadow": None, "soft_shadow": False, "inner_shadow": False, "glow": False, "reflection": False,
           "soft_edge": False, "via": via}
    if lst is None:
        return out
    for e in lst:
        n = local(e)
        if n in ("outerShdw", "prstShdw"):
            c = first_colour(e)
            r = resolve(c, ctx, ph) if c is not None else {"hex": "000000", "alpha": 1.0}
            blur = int(e.get("blurRad", "0")) / EMU_PT
            out["shadow"] = {"kind": "outer" if n == "outerShdw" else "preset",
                             "blur_pt": round(blur, 2), "dist_pt": round(int(e.get("dist", "0")) / EMU_PT, 2),
                             "dir_deg": round(int(e.get("dir", "0")) / 60000.0, 1), "hex": r["hex"],
                             "alpha": r["alpha"]}
            out["soft_shadow"] = blur > 0.75     # more than 1px of blur is the soft-shadow tell
        elif n == "innerShdw":
            out["inner_shadow"] = True
        elif n == "glow":
            out["glow"] = True
        elif n == "reflection":
            out["reflection"] = True
        elif n == "softEdge":
            out["soft_edge"] = True
    return out


def resolve_effects(spPr, style, ctx: ColourCtx) -> dict:
    """spPr/effectLst (an empty one means none) wins; else effectRef into effectStyleLst (the ghost-shadow case)."""
    lst = spPr.find(A("effectLst")) if spPr is not None else None
    if lst is not None:
        return _effects_from(lst, ctx, None, "spPr")
    dag = spPr.find(A("effectDag")) if spPr is not None else None
    if dag is not None:
        out = _effects_from(dag, ctx, None, "spPr-dag")
        return out
    ref = _style_ref(style, "effectRef")
    if ref is not None:
        try:
            idx = int(ref.get("idx", "0"))
        except ValueError:
            idx = 0
        if 0 < idx <= len(ctx.fmt["effect"]):
            es = ctx.fmt["effect"][idx - 1]
            ph = resolve_rgb(first_colour(ref), ctx)
            return _effects_from(es.find(A("effectLst")), ctx, ph, "style:%d" % idx)
    return _effects_from(None, ctx, None, "default")


def resolve_background(bg, ctx: ColourCtx) -> dict | None:
    """p:bg (bgPr or bgRef) to a fill record, or None if bg is absent."""
    if bg is None:
        return None
    pr = bg.find(P("bgPr"))
    if pr is not None:
        el = first_child(pr, FILL_TAGS)
        if el is None:
            return {"type": "none", "via": "bgPr"}
        f = fill_from(el, ctx, "bgPr")
        f["via"] = "bgPr"
        return f
    ref = bg.find(P("bgRef"))
    if ref is not None:
        f = fill_ref(ref, ctx)
        f["via"] = "bgRef"
        return f
    return None

