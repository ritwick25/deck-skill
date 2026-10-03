# Solution architecture

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a21 | f04 | layers | v1 |

## Use when
- The solution must show where each component runs, with sources outside one edge, consumers outside the other and a shared platform beneath, so every boundary crossing reads as a decision.
- The audience is a technical evaluator who needs to see the drawn boundary of what is new against what already exists.

## Avoid when
- The argument is a dependency stack of full-width layers with no boundary; use layered-architecture instead.
- One request is traced end to end with literal payloads at every hop; use worked-example instead.
- The tiers are forums or decision rights rather than components; use governance-model instead.

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 3% (2 to 4) | 3% (2 to 6) | 94% (91 to 95) | 6% (5 to 10) |
| sources | 3% (2 to 4) | 18% (16 to 68) | 12% (9 to 18) | 57% (23 to 80) |
| core | 16% (4 to 23) | 18% (15 to 27) | 69% (52 to 75) | 57% (41 to 71) |
| consumers | 76% (4 to 87) | 21% (10 to 37) | 19% (11 to 93) | 42% (15 to 48) |
| side-panel | 30% (4 to 57) | 25% (18 to 31) | 55% (18 to 93) | 34% (7 to 60) |
| platform-band | 14% (3 to 22) | 75% (69 to 82) | 71% (50 to 93) | 14% (10 to 22) |
| legend | 4% (4 to 4) | 75% (75 to 75) | 44% (44 to 44) | 6% (6 to 6) |

## Components
- Tab-headed zones, lanes or stage columns inside the core, 4 (2 to 5) items in the dominant repeat, each a hairline card holding service marks or named steps.
- Connectors 12 (9 to 15) per slide, each leaving a box and landing on a box, styled by connection type when a key is present.
- Icons 35 (17 to 36) per slide, one consistent glyph family with a plain role label, never a vendor logo on glass.

## Type roles
| Role | Size |
|---|---|
| title | 28 pt (21 to 32) |
| card-heading | 11 pt (7 to 11) |
| label | 7.5 pt (6 to 11) |
| section-label | 10 pt (8.25 to 13) |

## Density
Content words 135 (67 to 287) across 5 top exemplars, with 55 (36 to 70) text shapes per slide.

## Word budget
Budget 200 words normalized and 140 on the w10 canvas, advisory floor 90, under the ceiling of 250.

## Device notes
- Sources stand in a column outside the left edge of the core and consumers outside the right edge, so the flow reads left to right across the boundary.
- Every zone inside the core carries a filled header tab or bar naming the zone, with its service cards hanging below it.
- A shared platform, tooling or governance band spans the full width beneath the core, holding what every zone depends on.
- The core is drawn as a single bounded panel, dashed on some exemplars, so what sits inside it reads as the solution and what sits outside reads as existing estate.

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| 8pt-floor | Step labels, captions, arrow labels or telemetry chips render below the floor on 5 top exemplars. | Every run at 8 pt or above. | Cut each service card to one noun phrase and drop under-lane captions, or widen the core by trimming the side panels. |
| no-subtitle | A line or column subheads sit under the title on 3 top exemplars. | No subtitle under the title. | Fold the point into the one-claim title and fold column subheads into their header tabs. |
| no-footer | A confidentiality line, client wordmark, folio or foot takeaway band appears on 3 top exemplars. | No footer, page number, confidentiality line or foot summary band. | The platform band becomes the lowest element, and a takeaway moves into the title or the speaker notes. |
| shadow | A soft blurred shadow lifts a target panel, banner or pill on 2 top exemplars. | Hairlines with at most a 1 px shadow. | Replace the shadow with a hairline outline matching the core frame. |
| flat-fill | A takeaway band or edge bar carries a gradient on 2 top exemplars. | Flat fills, no gradients. | Fill any surviving band with one flat pale tint and remove decorative gradient bars outright. |
| glyphs | Em dashes, en dashes or curly apostrophes appear in tiles and legends on 2 top exemplars. | No em dash, en dash or arrow glyph in text. | Use a colon in labels and straight apostrophes, and draw arrows as connector shapes only. |
| left-accent | A gradient left edge bar decorates the slide on 1 top exemplar. | A colored left or top accent bar only where it encodes a changeable state. | Drop the edge bar, and the sources column moves flush to the left margin. |
| word-budget | Source notes and binding notes push content words over the budget on 1 top exemplar. | Per-archetype word budget under the ceiling of 250. | Move explanatory notes into the speaker notes and keep only labels and connector names on glass. |
| other | A label title naming the client or vendor logos on glass appear on 4 top exemplars. | A title of one claim in at most 14 words with up to 3 keywords in the brand color, and one neutral icon family with capability labels in place of logos. | Service cards trade logos for glyph plus role label, which needs a uniform card width on a grid. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d08-s007 | greeked/d08/s007.png | header-barred estate panels placed left to right, connection types coded by line style with a key, a governance strip under all |
| d04-s016 | greeked/d04/s016.png | bounded platform of headed stage columns in flow order, sources outside left, consumers outside right, tooling strip beneath |
| d06-s002 | greeked/d06/s002.png | tab-headed cards joined by arrows that name their payload, a source column and an operations band |
| d03-s026 | greeked/d03/s026.png | one framework panel with a gray lane per source, a target panel and capability strips beneath |
| d01-s050 | greeked/d01/s050.png | dashed boundary around a five-stage agent pipeline under a capability banner, fed by headed side panels |

## Anti-exemplars
None.

## Variants
- Estate panels with a connector key, shown by d08-s007.
- Headed stage columns in flow order inside a bounded platform, shown by d04-s016.
- Tab-headed cards linked by payload-named arrows, shown by d06-s002.
- One lane per source inside a single framework panel, shown by d03-s026.
- Disc pipeline in a dashed boundary with side panels, shown by d01-s050.

## Devices used
dv06, dv08, dv09, dv11

## Provenance
- Source: cards/src/a21.json sha256 1375dceb2e39e6a5dc61846849c0f9f9c1329c163edc549d12615a11fd432a7c
- Measures: measures/a21.json sha256 11e44bd5b7cd5002cd459e1d5eeb635c02f0b990a2e7cc92c94cd9d41b035d1b
- Final ranking: rankings/a21.final.json sha256 0d666a661980d5d8287df71ffd76ac7f5fd0f8b1b1e0dfa19340c327f0fd8b5a
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
