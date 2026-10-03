"""P27 charts: every native chart part holds the house rules the slide gates cannot see inside it.

The slide gates read slide XML; a chart's text, colours and data live in their own part (ppt/charts/chartN.xml). P27
reads the part behind every chart frame (deckkit.charts.parse for the data) and fails:
  floor     a text size under 8pt anywhere in the part (tick labels, data labels, titles), or no explicit size on the
            chart's own txPr (PowerPoint and LibreOffice fall back to different defaults);
  colour    a colour that is neither a theme role (scheme slot plus lumMod/lumOff exactly as a role writes it, as in
            P16) nor an identity hex; a RAG status identity on a chart (status never rides a chart mark); sysClr,
            prstClr, scrgbClr or hslClr;
  style     3D (view3D, any *3DChart, bubble3D true), a gradient, pattern or picture fill, an effect list with
            children, a c:style other than 1 or 2, roundedCorners missing or true;
  form      a chart title (the slide title carries the claim); a legend over 3 series or fewer (label directly);
            more than 3 categorical colours; more than one accent mark (one subject per chart); a bar, column or area
            value axis with no fixed minimum of 0, or a log scale; a second axis pair; a pie or doughnut of more than
            2 points; a plot area not pinned by c:manualLayout (kit labels sit on its coordinates);
  text      a banned glyph, word, phrase, jargon or deck-voice pattern in any chart text (series names, category
            caches, rich text), with P17's own rules file and canary;
  contrast  native tick labels and data labels against what they sit on (paper, or the series fill for a label
            inside a bar), at the WCAG minimum for their size (deckkit.rules.contrast_min);
  kind      a frame whose alt text does not end "(chart kind <kind>)", or a planning kind with no basis label
            ("Illustrative figures", "Target figures", "Benchmark figures") whose whole text sits on its slide;
  drift     on a deck with a manifest: no manifest["charts"] record for a frame, a data cache that differs from it
            (Edit Data after the build), or a label shape <frame>.* whose text differs from it.
A deck with no chart passes with a note.
"""
from __future__ import annotations

import sys

from _shared import FAIL, NOTE, Finding, cli, text_of
from deckkit import charts
from deckkit.measure import FLOOR
from deckkit.read.colour import apply_mods, contrast
from deckkit.read.ns import NS, local
from deckkit.rules import contrast_min, is_neutral_colour

GATE, TITLE = "P27", "charts"
C, A, R, P = ("{%s}" % NS["c"]), ("{%s}" % NS["a"]), ("{%s}" % NS["r"]), ("{%s}" % NS["p"])
COLOURS = ("srgbClr", "schemeClr", "sysClr", "prstClr", "scrgbClr", "hslClr")
THREE_D = ("view3D", "bar3DChart", "line3DChart", "pie3DChart", "area3DChart", "surface3DChart", "floor",
           "sideWall", "backWall")
FILLS_BANNED = ("gradFill", "pattFill", "blipFill")

STYLES_OK = ("1", "2")
INSIDE = ("inEnd", "ctr", "inBase")
PAPER = "FFFFFF"


def _frames(ctx, i):
    """[(name, descr, chart part, chart root)] for every chart frame on slide i, nested ones included."""
    out = []
    part = ctx.dr.slide_part(i)
    rels = ctx.dr.rels(part)
    for gf in ctx.slide_root(i).iter(P + "graphicFrame"):
        gd = gf.find(A + "graphic/" + A + "graphicData")
        if gd is None or gd.get("uri") != charts.CHART_URI:
            continue
        c = gd.find(C + "chart")
        rid = c.get(R + "id") if c is not None else None
        nv = gf.find(".//" + P + "cNvPr")
        name = nv.get("name", "") if nv is not None else ""
        descr = nv.get("descr") if nv is not None else None
        tgt = rels.get(rid)
        if tgt is None or not ctx.dr.has(tgt[1]):
            out.append((name, descr, None, None))
            continue
        out.append((name, descr, tgt[1], ctx.dr.xml(tgt[1])))
    return out


