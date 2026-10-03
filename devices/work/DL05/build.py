"""DL05: six-stage chevron pipeline with a glyph, an action and an output per stage, one stage marked current,
and a detail panel below that opens the current stage into gate criteria, owners and open risks (process-flow)."""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import text as txt  # noqa: E402
from deckkit.prims import set_fill, set_line  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL05")
VARIANT = "chevron-stages-detail-panel"

# chrome the house rules ban: the subtitle; residue: an empty container box and the emptied icon group
for n in ("dev.4", "dev.62"):
    delete(s, n)
_g = find(s, "dev.16")._element                     # identity-transform group around the six actions: ungroup
for ch in [c for c in _g if c.tag in (qn("p:sp"), qn("p:cxnSp"))]:
    _g.addprevious(ch)
_g.getparent().remove(_g)

# title: one claim, two-tone
rename(s, "dev.3", "slot.title")
move(s, "slot.title", 0.48, 0.30, 12.40, 0.50)
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "Validation is the gate that moves the forecasting pilot into launch", ("Validation",))))],
    th, size=22, bold=True, anchor="middle")

# the pipeline: chevron, glyph, action, divider, output
STAGES = [  # chevron, divider, action, output, glyph, label, action text, (output accent, output rest)
    ("dev.5", "dev.23", "dev.17", "dev.29", "search", "Assess",
     "Size the value and pick the pilot lines", ("Signed business case", " and scope")),
    ("dev.6", "dev.24", "dev.18", "dev.30", "gauge", "Baseline",
     "Measure current forecast accuracy by line", ("Accuracy baseline", " by product line")),
    ("dev.7", "dev.25", "dev.19", "dev.31", "cog", "Build",
     "Train models on sales and promotion history", ("Pilot model", " ready for testing")),
    ("dev.8", "dev.26", "dev.20", "dev.32", "clipboard-check", "Validate",
     "Run beside the plan against gate criteria", ("Gate decision note", " for launch")),
    ("dev.9", "dev.27", "dev.21", "dev.33", "rocket", "Launch",
     "Move pilot lines onto model forecasts", ("Live forecasts", " on every pilot line")),
    ("dev.10", "dev.28", "dev.22", "dev.34", "trending-up", "Scale",
     "Extend to every region and category", ("Rollout plan", " by region and wave")),
]
ICON_X = (1.373, 3.416, 5.464, 7.511, 9.559, 11.601)          # the removed icon boxes, lift.json
CURRENT = 4
for i, (chev, div, act, out, g, label, action, (oa, orest)) in enumerate(STAGES, 1):
    bg = "card" if i == CURRENT else "paper"
    rename(s, chev, "slot.stage.%d.label" % i)
    set_fill(find(s, "slot.stage.%d.label" % i), "accent", theme=th)
    text(s, "slot.stage.%d.label" % i, [txt.Para((txt.Run(label, "on-accent", bold=True, size=13),),
                                                  align="center")], th, size=13, anchor="middle",
         background="accent")
    icon(s, "slot.stage.%d.icon" % i, g, ICON_X[i - 1] - 0.02, 0.99, 0.42, th, role="accent")
    rename(s, div, "struct.stage.%d.rule" % i)
    sh = find(s, "struct.stage.%d.rule" % i)
    move(s, "struct.stage.%d.rule" % i, sh.left / EMU, 2.82, sh.width / EMU, 0)
    rename(s, act, "slot.stage.%d.action" % i)
    sh = find(s, "slot.stage.%d.action" % i)
    move(s, "slot.stage.%d.action" % i, sh.left / EMU, 2.12, sh.width / EMU, 0.62)
    text(s, "slot.stage.%d.action" % i, [txt.Para((txt.Run(action, "ink", size=11),), align="center")],
         th, size=11, background=bg)
    rename(s, out, "slot.stage.%d.output" % i)
    sh = find(s, "slot.stage.%d.output" % i)
    move(s, "slot.stage.%d.output" % i, sh.left / EMU, 2.92, sh.width / EMU, 0.42)
    text(s, "slot.stage.%d.output" % i, [txt.Para((txt.Run(oa + orest, "ink-deep", bold=True, size=11),),
                                                  align="center")], th, size=11, background=bg)
for k, n in enumerate(range(11, 16), 1):
    rename(s, "dev.%d" % n, "struct.stage.sep.%d" % k)
    sh = find(s, "struct.stage.sep.%d" % k)
    move(s, "struct.stage.sep.%d" % k, sh.left / EMU, 2.04, 0, 1.38)
