"""DL04: four forum columns, each a month calendar of its meeting days over chair, members and decision rows,
a standing-rules panel under them and a numbered escalation ladder with day triggers (governance-model)."""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import text as txt  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL04")
VARIANT = "forum-calendars-escalation"


# ungroup every group (all carry identity child transforms); a grpFill child takes the group's own fill
def ungroup(g):
    gel = g._element
    gfill = gel.find(qn("p:grpSpPr") + "/" + qn("a:solidFill"))
    parent = gel.getparent()
    for ch in list(gel):
        if ch.tag in (qn("p:nvGrpSpPr"), qn("p:grpSpPr")):
            continue
        sp = ch.find(qn("p:spPr"))
        if sp is not None and sp.find(qn("a:grpFill")) is not None:
            gf = sp.find(qn("a:grpFill"))
            gf.addprevious(copy.deepcopy(gfill))
            sp.remove(gf)
        gel.addprevious(ch)
    parent.remove(gel)


import copy  # noqa: E402

again = True
while again:
    again = False
    for sh in list(s.shapes):
        if sh.shape_type == 6:
            ungroup(sh)
            again = True


def set_fill(name, role):
    sp = find(s, name)._element.find(qn("p:spPr"))
    for t in ("a:solidFill", "a:noFill", "a:grpFill", "a:gradFill"):
        for el in sp.findall(qn(t)):
            sp.remove(el)
    sf = etree.SubElement(sp, qn("a:solidFill"))
    sf.append(th.spec(role))
    sp.find(qn("a:prstGeom")).addnext(sf)


def set_line(name, role=None):
    sp = find(s, name)._element.find(qn("p:spPr"))
    for el in sp.findall(qn("a:ln")):
        sp.remove(el)
    ln = etree.SubElement(sp, qn("a:ln"), w="6350")
    if role is None:
        etree.SubElement(ln, qn("a:noFill"))
    else:
        etree.SubElement(ln, qn("a:solidFill")).append(th.spec(role))
    (sp.find(qn("a:solidFill")) if sp.find(qn("a:solidFill")) is not None else sp.find(qn("a:prstGeom"))).addnext(ln)


from lxml import etree  # noqa: E402


def set_ins(name, l=0.0, t=0.0, r=0.0, b=0.0):
    bp = find(s, name)._element.find(".//" + qn("a:bodyPr"))
    for k, v in (("lIns", l), ("tIns", t), ("rIns", r), ("bIns", b)):
        bp.set(k, str(int(round(v * EMU))))


def radius(name, r=0.05):
    sh = find(s, name)
    av = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst"))
    for gd in list(av):
        av.remove(gd)
    etree.SubElement(av, qn("a:gd"), name="adj", fmla="val %d" % round(r / (min(sh.width, sh.height) / EMU) * 100000))

# banned chrome: subtitle, mid sentence band, panel sentence, foot sentence, escalation footnote, empty item frames
for n in ("dev.3", "dev.194", "dev.209", "dev.212", "dev.226",
          "dev.197", "dev.200", "dev.203", "dev.206"):
    try:
        delete(s, n)
    except Exception:
        pass

# title
rename(s, "dev.2", "slot.title")
move(s, "slot.title", 0.48, 0.30, 12.40, 0.50)
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "Four standing forums take any escalation to a decision within ten days", ("Four standing forums",))))],
    th, size=22, bold=True, anchor="middle")

# section heads, one line each, over their rules
rename(s, "dev.6", "slot.cadence.label")
move(s, "slot.cadence.label", 0.48, 0.98, 9.18, 0.30)
text(s, "slot.cadence.label", "Forum cadence", th, size=13, bold=True, role="ink-deep", anchor="bottom")
rename(s, "dev.4", "slot.escalation.label")
move(s, "slot.escalation.label", 10.13, 0.98, 2.75, 0.30)
text(s, "slot.escalation.label", "Escalation path", th, size=13, bold=True, role="ink-deep", anchor="bottom")
rename(s, "dev.7", "struct.cadence.rule")
rename(s, "dev.8", "struct.escalation.rule")
rename(s, "dev.5", "struct.divider")