def _in_ext(el) -> bool:
    return any(local(a) == "extLst" for a in el.iterancestors() if isinstance(a.tag, str))


def _mods(el):
    return tuple((local(m), int(m.get("val", "0"))) for m in el if isinstance(m.tag, str))


def _hex(el, th) -> str | None:
    """The resolved hex of a colour element (schemeClr through the theme's slots), or None."""
    k = local(el)
    if k == "schemeClr":
        try:
            return apply_mods(th.slot_hex(el.get("val")), list(_mods(el)))
        except Exception:
            return None
    if k == "srgbClr":
        return apply_mods(el.get("val") or "000000", list(_mods(el)))
    return None


def _fill_colour(sppr):
    """The colour element of an spPr's solid fill (or of its line when it has no fill), or None."""
    if sppr is None:
        return None
    sf = sppr.find(A + "solidFill")
    if sf is not None and len(sf):
        return sf[0]
    ln = sppr.find(A + "ln")
    if sf is None and ln is not None:
        lf = ln.find(A + "solidFill")
        if lf is not None and len(lf):
            return lf[0]
    return None


def _unit_colours(ser):
    """Colour elements painting the series itself: its spPr fill and line, and its marker."""
    out = []
    for sp in (ser.find(C + "spPr"), ser.find(C + "marker/" + C + "spPr")):
        if sp is None:
            continue
        for tag in ("solidFill", "ln/" + A + "solidFill"):
            sf = sp.find(A + tag)
            if sf is not None and len(sf):
                out.append(sf[0])
    return out


def _txt_props(el):
    """(sz in hundredths or None, bold, colour element or None) from a txPr/rich's first defRPr or rPr."""
    if el is None:
        return None, False, None
    for d in el.iter(A + "defRPr", A + "rPr"):
        sf = d.find(A + "solidFill")
        sz = d.get("sz")
        return (int(sz) if sz else None), d.get("b") in ("1", "true"), (sf[0] if sf is not None and len(sf) else None)
    return None, False, None


