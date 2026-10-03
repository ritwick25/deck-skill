"""DL02: challenge strip, a three-stage work band with its exhibit and failure loop, a value strip, a brief rail
(deep-dive)."""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import prims, text as txt  # noqa: E402
from lxml import etree  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL02")
VARIANT = "stage-band-brief-rail"
R, P = txt.Run, txt.Para

# chrome the house rules ban: the page-number disc
delete(s, "dev.65")


def ungroup(name):
    """Lift a group's children onto the slide at their absolute boxes, then drop the group."""
    g = find(s, name)
    gx = g._element.find(qn("p:grpSpPr") + "/" + qn("a:xfrm"))
    off, ext = gx.find(qn("a:off")), gx.find(qn("a:ext"))
    coff, cext = gx.find(qn("a:chOff")), gx.find(qn("a:chExt"))
    sx = int(ext.get("cx")) / max(int(cext.get("cx")), 1)
    sy = int(ext.get("cy")) / max(int(cext.get("cy")), 1)
    for ch in list(g._element):
        if ch.tag in (qn("p:nvGrpSpPr"), qn("p:grpSpPr")):
            continue
        x = ch.find(".//" + qn("a:xfrm"))
        o, e = x.find(qn("a:off")), x.find(qn("a:ext"))
        o.set("x", str(round(int(off.get("x")) + (int(o.get("x")) - int(coff.get("x"))) * sx)))
        o.set("y", str(round(int(off.get("y")) + (int(o.get("y")) - int(coff.get("y"))) * sy)))
        e.set("cx", str(round(int(e.get("cx")) * sx)))
        e.set("cy", str(round(int(e.get("cy")) * sy)))
        g._element.addprevious(ch)
    g._element.getparent().remove(g._element)


for n in ("dev.44", "dev.49", "dev.51", "dev.56", "dev.58"):
    ungroup(n)


# title: one claim, two-tone
rename(s, "dev.5", "slot.title")
move(s, "slot.title", 0.50, 0.20, 12.40, 0.50)
text(s, "slot.title", [P(tuple(txt.title_runs(
    "Rule passes clear routine invoices and reviewers settle the rest",
    ("Rule passes",))))], th, size=22, bold=True, anchor="middle")

# challenge strip: outlined frame, a label in the gap of its top edge, three iconned pains
rename(s, "dev.13", "struct.challenge")
move(s, "struct.challenge", 0.50, 1.00, 9.01, 1.10)
move(s, "dev.18", 3.87, 1.24, 0, 0.63)
move(s, "dev.19", 6.71, 1.24, 0, 0.63)
rename(s, "dev.14", "slot.challenge.label")
move(s, "slot.challenge.label", 0.50, 0.72, 1.83, 0.24)
text(s, "slot.challenge.label", [P((R("Challenge", "accent-ink", bold=True, size=14),))], th, size=14, anchor="middle")
rename(s, "dev.18", "struct.challenge.rule.1")
rename(s, "dev.19", "struct.challenge.rule.2")
PAINS = [  # (shape, box, glyph, glyph box, paras)
    ("dev.15", (1.58, 1.12, 2.20, 0.86), "hourglass", (0.84, 1.26, 0.58),
     [P((R("3 days", "accent-ink", bold=True, size=20),)),
      P((R("to clear one held invoice", "ink", size=12),))]),
    ("dev.16", (4.95, 1.12, 1.70, 0.86), "file-spreadsheet", (4.21, 1.26, 0.58),
     [P((R("Matching rules live in", "ink", size=12),)), P((R("personal spreadsheets", "ink", size=12),))]),
    ("dev.17", (7.76, 1.12, 1.67, 0.86), "coins", (7.05, 1.26, 0.58),
     [P((R("Late payments forfeit", "ink", size=12),)), P((R("early-pay discounts", "ink", size=12),))]),
]
for i, (n, box, g, gb, paras) in enumerate(PAINS, 1):
    rename(s, n, "slot.pain.%d.body" % i)
    move(s, "slot.pain.%d.body" % i, *box)
    text(s, "slot.pain.%d.body" % i, paras, th, size=12, anchor="middle")
    icon(s, "slot.pain.%d.icon" % i, g, gb[0], gb[1], gb[2], th, role="accent")

# work band: header bar with its illustrative tag, then three numbered stage chevrons
rename(s, "dev.20", "slot.work.head")
text(s, "slot.work.head", "How invoice matching works", th, size=13, role="on-accent", bold=True,
     background="accent", anchor="middle")
