# Layered architecture

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a20 | f04 | layers | v1 |

## Use when
- The platform must read as a dependency stack from sources up to consumers, with every component placed in exactly one layer.
- Cross-cutting concerns such as governance or a learning loop apply to every layer and need to sit beside the stack, not inside it.

## Avoid when
- Components sit in zones left to right inside a drawn trust boundary with sources and consumers outside its edges. Use solution-architecture instead.
- The tiers are forums, cadences or roles rather than platform layers. Use governance-model instead.
- One request must be traced hop by hop with real payloads. Use worked-example instead.

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 4% (3 to 4) | 2% (1 to 6) | 93% (91 to 94) | 9% (4 to 11) |
| top-band | 4% (3 to 4) | 18% (16 to 19) | 92% (91 to 94) | 5% (5 to 19) |
| layer-stack | 4% (3 to 15) | 24% (13 to 39) | 91% (64 to 94) | 56% (47 to 69) |
| source-band | 11% (4 to 17) | 79% (77 to 81) | 86% (80 to 92) | 18% (15 to 21) |
| left-rail | 4% (4 to 4) | 18% (18 to 18) | 11% (11 to 11) | 69% (69 to 69) |
| right-rail | 78% (70 to 86) | 16% (14 to 18) | 18% (11 to 26) | 66% (62 to 69) |

## Components
- Layer rows or bars stacked full width, each holding a repeat of hairline cards or chips, 5 (3 to 10) items in the dominant repeat.
- Connectors between layers, 0 (0 to 5) per slide, short and vertical, each landing on the layer above.
- Icons 16 (0 to 41) per slide, line glyphs inside cards or beside source chips, never a third-party product mark.

## Type roles
| Role | Size |
|---|---|
| title | 21 pt (18 to 28) |
| card-heading | 9 pt (8.75 to 13.25) |
| label | 8 pt (8 to 13.25) |
| section-label | 9 pt (8 to 13.25) |
| body | 8 pt (8 to 9) |

## Density
Content words 263 (100 to 325) across 5 top exemplars, with 75 (33 to 94) text shapes per slide.

## Word budget
Budget 250 words normalized and 100 on the w10 canvas, advisory floor 250, under the ceiling of 250.

## Device notes
- Between adjacent layers a short marker sits on the seam, an upward wedge, a verb pill or a caption naming what crosses, so dependency reads bottom up without a connector per card.
- Each layer opens with its name in a fixed tab or label column at the left, so every layer label aligns on one vertical and the components fill the row to its right.
- Cross-cutting concerns run either as full-height rails flanking the stack or as one strip spanning the stack's full width, so they read as touching every layer.
- The sources sit in a separate footing band under the lowest layer, drawn as a row of chips or cards rather than as a layer of their own.
- A tier opens with a full-width header bar naming it, and the tiers narrow from many consumer cards to fewer shared components, so reuse reads from the change in count.

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| no-footer | A confidentiality line, page number, corner logo or foot band appears on 5 top exemplars. | No footer, page number, confidentiality line or foot summary band. | The stack and its source band take the reclaimed height, and any foot claim moves into the title or the speaker notes. |
| left-accent | A colored edge bar marks the title or each layer row on 3 top exemplars. | A colored left or top accent bar only where it encodes a changeable state. | Layer identity moves to the fixed left label column and a hairline row edge, with any hue carried on the chips only. |
| no-subtitle | A lead sentence sits under the title on 3 top exemplars. | No subtitle under the title. | The lead sentence folds into the one-claim title or moves to the speaker notes, and the top band moves up. |
| word-budget | Content words run over the budget on 4 top exemplars, with mottos and rail items as the excess. | Per-archetype word budget under the ceiling of 250. | Cut layer mottos and shorten rail items before shrinking type. |
| flat-fill | A header bar or band carries a multi-stop gradient on 2 top exemplars. | Flat fills, no gradients. | Fill a header bar that carries a layer name with one flat tint, and remove any gradient band that carries no content. |
| shadow | A soft blurred shadow lifts cards or the framed layer on 1 top exemplar. | Hairlines with at most a 1 px shadow. | Replace the shadow with a hairline outline, and let the framed layer carry its boundary as a stroke. |
| glyphs | Dashes appear in titles or labels on 1 top exemplar. | No em dash, en dash or arrow glyph in text. | Replace a dash after a keyword with a colon and write any range with the word to. |
| first-person | The title speaks in the first person on 1 top exemplar. | No first or second person. | Restate the title as a third-person claim about the foundation. |
| other | Third-party product marks, faint colored text on white, navigation roundels or an overlong title appear on 5 top exemplars. | Category labels in place of product marks, ink text with a colored hairline, no navigation chrome, a title of at most 14 words with up to 3 keywords in the brand color. | Cards lose their logo row and gain label space, and the title band holds one line. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d15-s031 | refs/views/d15-s031.jpg | layer rows of chips each ending in the gaps it closes, framed by two full-height cross-cutting rails |
| d01-s056 | refs/views/d01-s056.jpg | tab-led layer bands of icon components with verb pills on the seams, beside a numbered trace that tags each step with the layer it touches |
| d18-s007 | refs/views/d18-s007.jpg | a framed proposed layer between a consumer row and a source row, with boundary captions naming what flows up and what never crosses |
| d09-s036 | refs/views/d09-s036.jpg | outlined layer bands bottom to top with a fixed left label column, centered upward wedges and a source band |
| d15-s032 | refs/views/d15-s032.jpg | three header-barred tiers narrowing from application cards to shared service chips to iconed tool columns |

## Anti-exemplars
| Slide | View | Failure |
|---|---|---|
| d01-s130 | refs/views/d01-s130.jpg | A strong tabbed stack whose principle band prints every line twice on top of itself, and an icon breaks the channels tab label. |
| d12-s042 | refs/views/d12-s042.jpg | A dark slide over the word ceiling, with text glyphs and emoji as icons, type below the floor and color rules as decoration. |
| d21-s010 | refs/views/d21-s010.jpg | Both panels under the spanning band are bullet lists of tool names with no icons, centered with empty upper bands. |

## Variants
- Layer rows between two full-height cross-cutting rails, shown by d15-s031.
- Tab-led layer bands beside a numbered trace that tags each step with its layer, shown by d01-s056.
- A framed proposed layer between a consumer row and a source row, with boundary captions, shown by d18-s007.
- Outlined bands with a fixed left label column and a persona header, shown by d09-s036.
- Three header-barred tiers narrowing from applications to shared services to tools, shown by d15-s032.

## Devices used
dv06, dv08, dv27

## Provenance
- Source: cards/src/a20.json sha256 c3e3ab5c23fcf27ea356add3c6fc974bcc01eac3e4659c4334ade73ede854703
- Measures: measures/a20.json sha256 69b06f0e88a4b8e329c26de65bae1afa5f91f755f8d625111f89398b1d08ed56
- Final ranking: rankings/a20.final.json sha256 fff1ce52f314e522f9b12b4abbf45ec0314c1f6df5e61cb93f49a4dffc931bd4
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