def _check_part(ctx, i, name, root, th, roles, identity, accent, rules):
    out = []

    def fail(msg):
        out.append(Finding(GATE, FAIL, i, name, msg))
    # floor
    cs_sz, cs_b, cs_clr = _txt_props(root.find(C + "txPr"))
    if cs_sz is None:
        fail("the chart's own txPr sets no text size; write sz explicitly (8pt floor)")
    small = sorted({int(e.get("sz")) for e in root.iter(A + "defRPr", A + "rPr") if (e.get("sz") or "").isdigit()
                    and int(e.get("sz")) < FLOOR * 100 - 1e-9 and not _in_ext(e)})
    if small:
        fail("chart text at %s pt, under the 8pt floor" % ", ".join("%.1f" % (s / 100) for s in small))
    # colour
    for el in root.iter():
        if not isinstance(el.tag, str) or local(el) not in COLOURS or _in_ext(el):
            continue
        k = local(el)
        if k == "schemeClr":
            t = (el.get("val"), _mods(el))
            if t not in roles:
                fail("schemeClr %s %s is not a theme role" % (t[0], " ".join("%s %d" % m for m in t[1]) or "(no mods)"))
        elif k == "srgbClr":
            hx = (el.get("val") or "").upper()
            key = identity.get(hx)
            if key is None:
                fail("srgb %s is neither a theme role nor an identity colour" % hx)
            elif key.startswith("rag-"):
                fail("srgb %s is the %s status identity; status never rides a chart mark, it lives in a status mark "
                     "with its word" % (hx, key))
        else:
            fail("%s %s in a chart" % (k, el.get("val") or ""))
    # style
    for el in root.iter():
        if not isinstance(el.tag, str) or _in_ext(el):
            continue
        k = local(el)
        if k in THREE_D:
            fail("3D: c:%s" % k)
        elif k == "bubble3D" and el.get("val") in ("1", "true"):
            fail("3D: bubble3D")
        elif k in FILLS_BANNED:
            fail("a %s fill; charts are flat solid fills" % {"gradFill": "gradient", "pattFill": "pattern",
                                                              "blipFill": "picture"}[k])
        elif k == "effectLst" and len(el):
            fail("an effect list with %s (shadow or glow); charts carry no effects" % ", ".join(local(c) for c in el))
        elif k == "style" and el.tag == C + "style" and el.get("val") not in STYLES_OK:
            fail("c:style %s applies a preset style; write every property instead" % el.get("val"))
    rc = root.find(C + "roundedCorners")
    if rc is None or rc.get("val") not in ("0", "false"):
        fail("roundedCorners is %s; write <c:roundedCorners val=\"0\"/>" % ("missing" if rc is None else rc.get("val")))
    # form
    ch = root.find(C + "chart")
    pa = ch.find(C + "plotArea") if ch is not None else None
    if ch is None or pa is None:
        fail("no plot area")
        return out
    if ch.find(C + "title") is not None:
        fail("a chart title; the slide title carries the claim")
    groups = [g for g in pa if isinstance(g.tag, str) and local(g) in charts.CHART_TYPES]
    sers = [s for g in groups for s in g.findall(C + "ser")]
    if ch.find(C + "legend") is not None and len(sers) <= 3:
        fail("a legend box over %d series; label each series directly" % len(sers))
    if pa.find(C + "layout/" + C + "manualLayout") is None:
        fail("the plot area is not pinned by c:manualLayout, so labels and annotations cannot land on data")
    hexes, n_accent = set(), 0
    for g in groups:
        for s in g.findall(C + "ser"):
            unit = _unit_colours(s)
            if any(local(c) == "schemeClr" and (c.get("val"), _mods(c)) == accent for c in unit):
                n_accent += 1
            for c in unit:
                h = _hex(c, th)
                if h and not is_neutral_colour(h, th):
                    hexes.add(h)
            for d in s.findall(C + "dPt"):
                c = _fill_colour(d.find(C + "spPr"))
                if c is None:
                    c = _fill_colour(d.find(C + "marker/" + C + "spPr"))
                if c is None:
                    continue
                if local(c) == "schemeClr" and (c.get("val"), _mods(c)) == accent:
                    n_accent += 1
                h = _hex(c, th)
                if h and not is_neutral_colour(h, th):
                    hexes.add(h)
    if len(hexes) > charts.CATEGORICAL_MAX:
        fail("%d categorical colours (%s); a chart carries at most %d: the subject, navy and one grey"
             % (len(hexes), ", ".join(sorted(hexes)), charts.CATEGORICAL_MAX))
    if n_accent > 1:
        fail("%d marks in accent; one subject per chart" % n_accent)
    axes = {}
    for ax in pa:
        if isinstance(ax.tag, str) and local(ax) in ("valAx", "catAx", "dateAx", "serAx"):
            aid = ax.find(C + "axId")
            if aid is not None:
                axes[aid.get("val")] = ax
    pairs = {tuple(sorted(a.get("val") for a in g.findall(C + "axId"))) for g in groups if g.findall(C + "axId")}
    if len(pairs) > 1:
        fail("%d axis pairs: a second value axis; one scale per plot" % len(pairs))
    for g in groups:
        if local(g) not in ("barChart", "areaChart"):
            continue
        for a in g.findall(C + "axId"):
            ax = axes.get(a.get("val"))
            if ax is None or local(ax) != "valAx":
                continue
            sc = ax.find(C + "scaling")
            mn = sc.find(C + "min") if sc is not None else None
            if sc is not None and sc.find(C + "logBase") is not None:
                fail("a log scale under %s" % local(g))
            if mn is None:
                fail("the %s value axis has no fixed minimum; bars and areas start at 0" % local(g))
            elif abs(float(mn.get("val", "0"))) > 1e-9:
                fail("the %s value axis starts at %s; bars and areas start at 0" % (local(g), mn.get("val")))
    for g in groups:
        if local(g) in ("pieChart", "doughnutChart", "ofPieChart"):
            for s in g.findall(C + "ser"):
                n = len(charts._cache(s.find(C + "val")))
                if n > 2:
                    fail("a %s of %d points; a ring holds one share and its rest, a comparison is a bar chart"
                         % (local(g), n))
    # text
    texts = []
    for s in sers:
        texts += [t for t in charts._cache(s.find(C + "tx")) if t]
        texts += [t for t in charts._cache(s.find(C + "cat")) if t]
    texts += [t.text for t in root.iter(A + "t") if t.text]
    out += _fingerprints(ctx, i, name, texts, rules)
    # contrast: tick labels and data labels
    bg = PAPER
    for ax in axes.values():
        dl = ax.find(C + "delete")
        tl = ax.find(C + "tickLblPos")
        if (dl is not None and dl.get("val") in ("1", "true")) or (tl is not None and tl.get("val") == "none"):
            continue
        sz, b, clr = _txt_props(ax.find(C + "txPr"))
        sz = sz or cs_sz or 1000
        b = b or cs_b
        clr = clr if clr is not None else cs_clr
        fg = _hex(clr, th) if clr is not None else "000000"
        r = contrast(fg or "000000", bg)
        need = contrast_min(sz / 100, b)
        if r + 1e-9 < need:
            fail("%s tick labels %s on %s at %.2f:1 (needs %.1f:1)" % (local(ax), fg, bg, r, need))
    for g in groups:
        for owner in [g] + g.findall(C + "ser"):
            dls = owner.find(C + "dLbls")
            if dls is None:
                continue
            shown = any((dls.find(C + t) is not None and dls.find(C + t).get("val") in ("1", "true"))
                        for t in ("showVal", "showCatName", "showSerName", "showPercent"))
            if not shown:
                continue
            sz, b, clr = _txt_props(dls.find(C + "txPr"))
            sz = sz or cs_sz or 1000
            fg = _hex(clr, th) if clr is not None else (_hex(cs_clr, th) if cs_clr is not None else "000000")
            pos = dls.find(C + "dLblPos")
            behind = bg
            if pos is not None and pos.get("val") in INSIDE and local(owner) == "ser":
                c = _fill_colour(owner.find(C + "spPr"))
                behind = (_hex(c, th) if c is not None else None) or bg
            r = contrast(fg, behind)
            need = contrast_min(sz / 100, b or cs_b)
            if r + 1e-9 < need:
                fail("data labels %s on %s at %.2f:1 (needs %.1f:1)" % (fg, behind, r, need))
    return out


