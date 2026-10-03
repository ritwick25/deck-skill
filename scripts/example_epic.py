"""Three slides in the epic layer (ruling 10): solid brand bands, a near-black stat band, numbered panels, a stage
chain, a coded autonomy ladder. The pattern for dense, high-contrast slides under the house rules.

    $PY scripts/example_epic.py [--out .cache/epic/epic.pptx] [--theme themes/sigmoid.json]

Fictional client and figures; every stat is illustrative.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "kit"))

from pptx import Presentation  # noqa: E402

from deckkit import compose, package, prims, tag  # noqa: E402
from deckkit.canvas import WIDE, Box  # noqa: E402
from deckkit.glyphs import glyph  # noqa: E402
from deckkit.text import Para, Run, textbox, title  # noqa: E402
from deckkit.theme import Theme  # noqa: E402

C = WIDE.content


def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[0])


def problem(prs, th, numbers):
    s = blank(prs)
    tag.tag(s, "problem-framing", "banded-panels-stat-band")
    title(s, "Field briefs arrive late because no one owns the signal", keywords=("arrive late",), canvas=WIDE,
          theme=th)
    half = (C.w - 0.2) / 2
    compose.numbered_rows(s, Box(C.x, C.y, half, 3.9), [
        ("Signals are scattered", "Registries, press, congress and payer notices, read by no one person"),
        ("Reps learn last", "Customers mention a competitor move before the field hears of it"),
        ("Notes lack sources", "Ad hoc summaries reach reps with no source and no medical check"),
        ("Every region rebuilds it", "Six teams write six versions of the same week")],
        header="Why briefs arrive late", header_glyph="clock", name="why", theme=th)
    compose.numbered_rows(s, Box(C.x + half + 0.2, C.y, half, 3.9), [
        ("Manual triage", "Analysts sift signals by hand, so the backlog grows every week"),
        ("No single source list", "Each team trusts different feeds and none is approved"),
        ("Review comes too late", "Medical sees the brief after reps have used it"),
        ("No record of what changed", "Edits and rejections are lost in email threads")],
        header="Why it is hard to fix", header_glyph="triangle-alert", name="hard", theme=th)
    names = compose.stat_band(s, Box(C.x, C.y + 4.1, C.w, C.h - 4.1), [
        ("40+", "public competitor signals a week", "illustrative"),
        ("5 days", "from a competitor move to the field", "illustrative"),
        ("6", "regional versions of one brief", "illustrative")], name="stat", theme=th)
    numbers.update({n: {"value": v, "kind": "illustrative"} for n, v in zip(names, ("40+", "5 days", "6"))})


def process(prs, th):
    s = blank(prs)
    tag.tag(s, "process-flow", "pressure-band-stage-chain")
    title(s, "Five steps turn public signals into an approved brief each week", keywords=("approved brief",),
          canvas=WIDE, theme=th)
    compose.pressure_band(s, Box(C.x, C.y, C.w, 1.0), "Field pressures", [
        ("Volume", "40+ signals a week, most of them noise"),
        ("Speed", "Reps need the move before the Monday calls"),
        ("Trust", "Every claim must trace to a public source"),
        ("Control", "Medical signs before anything ships")], name="press", theme=th)
    compose.stage_chain(s, Box(C.x, C.y + 1.2, C.w, 3.7), [
        ("Scan", "scan-search", "Read the source list", "Approved public feeds only, every weekday"),
        ("Rank", "list-ordered", "Score each signal", "Relevance by territory and brand plan"),
        ("Draft", "file-text", "Write one page", "Every claim linked to its source"),
        ("Review", "user-check", "Medical decides", "Approve, edit or reject with a reason"),
        ("Release", "send", "Ship by territory", "Each rep gets the moves that matter")],
        facts=[[("Output", "New signals, no repeats"), ("Control", "Approved source list"), ("Owner", "Scan agent")],
               [("Output", "A ranked shortlist"), ("Control", "Relevance threshold"), ("Owner", "Scan agent")],
               [("Output", "Draft with sources"), ("Control", "No claim without a source"), ("Owner", "Brief agent")],
               [("Output", "Signed brief"), ("Control", "Reviewer signature"), ("Owner", "Medical reviewer")],
               [("Output", "Field brief and record"), ("Control", "Release log"), ("Owner", "Field excellence")]],
        name="chain", theme=th)
    compose.pressure_band(s, Box(C.x, C.y + 5.05, C.w, C.h - 5.05), "How it is measured", [
        ("Speed", "Signal to brief in under a week"), ("Traceability", "Claims with a live source"),
        ("Control", "Unsigned releases: none"), ("Usefulness", "Reps who rate it useful")],
        fill="ink-deep", label_w=2.1, name="measure", theme=th)


def architecture(prs, th):
    s = blank(prs)
    tag.tag(s, "layered-architecture", "consumption-agents-foundation-ladder")
    title(s, "One governed foundation feeds every brief, and autonomy is earned", keywords=("autonomy is earned",),
          canvas=WIDE, theme=th)
    lw = 8.75
    compose.icon_cards(s, Box(C.x, C.y, lw, 1.66), [
        ("smartphone", "Field app", "The brief in the rep's app"),
        ("mail", "Digest", "Monday, before the calls"),
        ("archive", "Archive", "Every past brief, searchable"),
        ("chart-column", "Insight", "Which moves reps used")], glyph_pt=0.42, name="use", theme=th)
    compose.icon_cards(s, Box(C.x, C.y + 1.81, lw, 1.66), [
        ("scan-search", "Scan agent", "Reads approved feeds, drops repeats"),
        ("bot", "Brief agent", "Drafts one page per territory with sources"),
        ("user-check", "Review queue", "Medical approves, edits or rejects")],
        fill="card", align="left", glyph_pt=0.42, name="agents", theme=th)
    compose.pressure_band(s, Box(C.x, C.y + 3.62, lw, 0.74), "Trust", [
        ("Access", "By role, per brief"), ("Audit", "Every edit kept"), ("Evaluation", "Sourcing checked weekly")],
        fill="ink-strong", label_w=1.3, name="trust", theme=th)
    base = Box(C.x, C.y + 4.5, lw, C.h - 4.5)
    prims.card(s, base, fill="card", line=None, name="base.card", theme=th)
    textbox(s, Box(base.x + 0.22, base.y + (base.h - 0.62) / 2, 2.2, 0.62),
            [Para((Run("Governed foundation", "ink-deep", bold=True, size=13.0),)),
             Para((Run("One source ledger", "ink", size=11.0),), space_before=2.0)], "base.text", th,
            background="card")
    stages = ["Landing", "Raw", "Refined", "Certified"]
    sx, sw, sg = base.x + 2.6, 1.2, 0.36
    sh = 0.52
    sy = base.y + (base.h - (sh + 0.16 + 0.36)) / 2
    for i, st in enumerate(stages):
        b = Box(sx + i * (sw + sg), sy, sw, sh)
        prims.block(s, b, fill="ink-deep" if i < 3 else "accent", name="stage.%d" % i, theme=th)
        f = "ink-deep" if i < 3 else "accent"
        textbox(s, b, [Para((Run(st, "paper" if i < 3 else "on-accent", bold=True, size=11.0),), align="center")],
                "stage.%d.text" % i, th, background=f, anchor="middle")
        if i:
            prims.connect(s, (b.x - sg, sy + sh / 2), (b.x, sy + sh / 2), head="end", role="ink-muted",
                          name="stage.arrow.%d" % i, theme=th)
    textbox(s, Box(sx, sy + sh + 0.16, 4 * sw + 3 * sg, 0.36),
            [Para((Run("Sources  ", "ink-muted", bold=True, size=10.0),
                   Run("regulatory notices, trial registries, press releases, congress abstracts, payer updates",
                       "ink", size=10.0)),)], "base.sources", th, background="card")
    rx = C.x + lw + 0.25
    rw = C.r - rx
    prims.tab(s, Box(rx, C.y, rw, 0.42), "Autonomy is earned", fill="accent", name="ladder.header", theme=th)
    compose.ladder(s, Box(rx, C.y + 0.55, rw, C.h - 0.55), [
        ("L0", "Inform", "Reps read the brief"),
        ("L1", "Recommend", "Agent ranks the signals"),
        ("L2", "Draft", "Agent writes, medical signs"),
        ("L3", "Release on rule", "Low-risk updates ship alone"),
        ("L4", "Autonomous", "Policy-bound, audited")], name="ladder", theme=th)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(SKILL / ".cache" / "epic" / "epic.pptx"))
    ap.add_argument("--theme", default=str(SKILL / "themes" / "sigmoid.json"))
    a = ap.parse_args()
    th = Theme.load(a.theme)
    prs = Presentation(str(SKILL / "kit" / "assets" / "base-wide.pptx"))
    prims.bind(th)
    numbers: dict = {}
    problem(prs, th, numbers)
    process(prs, th)
    architecture(prs, th)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sha = package.save(prs, out, title="Epic layer", theme=th, manifest={"numbers": numbers}, overwrite=True,
                       date="2026-10-03")
    dj = out.parent / "deck.json"
    if not dj.exists():
        dj.write_text(json.dumps({"type": "example", "canvas": "wide", "theme": a.theme, "client": None,
                                  "spelling": "US", "overrides": {}, "series": [], "deliverable": out.name,
                                  "build": ["{python}", str(Path(__file__).resolve()), "--theme", a.theme,
                                            "--out", "{out}"]}, indent=2) + "\n")
    print("OK %s sha256 %s" % (out, sha[:12]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
