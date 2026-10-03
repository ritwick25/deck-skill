# C charts: API and usage note

## Built
- **kit/deckkit/charts.py**: native python-pptx charts, house-styled, every label a kit text box on data
  coordinates (plot area pinned by `c:manualLayout`, axes fixed). Every call takes `kind=` (a stat kind) and
  `name=`, raises `Overflows` / `ChartError` before anything is written, and returns a `Plot` (`box`, `val(v)`,
  `cat(i)`, `point(i, v)`, `xy(x, y)`, `series`, `marks`).
  - `bar(s, box, cats, values, *, kind, name, subject=None, fmt="{:,.0f}", vmax=None, sort=None)`: rows; subject
    in accent, the rest grey context (navy when no subject); names right-aligned left, values at the tips.
  - `column(...)` same args, time order left to right, names under, values over the caps (never rotated).
  - `stacked(s, box, cats, {series: values}, *, kind, name, subject=None, fmt, total_fmt=None)`: horizontal, 1 to 3
    named segments plus "Other"; segment names over the first bar (no legend), totals at the ends.
  - `line(s, box, cats, {series: values}, *, kind, name, subject=None, vmin=0, vmax=None, fmt, axis_format="#,##0",
    tick_fmt=None, ticks=4, end_labels=True, area=False)`: up to 3 series; direct end labels; native value axis.
  - `area(s, box, cats, values, *, series_name, kind, name)`: one line over an accent-wash area.
  - `waterfall(s, box, [(label, value)], *, total, kind, name, fmt, signed=None, connectors=True)`: horizontal
    bridge; positive navy, negative ink-muted, total accent; dashed carry lines; Edit Data holds the arithmetic.
  - `scatter(s, box, [(label, x, y)], *, x_range, y_range, x_label, y_label, kind, name, groups=None,
    subject=None, sizes=None, splits=None, quadrants=None, numbered=False)`: groups up to 3; `sizes` makes a bubble
    chart (area maps size); labels placed on the first free side; quadrant rules dashed grey.
  - `ring(s, square, value, of, *, kind, name)` (dv38, two points); `bullet(s, box, [Row(label, value, target)], *,
    scale_max, kind, name)` and `progress(s, box, value, of, *, label, kind, name)`: kit-shape KPI bars 0.16in.
  - `annotate(plot, at, text, *, kind="callout"|"drop"|"crossover"|"band", side="above", to=None)`: callout dot
    with a dashed drop, or a tolerance band drawn behind the frame. Tries the asked side then the others, clear of
    bars, points, labels and lines; raises when all four are taken, or when a band would cut a label.
  - `records(prs)` for `manifest["charts"]`; `parse(root)`, `frame_kind(descr)`, `check_theme(theme)`.
- **gates/p27_charts.py** (after P26) reads every chart part: 8pt floor and explicit sizes; theme roles or identity
  only, never a RAG hex; no 3D, gradient, effect, `c:style` > 2, rounded corners, title, small legend; at most 3
  categorical colours and 1 accent; bar and area axes fixed at 0; one axis pair; rings of 2 points; a pinned plot;
  P17's banned words in chart text; tick and data-label contrast; `(chart kind X)` alt text and the basis label;
  drift against `manifest["charts"]`.
- **gates/negatives_charts.py**: 25 P27 and 2 P12 planters, discovered by `run_all --negatives` (164/164, 27/27).
- **package.py**: `part_xsd` checks `ppt/charts/chart*.xml` against `dml-chart.xsd` (python-pptx's signed axis ids
  are a known value); `find_validator` takes the newest synced copy.
- **clone.py**: a chart frame travels with its own chart part, workbook and style parts (never shared between
  slides), alt text kept; linked data, user shapes and `cx:chart` are refused.
- **themes**: sigmoid `accent4`/`accent5` (series-3, series-4) are now greys A6A6A6 and D9D9D9, no longer the
  rag-amber and rag-green hexes; every series clears CIEDE2000 10 against every RAG identity. Neutral unchanged.
- **scripts/example_charts.py**: 5 slides (bar with a stat band, line with area and crossover, price waterfall,
  before and after, value-effort scatter); 27/27 gates on sigmoid and neutral, byte-identical rebuild, all read.

## How a builder uses it
`plot = charts.bar(...)`, `charts.annotate(plot, ...)`, then save with `manifest={"numbers": ..., "charts":
charts.records(prs)}`. Draw `compose.stat_band` first so the chart reuses its basis label (or pass `basis=False`).
Axis names at the foot stay at 4 words or fewer (P09 reads a longer line there as a foot sentence).

## Requests to other owners
- B: `test_geom_clone` `test_chart_refused_before_writing` must plant a `chartex` uri now (native charts travel).
  P13 does not count words inside chart parts (kit charts write theirs as kit text; foreign charts slip).
- Integrator (unowned): `test_core` `test_cvd_report` asserts the amber/green collision this removes; assert
  `cvd() == []`. Rerun `$PY scripts/make_base.py` for `test_make_base_deterministic_and_fresh` (saves re-theme).
- brand.py owner: refuse a client secondary within CIEDE2000 10 of a RAG identity. Docs: SKILL.md Kit bullet,
  `references/charts.md` (spec section 0 table), a P27 row in rules.md.

## Open, for the user
- On sigmoid, `accent` is D91E18, which is also the `rag-red` identity. Charts never use RAG hexes and draw
  negatives in ink-muted. Even so, a red subject bar beside a red status mark reads alike. accent1 is the brand
  and outside this track.
- The review's feasibility build (`charts-proto/proto.pptx`) is schema-invalid: its chart and axis `spPr` are
  misplaced. PowerPoint would have offered a repair. The new P12 chart pass catches this.
