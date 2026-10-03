# Design system

## Grid and type

### Canvases
Two canvases carry the content set. The wide canvas (w13) holds 216 content slides and the compact canvas (w10) holds 137, out of 354 content slides across 18 decks. One portrait A4 deck appears and is single-deck, so it sets no rule. Build on the wide canvas by default. Treat the compact canvas as a sibling with its own figures: every inch value below is quoted per canvas and is never carried across.

### Margins on the wide canvas
Across 216 wide slides the left margin is 0.48 in (0.00 to 0.55) and the right margin is 0.42 in (0.00 to 0.83). The top margin is 0.14 in (0.00 to 0.55) because the title sits close to the top edge. The bottom margin is 0.58 in (0.00 to 1.74). House rendering: the bottom margin stays empty space. No footer, page number or foot band fills it.

### Margins on the compact canvas
Across 137 compact slides the left margin is 0.22 in (0.00 to 0.73) and the right margin is 0.17 in (0.00 to 0.53). The top margin is 0.08 in (0.00 to 0.34) and the bottom margin is 0.27 in (0.00 to 2.10). The compact references run tighter to the edge than the wide ones. Keep the left and right margins equal so the content block centers.

### The title box
Every content slide carries a title (100%). On the wide canvas the title box starts at x 0.48 in (0.18 to 4.01) and y 0.23 in (0.11 to 3.51), spans 12.40 in (1.71 to 13.07) and stands 0.47 in (0.32 to 1.92) tall, across 216 slides. Titles hold 1 (1 to 5) lines. The title box shares its left edge with the left margin, so the title and the content block align on one line. House rendering: one claim on one line of at most 14 words.

### The title box on the compact canvas
On the compact canvas the title box starts at x 0.28 in (0.07 to 0.73) and y 0.08 in (0.00 to 0.98), spans 9.44 in (2.13 to 12.77) and stands 0.51 in (0.27 to 1.01) tall, across 137 slides. Two-tone titles, with keywords of the claim set in the brand color, appear on 39% of wide slides and 12% of compact slides. House rendering: up to 3 keywords in the brand color, titles only.

### Columns and gutters
Left edges of text and shapes cluster into peaks. On the wide canvas 6 peaks stand out and the best fit is 3 columns of 3.48 in with a gutter of 1.00 in, across a content width of 12.44 in and a fit residual of 0.52 in. The tallest peak sits at 0.48 in, which is the margin line. On the compact canvas 11 peaks stand out and the best fit is 5 columns of 1.74 in with a gutter of 0.23 in, across 9.61 in.

### Card rows
A row of same-size cards on the wide canvas sizes by count. Two cards run 1.93 in (0.80 to 6.28) wide, three run 2.64 in (0.80 to 4.19), four run 1.88 in (0.85 to 3.06) and five run 1.87 in (0.82 to 2.39). The gap inside a row is 0.23 in (0.00 to 9.77) across 401 rows. Snap every row to the column grid so card edges land on peaks.

### Vertical rhythm
The gap from the title to the first content zone is 0.08 in (0.00 to 1.29) on the wide canvas and 0.19 in (0.00 to 0.82) on the compact canvas. The gap between stacked content zones is 0.16 in (0.00 to 4.62) wide, across 1931 gaps, and 0.12 in (0.00 to 4.56) compact. Use the zone gap as the one vertical unit and repeat it, rather than spacing each zone by eye.

### Type scale on the wide canvas
Measured run sizes by role on the wide canvas: title 21 pt (16.5 to 48), card heading 11 pt (5 to 22), section label 10.75 pt (8 to 20), body 9 pt (6 to 16), label 9 pt (5 to 17) and numeral 12 pt (5 to 128). Card headings are set bold on 93% of runs, body on 12%.

### Type scale on the compact canvas
On the compact canvas: title 19.5 pt (8 to 33), card heading 9 pt (5 to 18), section label 9 pt (4 to 14), body 8 pt (4.25 to 12.25), label 8 pt (4 to 18) and numeral 10 pt (6 to 96), across 113 slides with body text. The compact body median sits at the house floor, so the compact scale has no room below body. House rendering: caption, label and legend share the floor size on this canvas and separate by weight and color.

