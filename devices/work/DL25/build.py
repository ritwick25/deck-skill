"""DL25: a pill-headed triptych. An input panel lists the brief and the data sources over two sample-data zones, a
wider method panel stacks six numbered step cards marked by who runs them (rules, model, reviewer) beside three
proof zones, and an output panel lists three typed outputs with format tags and proof zones. Two strips beneath
name the reusable skills and the further uses (input-process-output)."""
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

prs, s, th = open_lifted("DL25")
VARIANT = "pill-triptych-step-stack-proofs"


def P(t, role="ink", size=10, bold=False, before=0, align="left"):
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


def radius(name, r=0.05):
    sh = find(s, name)
    gd = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst") + "/" + qn("a:gd"))
    gd.set("fmla", "val %d" % round(r / min(sh.width / EMU, sh.height / EMU) * 100000))


def put(old, new, x=None, y=None, w=None, h=None):
    rename(s, old, new)
    if x is not None:
        move(s, new, x, y, w, h)


def zone(name, box, glyph_name, label, fill="card"):
    """A neutral card zone where a screen or sample sat: hairline card, one glyph, one short caption."""
    prims.card(s, box, fill=fill, line="hairline", radius_in=0.06, name="struct.%s.zone" % name, theme=th)
    side = 0.30
    icon(s, "slot.%s.icon" % name, glyph_name, box.x + box.w / 2 - side / 2, box.y + box.h / 2 - 0.26, side, th,
         role="accent")
    txt.textbox(s, Box(box.x + 0.06, box.y + box.h / 2 + 0.08, box.w - 0.12, 0.24), [P(label, "ink", 10,
                align="center")], "slot.%s.label" % name, th, size=10, anchor="middle", background=fill)


# banned furniture: section-number pill, decorative bars under the title, the scope chip and its mark, the demo button
for n in ("dev.2", "dev.4", "dev.5", "dev.18", "dev.92"):
    delete(s, n)

# title: one claim, two-tone, on the shared left margin
put("dev.3", "slot.title", 0.45, 0.28, 12.43, 0.62)
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "Six automated steps turn sales signals into a weekly demand plan",
    ("Six automated steps", "weekly demand plan"))))], th, size=24, bold=True, anchor="middle")

# the three panels, their pill headers and header discs
PANELS = [("input", "dev.6", "dev.9", "dev.10", "dev.11", "Inputs", "folder-open", 0.74),
          ("method", "dev.7", "dev.12", "dev.13", "dev.14", "Forecast engine", "workflow", 4.57),
          ("output", "dev.8", "dev.15", "dev.16", "dev.17", "Outputs", "send", 9.80)]
for key, panel, pill, disc, head, label, gl, gx in PANELS:
    put(panel, "struct.%s.panel" % key)
    p = find(s, "struct.%s.panel" % key)
    move(s, "struct.%s.panel" % key, p.left / EMU, 0.98, p.width / EMU, 4.86)
    frame("struct.%s.panel" % key, "paper", "rule-strong")
    radius("struct.%s.panel" % key)
    put(pill, "struct.%s.pill" % key)
    frame("struct.%s.pill" % key, "accent")
    put(disc, "struct.%s.disc" % key)
    frame("struct.%s.disc" % key, "paper")
    icon(s, "slot.%s.icon" % key, gl, gx, 1.17, 0.17, th, role="accent")
    put(head, "slot.%s.head" % key)
    text(s, "slot.%s.head" % key, [P(label, "on-accent", 12, True)], th, size=12, background="accent",
         anchor="middle")

# input panel: the planning brief, a rule, the data sources grid, two sample-data zones
BRIEF = [("dev.19", "Planning questions", "circle-question-mark", 1.66, True),
         ("dev.20", "Forecast horizon of 13 weeks", "calendar-days", 1.93, False),
         ("dev.21", "Regions and channels in scope", "globe", 2.23, False),
         ("dev.22", "Accuracy target per product family", "target", 2.53, False)]
