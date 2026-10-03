# Gantt on a dated grid

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a37 | f08 | timeline | v1 |

## Use when
- Several workstreams run in parallel against real dates and the claim turns on overlap, duration or a critical gate.
- A dependency or go-live date must read across every stream at once, as a gate line crossing the grid.

## Avoid when
- Phases follow one another as columns with no period grid, each with its own scope and exit, so use phased-roadmap instead.
- The point is value or capability climbing across years rather than dated work, so use value-horizons instead.

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 3% (3 to 4) | 4% (1 to 6) | 94% (89 to 96) | 7% (5 to 16) |
| time-header | 23% (2 to 30) | 18% (13 to 21) | 72% (66 to 95) | 7% (4 to 10) |
| row-labels | 4% (2 to 4) | 27% (23 to 27) | 17% (15 to 22) | 55% (45 to 71) |
| bar-field | 19% (3 to 26) | 24% (16 to 25) | 78% (71 to 95) | 55% (36 to 83) |
| milestones | 28% (28 to 28) | 73% (73 to 73) | 68% (68 to 68) | 9% (9 to 9) |
| legend | 39% (39 to 39) | 94% (94 to 94) | 56% (56 to 56) | 2% (2 to 2) |
| support-strip | 3% (3 to 3) | 73% (64 to 83) | 77% (60 to 94) | 19% (11 to 27) |

## Components
- Dominant repeat of drawn shapes, bars or period cells, 6 (2 to 7) items, each bar a flat fill with its name inside.
- Icons 3 (0 to 38) per slide, placed on bars as milestone glyphs or in the row rail.
- Connectors 2 (0 to 13) per slide, dashed gate lines or period gridlines crossing the bar field.
- One header strip of period cells directly above the grid, one cell per week, month or quarter.

## Type roles
| Role | Size |
|---|---|
| title | 24 pt (18.75 to 32) |
| label | 10.5 pt (8 to 14.75) |
| body | 10.25 pt (6 to 14.75) |
| legend | 10.25 pt (10 to 10.75) |
| numeral | 20 pt (20 to 20) |
| section-label | 11 pt (10.75 to 13.25) |

## Density
Content words 132 (69 to 181) across 5 exemplars, title words 6 (3 to 13).

## Word budget
Budget 150 words normalized and 150 on the w10 canvas, advisory floor 110 and 90, under the ceiling of 250.

## Device notes
- A header strip of filled period cells sits directly above the bar field and aligns to the grid columns, not to the label column.
- Bars stagger down and to the right, so the rows read as a staircase that closes on the final date.
- Bar fill encodes phase or work type, and the row label or rail cell repeats that tone.
- Dashed vertical lines cut the bar field at gates or period boundaries.

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| no-footer | A confidentiality line, folio, wordmark or foot caption sits under the chart on 5 top exemplars. | No footer, page number, confidentiality line or foot summary band. | The bar field and support strip take the freed band at the foot, and any takeaway moves to the speaker notes. |
| glyphs | Date ranges carry en dashes, smart quotes or arrow glyphs on 5 top exemplars. | No em dash, en dash, arrow glyph or smart quote in text. | Ranges are written with the word to, which lengthens bar labels, so bars carry the name only and the range sits on the grid. |
| shadow | Soft shadows on bars, phase cards or the chart card on 3 top exemplars. | Hairlines with at most a 1 px shadow, flat fills. | The chart sits on the ground or inside a hairline frame, with no card around the whole grid. |
| 8pt-floor | Week cells, bar detail lines and phase captions run below the floor on 2 top exemplars. | Every run at 8 pt or above. | Detail lines leave the bars for the notes, and period cells widen by narrowing the label column. |
| left-accent | A colored edge bar beside the title or the slide edge on 2 top exemplars. | An accent bar only where it encodes a state that can change. | The edge bar goes, and the current period can be marked by a tinted column instead. |
| no-subtitle | A sentence line or parenthetical aside under the title on 2 top exemplars. | No subtitle under the title, which is one claim of 14 words or fewer. | The aside becomes a hatched lead-in column on the grid or moves to the notes, and the grid moves up. |
| first-person | The title or a bar detail speaks as we or our on 2 top exemplars. | No first or second person. | The title becomes a third-person claim about cadence or the critical date. |
| flat-fill | Row tabs carry a linear gradient on 1 top exemplar. | Flat fills, no gradients. | Row tabs fill flat in the brand color. |
| other | Changes outside the named rules appear on 4 top exemplars, among them gate type keyed by dash color alone. | Identity is never carried by color alone. | Each gate type carries a glyph or a label beside its dash color, and the legend shows both. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d03-s040 | greeked/d03/s040.png | color-keyed bars on a month grid, dashed gate lines landing on triangle milestones, a compact key |
| d12-s019 | greeked/d12/s019.png | phase rail with icon discs beside a week grid, staggered bars closing on a go-live staircase |
| d10-s009 | greeked/d10/s009.png | tinted milestone column bands behind alternating bars, a phase caption at the foot of each band |
| d01-s090 | greeked/d01/s090.png | capability icons placed on swimlane bars, defined once in a key row beneath the chart |
| d09-s046 | greeked/d09/s046.png | staggered phase bars with pale handover tails, cadence restated as an icon stat pair |

## Anti-exemplars
None.

## Variants
- Gate-line gantt, dashed gates through every stream to labelled milestone markers, shown by d03-s040.
- Banded gantt, tinted milestone columns behind the bars and captioned at their foot, shown by d10-s009.
- Swimlane gantt with an icon key, milestone glyphs on the bars decoded in key cards beneath, shown by d01-s090.
- Gantt over a stat pair, the cadence restated as headline figures under the grid, shown by d09-s046.
- Rail and staircase, a phase rail beside a week grid closing on a stepped go-live, shown by d12-s019.

## Devices used
dv22, dv23, dv24, dv34

## Provenance
- Source: cards/src/a37.json sha256 05109f1e3d9057705c49d25db355ece0e4c9928f141ae75f2b8d927ccf4cccd0
- Measures: measures/a37.json sha256 085ab45c36539ad564fff968a1c98d14006fde61553299993cb5d70b9f56a964
- Final ranking: rankings/a37.final.json sha256 66e4cab810929959291006cef21910640620621bd06c74d43384e18103302e2c
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
