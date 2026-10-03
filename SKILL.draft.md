---
name: deck
description: House deck builder. Use whenever planning, building, extending, restyling, reviewing or fixing a slide, deck, pptx, proposal, RFP or RFI response, POV, pitch, capability or credentials deck, roadmap or architecture slide, including before any project folder exists. Picks a storyline and one archetype per slide from 45 measured archetypes in 10 visual families, builds natively in python-pptx with the house kit (theme roles, primitives, glyphs, measured text, deterministic save), gates every deck against the house rules (8pt floor, no footer, no subtitle, no AI tells, word budgets, fill, balance, arrows, contrast, numbers, leaks), then renders and reads every slide. Colour- and client-agnostic, so a client cut is a theme swap. Not for Word, Excel or PDF documents. For only reading or extracting text from an existing pptx without changing its design, the pptx skill's file mechanics are enough.
---

# deck

Decides what goes on each slide and how it looks, then builds it with the kit and proves it with the gates.
`~/.claude/CLAUDE.md` (§3, §4, §6) is the authority: where this skill and CLAUDE.md disagree, CLAUDE.md wins. A
project's `DECISIONS.md`, `DESIGN.md`, `CANON.md` or `deck.json` override wins inside that project when it names its
source. The pptx skill keeps file mechanics only; its pptxgenjs route and its design advice do not apply. Read the
`dataviz` skill before drawing any chart.

```bash
PY=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
K=~/.claude/skills/deck
```

## Modes

| Mode | When | Starts at |
|---|---|---|
| NEW | A deck that does not exist yet, folder or not | step 1 |
| EXTEND | Slides added to an existing deck | step 1; clone the deck's own accepted slides first |
| RESTYLE | Same content, house look | step 1; propose on ONE representative slide, get a yes, then sweep |
| REVIEW | Judge a deck, change nothing | run the gates on it (step 8), render and read (step 9), report |
| FIX | A named defect | step 8 on the deck; change only what was pointed at; re-gate; re-read |

## Procedure

1. **Context.** Read the project's `CLAUDE.md`, `DECISIONS.md`, `DESIGN.md` and `CANON.md` when they exist. If "the
   deck" could mean more than one file, name the candidates and ask.
2. **Restate the object**: what it is, who reads it, what is not in it, and three checkable done-conditions. Get a
   yes before building.
3. **Storyline.** Read `references/storylines.md`. Write the ghost deck: one line per slide, the claim as its title,
   its archetype and family. An RFP's own section order wins over any house order; keep a requirement-to-slide
   coverage table beside it. When a slide cap is shorter than the request's sections plus an agenda, merge two
   adjacent requested sections onto one slide before dropping the agenda (a house default, not a measured pattern).
   Get a yes on the ghost deck.
4. **One archetype per slide** from the chooser below. Check variety now: at least two families in any three
   consecutive slides, no archetype twice in a section (unless the section is a declared `series`), never more than
   two tables in a row, and no two adjacent slides with the same structure.
5. **Open the card**: `archetypes/<slug>.md`. It gives use-when and avoid-when, measured zones, components, type
   roles, density, the word budget, the device notes, the translation table (how the references break the house
   rules and what the house does instead), the exemplars and anti-exemplars, and named variants.
6. **Look at the exemplars**: `$PY $K/scripts/find.py <slug>`, then Read the greeked sheet it prints. Borrow
   structure, never words (`references/library.md`).
7. **Build** in `build.py` (scaffold with `$PY $K/scripts/new_deck.py FOLDER --name "Name"`). In order of preference:
   clone the deck's own accepted slide and retext it (EXTEND); else place a library device that serves the archetype
   (`find.py <slug>` lists them with renders; `references/device-library.md` has all 31) and fill every slot; else
   compose from the card's anatomy with `deckkit.compose` and the kit (below). Never clone a raw reference slide.
8. **Gate**: `$PY $K/gates/run_all.py --deck OUT.pptx` must exit 0. Fix the slide, never the gate. A gate that
   is wrong is reported to the user with the evidence, not edited to pass.
9. **Render and read every slide**: `$PY $K/scripts/render.py OUT.pptx`, then Read every PNG. Not a sample. Look for
   what no gate sees: cards stretched around one line, a device that does not argue the title, uneven row counts,
   a zone larger than its content, arrows that point at nothing, a slide that looks like its neighbour.
