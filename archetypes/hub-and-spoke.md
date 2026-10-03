# Hub and spoke

| Archetype | Family | Message shape | Taxonomy |
|---|---|---|---|
| a34 | f07 | hub-spoke | v1 |

## Use when
- One core, a platform, a team or an idea, and a set of peer parts that all depend on it, where the audience must see the dependency at a glance.
- The parts are parallel and unordered, so position around the core carries no sequence.
- The same wheel will recur on later slides as a map, with one part lit or expanded per slide.

## Avoid when
- The parts are steps that repeat in order around the center: use a35 lifecycle-loop.
- Many sources or cases flow into one shared element and read out to outcomes: use a36 convergence-hub.

## Zones
| Zone | x | y | w | h |
|---|---|---|---|---|
| title | 3% (2 to 3) | 3% (1 to 6) | 95% (94 to 98) | 13% (6 to 15) |
| wheel | 15% (3 to 26) | 19% (15 to 30) | 49% (43 to 81) | 63% (49 to 79) |
| satellite-text | 3% (3 to 3) | 16% (15 to 18) | 79% (64 to 94) | 76% (73 to 78) |
| base | 14% (14 to 14) | 54% (54 to 54) | 71% (71 to 71) | 40% (40 to 40) |
| side-rail | 63% (54 to 72) | 23% (17 to 28) | 34% (27 to 41) | 71% (65 to 76) |

## Components
- One core drawn as a disc, a quartered disc, a hub mark or a set of type, sitting at the geometric center of the wheel.
- Peer parts arranged around the core as wedges, quadrant tiles, ring roundels, hexagon triangles or interlocking lobes, all one size.
- Optional satellite text: a short heading plus one line beside each part.
- Optional base: foundation cards or bands seated directly under the wheel.
- Optional side rail of proof figures or a sample gallery, split from the wheel by a hairline.
- Icons per slide 7 (0 to 41), connectors per slide 0 (0 to 7).

## Type roles
| Role | Size |
|---|---|
| title | 28 pt (26.75 to 32) |
| card-heading | 13.5 pt (10.5 to 18.75) |
| label | 11 pt (10 to 13.25) |
| body | 12.75 pt (12 to 13.25) |
| section-label | 11 pt (10 to 12) |
| numeral | 37.25 pt (37.25 to 37.25) |

## Density
Content words 94 (25 to 175) over 5 exemplars. Title words 8 (3 to 13). Wheel width 49% (43 to 81) of the canvas.

## Word budget
Word budget 100 pooled, 140 on the standard canvas and 90 on the wide canvas, under the 250 ceiling. Advisory floor 60.

## Device notes
- The core contrasts with its parts by hue or by tint, a lime disc against dark tiles, an orange disc inside navy wedges, a white disc inside saturated lobes, so the eye lands on the center first.
- Every part has the same shape and size as its peers, which is what makes them read as equals rather than as a sequence.
- Where parts carry explanation, the text sits outside the wheel beside its own part, never inside the shape, and mirrors left and right.
- When a side rail is present it is split from the wheel by a hairline or white space and holds a different kind of content, figures or samples, not more parts.

## Translation under the house rules
| Rule | Reference | House | Consequence |
|---|---|---|---|
| light-bg | Dark navy base bars under the wheel on one exemplar, 1 flagged in the top set. | Light tint bars with navy ink on a light ground. | The base keeps its position and height, only its fill and ink change. |
| flat-fill | Gradient crescents, gradient stat bars and textured pipes, 2 flagged. | Flat brand fills, or brand and tint alternating across the parts. | Lobes need a white gap or a hairline to separate them once the gradient is gone. |
| shadow | Soft shadows under cards, lobes and the hub, 2 flagged. | Hairline outline, at most a 1 px shadow. | No change to geometry, the edge carries the separation. |
| first-person | Titles and satellite bodies written as we, our and you, 3 flagged. | Third person claims with role nouns such as the client and the vendor. | Satellite lines often shorten, which frees width for the wheel. |
| no-footer | Page number, logo lockup and folio at the foot, 3 flagged. | No foot chrome at all. | The wheel and satellites may extend into the reclaimed foot band. |
| glyphs | En dashes in bodies, a leading ellipsis and a smart apostrophe in titles, 3 flagged. | Commas, colons or full stops, straight apostrophes, no leading ellipsis. | None on layout. |
| word-budget | Satellite paragraphs and three bullets per lobe, 2 flagged. | One heading plus one line per part, detail moved to notes, within the word budget. | Satellite text blocks shrink to two lines, so the wheel can grow. |
| left-accent | Twin brand bars flush to both edges of the title band that encode no state, 1 flagged. | Remove the bars. | The title band runs clean to the margins. |
| no-subtitle | A two line subtitle under the title, 1 flagged. | Delete the subtitle, the title carries the one claim. | The wheel moves up into the freed band. |
| other | Vendor logos, a logo raster as the hub, illegible thumbnails and tiles stretched around one label, 5 flagged. | Tools named by category, the hub set as the claim noun in type, a named list in place of thumbnails, tiles sized to their content. | Hub and rail carry meaning rather than decoration, and tile height drops to fit content. |

## Exemplars
| Slide | View | Why |
|---|---|---|
| d04-s015 | greeked/d04/s015.png | half wheel of use case wedges fanning from one platform core, foundation cards seated under the hub |
| d09-s025 | greeked/d09/s025.png | four tiles meeting at a quartered contrasting disc, reusable as a map on later slides |
| d12-s021 | greeked/d12/s021.png | ring roundels strung on an arc around a central mark, heading and line mirrored left and right |
| d16-s005 | greeked/d16/s005.png | three interlocking lobes around a hub disc beside a hairline split rail of three figures |
| d03-s047 | greeked/d03/s047.png | six flat triangles tiled into a hexagon around a contrasting value disc |

## Anti-exemplars
None.

## Variants
- Half wheel fan over a foundation, shown by d04-s015.
- Quartered hub with four tiles, shown by d09-s025.
- Roundel arc with mirrored satellites, shown by d12-s021.
- Interlocking lobes beside a figure rail, shown by d16-s005.
- Wedge hexagon beside a sample gallery, shown by d03-s047.

## Devices used
dv19, dv20, dv08, dv33

## Provenance
- Source: cards/src/a34.json sha256 0c29096af87f3c318cb3844e77bd580fdcb0f3235f9f56240b42049c3c4db33b
- Measures: measures/a34.json sha256 cb6a1dd4a24f98369b8e76ade929f630175c207893f53a498ce6ea67ca27f614
- Final ranking: rankings/a34.final.json sha256 c7a7f9bc6d7129c8ea20321351bc1a5ab7e8022e5050e0784b5c1dd7504d1675
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Taxonomy: taxonomy/v1.json sha256 6f40a44386d2e633aa1808cc786483039990b5fec9b80c856b53211a00836924
- Claims removed: 0
- Renderer: render_card@1
