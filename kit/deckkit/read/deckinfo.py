"""deck_info: the deck@1 dict (masters, themes, txStyles, persistent chrome, layouts, dividers, fonts)."""
from __future__ import annotations

import re

from .colour import resolve
from .ns import A, P, local
from .opc import DeckRead, PhIndex
from .textmetrics import para_text, words
from .xform import read_xfrm

SCHEMA = "deck@1"
STATUS_TITLE = {
    "appendix": re.compile(r"^\s*(?:appendix|appendices|annex(?:ure)?|back-?up(?: slides)?|supporting slides|"
                           r"additional (?:slides|material))\s*$", re.I),
    "graveyard": re.compile(r"^\s*(?:graveyard|slide graveyard|parking lot|unused(?: slides)?|archive(?:d slides)?|"
                            r"old slides|spare slides|deprecated)\s*$", re.I),
}
AGENDA = re.compile(r"^\s*(?:agenda|contents|table of contents|today'?s agenda|what we will cover)\b", re.I)
CONFIDENTIAL = re.compile(r"confidential|classified|proprietary|internal use", re.I)


# ------------------------------------------------------------------ quick text access (no geometry)

def _slide_paragraph_texts(deck: DeckRead, index1: int) -> list[str]:
    root = deck.xml(deck.slide_part(index1))
    out = []
    for p in root.iter(A("p")):
        t = para_text(p).strip()
        if t:
            out.append(t)
    return out


def _real(t: str) -> bool:
    return words(t) > 0 and not re.fullmatch(r"(?i)x+", t.strip())


def status_ranges(deck: DeckRead) -> dict:
    """main/appendix/graveyard as 1-based inclusive ranges. A status divider opens its section; the divider
    itself stays in the preceding scope (so a deck whose graveyard divider is slide 104 has 105-end)."""
    c = deck.cache.get("status_ranges")
    if c is not None:
        return c
    n = deck.n_slides
    marks = []
    for i in range(1, n + 1):
        texts = [t for t in _slide_paragraph_texts(deck, i) if _real(t)]
        if not texts or sum(words(t) for t in texts) > 8:
            continue
        for k, rx in STATUS_TITLE.items():
            if any(rx.match(t) for t in texts):
                marks.append((i, k))
                break
    ranges = {"main": [], "appendix": [], "graveyard": []}
    member = {}
    for j, (start, kind) in enumerate(marks):
        end = marks[j + 1][0] - 1 if j + 1 < len(marks) else n
        if start + 1 <= end:
            ranges[kind].append([start + 1, end])
            for k in range(start + 1, end + 1):
                member[k] = kind
    run = None
    for i in range(1, n + 1):      # main: every slide outside a status section, dividers included
        if i in member:
            run = None
            continue
        if run is None:
            run = [i, i]
            ranges["main"].append(run)
        else:
            run[1] = i
    deck.cache["status_ranges"] = ranges
    deck.cache["status_dividers"] = marks
    return ranges


# ------------------------------------------------------------------ font words (light pass, cached)

def font_words(deck: DeckRead, include_chrome: bool = False) -> dict:
    key = "font_words_chrome" if include_chrome else "font_words"
    c = deck.cache.get(key)
    if c is not None:
        return c
    from .walk import read_slide
    content: dict = {}
    chrome: dict = {}
    for i in range(1, deck.n_slides + 1):
        s = read_slide(deck, i, light=True, dominant_face="-")
        for L in s["shapes"]:
            for f, n in ((L.get("text") or {}).get("font_words") or {}).items():
                content[f] = content.get(f, 0) + n
        for L in s["chrome"]:
            for f, n in ((L.get("text") or {}).get("font_words") or {}).items():
                chrome[f] = chrome.get(f, 0) + n
    both = dict(content)
    for f, n in chrome.items():
        both[f] = both.get(f, 0) + n
    deck.cache["font_words"] = dict(sorted(content.items(), key=lambda kv: -kv[1]))
    deck.cache["font_words_chrome"] = dict(sorted(both.items(), key=lambda kv: -kv[1]))
    return deck.cache[key]


def dominant_face(deck: DeckRead) -> str | None:
    fw = font_words(deck)
    return next(iter(fw), None)


# ------------------------------------------------------------------ deck_info

def _txstyle_summary(lst, cctx, major, minor) -> dict:
    out = {}
    if lst is None:
        return out
    for lv in range(1, 10):
        p = lst.find(A("lvl%dpPr" % lv))
        d = p.find(A("defRPr")) if p is not None else None
        if d is None:
            continue
        rec = {}
        if d.get("sz"):
            rec["size_pt"] = int(d.get("sz")) / 100.0
        lat = d.find(A("latin"))
        if lat is not None and lat.get("typeface"):
            f = lat.get("typeface")
            rec["font"] = major if f.startswith("+mj") else minor if f.startswith("+mn") else f
        if d.get("b") is not None:
            rec["bold"] = d.get("b") in ("1", "true")
        sf = d.find(A("solidFill"))
        if sf is not None and len(sf) and cctx is not None:
            rec["hex"] = resolve(sf[0], cctx)["hex"]
        if rec:
            out["lvl%d" % lv] = rec
    return out