### Step ratios
Ratios between adjacent roles on one slide: title to body 2.33 (1.00 to 4.92) across 307 slides, numeral to card heading 1.09 (0.60 to 8.73), card heading to section label 1.00 (0.50 to 1.88), and label to caption 1.00 (0.57 to 1.60). The references keep a wide jump from title to body and a flat ladder below it. Hold that shape: one large step under the title, then roles separated by weight rather than size.

### Families and weight
One neutral sans family carries 68% of all runs. A monospace family carries 7%, concentrated in footers (80%) and kickers (53%). A serif title face appears on 12% of title runs. Titles are bold on 84% of runs. House rendering: one sans family for every role, and no monospace label above headings or on cards.

### The floor and how often it breaks
The house floor is 8 pt for every run. The references break it on 31% of content slides and in 21% of runs. The compact canvas breaks it on 48% of slides against 20% on the wide canvas. Caption runs sit at 7 pt (4 to 14) on the compact canvas. House rendering: no run below the floor. When a run will not fit at the floor, cut words or widen the box, never shrink the type.

### Roles the house drops
Some measured roles do not survive the house rules. Subtitles appear on 44% of wide slides at 14 pt (9.5 to 18). Footers appear on 10% of slides and page numbers on 16%. Kickers appear on 29% of wide slides. House rendering: no subtitle, no footer, no page number, and no kicker above every card. The title carries the claim alone.

### Provenance
- Source: system/grid-type.json sha256 6c50c4c9f5f01afae2f227a32a6eb4cf05b09ea6a9a57d5a7afb6b5d3b46ed26
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Input: system/grid.measures.json sha256 7270a8c6c7b8b738b6cad914560d71200c5eb6a7fd8a47c96c458f9f2887060d
- Input: system/type.measures.json sha256 3ea498c590146986bd791757f24572ef14031a769366d9171497a9bf67d6ba84
- Renderer: render_card@1

## Color roles

### Background
The ground is white on 93% of 354 content slides and near-white on 7%. Dark, mid-tone, tinted, gradient and picture grounds each measure 0%. The most common ground is FFFFFF. House rendering: a white or near-white ground on every slide.

### Surface and card
A non-white surface appears on 63% of content slides. Surface fills sit at lightness 1.00 (0.90 to 1.00) across 1936 fills, and 55% of them are white. The most common non-white surface is F2F2F2. House rendering: four card treatments, a white card held by a hairline, a light neutral fill with no outline, a solid brand card, and a near-black panel. A brand tint is never the default container.

### Brand and brand tint
Each palette names one brand color, the saturated hue that carries title keywords, header tabs and the active state. A brand tint, a pale wash of the brand, appears on 50% of content slides, 66% wide and 26% compact. Tints sit at lightness 0.94 (0.86 to 0.97) and mix 88% (58 to 97) white into the hue, across 942 fills. 46% of tints derive from the first accent slot. Fills drawn from the theme scheme rather than typed hex make up 46% of colored fills. House rendering: the brand is a solid fill (a band, a header tab, an emphasis card) or the title keywords. A brand tint covers a large background only, never a card, a chip or a small panel, unless the tint encodes a state a legend keys.

### Hairline
Hairlines weigh 0.75 pt (0.25 to 1) across 6922 lines and sit at lightness 0.75 (0.00 to 1.00). A neutral gray carries 66% of them, most often BFBFBF. House rendering: hairlines are the structure, plus at most a 1 px shadow. A boundary that carries meaning holds at least 3.00 against its surface. A decorative divider is exempt.

### Ink tiers
Primary ink sits at lightness 0.11 (0.00 to 1.00) with contrast against white of 17.22 (1.00 to 21.00), across 354 slides. Pure black is the primary ink on 49% of slides, and the most common ink is 000000. A second tier, a slate or dark gray, comes from the dark-two theme slot, as in p3 (44546A) and p5 (4B5960). House rendering: a near-black primary ink, a gray secondary ink, and every text pair at least 4.50, or 3.00 for large text. Two brand text roles derive from the brand: accent-ink, deepened until it clears 4.50 on paper and card, carries title keywords and brand numerals on a light ground; accent-bright, lightened until it clears 3.00 on the near-black and navy fills, carries large brand numerals on a dark band and nothing smaller.

