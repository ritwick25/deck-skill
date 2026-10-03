"""A two-slide deck built only from the kit: the pattern every new deck's build.py follows.

    $PY scripts/example_build.py [--out .cache/example/example.pptx] [--theme themes/sigmoid.json]
    $PY gates/run_all.py --deck .cache/example/example.pptx --static

Slide 1 is offering-pillars (Parallel columns): three cards, a foundation band, a stat row. Slide 2 is
process-flow (Directed sequence) in a different structure: numbered rows down the left, one decision panel on
the right. Both fill the content band (P24) and do not look alike (P15). Stats are declared in the manifest
(P23); deck.json beside the deck carries the build command (P21). Every figure is fictional.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "kit"))

from pptx import Presentation  # noqa: E402

from deckkit import package, prims, tag  # noqa: E402
from deckkit.canvas import WIDE, Box  # noqa: E402
from deckkit.glyphs import glyph  # noqa: E402
from deckkit.text import Para, Run, textbox, title  # noqa: E402
from deckkit.theme import Theme  # noqa: E402

C = WIDE.content                     # x 0.50, y 0.85, w 12.40, h 5.99: the band every slide fills
STATS = {"stat.1": ("3", "agents on one foundation"), "stat.2": ("1", "review gate before the field"),
         "stat.3": ("100%", "claims carry a source")}


def blank_slide(prs):
    return prs.slides.add_slide(prs.slide_layouts[0])          # the base template's one blank layout


def head_body(s, box, head, body, name, th, background="card"):
    textbox(s, box, [Para((Run(head, "ink-deep", bold=True, size=14),)),
                     Para((Run(body, "ink", size=12),), space_before=4)], name, th, background=background)


def pillars(prs, th):
    s = blank_slide(prs)
    tag.tag(s, "offering-pillars", "icon-columns")
    title(s, "Three agents share one governed data foundation", keywords=("one governed",), canvas=WIDE, theme=th)
    cols = C.split_cols(3, WIDE.gutter)
    rows = [("search", "Market scan", "A weekly read of competitor moves, ranked by impact on the brand plan",
             (("Reads", "public filings, congress abstracts"), ("Writes", "a ranked signal list"),
              ("Owner", "brand insights lead"))),
            ("bot", "Brief writer", "Drafts the field brief from the scan, with a source behind every claim",
             (("Reads", "the signal list, the brand plan"), ("Writes", "a draft brief with sources"),
              ("Owner", "field excellence"))),
            ("shield-check", "Review gate", "A named reviewer approves each brief before it reaches the field",
             (("Reads", "the draft and its sources"), ("Writes", "an approval record"),
              ("Owner", "medical reviewer")))]
    card_h = 3.05
    for i, (g, h, body, facts) in enumerate(rows, 1):
        c = cols[i - 1]
        prims.card(s, Box(c.x, C.y, c.w, card_h), fill="card", line=None, name=f"pillar.{i}.card", theme=th)
        glyph(s, g, Box(c.x + 0.25, C.y + 0.25, 0.5, 0.5), role="accent", shape_name=f"pillar.{i}.icon", theme=th)
        head_body(s, Box(c.x + 0.25, C.y + 0.9, c.w - 0.5, 0.95), h, body, f"pillar.{i}.text", th)
        prims.hairline(s, (c.x + 0.25, C.y + 1.95), (c.r - 0.25, C.y + 1.95), name=f"pillar.{i}.rule", theme=th)
        textbox(s, Box(c.x + 0.25, C.y + 2.05, c.w - 0.5, card_h - 2.05 - 0.2),
                [Para((Run(k + "  ", "ink-muted", bold=True, size=11), Run(v, "ink", size=11)),
                      space_before=0 if j == 0 else 3) for j, (k, v) in enumerate(facts)],
                f"pillar.{i}.facts", th, background="card")
    band = Box(C.x, C.y + card_h + 0.2, C.w, 0.7)
    prims.zone(s, band, fill="accent-tint", label=None, name="foundation.zone", theme=th)
    textbox(s, Box(band.x + 0.3, band.y + 0.1, band.w - 0.6, band.h - 0.2),
            [Para((Run("Governed data foundation", "ink-deep", bold=True, size=14),
                   Run("   one semantic layer, one access policy, one audit trail", "ink", size=12)))],
            "foundation.text", th, background="accent-tint", anchor="middle")
    for i, c in enumerate(cols, 1):
        v, lbl = STATS[f"stat.{i}"]
        prims.stat(s, Box(c.x, band.b + 0.2, c.w, C.b - band.b - 0.2), v, lbl, kind="illustrative", pt=44,
                   label_pt=12, name=f"stat.{i}", theme=th)
    return s


def process(prs, th):
    s = blank_slide(prs)
    tag.tag(s, "process-flow", "numbered-rows")
    title(s, "Every brief passes four steps before it reaches the field", keywords=("four steps",), canvas=WIDE,
          theme=th)
    left_w, gap = 7.7, 0.2
    row_h = (C.h - 3 * gap) / 4
    steps = [("Scan", "Signals gathered from public sources and the brand plan", "Ranked signal list"),
             ("Draft", "The agent drafts the brief with its sources attached", "Draft brief, sourced"),
             ("Review", "A reviewer approves, edits or rejects the draft", "Approval record"),
             ("Publish", "The approved brief goes to the field with its review record", "Field brief")]
    d = 0.6
    out_w = 2.2
    for i, (h, body, made) in enumerate(steps, 1):
        y = C.y + (i - 1) * (row_h + gap)
        prims.disc(s, Box(C.x, y + (row_h - d) / 2, d, d), i, name=f"step.{i}.disc", theme=th)
        card = Box(C.x + d + 0.25, y, left_w - d - 0.25, row_h)
        prims.card(s, card, fill="card", line=None, name=f"step.{i}.card", theme=th)
        textbox(s, Box(card.x + 0.25, y + 0.15, card.w - out_w - 0.6, row_h - 0.3),
                [Para((Run(h, "ink-deep", bold=True, size=14),)), Para((Run(body, "ink", size=12),), space_before=4)],
                f"step.{i}.text", th, background="card", anchor="middle")
        prims.hairline(s, (card.r - out_w - 0.2, y + 0.2), (card.r - out_w - 0.2, y + row_h - 0.2),
                       name=f"step.{i}.split", theme=th)
        textbox(s, Box(card.r - out_w, y + 0.15, out_w - 0.2, row_h - 0.3),
                [Para((Run("Output", "ink-muted", bold=True, size=11),)), Para((Run(made, "ink", size=12),),
                                                                              space_before=3)],
                f"step.{i}.output", th, background="card", anchor="middle")
        if i < 4:
            cx = C.x + d / 2
            prims.connect(s, (cx, y + (row_h + d) / 2), (cx, y + row_h + gap + (row_h - d) / 2), head="end",
                          role="ink-muted", name=f"arrow.{i}-{i + 1}", theme=th)
    panel = Box(C.x + left_w + 0.3, C.y, C.w - left_w - 0.3, C.h)
    prims.card(s, panel, fill="paper", line="rule-strong", name="decision.card", theme=th)
    prims.person(s, Box(panel.x + 0.35, panel.y + 0.35, 0.5, 0.7), name="decision.person", theme=th)
    head_body(s, Box(panel.x + 0.35, panel.y + 1.25, panel.w - 0.7, 1.2), "A human decides at step three",
              "No brief reaches the field on the agent's word alone", "decision.text", th, background="paper")
    outs = [("circle-check", "Approve", "the brief publishes as written"),
            ("file-text", "Edit", "the reviewer's changes are kept with the brief"),
            ("circle-x", "Reject", "the draft returns with the reason recorded")]
    for i, (g, h, body) in enumerate(outs, 1):
        y = panel.y + 2.75 + (i - 1) * 1.22
        prims.hairline(s, (panel.x + 0.35, y - 0.15), (panel.x + panel.w - 0.35, y - 0.15), name=f"out.{i}.rule",
                       theme=th)
        glyph(s, g, Box(panel.x + 0.35, y, 0.4, 0.4), role="ink-strong", shape_name=f"out.{i}.icon", theme=th)
        textbox(s, Box(panel.x + 0.95, y - 0.05, panel.w - 1.3, 0.75),
                [Para((Run(h, "ink-deep", bold=True, size=12),)), Para((Run(body, "ink", size=12),), space_before=2)],
                f"out.{i}.text", th)
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(SKILL / ".cache" / "example" / "example.pptx"))
    ap.add_argument("--theme", default=str(SKILL / "themes" / "sigmoid.json"))
    a = ap.parse_args()
    th = Theme.load(a.theme)
    prs = Presentation(str(SKILL / "kit" / "assets" / "base-wide.pptx"))
    prims.bind(th)
    pillars(prs, th)
    process(prs, th)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    numbers = {k: {"value": v, "kind": "illustrative"} for k, (v, _) in STATS.items()}
    sha = package.save(prs, out, title="Example deck", theme=th, manifest={"numbers": numbers}, overwrite=True,
                       date="2026-10-03")
    dj = out.parent / "deck.json"
    if not dj.exists():                     # the P21 rebuild calls this script again with --out {out}
        dj.write_text(json.dumps({"type": "example", "canvas": "wide", "theme": a.theme, "client": None,
                                  "spelling": "US", "overrides": {}, "series": [], "deliverable": out.name,
                                  "build": ["{python}", str(Path(__file__).resolve()), "--theme", a.theme,
                                            "--out", "{out}"]}, indent=2) + "\n")
    print(f"OK {out} sha256 {sha[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
