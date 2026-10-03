# Prioritization matrix

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a32 | f06 | matrix | v1 |

## Use when
- Many candidates must be scored against shared criteria, or plotted on two axes such as value and effort, so the room can agree which go first.
- The ranking needs its reasons on the page: a score per criterion and one line of rationale per candidate.
- Candidates fall into families or phases that should read as groups on the same field.

## Avoid when
- There are only two or three discrete options to weigh: use a24 options-comparison.
- Use cases are placed on the value chain with no ranking: use a30 use-case-map.
- The rows are a catalogue to look up rather than ratings that decide order: use a33 reference-table.

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 3% (3 to 3) | 2% (2 to 4) | 93% (92 to 96) | 7% (7 to 11) |
| candidate-field | 3% (3 to 7) | 12% (12 to 19) | 94% (62 to 94) | 79% (71 to 79) |
| axis-labels | 4% (2 to 7) | 55% (21 to 90) | 71% (62 to 80) | 39% (2 to 77) |
| key-rail | 79% (71 to 88) | 27% (15 to 39) | 19% (12 to 26) | 49% (35 to 63) |

## Components
- The candidate field, in one of two forms: a scoring table of candidates by criteria with a wide rationale column, or a value by effort field holding every candidate.
- In the table form, narrow score columns under a solid header row, one row per candidate, the rationale column last.
- In the plotted form, a pale tinted field split into quadrants or a grid, candidates as numbered discs or small cards, optional dashed rings grouping a family.
- Axis labels along the left and bottom edges of a plotted field, naming value and effort or complexity.
- A key rail beside a plotted field, decoding each disc number or group color to its candidate.
- Icons per slide 1 (0 to 1), text shapes per slide 50 (40 to 55).

## Type roles
| Role | Size |
|---|---|
| title | 28 pt (18.75 to 28) |
| section-label | 13.25 pt (8 to 13.25) |
| card-heading | 12 pt (8 to 12) |
| body | 12 pt (5.75 to 12) |
| label | 13.25 pt (5.25 to 13.25) |
| numeral | 12 pt (8 to 12) |
| legend | 9.25 pt (8 to 10.75) |

## Density
Content words 197 (116 to 208) over 5 exemplars. Title words 7 (4 to 9). Candidate field width 94% (62 to 94) of the canvas.

## Word budget
Word budget 200 pooled and 200 on the standard canvas, under the 250 ceiling. No top exemplar sits on the wide canvas. Advisory floor 180.

## Device notes
- In the table form the criteria sit in narrow equal columns of single scores, and one wide column at the right carries the reason for each row.
- In the plotted form the field is a pale tint split by faint rules, with the axis names set outside the field along its left and bottom edges.
- Plotted candidates are colored by phase or family and a key rail beside the field decodes each color and number, so the field itself carries only marks.

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| first-person | A table title written as our framework, 3 flagged in the top set. | A third person claim naming which candidates rank highest. | The title states the finding, so the part counter beside it can go. |
| no-footer | Page numbers, logo lockups and a confidentiality line at the foot, 5 flagged. | No foot chrome at all. | The table or field may extend into the reclaimed foot band. |
| word-budget | A rationale column of two to four lines per row with linked sources, 3 flagged. | One short clause of rationale per row, sources moved to notes, within the word budget. | Row height drops, so a split set can return to fewer slides. |
| 8pt-floor | Disc numerals, key entries, card names and floating labels below the floor, 2 flagged. | Every run at 8 pt or larger, floating labels dropped. | Discs and the key rail grow, so fewer candidates fit one field. |
| shadow | Blurred shadows under discs, cards and the note card, 2 flagged. | Hairline outline, at most a 1 px shadow. | No change to geometry. |
| flat-fill | Gradient block arrows along both axes, 1 flagged. | Flat brand axis arrows drawn as shapes, or plain axis rules. | None on layout. |
| glyphs | Arrow glyphs in axis labels and in the sequencing note, 1 flagged. | Axis arrows drawn as shapes and a numbered order in the note. | None on layout. |
| no-subtitle | A line under the title, 1 flagged. | Delete the subtitle, the title carries the one claim. | The field moves up into the freed band. |
| other | A part counter and back to agenda roundel, raw numeric scores, identity carried by color alone, label style titles, 5 flagged. | Split a long set by stage or rank band with its own claim, scores as filled marks or shaded cells with a key, a letter or glyph on each group beside its color. | Score columns narrow to marks and the key rail carries a glyph per group. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d09-s020 | greeked/d09/s020.png | candidates by criteria with narrow score columns, a stage column and a wide rationale column closing each row |
| d12-s040 | greeked/d12/s040.png | numbered discs colored by phase on a tinted value by effort quadrant field, decoded by a side key rail |
| d16-s018 | greeked/d16/s018.png | dashed rings grouping candidate cards into families on a value by complexity grid with a legend |
| d09-s021 | greeked/d09/s021.png | the second page of the same scoring table, showing how a long candidate set splits across slides |
| d09-s022 | greeked/d09/s022.png | a further page of the scoring table, same columns and row pitch, a different candidate band |

## Anti-exemplars
None.

## Variants
- Scoring table with a rationale column, shown by d09-s020.
- Value by effort quadrants with numbered discs and a key rail, shown by d12-s040.
- Value by complexity grid with family rings, shown by d16-s018.
- Scoring table continued across pages, shown by d09-s021.

## Devices used
dv42, dv40, dv41

## Provenance
- Source: cards/src/a32.json sha256 138a7a451ed44cd87050c3eafba7334e275bb99fa5af893491c022bbfbca7b7c
- Measures: measures/a32.json sha256 bf8c27561bf0176d35f32e3b3f506b8375d7cebb1b000e0577f4e14f10860099
- Final ranking: rankings/a32.final.json sha256 d358f9e7ac59a03ef89bdc4361479f88d0aa90c80c2868d6252b0cf0cf2aaed1
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
