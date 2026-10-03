# Deep dive with brief rail

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a27 | f05 | claim-proof | v1 |

## Use when
- One use case, method or mechanism needs a full page: a wide exhibit shows how it works and a brief states the problem, the approach and the decision it supports.
- A technical reader must see the mechanism itself, a waterfall, a chip grid resolving to agreed inputs, a pipeline with its failure lane, or a node graph, rather than a description of it.

## Avoid when
- The engagement is delivered and the page reports outcomes, so use case-study instead.
- The page must carry the whole proposal, ask, scope, figures and assumptions, so use executive-summary instead.
- The page fences what is in and out of the commitment, so use scope-and-assumptions instead.

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 4% (4 to 4) | 4% (1 to 6) | 93% (92 to 96) | 5% (4 to 11) |
| exhibit | 4% (4 to 9) | 20% (10 to 35) | 69% (41 to 92) | 63% (44 to 80) |
| brief | 58% (5 to 75) | 20% (11 to 65) | 22% (22 to 90) | 41% (13 to 81) |
| challenge-strip | 4% (4 to 4) | 10% (10 to 10) | 68% (68 to 68) | 18% (18 to 18) |
| value-strip | 4% (4 to 4) | 82% (82 to 82) | 68% (68 to 68) | 7% (7 to 7) |
| evidence-line | 4% (4 to 4) | 53% (20 to 86) | 93% (93 to 93) | 39% (6 to 72) |

## Components
- Exhibit cards or chips, 4 (2 to 5) items in the dominant repeat, inside one wide exhibit that carries its own header band.
- Connectors 6 (4 to 11) per slide, each leaving a step, node or chip and landing on the next.
- Icons 2 (0 to 12) per slide, in one line family, on the challenge and value strips and the step diagrams.
- A brief of short blocks, problem, why it matters, approach and decision supported, the last held in a hairline box.

## Type roles
| Role | Size |
|---|---|
| title | 21 pt (17.5 to 27) |
| section-label | 8 pt (8 to 15) |
| card-heading | 11 pt (9 to 13) |
| body | 9 pt (8 to 13) |
| label | 8.25 pt (8 to 11) |
| caption | 8 pt (8 to 11) |
| numeral | 14 pt (8 to 22.75) |

## Density
Content words 155 (89 to 310) across 5 top exemplars, with 39 (25 to 62) text shapes per slide, most of them short labels inside the exhibit.

## Word budget
Budget 250 words normalized and 250 on the w13 canvas, held at the ceiling because the top exemplars run long, advisory floor 120, under the ceiling of 250.

## Device notes
- The brief sits as a narrow right rail of stacked blocks headed problem, why it matters and approach, and where challenge and value bands frame the exhibit it closes on a boxed decision supported.
- Challenge, work and value read top to bottom as stacked bands, an iconned pain strip, a work band under a filled header bar, and an iconned outcome strip.
- The exhibit carries an illustrative tag at its header, so the drawn data reads as a planning picture rather than a measured result.
- Small blocks of the exhibit name the step or field in a bold label and hold one line of detail under it, so the mechanism reads without the brief.

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| no-footer | A confidentiality line, client wordmark, page number, owner strip or vendor mark appears on 5 top exemplars. | No footer, page number, confidentiality line or foot summary band. | Owner, gate and phase fields move to the speaker notes and the exhibit takes the freed height. |
| left-accent | A gradient left edge bar or colored rules over the brief columns decorate the slide on 4 top exemplars. | A colored left or top accent bar only where it encodes a changeable state. | A hairline above each brief heading carries the split, and a red mark stays only on the failed chip or the fail lane. |
| flat-fill | Gradient work banners, value labels, foot bands or an identity pill appear on 3 top exemplars. | Flat fills, no gradients. | The work banner and the identity pill take one flat brand fill. |
| word-budget | Brief blocks that restate the strips push content words to or over the budget on 3 top exemplars. | Per-archetype word budget under the ceiling of 250. | Each brief block holds one or two lines, and the brief keeps its lead and the decision box. |
| no-subtitle | An italic line sits under the title on 2 top exemplars. | No subtitle under the title. | The point folds into the one-claim title and the brief moves up. |
| first-person | A heading such as how we solve it, or a caveat addressed to the reader, appears on 2 top exemplars. | No first or second person. | The heading becomes approach and the caveat states a fact about the method. |
| glyphs | En dashes in ranges or curly apostrophes appear on 2 top exemplars. | No em dash, en dash or arrow glyph in text. | Ranges read with the word to, and apostrophes are straight. |
| shadow | A soft shadow lifts the graph container and the use case card on 1 top exemplar. | Hairlines with at most a 1 px shadow. | The container and the card keep a hairline outline only. |
| other | A letterspaced vendor kicker above the title, green check discs or engine identity carried by outline hue appear on 4 top exemplars. | No kicker above the title, accents from the brand set only, identity carried by a label, and a title of one claim in at most 14 words. | Agreed cells take a brand or navy check glyph, node outlines share one color and the node label names the engine. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d01-s015 | greeked/d01/s015.png | challenge strip, numbered chevron steps each with a small working diagram, a value strip and a brief rail closing on the decision supported |
| d15-s008 | greeked/d15/s008.png | a problem, why and approach triad over expected and received chip rows and a pipeline whose failure lane returns as numbered steps |
| d18-s026 | greeked/d18/s026.png | a node graph with named edges filling the page, an identity spine at its center and a use case card inside the frame |
| d01-s016 | greeked/d01/s016.png | a conflicting chip grid resolving across a chevron into one ticked column of agreed inputs, beside a brief rail |
| d15-s013 | greeked/d15/s013.png | a horizontal waterfall from base to total with signed driver bars, beside a problem, why and approach rail |

## Anti-exemplars
None.

## Variants
- Challenge, chevron steps and value bands beside a brief rail, shown by d01-s015.
- Triad row over a contract diff and a two-lane pipeline, shown by d15-s008.
- Full-page node graph with an inset use case card, shown by d18-s026.
- Chip grid converging on an agreed column beside a brief rail, shown by d01-s016.
- Waterfall card beside a brief rail, shown by d15-s013.

## Devices used
dv31, dv07, dv28, dv37, dv14

## Provenance
- Source: cards/src/a27.json sha256 f03d2cc1e6f0b75e38a672101e8b982f8503b7fa7d3bb406c2eb7817366f1794
- Measures: measures/a27.json sha256 5d1d36202d99752ccbd1ed505e30543428a8c1931e7eef39dad3365ff838dd49
- Final ranking: rankings/a27.final.json sha256 39f35dbeaa36f11a2e97ba090576c03ad9bcdd30148aeff6c75f7c298c4104bf
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
