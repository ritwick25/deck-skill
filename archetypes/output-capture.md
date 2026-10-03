# Output capture

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a45 | f10 | claim-proof | v1 |

## Use when
- The proof is a real deliverable the solution produced, a report page, a table, a dashboard or a letter, and the reader should be able to inspect it.
- The same generated output exists in parallel forms for different recipients or markets and the comparison of the forms is the point.
- Sample outputs kept as evidence in an appendix behind a claim made earlier in the deck.

## Avoid when
- The point is the live product and how it is used, not what it produced: use product-screen (a44).
- The rows and columns of the output are the argument and must be read cell by cell: rebuild them as reference-table (a33).
- Only the headline numbers of the output matter: lift them out as headline-figures (a41).
- The output must be traced from input to result with payloads at each hop: use worked-example (a18).

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 2% (2 to 2) | 0% (0 to 0) | 97% (97 to 97) | 10% (10 to 10) |
| capture | 6% (0 to 11) | 5% (1 to 14) | 93% (85 to 99) | 86% (77 to 97) |

## Components
- One raster capture of the deliverable, or a row of page captures side by side. Captures per slide 1 (1 to 3).
- A title band above the capture on the exemplars that carry one, otherwise the captured page's own title stands in for it.
- An optional takeaway band at the foot of a captured report page, inside the raster, stating how to read it.
- No live annotation over the capture. Live text shapes per slide 0 (0 to 1).

## Type roles
| Role | Size |
|---|---|
| title | 29.25 pt (29.25 to 29.25), measured on the exemplars whose title is live text |

## Density
Live text is almost nil, the words sit inside the raster where a word count cannot see them. Live content words 0 (0 to 2). The capture takes 93% (85 to 99) of the canvas width and 86% (77 to 97) of its height.

## Word budget
Word budget 10 live content words on this canvas, advisory floor 0, hard ceiling 250. Captured words count against the ceiling once the page is cropped or rebuilt, so crop to the rows that carry the claim.

## Device notes
- The capture is shown whole and unannotated, the reader is trusted to inspect it (d02-s025, d12-s037, d10-s006, d10-s007, d02-s018).
- Captured text renders far below the type floor at slide scale on 4 exemplars, so the capture reads as texture until cropped (d02-s025, d10-s006, d10-s007, d02-s018).
- A short label title sits over a wide product output view, with a corner block beside it (d10-s006, d10-s007).
- A home icon at top left returns to the main flow, marking the slide as a drill-down or appendix page (d02-s025, d02-s018).

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| other | A raster of another slide or page stands in for the slide, with a label title or none, on 5 exemplars. | Add one claim title of at most 14 words naming what the output shows, up to 3 keywords in the brand color, and rebuild a captured slide natively where its text must stay live. | A title band always sits above the capture, which shortens the capture by one title band height. |
| 8pt-floor | Captured text reads under the floor at slide scale on 4 exemplars. | Crop each capture to the header and the first rows or one chart and scale it up until its smallest text clears 8 pt. | The stage shows a cropped region at reading size, and parallel pages become parallel crops of the same region. |
| no-footer | Confidentiality lines, page counters, document footers and a foot takeaway band appear on 3 exemplars. | Crop foot chrome out of the capture and move a takeaway sentence into the title claim. | The capture can run to the bottom margin. |
| left-accent | A colored corner block beside the title encodes no state on 2 exemplars. | Drop the block and start the title at the content margin. | None beyond the title inset. |
| no-subtitle | A captured base line sits under the captured title on 1 exemplar. | Move the base into a source chip beside the capture. | No second line under the title. |
| shadow | Soft card and band shadows inside a captured report page on 1 exemplar. | Hairline borders with at most a 1 px shadow when the page is rebuilt. | None for the layout. |
| first-person | A heading and a column header address the reader directly on 1 exemplar. | Restate in neutral third person. | None for the layout. |
| glyphs | Column headers trail off in ellipses on 1 exemplar. | End each header as a plain label. | None for the layout. |
| word-budget | Three page captures hold several hundred words on 1 exemplar. | Crop to the rows that carry the comparison and keep the slide under 250 words. | Parallel pages become parallel crops of equal height. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d02-s025 | greeked/d02/s025.png | A whole report page captured as evidence, six small multiples isolating the one falling attribute. |
| d10-s006 | greeked/d10/s006.png | One dashboard output view, tiles over charts, shows what the tool produces at a glance. |
| d12-s037 | greeked/d12/s037.png | A captured three-column table of condition, output and impact read row by row. |
| d10-s007 | greeked/d10/s007.png | A triage table output whose status pills do the color work, framed under a short title. |
| d02-s018 | greeked/d02/s018.png | Three parallel page captures of one generated document, one per market, invite comparison. |

## Anti-exemplars
None.

## Variants
- Captured report page: a whole slide or page with its chart grid and takeaway band as one raster (d02-s025).
- Captured table: one pasted table filling the canvas (d12-s037).
- Titled output view: a short title over a wide dashboard or issue list capture (d10-s006, d10-s007).
- Parallel pages: portrait captures of one output for different recipients in a row (d02-s018).

## Devices used
dv39

## Provenance
- Source: cards/src/a45.json sha256 0648486a89ed8f6616f3403bddd46b344b872d715572f1d43df42a732db85192
- Measures: measures/a45.json sha256 da42f494ecc9333c859364fa46b4c5b76873f47cb62ab2ee6af6360795b7af27
- Final ranking: rankings/a45.final.json sha256 cfeecb46df2721cf87c0a615098a14eb5173595412df9503d060c01e2991a687
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
