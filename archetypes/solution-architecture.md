# Solution architecture

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a21 | f04 | layers | v1 |

## Use when
- The solution must show where each component runs, with sources outside one edge, consumers outside the other and a shared platform beneath, so every boundary crossing reads as a decision.
- The audience is a technical evaluator who needs to see the drawn boundary of what is new against what already exists.

## Avoid when
- The argument is a dependency stack of full-width layers with no boundary. Use layered-architecture instead.
- One request is traced end to end with literal payloads at every hop. Use worked-example instead.
- The tiers are forums or decision rights rather than components. Use governance-model instead.

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 3% (1 to 18) | 2% (1 to 6) | 93% (81 to 97) | 6% (6 to 7) |
| sources | 2% (1 to 3) | 14% (9 to 30) | 13% (9 to 19) | 73% (42 to 90) |
| core | 15% (3 to 23) | 14% (9 to 30) | 74% (54 to 94) | 67% (42 to 78) |
| consumers | 82% (71 to 89) | 21% (9 to 30) | 16% (8 to 28) | 45% (39 to 89) |
| side-panel | 42% (3 to 80) | 77% (74 to 79) | 55% (16 to 94) | 12% (8 to 16) |
| platform-band | 14% (3 to 21) | 82% (75 to 88) | 77% (50 to 93) | 14% (6 to 16) |
| legend | 3% (3 to 3) | 95% (95 to 95) | 89% (89 to 89) | 2% (2 to 2) |

## Components
- Tab-headed zones, lanes or stage columns inside the core, 5 (2 to 6) items in the dominant repeat, each a hairline card holding service marks or named steps.
- Connectors 9 (0 to 12) per slide, each leaving a box and landing on a box, styled by connection type when a key is present.
- Icons 32 (14 to 45) per slide, one consistent glyph family with a plain role label, or on the technical-service-icons variant the official cloud service icon family with the service name under each icon.

## Type roles
| Role | Size |
|---|---|
| title | 27.25 pt (17.25 to 32) |
| card-heading | 10.25 pt (8.75 to 11) |
| label | 8.75 pt (7 to 11) |
| section-label | 11.75 pt (8.25 to 13) |

## Density
Content words 162 (67 to 180) across 6 top exemplars, with 64 (36 to 75) text shapes per slide.

## Word budget
Budget 180 words normalized and 170 on the w10 canvas, advisory floor 140, under the ceiling of 250.

