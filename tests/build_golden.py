#!/usr/bin/env python3
"""The golden fixture: a seven-slide WIDE deck in the sigmoid theme, drawn only from kit primitives and
text, tagged per slide, that every static gate must pass. The negatives runner copies it and plants one
breakage per copy; a gate that does not go red on its plant has proved nothing.

    $PY tests/build_golden.py                 # writes .cache/golden.pptx, its manifest and deck.json
    $PY tests/build_golden.py --out X.pptx    # the same deck anywhere (gate P21 rebuilds it this way)

Slides (archetype:variant, family):
  1 cover:title-only            Frame     one two-tone title, nothing else
  2 pillars:icon-row            Columns   three cards, each a glyph, a heading and a measured body
  3 process-flow:chevron-row    Sequence  a chevron header, four step cards, three arrows card to card
  4 stat-hero:stat-row          Number    four stats (measured, delivered, illustrative, target), a glyph each
  5 matrix:table                Field     a small readiness table and a side card
  6 from-to:two-panel           Split     two zones, one arrow between them
  7 closing:line                Frame     the closing line

Every text box is sized from deckkit.measure at build time (tight fit, no slack beyond SLACK), so a
build with SLACK patched to 0.5 produces boxes that gate P02 rejects. Copy is fictional: a regional
planning team with no client, brand or person in it. Module constants are patch points for the
builder-refusal tests; nothing here is ever edited by a test.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(SKILL / "kit"))

from pptx import Presentation  # noqa: E402
from pptx.util import Emu  # noqa: E402

from deckkit import glyphs, ooxml, package, prims, tag, text  # noqa: E402
from deckkit.canvas import EMU_PER_IN, WIDE, Box  # noqa: E402
from deckkit.read.ns import NS  # noqa: E402
from deckkit.text import Para, Run  # noqa: E402
from deckkit.theme import Theme  # noqa: E402

BASE = SKILL / "kit" / "assets" / "base-wide.pptx"
THEME_PATH = SKILL / "themes" / "sigmoid.json"
DEFAULT_OUT = SKILL / ".cache" / "golden.pptx"
TITLE = "Golden fixture"

# patch points (the refusal tests patch these, never the source)
BODY_PT = 11.0
HEAD_PT = 13.0
CELL_PT = 11.0
PAD = 0.20            # card padding
ICON = 0.45           # glyph side
GAP = 0.10            # between stacked text blocks
CELL_MY = 0.11        # a table cell's top and bottom margin

_A = "{%s}" % NS["a"]
NO_TABLE_STYLE = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"     # PowerPoint's built-in "No Style, No Grid"

C = WIDE.content       # 0.50, 0.85, 12.403 x 5.99


# ------------------------------------------------------------------ measured helpers

def need(paras, w: float, theme, size: float) -> float:
    """Height the paragraphs need at width w (measured, SLACK applied), rounded UP to 0.0001 in because
    measure.fits reports need_in rounded to four places."""
    n = text.check_fit("probe", paras, Box(0, 0, w, 100.0), theme, size=size).need_in
    return math.ceil(n * 10000 + 1) / 10000.0


def stack(slide, x: float, y: float, w: float, blocks, theme, prefix: str) -> float:
    """Text blocks one under another, each box exactly its measured height. Returns the bottom."""
    for i, (paras, size) in enumerate(blocks):
        h = need(paras, w, theme, size)
        text.textbox(slide, Box(x, y, w, h), paras, "%s.%d" % (prefix, i + 1), theme, size=size)
        y += h + (GAP if i + 1 < len(blocks) else 0.0)
    return y


def blocks_height(blocks, w, theme) -> float:
    hs = [need(p, w, theme, s) for p, s in blocks]
    return sum(hs) + GAP * (len(hs) - 1)


def head(t):
    return [Para(Run(t, role="ink-deep", bold=True))]


def body(*lines):
    return [Para(Run(t, role="ink"), space_after=4.0 if i + 1 < len(lines) else 0.0) for i, t in enumerate(lines)]


def new_slide(prs, archetype, variant):
    s = prs.slides.add_slide(prs.slide_layouts[0])
    tag.tag(s, archetype, variant)
    return s


# ------------------------------------------------------------------ the table (no table module yet)

def table(slide, x, y, col_w, rows, theme, name):
    """A plain table: header row in ink-strong with paper text, body rows on paper, one hairline under
    every row, explicit margins, every cell's text written by text.write and sized by measurement."""
    from lxml import etree
    mx, my = 0.10, CELL_MY
    heights = []
    for ri, row in enumerate(rows):
        hh = 0.0
        for ci, cell in enumerate(row):
            paras = [Para(Run(cell, role="paper" if ri == 0 else "ink", bold=ri == 0))]
            hh = max(hh, need(paras, col_w[ci] - 2 * mx, theme, CELL_PT) + 2 * my)
        heights.append(hh)
    gf = slide.shapes.add_table(len(rows), len(col_w), *Box(x, y, sum(col_w), sum(heights)).emu)
    gf.name = name
    tbl = gf.table
    tblPr = tbl._tbl.tblPr
    for k in ("firstRow", "bandRow", "firstCol", "lastRow", "lastCol", "bandCol"):
        tblPr.set(k, "0")
    sid = tblPr.find(_A + "tableStyleId")
    if sid is None:
        sid = etree.SubElement(tblPr, _A + "tableStyleId")
    sid.text = NO_TABLE_STYLE
    for ci, w in enumerate(col_w):
        tbl.columns[ci].width = Emu(int(round(w * EMU_PER_IN)))
    for ri, h in enumerate(heights):
        tbl.rows[ri].height = Emu(int(round(h * EMU_PER_IN)))
    for ri, row in enumerate(rows):
        for ci, cell_text in enumerate(row):
            cell = tbl.cell(ri, ci)
            paras = [Para(Run(cell_text, role="paper" if ri == 0 else "ink", bold=ri == 0))]
            text.write(cell.text_frame, paras, theme, size=CELL_PT, anchor="middle")
            tcPr = cell._tc.get_or_add_tcPr()
            for c in list(tcPr):
                tcPr.remove(c)
            for k, v in (("marL", mx), ("marR", mx), ("marT", my), ("marB", my)):
                tcPr.set(k, str(int(round(v * EMU_PER_IN))))
            tcPr.set("anchor", "ctr")
            for side in ("lnL", "lnR", "lnT", "lnB"):
                ln = etree.SubElement(tcPr, _A + side)
                if side == "lnB":
                    ln.set("w", "9525")
                    etree.SubElement(ln, _A + "solidFill").append(theme.spec("hairline"))
                else:
                    ln.set("w", "0")
                    etree.SubElement(ln, _A + "noFill")
            etree.SubElement(tcPr, _A + "solidFill").append(theme.spec("ink-strong" if ri == 0 else "paper"))
    ooxml.finish(gf)
    return gf, sum(heights)


