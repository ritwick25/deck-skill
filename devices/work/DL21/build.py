"""DL21: a source layer of four system groups over a seam caption (records flow down, signals flow back up), a
platform layer of four stage cards joined by chevron discs, each holding a stack of component chips and an outcome
line, over a full-width strip of three cross-cutting enablers (layered-architecture)."""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import prims  # noqa: E402
from deckkit import text as txt  # noqa: E402
from deckkit.canvas import Box  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL21")
VARIANT = "source-band-stage-cards-enablers"


def P(t, role="ink", size=10, bold=False, before=0, align="center"):
    return txt.Para((txt.Run(t, role, bold=bold, size=size),), align=align, space_before=before)


def frame(name, fill, line=None, weight=0.75):
    sh = find(s, name)
    if fill is None:
        sp = sh._element.find(qn("p:spPr"))
        for f in sp.findall(qn("a:solidFill")):
            sp.remove(f)
    else:
        prims.set_fill(sh, fill, theme=th)
    if line is not None:
        prims.set_line(sh, line, weight, theme=th)


def drop_style(name):
    for st in list(find(s, name)._element.iter(qn("p:style"))):
        st.getparent().remove(st)


# brand art: every vector icon drawn in the source (the stage-card marks and the enabler-disc marks)
for n in list(range(31, 44)) + list(range(47, 66)) + list(range(69, 72)) + list(range(114, 144)):
    try:
        delete(s, "dev.%d" % n)
    except KeyError:                      # a member of a group already removed with its group
        pass
# the source band's logo captions and their rules, rebuilt below as glyph items; the split header's second half
for n in list(range(102, 114)) + [4]:
    delete(s, "dev.%d" % n)
# the bullet bodies, rebuilt below as component chips
for n in (98, 99, 100, 101):
    delete(s, "dev.%d" % n)

# column grid shared by the source groups and the stage cards
GAP = 0.46                                # wide enough for a join disc with clearance on both sides
CW = (12.82 - 0.52 - 3 * GAP) / 4
CX = [0.52 + i * (CW + GAP) for i in range(4)]
RADIUS = 0.05                             # the wide canvas card radius


def radius(name, r=RADIUS):
    sh = find(s, name)
    gd = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst") + "/" + qn("a:gd"))
    gd.set("fmla", "val %d" % round(r / (min(sh.width, sh.height) / EMU) * 100000))

# title: one claim, two-tone
rename(s, "dev.6", "slot.title")
move(s, "slot.title", 0.50, 0.20, 12.40, 0.82)
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "Four shared stages turn twelve sources into governed analytics",
    ("Four shared stages", "governed analytics"))))], th, size=24, bold=True, anchor="middle")

# source layer: header bar, frame, four groups of three systems
rename(s, "dev.2", "struct.source.bar")
move(s, "struct.source.bar", 0.37, 1.10, 12.60, 0.31)
frame("struct.source.bar", "ink-strong", "ink-strong")
rename(s, "dev.3", "slot.source.head")
move(s, "slot.source.head", 0.60, 1.10, 12.14, 0.31)
text(s, "slot.source.head", [P("Source systems", "paper", 12, True)], th, size=12, background="ink-strong",
     anchor="middle")
rename(s, "dev.5", "struct.source.frame")
move(s, "struct.source.frame", 0.37, 1.41, 12.60, 1.07)
frame("struct.source.frame", "paper", "rule-strong")

GROUPS = [("dev.7", "dev.8", "Core operations", (("Finance", "landmark"), ("Logistics", "truck"),
                                                  ("Workforce", "users"))),
          ("dev.10", "dev.11", "Customer channels", (("Web store", "store"), ("Call center", "headphones"),
                                                     ("Mobile app", "smartphone"))),
          ("dev.13", "dev.14", "Event streams", (("Sensors", "activity"), ("App logs", "terminal"),
                                                 ("Clickstream", "monitor"))),
          ("dev.16", "dev.17", "External feeds", (("Price data", "chart-line"), ("Weather", "cloud"),
                                                  ("Registries", "library")))]
