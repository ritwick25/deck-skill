# D · DL37 — queue, gated dual track, compounding stack (engagement-model)

Source: library slide d01-s039, lifted with `scripts/lift_device.py d01-s039 DL37`, finished by
`devices/work/DL37/build.py` (deterministic; `--out PATH` copies the result).

## What it is
- Left: an intake queue ranked top to bottom. Two live requests are solid brand cards (head plus one line),
  four queued requests are dashed paper cards. A chevron and the word "Pull" hand the queue to the squad.
- Middle: one squad, two framed tracks (discovery, delivery), three step boxes each with a time box line,
  arrows between steps, and a vertical value-gate arrow from track 1 to track 2 with a shield glyph and label.
- Right: six solid brand layers widening toward the base (the shared assets each release leaves behind).
  The release arrow runs from the delivery frame and lands on the layer level with it.
- Variant `queue-gated-tracks-stack`, family Directed sequence, archetype engagement-model.

## Slots (device.json)
- `slot.title` (14 words), `slot.queue.label`, `slot.queue.live.1..2` (on accent, head + line),
  `slot.queue.next.1..4`, `slot.pull.label`.
- `slot.track.{1,2}.icon`, `.head`, `.step.{1..3}` (step name + time box, on card).
- `slot.gate.icon`, `slot.gate.label`, `slot.squad.note` (two lines).
- `slot.stack.icon`, `slot.stack.label`, `slot.stack.layer.1..6` (top is narrowest; on accent),
  `slot.stack.note` (two lines).
- capacity_words 154 against the engagement-model floor 140 (not short). Filled sample copy: 140 words.
- Structure: `struct.queue` (group), `struct.queue.rule.1..2`, `struct.pull.chevron.1`, `struct.track.{1,2}`,
  `struct.track.{1,2}.arrow.{1,2}`, `struct.gate.arrow`, `struct.release.arrow`.

## House rules it holds
- Title at the kit wide title geometry (0.50, 0.13, 12.40 x 0.40in, 21pt, one line, two-tone).
- Subtitle, dark foot summary band, top-right section pill and corner source line removed (P09, no footer).
- Ruling 12: solid brand cards and layers; step boxes are card (small tints remapped by `finish`).
- Every rounded box at the canvas radius 0.05in, including grouped children (scaled by ext/chExt).
- The source's free-standing growth axis was deleted: it landed on nothing (P06). Every arrow lands on a box.
- No stats, so no basis label. No pictures were in the source, so no marks were placed.
- Gates: all 27 implemented pass on device.pptx. The neutral cut (`device-neutral.pptx`, `apply_theme`)
  passes all but P21, which needs a manifest the derived file does not have (same as the other devices).

## Using it
Place through `devices.place` once D-assemble has folded DL37 into `devices/devices.pptx`. Keep queue items
to four words, step names to three words plus a short time box, layer names to three words. Long layer
names on the narrow top layers wrap and fail the fit check.
