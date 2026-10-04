---
name: deck
description: House deck builder. Use whenever a message contains /deck anywhere, or asks to plan, build, extend, restyle, review or fix a slide, deck, pptx, proposal, RFP or RFI response, POV, pitch, capability or credentials deck, roadmap, chart, or architecture or technical diagram, including before any project folder exists. Once loaded, every later deck iteration in the session goes through it, one slide or one edit included. Picks a storyline and one archetype per slide from 45 measured archetypes, builds natively in python-pptx with the house kit, asks for the client's colours, logo and font when a client deck has none, gates every deck against the house rules and renders and reads every slide. Not for Word, Excel or PDF documents.
when_to_use: The user types /deck with or without a mode word (new, slide, edit, review, diagram, chart, brand), names a deck or slide to change, or asks for one more slide or one more change after the skill was used earlier in the session.
argument-hint: "[new|slide|edit|review|diagram|chart|brand] [brief, path or change]"
---

Request: $ARGUMENTS

## Commands

| Command | Does | Asks for, when missing |
|---|---|---|
| `/deck new <brief>` | Plans and builds a deck: restate, storyline, ghost deck, build, gates, read every slide | audience and the decision the deck must win, and for a client deck the brand (see `/deck brand`) |
| `/deck slide <what> [--deck path]` | Adds or rebuilds one slide: archetype, build in the deck's `build.py`, gates, read it | which deck, when more than one is in reach, and the claim the slide makes |
| `/deck edit <path> <change>` | Changes only what was pointed at, rebuilds, re-gates, re-reads. A deletion sweeps the whole deck | the slide, when the change could land on more than one |
| `/deck review <path>` | Runs the gates, reads every slide, reports. Changes nothing | the path, when the folder holds more than one deck |
| `/deck diagram <type> <subject>` | Architecture or technical diagram from the diagram engine (aws, azure or house grammar, L0 or deep dive) | the stack and cloud, and which components are in scope |
| `/deck chart <what>` | A native chart slide from supplied data, under the dataviz rules | the numbers and their source. Never invents a figure |
| `/deck brand <client>` | Client theme and logo lockup from `scripts/brand.py`, contrast-solved, identity colours kept | brand colours (hex, or a site to read the CSS from), logo file, font |
| `/deck` | Picks the mode from context: a path plus a change is edit, a brief is new, a deck alone is review | what the user wants, when context does not decide |

- `/deck` may sit anywhere in a longer prompt. The whole message is the brief, and the word after `/deck` picks the mode.
- Once loaded, the skill governs the session. Every later deck iteration, one slide or one word, follows this file
  (build, gates, read the changed slides) without the user typing `/deck` again.
- A client deck with no colour system or logo given stops at intake: ask for the brand colours, the logo file and
  the font, then run `brand.py`. The house theme is used for a client deck only when the user says so.
- After a context compaction, invoke the skill again before the next change.

## Setup

```bash
PY=${DECK_PYTHON:-/Library/Frameworks/Python.framework/Versions/3.14/bin/python3}
[ -x "$PY" ] || PY=python3                     # another machine: its own python3, or set DECK_PYTHON
K=${CLAUDE_SKILL_DIR}                          # filled in by Claude Code
[ -d "$K/kit" ] || K=~/.claude/skills/deck     # the default home, when this file is read raw
```

Shell variables do not survive between Bash calls: repeat the two lines, or write the paths out, in every command.

## Standing rules

- `~/.claude/CLAUDE.md` §3, §4, §6 and §8 are the authority; where this skill disagrees, CLAUDE.md wins. On a
  machine whose CLAUDE.md has no such sections, `references/rules.md` and this file are the authority. A project's
  `DECISIONS.md`, `DESIGN.md`, `CANON.md` or `deck.json` wins inside that project when it names its source. The pptx
  skill keeps file mechanics only. Read the `dataviz` skill before any chart.
- `build.py` is the source of truth. Never hand-edit a built pptx: change the build and rebuild (gate P21).
- Gates exit 0 before anything is called done. Fix the slide, never the gate; a gate that is wrong goes to the user
  with the evidence.
