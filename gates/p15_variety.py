"""P15 variety: families vary, archetypes do not repeat in a section, tables do not run, adjacent slides do not look alike.

  * any three consecutive slides span at least two families (from the archetype tags);
  * no archetype repeats inside a section, except in a section deck.json declares a "series" (ruling 5):
    a use-case map opens it (or, for a technical series, a layered architecture master) and every repeated member
    uses a different variant. The opener is the section's first slide outside the Frame family, so a divider may
    stand in front of it;
  * at most two slides carrying a table in a row, outside the appendix;
  * two adjacent slides whose 12 x 7 occupancy grids (each cell marked strong mass or other drawn content) have a
    Jaccard of 0.85 or more look alike;
  * no family carries more than 40% of the content slides (every family but Frame); one slide of a family is
    always allowed, so a two-slide deck is not failed for its arithmetic;
  * foot bands: at most 1 in 5 content slides (one always allowed) end on a full-width labelled band, and no two
    adjacent slides do. A foot band is a solid-filled shape (any fill but paper or near-white) at least 85% of the
    content band's width and under 1.3in (x k) tall, whose bottom sits in the lower quarter of the content band,
    that carries text (its own, or a text block painted on it), with nothing drawn below it but a short source
    line (12 words or fewer). A band along the foot as a cadence makes every slide look alike; the alternatives
    are a side rail, a header strip, or the shared items folded into the device.
Sections are PowerPoint's own (p14:sectionLst), else a section-divider slide opens one and the section takes the
divider's title as its name (what deck.json "series" names), else the deck is one section. An untagged slide fails: the gate cannot see its family.
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict

from _shared import FAIL, Finding, bx, cli, full_bleed, has_text, is_drawn, words
from deckkit.read.deckinfo import status_ranges

GATE, TITLE = "P15", "variety"
SERIES_OPENERS = ("use-case-map", "layered-architecture")
COLS, ROWS, COVER = 12, 7, 0.30
JACCARD = 0.85
MAX_TABLES = 2
MAX_FAMILY_SHARE = 0.40
FOOT_SHARE = 0.20       # at most 1 in 5 content slides end on a foot band
FOOT_W = 0.85           # of the content band's width
FOOT_H = 1.3            # in, x k: taller is a panel, not a band
FOOT_LOW = 0.75         # the band's bottom sits below this share of the content band
SOURCE_WORDS = 12       # a text line under the band this short is a source line, not content


def sections(ctx) -> list[tuple[str, list[int]]]:
    """[(name, [slide index, ...])] in deck order."""
    dr = ctx.dr
    by_id = {sid: i for i, sid in enumerate(dr.slide_ids, start=1)}
    lst = dr.pres.find(".//{*}sectionLst")
    if lst is not None:
        out = []
        for sec in lst:
            ids = [int(s.get("id", "0")) for s in sec.iter("{*}sldId")]
            out.append((sec.get("name", ""), [by_id[x] for x in ids if x in by_id]))
        return [o for o in out if o[1]]
    out, cur = [], ("", [])
    for i in range(1, ctx.n + 1):
        if ctx.tags()[i - 1]["archetype"] == "section-divider":
            if cur[1]:
                out.append(cur)
            cur = (divider_title(ctx, i) or "section %d" % (len(out) + 1), [])
        cur[1].append(i)
    out.append(cur)
    return out


def divider_title(ctx, i) -> str:
    """A divider's title: its title shape's text, else its longest text."""
    texts = [(L.get("name") or "", " ".join(((L.get("text") or {}).get("text") or "").split()))
             for L in ctx.slide(i)["shapes"]]
    texts = [(n, t) for n, t in texts if t]
    named = [t for n, t in texts if n in ("title", "slot.title", "slot.headline")]
    return (named or sorted((t for _, t in texts), key=lambda t: -len(t.split())) or [""])[0]


def _strong(L) -> bool:
    """A strong fill (dark or saturated): the masses the eye reads first. Dense slides occupy every cell, so the
    look is told by where the strong masses sit, not by occupancy alone."""
    f = L.get("fill") or {}
    h = f.get("hex") if f.get("type") == "solid" else None
    if not h or len(h) != 6:
        return False
    r, g, b = (int(h[k:k + 2], 16) / 255 for k in (0, 2, 4))
    mx, mn = max(r, g, b), min(r, g, b)
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return lum < 0.45 or (mx > 0 and (mx - mn) / mx >= 0.5 and mx >= 0.5)


def occupancy(ctx, i) -> set:
    """Cells of a 12 x 7 grid, each marked by class: a strong mass, or any other drawn content."""
    cw, ch = ctx.W / COLS, ctx.H / ROWS
    cover = defaultdict(float)
    for L in ctx.slide(i)["shapes"]:
        if not is_drawn(L) or full_bleed(L, ctx) or len(L.get("container_of") or []) >= 3:
            continue
        cls = "strong" if _strong(L) else "drawn"
        x0, y0, x1, y1 = bx(L)
        for c in range(max(0, int(x0 / cw)), min(COLS, int(x1 / cw) + 1)):
            for r in range(max(0, int(y0 / ch)), min(ROWS, int(y1 / ch) + 1)):
                ox = min(x1, (c + 1) * cw) - max(x0, c * cw)
                oy = min(y1, (r + 1) * ch) - max(y0, r * ch)
                if ox > 0 and oy > 0:
                    cover[(c, r, cls)] += ox * oy / (cw * ch)
    cells = {k for k, v in cover.items() if v >= COVER}
    strong = {(c, r) for c, r, k in cells if k == "strong"}
    return {(c, r, "strong") for c, r in strong} | {(c, r, "drawn") for c, r, k in cells if (c, r) not in strong}


def _near_white(hx: str) -> bool:
    try:
        r, g, b = (int(hx[k:k + 2], 16) / 255 for k in (0, 2, 4))
    except (TypeError, ValueError):
        return False
    return min(r, g, b) >= 0.97


def foot_band(ctx, i):
    """The leaf a content slide ends on when it is a full-width labelled foot band, else None."""
    band = ctx.canvas.content
    k = ctx.k
    shapes = ctx.slide(i)["shapes"]
    paper = (ctx.theme.hex("paper") or "").upper()
    for L in shapes:
        f = L.get("fill") or {}
        hx = (f.get("hex") or "").upper()
        if L["kind"] != "sp" or L.get("line_like") or f.get("type") != "solid" or hx == paper or _near_white(hx):
            continue
        x0, y0, x1, y1 = bx(L)
        if x1 - x0 < FOOT_W * band.w or not (0 < y1 - y0 < FOOT_H * k) or y1 < band.y + FOOT_LOW * band.h:
            continue
        labelled = has_text(L) or any(
            M is not L and has_text(M) and M.get("z", 0) > L.get("z", 0) and bx(M)[0] >= x0 - 0.02 and
            bx(M)[2] <= x1 + 0.02 and bx(M)[1] >= y0 - 0.02 and bx(M)[3] <= y1 + 0.02 for M in shapes)
        if not labelled:
            continue
        below = [M for M in shapes if M is not L and is_drawn(M) and bx(M)[1] >= y1 - 0.02 and
                 not (has_text(M) and not is_drawn_box(M) and words(M["text"]["text"]) <= SOURCE_WORDS)]
        if not below:
            return L
    return None


def is_drawn_box(L) -> bool:
    """A leaf that paints something other than words: a fill, an outline or a picture."""
    return (L.get("fill") or {}).get("type", "none") not in ("none", None) or \
        (L.get("line") or {}).get("type", "none") not in ("none", None) or L["kind"] == "pic"


def _content(ctx, i, fam) -> bool:
    if ctx.tags()[i - 1]["archetype"]:
        return fam.get(i) not in (None, "Frame")
    return ctx.slide(i)["text"]["words_content"] > 20


def foot_bands(ctx, fam) -> list[Finding]:
    out = []
    content = [i for i in range(1, ctx.n + 1) if _content(ctx, i, fam)]
    bands = {}
    for i in content:
        L = foot_band(ctx, i)
        if L is not None:
            bands[i] = L
    cap = max(1, int(FOOT_SHARE * len(content)))
    if len(bands) > cap:
        first = min(bands)
        out.append(Finding(GATE, FAIL, first, bands[first]["name"], "%d of %d content slides end on a full-width "
                           "labelled foot band (max %d, 1 in 5): slides %s" % (len(bands), len(content), cap,
                                                                               ", ".join(map(str, sorted(bands))))))
    for a in sorted(bands):
        if a + 1 in bands:
            out.append(Finding(GATE, FAIL, a + 1, bands[a + 1]["name"], "slides %d and %d both end on a full-width "
                               "labelled foot band" % (a, a + 1)))
    return out


def run(deck, ctx):
    out = []
    tags = ctx.tags()
    fam = {}
    for t in tags:
        if t["archetype"] is None:
            out.append(Finding(GATE, FAIL, t["index"], "", "untagged slide: its family is unknown (tag it archetype:variant)"))
        else:
            fam[t["index"]] = ctx.family(t["archetype"])
            if fam[t["index"]] is None:
                out.append(Finding(GATE, FAIL, t["index"], t["tag"], "archetype %r is not in the taxonomy" % t["archetype"]))
    series = set(ctx.deck_json.get("series") or [])
    secs = sections(ctx)
    in_series = {}
    for name, members in secs:
        for i in members:
            in_series[i] = name in series
        arch = Counter(tags[i - 1]["archetype"] for i in members if tags[i - 1]["archetype"])
        repeats = {a: c for a, c in arch.items() if c > 1}
        if not repeats:
            continue
        if name in series:
            first = next((tags[i - 1]["archetype"] for i in members if fam.get(i) not in (None, "Frame")), None)
            variants = defaultdict(list)
            for i in members:
                variants[tags[i - 1]["archetype"]].append(tags[i - 1]["variant"])
            bad = [a for a in repeats if len(set(variants[a])) != len(variants[a])]
            if first not in SERIES_OPENERS:
                out.append(Finding(GATE, FAIL, members[0], name, "series section not opened by a use-case map or a "
                                   "layered architecture master"))
            if len(repeats) > 1:
                out.append(Finding(GATE, FAIL, members[0], name, "a series repeats one archetype, this repeats %s"
                                   % ", ".join(sorted(repeats))))
            for a in bad:
                out.append(Finding(GATE, FAIL, members[0], name, "series members of %s share a variant" % a))
        else:
            for a, c in repeats.items():
                where = [i for i in members if tags[i - 1]["archetype"] == a]
                out.append(Finding(GATE, FAIL, where[1], name or "deck", "%s appears %d times in one section (slides %s)"
                                   % (a, c, ", ".join(map(str, where)))))
    idx = list(range(1, ctx.n + 1))
    for w in zip(idx, idx[1:], idx[2:]):
        fs = [fam.get(i) for i in w]
        if None in fs:
            continue
        if len(set(fs)) < 2:
            if all(in_series.get(i) for i in w) and len({tags[i - 1]["variant"] for i in w}) == 3:
                continue
            out.append(Finding(GATE, FAIL, w[0], "", "slides %d-%d are all %s" % (w[0], w[2], fs[0])))
    content = [i for i, f in fam.items() if f and f != "Frame"]
    share = Counter(fam[i] for i in content)
    for f, c in sorted(share.items()):
        if c > max(1, MAX_FAMILY_SHARE * len(content)):
            where = [i for i in content if fam[i] == f]
            out.append(Finding(GATE, FAIL, where[0], f, "%d of %d content slides are %s (%.0f%%, max %.0f%%): slides %s"
                               % (c, len(content), f, 100.0 * c / len(content), 100 * MAX_FAMILY_SHARE,
                                  ", ".join(map(str, where)))))
    appendix = {i for a, b in status_ranges(ctx.dr).get("appendix", []) for i in range(a, b + 1)}
    run_ = []
    for i in idx:
        has_table = any(L["kind"] == "cell" for L in ctx.slide(i)["shapes"])
        run_ = run_ + [i] if has_table and i not in appendix else []
        if len(run_) == MAX_TABLES + 1:
            out.append(Finding(GATE, FAIL, run_[0], "", "%d table slides in a row (%s)" % (len(run_), ", ".join(map(str, run_)))))
    out += foot_bands(ctx, fam)
    occ = {i: occupancy(ctx, i) for i in idx}
    for a, b in zip(idx, idx[1:]):
        u = occ[a] | occ[b]
        if not u:
            continue
        j = len(occ[a] & occ[b]) / len(u)
        if j >= JACCARD:
            out.append(Finding(GATE, FAIL, b, "", "looks like slide %d (occupancy Jaccard %.2f)" % (a, j)))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
