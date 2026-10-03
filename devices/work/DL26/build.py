"""DL26: a five-stage decision lane (signals, checks, ordered rules, outcomes, decision record), from d12-s016."""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F401
from devwork import EMU, find, qn  # noqa: E402
from deckkit import text as txt  # noqa: E402

VARIANT = "staged-rule-lanes"

ap = argparse.ArgumentParser()
ap.add_argument("--out")
args = ap.parse_args()

prs, s, th = open_lifted("DL26")
R, P = txt.Run, txt.Para


def ins(name, l=0.04, t=0.02, r=0.04, b=0.02):
    bp = find(s, name)._element.find(".//" + qn("a:bodyPr"))
    for k, v in (("lIns", l), ("tIns", t), ("rIns", r), ("bIns", b)):
        bp.set(k, str(int(v * EMU)))


def put(old, new, value, **kw):
    rename(s, old, new)
    ins(new)
    text(s, new, value, th, **kw)


def n(i):
    return "dev.%d" % i


# 1. Banned chrome: title accent bar, subtitle, foot sentence, caption under the example card.
for d in (2, 132, 133, 131):
    delete(s, n(d))
# Decorative left accent bars on the check cards.
for d in (58, 63, 68, 73, 78, 83):
    delete(s, n(d))
# Picture-stand-in arrows (white text chevrons): replaced by glyphs below.
for d in (9, 15, 21, 27):
    delete(s, n(d))

# 2. Title.
rename(s, n(3), "slot.title")
ins("slot.title", 0.04, 0.02, 0.04, 0.02)
text(s, "slot.title", [P(tuple(txt.title_runs("Five ordered rules route every late shipment to expedite or hold",
                                             ("Five ordered rules",))))], th, size=24, anchor="middle")

# Stage tabs: tab, disc, numeral, label, caption.
tabs = [("Order signals", "Six inputs"), ("Checks", "Yes or no"),
        ("Routing rules", "Five rules, in order"), ("Outcomes", "Two dispositions"),
        ("Decision", "Per order")]
for i, (base, (label, cap)) in enumerate(zip((4, 10, 16, 22, 28), tabs), 1):
    rename(s, n(base), "struct.tab.%d" % i)
    rename(s, n(base + 1), "struct.tab.%d.disc" % i)
    put(n(base + 2), "struct.tab.%d.num" % i, str(i), role="accent-ink", bold=True, size=10, background="card",
        anchor="middle")
    find(s, "struct.tab.%d.num" % i).text_frame.paragraphs[0].alignment = 2
    put(n(base + 3), "slot.stage.%d.label" % i, label, role="on-accent", bold=True, size=11,
        background="accent-deep", anchor="middle")
    put(n(base + 4), "slot.stage.%d.caption" % i, cap, role="ink-muted", size=9, anchor="middle")
    find(s, "slot.stage.%d.caption" % i).text_frame.paragraphs[0].alignment = 2

# Stage arrows between columns.
for i, x in enumerate((2.65, 5.23, 7.82, 10.41), 1):
    icon(s, "struct.arrow.%d" % i, "chevron-right", x, 3.66, 0.26, th, role="ink-muted")

# Column 1: input cards with a glyph tile.
signals = [("package", "Order profile", "Units and margin"), ("store", "Store stock", "Days of cover left"),
           ("truck", "Carrier status", "Last scan and delay"), ("map-pin", "Lane distance", "Hub to store miles"),
           ("calendar", "Promo calendar", "Upcoming events"), ("tag", "Price tier", "Markdown exposure")]
for i, (g, head, body) in enumerate(signals, 1):
    c = 33 + 4 * (i - 1)
    rename(s, n(c), "struct.input.%d" % i)
    rename(s, n(c + 1), "struct.input.%d.tile" % i)
    tile = find(s, "struct.input.%d.tile" % i)
    cx, cy = (tile.left + tile.width / 2) / EMU, (tile.top + tile.height / 2) / EMU
    icon(s, "slot.input.%d.icon" % i, g, round(cx - 0.12, 3), round(cy - 0.12, 3), 0.24, th)
    y = 2.19 + 0.80 * (i - 1)
    move(s, n(c + 2), 0.97, y + 0.06, 1.54, 0.24)
    put(n(c + 2), "slot.input.%d.head" % i, head, role="accent-ink", bold=True, size=10)
    move(s, n(c + 3), 0.97, y + 0.32, 1.54, 0.22)
    put(n(c + 3), "slot.input.%d.body" % i, body, role="ink", size=9)

# Column 2: checks, each a question, its test and the input it reads.
checks = [("Shelf empties first?", "Cover shorter than the delay", "Reads stock and carrier"),
          ("Event at stake?", "Promo starts within 7 days", "Reads promo calendar"),
          ("Margin worth saving?", "Lost margin above $5K", "Reads order profile"),
          ("Faster lane open?", "Air or direct truck free", "Reads lane distance"),
          ("Cost in bounds?", "Expedite under 20% of value", "Reads price tier"),
          ("Substitute on hand?", "Like item within 30 miles", "Reads store stock")]