- Render and read every slide a change could touch, not a sample. A gate cannot see a hollow card.
- Change only what was pointed at. A deletion is global: sweep the deck for every instance and report the list.
- A restyle is proposed on one representative slide and gets a yes before any sweep.
- Before a scripted pass on an existing deck (EXTEND, RESTYLE, FIX), copy it to `NAME-backup.pptx`.
- Every figure is a stat with a kind (measured, delivered, illustrative, target, benchmark). Never invent a number.
- No client names, logos or identifying structure in anything published; approved firm claims only (CLAUDE.md §5).
- Never commit, push or publish unless asked.

## Modes

| Mode | Command | Starts at |
|---|---|---|
| NEW | `/deck new` | step 1 |
| SLIDE | `/deck slide` | step 5 in the deck's own `build.py`, then 8 and 9 for that slide and its neighbours |
| EDIT, FIX | `/deck edit` | step 8 on the deck; change only what was pointed at; re-gate; re-read |
| REVIEW | `/deck review` | step 8 with `-v`, then step 9; report, change nothing |
| DIAGRAM | `/deck diagram` | the diagram chooser under Kit, then steps 7 to 9 |
| CHART | `/deck chart` | the chart chooser under Kit, then steps 7 to 9 |
| BRAND | `/deck brand` | Brand intake, then a rebuild on the new theme |
| RESTYLE | (a restyle request) | step 1; one representative slide first, a yes, then the sweep |

## Procedure

1. **Context.** Read the project's `CLAUDE.md`, `DECISIONS.md`, `DESIGN.md` and `CANON.md` when they exist. If "the
   deck" could mean more than one file, name the candidates and ask.
2. **Restate the object**: what it is, who reads it, what is not in it, and three checkable done-conditions. Get a
   yes before building.
3. **Brand.** A client deck with no colour system or logo given goes through Brand intake (below) before any build.
4. **Storyline.** Read `references/storylines.md`. Write the ghost deck: one line per slide, the claim as its title,
   its archetype and family. An RFP's own section order wins over any house order; keep a requirement-to-slide
   coverage table beside it. When a slide cap is shorter than the request's sections plus an agenda, merge two
   adjacent requested sections onto one slide before dropping the agenda (a house default). Get a yes.
5. **One archetype per slide** from the chooser. Variety (P15): two families in any three consecutive slides; no
   archetype twice in a section unless `deck.json` declares the section a `series`; at most two tables in a row; no
   two adjacent slides alike; no family over 40% of the content slides; at most one content slide in five ends on a
   full-width foot band, and never two adjacent.
6. **Card and exemplars.** Open `archetypes/<slug>.md` (zones, components, type roles, word budget, device notes,
   translation table, variants). Run `$PY $K/scripts/find.py <slug>`: it prints the budget and floor, the library
   devices with their renders, the greeked contact sheet and the exemplar views. Read the sheet. Borrow structure,
   never words.
7. **Build** in `build.py`. A new deck starts from `$PY $K/scripts/new_deck.py FOLDER --name "Name" [--theme
   brand/theme.json]`: `deck.json`, a `CLAUDE.md` that sends later sessions here, and a three-slide `build.py` in the
   epic layer whose every word is a `{{placeholder}}` gate P19 refuses until replaced. In order of preference: clone
   the deck's own accepted slide and retext it (EXTEND); reuse the showcase slide of the same archetype or diagram
   type (`showcase/index.json` names the code that drew it, `showcase/sheets/` shows it); place a library device;
   compose from the card with the kit. Never clone a raw reference slide.
8. **Gate**: `$PY $K/gates/run_all.py --deck OUT.pptx` must exit 0. An advisory count in P13's detail column is a
   slide under its archetype's floor: fill it with rows, owners, dates, figures and named specifics, never longer
   sentences.
9. **Render and read every slide**: `$PY $K/scripts/render.py OUT.pptx`, then Read every PNG. Look for what no gate
   sees: cards stretched around one line, a device that does not argue the title, uneven row counts, a zone larger
   than its content, arrows that point at nothing, a slide that looks like its neighbour.
10. **Notes**, when asked: a separate presenter deck (CLAUDE.md §6: verbatim transcript, slide thumbnail, IF THEY
    ASK, time chip). The travelling deck carries no notes (P20). The kit has no notes builder.
