"""DL18: five slanted lanes that route one inventory by ordered rules (decision-logic, lifted from d03-s017)."""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F401,F403
from devwork import EMU, find, glyph, txt, Box, qn  # noqa: E402
from deckkit import prims  # noqa: E402
from deckkit.canvas import WIDE  # noqa: E402

VARIANT = "slanted-lanes"

ap = argparse.ArgumentParser()
ap.add_argument("--out")
args = ap.parse_args()

prs, s, th = open_lifted("DL18")
prims.bind(th)


def T(name, value, role, size, bold=False, align="left", bg="paper", anchor="top"):
    lines = [value] if isinstance(value, str) else value
    paras = [txt.Para((txt.Run(v, role, bold=bold, size=size),), align=align,
                      space_before=0 if i == 0 else 2) for i, v in enumerate(lines)]
    text(s, name, paras, th, size=size, background=bg, anchor=anchor)


def R(old, new, x=None, y=None, w=None, h=None):
    rename(s, old, new)
    if x is not None:
        move(s, new, x, y, w, h)


def fill(name, role):
    prims.set_fill(find(s, name), role, theme=th)


# 1. Banned and corpus residue: subtitle, decorative left bar, the slide's own vector icons and check marks
for n in ["dev.69", "dev.70", "dev.12", "dev.15", "dev.78", "dev.82", "dev.86", "dev.90",
          "dev.79", "dev.83", "dev.87", "dev.91", "dev.94", "dev.98", "dev.107", "dev.108", "dev.111"]:
    delete(s, n)

# Title
txt.title(s, "Two signals route every supplier invoice to one of five handling lanes",
          keywords=("Two signals", "five handling lanes"), canvas=WIDE, theme=th, name="slot.title")
move(s, "slot.title", 0.42, 0.30, 12.50, 0.40)

# 2. Signals row
R("dev.4", "slot.signals.label", 0.42, 0.98, 3.00, 0.24)
T("slot.signals.label", "Signals on arrival", "ink-deep", 11, bold=True)
for k, (disc, head, body, x, gname, h_txt, b_txt) in enumerate([
        ("dev.5", "dev.7", "dev.8", 0.42, "gauge", "Match score", "Order, receipt and invoice agree"),
        ("dev.6", "dev.9", "dev.10", 4.04, "triangle-alert", "Exception flags", "Duplicate, price or tax variance")], 1):
    R(disc, "struct.signal.%d.disc" % k, x, 1.32, 0.42, 0.42)
    fill("struct.signal.%d.disc" % k, "card")
    icon(s, "slot.signal.%d.icon" % k, gname, x + 0.10, 1.42, 0.22, th, role="accent-ink")
    R(head, "slot.signal.%d.head" % k, x + 0.50, 1.28, 3.00, 0.24)
    T("slot.signal.%d.head" % k, h_txt, "ink-deep", 11, bold=True)
    R(body, "slot.signal.%d.body" % k, x + 0.50, 1.52, 3.00, 0.24)
    T("slot.signal.%d.body" % k, b_txt, "ink-muted", 10)
R("dev.11", "struct.note.panel", 8.31, 1.20, 4.61, 0.62)
fill("struct.note.panel", "accent-wash")
R("dev.13", "slot.note.body", 8.43, 1.27, 4.37, 0.48)
T("slot.note.body", ["Rules run top to bottom", "The first rule that matches sets the lane"], "ink-deep", 10,
  bg="accent-wash", anchor="middle")
R("dev.56", "struct.rule.top", 0.42, 2.00, 12.50, 0)

