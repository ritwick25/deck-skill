# Section divider

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a03 | f01 | section-marker | v1 |

## Use when
- The deck turns into a new part and the audience needs the numeral and the part name, with almost no other words.
- The deck already showed its contents as a grid, so the same grid returns with only the current part lit.

## Avoid when
- The contents appear for the first time, so use agenda (a02) instead.
- The page carries an argument, a figure or a diagram, so use the archetype of that argument instead, such as claim-proof or a diagram archetype.
- The page opens the deck with the parties and the date, so use cover (a01) instead.

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 3% (2 to 8) | 27% (3 to 45) | 94% (32 to 96) | 33% (6 to 66) |
| numeral-mark | 0% (0 to 0), one exemplar | 0% (0 to 0) | 28% (28 to 28) | 42% (42 to 42) |
| graphic-anchor | 65% (65 to 65), one exemplar | 15% (15 to 15) | 26% (26 to 26) | 70% (70 to 70) |
| contents-grid | 6% (6 to 6), one exemplar | 15% (15 to 15) | 89% (89 to 89) | 76% (76 to 76) |
| logo-lockup | 75% (75 to 75) | 4% (4 to 4) | 21% (21 to 21) | 13% (13 to 13) |

## Components
- A part title of title words 4 (2 to 4), set large on the left.
- A part numeral, either oversized and pale beside the title, held in a corner disc, or printed on the lit tile.
- At most one graphic anchor: the numeral itself, a bar-built pictogram, or the reprinted contents grid.
- Text shapes 2 (1 to 13) and content pictures 1 (0 to 2) per slide.

## Type roles
| Role | Size |
|---|---|
| title | 40 pt (25.25 to 54) |
| numeral | 224 pt (66 to 320) |

## Density
The emptiest page in the deck. Content words 5 (2 to 67) per slide, with the high end only where the contents grid is reprinted.

## Word budget
Word budget 10 with an advisory floor of 0, under the hard ceiling of 250. The title stays within 14 words.

## Device notes
- An oversized pale gray numeral counterweights a two-line brand title on an otherwise empty light ground (d12-s003, d13-s003).
- The party marks from the cover stay top right as a small lockup (d12-s003, d13-s003).
- The numeral is the largest type on the page and carries the position on its own (d02-s003, d12-s003, d13-s003, d01-s004).
- Besides the title, the page holds one graphic anchor and nothing else (d12-s003, d13-s003, d01-s004, d03-s004).

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| light-bg | A dark photo ground under a scrim, and a dark patterned ground, on 2 top exemplars. | Light slide ground with the title in dark ink. A solid brand or near-black block may hold the part numeral, set in that fill's ON_FILL role. | The photo goes, so the anchor is a pale numeral, a solid numeral block or a flat bar pictogram on the light ground. |
| flat-fill | Gradient tiles and a gradient quarter disc on 2 top exemplars. | One flat brand fill for the lit tile or disc, flat gray for the rest. | The lit state is carried by fill alone, so the tiles keep one type treatment. |
| shadow | A soft shadow under the lit tile on 1 top exemplar. | No soft shadow, at most 1 px. | The lit tile sits level with the grayed ones. |
| glyphs | Curly apostrophes and bullet markers on 2 top exemplars. | Straight apostrophes and plain stacked lines. | No layout change. |
| first-person | A possessive part title on 1 top exemplar. | A neutral noun phrase names the part. | The title gets shorter and the numeral gains room. |
| no-footer | A folio, a wordmark and a classification line at the foot on 2 top exemplars. | No footer, folio or classification line. | The foot of the divider stays empty ground. |
| other | Lifestyle imagery and a translucent wave band on 1 top exemplar. | No product or lifestyle imagery on a divider, and no decorative band. | The numeral disc or the pale numeral carries the divider alone. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d02-s003 | refs/views/d02-s003.jpg | The contents grid returns with one tile lit in brand and three grayed, so position in the deck is a visible state. |
| d12-s003 | refs/views/d12-s003.jpg | An oversized pale gray numeral beside a short bold headline and nothing else on the ground. |
| d13-s003 | refs/views/d13-s003.jpg | The same frame as its sibling dividers, a two-line title against a giant pale numeral. |
| d01-s004 | refs/views/d01-s004.jpg | A corner quarter disc holds the part numeral and repeats identically on every divider. |
| d03-s004 | refs/views/d03-s004.jpg | A pictogram built from flat bars of mixed weight faces a two-tone part title. |

## Anti-exemplars
None.

## Variants
- Ghost numeral divider: title left, oversized pale numeral right (d12-s003, d13-s003).
- Lit-tile divider: the contents grid reprinted with the current part lit (d02-s003).
- Corner disc divider: the numeral in a quarter disc bleeding off the top-left corner (d01-s004).
- Pictogram divider: a bar-built pictogram faces the part title (d03-s004).

## Devices used
dv01, dv02, dv03, dv04

## Provenance
- Source: cards/src/a03.json sha256 30955c7ad907378ab550bf7470548bf56685afdaf8368e21ec468645054b348a
- Measures: measures/a03.json sha256 e1ad3f7d1c854c3a345d7164f40b64a1fe6bfda91bc112ddfe8264700f82e47e
- Final ranking: rankings/a03.final.json sha256 e6a5ac1e1c256303f586bcd7e10bffa863e0e00824047d5e269c7d10559ae0bd
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
