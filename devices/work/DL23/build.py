"""DL23: a gated phase rail over four phase columns, each with its own mini-device, a metric and a deliverables
list, with a braced continuous-improvement loop under the last two phases (phased-roadmap)."""
import argparse
import copy
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import text as txt  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL23")
VARIANT = "gated-rail-phase-columns-loop"


def P(t, role="ink", size=10.5, bold=False, align="center"):
    return txt.Para((txt.Run(t, role, bold=bold, size=size),), align=align, space_before=0)


def put(old, new, value, *, x=None, y=None, w=None, h=None, role="ink", size=10.5, bold=False, align="center",
        bg="paper", anchor="middle"):
    if old != new:
        rename(s, old, new)
    sh = find(s, new)
    bp = sh._element.find(".//" + qn("a:bodyPr"))
    for k in ("lIns", "tIns", "rIns", "bIns"):
        bp.set(k, "0")
    move(s, new, x if x is not None else sh.left / EMU, y if y is not None else sh.top / EMU,
         w if w is not None else sh.width / EMU, h if h is not None else sh.height / EMU)
    text(s, new, [P(value, role, size, bold, align)], th, size=size, bold=bold, background=bg, anchor=anchor)


def clone(src, new):
    el = copy.deepcopy(find(s, src)._element)
    top = max(int(c.get("id")) for c in s._element.iter(qn("p:cNvPr")))
    find(s, src)._element.addnext(el)
    nv = el.find(".//" + qn("p:cNvPr"))
    nv.set("name", new)
    nv.set("id", str(top + 1))


# ---- title: one claim, two-tone
rename(s, "dev.2", "slot.title")
move(s, "slot.title", 0.37, 0.14, 12.59, 0.86)
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "Four phases take the first AI use case to scale in 40 weeks", ("40 weeks",))))],
     th, size=24, bold=True, anchor="middle")

# ---- the rail: dashed line, start marker, gate checks, phase discs, target
rename(s, "dev.3", "struct.rail")
for k, n in enumerate(("dev.12", "dev.13", "dev.14", "dev.15"), 1):
    rename(s, n, "struct.target.%d" % k)
rename(s, "dev.19", "struct.start.arrow")
put("dev.16", "slot.start.when", "Week 0", x=0.48, y=1.36, w=1.20, h=0.20, role="ink-deep", size=9, bold=True,
    align="left")
put("dev.17", "slot.start.label", "Scope and sponsor agreed", x=0.645, y=1.675, w=1.74, h=0.19, role="ink",
    size=8, align="left")
# the drawn check marks are custom geometry: replace each with a curated glyph on its white mask
for i in list(range(20, 23)) + list(range(24, 27)) + list(range(28, 31)) + list(range(32, 35)):
    try:
        delete(s, "dev.%d" % i)
    except KeyError:                       # a member of a group already removed with its group
        pass
for k, n in enumerate(("dev.18", "dev.23", "dev.27", "dev.31"), 1):
    rename(s, n, "struct.gate.%d" % k)
    g = find(s, "struct.gate.%d" % k)
    icon(s, "struct.gate.%d.icon" % k, "circle-check", g.left / EMU - 0.01, g.top / EMU - 0.01, 0.17, th,
         role="accent")

PHASES = [
    # disc, arrow, pill, pill text, rail glyph, week, head, sub, metric
    ("dev.4", "dev.5", "dev.92", "dev.96", "compass", "Week 6", "Assess",
     "Readiness scored three ways", "From interviews and system access", "6 weeks"),
    ("dev.6", "dev.7", "dev.93", "dev.97", "flask-conical", "Week 14", "Pilot",
     "Two use cases proven live", "Scored on five value measures", "8 weeks"),
    ("dev.8", "dev.9", "dev.94", "dev.98", "layers", "Week 26", "Scale",
     "One platform for every team", "Built once, reused by each team", "12 weeks"),
    ("dev.10", "dev.11", "dev.95", "dev.99", "trending-up", "Week 40", "Run",
     "Adoption tied to the value case", "Owned by the business after handover", "14 weeks"),
]
HEADS = [("dev.100", "dev.101", "dev.139"), ("dev.102", "dev.103", "dev.140"),
         ("dev.104", "dev.105", "dev.141"), ("dev.106", "dev.107", "dev.142")]
