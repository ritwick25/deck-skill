# Brand intake: note for the SKILL.md docs agent (ruling 23)

What to put in SKILL.md, in this order. Everything below is built and tested (`tests/test_brand.py`, 11 tests).

## 1. The intake step (goes into the procedure, right after "Restate the object")

**Brand.** When the deck is for a client and the prompt gave no colour system or logo, ask the question in §2 before
building. Do not default to the house theme silently: the house theme is used only when the user picks it. When the
user gave a website, read its CSS (`--from-url`) and show the candidates; never pick a colour for them. Then make the
theme and scaffold or rebuild the deck on it.

A `/deck brand` first word starts this step on its own (an existing deck being re-skinned for a client).

## 2. The exact AskUserQuestion

Ask all three in one call. The house rule is the recommended option first:

```json
{"questions": [
  {"header": "Colours", "multiSelect": false,
   "question": "Which brand colours should the <Client> deck use?",
   "options": [
     {"label": "Read them from the client's website (Recommended)",
      "description": "Give the URL. The skill reads the production CSS, lists the candidate colours with their counts and the date read, and you confirm the primary."},
     {"label": "I'll give the hex codes",
      "description": "The primary first, then a secondary and any accents."},
     {"label": "Use the house theme",
      "description": "The firm's own colours. No client colour on any slide."}]},
  {"header": "Logo", "multiSelect": false,
   "question": "Which logo file should the cover carry?",
   "options": [
     {"label": "An SVG file (Recommended)", "description": "Embedded as is, with a PNG fallback for older readers."},
     {"label": "A PNG file", "description": "At least twice the size it is shown at, or it is refused."},
     {"label": "No logo", "description": "The cover carries the title stack only."}]},
  {"header": "Font", "multiSelect": false,
   "question": "Which font should the deck set in?",
   "options": [
     {"label": "Arial (Recommended)", "description": "Measured by the kit, installed everywhere."},
     {"label": "The client's brand font", "description": "Name it. Used only when it is installed and the kit can measure it; otherwise Arial, and the reason is printed."},
     {"label": "Montserrat", "description": "Measured by the kit; needs the font installed on every machine that opens the deck."}]}
]}
```

The free-text "Other" answer carries the URL, the hex codes, the logo path or the font name.

## 3. The commands

```bash
# from hexes
$PY $K/scripts/brand.py --name "Client" --primary "#0B6E4F" --secondary "#F2A900" [--accent HEX ...] \
    --logo logo.svg [--font "Name"] [--out ./brand]

# from the client's site: prints the candidates and writes brand/brand-candidates.json, exit 3, nothing picked
$PY $K/scripts/brand.py --name "Client" --from-url https://client.example
# after the user confirms: the theme records the URL and the date the CSS was read
$PY $K/scripts/brand.py --name "Client" --from-url https://client.example --primary "#0B6E4F" --secondary "#F2A900" --logo logo.svg

$PY -m deckkit theme check brand/theme.json        # re-check by hand at any time (PYTHONPATH=$K/kit)
```

What it writes, in `./brand/` unless `--out` says otherwise:
- `theme.json`, in the `themes/sigmoid.json` schema:
  - the client primary is accent1;
  - dk2 is the primary's hue deepened to 8:1 on white (navy, hyperlinks), and lt2 is its near-white tint;
  - accent2 to accent6 are the secondary and accents in the order given, padded with house slates;
  - any slot under 4.5:1 on white is recorded fill-only;
  - `identity` and `vendors` are copied verbatim from `sigmoid.json`;
  - accent-ink is solved to 4.5:1 against paper and card, and on-accent is picked (white or black);
  - a `brand` block records client, primary, secondaries, font (requested, used, why), logo (file, sha256, alt) and
    the CSS verification (url, fetched date).
- `logo.svg` or `logo.png`, the client file copied byte for byte.

Exit codes: 0 written, 1 refused, 2 bad input, 3 candidates printed and waiting for the user.

Refusals the user will see, and what to do:
- **A mid-luminance primary** (many oranges and reds) is refused, because no text colour clears 4.5:1 on both the
  accent and its deeper fill. The message names a deeper shade of the same hue. Rerun with that shade as `--primary`
  and the brand colour as `--secondary`.
- **More than five series colours** are refused. Keep the five the charts need.
- **A font the kit cannot measure** (anything but Arial and Montserrat), or one not installed, falls back to Arial and
  the note says which case it was.

## 4. How a deck uses the theme

- New deck: `$PY $K/scripts/new_deck.py FOLDER --name "Name" --theme brand/theme.json`. The scaffold's deck.json
  `"theme"` points at it, and its CLAUDE.md names the client and the logo.
- Existing deck: set deck.json `"theme"` to the theme.json path (relative to the deck folder), or pass `--theme` to a
  build script that takes one (`example_epic.py`, `example_arch.py`). The gates read the same deck.json `"theme"`.
- Cover and closing lockup in `build.py`:

```python
from deckkit import brand
th = Theme.load("brand/theme.json")
s = prs.slides.add_slide(prs.slide_layouts[0]); tag.tag(s, "cover", "title-stack")
brand.lockup(s, Box(0.9, 0.75, 5.0, 0.56), brand.logo_path(th), firm_logo=None, theme=th,
             name=th.data["brand"]["client"])
```

  - `lockup(slide, box, client_logo, firm_logo=None, *, theme, name, firm_name="Sigmoid")`:
    - the client logo, then the firm logo after a hairline divider when one is given;
    - left-aligned in the box and centred on its middle line, aspect kept at the box height;
    - SVG with a PNG fallback, PNG as is (refused under 2x its displayed size);
    - alt text "<Client> logo"; shapes `logo.client`, `logo.divider`, `logo.firm`.
  - It refuses any slide not tagged `cover` or `closing`: a client logo belongs on the cover lockup only, and P09
    fails a logo in the foot.
  - `logo_path(theme)` returns the logo beside the theme and refuses it when its sha256 no longer matches the
    record.
- The kit has no firm logo asset. Pass the firm's own file as `firm_logo` when the cover should carry both marks.

## 5. Known limits, for the docs agent to state or route

- **Epic stat band on a dark primary.** `compose.stat_band` sets brand numerals (accent-ink) on its default near-black
  band. On a dark primary that pair falls under 3:1 and the kit refuses the slide. The proof theme hit this:
  0B6E4F on 1A1A1A is 2.78:1. `scripts/example_epic.py --theme` then fails on its first slide.
  - Workaround in a deck: `stat_band(..., fill="accent")`, which sets on-accent numerals on a brand band.
  - `theme check` does not test this pair (it is not in `CONTRAST_PAIRS`), so a theme can pass and still refuse a
    stat band.
  - Fixing it in `compose.py` or `theme.py` is outside this task.
- `HOUSE_SERIES` pads the series with neutral slates (4B5960, 6B7983, A6A6A6, D9D9D9, 1E3C7D). The theme passes, but
  a chart with more series than the client gave colours shows house greys.
