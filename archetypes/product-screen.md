# Product screen

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a44 | f10 | ui-walkthrough | v1 |

## Use when
- The running product is the proof and one screen can carry the claim with a title and almost no other words.
- A demo hand-off needs a slide that stages the live product in a device or browser frame before switching to it.
- A tour of a few screens where the order of the screens is the story and each screen speaks for itself.

## Avoid when
- The point is a deliverable the product produced, a report, a table or a letter the reader must inspect: use output-capture (a45).
- The point is how the product is built, its parts and their connections: use solution-architecture (a21).
- The screen has to be explained step by step with payloads at each hop: use worked-example (a18).
- The data on the screen is the content and must be read cell by cell: rebuild it natively as reference-table (a33).

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 2% (2 to 3) | 1% (0 to 2) | 94% (93 to 97) | 8% (5 to 11) |
| screen-stage | 8% (0 to 11) | 12% (9 to 14) | 82% (78 to 99) | 82% (80 to 86) |
| window-chrome | 11% (11 to 11) | 11% (11 to 11) | 79% (79 to 79) | 5% (5 to 5) |
| color-band | 0% (0 to 0) | 36% (36 to 36) | 99% (99 to 99) | 26% (26 to 26) |
| demo-badge | 73% (73 to 73) | 36% (36 to 36) | 20% (20 to 20) | 26% (26 to 26) |

## Components
- One product capture fills the stage, a cropped screenshot, or a screenshot set inside a laptop or browser frame. Screenshots per slide 1 (0 to 3).
- An optional drawn browser bar with three window dots above the capture, so a mockup reads as running software.
- An optional full-width flat band behind a device mockup, with the device straddling it.
- An optional single pill naming the demo moment, set on the band or on the device.
- No captions, callouts or body text on the stage. Text shapes per slide 1 (1 to 2).

## Type roles
| Role | Size |
|---|---|
| title | 28 pt (21 to 32) |
| label | 21.25 pt (18.75 to 24), the demo pill word only |

## Density
Near empty of words, the screen does the talking. Content words per slide 3 (2 to 10), title words 3 (1 to 10). The capture takes the stage, 82% (80 to 86) of the canvas height.

## Word budget
Word budget 10 content words on this canvas, advisory floor 0, hard ceiling 250. The title claim carries nearly all of them, at most 14 words.

## Device notes
- A device or browser frame turns a raw screenshot into staged running software: a laptop body (d09-s029, d12-s028) or a drawn browser bar with window dots (d09-s029, d01-s074).
- A single pill marks the live demo moment and is the only label besides the title (d09-s029, d12-s028).
- Frameless captures run off the slide foot, cropped rather than shrunk, so the top of the screen stays legible (d13-s014, d10-s008).
- The title is a short label rather than a claim, title words 3 (1 to 10), which the house rule replaces.

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| other | The title is a label such as a product or demo name on 5 exemplars. | The title is one claim of at most 14 words on what the screen lets the user do, with up to 3 keywords in the brand color. | The title band holds one line and the stage below it keeps its full height. |
| 8pt-floor | Screen text inside a full-width capture renders far below the floor at slide scale on 2 exemplars. | Crop the capture to one region, the tiles and the first rows, and enlarge it until its smallest text clears 8 pt, or rebuild the key panel natively. | The stage shows part of the screen at reading size instead of the whole screen at thumbnail size. |
| left-accent | A short colored bar or corner block beside the title on 3 exemplars encodes no state. | Drop the bar and let the title stand alone on the light ground. | The title starts at the content margin with no inset for a bar. |
| no-footer | Page numbers, vendor marks, logo lockups and a confidentiality line sit at the foot on 3 exemplars. | Remove all foot chrome. | The capture may run to the bottom margin. |
| glyphs | An em dash joins the title parts and a double chevron stands in for an arrow in a button label on 2 exemplars. | Use a colon in the title and a plain word in the pill. | None for the layout. |
| flat-fill | A gradient edge bar and foot strip frame one exemplar, 1 in the top set. | Flat fills only, hairline frame with at most a 1 px shadow on the device or browser frame. | The frame reads from a hairline and the window bar, not from a colored border. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d01-s074 | greeked/d01/s074.png | A drawn browser bar turns a mockup capture into running software and the screen fills the stage. |
| d09-s029 | greeked/d09/s029.png | Laptop and browser window straddle a flat band with one pill naming the demo moment. |
| d10-s008 | greeked/d10/s008.png | One frameless product view with a pinned issue and its record card carries the proof without captions. |
| d13-s014 | greeked/d13/s014.png | A cropped app capture, headline tiles over a status table, shows the screen instead of describing it. |
| d12-s028 | greeked/d12/s028.png | A plain laptop frame and one launch pill stage the hand-off to a live demo. |

## Anti-exemplars
None.

## Variants
- Browser-framed full width: a drawn window bar over one capture that spans the stage (d01-s074).
- Device on a band: a laptop and an overlapping window straddle a flat band, a pill on the band (d09-s029).
- Plain device hand-off: one laptop frame centered under the title with a launch pill on its screen (d12-s028).
- Frameless crop: the capture runs off the slide foot, cropped to the tiles and the first rows (d13-s014, d10-s008).

## Devices used
dv56

## Provenance
- Source: cards/src/a44.json sha256 752fb60b5463ee772ffdb7dc62008f92ad3512bd78d9ba391002498e333a080c
- Measures: measures/a44.json sha256 9af75dfa7ad2bcde47bac57d1d2d195ebcc03553ba0f55171d6dff3ae758fdd5
- Final ranking: rankings/a44.final.json sha256 b9d9991b09408a29ca3beff37bac6564262cb05d75c2a0bb5064c248cdbd167a
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
