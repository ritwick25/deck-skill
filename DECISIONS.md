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
