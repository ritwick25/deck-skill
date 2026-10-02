# deck skill — decisions

Newest ruling last. Every entry dated. Rulings 1–8 are the user's, recorded verbatim in substance.

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
