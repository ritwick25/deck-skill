# The reference pack and the library

The skill is self-contained (ruling 23): every build, gate run and lookup reads only files inside the skill. The
archetypes, budgets and design-system numbers were measured from a private library of accepted and reference decks;
the skill carries only what was published from it, scrubbed and greeked. Slides are named by neutral ids
(`d01-s015`); the id-to-file map lives only in the library's `manifest.json`, never here.

## What ships inside the skill

| Path | Holds |
|---|---|
| `archetypes/<slug>.md`, `archetypes.json` | the 45 cards, families, budgets per canvas, advisory floors, exemplar ids |
| `refs/sheets/aNN.jpg` | one greeked contact sheet per archetype (45) |
| `refs/views/dNN-sNNN.jpg` | the greeked view of every exemplar and anti-exemplar (249) |
| `refs/catalog.json` | the pack's lists and every file's sha256; `selftest.py` fails a missing, stray or altered file |
| `devices/` | the 44 sanitised devices, `devices.json`, sigmoid and neutral renders |
| `devices/refs/` | the hashed leak index gate P18 reads (SHA-1 digests only, no plaintext) |
| `references/design-system.md`, `storylines.md`, `devices.md` | published from the library export; never edit by hand |

A greeked image shows layout, type hierarchy and icons with every word and logo painted out. Only greeked images
enter the pack: a view is copied only when its OCR sweep came back clean.

## Looking at exemplars

- `$PY $K/scripts/find.py <slug>` (or `aNN`) prints the archetype id and definition, the wide and std budgets with
  their advisory floors, the card's path, the library devices serving the archetype with their render paths, the
  greeked contact sheet and each exemplar's greeked view. Read the sheet before building.
- `find.py` alone lists every family and archetype with its wide budget; `--search "words"` matches names and
  definitions. A device id (`DL07`) is not an archetype: read `references/device-library.md` or `devices/devices.json`
  for its slots.
- Borrow structure, never words. A greeked view is the only view that may inform a client deck.
- Anti-exemplars on each card are named failures: what not to build.

## The optional library

`~/Codes/Decks-For-Visuals/library/` (the `DECK_LIBRARY` environment variable moves it) holds the raw reference
decks, their real renders and the mining pipeline. It is internal client material and never enters the skill. Nothing
at runtime needs it; when it is absent every library-only command prints UNAVAILABLE or SKIPPED rather than pretending.

- `find.py <slug> --real` prints the real renders. They carry client text and marks: look, never copy a word, never
  share, never attach.
- `scripts/lift_device.py` lifts a new device from a library slide; `gates/characterise.py` measures the gates'
  false-positive rates on the library's copies of three reference decks (a characteriser: it never fails).
- New reference decks enter through the library's own pipeline (`library/tools/`), which re-measures and
  re-exports. The library is never edited during a deck build.

## Refreshing the skill from the library

```bash
PY=${DECK_PYTHON:-/Library/Frameworks/Python.framework/Versions/3.14/bin/python3}
[ -x "$PY" ] || PY=python3                     # another machine: its own python3, or set DECK_PYTHON
$PY ~/Codes/Decks-For-Visuals/library/tools/export.py         # rebuild the scrubbed export
$PY ~/.claude/skills/deck/scripts/build_archetypes.py          # republish cards, budgets, references and refs/
$PY ~/.claude/skills/deck/scripts/build_archetypes.py --pack   # refs/ only
$PY ~/.claude/skills/deck/scripts/build_archetypes.py --check  # exit 1 when anything published is stale or leaking
$PY ~/.claude/skills/deck/scripts/selftest.py                  # the skill's invariants, the name scan included
```

`references/design-system.md` comes from the library's `system/colour-roles.json` and `system/shape-icon-image.json`
through `tools/render_card.py render-system`, then `export.py` and `build_archetypes.py`. A hand edit makes
`--check` and `selftest.py` fail.

## Cloning the user's own accepted decks

Clone-and-retext is right for the user's own accepted decks (CLAUDE.md §6): `deckkit.clone.copy_shapes` copies a
slide's shapes between packages (a native chart travels with its own part and workbook); retext runs, never
paragraphs. That is a different act from borrowing a reference device. The accepted tier is catalogued in the library
and is the calibration for what the house accepts. A raw reference slide is never cloned into client work, and its
words never travel (gate P18 hashes them).
