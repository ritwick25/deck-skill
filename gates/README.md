# gates

The static deck gates (every pptx gate in `registry.json`), the runner and the characteriser.

| Command | What it is | Can it fail? |
|---|---|---|
| `$PY gates/run_all.py --deck X.pptx` | every registered gate on one deck; a passing gate with advisories shows their count and the first one in the detail column; later-phase PENDING rows show with `-v` | yes, exit 1 on any FAIL, 2 on a missing input |
| `$PY gates/run_all.py --deck X.pptx --theme T.json` | the same on a deck with no `deck.json` beside it (REVIEW mode) | yes |
| `$PY gates/run_all.py --negatives` | builds the golden, proves it passes, plants one breakage per planter (from `negatives.py` and every `negatives_*.py` it discovers) and requires each gate to fail on its own rule | yes |
| `$PY gates/run_all.py --list` | the registry, each gate's state and its planter count | no |
| `$PY gates/characterise.py` | every pptx gate over the library's reference-deck copies (d01, d15, d18), counted and sampled for review | **no, exit 0 whatever it finds** |

## Gates and the characteriser are different instruments

A gate tests machinery and fails. It is written for decks the kit builds, it is proven by a planter that makes it
fail on purpose, and the golden fixture proves it passes clean work. That is the whole of what a gate claims.

A gate's false-positive rate on real decks is not a gate. It is a measurement of the world, and it belongs to the
characteriser:

- `gates/characterise.py` stages each deck in the library's `_work/characterise/<stem>/` beside a review `deck.json`
  (client decks never enter the skill folder; without the library it says so and exits 0; `DECK_LIBRARY` moves it),
  runs every implemented pptx gate in-process, and writes `_work/characterise/fp_report.json`: per gate, per deck,
  the exit code, FAIL, advisory and note counts, the slides hit, the share of slides hit, the seconds and every
  finding.
- It then lists a stratified sample of three findings per gate (FAIL first, round-robin across decks, distinct
  slides first, fixed seed) with the slide's render path, for a person to mark true defect or false positive.
- It never computes a verdict and never exits non-zero. A rate it prints is not a threshold anything enforces.

The reference decks are hand-built and break house rules on purpose (they predate them), so most of what the
characteriser counts on them is real. Three gates are meaningless on them by construction: P18 leak matches the
corpus against itself, P21 determinism has no build command for a hand-built deck, and P15 variety fails every
untagged slide. Read those three columns as context, not as a rate.

When a sampled finding is a false positive, the fix is a ruling in `DECISIONS.md`, a narrower gate rule, a planter
that proves the narrowed gate still fails the breakage it exists for, and a pass-side test in
`tests/test_gate_rules.py` that proves it stops flagging the case. Then the characteriser runs again and its
counts are compared by hand.

## Files

- `registry.json` the gates, cheapest first, with kind and inputs.
- `_shared.py` context loading, leaf helpers (`ink_box`: a text block that draws nothing is judged where its words
  sit), measurement, reporting. No assertion lives there.
- `pNN_*.py` one gate each, every one runnable alone: `$PY gates/p10_density.py X.pptx`.
- `negatives.py` the planters; every implemented gate has at least one, and `--negatives` fails a gate without one.
  It discovers `PLANTERS` in every `gates/negatives_*.py` (a track's own planters: charts, architecture). A sibling
  imports `Planter` and the helpers from `negatives`; a same-named sibling planter replaces the earlier one; a sibling
  that does not import is a DISCOVERY ERROR row, never a silent skip.
- `characterise.py` the characteriser above.