for i, (q, test, src) in enumerate(checks, 1):
    c = 57 + 5 * (i - 1)
    rename(s, n(c), "struct.check.%d" % i)
    y = 2.13 + 0.80 * (i - 1)
    move(s, n(c + 2), 3.04, y + 0.04, 2.02, 0.22)
    put(n(c + 2), "slot.check.%d.head" % i, q, role="ink-deep", bold=True, size=10)
    move(s, n(c + 3), 3.04, y + 0.25, 2.02, 0.20)
    put(n(c + 3), "slot.check.%d.test" % i, test, role="accent-ink", size=9)
    move(s, n(c + 4), 3.04, y + 0.45, 2.02, 0.20)
    put(n(c + 4), "slot.check.%d.source" % i, src, role="ink-muted", size=9)

# Column 3: the rule header and five ordered rules.
rename(s, n(87), "struct.rules.head")
put(n(88), "slot.rules.head", "First match sets the route", role="on-accent",
    bold=True, size=9, background="accent", anchor="middle")
icon(s, "slot.rules.icon", "funnel", 5.63, 2.29, 0.24, th, role="on-accent")
rules = [("Promo stock-out", "Shelf empty during a promo", "Expedite by air"),
         ("Margin and lane", "Loss over limit, lane open", "Expedite by truck"),
         ("Substitute nearby", "Like item covers the gap", "Hold and transfer"),
         ("Cost over bounds", "Cost above 20% of value", "Hold and transfer"),
         ("No rule matched", "All other late orders", "Hold and transfer")]
for i, (head, cond, route) in enumerate(rules, 1):
    c = 89 + 6 * (i - 1)
    card = find(s, n(c))
    top = card.top / EMU
    rename(s, n(c), "struct.rule.%d" % i)
    rename(s, n(c + 1), "struct.rule.%d.disc" % i)
    move(s, "struct.rule.%d.disc" % i, 5.64, top + 0.05)
    move(s, n(c + 2), 5.64, top + 0.05)
    put(n(c + 2), "slot.rule.%d.num" % i, str(i), role="accent-ink", bold=True, size=9, background="card",
        anchor="middle")
    find(s, "slot.rule.%d.num" % i).text_frame.paragraphs[0].alignment = 2
    move(s, n(c + 3), 5.94, top + 0.04, 1.74, 0.22)
    put(n(c + 3), "slot.rule.%d.head" % i, head, role="ink-deep", bold=True, size=10)
    move(s, n(c + 4), 5.64, top + 0.26, 2.06, 0.20)
    put(n(c + 4), "slot.rule.%d.body" % i, cond, role="ink", size=9)
    move(s, n(c + 5), 5.64, top + 0.46, 2.06, 0.21)
    put(n(c + 5), "slot.rule.%d.route" % i, route, role="accent-ink", bold=True, size=9)

# Column 4: the two dispositions.
outs = [("Expedite now", "Carrier booked same day, cost charged to promo"),
        ("Hold and transfer", "Like item moved in, planner alerted")]
for i, (head, body) in enumerate(outs, 1):
    c = 119 + 3 * (i - 1)
    top = find(s, n(c)).top / EMU
    rename(s, n(c), "struct.outcome.%d" % i)
    move(s, n(c + 1), 8.25, top + 0.08, 1.96, 0.24)
    put(n(c + 1), "slot.outcome.%d.head" % i, head, role="ink-deep", bold=True, size=11)
    move(s, n(c + 2), 8.25, top + 0.36, 1.96, 0.40)
    put(n(c + 2), "slot.outcome.%d.body" % i, body, role="ink", size=10)

# Column 5: the decision record and one routed example.
rename(s, n(125), "struct.record")
put(n(126), "slot.record.head", "Each decision logs", role="on-accent", bold=True, size=12,
    background="accent")
move(s, n(127), 10.90, 2.76, 1.86, 1.14)
put(n(127), "slot.record.body",
    [P((R(t, "on-accent", size=11),), bullet="·", space_before=0 if j == 0 else 4)
     for j, t in enumerate(("Rule that fired", "Inputs it read", "Cost and owner", "Decision time"))],
    size=11, background="accent")
rename(s, n(128), "struct.example")
ex = find(s, "struct.example")
ex._element.find(".//" + qn("a:gd")).set("fmla", "val %d" % round(0.05 / (min(ex.width, ex.height) / EMU) * 100000))
move(s, n(129), 10.85, 4.18, 1.92, 0.24)
put(n(129), "slot.example.label", "Sample late order", role="accent-ink", bold=True, size=10, background="card")
rows = [("Cover", "2 days"), ("Promo", "in 5 days"), ("Rule fired", "1"), ("Route", "expedite by air"),
        ("Owner", "store planner")]
move(s, n(130), 10.85, 4.46, 1.92, 1.12)
put(n(130), "slot.example.body",
    [P((R(k + "  ", "ink-muted", size=10), R(v, "ink-deep", bold=True, size=10)), space_before=0 if j == 0 else 3)
     for j, (k, v) in enumerate(rows)], size=10, background="card")

out = save(prs, "DL26", th, archetype="decision-logic", variant=VARIANT)
if args.out and Path(args.out).resolve() != out.resolve():
    shutil.copyfile(out, args.out)