rename(s, "dev.2", "struct.current")
set_fill(find(s, "struct.current"), "card", theme=th)
move(s, "struct.current", find(s, "struct.current").left / EMU, 2.02, find(s, "struct.current").width / EMU, 1.42)


def radius(name, r=0.05):
    sh = find(s, name)
    gd = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst") + "/" + qn("a:gd"))
    gd.set("fmla", "val %d" % round(r / (min(sh.width, sh.height) / EMU) * 100000))


radius("struct.current")

# detail panel: the current stage opened up, on a light card
rename(s, "dev.35", "struct.panel")
set_fill(find(s, "struct.panel"), "card", theme=th)
radius("struct.panel")
rename(s, "dev.36", "slot.panel.head")
move(s, "slot.panel.head", 0.72, 3.98, 11.93, 0.30)
text(s, "slot.panel.head", [txt.Para((txt.Run("Validate", "ink-deep", bold=True, size=13),
                                      txt.Run(" passes when the pilot holds against the current plan for four "
                                              "straight weeks", "ink-deep", size=13)),)],
     th, size=13, background="card", anchor="middle")

for n, head, rule in (("dev.37", "Gate criteria", "dev.54"), ("dev.49", "Owners and actions", "dev.53"),
                      ("dev.43", "Open risks", "dev.47")):
    col = {"dev.37": 1, "dev.49": 2, "dev.43": 3}[n]
    rename(s, n, "slot.col.%d.head" % col)
    text(s, "slot.col.%d.head" % col, head, th, size=12, bold=True, role="ink-deep", background="card")
    rename(s, rule, "struct.col.%d.rule" % col)
    set_line(find(s, "struct.col.%d.rule" % col), "rule-strong", 1.0, theme=th)
rename(s, "dev.55", "struct.col.sep.1")
rename(s, "dev.48", "struct.col.sep.2")
for n in ("struct.col.sep.1", "struct.col.sep.2"):
    set_line(find(s, n), "rule-strong", 0.75, theme=th, dash="dash")

CRITERIA = [("Accuracy", " beats the current plan on most lines"),
            ("Bias", " stays inside the agreed tolerance band"),
            ("Coverage", " every pilot line carries a forecast"),
            ("Adoption", " planners review outputs weekly"),
            ("Sign-off", " business owner signs the gate note")]
for i, (n, (lead, rest)) in enumerate(zip(("dev.38", "dev.39", "dev.40", "dev.41", "dev.42"), CRITERIA), 1):
    rename(s, n, "slot.criterion.%d" % i)
    move(s, "slot.criterion.%d" % i, 0.72, 4.84 + (i - 1) * 0.355, 3.68, 0.26)
    text(s, "slot.criterion.%d" % i, [txt.Para((txt.Run(lead, "ink-deep", bold=True, size=11),
                                                txt.Run(rest, "ink", size=11)),)], th, size=11,
         background="card", anchor="middle")

OWNERS = [("dev.52", "dev.56", "dev.59", "Planning", "Compare model and planner forecasts every week"),
          ("dev.51", "dev.57", "dev.60", "Data", "Fix late shipment feeds before each weekly run"),
          ("dev.50", "dev.58", "dev.61", "Finance", "Confirm the savings logic behind the business case")]
for i, (row, tag, body, t, b) in enumerate(OWNERS, 1):
    rename(s, row, "struct.owner.%d" % i)
    set_line(find(s, "struct.owner.%d" % i), "hairline", 0.75, theme=th)
    radius("struct.owner.%d" % i)
    rename(s, tag, "slot.owner.%d.tag" % i)
    text(s, "slot.owner.%d.tag" % i, [txt.Para((txt.Run(t, "on-accent", bold=True, size=11),), align="center")],
         th, size=11, anchor="middle", background="accent")
    rename(s, body, "slot.owner.%d.body" % i)
    text(s, "slot.owner.%d.body" % i, b, th, size=11, anchor="middle", background="paper")

RISKS = [("dev.46", "Late data", " two regional feeds arrive after cutoff"),
         ("dev.45", "Promotions", " uplift history is thin on new lines"),
         ("dev.44", "Capacity", " planner reviews clash with month end")]
for i, (n, lead, rest) in enumerate(RISKS, 1):
    rename(s, n, "slot.risk.%d" % i)
    set_line(find(s, "slot.risk.%d" % i), "hairline", 0.75, theme=th)
    radius("slot.risk.%d" % i)
    text(s, "slot.risk.%d" % i, [txt.Para((txt.Run(lead, "ink-deep", bold=True, size=11),
                                           txt.Run(rest, "ink", size=11)),)], th, size=11,
         anchor="middle", background="paper")

out = save(prs, "DL05", th, archetype="process-flow", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