# ------------------------------------------------------------------ slides

def s_cover(prs, th):
    s = new_slide(prs, "cover", "title-only")
    paras = [Para(text.title_runs("One shared demand view for every region", ["shared demand view"]))]
    h = need(paras, C.w, th, 30.0)
    text.textbox(s, Box(C.x, 3.0, C.w, h), paras, "title", th, size=30.0, face="Arial")


TOP = C.y + 0.10      # content starts just inside the content band
LABEL_PT = 10.0       # the bold label over a value line
ROW_ICON = 0.45       # glyph side in a label-value row
ROW_GAP = 0.22        # between label-value rows


def label_value(label, value):
    return [Para(Run(label, role="ink-deep", bold=True, size=LABEL_PT)), Para(Run(value, role="ink"))]


def rows(slide, x, y, w, items, theme, prefix) -> float:
    """Label-value rows, each a glyph with its label and value beside it, the glyph centred on the text block.
    Returns the bottom."""
    tx, tw = x + ROW_ICON + 0.15, w - ROW_ICON - 0.15
    for k, (g, label, value) in enumerate(items, start=1):
        paras = label_value(label, value)
        h = need(paras, tw, theme, BODY_PT)
        rh = max(ROW_ICON, h)
        glyphs.glyph(slide, g, Box(x, y + (rh - ROW_ICON) / 2, ROW_ICON, ROW_ICON), role="ink-strong",
                     shape_name="%s.%d.icon" % (prefix, k), theme=theme)
        text.textbox(slide, Box(tx, y + (rh - h) / 2, tw, h), paras, "%s.%d.text" % (prefix, k), theme, size=BODY_PT)
        y += rh + (ROW_GAP if k < len(items) else 0.0)
    return y


