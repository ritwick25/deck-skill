# Gap analysis

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a25 | f05 | compare | v1 |

## Use when
- The proposal fills a gap, and the audience must see what exists or what shows set against what is missing or hidden in two opposed zones.
- Visible symptoms need to be traced to the capability gaps beneath them, or each missing practice to the failures its absence causes.

## Avoid when
- The slide lists pains with no opposing zone of what exists; use problem-framing instead.
- The slide draws one subject today and in its target form; use from-to-shift instead.
- Capabilities are graded cell by cell across owners or phases; use coverage-matrix instead.
- Readiness is graded on ordered levels; use maturity-model instead.

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 2% (1 to 4) | 4% (3 to 4) | 92% (63 to 92) | 10% (5 to 11) |
| zone-headers | 4% (1 to 6) | 18% (16 to 21) | 48% (6 to 90) | 39% (4 to 74) |
| exists | 4% (3 to 9) | 19% (11 to 21) | 61% (37 to 94) | 50% (34 to 74) |
| divider | 4% (3 to 4) | 46% (19 to 73) | 67% (40 to 94) | 41% (2 to 79) |
| gaps | 3% (0 to 45) | 54% (21 to 77) | 94% (50 to 100) | 46% (20 to 77) |
| coverage-rail | 75% (75 to 75) | 5% (5 to 5) | 25% (25 to 25) | 93% (93 to 93) |

## Components
- Paired blocks, 5 (4 to 6) items in the dominant repeat, each heading what exists in one zone and what is missing in the other.
- Connectors 0 (0 to 8) per slide, so position across the divider carries the relation rather than lines.
- Icons 8 (5 to 10) per slide, one line glyph or icon disc heading each block in one family.

## Type roles
| Role | Size |
|---|---|
| title | 24 pt (21.25 to 27) |
| section-label | 10 pt (9.25 to 12) |
| card-heading | 12 pt (11 to 12) |
| label | 9.75 pt (8 to 11.25) |
| body | 8 pt (8 to 9) |

## Density
Content words 253 (143 to 413) across 3 top exemplars, with 30 (18 to 43) text shapes per slide.

## Word budget
Budget 250 words normalized and 250 on the w10 canvas, advisory floor 190, under the ceiling of 250.

## Device notes
- A labelled divider splits the two zones, a spine with a rotated label, a label row between tiers or a waterline, so the opposition reads before any block.
- Each block opens with an icon disc or line glyph and a bold heading, then a short list or one claim line beneath.
- Blocks above and below the divider sit in the same columns, so each strength or symptom lines up with the gap or failure that belongs to it.

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| flat-fill | A gradient claim banner, gradient pill headers or a gradient rail header appear on 3 top exemplars. | Flat fills, no gradients. | Zone headers take one flat brand fill or become a caps label over a hairline. |
| 8pt-floor | Example bullets and failure lines render below the floor on 2 top exemplars. | Type at or above 8 pt everywhere. | Keep two examples or failures per block so every run clears the floor. |
| glyphs | A leading ellipsis and dashes inside failure or rail lines appear on 2 top exemplars. | No em dash, en dash, arrow glyph or ellipsis in text. | Join clauses with commas or split them into two short lines. |
| left-accent | Decorative left bars on panels and cards or a short rule under the title appear on 2 top exemplars. | A colored left or top accent bar only where it encodes a changeable state. | Remove the bars, and separate the two tiers with the divider and hairlines. |
| other | A topic label stands in for the title, a raster illustration sits among flat icons and dashed leaders stop short of their blocks on 2 top exemplars. | A title of one claim in at most 14 words, flat vector imagery, and every leader originating on one shape and landing on another. | Restate the title as the gap, redraw any illustration as a flat two-tone shape and land every leader on its block. |
| word-budget | Example lists and failure lines push content words to or past the ceiling on 2 top exemplars. | Per-archetype word budget under the ceiling of 250. | Cut failure and example lines to short noun phrases with the same count per block. |
| no-subtitle | A two-sentence claim banner sits under the title on 1 top exemplar. | No subtitle under the title. | Fold the banner point into a title of one claim and give the height to the blocks. |
| first-person | An italic aside speaks in the first person on 1 top exemplar. | No first or second person. | Drop the aside or restate it in the third person. |
| no-footer | A page number and a vendor mark sit at the foot on 1 top exemplar. | No footer, page number, confidentiality line or foot summary band. | Remove them, and the gap rows run to the bottom margin. |
| shadow | Blurred shadows lift every estate card and gap row on 1 top exemplar. | Hairlines with at most a 1 px shadow. | Keep the hairline outlines and drop the effects. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d16-s013 | refs/views/d16-s013.jpg | practice pillars each standing over a card of the failures its absence causes, split by one label row |
| d18-s003 | refs/views/d18-s003.jpg | as-built cards with identical field pairs facing icon-led rows of what is missing, split by a labelled spine |
| d16-s016 | refs/views/d16-s016.jpg | an iceberg split by a waterline, visible problems above and capability gaps below, with a rail sorting served from underserved |

## Anti-exemplars
None.

## Variants
- Pillars over failure cards, shown by d16-s013.
- As-built cards facing gap rows across a spine, shown by d18-s003.
- Waterline split with a coverage rail, shown by d16-s016.

## Devices used
dv47, dv06

## Provenance
- Source: cards/src/a25.json sha256 d4920692beab6bad530ce040b237549137ed9d53ff12e93b62639dd66ccd47f2
- Measures: measures/a25.json sha256 57717455f574906d9951400eb5a5c4ce0304eb77b89e2c77551b7a20e4b2e248
- Final ranking: rankings/a25.final.json sha256 0aff5a411c4f368d8d75b8330907ed5ddad76ef5149fe6c0b7cd52049fdcd647
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