def _fmt_summary(lst, kind: str) -> list:
    out = []
    for e in lst:
        n = local(e)
        if kind == "ln":
            fill = next((local(c) for c in e if local(c) in ("noFill", "solidFill", "gradFill", "pattFill")), None)
            out.append({"w_pt": round(int(e.get("w", "9525")) / 12700.0, 3), "fill": fill})
        elif kind == "effect":
            el = e.find(A("effectLst"))
            out.append({"effects": [local(c) for c in el] if el is not None else []})
        else:
            out.append({"type": n})
    return out


def _placeholders(root) -> list:
    out = []
    for info, el in PhIndex(root).items:
        sp = el.find(P("spPr"))
        r = read_xfrm(sp.find(A("xfrm")) if sp is not None else None)
        bbox = None
        if r is not None:
            bbox = {"x_in": round(r["x"] / 914400, 3), "y_in": round(r["y"] / 914400, 3),
                    "w_in": round(r["w"] / 914400, 3), "h_in": round(r["h"] / 914400, 3)}
        out.append({"type": info["type"], "idx": info["idx"], "bbox": bbox})
    return out


def deck_info(deck: DeckRead, *, deck_id: str | None = None, with_fonts: bool = True) -> dict:
    from .walk import Walker, chrome_leaves
    n = deck.n_slides
    hidden = [i for i in range(1, n + 1) if deck.xml(deck.slide_part(i)).get("show") in ("0", "false")]
    layout_use: dict = {}
    master_use: dict = {}
    slide_layout = {}
    for i in range(1, n + 1):
        lp = deck.layout_part_of(deck.slide_part(i))
        slide_layout[i] = lp
        layout_use[lp] = layout_use.get(lp, 0) + 1
        if lp:
            mp = deck.layout(lp).master_part
            master_use[mp] = master_use.get(mp, 0) + 1
    # origin: Google Slides exports name shapes "Google Shape;N;..."
    total = google = 0
    for i in range(1, n + 1):
        for c in deck.xml(deck.slide_part(i)).iter(P("cNvPr")):
            total += 1
            if c.get("name", "").startswith("Google Shape;"):
                google += 1
    share = round(google / total, 3) if total else 0.0
    origin = {"google_shape_share": share,
              "guess": "google-export" if share >= 0.5 else ("mixed" if share >= 0.05 else "powerpoint")}
    masters = []
    chrome_by_slide: dict = {}
    for mp in deck.master_parts:
        mi = deck.master(mp)
        cctx = mi.colour
        major, minor = mi.theme["fonts"]["major"], mi.theme["fonts"]["minor"]
        # persistent master leaves (rendered when a layout shows master shapes)
        persistent = []
        layouts = []
        for lp in deck.layouts_of_master(mp):
            li = deck.layout(lp)
            layouts.append({"part": "/" + lp, "name": li.name, "type": li.type, "slides_using": layout_use.get(lp, 0),
                            "show_master_sp": li.show_master_sp, "persistent": [],
                            "placeholders": _placeholders(li.root)})
        masters.append({"part": "/" + mp, "slides_using": master_use.get(mp, 0), "clrMap": mi.clrmap,
                        "theme": {"part": "/" + mi.theme_part if mi.theme_part else None, "name": mi.theme["name"],
                                  "colors": mi.theme["colors"], "fonts": mi.theme["fonts"],
                                  "fill_styles": _fmt_summary(mi.theme["fmt"]["fill"], "fill"),
                                  "line_styles": _fmt_summary(mi.theme["fmt"]["ln"], "ln"),
                                  "effect_styles": _fmt_summary(mi.theme["fmt"]["effect"], "effect"),
                                  "bg_fill_styles": _fmt_summary(mi.theme["fmt"]["bgfill"], "fill")},
                        "txStyles": {k.replace("Style", ""): _txstyle_summary(v, cctx, major, minor)
                                     for k, v in mi.txstyles.items()},
                        "persistent": persistent, "layouts": layouts,
                        "placeholders": _placeholders(mi.root)})
    # persistent leaves: walk master and layout spTrees once per layout, through a slide that uses it
    first_slide_of_layout = {}
    for i in range(1, n + 1):
        first_slide_of_layout.setdefault(slide_layout[i], i)
    for m in masters:
        mp = m["part"].lstrip("/")
        mi = deck.master(mp)
        for lay in m["layouts"]:
            lp = lay["part"].lstrip("/")
            i = first_slide_of_layout.get(lp)
            if i is None:
                continue
            w = Walker(deck, deck.slide_part(i), light=True)
            w.layer = "chrome"
            tree = deck.layout(lp).root.find(P("cSld") + "/" + P("spTree"))
            if tree is not None:
                w.walk(tree, lp, ph_ok=False)
            lay["persistent"] = [_brief(L, w) for L in w.leaves]
            if not m["persistent"] and deck.layout(lp).show_master_sp:
                w2 = Walker(deck, deck.slide_part(i), light=True)
                w2.layer = "chrome"
                t2 = mi.root.find(P("cSld") + "/" + P("spTree"))
                if t2 is not None:
                    w2.walk(t2, mp, ph_ok=False)
                m["persistent"] = [_brief(L, w2) for L in w2.leaves]
    # chrome summary per slide (text, pictures, bands) from the rendered chrome
    summary = {"confidentiality text": [], "logo picture": [], "bottom band": [], "page number": []}
    for i in range(1, n + 1):
        sp = deck.slide_part(i)
        root = deck.xml(sp)
        show = root.get("showMasterSp") not in ("0", "false")
        w = Walker(deck, sp, light=True)
        ch = chrome_leaves(deck, w.layout_part, show, True, w) if w.li else []
        for L in ch:
            t = (L.get("text") or {}).get("text", "") if L.get("text") else ""
            b = L["bbox"]
            if t and CONFIDENTIAL.search(t):
                summary["confidentiality text"].append(i)
            if L["kind"] == "pic":
                summary["logo picture"].append(i)
            if L["kind"] == "sp" and (L.get("fill") or {}).get("type") not in (None, "none") and \
                    b["y_in"] > 0.8 * deck.h_in and b["w_in"] >= 0.5 * deck.w_in:
                summary["bottom band"].append(i)
            if L["kind"] == "sp" and re.search(r"<#>|slidenum", " ".join(
                    r.get("field", "") for p in ((L.get("text") or {}).get("paragraphs") or []) for r in p["runs"])):
                summary["page number"].append(i)
        # slide-level page number fields
        for fld in root.iter(A("fld")):
            if (fld.get("type") or "") == "slidenum":
                summary["page number"].append(i)
                break
    chrome_summary = [{"what": k, "slides": sorted(set(v))} for k, v in summary.items() if v]
    sr = status_ranges(deck)
    dividers = []
    agenda = []
    for i in range(1, n + 1):
        texts = [t for t in _slide_paragraph_texts(deck, i) if _real(t)]
        wsum = sum(words(t) for t in texts)
        if any(AGENDA.match(t) for t in texts[:2]):
            agenda.append(i)
        if texts and wsum <= 12 and len(texts) <= 3:
            dividers.append({"slide": i, "title": max(texts, key=words)[:80],
                             "status": next((k for j, k in deck.cache.get("status_dividers", []) if j == i), None)})
    dts = {}
    pd = deck.default_text_style
    if pd is not None:
        cctx0 = deck.master(deck.master_parts[0]).colour if deck.master_parts else None
        f0 = deck.master(deck.master_parts[0]).theme["fonts"] if deck.master_parts else {"major": None, "minor": None}
        dts = _txstyle_summary(pd, cctx0, f0["major"], f0["minor"])
    fonts = {"requested_words": font_words(deck) if with_fonts else {},
             "requested_words_with_chrome": font_words(deck, include_chrome=True) if with_fonts else {},
             "embedded": deck.embedded_fonts(), "substitutions": {}}
    return {
        "schema": SCHEMA, "deck_id": deck_id, "file": deck.path.rsplit("/", 1)[-1], "sha256": deck.sha256,
        "bytes": _filesize(deck.path), "slides": n, "hidden": hidden,
        "canvas": {"w_in": round(deck.w_in, 3), "h_in": round(deck.h_in, 3), "kind": deck.canvas_kind,
                   "cx": deck.cx, "cy": deck.cy},
        "origin": origin, "status_ranges": sr, "default_text_style": dts, "masters": masters,
        "layouts_total": sum(len(m["layouts"]) for m in masters),
        "layouts_used": sum(1 for m in masters for l in m["layouts"] if l["slides_using"]),
        "chrome_summary": chrome_summary, "dividers": dividers, "agenda_slides": agenda, "fonts": fonts,
    }


def _filesize(p):
    import os
    return os.path.getsize(p)


def _brief(L: dict, w) -> dict:
    t = L.get("text")
    return {"id": L["id"], "name": L["name"], "kind": L["kind"], "bbox": L["bbox"],
            "fill": L.get("fill"), "text": (t or {}).get("text", "")[:120] if t else "",
            "picture": bool(L["kind"] == "pic")}
