"""DL07: a gated pipeline strip (input, gate, three-stage group, gate, output) over four stage cards, the wide
middle card carrying a numbered five-step sub-flow, with an enabler rail beneath (process-flow)."""
import argparse
import copy
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import text as txt  # noqa: E402
from lxml import etree  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL07")
VARIANT = "gated-pipeline-stage-cards"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"


def fill(name, scheme="accent1"):
    """Give a shape a flat scheme fill (the lift left the gate and step discs unfilled)."""
    sp = find(s, name)._element.find(qn("p:spPr"))
    for old in sp.findall(qn("a:solidFill")) + sp.findall(qn("a:noFill")):
        sp.remove(old)
    f = etree.SubElement(sp, qn("a:solidFill"))
    etree.SubElement(f, qn("a:schemeClr")).set("val", scheme)
    sp.find(qn("a:prstGeom")).addnext(f)


def copy_look(dst, src):
    """dst takes src's fill and outline."""
    dp = find(s, dst)._element.find(qn("p:spPr"))
    sp = find(s, src)._element.find(qn("p:spPr"))
    for tag in ("a:solidFill", "a:noFill", "a:ln"):
        for old in dp.findall(qn(tag)):
            dp.remove(old)
    anchor = dp.find(qn("a:prstGeom"))
    anchor.addnext(copy.deepcopy(sp.find(qn("a:ln"))))
    anchor.addnext(copy.deepcopy(sp.find(qn("a:solidFill"))))


def two(head, body, hsize=11, bsize=10, role="ink", align="left"):
    return [txt.Para((txt.Run(head, "ink-deep", bold=True, size=hsize),), align=align),
            txt.Para((txt.Run(body, role, size=bsize),), align=align, space_before=1)]


# chrome the house rules ban: the subtitle under the title, and an empty leftover group
for n in ("dev.12", "dev.90"):
    delete(s, n)

# title: one claim, two-tone
rename(s, "dev.2", "slot.title")
move(s, "slot.title", 0.47, 0.28, 12.40, 0.50)
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "Routine supplier invoices post the same day through one gated pipeline", ("post the same day",))))],
    th, size=22, bold=True, anchor="middle")

# ---- pipeline strip -------------------------------------------------------------------------------------------
rename(s, "dev.13", "struct.flow.input")
rename(s, "dev.22", "slot.flow.input.label")
move(s, "slot.flow.input.label", 1.12, 1.47, 0.94, 0.46)
text(s, "slot.flow.input.label", ["Supplier", "invoices"], th, size=11, bold=True, role="ink-deep",
     background="accent-wash", anchor="middle")
icon(s, "slot.flow.input.icon", "mail", 0.66, 1.51, 0.38, th, role="accent")

for i, (circ, lab, word, gx) in enumerate((("dev.17", "dev.23", "Intake gate", 2.628),
                                           ("dev.16", "dev.30", "Approval gate", 10.115)), 1):
    rename(s, circ, "struct.flow.gate.%d" % i)
    fill("struct.flow.gate.%d" % i)
    rename(s, lab, "slot.flow.gate.%d.label" % i)
    c = find(s, "struct.flow.gate.%d" % i)
    cx = (c.left + c.width / 2) / EMU
    move(s, "slot.flow.gate.%d.label" % i, cx - 0.60, 2.06, 1.20, 0.22)
    text(s, "slot.flow.gate.%d.label" % i, [txt.Para((txt.Run(word, "accent-ink", bold=True, size=10),),
                                                     align="center")], th, size=10)
    icon(s, "slot.flow.gate.%d.icon" % i, "shield-check", cx - 0.16, 1.70 - 0.16, 0.32, th, role="on-accent")

rename(s, "dev.14", "struct.flow.group")
rename(s, "dev.35", "slot.flow.group.label")
move(s, "slot.flow.group.label", 5.36, 1.02, 2.60, 0.26)
text(s, "slot.flow.group.label", "Straight-through processing", th, size=11, bold=True, role="ink-deep",
     anchor="middle")
