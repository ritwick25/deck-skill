# Layered architecture

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a20 | f04 | layers | v1 |

## Use when
- The platform must read as a dependency stack from sources up to consumers, with every component placed in exactly one layer.
- Cross-cutting concerns such as governance or a learning loop apply to every layer and need to sit beside the stack, not inside it.

## Avoid when
- Components sit in zones left to right inside a drawn trust boundary with sources and consumers outside its edges; use solution-architecture instead.
- The tiers are forums, cadences or roles rather than platform layers; use governance-model instead.
- One request must be traced hop by hop with real payloads; use worked-example instead.

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 3% (1 to 4) | 2% (1 to 6) | 94% (93 to 97) | 9% (4 to 13) |
| top-band | 3% (3 to 28) | 17% (14 to 19) | 80% (44 to 95) | 21% (5 to 31) |
| layer-stack | 4% (3 to 27) | 24% (18 to 43) | 70% (46 to 95) | 56% (37 to 69) |
| source-band | 22% (17 to 27) | 79% (76 to 81) | 63% (46 to 80) | 11% (7 to 15) |
| left-rail | 3% (2 to 4) | 17% (17 to 18) | 17% (11 to 23) | 70% (69 to 70) |
| right-rail | 73% (71 to 86) | 17% (14 to 18) | 25% (11 to 26) | 70% (69 to 76) |
| outcome-band | 3% (3 to 3) | 76% (76 to 76) | 95% (95 to 95) | 15% (15 to 15) |

## Components
- Layer rows or bars stacked full width, each holding a repeat of hairline cards or chips, 4 (3 to 6) items in the dominant repeat.
- Connectors between layers, 5 (0 to 7) per slide, short and vertical, each landing on the layer above.
- Icons 6 (0 to 10) per slide, line glyphs inside cards or beside source chips, never a third-party product mark.

## Type roles
| Role | Size |
|---|---|
| title | 24 pt (18 to 28) |
| card-heading | 12 pt (8.75 to 13.25) |
| label | 8 pt (8 to 13.25) |
| section-label | 12 pt (8 to 13.25) |
| body | 10 pt (8 to 12) |

## Density
Content words 177 (100 to 263) across 5 top exemplars, with 36 (31 to 75) text shapes per slide.

## Word budget
Budget 200 words normalized and 190 on the w10 canvas, advisory floor 160, under the ceiling of 250.

## Device notes
- Short upward wedges or arrows sit centered on the seam between adjacent layers, so dependency reads bottom up without a connector per card.
- A fixed left column names each layer while the row to its right carries the components, so every layer label aligns on one vertical.
- Cross-cutting concerns run as full-height rails flanking the stack, each under its own header tab, so they read as touching every layer.
- The sources sit in a separate footing band under the lowest layer, drawn as a row of chips rather than as a layer of their own.

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| no-footer | A confidentiality line, page number, corner logo or foot band appears on 5 top exemplars. | No footer, page number, confidentiality line or foot summary band. | The stack and its outcome band take the reclaimed height, and any foot claim moves into the title or the speaker notes. |
| left-accent | A colored edge bar marks the title or each layer row on 3 top exemplars. | A colored left or top accent bar only where it encodes a changeable state. | Layer identity moves to the fixed left label column and a hairline row edge, with any hue carried on the chips only. |
| no-subtitle | A lead sentence sits under the title on 2 top exemplars. | No subtitle under the title. | The lead sentence folds into the one-claim title or moves to the speaker notes, and the top band moves up. |
| 8pt-floor | Chip, source and bullet labels render below the floor on 2 top exemplars. | Every run at 8 pt or above. | Raising the labels widens each chip, so group chips into fewer named families or cut each layer card to a short bullet list. |
| word-budget | Content words run over the budget on 2 top exemplars, with mottos and rail items as the excess. | Per-archetype word budget under the ceiling of 250. | Cut layer mottos and shorten rail items before shrinking type. |
| flat-fill | Edge and foot bars carry a multi-stop gradient on 1 top exemplar. | Flat fills, no gradients. | Remove the gradient bars rather than flattening them, since they carry no content. |
| glyphs | Dashes and en dash level ranges appear in labels on 1 top exemplar. | No em dash, en dash or arrow glyph in text. | Write ranges with the word to and replace a dash after a keyword with a colon. |
| first-person | The title speaks in the first person on 1 top exemplar. | No first or second person. | Restate the title as a third-person claim about the foundation. |
| other | Third-party product marks, faint colored text on white, navigation roundels or an overlong title appear on 5 top exemplars. | Category labels in place of product marks, ink text with a colored hairline, no navigation chrome, a title of at most 14 words with up to 3 keywords in the brand color. | Cards lose their logo row and gain label space, and the title band holds one line. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d12-s008 | greeked/d12/s008.png | foundation tiers between an agent chip canopy and a source footing, flanked by a benefit rail and a failure-mode rail |
| d09-s036 | greeked/d09/s036.png | outlined layer bands bottom to top with a fixed left label column, centered upward wedges and a source band |
| d15-s031 | greeked/d15/s031.png | layer rows of chips each ending in the gaps it closes, framed by two full-height cross-cutting rails |
| d01-s054 | greeked/d01/s054.png | consumption tiles over an agent plane and one foundation, beside a rising autonomy ladder rail |
| d07-s004 | greeked/d07/s004.png | existing systems bar over new decision layers with an explicit read and write-back verb line, value horizons below |

## Anti-exemplars
None.

## Variants
- Pyramid of foundation tiers between two card rails, shown by d12-s008.
- Outlined bands with a fixed left label column and a persona header, shown by d09-s036.
- Layer rows between two full-height cross-cutting rails, shown by d15-s031.
- Stack beside a staircase rail of maturity levels, shown by d01-s054.
- New layers under an existing systems bar with read and write-back verbs, shown by d07-s004.

## Devices used
dv06, dv08, dv27

## Provenance
- Source: cards/src/a20.json sha256 a998dabe4f8a1f86a318b7b59a0efe49faccae83e81563b427062fbceefe8d24
- Measures: measures/a20.json sha256 0ae898cebf228660f6a932b656ac665467ae1ba724db49e1c606ab7e00a42094
- Final ranking: rankings/a20.final.json sha256 ac73fad36a832306760490540a066eb2bce1610507f974f56e13f4038aa3b1ab
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
