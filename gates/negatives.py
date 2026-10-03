"""Planters for run_all.py --negatives: each copies the golden deck (with its manifest and deck.json), plants
exactly one breakage, and names the one gate that must go red on it. No source file is ever patched.

A planter is plant(dst, work) -> dict | None. dst is the copied deck to mutate in place; work is a scratch
folder it may write into. The dict, when returned, is context for the gate (refs_dir, fingerprints) so a
negative can point a gate at an empty rules file or a test-registered image without touching the real ones.
A planter flagged ctx_only changes only that context; every other planter must change the deck's bytes.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from lxml import etree

GATES_DIR = Path(__file__).resolve().parent
SKILL = GATES_DIR.parent
if str(SKILL / "kit") not in sys.path:
    sys.path.insert(0, str(SKILL / "kit"))

from deckkit.read.ns import NS  # noqa: E402

A = "{%s}" % NS["a"]
P = "{%s}" % NS["p"]
R = "{%s}" % NS["r"]
EMU = 914400
THEME = SKILL / "themes" / "sigmoid.json"
FILLER = ("regional planners review weekly demand figures before the cycle closes and supply confirms "
          "capacity for every product family in each market").split()


@dataclass(frozen=True)
class Planter:
    name: str
    gate: str
    plants: str
    fn: Callable
    expect: str = ""          # the gate must fail WITH this text in a finding, or the plant proved another rule
    ctx_only: bool = False


# ------------------------------------------------------------------ package helpers

def members(p) -> dict:
    with zipfile.ZipFile(p) as z:
        return {i.filename: z.read(i.filename) for i in z.infolist() if not i.is_dir()}


def write(p, m: dict):
    buf = io.BytesIO()
    order = sorted(m, key=lambda n: (n != "[Content_Types].xml", n))
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for n in order:
            z.writestr(n, m[n])
    Path(p).write_bytes(buf.getvalue())


def slide_part(p, i: int) -> str:
    sys.path.insert(0, str(SKILL / "kit"))
    from deckkit.read import open_deck
    with open_deck(str(p)) as d:
        return d.slide_part(i)


def edit_part(p, part: str, fn):
    m = members(p)
    root = etree.fromstring(m[part])
    fn(root)
    m[part] = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    write(p, m)


def edit_slide(p, i: int, fn):
    edit_part(p, slide_part(p, i), fn)


def shape(root, name: str):
    for c in root.iter(P + "cNvPr"):
        if c.get("name") == name:
            return c.getparent().getparent()
    raise KeyError("no shape named %r" % name)


def runs_of(sh):
    return [r for r in sh.iter(A + "r")]


def first_run(sh):
    return runs_of(sh)[0]


def sppr(sh):
    return sh.find(P + "spPr")


def xfrm(sh):
    x = sh.find(".//" + A + "xfrm")
    return x.find(A + "off"), x.find(A + "ext")


def move(sh, dx_in=0.0, dy_in=0.0):
    off, _ = xfrm(sh)
    off.set("x", str(int(off.get("x")) + int(round(dx_in * EMU))))
    off.set("y", str(int(off.get("y")) + int(round(dy_in * EMU))))


def box_in(sh):
    off, ext = xfrm(sh)
    return (int(off.get("x")) / EMU, int(off.get("y")) / EMU, int(ext.get("cx")) / EMU, int(ext.get("cy")) / EMU)


def max_id(root) -> int:
    return max(int(c.get("id")) for c in root.iter(P + "cNvPr"))


def words(n: int) -> str:
    return " ".join(FILLER[k % len(FILLER)] for k in range(n))


def with_prs(p, fn):
    from pptx import Presentation
    prs = Presentation(str(p))
    fn(prs)
    prs.save(str(p))


def theme():
    from deckkit.theme import Theme
    return Theme.load(THEME)


def png(w: int, h: int, seed: int = 1) -> bytes:
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(im)
    for k in range(6):
        x0 = (seed * 37 + k * 53) % max(1, w - w // 4)
        y0 = (seed * 61 + k * 29) % max(1, h - h // 4)
        d.rectangle([x0, y0, x0 + w // 5, y0 + h // 6], fill=(30 + 30 * k, 60 + 20 * k, 140 - 15 * k))
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=False)
    return buf.getvalue()


def add_picture(prs, i, blob, box, name, alt):
    s = prs.slides[i - 1]
    x, y, w, h = (int(round(v * EMU)) for v in box)
    pic = s.shapes.add_picture(io.BytesIO(blob), x, y, w, h)
    c = pic._element.find(".//" + P + "cNvPr")
    c.set("name", name)
    c.set("descr", alt)
    return pic


SVG = (b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">'
       b'<rect x="6" y="6" width="36" height="36" rx="6" fill="#4B5960"/></svg>')


def add_svg(p, i):
    from deckkit import icons
    from deckkit.canvas import Box

    def fn(prs):
        icons.svg_picture(prs.slides[i - 1], SVG, Box(11.0, 6.0, 0.5, 0.5), "auto", name="icon.sample", alt="Sample mark")
    with_prs(p, fn)


# ------------------------------------------------------------------ planters

def p01_75(p, w):
    edit_slide(p, 2, lambda r: first_run(shape(r, "pillar.1.text.2")).find(A + "rPr").set("sz", "750"))


def p01_scale(p, w):
    def fn(r):
        sh = shape(r, "pillar.1.text.2")
        first_run(sh).find(A + "rPr").set("sz", "1000")
        body = sh.find(".//" + A + "bodyPr")
        for c in list(body):
            if etree.QName(c).localname in ("noAutofit", "normAutofit", "spAutoFit"):
                body.remove(c)
        body.insert(0, etree.Element(A + "normAutofit", fontScale="75000"))
    edit_slide(p, 2, fn)


def p02_words(p, w):
    def fn(r):
        t = first_run(shape(r, "pillar.2.text.2")).find(A + "t")
        t.text = t.text + " " + words(40)
    edit_slide(p, 2, fn)


def p03_edge(p, w):
    def fn(r):
        sh = shape(r, "pilot.card")
        x, y, bw, bh = box_in(sh)
        move(sh, dx_in=(13.333 + 0.10) - (x + bw))
    edit_slide(p, 5, fn)


def p04_edge(p, w):
    def fn(r):
        card, body = shape(r, "pillar.1.card"), shape(r, "pillar.1.text.2")
        move(body, dx_in=(box_in(card)[0] + 0.01) - box_in(body)[0])
    edit_slide(p, 2, fn)


def p05_overlap(p, w):
    def fn(r):
        sh = shape(r, "step.1.text.1")
        dup = etree.fromstring(etree.tostring(sh))
        c = dup.find(".//" + P + "cNvPr")
        c.set("id", str(max_id(r) + 1))
        c.set("name", "step.1.text.1.copy")
        move(dup, 0.12, 0.08)          # still inside its card: the collision is text on text, nothing else
        sh.addnext(dup)
    edit_slide(p, 3, fn)


def p06_arrow(p, w):
    edit_slide(p, 3, lambda r: move(shape(r, "step.arrow.1"), dx_in=-0.30))


def p07_gap(p, w):
    def fn(r):
        a, b = shape(r, "pillar.1.card"), shape(r, "pillar.2.card")
        ax, _, aw, _ = box_in(a)
        move(b, dx_in=(ax + aw + 0.02) - box_in(b)[0])
    edit_slide(p, 2, fn)


def p08_topheavy(p, w):
    from deckkit import prims, text
    from deckkit.canvas import Box
    from deckkit.text import Para, Run
    th = theme()

    def fn(prs):
        s = prs.slides[6]
        with prims.use(th):
            prims.card(s, Box(1.0, 4.3, 4.0, 1.8), fill="card", line="hairline", name="heavy.card")
            text.textbox(s, Box(1.2, 4.45, 3.6, 0.25), [Para(Run("Pilot owner", role="ink-deep", bold=True))],
                         "heavy.text.1", th, size=11.0)
            text.textbox(s, Box(1.2, 4.75, 3.6, 0.25), [Para(Run("Named per region", role="ink"))],
                         "heavy.text.2", th, size=11.0)
    with_prs(p, fn)


def _add_text(prs, i, box, t, pt, name, role="ink", bold=False):
    from deckkit import text
    from deckkit.canvas import Box
    from deckkit.text import Para, Run
    th = theme()
    return text.textbox(prs.slides[i - 1], Box(*box), [Para(Run(t, role=role, bold=bold))], name, th, size=pt,
                        require_fit=False)


def p09_band(p, w):
    from deckkit import prims
    from deckkit.canvas import Box
    th = theme()

    def fn(prs):
        s = prs.slides[3]
        with prims.use(th):
            prims.rect(s, Box(0.5, 6.45, 12.4, 0.55), fill="card", name="foot.band")
        _add_text(prs, 4, (0.7, 6.55, 11.0, 0.3), "Shared demand data cuts the planning cycle by more than half",
                  12.0, "foot.text")
    with_prs(p, fn)


def p09_subtitle(p, w):
    with_prs(p, lambda prs: _add_text(prs, 2, (0.5, 0.55, 10.0, 0.3),
                                      "How the regional teams will plan demand together next year", 13.0, "subtitle"))


def p09_pagenum(p, w):
    with_prs(p, lambda prs: _add_text(prs, 3, (11.60, 0.14, 1.20, 0.25), "2 / 34", 10.0, "page.number"))


def p09_pagenum_bare(p, w):
    with_prs(p, lambda prs: _add_text(prs, 3, (12.55, 7.05, 0.35, 0.25), "3", 10.0, "page.number"))


def p10_bar(p, w):
    from deckkit import ooxml, prims
    th = theme()

    def fn(prs):
        s = prs.slides[1]
        body = next(sh for sh in s.shapes if sh.name == "pillar.1.text.2")
        x, y, h = body.left / EMU, body.top / EMU, body.height / EMU
        bar = prims._add(s, "RECTANGLE", __import__("deckkit.canvas", fromlist=["Box"]).Box(x - 0.12, y, 0.05, h),
                         "accent.bar")
        prims.set_fill(bar, "accent", theme=th)
        prims.set_line(bar, None, theme=th)
        prims._drop_text(bar)
        ooxml.finish(bar)
    with_prs(p, fn)


def p11_style(p, w):
    def fn(r):
        sh = shape(r, "pillar.1.card")
        st = etree.fromstring(
            '<p:style xmlns:p="%s" xmlns:a="%s"><a:lnRef idx="2"><a:schemeClr val="accent1"/></a:lnRef>'
            '<a:fillRef idx="3"><a:schemeClr val="accent1"/></a:fillRef><a:effectRef idx="2"><a:schemeClr val="accent1"/>'
            '</a:effectRef><a:fontRef idx="minor"><a:schemeClr val="lt1"/></a:fontRef></p:style>' % (NS["p"], NS["a"]))
        sppr(sh).addnext(st)
    edit_slide(p, 2, fn)


def p11_gradient(p, w):
    def fn(r):
        sp = sppr(shape(r, "pillar.2.card"))
        old = sp.find(A + "solidFill")
        g = etree.fromstring('<a:gradFill xmlns:a="%s"><a:gsLst><a:gs pos="0"><a:schemeClr val="bg1"/></a:gs>'
                             '<a:gs pos="100000"><a:schemeClr val="accent1"/></a:gs></a:gsLst><a:lin ang="5400000"/>'
                             '</a:gradFill>' % NS["a"])
        old.addprevious(g)
        sp.remove(old)
    edit_slide(p, 2, fn)


def p11_shadow(p, w):
    def fn(r):
        lst = sppr(shape(r, "pillar.3.card")).find(A + "effectLst")
        lst.append(etree.fromstring('<a:outerShdw xmlns:a="%s" blurRad="40000" dist="20000" dir="5400000" algn="t">'
                                    '<a:schemeClr val="tx1"><a:alpha val="35000"/></a:schemeClr></a:outerShdw>' % NS["a"]))
    edit_slide(p, 2, fn)


def p11_calibri(p, w):
    def fn(r):
        rpr = first_run(shape(r, "pillar.1.text.2")).find(A + "rPr")
        for tag in ("latin", "ea", "cs"):
            e = rpr.find(A + tag)
            if e is not None:
                e.set("typeface", "Calibri")
    edit_slide(p, 2, fn)


def p12_double(p, w):
    edit_slide(p, 2, lambda r: sppr(shape(r, "pillar.1.card")).find(A + "effectLst").addnext(etree.Element(A + "effectLst")))


def p12_embed(p, w):
    def fn(r):
        sp = sppr(shape(r, "pillar.1.card"))
        old = sp.find(A + "solidFill")
        bf = etree.fromstring('<a:blipFill xmlns:a="%s" xmlns:r="%s"><a:blip r:embed="rId999"/><a:stretch><a:fillRect/>'
                              '</a:stretch></a:blipFill>' % (NS["a"], NS["r"]))
        old.addprevious(bf)
        sp.remove(old)
    edit_slide(p, 2, fn)


def p12_svg_ct(p, w):
    add_svg(p, 4)
    m = members(p)
    ct = etree.fromstring(m["[Content_Types].xml"])
    for e in list(ct):
        if (e.get("Extension") or "").lower() == "svg" or (e.get("PartName") or "").lower().endswith(".svg"):
            ct.remove(e)
    m["[Content_Types].xml"] = etree.tostring(ct, xml_declaration=True, encoding="UTF-8", standalone=True)
    write(p, m)


def p13_words(p, w):
    def fn(r):
        t = first_run(shape(r, "panel.1.text.2")).find(A + "t")
        t.text = t.text + " " + words(300)
    edit_slide(p, 6, fn)


def p14_opener(p, w):
    for i in (2, 3, 4):
        def fn(r):
            t = first_run(shape(r, "title")).find(A + "t")
            t.text = "Regional planning: " + t.text
        edit_slide(p, i, fn)


def p14_body_keyword(p, w):
    def fn(r):
        rn = first_run(shape(r, "pillar.1.text.2"))
        t = rn.find(A + "t")
        head, tail = t.text.split(" ", 1)
        dup = etree.fromstring(etree.tostring(rn))
        t.text = head + " "
        dup.find(A + "t").text = tail
        sf = rn.find(A + "rPr").find(A + "solidFill")
        for c in list(sf):
            sf.remove(c)
        sf.append(etree.Element(A + "schemeClr", val="accent1"))
        rn.addnext(dup)
    edit_slide(p, 2, fn)


def p15_duplicate(p, w):
    def fn(prs):
        src = prs.slides[2]
        dst = prs.slides.add_slide(src.slide_layout)
        tree = dst.shapes._spTree
        for el in list(src.shapes._spTree)[2:]:
            tree.append(etree.fromstring(etree.tostring(el)))
        dst._element.find(P + "cSld").set("name", src._element.find(P + "cSld").get("name"))
        lst = prs.part._element.find(P + "sldIdLst")
        new = lst[-1]
        lst.remove(new)
        lst.insert(3, new)
    with_prs(p, fn)


def p15_tables(p, w):
    """Two copies of the table slide after it, each holding only its title and the table shifted down, tagged
    in two other families, so the run of three tables is the only P15 rule they break."""
    def fn(prs):
        lst = prs.part._element.find(P + "sldIdLst")
        src = prs.slides[4]
        keep = [el for el in list(src.shapes._spTree)[2:]
                if el.find(".//" + P + "cNvPr").get("name") in ("title", "readiness.table")]
        for k, (tag_, dy) in enumerate((("options:table-a", 1.6), ("governance:table-b", 3.2))):
            dst = prs.slides.add_slide(src.slide_layout)
            for el in keep:
                cp = etree.fromstring(etree.tostring(el))
                if cp.find(".//" + P + "cNvPr").get("name") == "readiness.table":
                    off = cp.find(P + "xfrm").find(A + "off")
                    off.set("y", str(int(off.get("y")) + int(dy * EMU)))
                dst.shapes._spTree.append(cp)
            dst._element.find(P + "cSld").set("name", tag_)
            new = lst[-1]
            lst.remove(new)
            lst.insert(5 + k, new)
    with_prs(p, fn)


def p16_magenta(p, w):
    def fn(r):
        sf = sppr(shape(r, "pillar.1.card")).find(A + "solidFill")
        for c in list(sf):
            sf.remove(c)
        sf.append(etree.Element(A + "srgbClr", val="FF00FF"))
    edit_slide(p, 2, fn)


def p17_leverage(p, w):
    def fn(r):
        first_run(shape(r, "pillar.1.text.2")).find(A + "t").text = \
            "Teams leverage one store " + chr(0x2014) + " refreshed weekly."
    edit_slide(p, 2, fn)


def p17_empty_rules(p, w):
    f = Path(w) / "empty-fingerprints.json"
    f.write_text("{}\n", encoding="utf-8")
    return {"fingerprints": str(f)}


def _canary():
    return json.loads((SKILL / "devices" / "refs" / "canary.json").read_text(encoding="utf-8"))


def p18_canary(p, w):
    name = _canary()["entity"]

    def fn(r):
        t = first_run(shape(r, "pillar.1.text.2")).find(A + "t")
        t.text = "%s planners read one store." % name
    edit_slide(p, 2, fn)


def p18_image(p, w):
    blob = png(320, 320, seed=7)
    with_prs(p, lambda prs: add_picture(prs, 7, blob, (11.0, 5.5, 1.0, 1.0), "sample.mark", "Sample regional mark"))
    src = SKILL / "devices" / "refs"
    refs = Path(w) / "refs"
    refs.mkdir()
    for f in src.iterdir():
        if f.name != "media.json" and f.is_file():
            os.symlink(f, refs / f.name)
    media = json.loads((src / "media.json").read_text(encoding="utf-8"))
    media["items"] = list(media.get("items", [])) + [{"sha256": hashlib.sha256(blob).hexdigest(), "dhash": None,
                                                      "bytes": len(blob), "format": "PNG", "px": [320, 320],
                                                      "decks": 1, "test": "registered by the negatives runner"}]
    (refs / "media.json").write_text(json.dumps(media), encoding="utf-8")
    return {"refs_dir": str(refs)}


def p18_alt_path(p, w):
    edit_slide(p, 2, lambda r: shape(r, "pillar.1.icon").find(".//" + P + "cNvPr").set("descr", "/tmp/claude-0/x.png"))


def _notes(p):
    def fn(prs):
        prs.slides[1].notes_slide.notes_text_frame.text = "Pause here and point at the first card."
    with_prs(p, fn)


def p18_notes(p, w):
    _notes(p)


def p18_creator(p, w):
    def fn(r):
        for el in r.iter():
            if isinstance(el.tag, str) and etree.QName(el).localname == "creator":
                el.text = "Jane Doe"
    edit_part(p, "docProps/core.xml", fn)


def p19_click(p, w):
    with_prs(p, lambda prs: _add_text(prs, 7, (0.5, 5.0, 4.0, 0.3), "Click to add Text", 12.0, "leftover"))


def p19_hidden(p, w):
    edit_slide(p, 7, lambda r: r.set("show", "0"))


def p20_notes(p, w):
    _notes(p)


def p20_no_alt(p, w):
    blob = png(400, 400, seed=3)
    with_prs(p, lambda prs: add_picture(prs, 7, blob, (11.0, 5.5, 1.0, 1.0), "sample.mark", ""))


def p21_timestamp(p, w):
    def fn(r):
        for el in r.iter():
            if isinstance(el.tag, str) and etree.QName(el).localname == "modified":
                el.text = "2026-10-03T09:15:00Z"
    edit_part(p, "docProps/core.xml", fn)


def p22_raster(p, w):
    blob = png(48, 48, seed=5)
    with_prs(p, lambda prs: add_picture(prs, 7, blob, (11.0, 5.5, 1.0, 1.0), "sample.mark", "Sample regional mark"))


def p22_svg_fallback(p, w):
    add_svg(p, 4)

    def fn(r):
        pic = shape(r, "icon.sample")
        blip = pic.find(".//" + A + "blip")
        del blip.attrib[R + "embed"]
    edit_slide(p, 4, fn)


def p23_chip(p, w):
    def fn(r):
        chip = shape(r, "stat.3.basis")
        chip.getparent().remove(chip)
    edit_slide(p, 4, fn)


# ------------------------------------------------------------------ sub-rule planters (one rule each)

def _refs_copy(w, *, media_extra=None, vectors_extra=None) -> str:
    """A test refs folder: the real files linked, with media.json or vectors.sha1 extended."""
    src = SKILL / "devices" / "refs"
    refs = Path(w) / "refs"
    refs.mkdir(exist_ok=True)
    for f in src.iterdir():
        if f.is_file() and not (f.name == "media.json" and media_extra) and not (f.name == "vectors.sha1" and vectors_extra):
            os.symlink(f, refs / f.name)
    if media_extra:
        media = json.loads((src / "media.json").read_text(encoding="utf-8"))
        media["items"] = list(media.get("items", [])) + list(media_extra)
        (refs / "media.json").write_text(json.dumps(media), encoding="utf-8")
    if vectors_extra:
        lines = (src / "vectors.sha1").read_text(encoding="utf-8").split()
        (refs / "vectors.sha1").write_text("\n".join(sorted(set(lines) | set(vectors_extra))) + "\n", encoding="utf-8")
    return str(refs)


def p07_ragged(p, w):
    def fn(r):
        for nm in ("pillar.2.icon", "pillar.2.text.1", "pillar.2.text.2"):
            move(shape(r, nm), dy_in=0.15)
    edit_slide(p, 2, fn)


def p09_confidential(p, w):
    with_prs(p, lambda prs: _add_text(prs, 3, (0.5, 5.6, 4.0, 0.3), "Strictly confidential draft", 10.0, "conf.line"))


def p10_no_device(p, w):
    def fn(r):
        for c in list(r.iter(P + "cNvPr")):
            if ".icon" in (c.get("name") or ""):
                sh = c.getparent().getparent()
                sh.getparent().remove(sh)
    edit_slide(p, 2, fn)


def p10_caps(p, w):
    def fn(r):
        for k in (1, 2, 3):
            t = first_run(shape(r, "pillar.%d.text.1" % k)).find(A + "t")
            t.text = t.text.upper()
    edit_slide(p, 2, fn)


def p11_ladder(p, w):
    edit_slide(p, 2, lambda r: first_run(shape(r, "pillar.1.text.2")).find(A + "rPr").set("sz", "1075"))


def p12_schema(p, w):
    def fn(r):
        tree = r.find(".//" + P + "spTree")
        tree.append(etree.Element(P + "bogus"))
    edit_slide(p, 2, fn)


def p14_long(p, w):
    def fn(r):
        runs = runs_of(shape(r, "title"))
        runs[0].find(A + "t").text = "Four steps"
        runs[1].find(A + "t").text = (" take a forecast from a rough regional draft through review and "
                                      "reconciliation to a signed plan")
    edit_slide(p, 3, fn)


def p15_lookalike(p, w):
    def fn(prs):
        src = prs.slides[2]
        dst = prs.slides.add_slide(src.slide_layout)
        for el in list(src.shapes._spTree)[2:]:
            dst.shapes._spTree.append(etree.fromstring(etree.tostring(el)))
        dst._element.find(P + "cSld").set("name", "decision-flow:chevron-row")
        lst = prs.part._element.find(P + "sldIdLst")
        new = lst[-1]
        lst.remove(new)
        lst.insert(3, new)
    with_prs(p, fn)


def p15_family(p, w):
    def fn(r):
        for prop in r:
            nm = prop.get("name")
            v = {"deckkit:258": "team:grid", "deckkit:259": "the-ask:numbered-row"}.get(nm)
            if v:
                prop[0].text = v
    edit_part(p, "docProps/custom.xml", fn)


def p16_mod(p, w):
    def fn(r):
        sc = sppr(shape(r, "pillar.1.card")).find(A + "solidFill")[0]
        sc.find(A + "lumMod").set("val", "93000")
    edit_slide(p, 2, fn)


def p17_person(p, w):
    edit_slide(p, 2, lambda r: setattr(first_run(shape(r, "pillar.1.text.2")).find(A + "t"), "text",
                                       "We read one store each Monday."))


def p18_6gram(p, w):
    c = _canary()
    t = c["probe_text"]
    for nm in [c["entity"]] + list(c.get("aliases", [])):
        t = t.replace(nm, "")
    t = t.split(",")[0].strip()
    edit_slide(p, 2, lambda r: setattr(first_run(shape(r, "pillar.1.text.2")).find(A + "t"), "text", t))


def p18_number(p, w):
    num = next(x for x in _canary()["numphrases"] if " " in x)
    n, noun = num.split(" ", 1)
    t = "Teams tracked %s,%s %s weekly" % (n[:-3], n[-3:], noun) if len(n) > 3 else "Teams tracked %s weekly" % num
    edit_slide(p, 2, lambda r: setattr(first_run(shape(r, "pillar.1.text.2")).find(A + "t"), "text", t))


def p18_near_image(p, w):
    from deckkit.read import refnorm as rn
    blob = png(320, 320, seed=11)
    with_prs(p, lambda prs: add_picture(prs, 7, blob, (11.0, 5.5, 1.0, 1.0), "sample.mark", "Sample regional mark"))
    dh = rn.dhash64(blob)
    near = "%016x" % (int(dh, 16) ^ 1)            # one bit away, a different sha
    return {"refs_dir": _refs_copy(w, media_extra=[{"sha256": hashlib.sha256(b"not-the-bytes").hexdigest(),
                                                    "dhash": near, "test": "registered by the negatives runner"}])}


def p18_vector(p, w):
    from deckkit.read import refnorm as rn
    m = members(p)
    root = etree.fromstring(m[slide_part(p, 2)])
    sig = rn.custgeom_sig(shape(root, "pillar.1.icon").find(".//" + A + "custGeom"))
    edit_slide(p, 2, lambda r: shape(r, "pillar.1.icon").find(".//" + P + "cNvPr").set("descr", "Database"))
    return {"refs_dir": _refs_copy(w, vectors_extra=[rn.sha1(sig)])}


def p18_master(p, w):
    edit_part(p, "ppt/slideMasters/slideMaster1.xml", lambda r: r.find(P + "cSld").set("name", "Corporate"))


def p19_empty(p, w):
    def fn(prs):
        tb = prs.slides[6].shapes.add_textbox(int(1 * EMU), int(5 * EMU), int(3 * EMU), int(0.4 * EMU))
        tb.name = "empty"
    with_prs(p, fn)


def p19_slot(p, w):
    edit_slide(p, 2, lambda r: setattr(first_run(shape(r, "pillar.1.text.2")).find(A + "t"), "text", "{{slot:body}}"))


def p20_generic_alt(p, w):
    blob = png(400, 400, seed=3)
    with_prs(p, lambda prs: add_picture(prs, 7, blob, (11.0, 5.5, 1.0, 1.0), "sample.mark", "Picture 3"))


def p21_manifest_too(p, w):
    p21_timestamp(p, w)
    mp = Path(p).with_name(Path(p).stem + ".manifest.json")
    man = json.loads(mp.read_text(encoding="utf-8"))
    man["sha256"] = hashlib.sha256(Path(p).read_bytes()).hexdigest()
    mp.write_text(json.dumps(man, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def p22_emoji(p, w):
    def fn(r):
        t = first_run(shape(r, "pillar.1.text.1")).find(A + "t")
        t.text = t.text + " " + chr(0x1F680)
    edit_slide(p, 2, fn)


def p23_drift(p, w):
    edit_slide(p, 4, lambda r: setattr(first_run(shape(r, "stat.1.value")).find(A + "t"), "text", "46%"))


def p23_loose(p, w):
    with_prs(p, lambda prs: _add_text(prs, 6, (0.5, 5.6, 2.0, 0.6), "73%", 28.0, "loose.figure", role="accent-ink",
                                      bold=True))


# ------------------------------------------------------------------ planters for the third fix round

def _face(run, face):
    """Set a run's latin/ea/cs typeface, adding a:latin when the run inherits its face."""
    rpr = run.find(A + "rPr")
    lat = rpr.find(A + "latin")
    if lat is None:
        lat = etree.Element(A + "latin")
        after = [c for c in rpr if etree.QName(c).localname in ("ln", "noFill", "solidFill", "gradFill", "blipFill",
                                                                 "pattFill", "grpFill", "effectLst", "effectDag",
                                                                 "highlight", "uLnTx", "uLn", "uFillTx", "uFill")]
        (after[-1].addnext(lat) if after else rpr.insert(0, lat))
    for tag in ("latin", "ea", "cs"):
        e = rpr.find(A + tag)
        if e is not None:
            e.set("typeface", face)