rename(s, "dev.63", "slot.work.tag")
text(s, "slot.work.tag", [P((R("Illustrative", "on-accent", italic=True, size=11),), align="right")], th,
     size=11, background="accent", anchor="middle")
STAGES = [("dev.21", "dev.28", "dev.30", "dev.29", "Capture"), ("dev.22", "dev.31", "dev.33", "dev.32", "Match"),
          ("dev.23", "dev.34", "dev.36", "dev.35", "Review")]
move(s, "dev.28", 0.58, 2.91, 0.36, 0.27)
for i, (chev, num, rule, lab, word) in enumerate(STAGES, 1):
    rename(s, chev, "struct.stage.%d" % i)
    rename(s, num, "slot.stage.%d.num" % i)
    rename(s, rule, "struct.stage.%d.rule" % i)
    rename(s, lab, "slot.stage.%d.head" % i)
    text(s, "slot.stage.%d.num" % i, "%02d" % i, th, size=16, role="accent-ink", bold=True,
         background="hairline-soft", anchor="middle")
    text(s, "slot.stage.%d.head" % i, word, th, size=13, role="ink-deep", bold=True, background="hairline-soft",
         anchor="middle")
rename(s, "dev.26", "struct.column.rule.1")
rename(s, "dev.27", "struct.column.rule.2")

# stage 1: source, capture, ledger nodes on a dashed link, the exceptions box the loop returns to
rename(s, "dev.2", "struct.capture.link")
rename(s, "dev.3", "struct.capture.node")
icon(s, "slot.capture.icon.1", "file-text", 0.81, 3.90, 0.33, th, role="ink-deep")
icon(s, "slot.capture.icon.2", "scan-search", 1.61, 3.77, 0.58, th, role="accent")
icon(s, "slot.capture.icon.3", "database", 2.66, 3.90, 0.33, th, role="ink-deep")
rename(s, "dev.50", "slot.capture.label.1")
rename(s, "dev.52", "slot.capture.label.2")
text(s, "slot.capture.label.1", [P((R("Invoices", "ink", size=11),), align="center")], th, size=11)
text(s, "slot.capture.label.2", [P((R("Ledger", "ink", size=11),), align="center")], th, size=11)
rename(s, "dev.45", "struct.exceptions")
rename(s, "dev.46", "slot.exceptions.body")
move(s, "struct.exceptions", 0.87, 4.52, 1.75, 0.72)
move(s, "slot.exceptions.body", 0.93, 4.58, 1.63, 0.60)
text(s, "slot.exceptions.body", [P((R("Held lines return with", "ink", size=11),), align="center"),
                                 P((R("a reason code", "ink", size=11),), align="center")], th, size=11,
     anchor="middle")
for n in ("dev.53", "dev.54", "dev.55"):                  # lifted fan connectors lose their line once unstyled
    delete(s, n)

# stage 2: three rule passes in order, one caption
RULES = ["Exact order and amount", "Price within tolerance", "Fuzzy supplier and line text"]
for i, (n, r) in enumerate(zip(("dev.37", "dev.38", "dev.39"), RULES), 1):
    rename(s, n, "slot.rule.%d" % i)
    text(s, "slot.rule.%d" % i, [P((R(r, "ink", size=11),), align="center")], th, size=11, background="card",
         anchor="middle")
for i in range(1, 4):                                      # the ledger fans out to each rule pass
    rb = find(s, "slot.rule.%d" % i)
    yc = (rb.top + rb.height / 2) / EMU
    prims.elbow(s, [(2.99, 4.065), (3.34, 4.065), (3.34, yc), (rb.left / EMU, yc)], role="accent", weight_pt=1.0,
                name="struct.capture.fan.%d" % i, theme=th)
rename(s, "dev.64", "slot.rule.caption")
text(s, "slot.rule.caption", [P((R("The first pass to match wins", "ink", size=11),), align="center")], th,
     size=11)

# stage 3: the review step and its two outcomes
icon(s, "slot.review.icon", "file-search", 7.80, 3.49, 0.41, th, role="ink-deep")
rename(s, "dev.40", "slot.review.body")
text(s, "slot.review.body", [P((R("Unmatched lines go to review", "ink", size=11),), align="center")], th,
     size=11)
icon(s, "struct.review.arrow", "arrow-down", 7.86, 4.43, 0.28, th, role="accent")
rename(s, "dev.4", "struct.outcomes")
rename(s, "dev.43", "struct.outcomes.rule")
move(s, "struct.outcomes.rule", 8.01, 4.91, 0, 0.62)
rename(s, "dev.41", "slot.outcome.1")
rename(s, "dev.42", "slot.outcome.2")
move(s, "slot.outcome.1", 6.80, 4.91, 1.15, 0.62)
move(s, "slot.outcome.2", 8.07, 4.91, 1.15, 0.62)
for i, (h, b) in enumerate((("Approve", "and post"), ("Return", "with a reason")), 1):
    text(s, "slot.outcome.%d" % i, [P((R(h, "ink-deep", bold=True, size=11),), align="center"),
                                    P((R(b, "ink", size=11),), align="center")], th, size=11, anchor="middle")

