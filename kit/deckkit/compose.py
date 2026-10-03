"""Composed components: the flagship's devices rebuilt from kit primitives under the house rules (ruling 10).

Each function lays out a whole row or panel inside one box, so siblings share offsets (P07) and the box fills
(P24). Text is measured before anything is drawn and refuses overflow; nothing is clamped. Strong fills are the
brand (`accent`, `accent-deep`) and the near-black panel (`ink-deep`) on a light slide (ruling 12); text on a fill
takes that fill's ON_FILL role.

    icon_cards      solid cards, a glyph over a heading and one or two lines (the flagship's SEE / ACT / DECIDE row)
    numbered_rows   a panel under a solid header band: numbered discs, a bold lead, one line under each
    stat_band       a near-black band of two to four stats, brand numerals, paper labels, basis chips
    pressure_band   a solid brand band: a label block at its left, then columns of lead and line
    stage_chain     a chevron header in a strong fill, a glyph under each step, then each step's lines
    ladder          a staircase of levels rising left to right, a coded chip on each (L0 to L4)
    ask_cards       numbered decision cards (01, 02 ...) with a verb label, chevrons between them
    milestone_rail  a rail of ringed dots, a date and a label under each
"""
from __future__ import annotations

from . import prims
from .canvas import Box
from .errors import GeometryError, Overflows
from .glyphs import glyph
from .prims import ON_FILL, canvas_for, theme_of
from .text import Para, Run, need_height, textbox

PAD = 0.22          # inside a card or band, x k
GAP = 0.20          # between siblings, x k
HEAD_PT, BODY_PT, LABEL_PT = 14.0, 11.0, 10.0


def _paras(head, body, head_role, body_role, *, head_pt=HEAD_PT, body_pt=BODY_PT, align="left", gap=3.0):
    ps = []
    if head:
        ps.append(Para((Run(head, head_role, bold=True, size=head_pt),), align=align))
    if body:
        ps.append(Para((Run(body, body_role, size=body_pt),), align=align, space_before=gap if head else 0.0))
    return ps


def _need(paras, w, th):
    return need_height(paras, w, th) if paras else 0.0


def _cols(box: Box, n: int, gutter: float) -> list[Box]:
    if n < 1:
        raise GeometryError("columns", need=">= 1", have=n)
    return box.split_cols(n, gutter)


def icon_cards(slide, box: Box, items, *, fill="accent", glyph_pt=0.55, align="center", name: str, theme=None):
    """items: [(glyph, head, body)]. Solid cards in one row; every stack starts at one offset, centred on the
    fullest card's height, so the row reads level and no card floats at its top."""
    th = theme_of(theme)
    k = canvas_for(slide).k
    if fill not in ON_FILL:
        raise GeometryError("icon_cards %s fill" % name, need="an ON_FILL role", have=fill)
    on = ON_FILL[fill]
    cols = _cols(box, len(items), GAP * k)
    iw = cols[0].w - 2 * PAD * k
    stacks = [_paras(h, b, on, on, align=align) for _g, h, b in items]
    gh = glyph_pt * k
    need = max(gh + 0.14 * k + _need(p, iw, th) for p in stacks)
    if need > box.h - 2 * PAD * k:
        raise Overflows("icon_cards %s" % name, need=round(need + 2 * PAD * k, 3), have=round(box.h, 3),
                        hint="a taller box, fewer words, or fewer cards")
    top = box.y + (box.h - need) / 2
    for i, ((g, _h, _b), c, paras) in enumerate(zip(items, cols, stacks), 1):
        prims.block(slide, c, fill=fill, name="%s.%d.card" % (name, i), theme=th)
        gx = c.x + (c.w - gh) / 2 if align == "center" else c.x + PAD * k
        glyph(slide, g, Box(gx, top, gh, gh), role=on, shape_name="%s.%d.icon" % (name, i), theme=th)
        ty = top + gh + 0.14 * k
        textbox(slide, Box(c.x + PAD * k, ty, iw, _need(paras, iw, th)), paras, "%s.%d.text" % (name, i), th,
                background=fill)


