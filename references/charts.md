# Charts on slides

Ruling 22. Read the `dataviz` skill first for the form heuristic; this file is how the house draws the chart in a pptx.
`scripts/example_charts.py` is the worked pattern: five slides (`headline` bar beside a stat band, `horizons` line
over an area wash with a crossover, `commercials` price waterfall, `case` before and after, `priorities` value and
effort scatter), every one passing all 27 gates on both house themes.

## How a chart is built

The data marks are a native python-pptx chart, so the deck opened in PowerPoint carries Edit Data and a theme swap
re-skins the chart with the deck (every colour is a schemeClr from the theme). Everything the gates must see is a kit
shape drawn on exact data coordinates: category names, value labels, end labels, the basis label and every
annotation. The plot area is pinned (`c:manualLayout`) and the value axis fixed, so `Plot.val(v)`, `Plot.cat(i)`,
`Plot.point(i, v)` and `Plot.xy(x, y)` turn data into slide inches for anything drawn beside the chart.

```python
plot = charts.bar(s, box, ["Collect", "Rewrite", "Review", "Send"], [1, 2, 1, 1], subject="Rewrite",
                  fmt="{:g} days", kind="illustrative", name="days")
charts.annotate(plot, "Rewrite", "Six rewrites, two days", kind="callout")
package.save(prs, out, title=..., theme=th, manifest={"numbers": numbers, "charts": charts.records(prs)}, ...)
```

Every call takes `kind=` (measured, delivered, illustrative, target, benchmark) and `name=` (no spaces; kit labels are
named `<name>.cat.<i>`, `<name>.value.<i>` and so on), measures every label before writing, and raises `Overflows`
or `ChartError` before anything is drawn. Type never shrinks below its role and category names never rotate.

## Roles: a chart colour is a job, never a hex

| Job | Role | Rule |
|---|---|---|
| subject | `accent` | exactly one mark per chart: the bar, series, segment, group or point the title is about |
| other series, in order | `series-1` (navy), `rule-strong` (grey), `series-2` | at most 3 categorical colours per chart |
| context | `hairline` | every other bar when one bar is the subject; with no subject every bar is navy |
| negative step | `ink-muted` | never accent: the sign travels in the label |
| area, tolerance band | `accent-wash` | behind the plot |
| gridlines | `hairline-soft`, 0.75pt solid | never dashed; value-axis line off |
| tick text | `ink-muted`, 10pt | axis numbers and category names under a plot |
| category names on bar rows | 11pt | right-aligned left of the plot, two lines at most |
| value labels | 11pt, the subject's 12pt bold | direct labels at the tip or over the cap |
| annotation callout | 11pt bold | one line, 2 to 6 words, no box |
| basis label | 9pt `ink-muted` | "Illustrative figures", once per slide |

**Series slots.** A theme's chart order is `accent`, `series-1`, `rule-strong`, `series-2`. `charts.check_theme(th)`
returns why a theme cannot carry a chart: adjacent roles must clear 8 (OKLab x100) in normal vision and under the
three Machado simulations, each role must clear 15 against paper, and no chart role may be a status identity. On the
house theme `series-3` and `series-4` are greys (`A6A6A6`, `D9D9D9`), so every series clears CIEDE2000 10 against
every RAG identity. A client theme from `brand.py` puts the secondaries in `series-1` onward and pads with house
slates; a chart with more series than the client gave colours shows those greys.

**Status colours never ride a chart.** The RAG identities (`rag-red`, `rag-amber`, `rag-green`) are refused as chart
roles and P27 fails them in a chart part. A status lives in a glyph and a word beside the thing it judges (`dv57`). On
the house theme the brand red is the RAG red's hex, which is why a loss is `ink-muted` and a red subject bar never
sits beside a red status mark.

**Basis labels.** A planning kind (illustrative, target, benchmark) draws one basis label per slide, text exactly
"Illustrative figures" (or Target, Benchmark), unless the slide already carries it: draw `compose.stat_band` first and
the chart reuses its label, or pass `basis=False` when another label on the slide covers it. Never mix a delivered
chart and an illustrative band under one label. The frame's alt text ends `(chart kind <kind>)`.

## Per type

- **`bar(s, box, cats, values, *, kind, name, subject=None, fmt="{:,.0f}", vmax=None, sort=None)`**: horizontal
  bars, one series, categories top to bottom; `sort="desc"` for magnitudes, source order otherwise. Values at each
  tip. At most 16 categories (more is a table); no negative values (a negative step is a waterfall).
- **`column(...)`**: the same arguments, categories left to right in time order, names under each column, values over
  each cap.