10. **Sweep the pack**: deck, notes deck, any twin or client cut agree on every id, number, name and claim.
11. **Report** what ran, what passed, what was skipped and why. Never commit, push or publish unless asked.

## Chooser: the job decides the archetype, the form decides the family

| Family | Archetype | Pick it when the slide must |
|---|---|---|
| Frame | `cover` | open: engagement, parties, date |
| | `agenda` | hold the route once, in order |
| | `section-divider` | turn into a part: numeral, name, one anchor |
| | `closing` | end on one line, no new argument |
| Parallel columns | `problem-framing` | make the problem accepted before any answer |
| | `principles` | agree how the solution is decided |
| | `why-us` | give the few reasons to choose the firm, each with proof |
| | `offering-pillars` | show the parts of the offer a client would buy |
| | `catalogue` | list every agent or product with the same fields |
| | `team-roster` | introduce the people doing the work |
| | `case-wall` | show breadth of delivered work at a glance |
| | `the-ask` | end in decisions and dated next steps |
| Directed sequence | `process-flow` | show how the solution runs, step by step |
| | `as-is-process` | pin today's pains to the stages where they occur |
| | `input-process-output` | frame a mechanism as in, method, out |
| | `decision-logic` | show the rules that route each case |
| | `swimlane-handoff` | show who acts when, and every hand-off |
| | `worked-example` | trace one named instance hop by hop with real values |
| | `engagement-model` | show how the engagement runs, step or workstream |
| Stacked layers | `layered-architecture` | stack the platform from sources to consumers |
| | `solution-architecture` | place components in zones inside a boundary |
| | `governance-model` | set forums, cadence and escalation, top to bottom |
| Split | `from-to-shift` | set today against the target state of one subject |
| | `options-comparison` | set alternatives against one set of criteria, one marked |
| | `gap-analysis` | oppose what exists and what is missing |
| | `case-study` | tell one delivered engagement: need, build, outcome |
| | `deep-dive` | explain one use case: wide exhibit plus a narrow rail |
| | `executive-summary` | compress the proposal into labelled cells |
| | `scope-and-assumptions` | fence in, out, assumptions and dependencies |
| Two-dimensional field | `use-case-map` | place many use cases on the value chain |
| | `coverage-matrix` | cross two lists so every cell says what applies |
| | `prioritization-matrix` | score or plot candidates to agree what goes first |
| | `reference-table` | let a reader look up and compare rows |
| Radial hub | `hub-and-spoke` | put one core at the centre with its parts around it |
| | `lifecycle-loop` | show work that repeats and improves |
| | `convergence-hub` | converge many feeders onto one shared element |
| Axis of time or maturity | `gantt` | show duration, overlap and gates on a dated grid |
| | `phased-roadmap` | break delivery into phases with one repeated anatomy |
| | `value-horizons` | grow value or capability across years |
| | `maturity-model` | rank levels from basic to advanced |
| Numbers-led | `headline-figures` | make three to six figures the argument |
| | `commercials` | present the price and what it buys |
| | `credentials` | show the firm in facts and marks |
| Exhibit-led | `product-screen` | let the running product carry the claim |
| | `output-capture` | reproduce a real deliverable whole |

`$PY $K/scripts/find.py` lists them with their wide budgets; `--search "words"` matches definitions. The visual
mechanisms a card cites as `dvNN` are in `references/devices.md`.

## Building a slide from its card

The card's numbers are measured from the top exemplars and printed as `median (min to max)`. Use them as a starting
geometry, then fit the content.

| Card section | Becomes |
|---|---|
| Zones (x, y, w, h as % of the slide) | `Box` values inside `WIDE.content`; the title zone is always `text.title` |
| Components | prims: `card`, `zone`, `tab`, `pill`, `disc`, `step_header`, `connect`, `elbow`, `stat`, `quote`, `person`, glyphs |
| Type roles | `Run(size=...)`; body 11 to 12pt, card heading 13 to 14pt, title from the canvas; never under 8pt |
| Density, word budget | the ceiling for words on glass (P13); density beats air (P24) |
| Device notes | the drawing that carries the argument; build this first, then the text around it |
| Translation table | the reference habits NOT to copy (footers, subtitles, gradients, accent bars) and what replaces them |
| Variants | pick one per use; in a declared series every member takes a different variant |