def rows_height(items, w, theme) -> float:
    tw = w - ROW_ICON - 0.15
    hs = [max(ROW_ICON, need(label_value(lab, val), tw, theme, BODY_PT)) for _g, lab, val in items]
    return sum(hs) + ROW_GAP * (len(hs) - 1)


PILLARS = [
    ("database", "Shared demand signal",
     "Every region reads the same weekly demand figures, drawn from one governed store and refreshed each Monday.",
     [("user", "Owner", "Demand planning lead"), ("calendar", "Cadence", "Refreshed every Monday"),
      ("gauge", "Measure", "Forecast error by product family"), ("layers", "Scope", "Every region and channel")]),
    ("search", "Exception-first review",
     "Planners see only the accounts that moved outside tolerance, with the reason and the size of the gap beside each.",
     [("users", "Owner", "Regional planners"), ("clock", "Cadence", "Tuesday review, one hour"),
      ("target", "Measure", "Exceptions closed in the cycle"), ("funnel", "Scope", "Lines beyond tolerance only")]),
    ("file-check", "Signed plan of record",
     "Each cycle closes on one versioned plan that finance, supply and sales all sign before it is released.",
     [("handshake", "Owner", "Finance, supply and sales"), ("calendar-check", "Cadence", "Signed each Friday"),
      ("archive", "Measure", "Plans signed on time"), ("lock", "Scope", "One version per cycle")]),
]
RULE_GAP = 0.20       # air above and below the hairline that separates a card's claim from its rows


def s_pillars(prs, th):
    s = new_slide(prs, "pillars", "icon-row")
    text.title(s, "Three capabilities carry the regional planning model", ["Three capabilities"], WIDE, th)
    cols = Box(C.x, TOP, C.w, 4.0).split_cols(3, 0.30)
    iw = cols[0].w - 2 * PAD
    head_h = max(blocks_height([(head(h), HEAD_PT), (body(b), BODY_PT)], iw, th) for _, h, b, _r in PILLARS)
    rows_h = max(rows_height(r, iw, th) for _, _, _, r in PILLARS)
    content = ICON + GAP + head_h + 2 * RULE_GAP + rows_h
    for i, (col, (g, h, b, items)) in enumerate(zip(cols, PILLARS), start=1):
        card = Box(col.x, col.y, col.w, content + 2 * PAD)
        prims.card(s, card, fill="card", line="hairline", name="pillar.%d.card" % i, theme=th)
        glyphs.glyph(s, g, Box(card.x + PAD, card.y + PAD, ICON, ICON), role="accent",
                     shape_name="pillar.%d.icon" % i, theme=th)
        stack(s, card.x + PAD, card.y + PAD + ICON + GAP, iw, [(head(h), HEAD_PT), (body(b), BODY_PT)], th,
              "pillar.%d.text" % i)
        ry = card.y + PAD + ICON + GAP + head_h + RULE_GAP
        prims.hairline(s, (card.x + PAD, ry), (card.r - PAD, ry), name="pillar.%d.rule" % i, theme=th)
        rows(s, card.x + PAD, ry + RULE_GAP, iw, items, th, "pillar.%d.row" % i)


