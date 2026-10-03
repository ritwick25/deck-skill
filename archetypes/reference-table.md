# Reference table

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a33 | f06 | table | v1 |

## Use when
- Many items share the same attribute columns, a catalogue, a method map or a value breakdown, and a reader must look up and compare any row.
- The slide will be read alone or kept as a reference after the meeting, so completeness matters more than a single visual argument.
- A long list must run across two slides with identical columns, so both halves read as one table.

## Avoid when
- The ratings exist to decide which items go first: use a32 prioritization-matrix.
- The cells hold marks or shades rather than text: use a31 coverage-matrix.
- The items should be shown as cards with icons rather than read as rows: use a09 catalogue.

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 3% (1 to 5) | 2% (1 to 11) | 94% (91 to 97) | 8% (5 to 9) |
| header-row | 12% (12 to 12) | 19% (19 to 19) | 83% (83 to 83) | 6% (6 to 6) |
| row-header-column | 4% (4 to 4) | 19% (19 to 19) | 24% (24 to 24) | 76% (76 to 76) |
| table-body | 3% (3 to 30) | 13% (10 to 19) | 94% (30 to 95) | 76% (75 to 79) |
| side-panel | 59% (57 to 61) | 19% (19 to 19) | 38% (35 to 41) | 77% (76 to 78) |

## Components
- A solid header row of column labels in white bold on the brand fill, or grouped header tabs over paired sub columns.
- A row header column, bold or tinted, naming each item, optionally as a stepped tile spine for levels.
- The table body of short text cells on a fixed row pitch, separated by banding or white dividers rather than heavy rules.
- Optional side panel in a brand tint holding the payoff the rows serve, such as the questions they answer.
- Icons per slide 0 (0 to 7), text shapes per slide 65 (26 to 79).

## Type roles
| Role | Size |
|---|---|
| title | 24 pt (20 to 26) |
| section-label | 13.25 pt (9.25 to 14.75) |
| card-heading | 10.75 pt (9.25 to 12) |
| label | 9.25 pt (8 to 10.75) |
| body | 10.75 pt (7.25 to 12) |
| numeral | 10.75 pt (10.75 to 10.75) |

## Density
Content words 245 (130 to 300) over 5 exemplars. Title words 11 (6 to 12). Table body width 94% (30 to 95) of the canvas.

## Word budget
Word budget 250 pooled and 250 on the standard canvas, held at the 250 ceiling because the densest exemplars run past it. No top exemplar sits on the wide canvas. Advisory floor 160.

## Device notes
- The header row is the only solid brand fill in the table, white bold labels over a pale body, so the column grammar reads before any row.
- The first column is set apart by weight or tint, a bold label, a tinted cell or a shaded tile, so each row is found by its name.
- Rows sit on a fixed pitch separated by banding or white dividers, with no vertical rules heavier than a hairline.
- A list too long for one slide splits by height into halves that repeat the same columns and pitch unchanged.

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| word-budget | Tables at or past the ceiling, with description, example and source columns, 3 flagged in the top set. | One short phrase per cell, a short provenance mark in place of a source column, descriptions moved to notes. | Columns narrow or drop, which frees width for a larger type size. |
| 8pt-floor | Most cells, source qualifiers and example sub columns below the floor, 3 flagged. | Every run at 8 pt or larger. | Fewer rows per slide, so a long list splits by tier or moves its example column to notes. |
| glyphs | En dashes in value ranges, a spaced hyphen as a dash, curly quotes, a title ellipsis and continuation marker, 4 flagged. | The word to in ranges, straight quotes or italics, no ellipsis. | None on layout. |
| no-footer | Page numbers, logo lockups and a confidentiality line, 4 flagged. | No foot chrome at all. | The table may extend into the reclaimed foot band for one more row. |
| first-person | A possessive catalogue title and user questions written in first person, 2 flagged. | A third person claim, questions kept only as attributed quotations of a user role. | None on layout. |
| flat-fill | Header cells graded light to deep blue, 2 flagged. | Flat brand fill on every header cell. | None on layout. |
| left-accent | Brand edge bars at the ends of the title band that encode no state, 1 flagged. | Remove the bars. | The title runs clean to the margins. |
| other | Topic titles fused with a part counter, a review sticky over the title, an extra header color family, maturity as plain text, 5 flagged. | One claim of 14 words or fewer per half, no review marks, headers in the deck brand color, maturity as a small status mark per row. | The title states what this half shows and the maturity column narrows to a mark. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d09-s073 | refs/views/d09-s073.jpg | a full width method table where each row runs item to measure to formula to assumption to range to source |
| d12-s010 | refs/views/d12-s010.jpg | a source column with icons mapped across to what each powers, beside a tinted panel of the questions answered |
| d16-s010 | refs/views/d16-s010.jpg | a banded catalogue table pairing each item with a description, a link and a maturity tier, sorted by tier |
| d20-s012 | refs/views/d20-s012.jpg | coded dimension rows with an icon tile, a definition and sources, keyed by color and code to matching clusters in a node graph beside them |
| d09-s074 | refs/views/d09-s074.jpg | the continuation of the method table, same columns and pitch, so both halves read as one list |

## Anti-exemplars
None.

## Variants
- Full width method table, shown by d09-s073.
- Row table beside a question panel, shown by d12-s010.
- Banded catalogue sorted by tier, shown by d16-s010.
- Coded dimension rows keyed to a cluster graph, shown by d20-s012.
- Continuation half with identical columns, shown by d09-s074.

## Devices used
dv06, dv27, dv55, dv57

## Provenance
- Source: cards/src/a33.json sha256 6ddbad936f296c83e52c62f180804706863811486fbe5f6d15b4caa271211137
- Measures: measures/a33.json sha256 81e001b7def4eeddd741ae57b44273cbdaf54f20f7c376827a20670ecebb8376
- Final ranking: rankings/a33.final.json sha256 5299e4cc2128f1e3a17fc071f069b9b43c2fec124e56221722835bbc5b490ddb
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
