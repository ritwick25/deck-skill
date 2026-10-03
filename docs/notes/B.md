# Track B: gates (ruling 22 shared contracts)

## What changed, per gate
- **P03 bounds** adds content margins: any leaf more than 0.10in (x k) past the content band's left or right edge
  (WIDE 0.50 to 12.90in, STD 0.28 to 9.72in) fails, one finding per top-level shape naming its worst leaf. Undrawn
  text is judged by its ink box. `bleed.*` on the shape or any ancestor group exempts it (slide edge too).
- **P10**: a graphicFrame with a chart or chartex graphicData uri is the slide's device; a table frame is not.
- **P13**: docstring states the floor is the measured p25 (ruling 17). New FAIL: an archetype tag in neither
  archetypes.json nor deck.json `budgets`, with `difflib` suggestions. **P14**: `cover`, `closing` and
  `section-divider` may wrap to 3 lines (`STACKED`, `COVER_LINES`).
- **P15 variety** adds the foot-band cap. `foot_band(ctx, i) -> leaf | None`: a solid fill that is not paper or
  near-white, at least 85% of content width, under 1.3in x k tall, bottom in the lower quarter of the content band,
  carrying text (its own or a text block painted on it), nothing drawn below but a source line of 12 words or fewer.
  It fails when more than max(1, int(0.2 x content slides)) end on one, and on every adjacent pair.
- **P16 colour** adds small tint: a `sp` filled accent-tint or accent-wash (resolved hex) under 4 sq in x k^2 fails
  unless it or an ancestor group is named `state.*`. `_small_tints(ctx, i)`.
- **P18 leak**: `verified_marks(ctx) -> {part: "vendor.<key>" | "mark.<key>"}`. A media part behind a picture P22
  verifies by bytes (vendor: name and alt agree, key resolves, blob is the diagrams resource; mark: registry SVG and
  PNG) skips the corpus sha256 and dHash checks. A NOTE gives the count. The name alone never exempts. On the arch
  deck with `media_allow` removed: 14 FAILs without the exemption, 0 with it (72 parts exempt).
- **P23**: a chipless stat passes when a slide text reads exactly its chip plus " figures" ("Illustrative figures",
  "Target figures", "Benchmark figures"; any case). A label of another kind does not count.

## Runner, negatives, characteriser
- `run_all.py`: a passing gate with advisories shows `N advisory: sX <first>` in the detail column. PENDING rows
  show only with `-v` or when named in `--only`. The summary counts implemented gates. `--theme T.json` (cwd-relative)
  is for a deck with no deck.json beside it.
- `negatives.py`: 9 new planters (content-margin, table-not-a-device, misspelt-archetype, closing-four-lines,
  foot-band-adjacent, foot-band-share, small-tint, forged-mark-media, wrong-shared-label). New helper
  `foot_band(deck, slides)`. Discovery: `PLANTERS = _discover(PLANTERS)` imports `PLANTERS` from every
  `gates/negatives_*.py`, sorted by name. A sibling writes `from negatives import Planter, members, edit_slide, ...`
  and defines `PLANTERS = [Planter(name, gate, plants, fn, expect)]`. A same-named sibling planter replaces the
  earlier one, so E1 can move the P26 planters without double runs. A sibling that fails to import becomes a
  `DISCOVERY ERROR` row and fails the run. It is never skipped.
- `characterise.py`: inputs `library/_work/src/d01|d15|d18.pptx`, staging and `fp_report.json` under
  `library/_work/characterise/` (`DECK_LIBRARY` overrides). It refuses a staging folder or `--out` inside the skill,
  and exits 0 with a message when the library is absent.
- Tests: library-bound classes skip without the library (`DECK_LIBRARY=/nonexistent`: 104 ran, 41 skipped). The
  gate count comes from registry.json; discovery is tested; TestContracts holds 8 pass-side cases.

## Verified
- `run_all --negatives` exit 0, 137 of 137, 26/26 covered. arch.pptx: 25 pass; P21 FAILs on the rebuild (kit, not
  gates: `arch.py` private flow `sysDashDot`, which `prims.connect` refuses). My five test modules pass; the full
  suite fails 8, all other tracks' WIP: test_arch (same dash), test_devices x3 (place() demands archetype=),
  test_core x3 (stale base-wide.pptx, cvd_report, `_lighten_expr`), test_builder (`scripts/capture.py` floor).

## Fails the new rules (for D0 and the showcase rebuild)
- **devices P03:** DL08, 09, 10, 14, 17, 21, 22, 23, 24, 26, 28, 30, 31 (DL31: 35 findings, struct.page from 0.00in).
- **devices P16:** DL03, 04, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 18, 19, 21, 25.
- **devices foot bands:** DL07 struct.rail, DL10 struct.paths.frame, DL21 struct.enabler.strip.
- **Showcase v2 P03:** s7, 9, 11, 15, 22, 23, 25, 26, 28, 43, 53 (s28 screen.band.l/r bleed on purpose: `bleed.*`).
- **Showcase v2 P15:** 12 of 47 end on a foot band (3, 12, 21, 22, 24, 25, 32, 37, 39, 44, 50, 54; cap 9); 21-22, 24-25.
- **Showcase v2 P16:** s11, s14, s15, s21, s22, s25, s27, s34, s36, s40, s41, s42, s49, s51, s53, s54.

## Requests to other owners
- A1 or E1: `prims.DASHES` vs the private flow dash. A1: stat_band's label is one text holding only the label.
  `_shared.py` (unowned): docstring says P01 to P23; "no 'theme'" should read "no deck.json in <folder>; --theme".
- Docs agent: rules.md rows for P03 margins, P15 foot bands, P16 small tint, P18 marks, P23 shared label, P13 slug;
  SKILL REVIEW row `run_all.py --deck X --theme T.json -v`. Cleanup (user's call): `.cache/fp_report.json`, the old
  characteriser report, quotes client text inside the skill.
