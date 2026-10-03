# The ask

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a12 | f02 | closing | v1 |

## Use when
- The meeting must end in a commitment, and the decisions asked of the audience can each be named by one verb, endorse, nominate, assign or agree.
- The decisions have dated consequences, so a short rail of milestones can show what the audience will see and when.
- Part of the commitment is made now and part is decided later at a gate, so the page can separate what is committed today from what the gate decides.

## Avoid when
- The page signs off with no request, use closing (a04) instead.
- The request is price and terms, use commercials (a42) instead.
- The phases of delivery are shown with no decision asked, use phased-roadmap (a38) instead.
- The whole proposal must be compressed onto one page with the ask as one cell among several, use executive-summary (a28) instead.

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 4% (4 to 5) | 3% (2 to 4) | 91% (90 to 93) | 9% (9 to 10) |
| decision-cards | 4% (3 to 4) | 18% (15 to 21) | 92% (92 to 93) | 45% (38 to 51) |
| gate-panel | 31% (31 to 31) | 21% (21 to 21) | 35% (35 to 35) | 51% (51 to 51) |
| milestone-rail | 3% (3 to 3) | 58% (58 to 58) | 92% (92 to 92) | 20% (20 to 20) |
| commit-band | 4% (4 to 4) | 78% (75 to 81) | 90% (89 to 92) | 12% (8 to 17) |

## Components
- Decision cards or panels in a repeat of 3 (2 to 4), each 23% (19 to 27) of the slide width and 45% (38 to 51) of its height.
- Icons per slide 6 (0 to 12), at most one per decision card and one at the next-step label.
- Connectors per slide 1 (0 to 1), a single dated rail where the milestones are shown.

## Type roles
| Role | Size |
|---|---|
| title | 23 pt (21 to 25) |
| card-heading | 15.5 pt (12 to 19) |
| section-label | 12 pt (10 to 14) |
| body | 11 pt (10 to 12) |
| label | 10 pt (10 to 10) |

## Density
Text shapes per slide 29 (25 to 32). The decision zone fills 45% (38 to 51) of the slide height, and the commit band starts at 78% (75 to 81) from the top.

## Word budget
Word budget 210, the upper quartile of the top exemplars capped at 250. Content words on the top exemplars run 204 (202 to 206).

## Device notes
- Peer cards run across the width, each a short caps kicker over a bold heading and a short rationale, so every decision reads as one card (d01-s053, d12-s045).
- A short drawn link between neighbouring cards, chevrons or small arrows, makes the decisions read as a sequence (d01-s053, d12-s045).
- A full-width band at the foot names the immediate next step or what is committed now, split into cells by hairlines or led by a label tab (d01-s053, d12-s045).

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| 8pt-floor | Panel bullets and band kickers set below the floor, on 1 top exemplar. | Bullets trimmed to the strongest lines at the floor or above | Each panel holds fewer lines, so the cards shorten. |
| first-person | A section label and band kickers that speak as we or address the reader, on 2 top exemplars. | Neutral noun phrases, outcomes by date, committed now, aligned at the gate | None on geometry. |
| flat-fill | Multi-stop gradient edge and foot bars, on 1 top exemplar. | Removed rather than flattened | The freed foot returns to the commit band. |
| glyphs | A dash after the title keyword, typed arrows and bullet characters, on 2 top exemplars. | A colon after the keyword, drawn arrows and plain indents | None on geometry. |
| left-accent | A gradient left edge bar, colored top bars on every panel and a multicolour top stripe, on 2 top exemplars. | No accent bar, and the kicker carries phase identity | Title and cards start at the shared left margin and top margin. |
| light-bg | A dark navy slide ground, on 1 top exemplar. | A white ground. Panels that sat reversed on the navy ground become solid near-black or brand panels with text in the fill's ON_FILL role, or white cards with a hairline, never pale tint panels. | None on geometry. The ask takes its weight from one solid panel rather than from the ground. |
| no-footer | Confidentiality lines, client wordmarks, page numbers and a foot strip, on 2 top exemplars. | No footer, page number, confidentiality line or foot strip | The commit band becomes the lowest element and sits on the bottom margin. |
| no-subtitle | A lead sentence under the title, on 2 top exemplars. | Its claim folds into the title | The cards move up into the freed band. |
| other | A client name in the top corner, on 1 top exemplar. | Removed, the audience is named by role only | None on geometry. |
| shadow | A soft shadow under the next-step bar, on 1 top exemplar. | A hairline with at most a 1 px shadow | None on geometry. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d01-s053 | refs/views/d01-s053.jpg | Numbered verb-led decision cards chained by chevrons over a dated milestone rail and a next-step bar. |
| d12-s045 | refs/views/d12-s045.jpg | Two commitment panels around a gate panel of review criteria, over a band splitting now from later. |

## Anti-exemplars
None.

## Variants
- Verb-led decision cards over a dated milestone rail and a next-step bar (d01-s053).
- Commitment panels around a gate panel over a committed-now band (d12-s045).

## Devices used
dv08, dv24

## Provenance
- Source: cards/src/a12.json sha256 817087765e61e0f2d604361e31d48921708e4f9293ef7e1637c7ec83157835e4
- Measures: measures/a12.json sha256 fd67b0eca5642dfa8c4a96dd718c1e5a6efd0cd9475c9934f093b456b663d7e2
- Final ranking: rankings/a12.final.json sha256 27dea75a02f620d3f70f3b7645a94df729e1dafc4b38c24aad968fa529cd539a
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