for k, (n, t, gl, gy, is_head) in enumerate(BRIEF):
    name = "slot.input.brief.head" if is_head else "slot.input.brief.%d" % k
    sh = find(s, n)
    put(n, name, sh.left / EMU, gy - 0.03, 2.99, 0.24)
    text(s, name, [P(t, "ink-deep" if is_head else "ink", 11 if is_head else 10, is_head)], th,
         size=11 if is_head else 10, anchor="middle")
    icon(s, name + ".icon", gl, 0.61, gy, 0.17, th, role="accent")
put("dev.23", "struct.input.rule")
frame("struct.input.rule", None, "hairline")
put("dev.24", "slot.input.sources.head", 0.86, 3.03, 2.98, 0.24)
text(s, "slot.input.sources.head", [P("Data sources", "ink-deep", 11, True)], th, size=11, anchor="middle")
icon(s, "slot.input.sources.head.icon", "library", 0.61, 3.06, 0.17, th, role="accent")
SOURCES = [("dev.25", "Order history", "database"), ("dev.26", "Promotions", "megaphone"),
           ("dev.27", "Shipments", "truck"), ("dev.28", "Market trends", "chart-line"),
           ("dev.29", "Inventory", "warehouse"), ("dev.30", "Field notes", "messages-square"),
           ("dev.31", "Price lists", "tag"), ("dev.32", "Event calendar", "calendar")]
for k, (n, t, gl) in enumerate(SOURCES, 1):
    col, row = (k - 1) % 2, (k - 1) // 2
    gx, gy = (0.61, 2.23)[col], 3.33 + row * 0.30
    put(n, "slot.input.source.%d" % k, gx + 0.24, gy - 0.03, 1.30, 0.22)
    text(s, "slot.input.source.%d" % k, [P(t, "ink", 10)], th, size=10, anchor="middle")
    icon(s, "slot.input.source.%d.icon" % k, gl, gx, gy, 0.16, th, role="accent")
zone("input.sample.1", Box(0.61, 4.72, 1.56, 0.98), "file-spreadsheet", "Order archive")
zone("input.sample.2", Box(2.27, 4.72, 1.56, 0.98), "activity", "Daily store feeds")

# method panel: who runs each step (legend), six numbered step cards joined by links, three proof zones
LEGEND = [("dev.33", "Rules", "code", 6.81), ("dev.34", "Model", "bot", 7.48), ("dev.35", "Reviewer", "user", 8.20)]
for k, (n, t, gl, gx) in enumerate(LEGEND, 1):
    put(n, "slot.method.legend.%d" % k)
    text(s, "slot.method.legend.%d" % k, [P(t, "ink", 9)], th, size=9, anchor="middle")
    icon(s, "slot.method.legend.%d.icon" % k, gl, gx, 1.55, 0.14, th, role="ink-strong")
STEPS = [("dev.36", "dev.37", "dev.38", "Clean and join", "Units aligned, gaps filled", ("code", "bot")),
         ("dev.40", "dev.41", "dev.42", "Detect demand drivers", "Seasonality tagged by item", ("code",)),
         ("dev.44", "dev.45", "dev.46", "Build the baseline", "Forecast per product line", ("code",)),
         ("dev.48", "dev.49", "dev.50", "Adjust for signals", "Trends shift the baseline", ("code",)),
         ("dev.52", "dev.53", "dev.54", "Explain each change", "A reason drafted per shift", ("bot",)),
         ("dev.56", "dev.57", "dev.58", "Planner sign-off", "Overrides logged and dated", ("user",))]