STEPS = [
    ("Draft forecast", "The model proposes a weekly forecast per region and product family.",
     "A draft for every line", "Demand planning"),
    ("Review exceptions", "Planners accept or adjust the lines that moved beyond tolerance.",
     "Accepted or adjusted lines", "Regional planners"),
    ("Reconcile supply", "Supply confirms capacity and flags any line it cannot meet.",
     "Confirmed capacity", "Supply planning"),
    ("Sign the plan", "Finance, supply and sales sign one versioned plan of record.",
     "The signed plan of record", "Finance, supply and sales"),
]
DISC = 0.55           # the step disc; its digit is set large, an ordinal and never a figure (gate P23)


def s_process(prs, th):
    s = new_slide(prs, "process-flow", "chevron-row")
    text.title(s, "Four steps take a forecast from draft to signed plan", ["Four steps"], WIDE, th)
    prims.step_header(s, Box(C.x, TOP, C.w, 0.50), ["Draft", "Review", "Reconcile", "Sign"], name="steps",
                      theme=th)
    zpad = 0.25
    panel_y = TOP + 0.50 + 0.20
    inner = Box(C.x + zpad, panel_y + zpad, C.w - 2 * zpad, 3.0)
    cols = inner.split_cols(4, 0.50)
    iw = cols[0].w - 2 * PAD

    def blocks(h, b, out, owner):
        return [(head(h), HEAD_PT), (body(b), BODY_PT)], [label_value("Output", out), label_value("Owner", owner)]

    head_h = max(blocks_height(blocks(*st)[0], iw, th) for st in STEPS)
    tail_h = max(sum(need(p, iw, th, BODY_PT) for p in blocks(*st)[1]) + GAP for st in STEPS)
    content = DISC + GAP + head_h + 2 * RULE_GAP + tail_h
    panel = Box(C.x, panel_y, C.w, content + 2 * PAD + 2 * zpad)
    prims.zone(s, panel, fill="accent-tint", name="step.panel", theme=th)
    cards = []
    for i, (col, st) in enumerate(zip(cols, STEPS), start=1):
        top_blocks, tail = blocks(*st)
        card = Box(col.x, col.y, col.w, content + 2 * PAD)
        prims.card(s, card, fill="paper", line="rule-strong", name="step.%d.card" % i, theme=th)
        prims.disc(s, Box(card.x + PAD, card.y + PAD, DISC, DISC), i, fill="accent", name="step.%d.disc" % i, theme=th)
        stack(s, card.x + PAD, card.y + PAD + DISC + GAP, iw, top_blocks, th, "step.%d.text" % i)
        ry = card.y + PAD + DISC + GAP + head_h + RULE_GAP
        prims.hairline(s, (card.x + PAD, ry), (card.r - PAD, ry), name="step.%d.rule" % i, theme=th)
        stack(s, card.x + PAD, ry + RULE_GAP, iw, [(p, BODY_PT) for p in tail], th, "step.%d.detail" % i)
        cards.append(card)
    for i, (a, b) in enumerate(zip(cards, cards[1:]), start=1):
        prims.connect(s, (a.r, a.cy), (b.x, b.cy), name="step.arrow.%d" % i, theme=th)


STATS = [
    ("trending-down", "42%", "Fewer manual adjustments per planning cycle", "measured",
     "Counted from the planning log over the last two quarters, in both pilot regions."),
    ("timer", "5 days", "From draft forecast to signed plan, down from twelve", "delivered",
     "Elapsed days between the Monday draft and the Friday signature, averaged over the quarter."),
    ("package", "18%", "Lower safety stock at the same service level", "illustrative",
     "A planning assumption from the supply model, not yet seen in any region's stock."),
    ("flag", "8 wk", "To a working pilot in two regions", "target",
     "The committed date for the pilot. The clock starts when the data owners sign off."),
]
STAT_BOX = 1.70