## Device notes
- Sources stand in a column outside the left edge of the core and consumers outside the right edge, so the flow reads left to right across the boundary.
- Every zone inside the core carries a filled header tab or bar naming the zone, with its service cards or icons hanging below it.
- A shared platform, tooling or governance band spans the full width beneath the core, holding what every zone depends on.
- The core reads as one bounded field, a drawn panel or a row of regions capped by a shared band, so what sits inside reads as the solution and what sits outside reads as existing estate.
- Connectors carry meaning on the line itself, a short verb or payload name between tiles or a dash style named in a one-line key.

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| 8pt-floor | Service captions, step labels, arrow labels or tile names render below the floor on 6 top exemplars. | Every run at 8 pt or above. | Type is raised to the floor first. Each layer region then keeps only the tiles that fit at that size and closes with a +N more chip counted against the full set, with the region measured with the chip in place. |
| other | A label title naming the client, vendor logos on glass, words broken inside narrow tiles or half-empty agent cards and regions appear on 6 top exemplars. | A title of one claim in at most 14 words with up to 3 keywords in the brand color, one neutral icon family with capability labels in place of logos except the official cloud service icons on the technical-service-icons variant, no word broken inside a tile, and every card sized to its content. | A tile widens until its longest word fits on one line or the name moves to a shorter form, and a card with spare rows shrinks to its content or the row takes fewer, wider cards so no card sits half empty. |
| no-subtitle | A line or column subheads sit under the title on 4 top exemplars. | No subtitle under the title. | Fold the point into the one-claim title and fold column subheads into their header tabs. |
| shadow | A soft blurred shadow lifts cards, tiles, a target panel or a banner on 4 top exemplars. | Hairlines with at most a 1 px shadow. | Replace the shadow with a hairline outline matching the core frame. |
| left-accent | A colored edge bar beside the title or a region decorates the slide on 3 top exemplars. | A colored left or top accent bar only where it encodes a changeable state. | Drop the edge bar, and the sources column moves flush to the left margin. |
| no-footer | A confidentiality line, client wordmark, folio or foot takeaway band appears on 3 top exemplars. | No footer, page number, confidentiality line or foot summary band. | The platform band becomes the lowest element, and a takeaway moves into the title or the speaker notes. |
| glyphs | Em dashes or curly apostrophes appear in titles, tiles or legends on 2 top exemplars. | No em dash, en dash or arrow glyph in text. | Use a colon in labels and straight apostrophes, and draw arrows as connector shapes only. |
| emoji | An emoji stands in for an icon on 1 top exemplar. | Icons drawn as one SVG family, never emoji. | Replace the emoji with a glyph from the slide icon family at the same tile size. |
| word-budget | Tool lists and explanatory notes push content words over the budget on 1 top exemplar. | Per-archetype word budget under the ceiling of 250. | Move explanatory notes into the speaker notes and keep only labels and connector names on glass. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d19-s002 | greeked/d19/s002.png | Pinned by ruling for the technical-service-icons variant. Official cloud service icons in tab-headed layer regions, an external sources rail and an experience rail around a platform band. |
| d19-s004 | greeked/d19/s004.png | Pinned by ruling for the technical-service-icons variant. A dark shared data band caps one row of tab-headed regions, icons float over their names, a platform band closes the foot. |
| d06-s002 | greeked/d06/s002.png | tab-headed cards joined by arrows that name their payload, a source column and an operations band |
| d04-s016 | greeked/d04/s016.png | bounded platform of headed stage columns in flow order, sources outside left, consumers outside right, tooling strip beneath |
| d13-s048 | greeked/d13/s048.png | lanes under header tabs run source to experience over one platform band, each cross-system flow a dashed line named in a one-line key |
| d03-s038 | greeked/d03/s038.png | headed columns flow from sources through a central platform to analytics, and a legacy strip ends in a dashed arrow on a retire mark |

## Anti-exemplars
| Slide | View | Failure |
|---|---|---|
| d19-s003 | greeked/d19/s003.png | A draft with no title, an image in place of live text, type far under the floor, labels colliding with icons and most panel area empty. |
| d01-s059 | greeked/d01/s059.png | Most labels sit far below the floor and every column is packed to its edge, so the boundary drawing reads as a spec sheet. |

## Variants
- technical-service-icons: official cloud service icons over the service name inside tab-headed layer regions, an external sources rail at left and an experience rail at right around a full-width platform band, shown by d19-s002, with d19-s004 as its floating-icon form.
- Headed stage columns in flow order inside a bounded platform, shown by d04-s016.
- Tab-headed cards linked by payload-named arrows, shown by d06-s002.
- Lanes under header tabs with dashed cross-system loops named in a key, shown by d13-s048.
- Column flow that ends in a legacy strip retired by a dashed arrow, shown by d03-s038.

## Devices used
dv06, dv08, dv09, dv11

## Provenance
- Source: cards/src/a21.json sha256 7f5a31f5679f968a87bac01fab616a5c91941efb6df8e75ffbc4a00cdec048b7
- Measures: measures/a21.json sha256 a167b1537e7e6c590542b2b0f884615f81d3ed4e4c89f1700131640047d44174
- Final ranking: rankings/a21.final.json sha256 7f3e5c6d86957b11c647423362833e4ab06aba5d6624e8fa65095eb04aa30e63
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
