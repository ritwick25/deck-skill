# Use-case map

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a30 | f06 | map | v1 |

## Use when
- Many use cases or agents must be shown against the client's value chain, functions or phases, so coverage and placement read at once.
- The audience needs to see where each use case acts, and which stages are crowded or empty, before any ranking is discussed.
- A first wave or a starting domain should be lit inside the full landscape, keeping the rest visible as context.

## Avoid when
- The items are an unordered list of agents with the same fields, so placement adds nothing: use a09 catalogue.
- The candidates are scored or ranked to decide which go first: use a32 prioritization-matrix.
- Every cell of a stage by item grid must state what applies where: use a31 coverage-matrix.

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 3% (1 to 4) | 2% (1 to 5) | 94% (93 to 97) | 9% (6 to 12) |
| value-chain-axis | 6% (2 to 10) | 26% (12 to 51) | 85% (84 to 96) | 7% (4 to 15) |
| use-case-cards | 3% (2 to 4) | 21% (14 to 35) | 94% (91 to 96) | 61% (42 to 80) |
| cross-cutting | 4% (4 to 10) | 18% (18 to 75) | 91% (77 to 93) | 15% (11 to 76) |
| legend | 67% (67 to 67) | 96% (96 to 96) | 28% (28 to 28) | 3% (3 to 3) |

## Components
- A value-chain axis: header bars or tabs over columns, or a row of large stage discs as a spine, one per phase or function.
- Use case or agent cards stacked under each header, set in lanes, or hung above and below the spine, each with a name and one value line.
- Optional numbered discs on each card so the narration can call cards by number.
- Optional cross-cutting band or platform panel spanning every column, above or below the cards.
- Optional legend swatch decoding a heavier outline or tint that marks a first-wave subset.
- Card height 12% (5 to 64) and width 22% (7 to 93) of the canvas.
- Icons per slide 16 (12 to 36), connectors per slide 11 (0 to 50).

## Type roles
| Role | Size |
|---|---|
| title | 22.75 pt (21 to 25.25) |
| card-heading | 12 pt (8 to 16) |
| body | 10.75 pt (6.75 to 14.75) |
| section-label | 12.75 pt (10.75 to 16) |
| label | 12 pt (8 to 12) |
| numeral | 12 pt (12 to 12) |

## Density
Content words 161 (75 to 188) over 5 exemplars. Title words 13 (7 to 19). Card zone width 94% (91 to 96) of the canvas.

## Word budget
Word budget 180 pooled, 180 on the standard canvas and 150 on the wide canvas, under the 250 ceiling. Advisory floor 100.

## Device notes
- Each phase or function is announced once by a solid header bar, tab or stage disc, and the cards under it carry no repeat of that label.
- Cards under one header are the same size and stack on a fixed pitch, so a column's length shows how crowded that stage is.
- A selected subset, a first phase or a starting domain, is lit by a heavier outline, a solid tab or a flat tint and decoded by one key, while the rest stays in plain outline.
- A concern shared by every stage sits in one band or panel spanning the full width, set apart from the per stage cards.

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| no-footer | Confidentiality lines, page numbers, wordmarks and gradient foot bands, 5 flagged in the top set. | No foot chrome at all. | The cross-cutting band or the lowest card row may sit in the reclaimed foot band. |
| left-accent | Gradient left edge bars and lime bars on each row card that encode no state, 4 flagged. | Remove the bars. A heavier outline stays only where it marks a selected phase. | Row cards run clean to the margin and the selection outline becomes the only accent. |
| shadow | Soft blurred shadows under cards, header bars and pills, 3 flagged. | Hairline outline, at most a 1 px shadow. | No change to geometry, trays or white gaps carry the separation. |
| flat-fill | Multi stop gradient edge and foot bars, 2 flagged. | Remove the bars, keep any spotlight wedge as a flat tint. | None on layout once the bars are gone. |
| 8pt-floor | Card bodies and metric pills set below the floor in dense meshes, 2 flagged. | Every run at 8 pt or larger, keeping a heading and one value line per card. | Card bodies drop to one line, and a crowded mesh keeps one pill per agent. |
| glyphs | Smart apostrophes in titles, em and en dashes in card bodies, pipe separated lists, 3 flagged. | Straight apostrophes, colons or the word to, chips in place of pipe lists. | None on layout. |
| first-person | A title written as we combine, 1 flagged. | A third person claim with role nouns. | The shorter title clears the top right corner. |
| no-subtitle | A line under the title restating what the lanes already name, 1 flagged. | Delete the subtitle, the axis labels carry the frame. | The axis and cards move up into the freed band. |
| other | Label titles naming a client, product wordmark images, a back to agenda roundel, 4 flagged. | One claim of 14 words or fewer naming no client, plain type labels, no navigation chrome. | Card heads lose image height and the top right corner is free. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d01-s014 | greeked/d01/s014.png | numbered agent cards on two lanes with solid hand off arrows and dashed feedback loops, one band spanning both lanes |
| d09-s035 | greeked/d09/s035.png | full width row cards chained left to right by chevrons, each row one use case read from role to value |
| d12-s012 | greeked/d12/s012.png | four numbered header bars over gray trays of equal cards, a heavier outline marking the first wave against one key |
| d07-s007 | greeked/d07/s007.png | five stage discs as a spine with module cards hung above and below by drop lines to the stages each serves |
| d01-s065 | greeked/d01/s065.png | agent disc mesh under domain tabs, one tab lit as the starting domain, resting on a platform panel |

## Anti-exemplars
None.

## Variants
- Two lanes of numbered agent cards over a shared band, shown by d01-s014.
- Chained row cards under column headings, shown by d09-s035.
- Numbered header bars over card trays with a lit subset, shown by d12-s012.
- Stage disc spine with hung module cards, shown by d07-s007.
- Domain tabs over an agent mesh with a spotlit domain, shown by d01-s065.

## Devices used
dv06, dv05, dv08, dv17, dv45

## Provenance
- Source: cards/src/a30.json sha256 015a904ed504766a4c9a6ca779486c925b18e0f37b74620960b8e28e19bef27b
- Measures: measures/a30.json sha256 97d20c55b49196570ed1e406c51e81a0d1c94de5b169dd6c0f9350892e755748
- Final ranking: rankings/a30.final.json sha256 2b99c687efd7d935f02305e164a7216e6e6688b0f298b9207adbfe0d73bb4725
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