### Accent slots
Decks use 1 (0 to 5) accent slots beyond the brand, across 18 decks. accent1 is in use in 56% of decks, accent2 in 50%, accent3 in 33% and accent6 in 22%. House rendering: the brand, a navy and a gray carry the deck. A further accent is introduced by the deck owner, never by the build, and identity never rides on color alone.

### Status colors
Traffic-light status appears on 2% of content slides. The observed red is F30009, amber FFC000 and green 00B050. The p1 brand (F30009) is the same red as the status red, so on that palette a red mark cannot mean risk. House rendering: status carries a glyph and a word beside the color, and a palette whose brand is a status hue moves status to the glyph.

### Dark surfaces and the house translation
No content slide renders on a dark ground (0%). Dark surfaces inside a slide appear on 14% of content slides, 20% wide, and cover 7% (2 to 67) of the slide area across 51 slides. The most common is 000000. House rendering: the slide ground is always light. Inside it, a near-black panel (ink-deep, ink-strong) carries stats and headers and a solid brand band or card carries emphasis, each with text in the fill's own text role at 4.50 or better, and brand numerals on a dark band in accent-bright. Pastel tint is for large backgrounds only, never the default container.

### Observed palettes p1 to p5
Examples only, never a target. p1: brand F30009, tint FCEFE5, hairline BFBFBF, 91 slides. p2 (single-deck): brand 237C25, tint D3F8CA, hairline E7E7EB. p3: brand 001A70, tint E8EEFC, hairline DDE4F6, on the stock theme accents. p4: brand 024AE4, tint E2F6FD, hairline DCE0E7, across 5 decks. p5 (single-deck): brand 072130, tint FEF0E7.

### Observed palettes p6 to p9
p6: brand 1F36C7, tint FACFCC, hairline BFBFBF. p7 (single-deck): brand 0E4C86, tint CFE2F3, hairline 7F7F7F. p8 (single-deck): brand 0045AC, tint D9F2FC, ink 323F4F. p9: brand 3136C6, tint D4F0FF, hairline ECEFF7. Every palette repeats one shape: a saturated brand, a tint near white, a pale neutral hairline and a near-black ink. Copy the shape, not the hues.

### Provenance
- Source: system/colour-roles.json sha256 ace7461bf372c669e3f8670a8e0adb093175499917268ad627234916f9a23afc
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Input: system/colour.measures.json sha256 28c412a674b398e072edf63acdbeed44a794d73cc283235ed2d187d4f620a8e7
- Renderer: render_card@1

## Shape, icon and imagery

### Cards
Text cards are plain rectangles in 41% of cases and rounded rectangles in 34%, with top-rounded tabs at 6% and ellipses at 10%. Containers that hold other shapes are rounded in 64% of cases and square in 33%. Pick one card preset per deck and use it for every card, then match an accepted card exactly.

### Corner radius
Corner radius on rounded shapes is 0.06 in (0.00 to 0.77) on the wide canvas across 2426 shapes, and 0.05 in (0.00 to 0.85) on the compact canvas. As a preset adjustment it is 0.12 (0.00 to 4.19). A small, fixed radius in inches reads as deliberate. A large adjustment on a small shape turns a card into a pill, which the house refuses.

### Header tabs
A header tab, a filled strip that names the column or zone below it, appears on 21% of content slides. Tabs stand 0.50 in (0.20 to 5.76) tall on the wide canvas across 151 tabs, and 0.34 in (0.14 to 5.04) compact. Their radius is 0.08 in (0.00 to 0.46) wide. House rendering: a near-black or brand-color tab with paper or on-accent text, sitting flush on a white card held by a hairline.