# failure loop: returned lines travel back to the exceptions box
delete(s, "dev.47")                                   # the lifted bent connector routes wrongly once unstyled
_ob = find(s, "struct.outcomes")
_ox, _oy = (_ob.left + _ob.width / 2) / EMU, (_ob.top + _ob.height) / EMU
_eb = find(s, "struct.exceptions")
_ex, _ey = (_eb.left + _eb.width / 2) / EMU, (_eb.top + _eb.height) / EMU
prims.elbow(s, [(_ox, _oy), (_ox, 5.885), (_ex, 5.885), (_ex, _ey)], dash="dash", role="accent", weight_pt=1.0,
            name="struct.loop", theme=th)
rename(s, "dev.48", "slot.loop.label")
move(s, "slot.loop.label", 3.46, 5.79, 3.10, 0.19)
_lab = find(s, "slot.loop.label")._element                # the label masks the loop line it sits on
_lab.getparent().append(_lab)
text(s, "slot.loop.label", [P((R("Reviewer decisions retune tolerances", "accent-ink", italic=True, size=11),),
                              align="center")], th, size=11)

# value strip: a filled label tab and three iconned outcomes, a few words each
rename(s, "dev.24", "struct.value")
rename(s, "dev.25", "struct.value.panel")
text(s, "struct.value", "Value", th, size=14, role="on-accent", bold=True, background="accent", anchor="middle")
rename(s, "struct.value", "slot.value.label")
rename(s, "dev.62", "struct.value.rule.1")
rename(s, "dev.61", "struct.value.rule.2")
VALUES = [("dev.57", (2.60, 6.33, 1.45, 0.27), "piggy-bank", 2.14, "Discounts kept"),
          ("dev.59", (4.92, 6.33, 1.50, 0.27), "layers", 4.50, "One rule set"),
          ("dev.60", (7.27, 6.33, 2.10, 0.27), "timer", 6.81, "Same-day clearing")]
for i, (n, box, g, gx, w) in enumerate(VALUES, 1):
    rename(s, n, "slot.value.%d.body" % i)
    move(s, "slot.value.%d.body" % i, *box)
    text(s, "slot.value.%d.body" % i, w, th, size=12, anchor="middle")
    icon(s, "slot.value.%d.icon" % i, g, gx, 6.28, 0.36, th, role="accent")

# brief rail: problem, why it matters, approach, scope, and the boxed decision it supports
rename(s, "dev.6", "struct.brief")
W = "accent-wash"
rename(s, "dev.7", "slot.brief.head")
text(s, "slot.brief.head", "Use case brief", th, size=15, role="accent-ink", bold=True, background=W)
rename(s, "dev.8", "slot.brief.problem")
move(s, "slot.brief.problem", 10.11, 1.42, 2.62, 0.52)
text(s, "slot.brief.problem", "Supplier invoices stall in manual matching", th, size=13, role="ink-deep",
     bold=True, background=W)
BLOCKS = [("dev.9", "slot.brief.why", 2.20, 0.88, "Why it matters",
           "Held invoices delay payment runs and miss discount windows"),
          ("dev.10", "slot.brief.approach", 3.30, 0.88, "Approach",
           "Rule passes match routine lines and reviewers clear the rest"),
          ("dev.11", "slot.brief.scope", 4.40, 0.88, "Scope",
           "One ledger, three entities and twelve weeks")]
for n, name, y, h, head, body in BLOCKS:
    rename(s, n, name)
    move(s, name, 10.11, y, 2.62, h)
    text(s, name, [P((R(head, "ink-deep", bold=True, size=12),)), P((R(body, "ink", size=12),), space_before=2)],
         th, size=12, background=W)
rename(s, "dev.12", "slot.brief.decision")
move(s, "slot.brief.decision", 10.11, 5.56, 2.62, 1.08)
text(s, "slot.brief.decision", [P((R("Decision supported", "accent-ink", bold=True, size=12),), align="center"),
                                P((R("Fund a twelve-week pilot on one ledger", "ink", size=12),), align="center",
                                  space_before=2)], th, size=12, anchor="middle")

out = save(prs, "DL02", th, archetype="deep-dive", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
