# Maturity model

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a40 | f08 | hierarchy | v1 |

## Use when
- Levels of capability or autonomy are ranked from basic to advanced, and the audience must place itself on a rung and see the next one.
- Items such as use cases or provider types are positioned along a known maturity or adoption curve, so position carries the ranking.

## Avoid when
- Growth is plotted against years or horizons rather than levels, so use value-horizons instead.
- Rules route each case to an outcome rather than ranking levels, so use decision-logic instead.

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 3% (0 to 4) | 5% (1 to 10) | 94% (92 to 99) | 10% (5 to 13) |
| level-device | 11% (3 to 20) | 19% (17 to 37) | 72% (58 to 92) | 42% (26 to 57) |
| level-markers | 16% (13 to 36) | 43% (21 to 46) | 67% (63 to 81) | 50% (7 to 56) |
| level-grid | 2% (1 to 4) | 53% (51 to 56) | 96% (93 to 98) | 37% (29 to 45) |
| row-labels | 3% (3 to 4) | 39% (23 to 56) | 9% (7 to 11) | 38% (29 to 47) |
| side-rail | 73% (63 to 82) | 20% (19 to 21) | 24% (15 to 34) | 49% (41 to 56) |
| support-band | 3% (3 to 3) | 72% (65 to 78) | 94% (94 to 95) | 14% (14 to 14) |

## Components
- Dominant repeat of drawn shapes, one per level, 4 (3 to 5) items, with a gutter of 3% (1 to 7) of the canvas width.
- Icons 0 (0 to 16) per slide, in row headers, player boxes or rail cards.
- Connectors 0 (0 to 2) per slide, so the device carries order by position and fill rather than by arrows.
- One governing device, a rising curve, an indented ladder or a glyph redrawn per level, spanning the levels it ranks.

## Type roles
| Role | Size |
|---|---|
| title | 23.5 pt (18 to 32) |
| card-heading | 10.75 pt (8 to 15) |
| body | 8.5 pt (8 to 13) |
| label | 10 pt (8 to 13) |
| numeral | 10 pt (9.25 to 10.5) |
| section-label | 10.75 pt (10.5 to 14) |
| legend | 10.75 pt (10.75 to 10.75) |

## Density
Content words 192 (88 to 336) across 5 exemplars, title words 11 (5 to 30).

## Word budget
Budget 220 words normalized and 200 on the w10 canvas, advisory floor 80 and 190, under the ceiling of 250.

## Device notes
- Position on one rising curve ranks the levels, with a numbered disc or diamond marking each level on the curve.
- Each level heads a column of a grid under the device, so the device and its proof share column edges.
- Fill or shade steps with the level: a glyph filling in, rungs darkening toward the top, or columns deepening from pale to dark.
- A marker attached to the device places the players or the case on it: a box per stage on the curve, a fence over a stalled span, or a band under the top steps.

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| glyphs | En dashes in ranges, smart quotes in stage questions or dashes in callouts on 4 top exemplars. | No em dash, en dash, arrow glyph or smart quote in text. | Ranges read with the word to, so grid cells need room for the longer span or a single value. |
| no-footer | A confidentiality line, folio, wordmark or prose band closes the slide on 4 top exemplars. | No footer, page number, confidentiality line or foot summary band. | The foot band goes to the notes and the level grid or support band takes its height. |
| 8pt-floor | Stage notes, player text, callouts or a pasted chart image run below the floor on 2 top exemplars. | Every run at 8 pt or above. | The curve is redrawn natively with one short label per level, and player notes and legend rows are cut. |
| first-person | The title, stage questions or example cells speak as we, our or I on 2 top exemplars. | No first or second person. | Stage questions become third-person decision questions. |
| no-subtitle | Subtitle lines or a takeaway paragraph sit under or beside the title on 1 top exemplar. | No subtitle under the title, which is one claim of 14 words or fewer. | The takeaway folds into the title claim and the device moves up. |
| flat-fill | Gradient row bands, diamonds, section tabs or edge bars on 2 top exemplars. | Flat fills, no gradients. | Row bands take one flat tint each, and the level shade ramp is built from flat steps. |
| left-accent | A gradient edge bar or short bars beside row labels mark no state on 2 top exemplars. | An accent bar only where it encodes a state that can change. | The bars go, and the icon tile or row header heads each row alone. |
| word-budget | Principle cards, enabler strips and foot paragraphs push words past the budget on 2 top exemplars. | A per-archetype word budget under the ceiling of 250. | The device and its markers stay, and the support band moves to its own slide or the notes. |
| shadow | Blurred shadows on principle cards on 1 top exemplar. | Hairlines with at most a 1 px shadow. | Cards take a hairline outline only. |
| light-bg | A dark photo band under a navy overlay closes the slide on 1 top exemplar. | Light slide grounds. | The band becomes a light panel or is dropped under the foot band rule. |
| other | Changes outside the named rules appear on 5 top exemplars, among them titles of up to 11 (5 to 30) words and a second introduced accent color. | The title is one claim of 14 words or fewer, and accents stay to the brand color plus neutrals. | Titles are cut to one line, and row headers use the brand color and one neutral. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d01-s013 | refs/views/d01-s013.jpg | one glyph redrawn at rising fill per stage over a row-headed grid of impact and example cells |
| d17-s004 | refs/views/d17-s004.jpg | diamond milestones on a rising arc head a stage-by-dimension matrix, a fence marking the stall span |
| d21-s002 | refs/views/d21-s002.jpg | columns climbing as a staircase with fill deepening toward the top, and a band under the top two steps placing the case |
| d03-s031 | refs/views/d03-s031.jpg | rungs indenting toward the base and darkening toward the top, beside an owner column |
| d07-s006 | refs/views/d07-s006.jpg | numbered markers on one rising curve pair each stage with a player box, closing on a provider rail |

## Anti-exemplars
None.

## Variants
- Glyph fill row over a row-headed grid, shown by d01-s013.
- Arc over a stage matrix with a fenced risky span, shown by d17-s004.
- Staircase of rising columns with a band placing the case, shown by d21-s002.
- Indented ladder beside an owner column, shown by d03-s031.
- Numbered curve with player boxes and a provider rail, shown by d07-s006.

## Devices used
dv22, dv25, dv27, dv32, dv43

## Provenance
- Source: cards/src/a40.json sha256 99dce59b6797fcd74f8b00750d47da85d17148fdf8f47c97e812336a6238c441
- Measures: measures/a40.json sha256 d3a35717330adea4dd0605596945021ce5ce0014d6434072dc4375bab2b10b07
- Final ranking: rankings/a40.final.json sha256 225c4ac38f1965c70e1f6e5c928fe30351be2516242a51ecdd0543ebbc69753c
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
