# deck skill — decisions

Newest ruling last. Every entry dated. Rulings 1–9 and CP1 are the user's, recorded verbatim in substance.

## 2026-10-02 · RULING 1 — Rules win, devices borrowed
Every device and composition lifted from the reference decks is rendered under `~/.claude/CLAUDE.md` §4:
8pt floor, flat fills, hairlines (≤1px shadow), no footer, no subtitle, no glyphs, light slides.
Each archetype card states its translation (reference treatment → house rendering → rule).

## 2026-10-02 · RULING 2 — Per-archetype word budgets
Budgets are measured from the top exemplars of each archetype, per canvas, with a hard ceiling of 250
words. The CLAUDE.md "roughly 60 to 90 on a consulting slide" line is rewritten to point at the table.
Budget rule: min(250, ceil10(p75 of the top-k exemplars' content words)); advisory floor floor10(p25).

## 2026-10-02 · RULING 3 — Kit plus sanitised device library
Python composers cover the standard archetypes. `devices/devices.pptx` holds ~30 native slides lifted
from the references: client identity stripped, colours mapped to theme slots so they recolour per
client, shapes named by role, the rules applied. A leak gate runs on every clone. Raw reference slides
are never cloned into client work.

## 2026-10-02 · RULING 4 — pptx first, HTML twin generated
Every archetype gets a python-pptx composer or device. HTML decks are generated from the pptx (the
twin converter plus the keyboard engine). Native HTML composition is documented, not built per archetype.

## 2026-10-03 · RULING 5 — Declared series allowed
A storyline section declared `series` may repeat one archetype when a use-case map opens it and every
member uses a different variant. Everywhere else, no archetype repeats inside a section.

## 2026-10-03 · RULING 6 — Two-tone action titles
One to three keywords of the claim in the brand colour, in titles only, never in body copy.
Single-colour titles stay valid. The title gate counts the keywords.

## 2026-10-03 · RULING 7 — Accepted tier
The user's own accepted decks (SFA v0.9, the RFI deck, the Prototype-vs-Enterprise POV, the fabric POV
deck) are catalogued in place as a calibration tier: they calibrate translations and budgets, and show
as exemplars where they are the best rule-compliant instance of an archetype.

## 2026-10-03 · RULING 8 — Checkpoint commits, local only
Commits happen in this repo and the library repo only, at each phase gate, with messages naming what
verified them. Never push. No other repo is touched.

## 2026-10-03 · Structure (accepted with the plan)
- Name `deck`. Skill here, own git. Library at `~/Codes/Decks-For-Visuals/library/` (internal: client
  renders and verbatim text live there and never here).
- Skill text names no client and no person. Reference slides are neutral ids (`d01-s015`); the
  id-to-file map lives only in the library manifest. Runtime contact sheets are greeked.
- Families are visual (Frame, Columns, Sequence, Layers, Split, Field, Axis, Number) so the variety gate
  measures what the eye sees. The archetype list is frozen by the library taxonomy (v1).
- Theme slot model: dk1 000000 and lt1 FFFFFF fixed; a client theme changes dk2, lt2, accent1–6 and
  hlink only; every kit colour is a schemeClr role, so a client cut is a theme swap. fmtScheme flat.
- `sigmoid` theme: brand = accent1 = D91E18, measured from the house template. `neutral`: navy 1E3C7D,
  sky 00A0E9 (fill only), greys. 1F36C7 is avoided (a client's title blue in two references).
- Default canvas wide 13.333×7.5; compact 10×5.625 only when extending a 10-inch deck. Arial; Montserrat
  numerals opt-in. Client logo: cover lockup only.
- Hairlines: card borders and dividers exempt from the 3:1 non-text rule (hospital tokens precedent);
  an outline-only card on white uses 8C8C8C (3.36:1).
- Deck-voice patterns live in `~/.claude/hooks/fingerprints.json` as the opt-in `deck-voice` tier
  (never in hook mode, never in `--all`; the deck gates name it in `--tiers`). One home kept.
- The A4 one-pager is a device, not an archetype (n = 1).
- `SKILL.draft.md` until acceptance, so no parallel session triggers a half-built skill.

## 2026-10-03 · Builder strips decided by role; no link.* exemption; vendor marks verified by bytes
- A strip in the kit (at most 0.10in x k thick, longer than 0.18in x k and more than 2x its thickness) may be
  drawn only in `hairline`, `hairline-soft`, `rule-strong` or `ink-muted`, or on a shape named `state.*`. Every
  other role raises GeometryError (navy, the inks, paper, card, accent and its tints, the series), whatever its
  chroma on the theme. `rules.is_accent_strip` is the one predicate: `by="role"` in the builder, `by="colour"`
  in the gates, which read hexes.
- No `link.*` exemption: an undirected line outside the rule roles is refused whatever its name, by the builder
  (`rules.line_refusal`) and by P10. `state.*` stays exempt.
- `tab()`, `pill()`, `step_header()` and `quote()` run the strip check before drawing. `set_fill()` and
  `set_line()` re-check the strip rule (and the line rule on a connector or open path) on the shape they modify,
  before modifying it. `allow_strip=True` skips the re-check; only `gates/negatives.py` passes it (a test reads
  every call by AST).
- `vendor_path` / `vendor_resolves` refuse a key with `..`, a leading `/` or a backslash, with or without a theme.
  P22 checks a `vendor.*` picture's blob: its sha256 must equal `kit/assets/vendor_hashes.json` for that key at
  the blob's pixel size (the diagrams resource, embedded byte for byte; `scripts/build_vendor_hashes.py` rebuilds
  it, `--check` reports staleness). `vendor()` checks the same table before drawing.

## 2026-10-03 · Gate rulings after the round-4 real-deck review (relayed by the gate-rulings workflow task)
- **P10 bars by colour, any deck.** A filled strip (`rules.is_strip`) is a bar when it is at least 1.5pt (0.0208in)
  thick, not grey (HLS saturation 0.15 or more, and not a rule role's hex), not `state.*`, and within 0.30in (x k) of a
  text block's left edge (vertical) or top edge (horizontal), parallel to it. Thinner strips are dividers. A line
  (cxnSp or line-like sp) without an arrowhead counts only when at least 2pt, vertical or horizontal, not grey, within
  0.15in (x k) of a text block's left edge and no longer than 1.5x that block's height. A text edge is the frame's or
  the ink box's. `rules.is_accent_strip(by="colour")` carries the 1.5pt floor and the HLS test (`rules.is_grey`);
  `by="role"` (the builder) is unchanged and has no floor, so kit decks stay under the stricter role rule.
- **P10 density counts links.** An undirected connector whose two ends land on two distinct tiles (filled or outlined
  shapes, pictures, graphic frames, at least 0.04 sq in) counts beside headed arrows, for the device rule and the
  identical-tiles rule.
- **P04 and P05 judge text by its ink box** (`walk._text_box`, occupancy-trimmed; `_shared.ink_box`) when the text
  block draws no fill and no outline. P04's overlay and span idioms are still judged on the frame. P05 nests two loose
  chevron-family shapes when they read as one row (same top and height within 0.02in, overlap no deeper than the
  point); a grouped chevron against a loose one is still compared.
- **P06 hidden ends and junctions.** An end under an opaque picture (no alpha, no alphaModFix below 100%) or an opaque
  solid fill painted above the connector is skipped. An end within 0.03in of another straight line's stroke is a
  junction and touches.
- **P17 strips URLs** (http, https, www. and bare domain paths) before matching. The hook's dv-placeholder WIP clause
  is `\bWIP\b(?!\s+[A-Z][a-z])`; every other pattern byte-identical; hook default and `--all` outputs verified
  unchanged on a probe; recorded in `fingerprints.json` `_opt_in`.
- **P24 measures the main mass.** Marked cells dilated by one cell (never across an empty band row), components
  largest first to 85% of the marked cells, then a component at most 3 rows tall wholly below the largest one, past an
  empty band row, is a foot sentence and left out. An untagged slide 1 is a frame; a cover is content only when
  tagged as one.
- **Real-deck false-positive rates are a characteriser** (`gates/characterise.py`, `.cache/fp_report.json`, a
  stratified sample of 3 per gate for review), never a gate. Planters retired: `thin-accent-bar` (0.01in) and
  `thin-accent-line` (1pt) are dividers now and live as pass-side tests.

## 2026-10-03 · CP1 — taxonomy v1 approved (user)
The library taxonomy v1 is frozen: 10 visual families (Frame, Parallel columns, Directed sequence, Stacked
layers, Split, Two-dimensional field, Radial hub, Axis of time or maturity, Numbers-led, Exhibit-led), 45
archetypes, 59 devices. The variety gate counts these families. The form decides the family; the job
decides the archetype.

## 2026-10-03 · RULING 9 — Lean finish (user, on token budget); amends rulings 3 and 4
- Deferred: the sanitised device library (ruling 3), per-archetype composers and the generated HTML twin
  (ruling 4). Claude builds slides from each archetype card's measured anatomy with the kit's primitives,
  text writer, glyphs and gates. The kit's clone tool still serves clone-and-retext of the user's OWN
  accepted decks (CLAUDE.md §6); raw reference slides are still never cloned into client work.
- Exemplars: the 12 archetypes ranked comparatively keep their rankings; the other 33 take their top
  exemplars by script (fit, then catalogue quality, round-robin across decks).
- Cards: one agent per family writes its archetypes' cards; numbers stay script-measured and cited by key.
- The deferred parts can resume later from the saved runs; nothing built is thrown away.

## 2026-10-03 · Lean-finish build decisions
- **archetypes/archetypes.json is the taxonomy the gates read** (family by name, budgets per kit canvas `wide` and
  `std`, exemplars, sheet, card), published by `scripts/build_archetypes.py` from the library export; `--check`
  exits 1 when stale or leaking. `gates/families.json` carries the same v1 families as the fallback. The golden
  fixture, tests and negatives use v1 slugs and family names.
- **A `std` budget** is the library's w10 measure when two or more compact exemplars exist, else the wide budget x
  the canvas area ratio, marked `derived`.
- **P08 judges a card by ink, crediting the kit's fitting slack** (15% of the ink height, never past the frame). The
  first example build passed P08 with cards half empty because the gate read text frames. Planter
  `stretched-frame` proves the new reading; it passes under the frame reading by arithmetic.
- **Fingerprint adjudication, skill text.** `references/copy.md` quotes banned words as the rule itself (prototype,
  POC, "This slide shows") and `references/library.md` names the user's own deck title (Prototype-vs-Enterprise
  POV). These are internal Claude-context files, the class CLAUDE.md is in; kept. Canary verified firing.
- **Acceptance is reduced to one fictional RFP deck** of 8 to 10 slides built by one fresh agent with only the
  skill (ruling 9); the three-judge panel and trigger evals are deferred with the twin.

## 2026-10-03 · After the acceptance deck (user chose: fix the leak and the cheap bugs, ship)
- **Kit**: `prims.block` (rounded strong fill) and `prims.circle` (plain circle, filled or ring) close the gap
  that forced empty-label discs; `rect` already drew square solids and is now documented.
- **P11** exempts fully rounded shapes (radius at least 45% of the short side: pills and circles) from the card
  corner rule; a kit pill failing a gate by size was a gate bug.
- **P14** lets a slide tagged `cover` stack its title on up to three lines; **P09** lets a cover carry label lines
  of 12 words or fewer under its title (parties, engagement, date). Planter `cover-sentence` proves a sentence there
  still fails.
- **Budgets**: the published wide budget is the `@norm` measure every card cites (it was w13, so cards and gates
  disagreed); advisory floors never exceed half their budget.
- **run_all** marks a gate whose sub-check printed SKIPPED as `partial`, never `pass`.
- **SKILL.md** documents lines (hairline is orthogonal; a diagonal spoke is `connect(head="none", role="hairline")`),
  type translation up to the house scale, variant slugs, and a short-RFP rule (merge adjacent requested sections
  before dropping the agenda; a house default).
- **Deferred, logged**: P07 flags staggered swimlane lanes; P10 does not count gantt bars and gate lines as a
  device; P24 discards an unfilled stat band a card prescribes; LibreOffice hyphenation is unchecked until R01.

## 2026-10-03 · RULING 10 — Staged route to the EPIC look (user); amends ruling 9
The acceptance deck was rejected as not cutting-edge against the flagship. Measured gap (median per slide,
acceptance vs flagship slides 2 to 104): vivid colour 0.8% vs 7.6% of the area, pastel tint 13.5% vs 2.7%, vivid
hues 1 vs 3, words 100 vs 150, shapes 41 vs 52. Route, with a stop for the user's yes after each step:
1. the epic layer in theme and kit (solid brand bands, near-black panels, numbered headers), proven on three
   rebuilt acceptance slides;
2. intake of the user's architecture decks and a re-rank of the architecture archetypes;
3. the device library (ruling 3, un-deferred): about 30 lifted, sanitised, theme-mapped native devices;
4. a showcase deck exercising all 45 archetypes as the acceptance test.

## 2026-10-03 · RULING 11 — Intake: the architecture decks (user)
the sample AI architectures deck (4 slides), a pharma-client capabilities deck (14), the agents-on-structured-data deck (12); file names live only in the library manifest.
The CI decks, the material-planner POV and the AI Hub scale-up proposal stay out. Client-authored decks stay out.

## 2026-10-03 · RULING 12 — Colour: brand solid plus near-black panels (user)
Solid brand bands and cards, and near-black stat and header panels on light slides. No second hue: a client cut is
still one accent swap. Pastel tints are for large backgrounds only, never the default container.

## 2026-10-03 · RULING 13 — Technical architecture boards pinned as a variant (user)
The two service-icon reference architecture boards from the intake are pinned as exemplars of a named
`technical-service-icons` variant of solution-architecture (a21), by the user's ruling, although their catalogue
quality is 3 and 2 (type down to 5pt, words broken in narrow tiles, half-empty agent cards). The scores stay on
record unaltered. The card translates the device: type raised to the 8pt floor, fewer tiles per layer, a measured
+N more chip. Layered-architecture, solution-architecture and hub-and-spoke get a comparative re-rank with the new
members; the other affected archetypes a scripted one, and a comparatively ranked archetype is re-ranked only where
a new member's quality reaches its top (cost cap, logged in the library DECISIONS).

## 2026-10-03 · RULING 14 — Step 3 at full scale: about 30 devices (user)
The sanitised device library is built at the original scale of about 30 lifted native devices (ruling 3), quoted at
about 5M tokens after step 2 ran 2.8M against a 1M estimate.

## 2026-10-03 · Device pilot findings
- **P09 catches a high foot band.** A wide band no taller than 1in, ending in the bottom 15% of the canvas and
  carrying one sentence across half its width or more, is a foot summary or next-step band wherever its top sits.
  The pilot device kept one at 6.06in, above the old 6.20in line. Multi-column content bands still pass. Planter
  `high-foot-band`.
- **Device agents hold card bodies to one or two lines.** Density comes from the device, never from paragraphs;
  cards shrink to their content and the freed height goes to the device.

## 2026-10-03 · Device library built (step 3 of ruling 10, ruling 14)
- 31 devices, DL01 to DL31, lifted from 31 reference slides by `scripts/lift_device.py` (identity stripped, every
  word replaced, colours mapped to roles, type floored) and finished by one agent each through a versioned
  `devices/work/DLnn/build.py`. Each passes all 25 implemented gates; the assembled `devices/devices.pptx` passes
  the library gates (floor, bounds, style, package, colour, fingerprints, leak, icons, contrast).
- **P19 scopes device samples.** A slide tagged with a device's variant is checked against all of that device's
  sample copy; every other slide only against samples of four words or more, so ordinary short copy ("Not
  started") never reads as filler.
- **Slot roles.** Agents used a slot's `role` for its purpose; the assembler moves any value that is not a theme
  role to `purpose`, and `devices.place` keeps each paragraph's own size, weight, colour role and alignment.
- Token cost: device agents about 4.5M (31 at about 145K each), the pilot 0.12M.

## 2026-10-03 · Showcase acceptance build (step 4 of ruling 10)
- 49 slides, all 45 archetypes, built by nine agents on one canon (`acceptance/showcase/canon.json`): 22 slides
  place a library device, 27 are composed. The assembled deck passes all 25 implemented gates, P15 variety and P21
  determinism included; a canon sweep finds every price, date and count consistent.
- **devices.place fixed** for what every agent hit: colours match by scheme slot and lumMod/lumOff (serialised
  XML carried namespace declarations, so every run read back as ink); a raw RGB colour maps to its nearest role; a
  slot's ground is the topmost fill painted behind it covering 60% of its box, in absolute geometry, by shape id
  (lxml proxy ids are not stable); glyph slots keep the device's colour; anchors and paragraph spacing are kept;
  group slots take one value per text; table slots take rows of cells; rotated slots fit on their frame sides. Test:
  every library device places with plain fills in every slot (`tests/test_devices.py`).
- **P14** reads the kit's named `title` on a content slide (a 28pt stat near the top was taken for the title); a
  cover is still read visually (the `cover-tier-title` plant still fails).
- **P19** ignores one-word device samples ("Approach" is ordinary copy).
- **Open finding (not acted on):** P17 does not load the hook's maturity tier, and `mat-prototype` covers
  prototype and POC but not demo or alpha, which CLAUDE.md §4 also bans for the firm's own maturity. A "Live demo"
  pill passed every gate; caught by reading the render. The fix is in the global hook, so it is the user's call.
- Token cost: showcase agents about 1.8M.

## 2026-10-03 · RULING 15 — Showcase accepted; the skill ships (user)
SKILL.draft.md became SKILL.md; the skill triggers in every session.

## 2026-10-03 · RULING 16 — Maturity words: deck gate only (user)
`dv-maturity` (demo, alpha, prototype, proof of concept, POC) joins the opt-in deck-voice tier in
`~/.claude/hooks/fingerprints.json`: P17 runs it on slides, the editor hook does not (its `mat-prototype` rule is
unchanged). A deck quoting the client's own vocabulary grants `P17:dv-maturity` in deck.json with its source.
Planter `maturity-word`; canary sentence added.

## 2026-10-03 · RULING 17 — Density to the measured range, and a technical section (user)
The user asked for slightly more content on some slides and for architecture and technical slides. Measured: 16 of
40 showcase content slides sat under their archetype's exemplar p25 of words (median 135 words). The advisory floor
returns to ruling 2's measured p25 (the half-budget cap is withdrawn) and SKILL.md asks every content slide to fill
to its archetype's measured range. The showcase gains a technical section, "How it is built", on the house AWS stack
with official service marks: cloud reference architecture, agent runtime, data architecture, release pipeline and
environments, security and access controls, and a signal-to-field API sequence. Device glyph slots take `vendor:`
keys.

## 2026-10-03 · Ruling 17 applied to the showcase
- 56 slides, six sections. A new "How it is built" section has 7 slides on the AWS house stack with official marks
  (reference architecture, agent runtime, data architecture, release pipeline, security controls, signal-to-field
  sequence). 47 content slides, median 162 words (was 135). Passes all 25 implemented gates.
- **P20 judges a vendor mark's label**, the alt text before its `(vendor mark <key>)` record, so "Amazon Bedrock"
  is semantic alt text.
- Six slides stay under their exemplar p25: from-to-shift DL14 (100 of 121; the device has no free zone left),
  both layered-architecture slides (185 and 234 of 259), both swimlanes (224 and 160 of 234) and decision-logic
  (169 of 183). The floor is advisory; they read full in the renders.
- Token cost: about 1.6M (quoted 1.3M).

## 2026-10-03 · RULING 18 — Architecture slides come from a diagram engine with three grammars (user)
The showcase architecture slides were rejected as not reading like enterprise AWS, Azure or the user's own
architecture decks. Measured against eight reference architecture slides:
- product logos: 20 to 45 per slide (median 36) against 0 to 11 (one slide drew 48 generic line glyphs);
- icons boxed alone in a tile: 0 to 10% (one chip board 75%) against 91 to 100%;
- arrows labelled with what flows: 7 of 7 to 11 of 14 against 0 of 15;
- no cloud boundary grammar;
- the data-architecture slide was a text matrix.
Route: `deckkit.arch` draws a declared diagram (groups, services, flows, steps) in one of three grammars:
- official AWS: Cloud, Region, VPC, AZ and subnet groups in the AWS notation colours; floating service icons;
  labelled flows; numbered steps with a legend;
- official Azure: subscription, resource group, VNet, subnet and private endpoint;
- house layered: region header tabs, floating product marks, labelled flows, platform band. An L0 master carries
  no arrows (CLAUDE.md §8).
The AWS and Azure notation colours are identity colours of the notation: registered, never moved by a theme. Gate
P26 holds architecture slides to the measured grammar. The kit's product marks extend to the diagrams package's
onprem, programming and saas sets, byte-verified as before.

## 2026-10-03 · RULING 19 — Marks with no offline source come from the 21st MCP logo search (user)
LangGraph, LangChain, Langfuse, Anthropic, Dataiku and other marks absent offline are fetched once through the 21st
MCP logo search. Each is stored in the kit with its source, fetch date and sha256, and verified by bytes like the
vendor marks. Marks are used nominatively, unaltered, to name the product in a diagram.

## 2026-10-03 · RULING 20 — Every technical diagram type, researched first (user)
The bar covers every technical diagram, not only architecture: solution architecture (AWS, Azure), the house L0
master and deep dive, deployment and network topology, CI/CD and release, MLOps and LLMOps, DFD and threat model,
data flow and lineage, sequence, and event-driven integration. A research sweep sets the measured spec per type
before the engine is extended: the user's own epic diagrams (the AI Council platform architecture, a pharma
client's KOL architecture and AWS deployment view, the AI architecture test decks) plus the official AWS, Azure and
Google architecture centres and the diagram-craft literature. Notes and spec are internal at
`library/design/tech-diagrams/`; a scrubbed spec becomes `references/tech-diagrams.md`.

## 2026-10-03 · RULING 21 — Technical diagram spec decisions (user)
- **Logos:** LangGraph, LangChain, Langfuse, Anthropic and Dataiku come from each vendor's own published SVG (press kit
  or official repository), byte-verified into `kit/assets/marks/` with source URL and date, used unaltered to name the
  product. 21st rejected its credentials on reconnect; this supersedes ruling 19's source, not its rules.
- **AWS VPC purple** `#8C4FFF` stays as a 1.25pt stroke and corner icon on AWS-notation slides only, never a fill.
- **Azure step badges** are green `#107C10` (identity `azure-step`), the Azure Architecture Center notation.
- **More diagram types** join the showcase: current versus target state, agent state machine, C4 context and container,
  and multi-region DR with landing zone; 16 technical types in all.
- **Defaults taken from the spec** (`library/design/tech-diagrams/spec.md` §6):
  - the house platform band is light (`card`), so dark logos stay visible;
  - no brand-colour edge on logo chips (the left-accent ban);
  - the faint Azure strokes pass only with a label and a corner icon;
  - medallion and threat colours stay off until the user introduces them.

## 2026-10-03 · RULING 22 — One final end-to-end round, bounded (user)
The user asked for one final review and polish so that the skill produces cutting-edge proposal decks across
archetypes, representation, styling, charts, component and tech diagrams, and functional and non-functional
quality. The best reference slides must be used. It must not become a 10-hour job.
- **Review:** six read-only lenses (docs against code, visual quality, charts, archetype and reference coverage,
  health, fresh-agent usability), reported to `library/design/final-review/`.
- **Build:** one parallel round:
  - the review fixes;
  - a native chart module;
  - the remaining device lifts;
  - the tech diagram types from rulings 20 and 21;
  - the showcase rebuild.
- **Verify:** a full gate run, every slide read, and the commit.

## 2026-10-03 · RULING 23 — Self-contained, easy to use, client brand asked for (user)
- **Self-contained.** The skill must run with no outside folder. Everything a build reads at runtime lives inside the
  skill: cards, budgets, devices, themes, marks, and the greeked exemplar views and sheets. The raw reference decks
  and the mining pipeline stay in `~/Codes/Decks-For-Visuals/`.
  - They are client material (279MB of pptx carrying client names, logos and figures).
  - Copying them into the skill would widen their distribution with every copy of the skill, against CLAUDE.md §5.
  - Nothing at runtime needs them.
  The skill reports the library only as an optional source for re-mining and real renders.
- **Easy to use.**
  - `/deck` works anywhere in a prompt; a first word selects the mode (new, slide, edit, review, diagram, chart,
    brand).
  - Once loaded, every later iteration in the session goes through the skill, including one slide or one edit.
  - A scaffolded deck folder carries a short CLAUDE.md, so later sessions in that folder load the skill too.
- **Light documentation.** A command table at the top of SKILL.md, a short README.md, and the slash-command
  description.
- **Client brand intake.** When a deck is for a client and no colour system or logo was given, the skill asks for:
  - the brand colours (hex, or a website to read them from);
  - the logo file;
  - the font.
  It then builds a client theme (contrast-solved, identity colours kept) and a cover logo lockup. The fallback is the
  house theme, and it is used only when the user says so.

## 2026-10-03 · Ruling 18 built: deckkit.arch, P26, brand marks (workflow task)
- **Engine** `kit/deckkit/arch.py`: a declared diagram (groups, nodes, flows, steps) drawn in the aws, azure or house
  grammar on measured grids; marks float with captions; flows run edge to edge (straight, Z, C, L into a top, U over a
  row), never along a border or another flow, and carry a label or a numbered badge; `l0=True` refuses flows.
  `align`, `weights`, `stretch`, `gaps`, `head_air` and node `anchor` are the layout levers; `render(draft=True)` lists
  what does not fit while iterating.
- **Colours verified 2026-10-03** (detail in the module header): the AWS toolkit deck 07312026 corrects three of the
  brief's starting values (AZ `#00A4A6` not `#147EBA`; security group `#DD344C` not `#DD3522`; subnets carry no fill).
  Azure publishes no boundary colours; VNet, subnet, zone and region come from Microsoft's reference diagrams, the
  subscription and resource group colours are house choices. Azure step badges are `#107C10` (ruling 21). All are
  identity colours in both themes; `Theme.spec` writes an identity name as srgbClr and refuses a name that shadows a role.
- **Marks** `icons.mark` and `kit/assets/marks/registry.json` (empty); P22 verifies `mark.*` pictures by bytes.
- **Gate P26** with five planters; P22 gains three mark planters; 119 negatives behave.
- **Open, for the user**: P18 flags official vendor marks that the reference decks also embed (10 marks on the example);
  the example grants them in `deck.json` `media_allow`. A P18 exemption for P22-verified marks is the user's call.

## 2026-10-03 · Ruling 18 fix round: the critics' defects on the four engine slides (workflow task)
- **Engine** `deckkit.arch` gains the levers the critics' fixes needed, each a general rule, not a slide patch:
  - notation per grammar: aws flows `#232F3E` 1.25pt open arrow, aws badges 0.30in with a 9pt numeral, aws group
    labels and node names regular (spec 1.2, 1.4, 1.5); azure and house keep 1.0pt triangles and 0.22in badges;
  - edge pins (`anchor="edge:l|edge:r|edge:t"`) centred on a group's frame line, caption outside; captions beside
    an icon (`caption="right|left"`) so a vertical flow can leave its bottom; `align(..., axis="x")`;
  - `group(..., band=, drop=, row_gap=, gutter=)`; house kinds `section`, `boundary`, `zone`; rails drawn as light
    cards with a label tab; round header tabs on house cards; the Azure VNet as a filled ground with its label above
    and an NSG shield on every subnet; flow kind `private` keyed in the legend;
  - routing picks the route with the fewest crossings and refuses a final leg under 0.15in; badges go first, beside
    the source end (no destination fallback, never over a line); labels sit on one line (never wrapped) beside the
    longest segment that holds them, clear of every other flow, else knocked out on their own line;
  - marks are cropped to their ink with `a:srcRect` (bytes untouched) so they share one optical size; metrics count
    product marks without actor glyphs and count placed labels (`labelled`, `badge_only`); draft mode lists caption,
    height, label and badge failures instead of raising;
  - a house deep dive refuses a name of three words or fewer that wraps; an L0 master and the aws and azure notations
    wrap long service names, as AWS and Azure do.
- **Gate P26** now holds the spec's checks: marks without actor glyphs (floor 20; house deep dive 15; layered 16),
  boxed alone at most 10%, labels or badges or a keyed style on 80% of flows, captions (an edge pin's above), no
  crossing (h), steps 1..N in one size within the type's band (j), outer boundary labels state a fact and enough
  boundary kinds (k), L0 regions varied with two icon tiers, no orphan outside a band (r), AWS and Azure notation
  (s: actors outside the cloud, regional services and PaaS outside the network, VPC crossings land on a pin), label
  and badge collisions (u), one name one mark across slides (v), ink at least 75% of a mark (w). Nine new planters;
  P04 and P05 accept an edge pin on its border. 128 negatives behave.
- **Examples** rebuilt: AWS (Region with 2 AZs, agents and data subnets, S3 and Bedrock endpoints, ALB and NAT on
  the VPC edge, CloudFront ingress, SaaS outside, ops band, 10 steps, 23 marks), Azure (Region, subscription, VNet
  tiled by integration, gateway, agents and endpoint subnets, every PaaS service straight across from its private
  endpoint, shared-services band, the same 10 steps, 24 marks), house L0 (dashed platform boundary, client estate
  outside, identity and operations rails, regions of unequal width with sections, two icon tiers, delivery band,
  36 marks, no arrows), house deep dive (account boundary, agent trust zone, sections, 6 numbered hops, legend).
- **Not applied, with the reason:**
  - AWS density 28 to 34 marks: the slide carries 23 product marks plus 3 actors. Four nesting levels, ten steps and
    a legend in the 12.4 x 6.0in field leave no room for more without 2-line wrapping everywhere; spec 3.1's floor
    is 20.
  - A CRM SaaS mark outside the AWS Cloud: no CRM vendor mark exists offline (no Salesforce or Veeva in the diagrams
    package); the L0 shows CRM as an actor glyph.
  - Claude beside Bedrock on the AWS slide: folded into Bedrock's role ("Claude models"); a separate Claude node
    could not be routed without a crossing. The house slides keep Claude with its `model call` flow.
  - V24 Entra ID: the V24 set has no plain Entra ID service icon; the other V24 icons are already in the diagrams
    package under newer keys and the azure slide uses them.
  - Azure tiles per PaaS service (AAC convention): the azure grammar floats marks, by ruling 18.
  - P26.h hop gaps: the engine never draws a crossing, so the gate fails any crossing instead of counting hops.
  - "Refuse a badge within 0.45in of an icon that already has one": kept as a preference, not a refusal; a hard
    refusal left steps with no place on the AWS and Azure slides.
  - A one-line step legend on the AWS slide: ten steps in one bottom row wrap to two lines; the rail is shorter.
- **For the user:** the showcase deck's rejected architecture slides (v2 slides 22, 23, 32, 34) already failed P26
  and now fail more of it; they are rebuilt from the engine in the showcase round, not patched.
