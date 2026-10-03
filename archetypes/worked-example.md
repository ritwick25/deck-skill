# Worked example

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a18 | f03 | claim-proof | v1 |

## Use when
- A technical reader must be able to check the mechanism on one named instance, a record, a case or an input, with the literal values it carries at each hop.
- The proof needs a failure as well as a success, such as an exception row, a flagged field or a held record, so the trace reads as evidence rather than a brochure.

## Avoid when
- The steps are described in labels with no instance or values, so use process-flow instead.
- The slide is a framed product screen with no trace through it, so use product-screen instead.
- The point is which actor acts at each stage and where control passes, so use swimlane-handoff instead.
- The story is one engagement and its business result rather than one record through the system, so use case-study instead.

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 4% (1 to 4) | 4% (2 to 6) | 94% (92 to 97) | 5% (4 to 11) |
| case-anchor | 4% (4 to 50) | 19% (15 to 54) | 31% (13 to 45) | 54% (35 to 68) |
| trace | 11% (4 to 18) | 19% (17 to 22) | 86% (80 to 92) | 43% (30 to 56) |
| payload | 19% (4 to 35) | 37% (20 to 54) | 43% (40 to 45) | 46% (35 to 56) |
| outcome | 24% (4 to 43) | 56% (38 to 74) | 72% (51 to 94) | 31% (17 to 45) |
| context-rail | 77% (77 to 77) | 20% (20 to 20) | 20% (20 to 20) | 47% (47 to 47) |

## Components
- Hop cards or stage columns in the dominant repeat, 3 (2 to 6) per slide, each carrying the value the instance holds at that hop.
- Connectors 2 (0 to 6) per slide, short arrows or chevrons between hops, each starting on one card and landing on the next.
- Icons 5 (0 to 23) per slide, one line glyph per hop at most, never a third-party product mark.
- A payload well or field table holding the literal record, set in a monospaced or tabular face so ids and figures align.
- Numbered discs on each hop and, where the trace branches, a second numbered row for the exception path that loops back to the check it failed.

## Type roles
| Role | Size |
|---|---|
| title | 21 pt (17 to 27) |
| section-label | 8 pt (8 to 8) |
| card-heading | 10.75 pt (9 to 16.75) |
| body | 8.25 pt (8 to 12) |
| label | 8 pt (8 to 11.25) |
| numeral | 18.75 pt (8 to 20.25) |
| quote | 8 pt (8 to 8) |

## Density
Content words 251 (6 to 393) across 5 top exemplars, with 33 (1 to 67) text shapes per slide.

## Word budget
Budget 250 words normalized and 250 on the w13 canvas, advisory floor 210 on the w13 canvas, under the ceiling of 250.

## Device notes
- Each hop carries a number, as a column numeral or a disc on the card corner, so the trace can be followed and cited by step.
- The literal values sit in their own well or table, ids and figures in aligned columns, so the reader checks values rather than reads claims.
- One row or field is visibly marked as the outcome or the exception, a highlighted winner row or a tinted row flagged for a person, so the trace shows where judgement lands.
- A failure path is drawn beside the success path, a second numbered row or a set of low-confidence rows sent back for review, so the trace is not all green.

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| no-footer | A wordmark, confidentiality line, page number or owner strip appears on 4 top exemplars. | No footer, page number, confidentiality line or foot summary band. | The trace and payload take the reclaimed height, and owner and gate details move to the speaker notes. |
| no-subtitle | A lead line, strapline or list heading sits under the title on 4 top exemplars. | No subtitle under the title. | The line folds into the one-claim title or is cut where it restates the title, and the case anchor moves up. |
| 8pt-floor | Table cells, inset formulas and hop captions render below the floor on 2 top exemplars. | Every run at 8 pt or above. | Cut each hop to one value line, cut tables to the rows the claim needs, and move derivations to the speaker notes. |
| word-budget | Content words run over the budget on 4 top exemplars, with inset detail and rail prose as the excess. | Per-archetype word budget under the ceiling of 250. | Keep the literal values and cut the descriptive prose around them before shrinking type. |
| left-accent | Colored edge bars or ticks mark the title or rail headings as decoration on 4 top exemplars. | A colored left or top accent bar only where it encodes a changeable state. | Remove the bars and carry a heading with a hairline above its label. |
| flat-fill | Discs, chips and edge bars carry gradients on 2 top exemplars. | Flat fills, no gradients. | Flat fills on discs and chips, and gradient edge bars removed since they carry no content. |
| light-bg | A dark comparison band closes the slide on 1 top exemplar. | Light slide grounds. | The band becomes a light surface with dark ink, separated from the trace by a hairline. |
| glyphs | Arrow glyphs, dashes and smart quotes appear in formulas and captions on 2 top exemplars. | No em dash, en dash or arrow glyph in text. | Write the word to in place of an arrow, commas in place of dashes, and drawn connectors between hops. |
| shadow | Soft outer shadows sit under cards and wells on 1 top exemplar. | Hairlines with at most a 1 px shadow. | Outline every card and well with a hairline and drop the shadow. |
| first-person | A rail heading speaks in the first person on 1 top exemplar. | No first or second person. | Rename the heading as a neutral noun, a quoted input keeps its own voice as a quotation. |
| other | A flattened raster body, a letterspaced kicker or a label title in place of a claim appears on 3 top exemplars. | Native editable shapes, no kicker, a title of one claim. | Rebuild the trace as native cards and connectors, drop the kicker, and hold the title to 14 words with up to 3 keywords in the brand color. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d01-s084 | greeked/d01/s084.png | four numbered stage columns, each with its own device carrying the instance's values, closed by a band contrasting the old method on one figure |
| d18-s016 | greeked/d18/s016.png | a copy chain proven by one named record whose source ids resolve to one key, with the stored entry shown as a code panel |
| d13-s011 | greeked/d13/s011.png | one named case run through a numbered regular row over a numbered exception row that loops back until the check agrees |
| d15-s024 | greeked/d15/s024.png | a verbatim input beside the field table it becomes, each row with a confidence bar and the uncertain rows flagged back to a person |
| d01-s076 | greeked/d01/s076.png | one lit cell in a reprinted scoping matrix anchors the case, and a ranked action list gives the responses with the first recommended |

## Anti-exemplars
None.

## Variants
- Numbered stage columns, a different device per column, over a contrast band, shown by d01-s084.
- Arrowed card chain over a payload pair of code panel and record card, shown by d18-s016.
- Regular row over exception row, both numbered, shown by d13-s011.
- Input record beside its extracted field table with confidence and flags, shown by d15-s024.
- Lit matrix cell beside a ranked action list, shown by d01-s076.

## Devices used
dv01, dv03, dv14, dv50, dv52, dv57

## Provenance
- Source: cards/src/a18.json sha256 f65e91960228fa033404670dee599c3f3c7b03843e6a9c6bf09a9c402806660d
- Measures: measures/a18.json sha256 3b37909ef13984c8b5a969bbb8a7dff579d741cbd94c5f264e2541dc459c3192
- Final ranking: rankings/a18.final.json sha256 0c0b531ca65d47eb80b5091014a26ae27c3a7715dcd7668f8826e36fdb5e84db
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
