"""Effective text properties through PowerPoint's inheritance chain.

Most to least specific: run rPr, shape lstStyle, layout placeholder lstStyle, master placeholder
lstStyle, master txStyles by placeholder type (placeholders only), p:style fontRef, presentation
defaultTextStyle. pPr/defRPr is not part of PowerPoint's run inheritance and is not consulted.
normAutofit fontScale (shape, else layout placeholder, else master placeholder) gives size_rendered_pt.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from lxml import etree

from .colour import ColourCtx, first_colour, resolve
from .ns import A, first_child, local
from .textmetrics import para_text, token_spans, words

DEFAULT_SIZE = 18.0
BODY_DEFAULTS = {"lIns": 91440, "tIns": 45720, "rIns": 91440, "bIns": 45720}


def lvl_def(lst, lvl: int, child: str = "defRPr"):
    if lst is None:
        return None
    p = lst.find(A("lvl%dpPr" % lvl))
    if p is None:
        return None
    return p if child is None else p.find(A(child))


def _fontref_rpr(style):
    """p:style fontRef as a synthetic rPr carrying its face (+mj-lt/+mn-lt) and colour."""
    if style is None:
        return None
    fr = style.find(A("fontRef"))
    if fr is None:
        return None
    rpr = etree.Element(A("rPr"))
    idx = fr.get("idx", "minor")
    if idx in ("major", "minor"):
        etree.SubElement(rpr, A("latin")).set("typeface", "+mj-lt" if idx == "major" else "+mn-lt")
    c = first_colour(fr)
    if c is not None:
        sf = etree.SubElement(rpr, A("solidFill"))
        sf.append(_copy(c))
    return rpr


def _copy(el):
    return etree.fromstring(etree.tostring(el))


@dataclass
class TextCtx:
    colour: ColourCtx
    theme_major: str | None
    theme_minor: str | None
    pres_default: object = None
    lst_style: object = None          # shape txBody/lstStyle
    ph_type: str | None = None
    layout_ph_lst: object = None
    master_ph_lst: object = None
    master_txstyle: object = None
    fontref_rpr: object = None
    extra_rpr: object = None          # table style tcTxStyle as a synthetic rPr, between shape and defaults
    font_scale: float = 1.0
    ln_spc_reduction: float = 0.0
    is_title_ph: bool = False
    _chains: dict = field(default_factory=dict)

    def chain(self, lvl: int, child: str = "defRPr"):
        key = (lvl, child)
        c = self._chains.get(key)
        if c is not None:
            return c
        out = [("shape_lst", lvl_def(self.lst_style, lvl, child))]
        if self.ph_type is not None:
            out += [("layout_ph", lvl_def(self.layout_ph_lst, lvl, child)),
                    ("master_ph", lvl_def(self.master_ph_lst, lvl, child)),
                    ("master_txStyles", lvl_def(self.master_txstyle, lvl, child))]
        if child == "defRPr":
            out.append(("table_style", self.extra_rpr))
            out.append(("style_fontRef", self.fontref_rpr))
        out.append(("pres_default", lvl_def(self.pres_default, lvl, child)))
        c = [(s, e) for s, e in out if e is not None]
        self._chains[key] = c
        return c


def _face(name: str | None, tc: TextCtx) -> str | None:
    if name is None:
        return None
    if name.startswith("+mj"):
        return tc.theme_major
    if name.startswith("+mn"):
        return tc.theme_minor
    return name


def run_props(run, lvl: int, tc: TextCtx) -> dict:
    rpr = run.find(A("rPr"))
    ch = ([("run", rpr)] if rpr is not None else []) + tc.chain(lvl)

    def pick(attr):
        for s, e in ch:
            v = e.get(attr)
            if v is not None:
                return v, s
        return None, "fallback"

    sz, sz_src = pick("sz")
    size = int(sz) / 100.0 if sz else DEFAULT_SIZE
    face, face_src = None, "fallback"
    for s, e in ch:
        lat = e.find(A("latin"))
        if lat is not None and lat.get("typeface"):
            face, face_src = lat.get("typeface"), s
            break
    requested = face
    if face is None:
        face = tc.theme_major if tc.is_title_ph else tc.theme_minor
        face_src = "theme-major" if tc.is_title_ph else "theme-minor"
    elif face.startswith("+mj"):
        face, face_src = tc.theme_major, face_src + ":theme-major"
    elif face.startswith("+mn"):
        face, face_src = tc.theme_minor, face_src + ":theme-minor"
    col, col_src = None, None
    for s, e in ch:
        f = first_child(e, ("solidFill", "gradFill", "noFill", "pattFill"))
        if f is None:
            continue
        t = local(f)
        if t == "solidFill":
            c = first_colour(f)
            if c is None:
                continue
            col = resolve(c, tc.colour)
        elif t == "gradFill":
            gs = f.find(A("gsLst"))
            c = first_colour(gs[0]) if gs is not None and len(gs) else None
            if c is None:
                continue
            col = resolve(c, tc.colour)
            col["src"] = "grad-first-stop " + col["src"]
        elif t == "noFill":
            col = {"hex": None, "alpha": 0.0, "src": "noFill", "approx": False}
        else:
            c = first_colour(f.find(A("fgClr")))
            if c is None:
                continue
            col = resolve(c, tc.colour)
        col_src = s
        break
    if col is None:
        col = resolve(etree.Element(A("schemeClr"), val="tx1"), tc.colour)
        col_src = "tx1"
    b, _ = pick("b")
    i, _ = pick("i")
    u, _ = pick("u")
    cap, _ = pick("cap")
    baseline, _ = pick("baseline")
    hl = rpr is not None and rpr.find(A("hlinkClick")) is not None
    return dict(size_pt=size, size_src=sz_src, size_rendered_pt=round(size * tc.font_scale, 2),
                bold=b in ("1", "true"), italic=i in ("1", "true"),
                underline=bool(u) and u != "none", caps=cap or "none",
                font=face, font_src=face_src, font_requested=requested,
                hex=col["hex"], alpha=col.get("alpha", 1.0),
                colour_src="%s:%s" % (col_src, col["src"]) if col_src != "tx1" else "default:" + col["src"],
                baseline=int(baseline) / 1000.0 if baseline else 0, hlink=hl)


def _ppr_pick(ppr, lvl: int, tc: TextCtx, names, attr=None):
    """First pPr-level child (or attribute) along pPr then the lvlNpPr chain."""
    ch = ([("para", ppr)] if ppr is not None else []) + tc.chain(lvl, None)
    for s, e in ch:
        if attr is not None:
            v = e.get(attr)
            if v is not None:
                return v, s
        else:
            c = first_child(e, names)
            if c is not None:
                return c, s
    return None, None


def _spacing(el) -> tuple[str, float] | None:
    if el is None:
        return None
    pct, pts = el.find(A("spcPct")), el.find(A("spcPts"))
    if pct is not None:
        return ("pct", int(pct.get("val", "100000")) / 1000.0)
    if pts is not None:
        return ("pt", int(pts.get("val", "0")) / 100.0)
    return None


def para_props(p, tc: TextCtx) -> dict:
    """Paragraph level, alignment, bullet, left margin and first-line indent (mar_l_in, indent_in: pPr marL and
    indent through the lvlNpPr chain, 0 when unset), and spacing."""
    ppr = p.find(A("pPr"))
    lvl = int(ppr.get("lvl", "0")) + 1 if ppr is not None and ppr.get("lvl") else 1
    algn, _ = _ppr_pick(ppr, lvl, tc, None, "algn")
    bu, _ = _ppr_pick(ppr, lvl, tc, ("buNone", "buChar", "buAutoNum", "buBlip"))
    bullet = "none"
    if bu is not None:
        bullet = {"buNone": "none", "buChar": "char", "buAutoNum": "auto", "buBlip": "picture"}[local(bu)]
        if bullet == "char":
            bullet = "char:" + (bu.get("char") or "")
    out = {"lvl": lvl - 1, "algn": algn or "l", "bullet": bullet}
    for key, attr in (("mar_l_in", "marL"), ("indent_in", "indent")):
        v, _ = _ppr_pick(ppr, lvl, tc, None, attr)
        try:
            out[key] = round(int(v) / 914400.0, 4) if v is not None else 0.0
        except ValueError:
            out[key] = 0.0
    for key, tag in (("ln_spc", "lnSpc"), ("spc_bef", "spcBef"), ("spc_aft", "spcAft")):
        el, _ = _ppr_pick(ppr, lvl, tc, (tag,))
        sp = _spacing(el)
        if key == "ln_spc":
            out["ln_spc_pct"] = sp[1] if sp and sp[0] == "pct" else 100.0
            if sp and sp[0] == "pt":
                out["ln_spc_pt"] = sp[1]
        else:
            out[key + "_pt"] = sp[1] if sp and sp[0] == "pt" else 0.0
            if sp and sp[0] == "pct":
                out[key + "_pct"] = sp[1]
    return out, lvl


def body_props(body_prs, tc: TextCtx) -> dict:
    """body_prs: bodyPr elements most specific first (shape, layout ph, master ph)."""
    bp = [b for b in body_prs if b is not None]

    def attr(name, default=None):
        for b in bp:
            if b.get(name) is not None:
                return b.get(name)
        return default

    autofit, scale, red = "none", 1.0, 0.0
    for b in bp:
        a = first_child(b, ("noAutofit", "spAutoFit", "normAutofit"))
        if a is None:
            continue
        n = local(a)
        if n == "normAutofit":
            autofit = "norm"
            scale = int(a.get("fontScale", "100000")) / 100000.0
            red = int(a.get("lnSpcReduction", "0")) / 100000.0
        elif n == "spAutoFit":
            autofit = "shape"
        break
    return {"anchor": attr("anchor", "t"), "wrap": attr("wrap", "square"), "autofit": autofit,
            "font_scale": round(scale, 4), "ln_spc_reduction": round(red, 4),
            "insets_in": [round(int(attr(k, str(BODY_DEFAULTS[k]))) / 914400.0, 4)
                          for k in ("lIns", "tIns", "rIns", "bIns")],
            "vert": attr("vert", "horz"), "cols": int(attr("numCol", "1"))}


def read_text(txBody, tc: TextCtx, body: dict) -> dict | None:
    """txBody to the leaf's text block: paragraphs with effective runs and summary measures. Each paragraph
    carries end_pt, its endParaRPr size in points (None when unset): the height an empty paragraph takes."""
    if txBody is None:
        return None
    paras = []
    chars_by_size: dict[float, int] = {}
    fonts: dict[str, int] = {}
    colours: dict[str, int] = {}
    font_words: dict[str, int] = {}
    bold_chars = total_chars = 0
    sizes = []
    for p in txBody.findall(A("p")):
        pp, lvl = para_props(p, tc)
        runs = []
        pos = 0
        run_spans = []
        for n in p:
            t = local(n)
            if t in ("r", "fld"):
                tt = n.find(A("t"))
                text = (tt.text or "") if tt is not None else ""
                rp = run_props(n, lvl, tc)
                rp = {"t": text, **rp}
                if t == "fld":
                    rp["field"] = n.get("type", "")
                runs.append(rp)
                run_spans.append((pos, pos + len(text), rp))
                pos += len(text)
                if text.strip():
                    nch = len(text.strip())
                    total_chars += nch
                    sizes.append(rp["size_rendered_pt"])
                    chars_by_size[rp["size_rendered_pt"]] = chars_by_size.get(rp["size_rendered_pt"], 0) + nch
                    if rp["font"]:
                        fonts[rp["font"]] = fonts.get(rp["font"], 0) + nch
                    if rp["hex"]:
                        colours[rp["hex"]] = colours.get(rp["hex"], 0) + nch
                    if rp["bold"]:
                        bold_chars += nch
            elif t == "br":
                pos += 1
        end = p.find(A("endParaRPr"))
        try:
            pp["end_pt"] = int(end.get("sz")) / 100.0 if end is not None and end.get("sz") else None
        except ValueError:
            pp["end_pt"] = None
        text = para_text(p)
        w = words(text)
        # words attributed to the requested face of the run holding each token's first character
        if w:
            for s0, _s1 in token_spans(text):
                for a, b, rp in run_spans:
                    if a <= s0 < b:
                        f = rp["font"] or "?"
                        font_words[f] = font_words.get(f, 0) + 1
                        break
        paras.append({"text": text, **pp, "words": w, "runs": runs})
    full = "\n".join(p["text"] for p in paras)
    nonblank_runs = [r for p in paras for r in p["runs"] if r["t"].strip()]
    out = {"body": body, "paragraphs": paras, "text": full, "words": sum(p["words"] for p in paras),
           "chars": len(full.replace("\n", "")), "fonts": fonts, "colours": colours, "font_words": font_words,
           "bold_share": round(bold_chars / total_chars, 3) if total_chars else 0.0}
    if sizes:
        dom = max(chars_by_size.items(), key=lambda kv: (kv[1], kv[0]))[0]
        out["size"] = {"dominant_pt": dom, "min_pt": min(sizes), "max_pt": max(sizes)}
    else:
        out["size"] = None
    out["two_tone"] = len(colours) >= 2
    out["runs_nonblank"] = len(nonblank_runs)
    return out