def p02_unknown_face(p, w):
    """A body run in a face with no metrics, overflowing too: the gate names the face AND measures the overflow
    in its Arial fallback, so one unmeasurable face never hides a fit failure."""
    def fn(r):
        rn = first_run(shape(r, "pillar.2.text.2"))
        _face(rn, "Consolas")
        rn.find(A + "t").text = rn.find(A + "t").text + " " + words(40)
    edit_slide(p, 2, fn)


def p14_face_then_long(p, w):
    """A title in a face with no metrics on slide 2 and an 18-word title on slide 3: the gate reaches slide 3."""
    edit_slide(p, 2, lambda r: [_face(rn, "Consolas") for rn in runs_of(shape(r, "title"))])
    p14_long(p, w)


def p06_panel_short(p, w):
    """The arrow between the second and third step cards, inside the step panel, stopped 0.3in short of the
    third card: its end lies inside the panel, which must never count as the target."""
    edit_slide(p, 3, lambda r: [e.set("cx", str(int(e.get("cx")) - int(0.30 * EMU)))
                                for e in [xfrm(shape(r, "step.arrow.2"))[1]]])


def p07_ragged_under(p, w):
    """One card's content dropped 0.15in, with the three cards raised above their own content in z-order."""
    p07_ragged(p, w)

    def fn(r):
        tree = r.find(".//" + P + "spTree")
        for k in (1, 2, 3):
            sh = shape(r, "pillar.%d.card" % k)
            tree.remove(sh)
            tree.append(sh)
    edit_slide(p, 2, fn)