def s_stats(prs, th):
    s = new_slide(prs, "stat-hero", "stat-row")
    text.title(s, "Planning cycle time falls once regions share one view", ["cycle time"], WIDE, th)
    cols = Box(C.x, TOP, C.w, 4.4).split_cols(4, 0.40)
    iw = cols[0].w - 2 * PAD
    src_h = max(blocks_height([(head("How it is counted"), BODY_PT), (body(src), BODY_PT)], iw, th)
                for *_x, src in STATS)
    numbers = {}
    for i, (col, (g, v, lab, kind, src)) in enumerate(zip(cols, STATS), start=1):
        glyphs.glyph(s, g, Box(col.x, col.y, 0.60, 0.60), role="accent", shape_name="stat.%d.icon" % i, theme=th)
        prims.stat(s, Box(col.x, col.y + 0.85, col.w, STAT_BOX), v, lab, kind=kind, name="stat.%d" % i, theme=th)
        numbers["stat.%d" % i] = {"value": v, "kind": kind}
        card = Box(col.x, col.y + 0.85 + STAT_BOX + 0.30, col.w, src_h + 2 * PAD)
        prims.card(s, card, fill="card", line="hairline", name="stat.%d.source" % i, theme=th)
        stack(s, card.x + PAD, card.y + PAD, iw, [(head("How it is counted"), BODY_PT), (body(src), BODY_PT)], th,
              "stat.%d.source.text" % i)
    return numbers


REGIONS = [("Region", "Data ready", "Planners trained"),
           ("North", "Yes", "Yes"), ("Coastal", "Yes", "In progress"), ("Inland", "By week six", "Not started"),
           ("Highland", "Yes", "Not started"), ("Lakeside", "By week four", "In progress"),
           ("Delta", "By week eight", "Not started"), ("Plains", "Yes", "In progress"),
           ("Valley", "By week six", "Not started"), ("Harbour", "Yes", "Yes"), ("Ridge", "By week ten", "Not started")]
NEXT = [("calendar-check", "Wave two", "Lakeside and Plains, once their planners finish training"),
        ("calendar", "Wave three", "Every other region, once its data owner signs the readiness test")]


def s_table(prs, th):
    s = new_slide(prs, "matrix", "table")
    text.title(s, "Two regions are ready for the pilot this quarter", ["Two regions"], WIDE, th)
    _gf, _th = table(s, C.x, TOP, [3.0, 2.6, 2.6], REGIONS, th, "readiness.table")
    x = C.x + 8.2 + 0.40
    w = C.r - x
    iw = w - 2 * PAD
    blocks = [(head("Pilot regions"), HEAD_PT),
              (body("North and Coastal meet both readiness tests today and start first."), BODY_PT)]
    card = Box(x, TOP, w, ICON + GAP + blocks_height(blocks, iw, th) + 2 * PAD)
    prims.card(s, card, fill="card", line="hairline", name="pilot.card", theme=th)
    glyphs.glyph(s, "circle-check", Box(card.x + PAD, card.y + PAD, ICON, ICON), role="accent",
                 shape_name="pilot.icon", theme=th)
    stack(s, card.x + PAD, card.y + PAD + ICON + GAP, iw, blocks, th, "pilot.text")
    nxt = Box(x, card.b + 0.30, w, rows_height(NEXT, iw, th) + 2 * PAD)
    prims.card(s, nxt, fill="paper", line="rule-strong", name="next.card", theme=th)
    rows(s, nxt.x + PAD, nxt.y + PAD, iw, NEXT, th, "next.row")


PANELS = [
    ("card", "clock", "Weekly reconciliation", "Each region keeps its own spreadsheet of demand.",
     [("files", "Figures", "Five copies of the same demand, matched by hand"),
      ("hourglass", "Effort", "Two planner days before every review"),
      ("triangle-alert", "Disagreement", "Found in the meeting, not before it")]),
    ("accent-tint", "shield-check", "One governed view", "Regions read demand from one store with a named owner.",
     [("database", "Figures", "One store, refreshed each Monday"),
      ("list-ordered", "Effort", "Exceptions arrive ranked by the size of the gap"),
      ("circle-check", "Agreement", "The review starts from figures that already agree")]),
]