icon(s, "slot.flow.group.icon", "workflow", 4.98, 1.00, 0.30, th, role="accent")
for i, (n, w) in enumerate((("dev.26", "Extract fields"), ("dev.27", "Match to order"),
                            ("dev.28", "Code to ledger")), 1):
    rename(s, n, "slot.flow.stage.%d" % i)
    st = find(s, "slot.flow.stage.%d" % i)
    move(s, "slot.flow.stage.%d" % i, (st.left + st.width / 2) / EMU - 0.70, st.top / EMU, 1.40, st.height / EMU)
    text(s, "slot.flow.stage.%d" % i, [txt.Para((txt.Run(w, "ink-deep", bold=True, size=10),), align="center")],
         th, size=10, anchor="middle")
for i, (disc, lab, w) in enumerate((("dev.33", "dev.24", "Validated"), ("dev.34", "dev.25", "Matched")), 1):
    rename(s, disc, "struct.flow.check.%d" % i)
    d = find(s, "struct.flow.check.%d" % i)
    icon(s, "slot.flow.check.%d.icon" % i, "circle-check", d.left / EMU, d.top / EMU, d.width / EMU, th,
         role="accent")
    rename(s, lab, "slot.flow.check.%d.label" % i)
    cx = d.left / EMU + d.width / EMU / 2
    move(s, "slot.flow.check.%d.label" % i, cx - 0.45, 2.06, 0.90, 0.22)
    text(s, "slot.flow.check.%d.label" % i, [txt.Para((txt.Run(w, "accent-ink", bold=True, size=10),),
                                                      align="center")], th, size=10)

rename(s, "dev.15", "struct.flow.output")
rename(s, "dev.36", "struct.flow.output.rule")
rename(s, "dev.29", "slot.flow.output.label")
move(s, "slot.flow.output.label", 11.74, 1.47, 1.10, 0.46)
text(s, "slot.flow.output.label", ["Posted to", "the ledger"], th, size=11, bold=True, role="ink-deep",
     background="accent-wash", anchor="middle")
icon(s, "slot.flow.output.icon", "database", 11.11, 1.51, 0.38, th, role="accent")

for k, n in enumerate(("dev.18", "dev.19", "dev.32", "dev.31", "dev.20", "dev.21"), 1):
    rename(s, n, "struct.flow.link.%d" % k)
for k, (a0, a1) in ((3, (1, 2)), (4, (2, 3))):        # links run stage edge to stage edge
    l, r = find(s, "slot.flow.stage.%d" % a0), find(s, "slot.flow.stage.%d" % a1)
    lk = find(s, "struct.flow.link.%d" % k)
    move(s, "struct.flow.link.%d" % k, (l.left + l.width) / EMU, lk.top / EMU, (r.left - l.left - l.width) / EMU, 0)

# ---- stage cards ----------------------------------------------------------------------------------------------
CARD_TOP, CARD_H = 2.40, 3.42
ROW_Y = (3.50, 4.34, 5.18)
CARDS = [  # card, ordinal, head, rows, dividers, glyph, icon x, head text, row texts
    ("dev.37", "dev.86", "dev.51", ("dev.41", "dev.42", "dev.43"), ("dev.56", "dev.57"), "files",
     1.484, "Capture", ("Invoices arrive by email, portal and scan",
                        "One inbox replaces six regional mailboxes",
                        "Duplicates removed before any processing")),
    ("dev.38", "dev.87", "dev.52", ("dev.44", "dev.45", "dev.46"), ("dev.58", "dev.59"), "shield-check",
     4.046, "Check", ("Supplier verified against the master list",
                      "A missing purchase order sends it back",
                      "Fraud signals hold the invoice for review")),
    ("dev.40", "dev.88", "dev.53", ("dev.47", "dev.48", "dev.50"), ("dev.60", "dev.62"), "clipboard-check",
     11.518, "Post", ("Approved invoices post to the ledger daily",
                      "Payment runs on agreed supplier terms",
                      "Routine invoices close the same day")),
]
for n in ("dev.49", "dev.61"):                 # card 4 keeps three rows, like its neighbours
    delete(s, n)