# 3. The lanes
R("dev.14", "slot.lanes.label", 0.42, 2.14, 9.00, 0.26)
T("slot.lanes.label", "Handling lanes, tested in order", "ink-deep", 12, bold=True)
CT, CH, CW = 2.52, 2.25, 2.31
OFF = 0.25 * min(CH, CW)                         # the parallelogram's slant run at adj 25000
delete(s, "dev.2")                               # the track behind the lanes overlaps them, chevrons carry the order
LANES = [
    ("dev.16", "dev.21", "dev.22", "dev.23", "dev.24", "accent", "on-accent", "on-accent", "ink-deep", "paper",
     "circle-check", "Straight through", "Auto-post"),
    ("dev.17", "dev.25", "dev.26", "dev.27", "dev.28", "accent-wash", "accent-ink", "ink-deep", "accent", "on-accent",
     "scale", "Price variance", "Buyer"),
    ("dev.18", "dev.29", "dev.30", "dev.31", "dev.32", "ink-deep", "paper", "paper", "accent", "on-accent",
     "receipt", "Tax mismatch", "Tax desk"),
    ("dev.19", "dev.33", "dev.34", "dev.35", "dev.36", "hairline", "ink-deep", "ink-deep", "accent", "on-accent",
     "files", "Duplicate risk", "AP lead"),
    ("dev.20", "dev.37", "dev.38", "dev.39", "dev.40", "hairline-soft", "ink-deep", "ink-deep", "accent", "on-accent",
     "lock", "Vendor on hold", "Hold"),
]
XS = [0.42, 2.95, 5.48, 8.01, 10.54]


def mid_x(x, y):
    """The parallelogram's centre line at height y (its top edge is offset right by OFF)."""
    t = (y - CT) / CH
    return x + OFF * (1 - t) + (CW - OFF) / 2


for k, (shape, num, head, pill, owner, bg, num_role, head_role, pill_fill, pill_role, gname, h_txt, o_txt) in \
        enumerate(LANES, 1):
    x = XS[k - 1]
    R(shape, "struct.lane.%d.shape" % k, x, CT, CW, CH)
    icon(s, "slot.lane.%d.icon" % k, gname, x + CW - 0.62, CT + 0.16, 0.32, th, role=num_role)
    ny, nh = CT + 0.22, 0.70
    R(num, "struct.lane.%d.numeral" % k, mid_x(x, ny + nh / 2) - 0.55, ny, 0.90, nh)
    T("struct.lane.%d.numeral" % k, "%02d" % k, num_role, 36, bold=True, bg=bg, anchor="middle")
    hy, hh = CT + 0.96, 0.50
    R(head, "slot.lane.%d.head" % k, mid_x(x, hy + hh / 2) - 0.78, hy, 1.56, hh)
    T("slot.lane.%d.head" % k, h_txt, head_role, 13, bold=True, align="center", bg=bg, anchor="middle")
    py, pw = CT + 1.56, 1.00
    px = mid_x(x, py + 0.15) - pw / 2
    R(pill, "struct.lane.%d.pill" % k, px, py, pw, 0.30)
    fill("struct.lane.%d.pill" % k, pill_fill)
    R(owner, "slot.lane.%d.owner" % k, px, py, pw, 0.30)
    T("slot.lane.%d.owner" % k, o_txt, pill_role, 10, bold=True, align="center", bg=pill_fill, anchor="middle")
fill("struct.lane.1.pill", "ink-deep")
for k in range(1, 5):                            # order chevrons centred in the gap between lanes
    gx = XS[k - 1] + (CW + XS[k] - XS[k - 1]) / 2
    icon(s, "struct.lane.order.%d" % k, "chevron-right", gx - 0.14, CT + CH / 2 - 0.14, 0.28, th, role="ink-muted")

# 4. Rule row under the lanes
RY = CT + CH + 0.18
R("dev.41", "slot.rules.label", 0.42, RY, 12.43, 0.24)
T("slot.rules.label", "Rule that sends an invoice to the lane", "ink-deep", 11, bold=True)
RULES = [("dev.42", "dev.43", "Score 95 and up", "No open flags"),
         ("dev.45", "dev.46", "Price off by over 2%", "Buyer confirms or credits"),
         ("dev.48", "dev.49", "Tax code differs", "Tax desk fixes the code"),
         ("dev.51", "dev.52", "Same amount and date", "Second copy held"),
         ("dev.54", "dev.55", "Vendor on watch list", "Payment held until cleared")]