def s_fromto(prs, th):
    s = new_slide(prs, "from-to", "two-panel")
    text.title(s, "Weekly reconciliation gives way to one governed view", ["one governed view"], WIDE, th)
    cols = Box(C.x, TOP, C.w, 4.0).split_cols(2, 0.90)
    pad = 0.25
    iw = cols[0].w - 2 * pad
    cw = iw - 2 * PAD
    head_h = max(blocks_height([(head(h), HEAD_PT), (body(b), BODY_PT)], iw, th) for _, _, h, b, _i in PANELS)
    item_h = max(max(ROW_ICON, need(label_value(lab, val), cw - ROW_ICON - 0.15, th, BODY_PT))
                 for *_x, items in PANELS for _g, lab, val in items)
    content = ICON + GAP + head_h + 0.25 + 3 * (item_h + 2 * PAD) + 2 * 0.20
    zones = []
    for i, (col, (fill, g, h, b, items)) in enumerate(zip(cols, PANELS), start=1):
        z = Box(col.x, col.y, col.w, content + 2 * pad)
        prims.zone(s, z, fill=fill, name="panel.%d" % i, theme=th)
        glyphs.glyph(s, g, Box(z.x + pad, z.y + pad, ICON, ICON), role="accent" if i == 2 else "ink-strong",
                     shape_name="panel.%d.icon" % i, theme=th)
        stack(s, z.x + pad, z.y + pad + ICON + GAP, iw, [(head(h), HEAD_PT), (body(b), BODY_PT)], th,
              "panel.%d.text" % i)
        y = z.y + pad + ICON + GAP + head_h + 0.25
        for k, item in enumerate(items, start=1):
            c = Box(z.x + pad, y, iw, item_h + 2 * PAD)
            prims.card(s, c, fill="paper", line="rule-strong", name="panel.%d.item.%d.card" % (i, k), theme=th)
            rows(s, c.x + PAD, c.y + PAD, cw, [item], th, "panel.%d.item.%d" % (i, k))
            y = c.b + 0.20
        zones.append(z)
    a, b = zones
    prims.connect(s, (a.r, a.cy), (b.x, b.cy), weight_pt=1.5, role="accent", name="panel.arrow", theme=th)


def s_close(prs, th):
    s = new_slide(prs, "closing", "line")
    paras = [Para(text.title_runs("Next step: confirm the pilot region by month end", ["confirm the pilot region"]))]
    h = need(paras, C.w, th, 24.0)
    text.textbox(s, Box(C.x, 3.1, C.w, h), paras, "title", th, size=24.0, face="Arial")


# ------------------------------------------------------------------ build

def build(out: Path = DEFAULT_OUT) -> str:
    """Build the golden deck at out, with its manifest and deck.json beside it. Returns the pptx sha256."""
    out = Path(out)
    th = Theme.load(THEME_PATH)
    prs = Presentation(str(BASE))
    with prims.use(th):
        s_cover(prs, th)
        s_pillars(prs, th)
        s_process(prs, th)
        numbers = s_stats(prs, th)
        s_table(prs, th)
        s_fromto(prs, th)
        s_close(prs, th)
    manifest = {"fixture": "golden", "canvas": WIDE.name, "numbers": numbers}
    sha = package.save(prs, out, title=TITLE, theme=th, manifest=manifest, overwrite=True)
    deck_json = {
        "type": "fixture", "canvas": WIDE.name, "theme": str(THEME_PATH), "client": None, "spelling": "US",
        "overrides": {}, "budgets": {}, "series": [], "deliverable": out.name, "notes_deck": False,
        "build": ["{python}", str(Path(__file__).resolve()), "--out", "{out}"],
    }
    (out.parent / "deck.json").write_text(json.dumps(deck_json, indent=2) + "\n", encoding="utf-8")
    return sha


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    a = ap.parse_args(argv)
    sha = build(Path(a.out))
    print("%s  sha256 %s" % (a.out, sha))
    return 0


if __name__ == "__main__":
    sys.exit(main())
