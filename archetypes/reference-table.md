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
| title | 3% (1 to 3) | 2% (1 to 5) | 94% (91 to 97) | 8% (5 to 9) |
| header-row | 2% (2 to 2) | 1% (1 to 1) | 97% (97 to 97) | 19% (19 to 19) |
| row-header-column | 4% (4 to 4) | 19% (19 to 19) | 24% (24 to 24) | 76% (76 to 76) |
| table-body | 3% (1 to 30) | 13% (10 to 20) | 95% (30 to 98) | 76% (71 to 79) |
| side-panel | 61% (61 to 61) | 19% (19 to 19) | 35% (35 to 35) | 76% (76 to 76) |

## Components
- A solid header row of column labels in white bold on the brand fill, or grouped header tabs over paired sub columns.
- A row header column, bold or tinted, naming each item, optionally as a stepped tile spine for levels.
- The table body of short text cells on a fixed row pitch, separated by banding or white dividers rather than heavy rules.
- Optional side panel in a brand tint holding the payoff the rows serve, such as the questions they answer.
- Icons per slide 0 (0 to 7), text shapes per slide 68 (26 to 79).

## Type roles
| Role | Size |
|---|---|
| title | 25.25 pt (21.25 to 26) |
| section-label | 12 pt (9.25 to 13.25) |
| card-heading | 10 pt (9.25 to 10.75) |
| label | 10.75 pt (8 to 12) |
| body | 10.75 pt (7.25 to 12) |
| numeral | 10.75 pt (10.75 to 14.75) |

## Density
Content words 245 (130 to 300) over 5 exemplars. Title words 11 (6 to 11). Table body width 95% (30 to 98) of the canvas.

## Word budget
Word budget 250 pooled and 250 on the standard canvas, held at the 250 ceiling because the densest exemplars run past it. No top exemplar sits on the wide canvas. Advisory floor 220.

## Device notes
- The header row is the only solid brand fill in the table, white bold labels over a pale body, so the column grammar reads before any row.
- The first column is set apart by weight or tint, a bold label, a tinted cell or a shaded tile, so each row is found by its name.
- Rows sit on a fixed pitch separated by banding or white dividers, with no vertical rules heavier than a hairline.
- A list too long for one slide splits by height into halves that repeat the same columns and pitch unchanged.

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| word-budget | Tables at or past the ceiling, with description, example and source columns, 4 flagged in the top set. | One short phrase per cell, a short provenance mark in place of a source column, descriptions moved to notes. | Columns narrow or drop, which frees width for a larger type size. |
| 8pt-floor | Most cells, source qualifiers and example sub columns below the floor, 3 flagged. | Every run at 8 pt or larger. | Fewer rows per slide, so a long list splits by tier or moves its example column to notes. |
| glyphs | En dashes in value ranges, a spaced hyphen as a dash, curly quotes, a title ellipsis and continuation marker, 5 flagged. | The word to in ranges, straight quotes or italics, no ellipsis. | None on layout. |
| no-footer | Page numbers, logo lockups and a confidentiality line, 3 flagged. | No foot chrome at all. | The table may extend into the reclaimed foot band for one more row. |
| first-person | A possessive catalogue title and user questions written in first person, 2 flagged. | A third person claim, questions kept only as attributed quotations of a user role. | None on layout. |
| flat-fill | Header cells graded light to deep blue, 1 flagged. | Flat brand fill on every header cell. | None on layout. |
| left-accent | Brand edge bars at the ends of the title band that encode no state, 1 flagged. | Remove the bars. | The title runs clean to the margins. |
| other | Topic titles fused with a part counter, a review sticky over the title, an extra header color family, maturity as plain text, 5 flagged. | One claim of 14 words or fewer per half, no review marks, headers in the deck brand color, maturity as a small status mark per row. | The title states what this half shows and the maturity column narrows to a mark. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d09-s073 | greeked/d09/s073.png | a full width method table where each row runs item to measure to formula to assumption to range to source |
| d12-s010 | greeked/d12/s010.png | a source column with icons mapped across to what each powers, beside a tinted panel of the questions answered |
| d16-s010 | greeked/d16/s010.png | a banded catalogue table pairing each item with a description, a link and a maturity tier, sorted by tier |
| d09-s074 | greeked/d09/s074.png | the continuation of the method table, same columns and pitch, so both halves read as one list |
| d12-s027 | greeked/d12/s027.png | a shaded level spine indexing grouped metric and example columns whose ragged bottoms show each tree's depth |

## Anti-exemplars
None.

## Variants
- Full width method table, shown by d09-s073.
- Row table beside a question panel, shown by d12-s010.
- Banded catalogue sorted by tier, shown by d16-s010.
- Continuation half with identical columns, shown by d09-s074.
- Level spine against grouped column pairs, shown by d12-s027.

## Devices used
dv06, dv27, dv55, dv57

## Provenance
- Source: cards/src/a33.json sha256 28c8a21e98f75e800acaf0ea855657a491a7d0edc0327dcff762681c470faa96
- Measures: measures/a33.json sha256 89941ed3aec442f2aab83d5fcd389406f8e2bf7d1b38ef3fc2fb5a08c2b4d32b
- Final ranking: rankings/a33.final.json sha256 16c110daff10154ac1266c22cc85fe06282cab5fe679e8e09a4631edadae8f36
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
