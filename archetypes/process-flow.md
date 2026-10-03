# Process flow

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a13 | f03 | sequence | v1 |

## Use when
- The audience must believe the proposed solution runs end to end, so every step is shown in reading order with what happens there.
- Each step has a check, control or output that can sit under it, so the proof travels with the step rather than in a closing paragraph.
- One step or one traced record deserves a closer look, and a lower panel can expand it without breaking the chain above.

## Avoid when
- The steps are how the work runs today and the point is where it breaks, use as-is-process (a14) instead.
- The mechanism is best framed by what goes in and what comes out around one method panel, use input-process-output (a15) instead.
- Cases branch on rules into different actions, use decision-logic (a16) instead.
- Each lane is a role handing work to the next, use swimlane-handoff (a17) instead.
- The steps are phases delivered over months, use phased-roadmap (a38) instead.

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 4% (3 to 4) | 4% (2 to 6) | 93% (92 to 95) | 9% (4 to 13) |
| context-band | 4% (4 to 4) | 16% (13 to 19) | 93% (93 to 93) | 11% (7 to 15) |
| stage-chain | 4% (0 to 4) | 22% (8 to 34) | 93% (75 to 100) | 25% (13 to 90) |
| stage-detail | 4% (0 to 4) | 49% (42 to 49) | 91% (48 to 92) | 17% (15 to 21) |
| proof-panel | 4% (4 to 6) | 50% (42 to 69) | 93% (90 to 93) | 41% (22 to 45) |
| result-card | 79% (79 to 79) | 22% (22 to 22) | 18% (18 to 18) | 69% (69 to 69) |

## Components
- Stage cards, chevrons or spine boxes in a repeat of 5 (3 to 12), each 14% (11 to 17) of the slide width and 13% (3 to 21) of its height.
- Connectors per slide 4 (0 to 6), short arrows that start on one stage and land on the next, or a spine that fans out into lanes and rejoins.
- Icons per slide 9 (4 to 11), one per stage heading or one per system in the context band.
- Screens or insets per slide 0 (0 to 2), used only where a stage is proven by a miniature of its output.
- Optional chips under the stages naming the control that fires at each step, and an optional thin left rail naming each row of a vertical flow.

## Type roles
| Role | Size |
|---|---|
| title | 21 pt (16 to 32) |
| section-label | 8 pt (6.75 to 12) |
| card-heading | 10 pt (8 to 13) |
| body | 8 pt (6.75 to 10) |
| label | 8 pt (6.75 to 10) |
| caption | 8 pt (6.75 to 8.5) |

## Density
Text shapes per slide 53 (39 to 68). The stage chain fills 93% (75 to 100) of the slide width and 25% (13 to 90) of its height.

## Word budget
Word budget 250, the upper quartile of the top exemplars capped at 250. Content words on the top exemplars run 210 (153 to 384), so the busiest exemplars are cut before they are borrowed.

## Device notes
- Stages carry a number in a disc or a solid tab header, so the order reads without arrows (d03-s018, d15-s021).
- Short arrows start on one stage card and land on the next, and on one exemplar a bold verb captions each arrow (d15-s021, d18-s014, d12-s046).
- A band above the chain names what the flow answers or the systems it reads and writes, at 16% (13 to 19) of the slide height (d01-s042, d15-s021).
- A lower panel proves the flow with the measures it is held to, one traced record, or a problem and approach row, at 50% (42 to 69) of the slide height (d01-s042, d15-s021, d18-s014).
- Each stage card closes on a small chip naming its control or output (d15-s021, d18-s014).

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| 8pt-floor | Stage, box and stat labels set below the floor, on 2 top exemplars. | Every run at 8 pt or above. | Spine boxes widen into empty space, detail lines move to the notes, and a stat strip drops to two stats. |
| emoji | Check and fisheye characters used as list marks, on 1 top exemplar. | Vector icons or plain hairline rows. | None on geometry. |
| first-person | A lead or rail heading that speaks as we, on 2 top exemplars. | Neutral headings such as Approach. | None on geometry. |
| flat-fill | Multi-stop gradient edge and foot bars, on 1 top exemplar. | Removed rather than flattened. | The freed foot returns to the proof panel. |
| glyphs | Dashes in titles and ranges and arrow glyphs inside mapping lines, on 3 top exemplars. | A colon in the title and the word to in ranges and mappings. | None on geometry. |
| left-accent | Gradient left edge bars and full-height bars opening columns, on 2 top exemplars. | A hairline above each heading, and no accent bar unless it encodes a state that can change. | Title and stages start at the shared left margin. |
| no-footer | Page numbers, confidentiality lines, wordmarks, owner strips and gradient foot bands, on 5 top exemplars. | No footer, page number, confidentiality line or foot summary band, with owner and dependency in the notes. | The proof panel or the stage chain becomes the lowest element and sits on the bottom margin. |
| no-subtitle | A sentence or lead paragraph under the title, on 3 top exemplars. | Fold it into the title claim or the notes. | The context band or the chain starts directly under the title. |
| other | Letterspaced kickers, a client name in the corner, raster collages, lane identity hues and titles running to 16 words against a median of 7 (min 6), on 3 top exemplars. | One claim of 14 words or fewer with up to 3 keywords in the brand color, native thumbnail shapes for any output, and house blue, ink and gray with names carrying lane identity. | Insets redraw as native shapes at the same footprint. |
| shadow | Soft blurred shadows on stage and tooling cards, on 2 top exemplars. | Hairline outlines plus at most a 1 px shadow. | None on geometry. |
| word-budget | Content words above the archetype budget, on 3 top exemplars. | Hold the budget of 250, never above 250. | Each stage keeps two items at most, and chips that restate their card body are cut. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d01-s042 | greeked/d01/s042.png | A pressure band, a chevron chain with capabilities under each step, and a measures panel stack in three tiers. |
| d03-s018 | greeked/d03/s018.png | Numbered step cards each draw their own small mechanism and close on a filled result card. |
| d15-s021 | greeked/d15/s021.png | Arrow-linked step cards each carry the control that fires at that step in a chip beneath. |
| d18-s014 | greeked/d18/s014.png | Verb-captioned arrows chain the stages, then one failing record is traced to the people who read it. |
| d12-s046 | greeked/d12/s046.png | A spine fans into parallel lanes under one shared band and rejoins, with a rail naming each row. |

## Anti-exemplars
None.

## Variants
- Pressure band over a chevron chain over a measures panel (d01-s042).
- Numbered cards each with a native mini diagram, closed by a filled result card (d03-s018).
- Tab-headed step cards with a control chip under each (d15-s021).
- Verb-captioned stage row over a traced record band (d18-s014).
- Vertical spine fanning into lanes under a shared band, with a row rail (d12-s046).

## Devices used
dv01, dv06, dv07, dv08, dv11, dv12, dv15, dv52

## Provenance
- Source: cards/src/a13.json sha256 699c88ced4dcad99dbb12ad895b9e58a929b2b68728158a09880ffa7082d5a67
- Measures: measures/a13.json sha256 712de75ba5a33881834505da86576a11d36cdd3e5dec9f2afc0fa085b3434a3a
- Final ranking: rankings/a13.final.json sha256 e3c5d545b9d4338b550182fdd9770d8a8e38b807fbd34bb85e1449115dfa6443
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
