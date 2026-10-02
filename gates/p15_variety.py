"""P15 variety: families vary, archetypes do not repeat in a section, tables do not run, adjacent slides do not look alike.

  * any three consecutive slides span at least two families (from the archetype tags);
  * no archetype repeats inside a section, except in a section deck.json declares a "series" (ruling 5):
    a use-case map opens it and every repeated member uses a different variant;
  * at most two slides carrying a table in a row, outside the appendix;
  * two adjacent slides whose 12 x 7 occupancy grids have a Jaccard of 0.85 or more look alike.
Sections are PowerPoint's own (p14:sectionLst), else a section-divider slide opens one, else the deck is one
section. An untagged slide fails: the gate cannot see its family.
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict

from _shared import FAIL, Finding, bx, cli, full_bleed, is_drawn
from deckkit.read.deckinfo import status_ranges

GATE, TITLE = "P15", "variety"
COLS, ROWS, COVER = 12, 7, 0.30
JACCARD = 0.85
MAX_TABLES = 2


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
        if ctx.tags()[i - 1]["archetype"] == "section-divider" and cur[1]:
            out.append(cur)
            cur = ("section %d" % (len(out) + 1), [])
        cur[1].append(i)
    out.append(cur)
    return out


def occupancy(ctx, i) -> set:
    cw, ch = ctx.W / COLS, ctx.H / ROWS
    cover = defaultdict(float)
    for L in ctx.slide(i)["shapes"]:
        if not is_drawn(L) or full_bleed(L, ctx) or len(L.get("container_of") or []) >= 3:
            continue
        x0, y0, x1, y1 = bx(L)
        for c in range(max(0, int(x0 / cw)), min(COLS, int(x1 / cw) + 1)):
            for r in range(max(0, int(y0 / ch)), min(ROWS, int(y1 / ch) + 1)):
                ox = min(x1, (c + 1) * cw) - max(x0, c * cw)
                oy = min(y1, (r + 1) * ch) - max(y0, r * ch)
                if ox > 0 and oy > 0:
                    cover[(c, r)] += ox * oy / (cw * ch)
    return {k for k, v in cover.items() if v >= COVER}


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
            first = tags[members[0] - 1]["archetype"]
            variants = defaultdict(list)
            for i in members:
                variants[tags[i - 1]["archetype"]].append(tags[i - 1]["variant"])
            bad = [a for a in repeats if len(set(variants[a])) != len(variants[a])]
            if first != "use-case-map":
                out.append(Finding(GATE, FAIL, members[0], name, "series section not opened by a use-case map"))
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
    appendix = {i for a, b in status_ranges(ctx.dr).get("appendix", []) for i in range(a, b + 1)}
    run_ = []
    for i in idx:
        has_table = any(L["kind"] == "cell" for L in ctx.slide(i)["shapes"])
        run_ = run_ + [i] if has_table and i not in appendix else []
        if len(run_) == MAX_TABLES + 1:
            out.append(Finding(GATE, FAIL, run_[0], "", "%d table slides in a row (%s)" % (len(run_), ", ".join(map(str, run_)))))
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