for i, (disc, arrow, pill, ptxt, gl, week, name, head, sub, metric) in enumerate(PHASES, 1):
    rename(s, disc, "struct.phase.%d.disc" % i)
    d = find(s, "struct.phase.%d.disc" % i)
    cx, cy = (d.left + d.width / 2) / EMU, (d.top + d.height / 2) / EMU
    icon(s, "slot.phase.%d.icon" % i, gl, cx - 0.13, cy - 0.13, 0.26, th, role="on-accent")
    rename(s, arrow, "struct.phase.%d.arrow" % i)
    clone("slot.start.when", "slot.phase.%d.when" % i)
    put("slot.phase.%d.when" % i, "slot.phase.%d.when" % i, week, x=cx - 0.50, y=1.08, w=1.00, h=0.20,
        role="ink-deep", size=9, bold=True)
    rename(s, pill, "struct.phase.%d.pill" % i)
    put(ptxt, "slot.phase.%d.name" % i, name, role="on-accent", size=12, bold=True, bg="accent")
    hd, sb, mt = HEADS[i - 1]
    hx = find(s, hd).left / EMU
    put(hd, "slot.phase.%d.head" % i, head, x=hx, y=3.25, w=2.60, h=0.22, role="ink-deep", size=10.5, bold=True)
    put(sb, "slot.phase.%d.body" % i, sub, x=hx, y=3.47, w=2.60, h=0.20, role="ink", size=9)
    put(mt, "slot.phase.%d.metric" % i, metric, x=hx, y=3.67, w=2.60, h=0.21, role="accent-ink", size=10.5,
        bold=True)

# ---- phase 1 mini-device: three overlapping lenses
for k, (c, t, w) in enumerate((("dev.108", "dev.109", "Data"), ("dev.110", "dev.111", "Process"),
                               ("dev.112", "dev.113", "People")), 1):
    rename(s, c, "struct.lens.%d" % k)
    move(s, "struct.lens.%d" % k, 0.865 + 0.58 * (k - 1), 2.55, 0.66, 0.66)     # touching lenses, overlap kept under 0.1in
    cc = find(s, "struct.lens.%d" % k)
    put(t, "slot.lens.%d" % k, w, x=cc.left / EMU + 0.07, y=2.79, w=0.52, h=0.18, size=8)

# ---- phase 2 mini-device: five-axis scorecard and a build-test-tune track
for k, n in enumerate(("dev.114", "dev.137", "dev.138"), 1):
    rename(s, n, "struct.radar.%d" % k)
for k, i in enumerate(range(160, 170), 1):
    rename(s, "dev.%d" % i, "struct.radar.spoke.%d" % k)
rename(s, "dev.118", "struct.track")
for k, (n, t) in enumerate((("dev.119", "dev.115"), ("dev.120", "dev.116"), ("dev.121", "dev.117")), 1):
    rename(s, n, "struct.track.node.%d" % k)
    nd = find(s, "struct.track.node.%d" % k)
    ncx = (nd.left + nd.width / 2) / EMU
    put(t, "slot.track.%d" % k, ("Build", "Test", "Tune")[k - 1], x=ncx - 0.24, y=2.60, w=0.48, h=0.18, size=8)

# ---- phase 3 mini-device: three discs chained by arrows
for k, (dn, ln, gl, w) in enumerate((("dev.122", "dev.123", "database", "Integrate"),
                                     ("dev.125", "dev.126", "cog", "Automate"),
                                     ("dev.128", "dev.129", "shield-check", "Govern")), 1):
    rename(s, dn, "struct.step.%d" % k)
    d = find(s, "struct.step.%d" % k)
    cx, cy = (d.left + d.width / 2) / EMU, (d.top + d.height / 2) / EMU
    icon(s, "slot.step.%d.icon" % k, gl, cx - 0.14, cy - 0.14, 0.28, th, role="on-accent")
    put(ln, "slot.step.%d" % k, w, x=cx - 0.40, y=3.09, w=0.80, h=0.17, size=8)
rename(s, "dev.124", "struct.step.arrow.1")
rename(s, "dev.127", "struct.step.arrow.2")

# ---- phase 4 mini-device: three rollout chevrons
for k, (cn, ln) in enumerate((("dev.133", "dev.134"), ("dev.132", "dev.135"), ("dev.130", "dev.136")), 1):
    rename(s, cn, "struct.wave.%d" % k)
    move(s, "struct.wave.%d" % k, 10.16 + 0.877 * (k - 1), 2.60, 1.057, 0.36)   # point nests one notch deep
    c = find(s, "struct.wave.%d" % k)
    put(ln, "slot.wave.%d" % k, "Wave %d" % k, x=c.left / EMU + 0.14, y=2.69, w=0.74, h=0.18, role="on-accent",
        size=9, bold=True, bg="ink-deep")