for g, (strip, head, label, items) in enumerate(GROUPS, 1):
    x = CX[g - 1]
    rename(s, strip, "struct.source.%d.strip" % g)
    move(s, "struct.source.%d.strip" % g, x, 1.48, CW, 0.27)
    frame("struct.source.%d.strip" % g, "card")
    rename(s, head, "slot.source.%d.head" % g)
    move(s, "slot.source.%d.head" % g, x + 0.10, 1.48, CW - 0.20, 0.27)
    text(s, "slot.source.%d.head" % g, [P(label, "accent-ink", 11, True, align="left")], th, size=11,
         background="card", anchor="middle")
    iw = CW / 3
    for k, (name, gl) in enumerate(items, 1):
        ix = x + (k - 1) * iw
        icon(s, "slot.source.%d.item.%d.icon" % (g, k), gl, ix + iw / 2 - 0.13, 1.84, 0.26, th, role="ink-strong")
        txt.textbox(s, Box(ix + 0.02, 2.13, iw - 0.04, 0.24), [P(name, "ink", 10)],
                    "slot.source.%d.item.%d" % (g, k), th, size=10, anchor="middle")
for k, n in enumerate(("dev.9", "dev.12", "dev.15"), 1):
    rename(s, n, "struct.source.rule.%d" % k)
    move(s, "struct.source.rule.%d" % k, (CX[k - 1] + CW + CX[k]) / 2, 1.50, 0, 0.94)

# seam: records flow down, signals flow back up
rename(s, "dev.82", "struct.seam.down")
move(s, "struct.seam.down", 3.30, 2.55, 0.23, 0.22)
rename(s, "dev.83", "struct.seam.up")
move(s, "struct.seam.up", 9.80, 2.55, 0.23, 0.22)
for n in ("struct.seam.down", "struct.seam.up"):
    frame(n, "rule-strong")
rename(s, "dev.81", "slot.seam")
move(s, "slot.seam", 3.65, 2.53, 6.03, 0.26)
text(s, "slot.seam", [P("Raw records flow down, trusted signals flow back up", "ink-deep", 12, True)], th,
     size=12, anchor="middle")

# platform layer: header bar, frame, four stage cards
rename(s, "dev.18", "struct.platform.bar")
frame("struct.platform.bar", "accent", "accent")
rename(s, "dev.19", "slot.platform.head")
move(s, "slot.platform.head", 0.60, 2.85, 12.14, 0.31)
text(s, "slot.platform.head", [P("Shared data platform", "on-accent", 12, True)], th, size=12,
     background="accent", anchor="middle")
rename(s, "dev.20", "struct.platform.frame")
frame("struct.platform.frame", None, "accent")

STAGES = [("dev.22", "dev.74", "dev.84", "Ingest and land", "database-zap",
           ("Batch connectors", "Stream capture", "Schema checks", "Raw landing zone"), "dev.91",
           "Every source landed daily"),
          ("dev.23", "dev.75", "dev.85", "Clean and model", "workflow",
           ("Quality rules", "Entity matching", "Conformed tables", "Lineage capture"), "dev.92",
           "One version of each record"),
          ("dev.24", "dev.76", "dev.86", "Analyze and predict", "brain-circuit",
           ("Feature store", "Forecast models", "Anomaly alerts", "Model registry"), "dev.93",
           "Models retrained on schedule"),
          ("dev.25", "dev.77", "dev.87", "Serve and govern", "shield-check",
           ("Metrics layer", "Self-service views", "Access policies", "Usage audit"), "dev.94",
           "One governed metrics layer")]
for i, (card, hstrip, head, label, gl, chips, out, outcome) in enumerate(STAGES, 1):
    x = CX[i - 1]
    rename(s, card, "struct.stage.%d.card" % i)
    move(s, "struct.stage.%d.card" % i, x, 3.25, CW, 2.03)
    frame("struct.stage.%d.card" % i, "paper", "rule-strong")
    rename(s, hstrip, "struct.stage.%d.strip" % i)
    move(s, "struct.stage.%d.strip" % i, x, 3.25, CW, 0.48)
    frame("struct.stage.%d.strip" % i, "accent-wash", "rule-strong")
    icon(s, "slot.stage.%d.icon" % i, gl, x + 0.12, 3.34, 0.30, th, role="accent")
    rename(s, head, "slot.stage.%d.head" % i)
    move(s, "slot.stage.%d.head" % i, x + 0.52, 3.30, CW - 0.62, 0.38)
    text(s, "slot.stage.%d.head" % i, [P(label, "ink-deep", 12, True, align="left")], th, size=12,
         background="accent-wash", anchor="middle")
    for k, c in enumerate(chips, 1):
        cb = Box(x + 0.22, 3.86 + (k - 1) * 0.35, CW - 0.44, 0.28)
        prims.card(s, cb, fill="card", line="hairline", radius_in=0.04, name="struct.stage.%d.chip.%d" % (i, k),
                   theme=th)
        txt.textbox(s, cb, [P(c, "ink", 10)], "slot.stage.%d.chip.%d" % (i, k), th, size=10, anchor="middle",
                    background="card")
    rename(s, out, "slot.stage.%d.outcome" % i)
    move(s, "slot.stage.%d.outcome" % i, x, 5.33, CW, 0.24)
    text(s, "slot.stage.%d.outcome" % i, [P(outcome, "ink-deep", 11, True)], th, size=11, anchor="middle")
