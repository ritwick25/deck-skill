# The reference library

The skill's archetypes, budgets and design-system numbers were measured from a private library of accepted and
reference decks at `~/Codes/Decks-For-Visuals/library/` (`DECK_LIBRARY` overrides the path). The skill carries only
what was published from it: the cards, `archetypes.json`, the design system, the storylines and the device registry.
Slides are named by neutral ids (`d01-s015`); the id-to-file map lives only in the library's `manifest.json`.

## Looking at exemplars
- `scripts/find.py <slug>` prints the card, the budget, the greeked contact sheet and each exemplar's greeked view.
  Read the sheet before building: it shows layout, type hierarchy and icons with every word and logo painted out.
- Borrow structure, never words. A greeked view is the only view that may inform a client deck.
- `--real` prints the real renders. They carry client text and marks: look, never copy a word, never share.
- Anti-exemplars on each card are named failures. Read them as what not to build.
- When the library is absent, `find.py` prints SKIPPED and the card's zones, components and translation table are the
  whole reference.

## What never happens
- A reference slide is never cloned into client work, and its words never travel (gate P18 hashes them).
- A reference render or sheet is never attached, published or pasted outside this machine.
- The library is not edited during a deck build. New reference decks enter through its own pipeline
  (`library/tools/`), which re-measures and re-exports. `scripts/build_archetypes.py` then republishes.

## Cloning the user's own accepted decks
Clone-and-retext is right for the user's own accepted decks (CLAUDE.md §6): `deckkit.clone` copies a slide between
packages; retext runs, not paragraphs. That is a different act from borrowing a reference device. The accepted tier
(SFA v0.9, the RFI deck, the Prototype-vs-Enterprise POV, the fabric POV) is catalogued in the library and is the
calibration for what the house accepts.

## Refreshing
```bash
PY=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
$PY ~/Codes/Decks-For-Visuals/library/tools/export.py        # rebuild the scrubbed export
$PY ~/.claude/skills/deck/scripts/build_archetypes.py         # republish into the skill
$PY ~/.claude/skills/deck/scripts/build_archetypes.py --check # exit 1 when stale or leaking
```