def p10_thin_accent(p, w):
    """A 0.01in strip in the accent colour beside a card body: thin, but not a neutral hairline."""
    from deckkit import ooxml, prims
    from deckkit.canvas import Box
    th = theme()

    def fn(prs):
        s = prs.slides[1]
        body = next(sh for sh in s.shapes if sh.name == "pillar.1.text.2")
        x, y, h = body.left / EMU, body.top / EMU, body.height / EMU
        bar = prims._add(s, "RECTANGLE", Box(x - 0.08, y, 0.01, h), "accent.hair")
        prims.set_fill(bar, "accent", theme=th)
        prims.set_line(bar, None, theme=th)
        prims._drop_text(bar)
        ooxml.finish(bar)
    with_prs(p, fn)


def p11_radius(p, w):
    """A card drawn at a 0.15in corner radius on a canvas that sets 0.05in."""
    def fn(r):
        sh = shape(r, "pillar.1.card")
        _x, _y, bw, bh = box_in(sh)
        gd = sh.find(".//" + A + "prstGeom").find(A + "avLst").find(A + "gd")
        gd.set("fmla", "val %d" % round(0.15 / min(bw, bh) * 1e5))
    edit_slide(p, 2, fn)


AUTHORS_NS = "http://schemas.microsoft.com/office/powerpoint/2018/8/main"


