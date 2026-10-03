# Rules on glass, and the gate that holds each

`~/.claude/CLAUDE.md` §3, §4, §6 and §8 are the authority; this file maps them to the machinery. When a gate and
CLAUDE.md disagree, CLAUDE.md wins and the gate is the bug. A project's `DECISIONS.md`, `DESIGN.md` or `deck.json`
override wins inside that project only, and only when it names its source (`"overrides": {"P09:subtitle":
"DESIGN.md#R36"}`; a grant without a source is refused). Each gate's own docstring (`gates/pNN_*.py`) is the letter.

`$PY $K/gates/run_all.py --deck OUT.pptx` runs all 27 implemented gates cheapest first; `-v` prints every finding,
`--only P13,P24` a subset, `--theme T.json` reviews a deck with no `deck.json`. Exit 0 or the deck is not done.

| Gate | Holds | The kit's side | When it fails |
|---|---|---|---|
| P01 floor | every run at 8pt or more after autofit, with an explicit size on every run | `textbox` refuses a size under the floor; no autofit is written | cut words or widen the zone; never shrink |
| P02 fit | every text box fits at PowerPoint's slack (1.15, tolerance 0.035in x k), each run measured in its own cut | `textbox(require_fit=True)` raises `Overflows` with the height it needs | widen, split, or move the line to the notes deck |
| P03 bounds | every shape on the slide (0.05in x k), and inside the content band's left and right edges (WIDE 0.50 to 12.90in, STD 0.28 to 9.72in, 0.10in x k); undrawn text judged by its ink box; one finding per top-level shape | `WIDE.content` is the band | pull it in; a shape meant to bleed is named `bleed.*` (or sits in a `bleed.*` group) |
| P04 padding | a child that starts inside a container clears all four edges (fail under 0.04in, advisory to 0.10in); overlays, spans, `state.*` marks and diagram edge pins pass | | inset the child |
| P05 overlap | no two drawn, non-nested boxes overlap by more than 0.10 x 0.10in; text by its ink box; a chevron row nests; an edge pin overlaps its frame by notation | | re-grid; overlays need a deliberate group |
| P06 arrows | both ends of every headed connector land on two different shapes (0.09in of an edge); an end hidden under an opaque shape is skipped; an end on another line is a junction | `connect` takes points: compute them from box edges | snap ends to the edges meant |
| P07 row | sibling cards never touch (0.05in) and a row's first content sits at one offset (0.05in) | `split_cols`, `split_rows` | lay the row from one split |
| P08 balance | a card's content does not float at its top (bottom air minus top air at most 0.12in, judged by ink); a row is judged by its fullest card | compose cards are as tall as their fullest stack | same row count in every card, or shrink the card to its content |
| P09 chrome | no foot band, foot sentence, subtitle, page number, confidentiality line, footer logo or master chrome; a cover may carry label lines of 12 words or fewer | base templates carry none; `brand.lockup` refuses any slide but cover and closing | delete; fold a subtitle into the title claim |
| P10 density | every content slide argues with a device: an icon, a native chart frame, or two or more connectors (headed arrows, or undirected links between two tiles); a table frame is not a device; more than six identical tiles need six icons or connectors; no coloured accent bar (a strip 1.5pt or thicker, not grey, beside a text edge, not `state.*`); no caps kicker over most cards | strip roles refuse accent fills (`rules.is_accent_strip`) | find the device: hub, before-after, numbered pipeline, matrix, chart |
| P11 style | no `p:style`, gradient, soft or large shadow, 3D or glow, no autofit, theme faces, the half-point ladder, the canvas title size, one card radius (WIDE 0.05in) | prims never write shadows; `ooxml.finish()` strips `p:style` | rebuild the shape with prims |
| P12 package | no PowerPoint repair trap: structural checks plus the ISO 29500 validator, including every chart part against `dml-chart.xsd` | `package.save` normalises and validates | read the structural finding; never hand-patch XML |
| P13 budget | words within the archetype's budget for the canvas (ceiling 250); a content slide under the advisory floor (the exemplars' p25) is an advisory, counted in the detail column; a tag naming no known archetype fails with the nearest slugs | budgets in `archetypes/archetypes.json`; `deck.json` `"budgets"` wins in its folder | over: cut to the card's device. Under: add rows, owners, dates, figures |
| P14 titles | one title per slide, 14 words or fewer, within the canvas's lines (one on WIDE; a slide tagged cover, closing or section-divider may stack to 3), no more than two titles sharing their opening two words, two-tone keywords 1 to 3 spans and only in titles | `text.title(keywords=...)` | rewrite as the claim the slide proves |
| P15 variety | two families in any three consecutive slides; no archetype twice in a section, except a declared series (below); at most two table slides in a row outside the appendix; adjacent slides not alike (occupancy Jaccard under 0.85); no family over 40% of the content slides (one always allowed); at most 1 in 5 content slides end on a foot band, never two adjacent; every slide tagged | `tag.tag(s, archetype, variant)`; `devices.place(archetype=)` | change the structure, not the colours |
| P16 colour | every visible colour is a theme role tuple or an identity hex; a theme slot's hex typed as srgbClr fails unless the shape is `state.*` or `identity.*`; small tint: a shape filled `accent-tint` or `accent-wash` under 4 sq in (x k squared) fails unless it or its group is `state.*` | prims take role names only | use a role; a small tinted container becomes `card` with a hairline |
| P17 fingerprints | no banned glyph, word, phrase, structural tell, jargon or deck-voice pattern on glass or in alt text (first and second person, placeholders, maturity words); URLs blanked first; the canary fires before any slide is read; semicolons advisory | loads `~/.claude/hooks/fingerprints.json` with the deck-voice tier | rewrite; a client's own vocabulary is a `P17:dv-maturity` grant with its source |
| P18 leak | nothing matches the hashed corpus (names, 6-word shingles, numeric phrases, media sha256 and dHash, vector signatures) and the package carries no residue; a 6-gram inside an approved firm claim (`gates/approved_claims.json`, CLAUDE.md §5) is not a leak; a picture whose bytes P22 verifies as an official vendor or brand mark is exempt (the name alone never exempts) | `deck.json` `"client"` allows that client's name on its own deck; `"media_allow"` names a media sha256 with a reason | the reference decks are never copied from |
| P19 residue | no layout placeholder, empty text box, "Click to add", slot token, `{{placeholder}}`, device sample copy, hidden slide or hidden shape | blank layouts only; `devices.place` fills every named slot | fill or delete the residue |
| P20 notes and alt | the audience deck carries no speaker notes; every picture has semantic alt text of 120 characters or fewer | notes ship as a separate presenter deck | move notes out; write the alt text |
| P21 determinism | `deck.json` `"build"` rebuilds the same bytes and the manifest records the deck's sha256 | `package.save(date=...)` is deterministic | never hand-edit a built pptx; a hand-edited deck whose pptx is the source holds a `"P21"` grant |
| P22 icons | every SVG has a raster fallback; every raster is 192 dpi at its displayed size; `vendor.*` and `mark.*` pictures resolve and are the registered bytes; no emoji | `glyph`, `vendor`, `mark`, `monogram` | use a curated glyph, a registered mark or a monogram |
| P23 numbers | every stat states its kind; illustrative, target and benchmark carry a chip, or one shared basis label on the slide whose whole text is "Illustrative figures", "Target figures" or "Benchmark figures"; a large quantity outside a stat fails; every value equals `manifest["numbers"]` and every manifest number is on glass | `prims.stat(kind=)`, `stat(basis=False)` plus `prims.basis_label(kind)`; `compose.stat_band` draws the one label | declare it; never mix bases in one band |
| P24 fill | a content slide's main mass reaches 85% of the content band's height and covers 35% of it (a lone foot sentence left out) | | grow the governing visual; never pad with air |
| P25 contrast | every run clears WCAG against what is painted behind it (4.5:1, or 3:1 at 14pt bold or 18pt) | `textbox(background=role)` checks before drawing | pass the fill the text sits on; use the fill's text role |
| P26 architecture | slides tagged layered-architecture or solution-architecture, or with an `arch-*` variant, hold the measured diagram grammar per type (marks, boxed alone, labelled flows, captions, crossings, steps, boundary facts, nesting, legend, orphans, notation, collisions, one name one mark, ink size); thresholds in `references/tech-diagrams.md` | `deckkit.arch`, `arch_flow`, `arch_seq` draw the grammar | declare the diagram in the engine; a conceptual architecture grants `P26:marks` with its source |
| P27 charts | every native chart part: 8pt floor with explicit sizes; theme roles or identity hexes only, never a status colour; no 3D, gradient, effect, `c:style` over 2 or rounded corners; no chart title; no legend at 3 series or fewer; at most 3 categorical colours and 1 accent; bar, column and area value axes fixed at 0; one axis pair; rings of 2 points; a pinned plot area; P17's rules on chart text; tick and label contrast; `(chart kind X)` alt text and its basis label; no drift from `manifest["charts"]` | `deckkit.charts` writes all of it | rebuild through `deckkit.charts`; never edit chart data after the build |

R01 to R03 (render checks) and H01 to H10 (the HTML twin) are registered and report PENDING (ruling 9), so rendering
and reading every slide is the only render check that runs.

## The declared series (P15, rulings 5 and 23)

A section listed in `deck.json` `"series"` may repeat one archetype, and only one. It must be opened by a use-case
map or by a layered architecture master: the opener is the section's first slide outside the Frame family, so a
section divider may stand in front of it. Every repeated member takes a different variant slug. Sections are
PowerPoint's own when the pptx has them; otherwise each section-divider opens a section named by the divider's title,
and that title is what `"series"` lists.

## Rules no gate can hold

- **Read every rendered slide.** A gate passes a half-empty card it cannot see.
- **A deletion instruction is global.** Sweep the deck for every instance, check the rendered text, report the list.
- **Change only what was pointed at.** A restyle is proposed on one slide first.
- **Numbers are defensible.** Delivered and targeted stay apart, illustrative is labelled, and every number agrees
  across the deck, its notes and any twin.
- **No client names in published material**, and no structure that identifies a live account. CLAUDE.md §5.
- **Theme, not layout.** A client cut swaps the theme; it never re-composes slides.
- **Device figure slots are plain text.** P23 cannot read their kind: keep the device's basis slot true to them.