11. **Sweep the pack**: deck, notes deck, any twin or client cut agree on every id, number, name and claim.
12. **Report** what ran, what passed, what was skipped and why.

## Brand intake

Ask all three in one AskUserQuestion, the recommended option first. "Other" carries the URL, hexes, path or font.

| Header | Question | Options, recommended first |
|---|---|---|
| Colours | Which brand colours should the CLIENT deck use? | Read them from the client's website (Recommended): the skill reads the production CSS and lists candidates with counts and the date read · I'll give the hex codes · Use the house theme |
| Logo | Which logo file should the cover carry? | An SVG file (Recommended), embedded as is with a PNG fallback · A PNG file, at least twice its shown size · No logo |
| Font | Which font should the deck set in? | Arial (Recommended), measured by the kit · The client's brand font, used only when installed and measurable, else Arial with the reason printed · Montserrat |

```bash
$PY $K/scripts/brand.py --name "Client" --from-url https://client.example        # candidates only, exit 3
$PY $K/scripts/brand.py --name "Client" --from-url https://client.example \
    --primary "#0B6E4F" --secondary "#F2A900" --logo logo.svg [--font "Name"]   # after the user confirms
$PY $K/scripts/brand.py --name "Client" --primary "#0B6E4F" [--secondary HEX] [--accent HEX ...] --logo logo.svg
PYTHONPATH=$K/kit $PY -m deckkit theme check brand/theme.json                    # re-check at any time
```

- Never pick a colour for the user from the candidates. Exit codes: 0 written, 1 refused, 2 bad input, 3 waiting.
- Writes `brand/theme.json` (client primary in accent1; navy and the near-white derived; accent-ink solved to 4.5:1;
  accent-bright solved to 3:1 on the dark fills; identity and vendor registries copied from the house theme; a
  `brand` block with client, font, logo sha256 and the CSS URL and date) and the logo, byte for byte.
- A mid-luminance primary is refused with a deeper shade of the same hue named: rerun with that shade as
  `--primary` and the brand colour as `--secondary`. More than five series colours are refused. Fewer than five are
  padded with house slates.
- New deck: `new_deck.py ... --theme brand/theme.json`. Existing deck: set `deck.json` `"theme"` to the file, then
  rebuild. A client cut of a built deck is a rebuild into its own folder, `$PY build.py --theme brand/theme.json
  --out CUT/Name.pptx` (P21 rebuilds it); `theme apply` is only for a hand-edited deck holding a P21 grant.
- The logo goes on the cover and the closing only (P09 fails a logo in the foot):
  `brand.lockup(s, Box(0.9, 0.75, 5.0, 0.56), brand.logo_path(th), firm_logo=None, theme=th,
  name=th.data["brand"]["client"])`. It refuses a slide not tagged `cover` or `closing`. The kit carries no firm logo
  file: pass one as `firm_logo` for a two-mark lockup.

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

`$PY $K/scripts/find.py` lists them with their wide budgets; `--search "words"` matches definitions. A card's `dvNN`
mechanisms are in `references/devices.md`. The card's numbers are `median (min to max)` from the top exemplars: a
starting geometry, then fit the content. A content slide carries between its archetype's advisory floor (the
exemplars' p25 of words) and its budget (ceiling 250). Card bodies stay one or two lines; density comes from the
device. In a declared series every member takes a different variant slug.

## Kit

```python
import sys; from pathlib import Path
SKILL = Path("~/.claude/skills/deck").expanduser(); sys.path.insert(0, str(SKILL / "kit"))
from pptx import Presentation
from deckkit import arch, brand, charts, compose, devices, exhibits, icons, package, prims, tables, tag
from deckkit.canvas import WIDE, Box          # WIDE 13.333 x 7.5; STD 10 x 5.625 only to extend a 10-inch deck
from deckkit.glyphs import glyph
from deckkit.icons import mark, monogram, vendor
from deckkit.text import Para, Run, textbox, title, title_runs
from deckkit.theme import Theme

th = Theme.load(SKILL / "themes" / "sigmoid.json")      # neutral.json, or the client's brand/theme.json
prs = Presentation(str(SKILL / "kit" / "assets" / "base-wide.pptx"))
prims.bind(th)
C = WIDE.content                                          # x 0.50, y 0.85, w 12.40, h 5.99
s = prs.slides.add_slide(prs.slide_layouts[0])           # the one blank layout
tag.tag(s, "process-flow", "numbered-rows")              # archetype : variant, read by P13, P15, P24, P26
title(s, "Every brief passes four steps before it reaches the field", keywords=("four steps",), canvas=WIDE, theme=th)
```

