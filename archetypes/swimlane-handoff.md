# Swimlane hand-off

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a17 | f03 | sequence | v1 |

## Use when
- Two or more actors, such as a human role and an agent, share one process and the point is who acts at each stage and where control passes between them.
- Every hand-off between lanes needs a visible mark, a gate or a named rule, so the audience can see where people stay in control.

## Avoid when
- Only one actor runs the steps in a single chain, so use process-flow instead.
- The steps sit on dates or bars across a period grid, so use gantt instead.
- One named record must be traced with its literal values at every hop, so use worked-example instead.
- The lanes are the vendor's workstreams for running the engagement rather than actors in the solution, so use engagement-model instead.

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 3% (1 to 4) | 5% (1 to 6) | 97% (93 to 98) | 7% (4 to 31) |
| stage-header | 3% (3 to 4) | 19% (18 to 19) | 94% (93 to 95) | 3% (3 to 4) |
| lanes | 3% (1 to 4) | 30% (24 to 43) | 95% (93 to 96) | 35% (32 to 69) |
| loop-routes | 3% (3 to 3) | 24% (24 to 24) | 86% (86 to 86) | 74% (74 to 74) |
| spine | 1% (1 to 1) | 18% (18 to 18) | 97% (97 to 97) | 79% (79 to 79) |
| shared-band | 1% (1 to 1) | 54% (54 to 54) | 85% (85 to 85) | 7% (7 to 7) |
| legend | 82% (82 to 82) | 81% (81 to 81) | 17% (17 to 17) | 16% (16 to 16) |
| context-band | 4% (4 to 4) | 61% (61 to 61) | 93% (93 to 93) | 36% (36 to 36) |

## Components
- Step cards in each lane, 6 (5 to 7) in the dominant repeat, one card kind per actor so the lane owner reads before the text.
- Connectors 6 (5 to 7) per slide, thin elbow or straight routes with small arrowheads, each starting on one card and landing on another.
- Icons 2 (2 to 3) per slide, a line glyph on each lane label at most, never on every card.
- A hand-off row between two lanes, one short up or down arrow per crossing with its rule as a plain label, kept as thin as the labels allow.
- Stage headers as a tab row across the top or a label rail down the left, one per stage, shared by every lane.

## Type roles
| Role | Size |
|---|---|
| title | 21.5 pt (17 to 24) |
| section-label | 8.25 pt (8 to 12.75) |
| card-heading | 8.25 pt (8 to 11.5) |
| body | 8 pt (8 to 8.75) |
| label | 7.75 pt (7.25 to 8) |
| legend | 7.75 pt (6.75 to 9) |
| caption | 8 pt (6.75 to 9.25) |

## Density
Content words 296 (172 to 469) across 3 top exemplars, with 68 (44 to 74) text shapes per slide.

## Word budget
Budget 250 words normalized and 250 on the w13 canvas, advisory floor 230, under the ceiling of 250.

## Device notes
- Shared stage headers sit once above or beside all lanes, so every card aligns to a stage without repeating the stage name.
- Each actor owns one card kind, a filled header for the automated actor and a white or differently tinted header for the human one, so lane ownership survives when cards move between rows.
- Hand-offs are short arrowed routes between lanes, drawn as their own row or as elbows, so the crossing points read as a separate layer of the diagram.
- A small legend decodes the card kinds and route styles, kept in one corner and sized to its few entries.

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| no-footer | A page number, confidentiality line or version stamp appears on 3 top exemplars. | No footer, page number, confidentiality line or foot summary band. | The lanes and the context band take the reclaimed height. |
| no-subtitle | A lead line sits under the title on 2 top exemplars. | No subtitle under the title. | The lead line folds into the one-claim title or moves to the speaker notes, and the stage header moves up. |
| 8pt-floor | Card bodies, role tags and lane qualifiers render below the floor on 2 top exemplars. | Every run at 8 pt or above. | Raising card text widens each card, so cut every card body to one line and move qualifiers to the speaker notes. |
| word-budget | Content words run over the budget on 2 top exemplars, with card bodies and the context band as the excess. | Per-archetype word budget under the ceiling of 250. | Cut card bodies to one line and drop the context band before shrinking type. |
| first-person | A heading or hand-off label speaks in the first person on 1 top exemplar. | No first or second person. | Rewrite hand-off labels as imperatives and headings as neutral nouns. |
| left-accent | Colored edge bars mark the title or column heads as decoration on 2 top exemplars. | A colored left or top accent bar only where it encodes a changeable state. | Remove the bars and carry a heading with a hairline above its label. |
| shadow | Soft shadows sit under bars and cards on 1 top exemplar. | Hairlines with at most a 1 px shadow. | Outline every card with a hairline and drop the shadow. |
| glyphs | Dashes and arrow glyphs appear in the title or captions on 1 top exemplar. | No em dash, en dash or arrow glyph in text. | Write the word to in place of an arrow and a colon in place of a dash. |
| emoji | A pictograph glyph sits inside a bar label on 1 top exemplar. | No emoji. | Delete the glyph, the bar label carries the meaning alone. |
| other | A narrating callout, letterspaced mono kickers on every block or an overlong title appear on 2 top exemplars. | One label style, no narrating callout, a title of one claim. | Cut the callout, keep one sans label style, and hold the title to 14 words with up to 3 keywords in the brand color. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d15-s020 | refs/views/d15-s020.jpg | two lanes under shared stage tabs with a middle hand-off row of arrows, each labelled with its rule |
| d02-s007 | refs/views/d02-s007.jpg | phase headers over lanes where automated and human cards alternate, numbered discs on every human gate and loop routes for revision |
| d12-s015 | refs/views/d12-s015.jpg | a stage rail beside a centered spine that fans into parallel lanes through one shared band and rejoins into one output |

## Anti-exemplars
None.

## Variants
- Two lanes under stage tabs with a hand-off arrow row between them, shown by d15-s020.
- Phase-headed lanes with numbered gate discs and return loops, shown by d02-s007.
- Spine fanning into parallel lanes through a shared band and back, shown by d12-s015.

## Devices used
dv06, dv01, dv11, dv14, dv15, dv32

## Provenance
- Source: cards/src/a17.json sha256 5d8e71968e3431d14454ed2314a5079af4fd89d3f145959d632992cb924b0b8b
- Measures: measures/a17.json sha256 50216928a9ff0cd2bb875cc558c3bdcb4b7eb399dc24a61d8b99c6bbe0ed5b9d
- Final ranking: rankings/a17.final.json sha256 583d4e66287e204247b5f3ecf9db6511424ad4914f72247a3ee09c6c6be40fb5
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