for k, (hd, bd, h_txt, b_txt) in enumerate(RULES, 1):
    x = XS[k - 1]
    R(hd, "slot.rule.%d.head" % k, x, RY + 0.32, 2.20, 0.24)
    T("slot.rule.%d.head" % k, h_txt, "ink-deep", 11, bold=True)
    R(bd, "slot.rule.%d.body" % k, x, RY + 0.56, 2.20, 0.24)
    T("slot.rule.%d.body" % k, b_txt, "ink-muted", 10)
for k, d in enumerate(["dev.44", "dev.47", "dev.50", "dev.53"], 1):
    R(d, "struct.rule.divider.%d" % k, XS[k] - 0.13, RY + 0.34, 0, 0.44)

# 5. Controls panel, bottom left
BY = RY + 1.02
R("dev.3", "struct.controls.panel", 0.42, BY, 6.10, 0.98)
find(s, "struct.controls.panel")._element.find(".//" + qn("a:gd")).set("fmla", "val %d" % round(0.05 / 0.98 * 100000))
R("dev.58", "slot.controls.label", 0.56, BY + 0.10, 5.80, 0.26)
T("slot.controls.label", "Controls on every lane", "ink-deep", 12, bold=True, bg="accent-wash")
fill("struct.controls.panel", "accent-wash")
CTRL = [("dev.71", "Audit trail kept"), ("dev.72", "Reason coded"), ("dev.74", "Owner named"),
        ("dev.76", "Spot checked")]
CX0, CWD = 0.56, 5.82 / 4
for k, (nm, c_txt) in enumerate(CTRL, 1):
    cx = CX0 + (k - 1) * CWD
    icon(s, "slot.control.%d.icon" % k, "circle-check", cx, BY + 0.50, 0.26, th, role="ink-deep")
    R(nm, "slot.control.%d.text" % k, cx + 0.32, BY + 0.44, CWD - 0.46, 0.40)
    T("slot.control.%d.text" % k, c_txt, "ink-deep", 10, bg="accent-wash", anchor="middle")
for k, d in enumerate(["dev.73", "dev.75", "dev.77"], 1):
    R(d, "struct.controls.divider.%d" % k, CX0 + k * CWD - 0.08, BY + 0.47, 0, 0.34)

# 6. Escalation clock, bottom right
R("dev.57", "struct.clock.rule", 6.80, BY, 6.12, 0)
R("dev.59", "slot.clock.label", 6.80, BY + 0.10, 4.00, 0.26)
T("slot.clock.label", "Escalation clock for open cases", "ink-deep", 12, bold=True)
DX = [7.10, 8.95, 10.80, 12.62]
LY = BY + 0.58
R("dev.63", "struct.clock.line", DX[0] + 0.12, LY, DX[-1] - DX[0], 0)
CLOCK = [("dev.64", "dev.60", "Day 0 routed"), ("dev.65", "dev.61", "Day 2 reminder"),
         ("dev.66", "dev.62", "Day 5 escalated"), ("dev.67", "dev.68", "Day 10 closed")]
for k, (dot, lab, l_txt) in enumerate(CLOCK, 1):
    cx = DX[k - 1] + 0.12
    R(dot, "struct.clock.dot.%d" % k, cx - 0.14, LY - 0.14, 0.28, 0.28)
    bp = find(s, "struct.clock.dot.%d" % k)._element.find(".//" + qn("a:bodyPr"))
    for a in ("lIns", "tIns", "rIns", "bIns"):
        bp.set(a, "0")
    T("struct.clock.dot.%d" % k, str(k), "on-accent", 9, bold=True, align="center", bg="accent", anchor="middle")
    lw = 1.30
    lx = min(cx - lw / 2, 12.92 - lw)
    R(lab, "slot.clock.%d.text" % k, lx, LY + 0.20, lw, 0.24)
    T("slot.clock.%d.text" % k, l_txt, "ink-deep", 10, align="right" if lx < cx - lw / 2 else "center")

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
out = save(prs, "DL18", th, archetype="decision-logic", variant=VARIANT)
if args.out and Path(args.out).resolve() != out.resolve():
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(out, args.out)
print(out)