for i, (card, num, head, rows, divs, g, ix, h, lines) in zip((1, 2, 4), CARDS):
    c = find(s, card)
    cx = c.left / EMU
    rename(s, card, "struct.card.%d" % i)
    move(s, "struct.card.%d" % i, cx, CARD_TOP, c.width / EMU, CARD_H)
    rename(s, num, "slot.card.%d.num" % i)
    move(s, "slot.card.%d.num" % i, cx + 0.20, 2.58, 0.60, 0.36)
    text(s, "slot.card.%d.num" % i, "%02d" % i, th, role="accent-ink", background="card")
    icon(s, "slot.card.%d.icon" % i, g, ix, 2.56, 0.394, th, role="ink-deep")
    rename(s, head, "slot.card.%d.head" % i)
    move(s, "slot.card.%d.head" % i, cx + 0.20, 3.04, 1.97, 0.26)
    text(s, "slot.card.%d.head" % i, h, th, size=13, bold=True, role="ink-deep", background="card")
    for j, (r, y, t) in enumerate(zip(rows, ROW_Y, lines), 1):
        rename(s, r, "slot.card.%d.row.%d" % (i, j))
        move(s, "slot.card.%d.row.%d" % (i, j), cx + 0.20, y, 1.97, 0.46)
        last = i == 4 and j == 3
        text(s, "slot.card.%d.row.%d" % (i, j), [txt.Para((txt.Run(t, "accent-ink" if last else "ink",
                                                                   bold=last, size=11),))],
             th, size=11, background="card")
    for j, (dv, y) in enumerate(zip(divs, (4.17, 5.01)), 1):
        rename(s, dv, "struct.card.%d.rule.%d" % (i, j))
        move(s, "struct.card.%d.rule.%d" % (i, j), cx + 0.20, y, 1.97, 0)

# the wide card: a numbered five-step sub-flow
c = find(s, "dev.39")
rename(s, "dev.39", "struct.card.3")
move(s, "struct.card.3", c.left / EMU, CARD_TOP, c.width / EMU, CARD_H)
rename(s, "dev.89", "slot.card.3.num")
move(s, "slot.card.3.num", 5.82, 2.58, 0.60, 0.36)
text(s, "slot.card.3.num", "03", th, role="accent-ink", background="card")
icon(s, "slot.card.3.icon", "cpu", 7.782, 2.56, 0.394, th, role="ink-deep")
rename(s, "dev.54", "slot.card.3.head")
move(s, "slot.card.3.head", 5.82, 3.04, 4.32, 0.26)
text(s, "slot.card.3.head", "Process", th, size=13, bold=True, role="ink-deep", background="card")
rename(s, "dev.55", "slot.card.3.body")
move(s, "slot.card.3.body", 5.82, 3.44, 4.32, 0.46)
text(s, "slot.card.3.body", "Five automated steps clear a routine invoice untouched", th, size=11,
     background="card")

STEPS = (("Read", "Scan to text"), ("Extract", "Header and lines"), ("Match", "Order and receipt"),
         ("Code", "Ledger and tax"), ("Route", "Approver by value"))
LX = (5.81, 6.69, 7.58, 8.47, 9.36)
LW = 0.80
INSET = 0.06                                  # text ink clears the dashed dividers either side


def zero_insets(name):
    bp = find(s, name)._element.find(".//" + qn("a:bodyPr"))
    for att in ("lIns", "rIns"):
        bp.set(att, "0")


for k, (disc, lab, desc, (w, d)) in enumerate(zip(range(77, 82), range(63, 68), range(68, 73), STEPS), 1):
    cxk = LX[k - 1] + LW / 2
    rename(s, "dev.%d" % disc, "slot.card.3.step.%d.num" % k)
    fill("slot.card.3.step.%d.num" % k)
    bp = find(s, "slot.card.3.step.%d.num" % k)._element.find(".//" + qn("a:bodyPr"))
    for att in ("lIns", "tIns", "rIns", "bIns"):
        bp.set(att, "0")
    move(s, "slot.card.3.step.%d.num" % k, cxk - 0.15, 4.24, 0.30, 0.30)
    text(s, "slot.card.3.step.%d.num" % k, [txt.Para((txt.Run(str(k), "on-accent", bold=True, size=10),),
                                                     align="center")], th, size=10, anchor="middle",
         background="accent")
    rename(s, "dev.%d" % lab, "slot.card.3.step.%d.label" % k)
    move(s, "slot.card.3.step.%d.label" % k, LX[k - 1], 4.70, LW, 0.22)
    text(s, "slot.card.3.step.%d.label" % k, [txt.Para((txt.Run(w, "ink-deep", bold=True, size=11),),
                                                       align="center")], th, size=11, background="card")
    rename(s, "dev.%d" % desc, "slot.card.3.step.%d.desc" % k)
    move(s, "slot.card.3.step.%d.desc" % k, LX[k - 1] + INSET, 4.96, LW - 2 * INSET, 0.52)
    zero_insets("slot.card.3.step.%d.desc" % k)       # the inset is in the box: clear of both dividers
    text(s, "slot.card.3.step.%d.desc" % k, [txt.Para((txt.Run(d, "ink", size=10),), align="center")], th,
         size=10, background="card")