for k, (disc, chev) in enumerate((("dev.78", "dev.88"), ("dev.79", "dev.89"), ("dev.80", "dev.90")), 1):
    gx = (CX[k - 1] + CW + CX[k]) / 2
    rename(s, disc, "struct.join.%d.disc" % k)
    move(s, "struct.join.%d.disc" % k, gx - 0.16, 4.23, 0.32, 0.32)
    frame("struct.join.%d.disc" % k, "accent")
    rename(s, chev, "struct.join.%d.chevron" % k)
    move(s, "struct.join.%d.chevron" % k, gx - 0.04, 4.30, 0.11, 0.18)
    frame("struct.join.%d.chevron" % k, "on-accent")
    drop_style("struct.join.%d.chevron" % k)
for k, n in enumerate(("dev.95", "dev.96", "dev.97"), 1):
    gx = (CX[k - 1] + CW + CX[k]) / 2
    rename(s, n, "struct.outcome.rule.%d" % k)
    move(s, "struct.outcome.rule.%d" % k, gx, 5.36, 0, 0.18)

# cross-cutting enablers: one strip under the full stack
rename(s, "dev.21", "struct.enabler.strip")
frame("struct.enabler.strip", "card")
rename(s, "dev.29", "slot.enabler.head")
move(s, "slot.enabler.head", 3.67, 5.76, 6.00, 0.24)
text(s, "slot.enabler.head", [P("Cross-cutting enablers", "ink-deep", 12, True)], th, size=12,
     background="card", anchor="middle")
ENABLERS = [("dev.26", "dev.30", "dev.44", "dev.45", "clipboard-check", "Data governance",
             "Named owners, shared definitions and quality targets for each shared table"),
            ("dev.27", "dev.46", "dev.66", "dev.67", "settings", "Platform operations",
             "Automated releases, uptime monitoring and cost controls across all four stages"),
            ("dev.28", "dev.68", "dev.72", "dev.73", "lock", "Security and access",
             "Role-based access, masked fields and an audit trail on every layer of the stack")]
for i, (card, disc, head, body, gl, h, b) in enumerate(ENABLERS, 1):
    rename(s, card, "struct.enabler.%d.card" % i)
    frame("struct.enabler.%d.card" % i, "paper", "rule-strong")
    rename(s, disc, "struct.enabler.%d.disc" % i)
    frame("struct.enabler.%d.disc" % i, "ink-strong")
    d = find(s, "struct.enabler.%d.disc" % i)
    side = d.width / EMU
    icon(s, "slot.enabler.%d.icon" % i, gl, d.left / EMU + side * 0.22, d.top / EMU + side * 0.22, side * 0.56, th,
         role="paper")
    rename(s, head, "slot.enabler.%d.head" % i)
    hb = find(s, "slot.enabler.%d.head" % i)
    move(s, "slot.enabler.%d.head" % i, hb.left / EMU, 6.09, 3.08, 0.22)
    text(s, "slot.enabler.%d.head" % i, [P(h, "accent-ink", 11, True, align="left")], th, size=11, anchor="middle")
    rename(s, body, "slot.enabler.%d.body" % i)
    bb = find(s, "slot.enabler.%d.body" % i)
    move(s, "slot.enabler.%d.body" % i, bb.left / EMU, 6.31, 3.10, 0.38)
    text(s, "slot.enabler.%d.body" % i, [P(b, "ink", 10, align="left")], th, size=10)

for n in ["struct.source.bar", "struct.source.frame", "struct.platform.bar", "struct.platform.frame",
          "struct.enabler.strip"] + ["struct.stage.%d.%s" % (i, p) for i in range(1, 5) for p in ("card", "strip")] \
        + ["struct.enabler.%d.card" % i for i in range(1, 4)]:
    radius(n)

out = save(prs, "DL21", th, archetype="layered-architecture", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
