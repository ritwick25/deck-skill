# D · DL44 — operation columns with input and output wells (catalogue, variant io-wells)

Source: library slide d18-s008, lifted with `scripts/lift_device.py d18-s008 DL44`, finished by
`devices/work/DL44/build.py` (deterministic; `--out PATH` copies the result). Closes the review finding that
catalogue had no device showing what each entry takes and returns.

## What it is
- Three equal columns, one per operation. Each opens on a solid brand header (white numbered roundel, verb,
  white glyph), then one bold purpose line, a light `card` input well (label plus three lines), a near-black
  `ink-deep` output well of three glyph rows (name plus one line), a hairline, and a bold accent-ink line naming
  the one thing the operation never does.
- No outer card round each column, so no card-in-card nesting; the wells are the device.
- Family Parallel columns, archetype catalogue only (input-process-output is Directed sequence).

## Slots (device.json)
- `slot.title` (14 words).
- Per column i = 1..3: `slot.op.i.num` (1 word, on paper), `slot.op.i.verb` (1 word, on accent),
  `slot.op.i.icon` (glyph, on accent), `slot.op.i.purpose` (8), `slot.op.i.in.label` (1),
  `slot.op.i.in.text` (18, three paragraphs), `slot.op.i.out.label` (1, on ink-deep),
  `slot.op.i.out.1..3` (7 each: bold name paragraph plus one line, on ink-deep),
  `slot.op.i.out.1..3.icon` (glyph, accent-bright on ink-deep), `slot.op.i.never` (4).
- Structure: `struct.op.i.head`, `.disc`, `.in`, `.out`, `.rule`.
- capacity_words 179 against the catalogue floor 150 (not short). Sample copy: a fictional invoice-matching
  service (Match, Explain, Post).

## House rules it holds
- Title at the kit wide title geometry (0.50, 0.13, 12.40 x 0.40in, 21pt, one line, two-tone).
- Kicker, accent bar under the title, page number and the band sentence under the title removed (P09).
- Never line kept to four words: a five-word version tripped P09's foot-sentence rule.
- Ruling 12: solid brand headers, near-black output panels; the only tint is `card` on the input wells.
- Every rounded box at the canvas radius 0.05in. Inside the content band 0.50 to 12.90in. No stats.
- The 14 removed pictures became glyphs: one per header, one per output row (the vendor mark became nothing).
- Gates: all 27 implemented pass on device.pptx. Rendered and read under sigmoid and neutral.

## Finding for A1 (theme) and B (gates), not acted on
`accent-bright` is solved per theme (sigmoid lumMod 50000 lumOff 50000; neutral differs), so a theme swap by
`apply_theme` leaves the sigmoid recipe in place and P16 fails it on the neutral cut as "not a theme role". Every
device using it (DL32, DL38, DL39, DL40, DL44, DL45) is affected; placement or `apply_theme` must re-resolve it.
