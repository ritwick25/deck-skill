# Rules on glass, and the gate that holds each

`~/.claude/CLAUDE.md` §3, §4 and §6 are the authority; this file maps them to the machinery. When a gate and
CLAUDE.md disagree, CLAUDE.md wins and the gate is the bug. A project's `DECISIONS.md` / `DESIGN.md` / `deck.json`
overrides win inside that project only, and only when they name their source.

| Rule | Gate | What the kit already does | When it fails |
|---|---|---|---|
| 8pt floor, every run, after autofit | P01 | `text.textbox` refuses a size under the floor; no autofit is ever written | Cut words or widen the zone; never shrink |
| Text fits its box with PowerPoint slack (1.15) | P02 | `require_fit=True` measures with real metrics and raises `Overflows` | Widen, split, or move the line to the notes deck |
| Nothing leaves the slide | P03 | | `bleed.*` names are the only exception |
| Children clear their container (0.04in) | P04 | | Inset the child |
| No overlap between drawn boxes | P05 | | Re-grid; overlays need a deliberate group |
| Arrows start on a box and land on a box | P06 | `prims.connect` takes points: compute them from the boxes | Snap ends to the edges you mean |
| Row siblings share offsets and never touch | P07 | `Box.split_cols` / `split_rows` | Lay the row from one split |
| A card's content does not float at its top (ink, with fitting slack) | P08 | | Give every card in a row the same row count, or shrink the card to its content |
| No footer, page number, confidentiality line, foot band, subtitle, master chrome | P09 | Base templates carry none | Delete; fold a subtitle into the title claim |
| Every content slide argues with a device; no unearned tile grid; accent bars only for state | P10 | Strip roles refuse accent fills (`rules.is_accent_strip`) | Find the device: hub, before-after, numbered pipeline, matrix |
| Flat fills, no `p:style`, no gradient, no soft shadow, theme faces, half-point ladder | P11 | `ooxml.finish()` strips `p:style`; prims never write shadows | Rebuild the shape with prims |
| No PowerPoint repair trap; XSD valid | P12 | `package.save` normalises and validates | Read the structural finding; never hand-patch XML |
| Words within the archetype budget (ceiling 250) | P13 | Budgets in `archetypes/archetypes.json`, per canvas | Cut to the card's device; move prose to notes |
| Title: one claim, 14 words or fewer, two-tone with 1 to 3 keywords | P14 | `text.title(keywords=...)` | Rewrite as the claim the slide proves |
| Variety: two families in any three slides, no archetype twice in a section, no table runs, adjacent slides differ | P15 | | Change the structure, not the colours |
| Every colour is a theme role (or a registered identity hex) | P16 | Prims take role names only | Use a role; client hues go in the theme |
| No banned glyph, word, phrase, jargon or deck-voice pattern | P17 | Loads `~/.claude/hooks/fingerprints.json` with the `deck-voice` tier on | Rewrite; never add an exemption to pass |
| No corpus leak (text, names, media hashes, package residue) | P18 | | The reference decks are never copied from |
| No empty placeholder, "Click to add", slot token, hidden slide or shape | P19 | Blank layouts only | Delete the residue |
| No speaker notes in the audience deck; alt text on every picture | P20 | Notes ship as a separate presenter deck | Move notes out |
| The deck rebuilds byte-identical from `deck.json` "build" | P21 | `package.save(date=...)` is deterministic | Never hand-edit a built pptx; fix the build |
| Icons: SVG with raster fallback, vendor marks byte-verified, no emoji | P22 | `glyphs.glyph`, `icons.vendor`, `icons.monogram` | Use a curated glyph or a monogram |
| Every figure states its kind; planning figures carry a chip; manifest agrees | P23 | `prims.stat(kind=...)` | Declare it in `manifest["numbers"]` |
| A content slide fills its band (mass, not a union box) | P24 | | Grow the governing visual; never pad with air |
| Text contrast clears WCAG against what is painted behind it | P25 | `textbox(background=role)` checks before drawing | Pass the fill the text sits on |
| Architecture slides: 12+ product marks (8 on layered), at most 25% of icons boxed alone, 80% of flows labelled or numbered, no arrows on an L0 master, every mark captioned | P26 | `deckkit.arch` draws the grammar | Declare the diagram in `arch`; a conceptual architecture grants `P26:marks` with its source |
| Icons: brand marks byte-verified against the mark registry | P22 | `icons.mark` | Register the mark with its source, date and sha256 |

R01 to R03 (render checks) and H01 to H10 (the HTML twin) are registered and report PENDING. They are deferred by
ruling 9, so rendering and reading every slide is the only render check that runs.

## Rules no gate can hold

- **Read every rendered slide.** A gate passes a half-empty card it cannot see: the first build of
  `scripts/example_build.py` passed P08 until the gate learned to read ink.
- **A deletion instruction is global.** Sweep the deck for every instance, and check the rendered text.
- **Change only what was pointed at.** A restyle is proposed on one slide first.
- **Numbers are defensible.** Delivered and targeted stay apart, illustrative is labelled, and every number agrees
  across the deck, its notes and any twin.
- **No client names in published material**, and no structure that identifies a live account. CLAUDE.md §5.
- **Theme, not layout.** A client cut swaps the theme; it never re-composes slides.