for i, (card, num, body, head, line, marks) in enumerate(STEPS, 1):
    fill = "card" if i % 2 else "accent-tint"
    put(card, "struct.step.%d.card" % i)
    frame("struct.step.%d.card" % i, fill)
    radius("struct.step.%d.card" % i)
    cy = find(s, "struct.step.%d.card" % i).top / EMU
    put(num, "struct.step.%d.disc" % i)
    frame("struct.step.%d.disc" % i, "accent")
    rename(s, "struct.step.%d.disc" % i, "slot.step.%d.num" % i)
    text(s, "slot.step.%d.num" % i, [P(str(i), "on-accent", 11, True, align="center")], th, size=11,
         background="accent", anchor="middle")
    put(body, "slot.step.%d.head" % i, 4.92, cy + 0.06, 2.00, 0.24)
    text(s, "slot.step.%d.head" % i, [P(head, "ink-deep", 11, True)], th, size=11, background=fill,
         anchor="middle")
    txt.textbox(s, Box(4.92, cy + 0.30, 2.00, 0.22), [P(line, "ink", 10)], "slot.step.%d.body" % i, th, size=10,
                anchor="middle", background=fill)
    for k, gl in enumerate(marks, 1):
        gx = 7.18 - (len(marks) - k) * 0.22
        icon(s, "slot.step.%d.mark.%d" % (i, k), gl, gx, cy + 0.21, 0.16, th, role="ink-strong")
for k, n in enumerate(("dev.39", "dev.43", "dev.47", "dev.51", "dev.55"), 1):
    put(n, "struct.step.link.%d" % k)
    frame("struct.step.link.%d" % k, None, "rule-strong")
zone("method.proof.1", Box(7.58, 1.88, 1.37, 1.14), "table", "Joined dataset")
zone("method.proof.2", Box(7.58, 3.22, 1.37, 1.14), "chart-line", "Baseline forecast")
zone("method.proof.3", Box(7.58, 4.53, 1.37, 1.14), "file-text", "Change notes")

# handoff discs on the two panel gaps
for k, (n, gx) in enumerate((("dev.59", 4.06), ("dev.60", 9.29)), 1):
    put(n, "struct.handoff.%d.disc" % k)
    frame("struct.handoff.%d.disc" % k, "accent-tint")
    icon(s, "struct.handoff.%d.mark" % k, "chevron-right", gx, 3.48, 0.16, th, role="accent")

# output panel: three typed outputs, each with format tags, one line and a proof zone
OUTS = [("dev.61", ("dev.63", "dev.62"), "dev.64", "Demand plan", ("Weekly", "Table"),
         "Units by product, region and week", "layout-dashboard", 1.67),
        ("dev.65", ("dev.67", "dev.66"), "dev.68", "Exception list", ("Daily", "Alert"),
         "Products drifting more than 10% off target", "triangle-alert", 3.08),
        ("dev.69", ("dev.70",), "dev.71", "Change summary", ("Weekly",),
         "Reasons behind each forecast shift", "file-text", 4.49)]
for i, (head, tags, body, h, tg, b, gl, gy) in enumerate(OUTS, 1):
    put(head, "slot.output.%d.head" % i, 9.90, gy - 0.05, 1.55, 0.26)
    text(s, "slot.output.%d.head" % i, [P(h, "ink-deep", 11, True)], th, size=11, anchor="middle")
    icon(s, "slot.output.%d.icon" % i, gl, 9.67, gy, 0.16, th, role="accent")
    for k, (n, t) in enumerate(zip(tags, tg), 1):
        put(n, "slot.output.%d.tag.%d" % (i, k), (12.14, 11.50)[len(tags) - k], gy - 0.03, 0.58, 0.22)
        frame("slot.output.%d.tag.%d" % (i, k), "card")
        text(s, "slot.output.%d.tag.%d" % (i, k), [P(t, "accent-ink", 8, True, align="center")], th, size=8,
             background="card", anchor="middle")
    put(body, "slot.output.%d.body" % i, 9.67, gy + 0.24, 3.05, 0.24)
    text(s, "slot.output.%d.body" % i, [P(b, "ink", 10)], th, size=10, anchor="middle")