### Step chevrons
Stepped process rows appear on 12% of content slides, across 267 step shapes. Home-plate pentagons make up 40% of steps and chevrons the rest. The point depth is 0.09 in (0.03 to 0.23) on the wide canvas and 0.33 (0.00 to 1.00) as an adjustment. A shallow point keeps the label room. Number the steps in text, since the arrow shape alone does not order them in grayscale.

### Discs and person glyphs
Discs appear on 52% of content slides, 62% wide. Their diameter is 0.24 in (0.01 to 27.43) on the wide canvas across 1400 discs, and 0.30 in (0.04 to 2.15) compact. Small discs carry a step number or a status. Person glyphs are rare (1% of slides) and set no rule. A role is better named in text than drawn as a figure.

### Line weights
Card outlines weigh 0.75 pt (0.25 to 6) across 4661 outlines, and 3% are dashed. Rules weigh 0.75 pt (0.25 to 7.25), and 45% are dashed. House rendering: one hairline weight for outlines and rules, solid by default. A dashed outline marks a boundary that is proposed or optional, never decoration. A colored strip no thicker than 0.10 in on a card edge is an accent bar, used only where it encodes a state that can change.

### Connectors
Connectors per slide run 3 (0 to 85) on the wide canvas and 0 (0 to 26) compact. They weigh 0.75 pt (0.5 to 3) across 1584 weighted lines. Straight lines are 83%, elbows 13% and curves 3%. 35% are dashed. Heads appear on 54%, double heads on 9%, and triangle heads are 84% of heads.

### Connector contact
Both ends touch a shape on 86% of connectors, yet only 20% are glued at both ends. House rendering: every arrow starts on a box and lands on a box, each end within 0.09 in of an edge, straight or elbowed, no heavier than 1.5 pt, with a triangle head. A dash means a proposed or optional link, never a style choice.

### Shadows and gradients
Soft shadows appear on 32% of content slides, 31% wide and 33% compact, though on only 3% of shapes. Gradients appear on 23% of slides and 1% of shapes. House rendering: flat fills only, a hairline in place of a soft shadow, at most a 1 px shadow, and the theme shadow switched off on every shape.

### Icon density and size
Icons appear on 78% of content slides, at 8 (0 to 95) per wide slide and 4 (0 to 71) per compact slide. Density follows the slide role: architecture slides carry 16 (0 to 71), solution slides 11 (0 to 95) and insight slides 1 (0 to 14). Icons stand 0.28 in (0.12 to 0.90) on the wide canvas across 2445 icons.

### Raster versus vector icons
Raster icons are 73% of icons and native vector icons 22%, with SVG at 1%. Baked-color pictures are 74%, and vectors filled from the theme scheme are 15%. Decks hold 2 (1 to 13) icon styles. House rendering: one vector icon family per deck, filled from the theme so a re-skin recolors it, every named tool given an icon, and no emoji. Vendor and product marks are the exception: official artwork in its own colors, never recolored, verified by bytes.

### Photos and screenshots
Imagery is sparse. Photos appear on 6% of content slides and cluster on team slides (0 (0 to 10)). Screenshots appear on 9% and cluster on proof slides (0 (0 to 6)). Illustrations appear on 27%, logos on 7%, and full-bleed images on 0%. House rendering: a screenshot is evidence and sits inside a hairline frame. A logo wall that names clients stays out of published material.

### Provenance
- Source: system/shape-icon-image.json sha256 09efb0b308ba7708cff07da877100bd9294d593a11a3d6a93079dc2127cc7680
- Rule constants: tools/rules_constants.json sha256 ad8e658546248e054701a7e56d27db5f9f6b32a742931081abf114290f153227
- Input: system/shape.measures.json sha256 4e21c4057546ff1d3fb708661aa5a6b332b4164994cd1f0d7ef2fc38a0e4cf74
- Input: system/icons.measures.json sha256 95fde2d4ad2a856b79089a466996e78be73a23cd0013e1245c05526c7cee22ae
- Input: system/imagery.measures.json sha256 9e43d167c8f5926b575f11341c1cc01ce3747a143650888d23d45dfea1581cd9
- Renderer: render_card@1
