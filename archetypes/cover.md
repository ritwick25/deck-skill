# Cover

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a01 | f01 | title | v1 |

## Use when
- The deck opens and has to name the engagement, the parties and the date in one title stack before any argument starts.
- A working session opens with the people in the room, so a row of portrait discs with name and role replaces the hero visual.

## Avoid when
- The page marks a part boundary inside the deck, so use section-divider (a03) instead.
- The page signs off with contact detail or a last claim, so use closing (a04) instead.
- The page has to list the parts of the session in order, so use agenda (a02) instead.

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 7% (3 to 32) | 16% (0 to 23) | 44% (30 to 92) | 56% (30 to 100) |
| logo-lockup | 48% (18 to 78) | 8% (7 to 10) | 16% (14 to 18) | 7% (7 to 8) |
| hero-visual | 37% (0 to 45) | 14% (0 to 14) | 62% (55 to 100) | 86% (83 to 100) |
| attendee-row | 5% (5 to 5), one exemplar | 48% (48 to 48) | 60% (60 to 60) | 37% (37 to 37) |

## Components
- One flush-left title stack: an optional kicker, the title, one label line and the date, all on one left edge.
- A logo lockup of the party marks, split by a thin vertical rule, set above the title stack or at top right.
- One large visual that balances the stack on the right: a vector illustration of the subject, a flat brand shape, or a native diagram.
- Optional attendee row: portrait discs in an even row, each over a bold name and a short role line, split by hairlines.
- Content pictures per slide 3 (3 to 6), text shapes 4 (3 to 7).

## Type roles
| Role | Size |
|---|---|
| title | 29.25 pt (28 to 37) |
| kicker | 10.5 pt (10 to 11) |
| label | 17.25 pt (12.5 to 18.75) |
| caption | 12 pt (10 to 14) |

## Density
Sparse by design. Content words 19 (9 to 34) per slide, title words 4 (3 to 8). The visual carries the page and the stack stays one block.

## Word budget
Word budget 30 with an advisory floor of 10, under the hard ceiling of 250. The title stays within 14 words.

## Device notes
- The title stack sits flush left against one large visual that fills the right side of the canvas (d18-s001, d13-s001, d11-s001, d17-s001).
- A tall brand bar runs down the left edge of the title stack and encodes no state (d18-s001, d11-s001, d13-s001).
- The party marks pair up in one lockup split by a thin rule (d11-s001, d13-s001, d01-s001).
- The date closes the stack as its last line, set small under the title (d18-s001, d13-s001, d11-s001, d17-s001).

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| flat-fill | Gradient waves, washes and panels behind the visual, on 4 top exemplars. | One flat brand-tint shape of the same silhouette, or the plain light ground. | The right side reads as a single flat field, so the visual must carry content rather than mood. |
| left-accent | A tall brand bar binds the title stack on 3 top exemplars. | No bar. Shared left alignment alone groups kicker, title, label and date. | The stack needs a strict type ladder and even spacing, since no rule holds it together. |
| light-bg | Raster photo fields cover the canvas behind or beside the stack on 2 top exemplars. | Light ground, with any visual held to the right side and drawn as vector. | The title zone keeps full contrast and the visual zone shrinks toward the right side. |
| no-subtitle | An italic promise or proposal line under the title on 4 top exemplars. | The promise folds into the title as its one claim, or it goes. | The title carries the claim, so the stack loses a line and the date moves up. |
| no-footer | A web address line under the date on 2 top exemplars. | No web line, no footer, no page number. | The stack ends on the date. |
| shadow | A soft shadow under the diagonal band on 1 top exemplar. | Hairlines plus at most a 1 px shadow. | Any band reads flat and sits behind the visual without lift. |
| other | Raster product photos, generated illustrations and stock imagery carry the visual zone on 3 top exemplars. | A native vector diagram of the subject, a plain screen frame with a labelled grid, or empty ground. | The visual has to state the thesis, not decorate it, or the right side stays ground. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d18-s001 | greeked/d18/s001.png | Strict type ladder in one left block, kicker over title over date, balanced by one shape on the right. |
| d01-s001 | greeked/d01/s001.png | Welcome variant: an even row of portrait discs, each over a bold name and a role line, split by dashed hairlines. |
| d11-s001 | greeked/d11/s001.png | Compact lockup of two marks split by a thin rule, set above a short title stack. |
| d13-s001 | greeked/d13/s001.png | Lockup, two-line title, label line and date all on one left edge against a single large visual. |
| d17-s001 | greeked/d17/s001.png | The visual states the thesis: a demo screen points into the grid of parts it hides. |

## Anti-exemplars
| Slide | View | Failure |
|---|---|---|
| d15-s001 | greeked/d15/s001.png | Dark ground, and the right half is empty air behind a decorative hexagon that carries no content. |
| d08-s001 | greeked/d08/s001.png | A full-bleed packaging photo on a dark ground carries the slide, and a subtitle plus a web line add chrome. |
| d14-s001 | greeked/d14/s001.png | A dark full-bleed brand photograph under a generic ruled stack, with a subtitle, a footer line and a banned glyph. |

## Variants
- Title stack beside hero visual, the default (d13-s001).
- Thesis cover, where the visual argues the deck's gap in one picture (d17-s001).
- Welcome cover, where an attendee row of portrait discs replaces the visual (d01-s001).

## Devices used
dv53, dv56

## Provenance
- Source: cards/src/a01.json sha256 92bf98af29a864bc7d19e4892e2579d3e98a8063187e472af41761228d510ba3
- Measures: measures/a01.json sha256 7d6b1ee7a9c068f78a2b9d52bbb709f6a8a0899aa35a039f7a137e8f8c20237f
- Final ranking: rankings/a01.final.json sha256 349fe10e5c91f3ae54a6e1ad6d83fd1e97386b6d31f73b411d08a6d07d4d620e
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