def numbered_rows(slide, box: Box, items, *, header=None, header_glyph=None, header_fill="accent",
                  disc_fill="accent", fill="card", name: str, theme=None):
    """A panel: an optional solid header band with its label, then rows of a numbered disc, a bold lead and one
    line. Rows are spread evenly down the panel so it fills without a stretched card."""
    th = theme_of(theme)
    k = canvas_for(slide).k
    prims.card(slide, box, fill=fill, line=None, name="%s.panel" % name, theme=th)
    y = box.y
    if header:
        hh = 0.42 * k
        if header_glyph:
            prims.block(slide, Box(box.x, box.y, box.w, hh), fill=header_fill, radius_in=0,
                        name="%s.header" % name, theme=th)
            gs = hh * 0.6
            glyph(slide, header_glyph, Box(box.x + PAD * k, box.y + (hh - gs) / 2, gs, gs), role=ON_FILL[header_fill],
                  shape_name="%s.header.icon" % name, theme=th)
            lp = [Para((Run(header, ON_FILL[header_fill], bold=True, size=12.0),))]
            lx = box.x + PAD * k + gs + 0.12 * k
            textbox(slide, Box(lx, box.y, box.r - PAD * k - lx, hh), lp, "%s.header.text" % name, th,
                    background=header_fill, anchor="middle")
        else:
            prims.tab(slide, Box(box.x, box.y, box.w, hh), header, fill=header_fill, name="%s.header" % name, theme=th)
        y += hh
    d = 0.38 * k
    tx = box.x + PAD * k + d + 0.16 * k
    tw = box.r - PAD * k - tx
    rows = [_paras(h, b, "ink-deep", "ink", head_pt=13.0) for h, b in items]
    hs = [max(d, _need(p, tw, th)) for p in rows]
    room = box.b - 0.12 * k - (y + PAD * k)            # the foot pad matches the header's own air (P08)
    if sum(hs) > room:
        raise Overflows("numbered_rows %s" % name, need=round(sum(hs) + 2 * PAD * k + (y - box.y), 3),
                        have=round(box.h, 3), hint="fewer rows or shorter lines")
    slot = max(hs)                       # one pitch for every row: a measured wrap never shifts its neighbours
    n = len(hs)
    pitch = (room - slot) / (n - 1) if n > 1 else 0.0
    ry = y + PAD * k if n > 1 else y + PAD * k + (room - slot) / 2
    for i, paras in enumerate(rows, 1):
        prims.disc(slide, Box(box.x + PAD * k, ry, d, d), i, fill=disc_fill, name="%s.%d.disc" % (name, i), theme=th)
        textbox(slide, Box(tx, ry, tw, _need(paras, tw, th)), paras, "%s.%d.text" % (name, i), th, background=fill)
        ry += pitch


def stat_band(slide, box: Box, stats, *, fill="ink-deep", name: str, theme=None):
    """stats: [(value, label, kind)]. A near-black band with brand numerals and paper labels; every stat keeps
    its kind (P23) and its basis chip. Returns the stat names for the manifest's numbers record."""
    th = theme_of(theme)
    k = canvas_for(slide).k
    prims.block(slide, box, fill=fill, name="%s.band" % name, theme=th)
    inner = Box(box.x + PAD * k, box.y + PAD * k * 0.8, box.w - 2 * PAD * k, box.h - 1.6 * PAD * k)
    cols = _cols(inner, len(stats), 0.40 * k)
    names = []
    num_role = "accent-ink" if fill in ("ink-deep", "ink-strong", "navy") else ON_FILL[fill]
    need = max(prims.stat_height(slide, c.w, v, lab, kind=kind, theme=th) for (v, lab, kind), c in zip(stats, cols))
    if need > inner.h:
        raise Overflows("stat_band %s" % name, need=round(need + 1.6 * PAD * k, 3), have=round(box.h, 3))
    sy = box.y + (box.h - need) / 2                   # the stats sit centred in the band, no dark air below
    for i, ((v, lab, kind), c) in enumerate(zip(stats, cols), 1):
        nm = "%s.%d" % (name, i)
        prims.stat(slide, Box(c.x, sy, c.w, need), v, lab, kind=kind, role=num_role, background=fill,
                   label_role=ON_FILL[fill], name=nm, theme=th)
        names.append(nm)
    return names


def pressure_band(slide, box: Box, label: str, items, *, fill="accent", label_w=1.7, name: str, theme=None):
    """A solid band: a label block at its left (deeper fill), then columns of a bold lead and one line, all in
    the fill's text role."""
    th = theme_of(theme)
    k = canvas_for(slide).k
    on = ON_FILL[fill]
    deep = "accent-deep" if fill == "accent" else "ink-deep"
    lw = label_w * k
    prims.block(slide, box, fill=fill, name="%s.band" % name, theme=th)
    prims.block(slide, Box(box.x, box.y, lw, box.h), fill=deep, name="%s.label.block" % name, theme=th)
    lp = [Para((Run(label, ON_FILL[deep], bold=True, size=13.0),))]
    textbox(slide, Box(box.x + 0.16 * k, box.y + 0.1 * k, lw - 0.32 * k, box.h - 0.2 * k), lp, "%s.label" % name,
            th, background=deep, anchor="middle")
    area = Box(box.x + lw + PAD * k, box.y, box.w - lw - 2 * PAD * k, box.h)
    cols = _cols(area, len(items), 0.25 * k)
    stacks = [_paras(h, b, on, on, head_pt=12.0, body_pt=10.5) for h, b in items]
    need = max(_need(p, cols[0].w, th) for p in stacks)
    if need > box.h - 0.2 * k:
        raise Overflows("pressure_band %s" % name, need=round(need + 0.2 * k, 3), have=round(box.h, 3))
    ty = box.y + (box.h - need) / 2
    for i, (p, c) in enumerate(zip(stacks, cols), 1):
        textbox(slide, Box(c.x, ty, c.w, _need(p, c.w, th)), p, "%s.%d.text" % (name, i), th, background=fill)


