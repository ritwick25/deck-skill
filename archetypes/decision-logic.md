# Decision logic

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a16 | f03 | hierarchy | v1 |

## Use when
- The audience must trust that the system decides predictably, so the rules that route each case are shown as questions with their answers.
- One inventory or one trigger splits into a few disposition lanes or actions, and each lane can be named with its path.
- A why question is answered level by level, so a drill-down ladder shows how a headline finding is reached and can be audited.

## Avoid when
- The steps run in a line with no branching, use process-flow (a13) instead.
- The rungs are levels of capability an organization climbs, use maturity-model (a40) instead.
- Options are weighed side by side for one choice by the audience, use options-comparison (a24) instead.
- Items are ranked on two axes rather than routed by rules, use prioritization-matrix (a32) instead.

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 3% (2 to 3) | 6% (1 to 7) | 94% (93 to 97) | 10% (5 to 16) |
| question-band | 4% (4 to 4) | 12% (12 to 12) | 87% (87 to 87) | 27% (27 to 27) |
| stage-tabs | 3% (2 to 4) | 41% (17 to 42) | 87% (68 to 95) | 5% (4 to 5) |
| case-input | 3% (2 to 3) | 21% (18 to 27) | 37% (27 to 94) | 42% (9 to 72) |
| decision-ladder | 4% (3 to 41) | 23% (16 to 48) | 87% (18 to 94) | 44% (29 to 72) |
| method-row | 55% (3 to 60) | 40% (19 to 82) | 33% (18 to 94) | 51% (9 to 72) |
| output-panel | 66% (2 to 80) | 48% (26 to 85) | 30% (16 to 47) | 44% (6 to 54) |

## Components
- Rungs, tiles or cards in a repeat of 6 (3 to 6), each 17% (6 to 57) of the slide width and 9% (4 to 20) of its height.
- Connectors per slide 1 (0 to 18), short arrows from each rung to its answer or outcome, elbow arrows feeding one rung down to the next, and a bracket where one set splits or gathers.
- Icons per slide 7 (0 to 24), one per input, lane lead or tool card.
- Optional numbered tabs naming each column, and an optional example card beside the output panel showing one routed case.

## Type roles
| Role | Size |
|---|---|
| title | 25.25 pt (24 to 32) |
| section-label | 11 pt (8.25 to 12) |
| card-heading | 10 pt (9 to 12) |
| body | 7.5 pt (6.5 to 10.75) |
| label | 8.75 pt (7 to 10.75) |
| numeral | 9 pt (8.25 to 14.75) |

## Density
Text shapes per slide 61 (27 to 88). The decision ladder fills 87% (18 to 94) of the slide width and 44% (29 to 72) of its height.

## Word budget
Word budget 250, the upper quartile of the top exemplars capped at 250. Content words on the top exemplars run 241 (131 to 329).

## Device notes
- Each rung of the ladder carries a number in a disc or tile, so the order of the questions reads without arrows (d12-s025, d12-s051, d12-s052).
- Each question rung names its test and the outcome it routes to on the same row, so every route can be read off one line (d12-s051, d12-s052).
- Rungs or criterion tiles step in tint from the first to the last, so depth or order is carried by shade as well as by number (d12-s025, d03-s017).
- A bracket splits one set into disposition lanes or gathers the ladder answers into one written output (d12-s025, d03-s028).
- Numbered tabs joined by chevrons head the columns from inputs through the ladder to a filled output panel at the right end, at 66% (2 to 80) from the left edge (d12-s051, d12-s052).

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| 8pt-floor | Chain labels, card bullets, ladder answers and formula lines set at or below the floor, on 4 top exemplars. | Every run at 8 pt or above. | Fewer cards per column and fewer ladder rows, with the rest moved to the notes or a second slide. |
| first-person | Possessives in the title and our and us inside formulas and panel sentences, on 4 top exemplars. | The framework or the client as the subject in the third person. | None on geometry. |
| flat-fill | A gradient level axis and a vertical gradient benefits panel, on 2 top exemplars. | Flat steps that match the rung shades, and one flat brand tint. | None on geometry. |
| glyphs | Spaced hyphens and dashes in titles and headers and arrow glyphs inside card text, on 5 top exemplars. | A colon, a comma, the word to, or arrows drawn as shapes. | None on geometry. |
| left-accent | Title edge bars, a navy bar on each metric card and a bar on a gate panel, on 3 top exemplars. | No accent bar unless it encodes a state that can change, such as a pass or hold on a gate. | Title and columns start at the shared left margin. |
| no-footer | Lockups, folios, confidentiality lines and a foot note line, on 4 top exemplars. | No footer, page number, confidentiality line or foot summary band, with data caveats in the notes. | The method row or the ladder sits on the bottom margin. |
| no-subtitle | A subtitle line or a header line saying what the rows address, on 3 top exemplars. | Fold it into the title claim, or let the band label stand alone. | The ladder starts directly under the title. |
| other | Topic label titles of 5 (4 to 8) words, giant letters set behind their criterion names, italic reading captions, and arrows in a second color with no status, on 5 top exemplars. | One claim of 14 words or fewer with up to 3 keywords in the brand color, a letter above its name, and one arrow color. | None on geometry. |
| shadow | Soft card shadows, on 2 top exemplars. | A gray hairline plus at most a 1 px shadow. | None on geometry. |
| word-budget | Content words above the archetype budget, on 5 top exemplars. | Hold the budget of 250, never above 250. | One line per card, purpose lines and the second bullet on each tool card cut, and a restating benefits panel or stepper dropped. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d12-s025 | refs/views/d12-s025.jpg | A numbered ladder of why questions, shaded by depth and answered beside each rung, bracketed into the written output. |
| d03-s028 | refs/views/d03-s028.jpg | A bracket splits one inventory into tinted disposition lanes whose step chains shrink from rebuild to retire. |
| d12-s051 | refs/views/d12-s051.jpg | A trigger box heads a numbered question ladder that routes each case to an outcome inside numbered tab columns. |
| d03-s017 | refs/views/d03-s017.jpg | Weighted criterion tiles on one track, fed by a gate and stepping in tint from first to last. |
| d12-s052 | refs/views/d12-s052.jpg | The same tab columns and trigger ladder on a second case, showing the device carries across inputs. |

## Anti-exemplars
None.

## Variants
- Drill-down ladder of why questions bracketed into a written answer (d12-s025).
- Bracket triage into disposition lanes over a numbered tool row (d03-s028).
- Tab columns with a trigger and question ladder ending in a filled output panel and example card (d12-s051).
- Weighted criterion tiles on a track behind an entry gate (d03-s017).

## Devices used
dv01, dv06, dv13, dv18, dv27

## Provenance
- Source: cards/src/a16.json sha256 bfb51ad5f348955f31cbc56aa5deba1dab8606a37bc877f97d282665edcf8438
- Measures: measures/a16.json sha256 8b993a243a40611e558c746d1407f99b947ae24fb893f9c7c474eb56efe03f1d
- Final ranking: rankings/a16.final.json sha256 c1a72997d8bd878c687bb97e1fa930948d5c929ee2661bc5f7d8f164280ed494
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