- **`stacked(s, box, cats, {series: values}, *, kind, name, subject=None, total_fmt=None)`**: one horizontal bar per
  category, one to three named segments plus an optional "Other" in grey; segment names sit over the first bar (a
  direct key, never a legend box); a segment value is written inside only when it fits at 4.5:1, else the bar's
  total at its end carries the number. Segments are outlined 1.5pt in paper.
- **`line(s, box, cats, {series: values}, *, kind, name, subject=None, vmin=0, vmax=None, axis_format="#,##0",
  tick_fmt=None, ticks=4, end_labels=True, area=False)`**: up to three series; the subject in accent with markers,
  the others navy then grey without; a native value axis on nice steps with hairline-soft gridlines; each series
  ends in a direct label (name and last value), never a legend. Two value axes are refused.
- **`area(s, box, cats, values, *, series_name, kind, name)`**: one series as an accent line over an accent-wash
  area. A stacked area is refused: use `stacked`.
- **`waterfall(s, box, [(label, value)], *, total, kind, name, signed=None, connectors=True)`**: a horizontal bridge;
  each step floats from the running total, the `total` bar starts at zero in accent; positive steps navy, negative
  `ink-muted`; signed values when any step is negative; dashed carry lines between bars (the one dash a chart allows:
  it means carried over). Edit Data holds the arithmetic (an invisible base series).
- **`scatter(s, box, [(label, x, y)], *, x_range, y_range, x_label, y_label, kind, name, groups=None, subject=None,
  sizes=None, splits=None, quadrants=None, numbered=False)`**: two fixed native axes; up to three groups; each point
  labelled on its first free side, or by number with `numbered=True` (draw the key); `splits=(x, y)` draws dashed
  grey quadrant rules and `quadrants` names the corners; `sizes` makes a bubble chart whose area maps the size. Axis
  names are kit text, never rotated, four words or fewer at the foot (P09 reads a longer line there as a foot
  sentence).
- **`ring(s, square, value, of, *, kind, name)`**: a share ring (`dv38`): a native doughnut of two points, the share
  in accent, the rest in card, hole 78%, no labels on the ring. Put the figure in the hole with `prims.stat`. A
  comparison of close values is a bar chart.
- **`bullet(s, box, [charts.Row(label, value, target)], *, scale_max, kind, name, subject=None)`** and
  **`progress(s, box, value, of, *, label, kind, name)`**: KPI rows drawn from kit shapes, a card track the full
  scale, a 0.16in measure bar (navy, the subject row accent), a target tick, the value at the right. 0.10in and under
  would be the accent strip the house refuses.

## The annotation

Every chart slide names the one point that proves its title: `charts.annotate(plot, at, text, kind=, side="above",
to=None)`. `at` is a category name or index (the subject's value), `(index, value)`, or a point label or `(x, y)` on a
scatter.

| kind | Draws |
|---|---|
| `callout` | a bold label of 2 to 6 words beside the point, 0.10in off it, no box |
| `drop` | a dashed grey line from the point to the category axis, the callout above the point |
| `crossover` | the drop plus a solid accent dot ringed in paper on the point |
| `band` | an accent-wash tolerance band behind the plot from value `at` to value `to`, named at its left edge |

It tries the asked side, then the others, clear of bars, points, labels and lines, and raises when all four are
taken. The text never repeats the title and never tells the reader where to look. A takeaway band under the plot is a
summary band and is not drawn.

## Manifest and gate P27

`charts.records(prs)` returns `{frame name: {"groups", "kind", "series", "labels"}}` for every chart; save it as
`manifest["charts"]`. Gate P27 reads every chart part behind its frame and fails: a text under 8pt or without an
explicit size; a colour that is not a theme role or identity, or a RAG status on a chart; 3D, a gradient, pattern or
picture fill, an effect, `c:style` other than 1 or 2, rounded corners; a chart title; a legend at three series or
fewer; more than three categorical colours or more than one accent mark; a bar, column or area value axis not fixed at
0, or a log scale; a second axis pair; a pie or doughnut of more than two points; an unpinned plot area; P17's banned
patterns in any chart text; tick and label contrast under the WCAG minimum; alt text without `(chart kind <kind>)`, or
a planning kind with no basis label on its slide; and drift: a frame with no manifest record, a data cache changed
after the build (Edit Data), or a kit label whose text changed. P12 validates every chart part against
`dml-chart.xsd`; P10 counts a chart frame as the slide's device. A deck with no chart passes P27 with a note.

## What the house drops from the references

The mono kicker over every chart card, series-coloured label text, the italic footnote under the plot, a red negative
bar, legend boxes, hover layers and tooltips, dark mode, rounded data ends (native bars cannot round one end), and any
dashed gridline.
