# Track D-assemble: the device library, 45 devices

## What was built
- `devices/devices.pptx`, `devices/devices.json`, `devices/renders/<id>-{sigmoid,neutral}.png` (90 renders) and
  `references/device-library.md`, all written by `scripts/assemble_devices.py` from `devices/work/DL01..DL45`.
- Assembler: exit 0. Library gates: 9 pass, 0 fail (P01 P03 P11 P12 P16 P17 P18 P22 P25).
- `references/device-library.md` lists all 45 with archetypes, advisory floor, slots, word capacity and mechanism.
  It is generated: edit a device's `device.json`, not the table.
- Every render read: DL32 to DL45 under sigmoid and neutral.

## Fixes made in device folders (the task allowed build.py; device.json changed with it)
- **DL42**: its 18 fixed vendor pictures failed P22 ("alt records no key") and P18 (dHash match against the
  corpus) once assembled. Cause: `clone.copy_shapes` under `DEVICE_STRIP` drops every cNvPr `descr`, including
  the kit's own `(vendor mark <key>)` record. The marks are now 18 glyph slots, `slot.platforms.mark.1..18`, using
  DL40's convention: kind glyph, alt "takes a vendor: mark key". The library shows kit glyphs. A builder fills
  `vendor:aws/aws` and so on, and `devices.place` draws each mark fresh with its alt record. The build.py comments
  record which key each slot was drawn for.
- **DL32 cover, DL34 section divider, DL35 closing**: `fit_band` sets any shape named `slot.title` to the content
  title band (x 0.50, w 12.40), so each hero title spread under the brand field, the ghost numeral or the promise
  panel. `devices.place` also snaps a title-kind slot to the 21pt one-line band. The hero title is now
  `slot.headline`, kind text (purpose cover-title, section-title or closing-title). Pass kit Paras built from
  `txt.title_runs(text, keywords)` to keep the two-tone. P14 reads cover-like titles visually, so no gate depends
  on the name.

## How a builder uses it
    s = devices.place(prs, "DL42", {"slot.title": ("Five reasons ...", ("Five reasons",)),
                                    "slot.platforms.mark.1": "vendor:aws/aws", ...},
                      theme=th, archetype="why-us")
- When a device serves more than one archetype, pass `archetype=`. A slot whose value is None is removed.
- `find.py <archetype>` lists the devices and their renders. A cover, divider or closing device takes
  `slot.headline`, not `slot.title`.

## Requests to other tracks (not edited here)
- **C (clone.py)**: under `alt_text` stripping, keep a `descr` on a picture named `vendor.<key>` or `mark.<key>`
  when `icons.vendor_key_of` or `mark_key_of` accepts the pair. That text is the kit's own record, not reference
  text. A dry run with this patch (scratch, no file changed) assembled the original DL42 with 9 of 9 gates
  passing. Without it, a fixed mark in any device or cloned slide fails P22 and P18.
- **D0 (assemble_devices.py)**: `fit_band` should widen `slot.title` only when it sits in the title band
  (top under 0.6in), so the next hero-title device does not repeat the DL32 defect.
- **owner of tests/test_devices.py (unowned)**: three tests fail because `devices.place` now requires
  `archetype=` for multi-archetype devices (A1's contract). Pass `archetype=self.e["archetypes"][0]` at lines 44,
  53 and 93, and `archetype=e["archetypes"][0]` at line 86. With that change, all 4 tests pass and all 45 devices
  place with plain fills (run from a scratch copy).
- **Content to review before use** (P19 forces replacement): DL40 has the sample "twelve years of enterprise
  delivery", and DL40 and DL41 carry sample headcounts and revenue ($90M, $400M, 1,500+). These are labelled
  illustrative, but they read like firm facts.