for n in ("dev.94", "dev.93"):
    delete(s, n)
zone("output.proof.1", Box(10.30, 2.21, 1.55, 0.78), "chart-column", "Plan view")
zone("output.proof.2", Box(10.30, 3.62, 1.55, 0.78), "list-checks", "Flag queue")
delete(s, "dev.95")
prims.card(s, Box(9.80, 5.03, 1.02, 0.70), fill="card", line="hairline", radius_in=0.06,
           name="struct.output.proof.3.zone", theme=th)
icon(s, "slot.output.proof.3.icon", "file-text", 10.15, 5.22, 0.32, th, role="accent")
put("dev.72", "slot.output.3.note", 11.00, 5.03, 1.74, 0.70)
text(s, "slot.output.3.note", [P("Planner brief", "ink-deep", 11, True),
                               P("One page per region", "ink", 10, before=2)], th, size=11, anchor="middle")

# strips: reusable skills and further uses
STRIPS = [("reuse", "dev.73", "dev.75", "dev.76", "dev.77", "Reusable skills", "blocks", 0.73),
          ("uses", "dev.74", "dev.78", "dev.79", "dev.80", "Further uses", "compass", 6.97)]
for key, panel, pill, disc, head, label, gl, gx in STRIPS:
    put(panel, "struct.%s.panel" % key)
    p = find(s, "struct.%s.panel" % key)
    move(s, "struct.%s.panel" % key, p.left / EMU, 5.96, p.width / EMU, 0.84)
    frame("struct.%s.panel" % key, "paper", "rule-strong")
    radius("struct.%s.panel" % key)
    put(pill, "struct.%s.pill" % key)
    frame("struct.%s.pill" % key, "accent")
    put(disc, "struct.%s.disc" % key)
    frame("struct.%s.disc" % key, "paper")
    icon(s, "slot.%s.icon" % key, gl, gx, 6.12, 0.13, th, role="accent")
    put(head, "slot.%s.head" % key)
    text(s, "slot.%s.head" % key, [P(label, "on-accent", 11, True)], th, size=11, background="accent",
         anchor="middle")
SKILLS = [("dev.81", "dev.82", "Data cleaning", "sparkles", 0.70),
          ("dev.83", "dev.84", "Driver search", "search", 2.195),
          ("dev.85", "dev.86", "Report writer", "file-text", 3.776),
          ("dev.87", "dev.88", "Feeds", "plug", 5.412)]
for k, (chip, lab, t, gl, gx) in enumerate(SKILLS, 1):
    put(chip, "struct.reuse.chip.%d" % k)
    frame("struct.reuse.chip.%d" % k, "card")
    c = find(s, "struct.reuse.chip.%d" % k)
    move(s, "struct.reuse.chip.%d" % k, c.left / EMU, 6.42, c.width / EMU, 0.26)
    put(lab, "slot.reuse.%d" % k, gx + 0.20, 6.42, c.width / EMU - (gx + 0.20 - c.left / EMU) - 0.06, 0.26)
    text(s, "slot.reuse.%d" % k, [P(t, "accent-ink", 9, True)], th, size=9, background="card", anchor="middle")
    icon(s, "slot.reuse.%d.icon" % k, gl, gx, 6.48, 0.14, th, role="accent")
USES = [("dev.89", "Inventory planning", "warehouse", 6.85), ("dev.90", "Price testing", "tag", 8.80),
        ("dev.91", "Staff scheduling", "calendar-check", 10.75)]
for k, (n, t, gl, gx) in enumerate(USES, 1):
    put(n, "slot.uses.%d" % k, gx + 0.22, 6.42, 1.60, 0.26)
    text(s, "slot.uses.%d" % k, [P(t, "ink", 10)], th, size=10, anchor="middle")
    icon(s, "slot.uses.%d.icon" % k, gl, gx, 6.48, 0.14, th, role="accent")

out = save(prs, "DL25", th, archetype="input-process-output", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