Order of work for one slide: tag it, set the title claim, lay the governing device from one grid split, put text in
measured boxes, connect with points computed from box edges, declare every figure, then gate and look. Every shape
takes a `name`, which the gates report. Every kit call measures first and raises (`Overflows` with the height it
needs, `GeometryError`, `ThemeInvariant`, `BelowFloor`) instead of shrinking or clamping: cut words, never type.

- **Geometry**: `C.split_cols(n, WIDE.gutter, weights=)`, `split_rows`, `inset`; `.r` and `.b` are the right and
  bottom edges. P03 holds every shape inside x 0.50 to 12.90in; `bleed.*` names are the exception.
- **Roles, never hexes** (22): `paper`, `card`, `hairline-soft`, `hairline`, `rule-strong`, `ink-deep`, `ink`,
  `ink-strong`, `ink-muted`, `accent`, `accent-tint`, `accent-wash`, `accent-deep`, `accent-ink`, `accent-bright`,
  `on-accent`, `navy`, `series-1` to `series-5`. `accent-ink` is brand text on light ground (title keywords, stat
  numerals). `accent-bright` is brand numerals on `ink-deep`, `ink-strong` or `navy`, large text only. Text on a fill
  takes that fill's text role: `ink` on light fills, `paper` on the inks and navy, `on-accent` on accent fills.
  Identity names (`rag-red`, `rag-amber`, `rag-green`, the `aws-*` and `azure-*` notation colours) work in `rect`,
  `glyph` and line roles only; a status mark always carries its word and glyph (on the house theme `rag-red` is the
  brand's hex).
- **Colour, ruling 12**: solid brand bands and cards, near-black stat and header panels, light slide ground. Pastel
  `accent-tint` and `accent-wash` are for large backgrounds only: a tinted shape under 4 sq in fails P16 unless named
  `state.*`. `references/design-system.md` carries the same rule.
- **Text**: `textbox(slide, box, [Para((Run(text, role, bold=, size=),), space_before=)], name, th,
  background=fill_role, anchor="top"|"middle"|"bottom")` measures and refuses overflow, the floor and low contrast;
  pass the role of the fill the text sits on as `background`. `title()` is one line, 14 words, 21pt, 0 to 3 keywords
  in accent-ink. `title_runs(text, keywords)` builds two-tone runs with no size, for a cover, closing or divider
  headline set large (P14 lets those three wrap to 3 lines).
- **Type**: body 10.5 to 12pt, card heads 12 to 14pt, labels 10pt, small 9pt (`WIDE.ramp`), diagram captions 9pt
  names and 8pt roles and flow labels, nothing under 8pt (P01). Fewer words, never smaller type.
- **Shapes** (`prims`): `card(s, box, fill="card"|"paper"|"accent-tint", line="hairline"|"rule-strong"|None, name=)`;
  `block(s, box, fill=)` a rounded strong fill (`accent`, `accent-deep`, `ink-deep`, `ink-strong`, `navy`: a brand
  card, a near-black panel, a gantt bar); `rect(s, box, fill=)` square; `circle(s, square_box, fill=)` or
  `circle(..., fill=None, line="rule-strong")`; `disc(s, square_box, n)`; `tab(s, box, label, fill="ink-strong")`;
  `pill`; `step_header(s, box, labels, active=i)`; `zone(s, box, fill="accent-tint")` (large backgrounds only);
  `stat(s, box, value, label, kind=, basis=True)`; `quote(s, box, text, attribution)` (its left bar is the one the
  rules allow); `person` (prefer `exhibits.portrait`).
- **Lines**: `hairline(s, p1, p2)` is horizontal or vertical; `connect(s, p1, p2, head="end", dash=None)` is an
  arrow; a diagonal spoke is `connect(..., head="none", role="hairline")`; `elbow(s, points)` routes orthogonally.
  An undirected line outside the rule roles, and any strip in a colour, is refused (the accent-bar rule).
- **Icons**: `glyph(s, name, box, role="accent", shape_name=)` from 193 curated Lucide glyphs (an unknown name raises
  with the closest matches); `vendor(s, key, box)` from 1,771 byte-verified marks (aws 525, azure 808, gcp 123,
  onprem 173, programming 74, saas 41, generic 27; `[k for k in icons.vendor_keys() if "kafka" in k]`);
  `mark(s, key, box)` for the registered brand marks in `kit/assets/marks/registry.json` (anthropic-logo,
  anthropic-symbol, claude-logo, claude-spark, dataiku-logo, dataiku-logo-straight, langchain-logo, langgraph-logo,
  langfuse-icon; vendor-published SVG, ruling 21); `monogram(s, box, "AB", name=)` for anything else. Marks keep
  their own artwork and colour. Never emoji.
- **Devices** (rulings 3, 14): 44 sanitised native slides, DL01 to DL30 and DL32 to DL45 (DL31 is retired: the
  diagram engine replaced it). `references/device-library.md` lists them with archetypes, slots and capacity;
  `find.py <slug>` shows the ones serving an archetype with renders.
  `s = devices.place(prs, "DL07", {slot: value}, theme=th, archetype="input-process-output", variant=None)` adds,
  tags and fills the slide. `archetype=` is required when the device serves more than one; `variant=` gives each
  member of a declared series its own slug. A `slot.title` takes `(text, keywords)` and is set in the kit's title
  geometry; DL32, DL34 and DL35 (cover, divider, closing) take a large `slot.headline`, given as
  `[Para(title_runs(text, keywords))]`. A text slot takes a string, a list of paragraph strings or kit Paras; a
  group slot one string per text, top to bottom; a table slot rows of cell strings; a glyph slot a glyph name or a
  `vendor:<key>`; `None` deletes that slot's shapes. Every slot is filled (P19 fails surviving sample copy). Figure
  slots are plain text that P23 cannot read: keep the device's basis slot true to their kind, or compose the
  figures with `stat_band`. Slot names, words and paragraphs: `devices/devices.json`.
- **Compose** (ruling 10; each lays out a whole row or panel in one box and raises with the height it needs):
  `icon_cards(s, box, [(glyph, head, body)], fill="accent")` and `ask_cards(s, box, [(verb, glyph, head, body)])`
  return the row foot (place the next row there; `spread=True` fills the box and refuses a hollow card);
  `numbered_rows(s, box, [(lead, line)], header=, header_glyph=)`; `stat_band(s, box, [(value, label, kind)],
  fill="ink-deep")` returns the stat names and draws one basis label for the band (mixed bases raise);
  `pressure_band(s, box, label, [(lead, line)])` at the top or middle, never the foot; `stage_chain(s, box,
  [(label, glyph, head, body)], facts=)` returns its foot; `ladder(s, box, [(code, head, body)])`;
  `milestone_rail(s, box, [(date, label)])`. All take `name=` and `theme=`.
- **Exhibits** (`exhibits`, `tables`): `cycle_ring(s, box, [(glyph, head, line)], hub=, style="wedges"|"nodes")`
  (lifecycle-loop); `mark_wall(s, box, [(label, [(key, caption)])])` with `vendor:`, `mark:` or `mono:` keys
  (credentials, tech stacks); `screen_frame(s, box, png, chrome="browser"|"laptop"|None)` on a capture from
  `$PY $K/scripts/capture.py page.html out.png --placed-width 11.5` (refused under 8pt at the placed width);
  `portrait(s, box, image=None, initials=)` and `quote_portrait` (team-roster); `cell_grid(s, box, rows, cols,
  cells, legend)` (coverage-matrix: glyph plus word in every cell); `tables.table(s, box, header, rows,
  marked_col=, cell_glyphs=)` returns `(frame, height, row_tops, col_lefts)`.
- **Charts** (`charts`, ruling 22): the chart chooser below and `references/charts.md`.
- **Diagrams** (`arch`, `arch_flow`, `arch_seq`, ruling 18): the diagram chooser below and
  `references/tech-diagrams.md`. Every layered-architecture and solution-architecture slide is a declared diagram,
  never hand-placed tiles. `render(draft=True)` lists what does not fit while iterating; never ship a draft.
- **Save**: `package.save(prs, out, title=, theme=th, manifest={"numbers": {stat_name: {"value": v, "kind": k}},
  "charts": charts.records(prs)}, overwrite=True, date="YYYY-MM-DD")` is deterministic; P21 rebuilds from
  `deck.json` `"build"` and compares bytes.
- **Worked patterns**: `scripts/template_build.py` (what `new_deck.py` scaffolds: composed panels and stat band,
  engine L0, device DL01), `scripts/example_epic.py` (the epic layer), `scripts/example_exhibits.py`,
  `scripts/example_charts.py`, `scripts/example_arch.py`, `scripts/example_arch_topology.py`,
  `scripts/example_arch_flow.py`, `scripts/example_arch_seq.py`, `scripts/example_build.py` (plain prims) and
  `tests/build_golden.py` (the gates' clean fixture). Each runs with `--out` and `--theme`.

### Diagram chooser

Tag the slide `archetype:variant` as below: the `arch-*` variant word picks P26's thresholds. Each example function
is the worked instance.

| Diagram | Tag | Engine | Example |
|---|---|---|---|
| AWS solution architecture | `solution-architecture:aws-reference` | `arch.Diagram("aws")` | `example_arch.py` `aws()` |
| Azure solution architecture | `solution-architecture:azure-reference` | `arch.Diagram("azure")` | `example_arch.py` `azure()` |
| House L0 master (no arrows, no numbers) | `layered-architecture:l0-house` | `arch.Diagram("house", l0=True)` | `example_arch.py` `l0()` |
| House deep dive | `solution-architecture:house-deep-dive` | `arch.Diagram("house")` | `example_arch.py` `deep()` |
| AWS deployment and network | `solution-architecture:arch-deploy-aws` | `arch.Diagram("aws")`, `span`, `pin` | `example_arch_topology.py` `aws_deploy()` |
| Azure deployment and network | `solution-architecture:arch-deploy-azure` | `arch.Diagram("azure")`, peering | `example_arch_topology.py` `azure_deploy()` |
| DR and landing zone | `solution-architecture:arch-dr-aws` | `arch.Diagram("aws")`, `bus(tree=True)` | `example_arch_topology.py` `aws_dr()` |
| Current versus target | `solution-architecture:arch-current-target` | `arch.Diagram`, `change`, `change_key` | `example_arch_topology.py` `current_target()` |
| CI/CD and release | `process-flow:arch-cicd` | `arch_flow.cicd` | `example_arch_flow.py` `cicd()` |
| MLOps and LLMOps | `solution-architecture:arch-mlops` | `arch_flow.mlops` | `example_arch_flow.py` `mlops()` |
| Data flow, medallion, lineage inset | `input-process-output:arch-medallion` | `arch_flow.medallion` | `example_arch_flow.py` `medallion()` |
| Event-driven integration | `convergence-hub:arch-events` | `arch_flow.events` | `example_arch_flow.py` `events()` |
| Agent state machine | `decision-logic:arch-state` | `arch_flow.state_graph` | `example_arch_flow.py` `state()` |
| Sequence, API and agent | `swimlane-handoff:arch-sequence` | `arch_seq.Sequence` | `example_arch_seq.py` `sequence()` |
| DFD and threat model | `solution-architecture:arch-dfd` | `arch_seq.DFD` | `example_arch_seq.py` `dfd()` |
| C4 system context | `solution-architecture:arch-c4-context` | `arch_seq.C4("context")` | `example_arch_seq.py` `c4_context()` |
| C4 container | `layered-architecture:arch-c4-container` | `arch_seq.C4("container")` | `example_arch_seq.py` `c4_container()` |

No builder or example yet: a lineage DAG of datasets (`arch-lineage`), a hub-and-spoke view (`arch-hub`) and a GCP
grammar (use the house grammar with `vendor:gcp/...` marks). P26 still judges a slide tagged with those words.

### Chart chooser

Read the `dataviz` skill first. One chart argues one message, with one subject in accent and one annotation.

| Message | Call |
|---|---|
| rank or compare magnitudes | `charts.bar(s, box, cats, values, kind=, name=, subject=, sort="desc")` |
| a value over a few periods | `charts.column(s, box, cats, values, kind=, name=, subject=)` |
| what a whole is made of, per category | `charts.stacked(s, box, cats, {series: values}, kind=, name=, subject=)` |
| a trend, up to three series | `charts.line(s, box, cats, {series: values}, kind=, name=, subject=, area=False)` |
| one series and its volume | `charts.area(s, box, cats, values, series_name=, kind=, name=)` |
| how a total is built (price, bridge) | `charts.waterfall(s, box, [(label, value)], total=, kind=, name=)` |
| two scores per item (value and effort) | `charts.scatter(s, box, [(label, x, y)], x_range=, y_range=, x_label=, y_label=, kind=, name=, splits=, quadrants=, sizes=)` |
| one share of a whole | `charts.ring(s, square, value, of, kind=, name=)` plus a `prims.stat` in the hole |
| KPIs against targets, one ratio | `charts.bullet(s, box, [charts.Row(label, value, target)], scale_max=, kind=, name=)`, `charts.progress` |
| the one point that proves the title | `charts.annotate(plot, at, text, kind="callout")`; also `drop`, `crossover`, `band` |

## Gates

```bash
$PY $K/gates/run_all.py --deck OUT.pptx                  # P01 to P27, cheapest first; exit 0 or it is not done
$PY $K/gates/run_all.py --deck OUT.pptx -v --only P13,P24 # every finding, chosen gates
$PY $K/gates/run_all.py --deck X.pptx --theme T.json -v   # REVIEW: a deck with no deck.json beside it
$PY $K/gates/run_all.py --negatives                       # after editing a gate: each gate fails its planted breakage
$PY $K/scripts/selftest.py                                # after editing skill text: must print OK
```

- `references/rules.md` has one line per gate and the fix. R01 to R03 and H01 to H10 report PENDING.
- REVIEW of a deck the kit did not build: untagged slides make P13, P15, P24 and P26 meaningless and P21 has no build
  command. Say so in the report; never retag a client's deck to pass.
- `deck.json` in the deck's own folder: `"overrides": {"RULE:key": "SOURCE#anchor"}` (a grant without a source is
  refused; for example `"P17:dv-maturity"` when the client's own vocabulary says alpha, `"P26:marks"` for a
  conceptual architecture, `"P21"` for a hand-edited deck whose pptx is the source); `"series"`: section names (a
  section opens at each section-divider and takes its title); `"budgets"`, `"client"`, `"theme"`, `"build"`,
  `"media_allow"`, `"notes_deck"`.

## References

| File | Read it when |
|---|---|
| `references/storylines.md` | choosing the deck's order (proposal, POV, RFP and RFI response, capability, workshop) |
| `references/design-system.md` | setting grid, type scale, colour roles, cards, radius, lines, connectors, icons |
| `references/tech-diagrams.md` | drawing any architecture or technical diagram |
| `references/charts.md` | drawing any chart, KPI bar or share ring |
| `references/devices.md` | a card cites `dvNN` |
| `references/device-library.md` | choosing a library device (DL01 to DL30, DL32 to DL45) to place |
| `references/rules.md` | a gate fails, or before a review |
| `references/copy.md` | writing titles, card bodies, numbers and notes |
| `references/library.md` | looking at exemplars, cloning the user's own decks, refreshing from the library |
| `showcase/index.json` | before building a slide: the accepted 65-slide showcase, each slide's archetype, variant, device, code and sheet (ruling 24) |
| `DECISIONS.md` | why the skill is the way it is (rulings 1 to 24, newest last) |

## Not built

- The generated HTML twin and its gates H01 to H10, and the render gates R01 to R03, report PENDING. A twin, when one
  is needed, is built by hand under CLAUDE.md §7.
- A presenter-notes builder. Build the notes deck by hand (step 10).
- Diagram builders for a dataset lineage DAG, a hub-and-spoke view and a GCP grammar (see the diagram chooser).