def _authors_part(p):
    """PowerPoint's authors.xml extension part, with its relationship and content type."""
    m = members(p)
    m["ppt/authors.xml"] = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<p188:authorLst '
                            'xmlns:p188="%s"/>' % AUTHORS_NS).encode()
    rels = etree.fromstring(m["ppt/_rels/presentation.xml.rels"])
    ids = {r.get("Id") for r in rels}
    rid = next("rId%d" % k for k in range(900, 999) if "rId%d" % k not in ids)
    etree.SubElement(rels, rels[0].tag, Id=rid, Type="http://schemas.microsoft.com/office/2018/10/relationships/authors",
                     Target="authors.xml")
    m["ppt/_rels/presentation.xml.rels"] = etree.tostring(rels, xml_declaration=True, encoding="UTF-8", standalone=True)
    ct = etree.fromstring(m["[Content_Types].xml"])
    etree.SubElement(ct, "{http://schemas.openxmlformats.org/package/2006/content-types}Override",
                     PartName="/ppt/authors.xml", ContentType="application/vnd.ms-powerpoint.authors+xml")
    m["[Content_Types].xml"] = etree.tostring(ct, xml_declaration=True, encoding="UTF-8", standalone=True)
    write(p, m)


def p12_glue_ext(p, w):
    """An extension part the schema bundle cannot validate (skipped) AND a connector glued to a missing shape id:
    skipping the part must never hide the glue defect."""
    _authors_part(p)

    def fn(r):
        cx = shape(r, "step.arrow.1")
        c = cx.find(".//" + P + "cNvCxnSpPr")
        etree.SubElement(c, A + "stCxn", id="9999", idx="0")
    edit_slide(p, 3, fn)