def stage_chain(slide, box: Box, stages, *, fill="accent", glyph_pt=0.45, facts=None, name: str, theme=None):
    """stages: [(label, glyph, head, body)]. A chevron header in a strong fill, then under each step a glyph in
    the brand and the step's lead and lines, columns aligned to the chevrons. facts: per stage [(label, value)],
    set as label-value rows under a hairline and spread to the box's foot. Returns the y of the content's foot."""
    th = theme_of(theme)
    k = canvas_for(slide).k
    hh = 0.48 * k
    prims.step_header(slide, Box(box.x, box.y, box.w, hh), [s[0] for s in stages], fill=fill,
                      name="%s.steps" % name, theme=th)
    n = len(stages)
    cols = _cols(Box(box.x, box.y, box.w, box.h), n, 0.04 * k)
    gh = glyph_pt * k
    gy = box.y + hh + 0.18 * k
    stacks = [_paras(h, b, "ink-deep", "ink", head_pt=12.0, body_pt=10.5, align="center") for _l, _g, h, b in stages]
    tw = cols[0].w - 0.30 * k
    need = gh + 0.12 * k + max(_need(p, tw, th) for p in stacks)
    if gy + need > box.b:
        raise Overflows("stage_chain %s" % name, need=round(gy + need - box.y, 3), have=round(box.h, 3))
    foot = gy + need
    fstacks = []
    if facts:
        fstacks = [[q for j, (lab, v) in enumerate(f) for q in
                    (Para((Run(lab, "ink-muted", bold=True, size=LABEL_PT),), align="center",
                          space_before=0.0 if j == 0 else 6.0),
                     Para((Run(v, "ink", size=BODY_PT),), align="center"))] for f in facts]
        fneed = max(_need(q, tw, th) for q in fstacks)
        fy = foot + 0.16 * k
        if fy + 0.14 * k + fneed > box.b:
            raise Overflows("stage_chain %s facts" % name, need=round(fy + 0.14 * k + fneed - box.y, 3),
                            have=round(box.h, 3))
        fy = max(fy, box.b - 0.14 * k - fneed - 0.12 * k)            # spread: the facts rest on the box's foot
        foot = fy + 0.14 * k + fneed
    for i, ((_l, g, _h, _b), c, p) in enumerate(zip(stages, cols, stacks), 1):
        glyph(slide, g, Box(c.x + (c.w - gh) / 2, gy, gh, gh), role="accent", shape_name="%s.%d.icon" % (name, i),
              theme=th)
        textbox(slide, Box(c.x + 0.15 * k, gy + gh + 0.12 * k, tw, _need(p, tw, th)), p, "%s.%d.text" % (name, i),
                th)
        if fstacks:
            prims.hairline(slide, (c.x + 0.3 * k, fy), (c.r - 0.3 * k, fy), name="%s.%d.rule" % (name, i), theme=th)
            q = fstacks[i - 1]
            textbox(slide, Box(c.x + 0.15 * k, fy + 0.14 * k, tw, _need(q, tw, th)), q, "%s.%d.facts" % (name, i), th)
    return foot


def ladder(slide, box: Box, levels, *, name: str, theme=None, chip_fill="accent", top_fill="accent"):
    """levels, lowest first: [(code, head, body)]. A staircase rising left to right; each level a card with a
    coded chip. The top level is drawn in the brand fill: the goal the ladder climbs to."""
    th = theme_of(theme)
    k = canvas_for(slide).k
    n = len(levels)
    gap = 0.12 * k
    rh = (box.h - gap * (n - 1)) / n
    step = min(0.35 * k, box.w * 0.25 / max(1, n - 1))
    w = box.w - step * (n - 1)
    chip = min(0.52 * k, rh - 0.16 * k)
    for i, (code, head, body) in enumerate(levels):
        y = box.b - (i + 1) * rh - i * gap
        x = box.x + i * step
        top = i == n - 1
        f = top_fill if top else "card"
        cf = "ink-deep" if top else chip_fill
        if top:
            prims.block(slide, Box(x, y, w, rh), fill=f, name="%s.%d.card" % (name, i), theme=th)
        else:
            prims.card(slide, Box(x, y, w, rh), fill=f, line=None, name="%s.%d.card" % (name, i), theme=th)
        cy = y + (rh - chip) / 2
        prims.block(slide, Box(x + 0.12 * k, cy, chip, chip), fill=cf, name="%s.%d.chip" % (name, i), theme=th)
        textbox(slide, Box(x + 0.12 * k, cy, chip, chip), [Para((Run(code, ON_FILL[cf], bold=True, size=11.0),),
                align="center")], "%s.%d.code" % (name, i), th, background=cf, anchor="middle")
        tx = x + 0.12 * k + chip + 0.14 * k
        tw = x + w - 0.12 * k - tx
        on = ON_FILL[f] if top else "ink-deep"
        p = _paras(head, body, on, ON_FILL[f] if top else "ink", head_pt=12.0, body_pt=10.0, gap=1.0)
        h = _need(p, tw, th)
        if h > rh - 0.08 * k:
            raise Overflows("ladder %s level %s" % (name, code), need=round(h + 0.08 * k, 3), have=round(rh, 3))
        textbox(slide, Box(tx, y + (rh - h) / 2, tw, h), p, "%s.%d.text" % (name, i), th, background=f)