# forum columns: tab, weekday letters, 4 x 7 month grid, frequency chip, three rows
COLS = [  # tab, chip, x of column, day labels, grid x origin
    ("dev.15", "dev.193", 0.48, list(range(16, 23)), 0.59),
    ("dev.12", "dev.190", 2.65, list(range(23, 30)), 2.97),
    ("dev.13", "dev.191", 5.04, list(range(30, 37)), 5.34),
    ("dev.14", "dev.192", 7.44, list(range(37, 44)), 7.71),
]
GLYPHS = ("landmark", "list-checks", "layers", "users")
FORUMS = [  # name, chip, meeting cells (row, col) 0-based, rows
    ("Steering group", "Monthly", {(2, 3)},
     [("Chair", "Executive sponsor"), ("Members", "Both sponsors, program leads and finance"),
      ("Decides", "Budget and phase gates")]),
    ("Program board", "Every two weeks", {(0, 1), (2, 1)},
     [("Chair", "Program director"), ("Members", "Workstream leads from both parties"),
      ("Decides", "Plan changes and staffing")]),
    ("Design authority", "Weekly", {(r, 2) for r in range(4)},
     [("Chair", "Lead architect"), ("Members", "Architects, security and data owners"),
      ("Decides", "Standards and design waivers")]),
    ("Delivery stand-up", "Daily on weekdays", {(r, c) for r in range(4) for c in range(5)},
     [("Chair", "Delivery manager"), ("Members", "Squad leads and product owners"),
      ("Decides", "Blockers and daily priorities")]),
]
LABELS = [("dev.157", "dev.163", "dev.164", "dev.160"), ("dev.170", "dev.171", "dev.172", "dev.167"),
          ("dev.176", "dev.177", "dev.178", "dev.179")]
VALUES = [("dev.158", "dev.159", "dev.162", "dev.161"), ("dev.165", "dev.166", "dev.169", "dev.168"),
          ("dev.173", "dev.174", "dev.175", "dev.180")]
RULES = [("dev.181", "dev.182"), ("dev.183", "dev.184"), ("dev.185", "dev.186"), ("dev.187", "dev.188")]
GRID_Y0, PITCH_Y, CELL_H = 2.14, 0.30, 0.24
ROW_Y = (3.78, 4.30, 4.96)
ROW_HS = (0.40, 0.54, 0.40)

# grid cells in dev order: column blocks of 28, row-major
cells = list(range(45, 157))
for i, (tab, chip, cx, days, gx) in enumerate(COLS, 1):
    name, freq, on, rows = FORUMS[i - 1]
    rename(s, tab, "slot.forum.%d.name" % i)
    set_fill("slot.forum.%d.name" % i, "accent")
    set_ins("slot.forum.%d.name" % i, 0.42, 0.02, 0.08, 0.02)
    text(s, "slot.forum.%d.name" % i, name, th, size=11, bold=True, role="on-accent", background="accent",
         anchor="middle")
    tb = find(s, "slot.forum.%d.name" % i)
    icon(s, "slot.forum.%d.icon" % i, GLYPHS[i - 1], tb.left / EMU + 0.12, tb.top / EMU + (tb.height / EMU - 0.24) / 2,
         0.24, th, role="on-accent")
    for k, (n, d) in enumerate(zip(days, "MTWTFSS"), 1):
        rename(s, "dev.%d" % n, "struct.forum.%d.day.%d" % (i, k))
        text(s, "struct.forum.%d.day.%d" % (i, k), [txt.Para((txt.Run(d, "ink-muted", bold=True, size=8),),
                                                            align="center")], th, size=8)
    for j, n in enumerate(cells[(i - 1) * 28:i * 28]):
        r, c = divmod(j, 7)
        nm = "slot.forum.%d.day.%d.%d" % (i, r + 1, c + 1)
        rename(s, "dev.%d" % n, nm)
        sh = find(s, nm)
        move(s, nm, sh.left / EMU, GRID_Y0 + r * PITCH_Y, None, CELL_H)
        set_fill(nm, "accent" if (r, c) in on else "hairline")
    rename(s, chip, "slot.forum.%d.cadence" % i)
    move(s, "slot.forum.%d.cadence" % i, find(s, "slot.forum.%d.cadence" % i).left / EMU, 3.36,
         find(s, "slot.forum.%d.cadence" % i).width / EMU, 0.30)
    set_fill("slot.forum.%d.cadence" % i, "accent-wash")
    set_line("slot.forum.%d.cadence" % i, "accent")
    text(s, "slot.forum.%d.cadence" % i, [txt.Para((txt.Run(freq, "ink-deep", bold=True, size=10),),
                                                   align="center")], th, size=10, background="accent-wash",
         anchor="middle")
    for k, (lab, val) in enumerate(rows):
        ln, vn = LABELS[k][i - 1], VALUES[k][i - 1]
        rename(s, ln, "slot.forum.%d.row.%d.label" % (i, k + 1))
        rename(s, vn, "slot.forum.%d.row.%d.value" % (i, k + 1))
        lsh, vsh = find(s, ln if False else "slot.forum.%d.row.%d.label" % (i, k + 1)), \
            find(s, "slot.forum.%d.row.%d.value" % (i, k + 1))
        move(s, "slot.forum.%d.row.%d.label" % (i, k + 1), cx, ROW_Y[k], 0.74, 0.24)
        vx = cx + 0.80
        vw = (find(s, "slot.forum.%d.name" % i).left + find(s, "slot.forum.%d.name" % i).width) / EMU - vx
        move(s, "slot.forum.%d.row.%d.value" % (i, k + 1), vx, ROW_Y[k], vw, ROW_HS[k])
        text(s, "slot.forum.%d.row.%d.label" % (i, k + 1), lab, th, size=10, bold=True, role="ink-deep")
        text(s, "slot.forum.%d.row.%d.value" % (i, k + 1), val, th, size=10, role="ink")
    for k, rn in enumerate(RULES[i - 1]):
        rename(s, rn, "struct.forum.%d.rule.%d" % (i, k + 1))
        sh = find(s, "struct.forum.%d.rule.%d" % (i, k + 1))
        move(s, "struct.forum.%d.rule.%d" % (i, k + 1), sh.left / EMU, ROW_Y[k] + ROW_HS[k] + 0.06, sh.width / EMU, 0)