Order of work for one slide: tag it, set the title claim, lay the governing device from one grid split, put text
in measured boxes, connect with points computed from box edges, declare any figure, then gate and look.

## Kit

```python
import sys; from pathlib import Path
SKILL = Path("~/.claude/skills/deck").expanduser(); sys.path.insert(0, str(SKILL / "kit"))
from pptx import Presentation
from deckkit import package, prims, tag
from deckkit.canvas import WIDE, Box          # WIDE 13.333 x 7.5; STD 10 x 5.625 only to extend a 10-inch deck
from deckkit.glyphs import glyph
from deckkit.icons import vendor, monogram
from deckkit.text import Para, Run, textbox, title
from deckkit.theme import Theme

th = Theme.load(SKILL / "themes" / "sigmoid.json")       # or neutral.json, or the project's client theme
prs = Presentation(str(SKILL / "kit" / "assets" / "base-wide.pptx"))
prims.bind(th)
s = prs.slides.add_slide(prs.slide_layouts[0])          # the one blank layout
tag.tag(s, "process-flow", "numbered-rows")              # archetype slug : variant, read by P13 and P15
title(s, "Every brief passes four steps before it reaches the field", keywords=("four steps",), canvas=WIDE, theme=th)
```

- **Geometry**: `C = WIDE.content` (x 0.50, y 0.85, w 12.40, h 5.99); `C.split_cols(n, WIDE.gutter)`,
  `split_rows`, `inset`; `.r` and `.b` are the right and bottom edges. Every shape takes a `name`, which the gates
  report.
- **Roles, never hexes**: `paper`, `card`, `ink`, `ink-deep`, `ink-strong`, `ink-muted`, `hairline`,
  `hairline-soft`, `rule-strong`, `accent`, `accent-deep`, `accent-ink`, `accent-tint`, `accent-wash`, `on-accent`,
  `navy`, `series-1` to `series-5`.
- **Text**: `textbox(slide, box, [Para((Run(text, role, bold=, size=),), space_before=)], name, th,
  background=fill_role, anchor="top"|"middle"|"bottom")` measures and refuses overflow, the floor and low contrast.
  Pass the role of the fill the text sits on as `background`. `text.title_runs(text, keywords)` builds two-tone
  runs with no size: pass `size=` when measuring them with `text.need_height`. On light fills text takes `ink`
  roles; on a `block`, `circle` or `disc` it takes `paper` (dark fills) or `on-accent` (accent fills).
- **Type sizes**: a card's type roles are the references' sizes. Translate them up to the house scale: body 11 to
  12pt, labels 10pt and up, nothing under 8pt. Fewer words, never smaller type.
- **Variants**: tag the variant as a short kebab slug of the card's variant line you used (`icon-columns`,
  `numbered-rows`); in a declared series every member's slug differs.
- **Shapes**: light containers are `prims.card(s, box, fill="card"|"paper"|"accent-tint", line=None|"hairline"|
  "rule-strong", name=)` and `zone(..., fill="accent-tint")`. Strong fills are `block(s, box, fill="accent"|
  "ink-strong"|"navy"|...)` (rounded: a gantt bar, a price panel) and `rect(s, box, fill=role)` (square).
  `circle(s, square_box, fill=role)` or `circle(..., fill=None, line="rule-strong")` is a hub core, a roundel or a
  milestone dot; `disc(s, square_box, n)` is a numbered one. Also `tab`, `pill`, `step_header(s, box, labels,
  active=i)`, `stat(s, box, value, label, kind="measured|delivered|illustrative|target|benchmark")` (it raises
  `Overflows` with the height it needs), `quote(s, box, text, attribution)` (its left bar is the one the rules
  allow), `person(s, box)`.
- **Devices** (`from deckkit import devices`; rulings 3 and 14): 31 native slides lifted from the references,
  sanitised and theme-mapped. `devices.place(prs, "DL07", {slot: value}, theme=th)` adds the slide, tags it, and
  fills each named slot in its own box, size, weight, colour and alignment; a value that does not fit raises
  `Overflows` (cut words, never shrink). Text slots take a string or a list of paragraph strings; a title slot takes
  `(text, keywords)`; a glyph slot takes a glyph name; `None` removes an optional slot. Every slot must be filled: a
  device's sample copy left on its slide fails P19. Slot names and word capacities are in `devices/devices.json`.