def _fingerprints(ctx, i, name, texts, rules):
    import p17_fingerprints as p17
    out = []
    maturity_ok = ctx.overridden("P17:dv-maturity")
    for t in texts:
        t = p17.strip_urls(t)
        for rid, _tier, rx in rules:
            if rid in p17.ADVISORY_IDS or (rid == "dv-maturity" and maturity_ok):
                continue
            m = rx.search(t)
            if m:
                out.append(Finding(GATE, FAIL, i, name, "chart text fingerprint [%s] %r in %r" % (rid, m.group(0),
                                                                                                    t[:60])))
    return out


def _labels(ctx, i, name) -> dict:
    s = ctx.prs().slides[i - 1]
    return {sh.name: sh.text_frame.text for sh in s.shapes if sh.has_text_frame and sh.name.startswith(name + ".")}


def _close(a, b) -> bool:
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_close(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_close(a[k], b[k]) for k in a)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(a)))
    return a == b


def _drift(ctx, i, name, descr, root, man):
    out = []
    recs = man.get("charts")
    if recs is None:
        return [Finding(GATE, FAIL, i, name, "the manifest has no chart records; pass charts.records(prs) to "
                                              "package.save as manifest['charts']")]
    rec = recs.get(name)
    if rec is None:
        return [Finding(GATE, FAIL, i, name, "no manifest['charts'] record for this frame")]
    now = charts._record(root, descr, _labels(ctx, i, name))
    if not _close(now["series"], rec.get("series")):
        for a, b in zip(now["series"], rec.get("series") or []):
            if not _close(a, b):
                out.append(Finding(GATE, FAIL, i, name, "chart data drift in series %r: %s on glass, %s in the build; "
                                   "rebuild so the labels agree" % (a.get("name"), _brief(a), _brief(b))))
                break
        else:
            out.append(Finding(GATE, FAIL, i, name, "chart data drift: %d series on glass, %d in the build"
                               % (len(now["series"]), len(rec.get("series") or []))))
    if now["groups"] != rec.get("groups"):
        out.append(Finding(GATE, FAIL, i, name, "chart type drift: %s on glass, %s in the build"
                           % (now["groups"], rec.get("groups"))))
    want = rec.get("labels") or {}
    for k in sorted(set(want) | set(now["labels"])):
        if want.get(k) != now["labels"].get(k):
            out.append(Finding(GATE, FAIL, i, name, "label drift %s: %r on glass, %r in the build"
                               % (k, now["labels"].get(k), want.get(k))))
    return out