for k, n in enumerate(("dev.11", "dev.10", "dev.9"), 1):        # column dividers, left to right
    rename(s, n, "struct.forum.divider.%d" % k)
    sh = find(s, "struct.forum.divider.%d" % k)
    move(s, "struct.forum.divider.%d" % k, sh.left / EMU, 1.47, 0, ROW_Y[2] + ROW_HS[2] - 1.47)

# standing rules panel
PY = 5.62
rename(s, "dev.195", "struct.rules.panel")
move(s, "struct.rules.panel", 0.48, PY, 9.18, 1.20)
rename(s, "dev.210", "slot.rules.label")
move(s, "slot.rules.label", 0.69, PY + 0.12, 3.60, 0.28)
text(s, "slot.rules.label", "Standing rules for every forum", th, size=12, bold=True, role="ink-deep")
rename(s, "dev.211", "struct.rules.rule")
move(s, "struct.rules.rule", 4.40, PY + 0.26, 5.05, 0)
RULE_ITEMS = ["Decisions logged within one day", "Papers sent two days ahead of each session",
              "Quorum needs both parties present", "One shared risk and action log"]
nums = ("dev.198", "dev.201", "dev.204", "dev.207")
bodies = ("dev.199", "dev.202", "dev.205", "dev.208")
seps = ("dev.215", "dev.214", "dev.213")
IW = (9.45 - 0.69) / 4
for k in range(4):
    x = 0.69 + k * IW
    rename(s, nums[k], "slot.rules.%d.num" % (k + 1))
    rename(s, bodies[k], "slot.rules.%d.body" % (k + 1))
    move(s, "slot.rules.%d.num" % (k + 1), x, PY + 0.56, 0.36, 0.30)
    move(s, "slot.rules.%d.body" % (k + 1), x + 0.40, PY + 0.56, IW - 0.56, 0.52)
    text(s, "slot.rules.%d.num" % (k + 1), "%02d" % (k + 1), th, size=14, bold=True, role="accent-ink")
    text(s, "slot.rules.%d.body" % (k + 1), RULE_ITEMS[k], th, size=10, bold=False, role="ink")
    if k:
        rename(s, seps[k - 1], "struct.rules.sep.%d" % k)
        move(s, "struct.rules.sep.%d" % k, x - 0.10, PY + 0.56, 0, 0.48)

# escalation ladder: five cards, numbered disc, who intervenes, day trigger pill
STEPS = [("Workstream lead", "Day 1"), ("Delivery manager", "Day 2"), ("Design authority", "Day 5"),
         ("Program board", "Day 7"), ("Steering group", "Day 10")]
Y0, Y1, GAP = 1.47, PY + 1.20, 0.14
CH = (Y1 - Y0 - 4 * GAP) / 5
for k, (who, when) in enumerate(STEPS):
    i = k + 1
    y = Y0 + k * (CH + GAP)
    rename(s, "dev.%d" % (216 + k), "struct.step.%d" % i)
    move(s, "struct.step.%d" % i, 10.13, y, 2.75, CH)
    radius("struct.step.%d" % i)
    rename(s, "dev.%d" % (233 + k), "slot.step.%d.num" % i)
    move(s, "slot.step.%d.num" % i, 10.24, y + (CH - 0.40) / 2, 0.40, 0.40)
    set_line("slot.step.%d.num" % i, None)
    set_ins("slot.step.%d.num" % i)
    text(s, "slot.step.%d.num" % i, [txt.Para((txt.Run(str(i), "paper", bold=True, size=11),), align="center")],
         th, size=11, background="ink-deep", anchor="middle")
    rename(s, "dev.%d" % (221 + k), "slot.step.%d.who" % i)
    move(s, "slot.step.%d.who" % i, 10.70, y + 0.10, 1.04, CH - 0.20)
    text(s, "slot.step.%d.who" % i, who, th, size=11, bold=True, role="ink-deep", background="card", anchor="middle")
    rename(s, "dev.%d" % (228 + k), "slot.step.%d.when" % i)
    move(s, "slot.step.%d.when" % i, 11.82, y + (CH - 0.36) / 2, 0.94, 0.36)
    text(s, "slot.step.%d.when" % i, [txt.Para((txt.Run(when, "on-accent", bold=True, size=11),), align="center")],
         th, size=11, background="accent", anchor="middle")

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
out = save(prs, "DL04", th, archetype="governance-model", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
