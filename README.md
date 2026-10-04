# deck

The house deck builder for Claude Code. It plans a deck, picks one measured archetype per slide, builds it natively
in python-pptx with its own kit, draws architecture diagrams and charts with its own engines, gates the result
against the house rules and reads every slide. Everything it needs at runtime lives in this folder.

## Commands

| Command | Does |
|---|---|
| `/deck new <brief>` | Plans and builds a whole deck |
| `/deck slide <what> [--deck path]` | Adds or rebuilds one slide |
| `/deck edit <path> <change>` | Changes only what was named, then re-gates |
| `/deck review <path>` | Gates and reads every slide, changes nothing |
| `/deck diagram <type> <subject>` | Architecture or technical diagram (aws, azure, house) |
| `/deck chart <what>` | A native chart slide from supplied data |
| `/deck brand <client>` | Client theme and logo lockup |
| `/deck` | Picks the mode from context |

`/deck` works anywhere in a longer prompt. Once loaded it handles every later iteration in the session, one slide
or one edit, without typing it again. After a context compaction, type it once more.

## Quickstart

1. `/deck new` with the brief: who reads it, what they decide, the slide count.
2. Brand intake. For a client deck with no brand given, the skill asks for the colours (hex or a website), the logo
   file and the font, then builds the client theme. The house theme is used only on request.
3. Say yes to the restated object and the storyline (one line per slide: title claim, archetype).
4. The skill scaffolds the folder (`build.py`, `deck.json`, `CLAUDE.md`) and builds.
5. Gates pass and every slide is rendered and read before it reports. `/deck review <path>` repeats that on demand.

## Where things live

| Path | Holds |
|---|---|
| `SKILL.md` | Commands, procedure, brand intake, the archetype, diagram and chart choosers, the kit API |
| `archetypes/` | 45 cards in 10 families and `archetypes.json` (budgets, floors, exemplars) |
| `refs/` | The greeked reference pack: 45 contact sheets, 249 exemplar views, `catalog.json` |
| `showcase/` | The accepted 65-slide showcase deck, `index.json` (archetype, variant, device and code per slide) and 4-up `sheets/`; refresh with `scripts/sync_showcase.py` |
| `devices/` | 44 sanitised native devices (DL01 to DL30, DL32 to DL45), `devices.json`, renders |
| `themes/` | House themes `sigmoid` and `neutral` (client themes live in the deck's folder) |
| `kit/deckkit/` | Theme roles, primitives, text, compose, exhibits, tables, charts, glyphs, marks, diagram engines |
| `gates/` | P01 to P27, `run_all.py`, the negatives |
| `scripts/` | `new_deck.py`, `find.py`, `brand.py`, `render.py`, `capture.py`, the worked examples, `selftest.py` |
| `references/` | Rules, design system, tech diagrams, charts, devices, copy, storylines, the library |
| `DECISIONS.md` | Every ruling, dated, newest last |

## Tests and checks

```bash
PY=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
cd ~/.claude/skills/deck
$PY -m unittest discover -s tests -t .      # the unit suite (about 540 tests, a few minutes)
$PY gates/run_all.py --negatives            # every gate fails on its own planted breakage
$PY gates/run_all.py --deck X.pptx          # gate one deck
$PY scripts/selftest.py                     # frontmatter, chooser, reference pack, name scan, self-containment
$PY scripts/build_archetypes.py --check     # the published cards and pack are not stale (needs the library)
```

Library-bound tests skip when the library is absent (`DECK_LIBRARY=/nonexistent` proves it).

## Refreshing from the library

The raw reference decks and the mining pipeline stay in the library (`DECK_LIBRARY`, default
`~/Codes/Decks-For-Visuals/library`). Nothing at runtime needs it. `references/library.md` has the refresh order.

## House rules

`~/.claude/CLAUDE.md` sections 3, 4, 6 and 8 govern every slide and win over this skill. `references/rules.md` maps
each rule to its gate.
