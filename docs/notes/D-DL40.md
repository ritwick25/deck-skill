# D-DL40: scale band over workforce ring and footprint (credentials)

Source d01-s005, lifted by `scripts/lift_device.py d01-s005 DL40`, finished by `devices/work/DL40/build.py`.
Archetypes: credentials, headline-figures. Family: Numbers-led. Variant `scale-band-ring-footprint`.
Capacity 138 words (floors: credentials 90, headline-figures 110; neither is short).

## What it draws
- Title at the kit title geometry (0.50, 0.13, 12.40 x 0.40in, 21pt, one line, two-tone).
- `slot.basis`: the one shared basis label, "Illustrative figures", 9pt ink-muted, top right above the band (P23).
- Solid brand band (`struct.band`, accent) with five glyph-led stats `slot.band.1..5` (+ `.icon`), dashed dividers.
- Left zone "Depth by discipline": a native ring of four `blockArc` arcs (`struct.ring.1..4`: accent-deep,
  ink-strong, rule-strong, accent) whose sweeps are drawn from the figures in the build; a paper disc
  `struct.ring.hole` so the total reads on paper (P25); `slot.ring.total` in the hole and `slot.ring.1..4` beside
  their arcs. The source's chart picture is replaced by the ring.
- Near-black panel `struct.panel` (ink-deep, no outline) with four stacked stats `slot.panel.1..4`, numerals in
  accent-bright (ruling 12).
- Right zone "Delivery footprint": three columns, each glyph, head, stat, one body line (`slot.foot.N.*`).
  The source's map picture and its place names are gone; the columns are delivery models, not places.
- Foot strip: `slot.partners.head` plus six partner slots, `slot.partner.N.icon` (a glyph in the device) and
  `slot.partner.N.label`. The source's partner logos become these glyph slots; its client logo is gone.

## How a builder uses it
    devices.place(prs, "DL40", {
        "slot.title": "...",
        "slot.band.1": ["55+", "Regulated clients"],          # a stat slot takes [value, label]
        "slot.partner.1.icon": "vendor:aws/aws",              # a partner slot takes a vendor: key
        "slot.partner.1.label": "Cloud platforms", ...}, theme=th, archetype="credentials")
- Smoke-tested in scratch against a one-device library: place with vendor:aws/aws, azure/azure, gcp/gcp works.
- The stats are prims.stat groups, kind illustrative, basis=False. If the builder fills them with delivered or
  measured facts (the credentials card asks for the firm's own facts, CLAUDE.md §5 approved claims), change or
  remove `slot.basis` to match. The ring sweeps are geometry from the sample figures. A builder who changes the
  four discipline figures must redraw the arcs, or the ring misstates the split.

## House rules held
- Every shape is slot.* or struct.*. Nothing goes past 0.50 to 12.90in (P03). No small tint container (P16):
  the source's pastel side panel became the near-black panel. Flat fills, no footer, no subtitle, 9pt minimum type.
- Gates: 27 of 27 implemented gates pass on device.pptx. P04 has advisory notes only.
- Rendered under sigmoid and neutral (`render/device`, `render/device-neutral`), and both renders read.

## Requests for other tracks
- D-assemble: add DL40 to the library. The source's accent underline bars under the region heads were dropped,
  because prims refuses an accent strip.
- Whoever owns devices.place: the ring arcs do not follow the slot values. A `charts.ring` or a
  `ring_sweeps` hook would let place() redraw them.