def p12_busz(p, w):
    """A bullet size of 5000 (5%): outside the 25%..400% PowerPoint writes, so not a known value."""
    def fn(r):
        para = shape(r, "pillar.1.text.2").find(".//" + A + "p")
        ppr = para.find(A + "pPr")
        if ppr is None:
            ppr = etree.Element(A + "pPr")
            para.insert(0, ppr)
        bu = etree.Element(A + "buSzPct", val="5000")
        later = [c for c in ppr if etree.QName(c).localname in ("buFontTx", "buFont", "buNone", "buAutoNum", "buChar",
                                                                 "buBlip", "tabLst", "defRPr", "extLst")]
        (later[0].addprevious(bu) if later else ppr.append(bu))
    edit_slide(p, 2, fn)


def p16_theme_hex(p, w):
    def fn(r):
        sf = sppr(shape(r, "pillar.1.card")).find(A + "solidFill")
        for c in list(sf):
            sf.remove(c)
        sf.append(etree.Element(A + "srgbClr", val="D91E18"))
    edit_slide(p, 2, fn)


def p17_no_deck_voice(p, w):
    d = json.loads(Path(os.path.expanduser("~/.claude/hooks/fingerprints.json")).read_text(encoding="utf-8"))
    d["rules"] = [r for r in d.get("rules", []) if r.get("tier") != "deck-voice"]
    f = Path(w) / "fingerprints-no-deck-voice.json"
    f.write_text(json.dumps(d), encoding="utf-8")
    return {"fingerprints": str(f)}


