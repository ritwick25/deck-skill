# deck

The house deck builder for Claude Code. It plans a deck, picks one measured archetype per slide, builds it in
python-pptx, gates it against the house rules and reads every slide. Everything it needs at runtime lives here.

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
| `SKILL.md` | The procedure, the chooser and the kit API |
| `archetypes/` | 45 cards and `archetypes.json` (families, budgets, exemplars) |
| `refs/` | Greeked contact sheets and exemplar views, `catalog.json` |
| `devices/` | 31 sanitised native devices, `devices.json`, renders |
| `themes/` | House themes (client themes live in the deck's folder) |
| `kit/deckkit/` | Theme roles, primitives, text, glyphs, marks, the diagram engine |
| `gates/` | P01 to P26 and `run_all.py` |
| `scripts/` | `find.py`, `new_deck.py`, `brand.py`, `render.py`, `selftest.py` |
| `DECISIONS.md` | Every ruling, dated |

## Refreshing from the library

The raw reference decks and the mining pipeline stay in the library (`DECK_LIBRARY`, default
`~/Codes/Decks-For-Visuals/library`). Nothing at runtime needs it.

```bash
PY=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
$PY scripts/build_archetypes.py           # cards, budgets, references and refs/
$PY scripts/build_archetypes.py --pack    # refs/ only
$PY scripts/selftest.py                   # pack, paths and cards agree
```

## House rules

`~/.claude/CLAUDE.md` sections 3, 4 and 6 govern every slide and win over this skill. `references/rules.md` maps each
rule to its gate.
