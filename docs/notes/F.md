# Track F: library and cards

## What changed
- **Ruling 12 in the cards.** The light-bg translation row of 13 cards (cover, section-divider, closing,
  problem-framing, case-wall, the-ask, worked-example, engagement-model, coverage-matrix, value-horizons,
  maturity-model, headline-figures, commercials) now says: only the slide ground goes light; a near-black
  (ink-deep, ink-strong) or brand band or panel inside the slide stays solid, its text in the fill's ON_FILL role;
  numerals on a dark band take accent-bright; pastel only as a full-bleed ground. Written through
  `library/tools/put_json.py card-src`, checked and rendered by `render_card.py`, exported, published.
  Only those 13 rows changed (house and consequence cells; the measured reference cell is untouched).
- **EPIC slide 38 excluded from both catalogs.** `library/tools/export.py` reads `exclusion` from the slide's shapes
  JSON and leaves the slide out of `export/catalog.json`, the internal `catalog.json` and `CATALOG.md`: no entry, no
  membership, no rank, no tile. Only `counts.excluded` (1) is kept. A final ranking, sheet or card that cites an
  excluded slide, or any staged file or catalog naming one, fails the export. Two tests in
  `library/tools/tests/test_export.py`.
- **Name scan reads aliases.** `scripts/build_archetypes.py denylist()` compiles every term and every alias (261
  patterns), with the library's matcher: 3 characters or fewer case-sensitive, bounded by non-alphanumerics. It
  raises on a missing list, fewer than 200 patterns, an alias canary that does not fire, or a short alias matching a
  lower-case word. selftest reports a raise as a failure and names `file:line`, never the term.
- **selftest ruling-12 check.** `pastel_rows()` fails a card whose light-bg house or consequence cell turns a panel
  pastel (light surface, row, strip, panel, band, card; light or pale tint; brand tint; flat light) unless a
  never/not/no precedes it in the sentence. Proven against the 11 old rows: 9 caught; the two missed say "white
  cards with a brand hairline" and nothing pastel-specific.
- `scripts/build_glyphs.py` LUCIDE path is `~/Codes/...expanduser()`, so no username sits in skill text.

## Signatures
- `build_archetypes.denylist() -> list[re.Pattern]` (raises RuntimeError); `DENY_MIN = 200`; `_term_rx(term)`.
- `selftest.pastel_rows() -> list[str]`; `selftest.PASTEL_PANEL`.
- `export.check_stage(lib, stage_root, catalog, internal, excluded=frozenset()) -> list[str]`.

## Run order (all exit 0 at hand-off)
```
$PY library/tools/render_card.py --check --all
$PY library/tools/render_card.py render aNN ...
$PY library/tools/export.py
$PY scripts/build_archetypes.py && $PY scripts/build_archetypes.py --check
$PY scripts/selftest.py
```
refs/ came out byte-identical (OCR finds no term in 294 images with aliases compiled).

## Tests
`tests/test_leak_scan.py` (new, 9): aliases and people match, short terms case-sensitive, refusal on missing,
short and alias-blind lists, selftest on a skill copy names a planted alias, a username path and a pastel light-bg
row. Skipped without the library.

## For the docs agent
- SKILL.md's card table can drop any "override the light-bg row" workaround: the cards now say ruling 12 directly.
- Notes and references must not carry `/Users/<name>/` paths: selftest now fails them by name.

## Open, not done (outside this track's files)
- Other card rows still send containers pastel under the flat-fill rule: a05 "dependencies band becomes a flat
  brand tint"; a14 "pale tint panels"; a31 "Flat brand tint"; a33 "side panel in a brand tint"; a20, a36, a38,
  a40, a43 "takes one flat tint" for a surviving band. The user's call whether ruling 12 reaches these.
- `library/records/d01-s038.json` still narrates the excluded slide. Not exported anywhere now; the finding's
  "[excluded]" rewrite of the record text, and a refusal in find.py and lift_device.py, are unowned.