for k, n in enumerate(range(82, 86), 1):     # arrows run disc edge to disc edge
    rename(s, "dev.%d" % n, "struct.card.3.arrow.%d" % k)
    x0 = LX[k - 1] + LW / 2 + 0.16
    x1 = LX[k] + LW / 2 - 0.16
    move(s, "struct.card.3.arrow.%d" % k, x0, 4.33, x1 - x0, 0.12)
for k, n in enumerate(range(73, 77), 1):     # column rules between the steps
    rename(s, "dev.%d" % n, "struct.card.3.rule.%d" % k)
    move(s, "struct.card.3.rule.%d" % k, LX[k] - 0.045, 4.70, 0, 0.80)

# ---- enabler rail ---------------------------------------------------------------------------------------------
rename(s, "dev.3", "struct.rail")
copy_look("struct.rail", "struct.card.1")
move(s, "struct.rail", 0.50, 6.00, 12.40, 0.82)
rename(s, "dev.4", "struct.rail.tab")
move(s, "struct.rail.tab", 0.63, 6.10, 2.05, 0.62)
ITEMS = (("dev.5", "file-check", "Audit trail", "Every action logged"),
         ("dev.6", "users", "Exception desk", "Held items cleared"),
         ("dev.7", "gauge", "Model watch", "Accuracy read weekly"),
         ("dev.8", "lock", "Access rules", "Approval by role"))
rename(s, "struct.rail.tab", "slot.rail.label")
text(s, "slot.rail.label", [txt.Para((txt.Run("Shared controls", "paper", bold=True, size=11),)),
                            txt.Para((txt.Run("under every step", "paper", size=10),), space_before=1)],
     th, size=11, background="ink-deep", anchor="middle")
IX = (2.86, 5.41, 7.88, 10.31)
SEP = (5.05, 7.52, 9.95)
for k, ((n, g, h, b), ix) in enumerate(zip(ITEMS, IX), 1):
    rename(s, n, "slot.rail.item.%d" % k)
    right = (SEP[k - 1] - 0.08) if k < 4 else 12.78
    move(s, "slot.rail.item.%d" % k, ix + 0.58, 6.13, right - (ix + 0.58), 0.56)
    text(s, "slot.rail.item.%d" % k, two(h, b, 11, 10), th, size=11, background="card", anchor="middle")
    icon(s, "slot.rail.item.%d.icon" % k, g, ix, 6.21, 0.40, th, role="ink-deep")
for k, n in enumerate(("dev.11", "dev.10", "dev.9"), 1):
    rename(s, n, "struct.rail.rule.%d" % k)
    move(s, "struct.rail.rule.%d" % k, SEP[k - 1], 6.16, 0, 0.50)



def radius(name, r=0.05):
    sh = find(s, name)
    av = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst"))
    gd = av.find(qn("a:gd"))
    if gd is None:
        gd = etree.SubElement(av, qn("a:gd"))
        gd.set("name", "adj")
    gd.set("fmla", "val %d" % round(r / (min(sh.width, sh.height) / EMU) * 100000))


for n in ("struct.card.1", "struct.card.2", "struct.card.3", "struct.card.4", "struct.rail", "struct.flow.group",
          "struct.flow.input", "struct.flow.output", "slot.flow.stage.1", "slot.flow.stage.2", "slot.flow.stage.3"):
    radius(n)

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
out = save(prs, "DL07", th, archetype="process-flow", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