- **Composed components** (`from deckkit import compose`; ruling 10, the flagship's devices under the house rules):
  `icon_cards` (solid brand cards, glyph over head and line), `numbered_rows` (a panel under a solid header band,
  numbered discs), `stat_band` (near-black band, brand numerals, returns stat names for the manifest),
  `pressure_band` (solid band, label block, columns), `stage_chain` (chevron header, glyph and lines per step,
  optional label-value facts, returns its foot), `ladder` (coded levels L0 to L4 rising), `ask_cards` (01 to 04
  decision cards with chevrons), `milestone_rail` (ringed dots, date and label). Each lays out a whole row or panel
  in one box and raises `Overflows` with the height it needs. Solid brand and near-black are the strong fills;
  pastel tint is for large backgrounds only (ruling 12). `scripts/example_epic.py` is the pattern.
- **Lines**: `hairline(s, p1, p2)` is horizontal or vertical; `connect(s, p1, p2, head="end", dash=None)` is an
  arrow; an undirected diagonal (a hub spoke) is `connect(..., head="none", role="hairline")`, because outside the
  rule roles an undirected line is refused; `elbow(s, points)` routes orthogonally.
- **Icons**: `glyph(s, name, box, role="accent", shape_name=)` from 193 curated Lucide glyphs (an unknown name
  raises with the closest matches); `vendor(s, key, box)` for AWS, Azure and GCP marks; `monogram(s, box, "AB")` for
  a mark with no asset. Never emoji, never a corpus raster.
- **Tables**: python-pptx `add_table` with no table style, cells written by `deckkit.text.write`, and a hairline
  under each row. `table()` in `tests/build_golden.py` is the recipe.
- **Save**: `package.save(prs, out, title=, theme=th, manifest={"numbers": {stat_name: {"value": v, "kind": k}}},
  overwrite=True, date="YYYY-MM-DD")` is deterministic, which gate P21 proves by rebuilding from `deck.json`.
- **Worked patterns**: `scripts/example_epic.py` (the epic layer: problem-framing, process-flow,
  layered-architecture), `scripts/example_build.py` (offering-pillars and process-flow, plain kit) and
  `tests/build_golden.py` (seven archetypes, the gates' clean fixture).
- **Client cut**: a theme JSON in the project, verified against the client's production CSS with the date, then
  `$PY -m deckkit theme check THEME.json` and `theme apply THEME.json DECK.pptx`. Identity colours keep their hue;
  theme colours move.

## Gates

`$PY $K/gates/run_all.py --deck OUT.pptx` runs P01 to P25 cheapest first (`--only P13,P24`, `-v` for every
finding). `references/rules.md` maps each rule to its gate and to the fix. A deck with no build command needs a
`deck.json` grant for P21 naming its source (a hand-edited deck whose pptx is the source of truth).
`$PY $K/gates/run_all.py --negatives` proves every gate fails on a planted breakage; run it after editing a gate.

## References

| File | Read it when |
|---|---|
| `references/storylines.md` | choosing the deck's order (proposal, POV, RFP and RFI response, capability, workshop) |
| `references/design-system.md` | setting grid, type scale, colour roles, cards, radius, lines, connectors, icons |
| `references/devices.md` | a card cites `dvNN` |
| `references/device-library.md` | choosing a library device (DL01 to DL31) to place |
| `references/rules.md` | a gate fails, or before a review |
| `references/copy.md` | writing titles, card bodies, numbers and notes |
| `references/library.md` | looking at exemplars, cloning the user's own decks, refreshing from the library |
| `DECISIONS.md` | why the skill is the way it is (rulings 1 to 9) |

## Not built yet (ruling 9, lean finish)

- **The HTML twin** (generated from the pptx) and its gates H01 to H10, plus the render gates R01 to R03, all
  report PENDING. A twin, when one is needed, is built by hand under CLAUDE.md §7.
- **Per-archetype composers.** Every slide is composed from its card with the kit.
