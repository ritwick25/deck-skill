# Convergence hub

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a36 | f07 | hub-spoke | v1 |

## Use when
- Many sources, lanes or cases must visibly resolve into one shared element, a contract, a standard or a platform.
- The argument runs from inputs through one shared point to outcomes, so every figure on the right has a visible source path.
- Reuse is the claim: several consumers or capabilities wire into one foundation built once.

## Avoid when
- The parts sit around a core with no direction of flow: use a34 hub-and-spoke.
- The stages repeat in a closed cycle: use a35 lifecycle-loop.

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 3% (2 to 4) | 4% (1 to 6) | 94% (92 to 97) | 8% (6 to 11) |
| feeders | 4% (3 to 4) | 14% (10 to 28) | 92% (29 to 93) | 74% (13 to 80) |
| hub | 32% (4 to 38) | 19% (13 to 32) | 34% (8 to 92) | 49% (25 to 77) |
| readout | 24% (4 to 67) | 20% (10 to 49) | 73% (29 to 93) | 65% (26 to 81) |
| support | 3% (3 to 3) | 19% (19 to 19) | 93% (93 to 93) | 61% (61 to 61) |

## Components
- Feeder cards, lanes or source groups, all one size, set in a row or a column.
- One shared element they converge on: a hub disc per row, a nested core, a locked contract card or a full-width band.
- Arrows or spokes from every feeder that land on the shared element.
- Optional readout of use cases, proof figures or detail cards on the far side of the shared element.
- Optional preconditions hung off the flow on a bracket or a chain.
- Icons per slide 12 (7 to 17), connectors per slide 6 (0 to 17).

## Type roles
| Role | Size |
|---|---|
| title | 27 pt (21 to 32) |
| section-label | 9 pt (8.5 to 10) |
| card-heading | 9 pt (8 to 11.75) |
| label | 8.5 pt (8 to 12) |
| body | 8.75 pt (8 to 12) |
| numeral | 16 pt (12 to 22.5) |

## Density
Content words 157 (113 to 297) over 5 exemplars. Title words 9 (3 to 10). Feeder zone width 92% (29 to 93) of the canvas.

## Word budget
Word budget 200 pooled and 200 on the wide canvas, where every exemplar sits, under the 250 ceiling. Advisory floor 140.

## Device notes
- Every feeder sends its own arrow or spoke, and each one lands on the shared element, so convergence is drawn rather than implied.
- The shared element is set apart from the feeders by form, a disc among cards, a full-width band under a card row, a nested panel or a locked card, never by color alone.
- In row-lane variants each row runs sources, hub disc, use cases and figures left to right, so one row reads as one argument.
- Readout figures sit in their own column or row beyond the shared element, split by hairlines, and never inside the feeders.

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| no-footer | Wordmark, confidentiality line, page number, vendor mark or a foot decision band, 4 flagged. | No foot chrome, a decision line moves to speaker notes. | The flow can run to the bottom margin. |
| shadow | Soft outer shadows on feeder, contract, detail and logo cards, 3 flagged. | Hairline outline, at most a 1 px shadow. | No change to geometry. |
| 8pt-floor | Source sublabels, an owner tag and a page number below the floor, 3 flagged. | Every run at or above 8 pt. | Feeder cards widen or their captions cut to two words, so fewer feeders fit per row. |
| flat-fill | A gradient left edge bar and a gradient foot band, 2 flagged. | Remove the bar and the band, a surviving band takes a flat tint. | None on the flow. |
| word-budget | More use cases per lane and a benefit row that restates the band, 2 flagged. | Two use cases per lane, restating rows cut, within the word budget. | The readout shrinks to one row or column. |
| left-accent | Brand left bars on every flank card that encode no state, 1 flagged. | Hairline outline on the flank cards. | None on layout. |
| no-subtitle | A subtitle under the title, 1 flagged. | Delete it, the locked card or band already states the mechanism. | The flow moves up into the freed band. |
| glyphs | An en dash in a use case line, 1 flagged. | A colon. | None on layout. |
| first-person | A second person phrase in a benefit card, 1 flagged. | A plain statement about the owner. | None on layout. |
| other | Partner, retailer and vendor logos, a named customer beside a figure, figures with no baseline, 3 flagged. | Generic source labels or category chips, every figure labelled delivered or targeted with its baseline. | Feeder tiles lose their logo rows and become shorter, figures gain a qualifier line. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d01-s111 | refs/views/d01-s111.jpg | row lanes run source cards into a hub disc, then use cases and proof figures, one lane tinted in focus |
| d02-s008 | refs/views/d02-s008.jpg | capability cards on both flanks wire by spokes into a nested core around a numbered stack |
| d03-s024 | refs/views/d03-s024.jpg | two input lanes meet at a swap disc and land on one locked contract card |
| d04-s008 | refs/views/d04-s008.jpg | elbow arrows funnel source groups into a hub disc per row that reads across to figures |
| d18-s009 | refs/views/d18-s009.jpg | a short arrow from each of four source cards lands on one full-width shared band |

## Anti-exemplars
None.

## Variants
- Row lanes with one lane tinted in focus, shown by d01-s111.
- Nested core fed from both flanks by spokes, shown by d02-s008.
- Two lanes through a swap disc into a locked card, shown by d03-s024.
- Hub disc per row with a figure column, shown by d04-s008.
- Card row arrowing into one full-width band, shown by d18-s009.

## Devices used
dv21, dv18, dv08, dv33

## Provenance
- Source: cards/src/a36.json sha256 7c7415088f3fbf38b65cf522c6aa97a9f35f9f42e1d4ce5028a2927fee3f646b
- Measures: measures/a36.json sha256 33f58389956e0c48869ddaf3e46d3b26e990621850920d675a5bef80eb382eee
- Final ranking: rankings/a36.final.json sha256 49bab218c1a6aa448b5bddf2016df2f72b465ce4ff85c97b60e42af993446916
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