def ask_cards(slide, box: Box, items, *, name: str, theme=None, fill="card"):
    """items: [(verb, glyph, head, body)]. Numbered decision cards: a large brand numeral and the verb as a
    label, a glyph at the top right, the head and one or two lines; brand chevrons between cards."""
    th = theme_of(theme)
    k = canvas_for(slide).k
    arrow = 0.34 * k
    n = len(items)
    cw = (box.w - arrow * (n - 1)) / n
    cols = [Box(box.x + i * (cw + arrow), box.y, cw, box.h) for i in range(n)]
    iw = cw - 2 * PAD * k
    stacks = []
    for i, (verb, _g, head, body) in enumerate(items, 1):
        stacks.append([Para((Run("%02d" % i, "accent-ink", bold=True, size=24.0),)),
                       Para((Run(verb.upper(), "accent-ink", bold=True, size=LABEL_PT),), space_before=2.0)]
                      + _paras(head, body, "ink-deep", "ink", head_pt=13.0, gap=3.0))
    stacks = [[s[0], s[1], Para(s[2].runs, space_before=8.0)] + s[3:] for s in stacks]
    need = max(_need(p, iw, th) for p in stacks)
    if need > box.h - 2 * PAD * k:
        raise Overflows("ask_cards %s" % name, need=round(need + 2 * PAD * k, 3), have=round(box.h, 3))
    top = box.y + PAD * k
    for i, ((_v, g, _h, _b), c, p) in enumerate(zip(items, cols, stacks), 1):
        prims.card(slide, c, fill=fill, line=None, name="%s.%d.card" % (name, i), theme=th)
        gs = 0.42 * k
        glyph(slide, g, Box(c.r - PAD * k - gs, top, gs, gs), role="ink-strong", shape_name="%s.%d.icon" % (name, i),
              theme=th)
        textbox(slide, Box(c.x + PAD * k, top, iw, _need(p, iw, th)), p, "%s.%d.text" % (name, i), th,
                background=fill)
        if i < n:
            a = 0.28 * k
            glyph(slide, "chevrons-right", Box(c.r + (arrow - a) / 2, c.y + (c.h - a) / 2, a, a), role="accent",
                  shape_name="%s.%d.next" % (name, i), theme=th)


def milestone_rail(slide, box: Box, points, *, name: str, theme=None):
    """points: [(date, label)]. A hairline rail through ringed brand dots, the date in bold and a label under
    each, centred on its dot."""
    th = theme_of(theme)
    k = canvas_for(slide).k
    n = len(points)
    d = 0.30 * k
    cols = _cols(box, n, 0.10 * k)
    cy = box.y + d / 2
    prims.hairline(slide, (cols[0].cx, cy), (cols[-1].cx, cy), role="rule-strong", name="%s.rail" % name, theme=th)
    stacks = [_paras(dt, lab, "ink-deep", "ink", head_pt=12.0, body_pt=10.5, align="center", gap=1.0)
              for dt, lab in points]
    need = max(_need(p, cols[0].w, th) for p in stacks)
    if d + 0.10 * k + need > box.h:
        raise Overflows("milestone_rail %s" % name, need=round(d + 0.10 * k + need, 3), have=round(box.h, 3))
    for i, (c, p) in enumerate(zip(cols, stacks), 1):
        prims.circle(slide, Box(c.cx - d / 2, box.y, d, d), fill="paper", line="accent",
                     name="%s.%d.ring" % (name, i), theme=th)
        dd = d * 0.46
        prims.circle(slide, Box(c.cx - dd / 2, box.y + (d - dd) / 2, dd, dd), fill="accent",
                     name="%s.%d.dot" % (name, i), theme=th)
        textbox(slide, Box(c.x, box.y + d + 0.10 * k, c.w, _need(p, c.w, th)), p, "%s.%d.text" % (name, i), th)