def _brief(s) -> str:
    for k in ("val", "y", "x"):
        if s.get(k):
            return "[%s]" % ", ".join("%g" % v if v is not None else "-" for v in s[k][:6])
    return "[]"


def run(deck, ctx):
    import p17_fingerprints as p17
    th = ctx.theme
    roles = {(e.slot, tuple(e.mods)) for e in th.roles.values()}
    identity = {v["hex"].upper(): k for k, v in th.identity.items()}
    ae = th.roles["accent"]
    accent = (ae.slot, tuple(ae.mods))
    rules = None
    out = []
    n = 0
    man = ctx.manifest
    for i in range(1, ctx.n + 1):
        frames = _frames(ctx, i)
        if not frames:
            continue
        if rules is None:
            rules, broken = p17.load_rules(ctx.fingerprints)
            _hits, missing = p17.canary(rules)
            out += [Finding(GATE, FAIL, None, "rules", "rule %s does not compile" % b) for b in broken]
            if missing:
                out.append(Finding(GATE, FAIL, None, "canary", "the fingerprint canary produced no hit for %s; chart "
                                   "text is unchecked" % ", ".join(r or t for t, r in missing)))
                rules = []
        texts = [text_of(L).strip() for L in ctx.slide(i)["shapes"]]
        for name, descr, part, root in frames:
            n += 1
            if root is None:
                out.append(Finding(GATE, FAIL, i, name, "chart frame points at no chart part"))
                continue
            out += _check_part(ctx, i, name, root, th, roles, identity, accent, rules)
            kind = charts.frame_kind(descr)
            if kind is None:
                out.append(Finding(GATE, FAIL, i, name, "the frame states no kind; its alt text ends "
                                                         "'(chart kind illustrative)' or another stat kind"))
            elif kind not in charts.KINDS:
                out.append(Finding(GATE, FAIL, i, name, "unknown chart kind %r" % kind))
            elif kind in charts.BASIS and charts.BASIS[kind] not in texts:
                out.append(Finding(GATE, FAIL, i, name, "a chart of kind %s with no '%s' label on its slide"
                                   % (kind, charts.BASIS[kind])))
            if man is not None:
                out += _drift(ctx, i, name, descr, root, man)
    if not n:
        return [Finding(GATE, NOTE, None, "", "no chart parts in the deck")]
    if man is None:
        out.append(Finding(GATE, NOTE, None, "drift", "no manifest beside the deck: chart data drift not checked"))
    out.append(Finding(GATE, NOTE, None, "", "%d chart frame(s) read" % n))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