def _refs_emptied(w, name) -> str:
    src = SKILL / "devices" / "refs"
    refs = Path(w) / "refs"
    refs.mkdir(exist_ok=True)
    for f in src.iterdir():
        if f.is_file() and f.name != name:
            os.symlink(f, refs / f.name)
    if name == "media.json":
        media = json.loads((src / "media.json").read_text(encoding="utf-8"))
        media["items"] = []
        (refs / name).write_text(json.dumps(media), encoding="utf-8")
    else:
        (refs / name).write_text("", encoding="utf-8")
    return str(refs)


def p18_empty_media(p, w):
    return {"refs_dir": _refs_emptied(w, "media.json")}


def p18_empty_vectors(p, w):
    return {"refs_dir": _refs_emptied(w, "vectors.sha1")}


def p23_range(p, w):
    """A range set large and bold outside any stat: the read layer guesses a heading, the figure rule does not."""
    with_prs(p, lambda prs: _add_text(prs, 6, (0.5, 5.6, 3.0, 0.6), "5 to 10%", 28.0, "range.figure", role="ink-deep",
                                      bold=True))


def p24_top_heavy(p, w):
    """Every shape on the pillars slide but the title squeezed into the top 45% of the content band."""
    from deckkit.canvas import WIDE
    band = WIDE.content

    def fn(r):
        tree = r.find(".//" + P + "spTree")
        kids = [k for k in tree if etree.QName(k).localname in ("sp", "cxnSp", "pic", "grpSp", "graphicFrame")
                and k.find(".//" + P + "cNvPr").get("name") != "title"]
        boxes = []
        for k in kids:
            x = k.find(".//" + A + "xfrm")
            boxes.append((x, int(x.find(A + "off").get("y")), int(x.find(A + "ext").get("cy"))))
        top = band.y * EMU
        bot = max(y + h for _x, y, h in boxes)
        f = 0.45 * band.h * EMU / (bot - top)
        for x, y, h in boxes:
            x.find(A + "off").set("y", str(int(round(top + (y - top) * f))))
            x.find(A + "ext").set("cy", str(int(round(h * f))))
    edit_slide(p, 2, fn)