put("dev.131", "slot.wave.label", "Rollout by region over three waves", y=3.01, h=0.20, size=9)

# ---- deliverables lists: a check glyph per row replaces the drawn marker and its rule
LISTS = [
    ("dev.35", 0.567, ["dev.36", "dev.38", "dev.40", "dev.42", "dev.44"], ["dev.37", "dev.39", "dev.41", "dev.43"],
     ["Data source inventory", "Process maps for top flows", "Skills and role survey", "Value case per use case",
      "Shortlist of three pilots"]),
    ("dev.45", 3.821, ["dev.46", "dev.48", "dev.50", "dev.52", "dev.54"], ["dev.47", "dev.49", "dev.51", "dev.53"],
     ["Working model on live data", "Control group comparison", "Five-measure scorecard", "Two user feedback rounds",
      "Go or stop decision"]),
    ("dev.55", 7.077, ["dev.56", "dev.58", "dev.60", "dev.62", "dev.64"], ["dev.57", "dev.59", "dev.61", "dev.63"],
     ["Shared feature store", "Automated release pipeline", "Model risk controls", "Access and audit logs",
      "Team onboarding kit"]),
    ("dev.65", 10.352, ["dev.66", "dev.68", "dev.70", "dev.72"], ["dev.67", "dev.69", "dev.71"],
     ["Regional rollout plan", "Adoption dashboard", "Quarterly value review", "Handover to operations"]),
]
for i in range(73, 92):
    delete(s, "dev.%d" % i)
for c, (card, ix, rows, rules, words) in enumerate(LISTS, 1):
    rename(s, card, "struct.list.%d" % c)
    cd = find(s, "struct.list.%d" % c)
    right = (cd.left + cd.width) / EMU
    for k, r in enumerate(rules, 1):
        rename(s, r, "struct.list.%d.rule.%d" % (c, k))
    for k, (r, w) in enumerate(zip(rows, words), 1):
        sh = find(s, r)
        yc = (sh.top + sh.height / 2) / EMU
        icon(s, "struct.list.%d.mark.%d" % (c, k), "check", ix - 0.01, yc - 0.085, 0.17, th, role="accent")
        put(r, "slot.list.%d.item.%d" % (c, k), w, x=ix + 0.25, y=yc - 0.11, w=right - 0.12 - (ix + 0.25),
            h=0.22, size=10.5, align="left", bg="card")

# ---- the braced loop under Scale and Run
rename(s, "dev.143", "struct.brace")
rename(s, "dev.144", "struct.loop")
for k, n in enumerate(("dev.146", "dev.147", "dev.148", "dev.149"), 1):
    rename(s, n, "struct.loop.head.%d" % k)
move(s, "struct.loop.head.4", 12.98, find(s, "struct.loop.head.4").top / EMU)
# the loop is an outline on paper: drop its fill and paint the arrowheads beneath it, so each head sits centred
# on the line it rides instead of reading as a child of the loop
sp = find(s, "struct.loop")._element.find(qn("p:spPr"))
for f in sp.findall(qn("a:solidFill")):
    idx = list(sp).index(f)
    sp.remove(f)
    sp.insert(idx, sp.makeelement(qn("a:noFill"), {}))
for k in range(1, 5):
    el = find(s, "struct.loop.head.%d" % k)._element
    find(s, "struct.loop")._element.addprevious(el)
put("dev.145", "slot.loop.label", "Continuous improvement once live", y=5.72, h=0.19, role="accent-ink",
    size=10.5, bold=True)
LOOP = [("dev.150", "dev.151", "gauge", "Monitor"), ("dev.152", "dev.153", "search", "Diagnose"),
        ("dev.154", "dev.155", "refresh-cw", "Retrain"), ("dev.156", "dev.157", "rocket", "Release"),
        ("dev.158", "dev.159", "chart-line", "Measure")]
for k, (dn, ln, gl, w) in enumerate(LOOP, 1):
    rename(s, dn, "struct.loop.step.%d" % k)
    d = find(s, "struct.loop.step.%d" % k)
    move(s, "struct.loop.step.%d" % k, d.left / EMU, 5.95)
    cx, cy = (d.left + d.width / 2) / EMU, (d.top + d.height / 2) / EMU
    icon(s, "slot.loop.step.%d.icon" % k, gl, cx - 0.16, cy - 0.16, 0.32, th, role="on-accent")
    put(ln, "slot.loop.step.%d" % k, w, x=cx - 0.50, y=6.55, w=1.00, h=0.24, size=10.5)

out = save(prs, "DL23", th, archetype="phased-roadmap", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