def p15_share(p, w):
    """Slides 2, 4 and 6 all in the Columns family (three archetypes, never adjacent): 60% of the content slides."""
    def fn(r):
        for prop in r:
            v = {"deckkit:259": "context-problem:split", "deckkit:261": "team:grid"}.get(prop.get("name"))
            if v:
                prop[0].text = v
    edit_part(p, "docProps/custom.xml", fn)


def p05_loose_chevron(p, w):
    """A chevron outside the step header's group, nested into its first step the way the row nests its own."""
    from pptx.enum.shapes import MSO_SHAPE

    def fn(prs):
        s = prs.slides[2]
        hdr = next(sh for sh in s.shapes if sh.name == "steps")
        x, y, h = hdr.left, hdr.top, hdr.height
        ch = s.shapes.add_shape(MSO_SHAPE.CHEVRON, x + int(2.6 * EMU), y, int(1.5 * EMU), h)
        ch.name = "loose.chevron"
    with_prs(p, fn)


PLANTERS = [
    Planter("run-7.5pt", "P01", "a body run set at 7.5pt", p01_75, "7.50pt run"),
    Planter("autofit-75pct", "P01", "a 10pt run under normAutofit fontScale 75% (7.5pt drawn)", p01_scale,
            "fontScale 75%"),
    Planter("forty-extra-words", "P02", "40 more words in a card body sized to its old text", p02_words, "needs"),
    Planter("unknown-face", "P02", "a Consolas run (no metrics) in a card body with 40 more words", p02_unknown_face,
            "measured as Arial"),
    Planter("past-the-edge", "P03", "a card moved 0.1in past the right edge", p03_edge, "past the right edge"),
    Planter("child-on-edge", "P04", "a card body 0.01in from its card's left edge", p04_edge, "from the left edge"),
    Planter("colliding-text", "P05", "a heading duplicated 0.12in right and 0.08in down over itself", p05_overlap,
            "step.1.text.1 / step.1.text.1.copy"),
    Planter("loose-chevron", "P05", "a chevron outside the step header's group nested into its first step",
            p05_loose_chevron, "loose.chevron"),
    Planter("arrow-shifted", "P06", "an arrow inside the step panel shifted 0.3in back along its axis", p06_arrow,
            "lands on nothing"),
    Planter("arrow-short-in-panel", "P06", "an arrow inside the step panel stopped 0.3in short of its card",
            p06_panel_short, "end lands on nothing"),
    Planter("card-gap", "P07", "two sibling cards 0.02in apart", p07_gap, "0.020in apart"),
    Planter("ragged-headings", "P07", "one card's content dropped 0.15in in a row of three", p07_ragged,
            "first content at"),
    Planter("ragged-under-cards", "P07", "the same drop with the cards raised above their content in z-order",
            p07_ragged_under, "first content at"),
    Planter("top-heavy", "P08", "a card whose content sits at its top with an inch of air below", p08_topheavy,
            "top-heavy"),
    Planter("foot-band", "P09", "a full-width band along the foot with a sentence on it", p09_band, "foot band"),
    Planter("subtitle", "P09", "a nine-word sentence directly under the title", p09_subtitle, "subtitle under"),
    Planter("page-number", "P09", "a page number '2 / 34' in the top-right corner", p09_pagenum, "'2 / 34'"),
    Planter("page-number-bare", "P09", "a bare page number in the bottom-right corner", p09_pagenum_bare,
            "page number '3'"),
    Planter("confidential-line", "P09", "a 'confidential' line on a slide", p09_confidential, "confidentiality"),
    Planter("left-bar", "P10", "an accent bar down the left of a card body", p10_bar, "left accent bar"),
    Planter("no-device", "P10", "a content slide with its icons removed and no arrows", p10_no_device,
            "nothing drawn"),
    Planter("caps-kicker", "P10", "every card heading set in capitals", p10_caps, "caps label"),
    Planter("thin-accent-bar", "P10", "a 0.01in accent strip beside a card body (thin, but not grey)",
            p10_thin_accent, "left accent bar"),
    Planter("ghost-style", "P11", "an injected <p:style> with effectRef idx 2 on a card", p11_style, "<p:style>"),
    Planter("gradient", "P11", "a gradient fill on a card", p11_gradient, "gradient fill"),
    Planter("blurred-shadow", "P11", "a 3pt blurred outer shadow on a card", p11_shadow, "shadow blur"),
    Planter("calibri-run", "P11", "a body run set in Calibri", p11_calibri, "'Calibri'"),
    Planter("off-ladder", "P11", "a body run at 10.75pt", p11_ladder, "half-point ladder"),
    Planter("off-radius", "P11", "a card at a 0.15in corner radius on a 0.05in canvas", p11_radius, "card radius"),
    Planter("double-effectLst", "P12", "a second <a:effectLst/> in one spPr", p12_double, "<effectLst> x2"),
    Planter("dangling-embed", "P12", "a blip fill pointing at r:embed rId999", p12_embed, "rId999"),
    Planter("svg-ct-dropped", "P12", "an SVG picture whose content type was dropped", p12_svg_ct, "no content type"),
    Planter("schema-violation", "P12", "an unknown <p:bogus/> in a slide's shape tree", p12_schema, "bogus"),
    Planter("glue-beside-extension", "P12", "a skipped authors.xml part and a connector glued to shape id 9999",
            p12_glue_ext, "glued to missing shape id 9999"),
    Planter("bullet-size-5pct", "P12", "a buSzPct of 5000, outside PowerPoint's own range", p12_busz, "buSzPct"),
    Planter("three-hundred-words", "P13", "300 words added to one slide", p13_words, "words on glass"),
    Planter("shared-opener", "P14", "three titles opening 'Regional planning'", p14_opener, "titles open with"),
    Planter("body-keyword", "P14", "a two-tone accent-ink keyword inside body copy", p14_body_keyword,
            "outside a title"),
    Planter("long-title", "P14", "an 18-word title", p14_long, "words in the title"),
    Planter("face-then-long-title", "P14", "a Consolas title on slide 2, then an 18-word title on slide 3",
            p14_face_then_long, "18 words in the title"),
    Planter("duplicate-adjacent", "P15", "the process slide duplicated next to itself", p15_duplicate,
            "appears 2 times"),
    Planter("lookalike", "P15", "the process slide duplicated next to itself under another archetype", p15_lookalike,
            "looks like slide"),
    Planter("same-family-run", "P15", "three slides in a row retagged into one family", p15_family, "are all Columns"),
    Planter("three-tables", "P15", "the table slide copied twice beside itself", p15_tables, "table slides in a row"),
    Planter("family-share", "P15", "slides 2, 4 and 6 retagged into Columns (60% of content slides)", p15_share,
            "content slides are Columns"),
    Planter("magenta-fill", "P16", "a card filled with srgb FF00FF", p16_magenta, "FF00FF"),
    Planter("mod-not-role", "P16", "a card fill at bg1 lumMod 93000, no role", p16_mod, "not a theme role"),
    Planter("theme-hex-fill", "P16", "a card filled with srgb D91E18, the accent1 slot's hex", p16_theme_hex,
            "hard-coded theme colour"),
    Planter("leverage-emdash", "P17", "'leverage' and an em dash in a card body", p17_leverage, "leverage"),
    Planter("first-person", "P17", "'We' opening a card body", p17_person, "dv-person"),
    Planter("empty-rules", "P17", "an empty fingerprints file: the canary must make the gate fail", p17_empty_rules,
            "canary", ctx_only=True),
    Planter("no-deck-voice-tier", "P17", "a fingerprints copy with the deck-voice tier removed", p17_no_deck_voice,
            "canary for dv-person", ctx_only=True),
    Planter("canary-name", "P18", "the refs canary entity's name in a card body", p18_canary, "name matches"),
    Planter("corpus-6gram", "P18", "six words of the canary probe, no name, no number", p18_6gram, "6-gram matches"),
    Planter("corpus-number", "P18", "the canary's numeric phrase", p18_number, "number matches"),
    Planter("corpus-image", "P18", "a picture whose sha256 a test refs folder registers as a corpus image", p18_image,
            "corpus image (sha256"),
    Planter("near-image", "P18", "a picture one dHash bit from a test-registered corpus image", p18_near_image,
            "dHash distance"),
    Planter("corpus-vector", "P18", "a glyph whose signature a test refs folder registers", p18_vector,
            "corpus vector"),
    Planter("alt-tmp-path", "P18", "alt text holding /tmp/claude-0/x.png", p18_alt_path, "/tmp/claude-0"),
    Planter("notes-leak", "P18", "speaker notes travelling with the deck", p18_notes, "notes text travels"),
    Planter("creator-jane", "P18", "docProps creator 'Jane Doe'", p18_creator, "Jane Doe"),
    Planter("foreign-master", "P18", "the slide master changed after the build", p18_master, "kit base"),
    Planter("empty-media-index", "P18", "a refs copy whose media.json lists no item", p18_empty_media,
            "media.json is empty", ctx_only=True),
    Planter("empty-vector-index", "P18", "a refs copy whose vectors.sha1 is empty", p18_empty_vectors,
            "vectors.sha1 is empty", ctx_only=True),
    Planter("click-to-add", "P19", "a 'Click to add Text' box", p19_click, "Click to add"),
    Planter("hidden-slide", "P19", "a hidden slide", p19_hidden, "hidden slide"),
    Planter("empty-box", "P19", "an empty text box", p19_empty, "empty text box"),
    Planter("slot-token", "P19", "an unfilled {{slot:body}}", p19_slot, "slot token"),
    Planter("notes-text", "P20", "speaker notes on an audience deck", p20_notes, "speaker notes"),
    Planter("no-alt", "P20", "a picture with no alt text", p20_no_alt, "without alt text"),
    Planter("generic-alt", "P20", "a picture whose alt text is 'Picture 3'", p20_generic_alt, "not semantic"),
    Planter("core-timestamp", "P21", "a timestamp written into docProps/core.xml after the build", p21_timestamp,
            "manifest's"),
    Planter("manifest-rewritten", "P21", "the same timestamp, with the manifest rewritten to match", p21_manifest_too,
            "rebuild sha"),
    Planter("raster-1x", "P22", "a 48px raster drawn at one inch (48 dpi)", p22_raster, "48 dpi"),
    Planter("svg-no-fallback", "P22", "an SVG picture with its PNG fallback removed", p22_svg_fallback,
            "without a PNG fallback"),
    Planter("emoji-icon", "P22", "an emoji after a card heading", p22_emoji, "emoji"),
    Planter("unlabelled-illustrative", "P23", "an illustrative stat with its chip removed", p23_chip,
            "'Illustrative' chip"),
    Planter("value-drift", "P23", "a stat value changed on glass after the build", p23_drift, "on glass '46%'"),
    Planter("loose-figure", "P23", "a large figure on glass outside any stat", p23_loose, "no kind"),
    Planter("loose-range", "P23", "'5 to 10%' set large and bold outside any stat", p23_range, "no kind: '5 to 10%'"),
    Planter("top-heavy-slide", "P24", "the pillars slide's content squeezed into the top 45% of the band",
            p24_top_heavy, "content spans"),
]


__all__ = ["Planter", "PLANTERS", "members", "write", "edit_slide", "shape"]
