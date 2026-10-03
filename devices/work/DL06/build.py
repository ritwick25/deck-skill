"""DL06: a shared foundation bar feeds four wave headers, each fanning out to three site cards, with a
readiness checklist beside it and a four-step band every wave repeats (phased-roadmap)."""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import prims, text as txt  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL06")
VARIANT = "wave-fanout-sites"



def ungroup(name):
    """Lift a group's children onto its parent at their absolute boxes, then drop the group."""
    g = find(s, name)
    el = g._element
    x = el.find(qn("p:grpSpPr") + "/" + qn("a:xfrm"))
    off, ext = x.find(qn("a:off")), x.find(qn("a:ext"))
    choff, chext = x.find(qn("a:chOff")), x.find(qn("a:chExt"))
    ox, oy, ex, ey = (int(off.get("x")), int(off.get("y")), int(ext.get("cx")), int(ext.get("cy")))
    cx0, cy0, cex, cey = (int(choff.get("x")), int(choff.get("y")), int(chext.get("cx")), int(chext.get("cy")))
    sx, sy = ex / cex if cex else 1.0, ey / cey if cey else 1.0
    parent = el.getparent()
    for ch in list(el):
        if ch.tag in (qn("p:nvGrpSpPr"), qn("p:grpSpPr")):
            continue
        xf = ch.find(".//" + qn("a:xfrm"))
        if xf is not None:
            o, e = xf.find(qn("a:off")), xf.find(qn("a:ext"))
            o.set("x", str(round(ox + (int(o.get("x")) - cx0) * sx)))
            o.set("y", str(round(oy + (int(o.get("y")) - cy0) * sy)))
            e.set("cx", str(round(int(e.get("cx")) * sx)))
            e.set("cy", str(round(int(e.get("cy")) * sy)))
        el.addprevious(ch)
    parent.remove(el)


def tight(name, lr=0.04, tb=0.02):
    bp = find(s, name)._element.find(".//" + qn("a:bodyPr"))
    for k, v in (("lIns", lr), ("rIns", lr), ("tIns", tb), ("bIns", tb)):
        bp.set(k, str(round(v * EMU)))


def radius(name, r=0.05):
    sh = find(s, name)
    gd = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst") + "/" + qn("a:gd"))
    gd.set("fmla", "val %d" % round(r / (min(sh.width, sh.height) / EMU) * 100000))


ungroup("dev.72")
ungroup("dev.47")

# chrome the house rules ban: the subtitle under the title
delete(s, "dev.3")

# title: one claim, two-tone
rename(s, "dev.2", "slot.title")
move(s, "slot.title", 0.48, 0.22, 12.40, 0.55)
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "Four waves take twelve sites live in nine months on one foundation", ("twelve sites",))))],
    th, size=22, bold=True, anchor="middle")

# left panel: six readiness checks, numbered
rename(s, "dev.4", "struct.panel")
radius("struct.panel")
rename(s, "dev.5", "slot.panel.head")
move(s, "slot.panel.head", 0.64, 1.04, 2.40, 0.40)
text(s, "slot.panel.head", "Go-live checks per site", th, size=11, bold=True, role="ink-deep",
     background="accent-wash")
CHECKS = [("Data quality", "Master data passes audit"),
          ("Process fit", "Steps mapped to standard"),
          ("Super users", "Two trained leads per shift"),
          ("Cutover plan", "Rollback proven in rehearsal"),
          ("Interfaces", "End-to-end tests signed off"),
          ("Hypercare", "Desk staffed for four weeks")]
ROW_Y = [1.47, 2.07, 2.67, 3.27, 3.87, 4.47]
for i, (num, body, (h, b)) in enumerate(zip(range(17, 23), range(6, 12), CHECKS), 1):
    rename(s, "dev.%d" % num, "slot.check.%d.num" % i)
    text(s, "slot.check.%d.num" % i, "%02d" % i, th, role="on-accent", background="accent", anchor="middle")
    rename(s, "dev.%d" % body, "slot.check.%d.body" % i)
    move(s, "slot.check.%d.body" % i, 1.10, ROW_Y[i - 1], 1.92, 0.56)
    text(s, "slot.check.%d.body" % i, [
        txt.Para((txt.Run(h, "ink-deep", bold=True, size=10),)),
        txt.Para((txt.Run(b, "ink", size=10),), space_before=1)], th, size=10, background="accent-wash",
        anchor="middle")
for i, n in enumerate(range(12, 17), 1):
    rename(s, "dev.%d" % n, "struct.check.rule.%d" % i)

# shared foundation bar with its six components
rename(s, "dev.23", "struct.foundation")
rename(s, "dev.30", "slot.foundation.label")
move(s, "slot.foundation.label", 4.06, 1.03, 1.68, 0.68)
text(s, "slot.foundation.label", [
    txt.Para((txt.Run("Shared foundation", "paper", bold=True, size=11),)),
    txt.Para((txt.Run("Built once, reused", "paper", size=10),), space_before=1)], th, size=11,
    background="ink-deep", anchor="middle")
icon(s, "slot.foundation.icon", "layers", 3.55, 1.17, 0.40, th, role="paper")
PARTS = ["Data model", "Interfaces", "Security roles", "Reports", "Training kit", "Support desk"]
for i, (n, p) in enumerate(zip(range(24, 30), PARTS), 1):
    rename(s, "dev.%d" % n, "slot.foundation.part.%d" % i)
    tight("slot.foundation.part.%d" % i)
    text(s, "slot.foundation.part.%d" % i, [txt.Para((txt.Run(p, "ink-deep", size=10),), align="center")], th,
         size=10, background="paper", anchor="middle")

# the arrow from the foundation lands on the first wave header
rename(s, "dev.99", "struct.foundation.arrow")
move(s, "struct.foundation.arrow", 4.40, 1.77, 0.20, 0.46)
prims.set_fill(find(s, "struct.foundation.arrow"), "ink-muted", theme=th)
rename(s, "dev.97", "slot.foundation.note")
move(s, "slot.foundation.note", 4.70, 1.85, 7.00, 0.30)
text(s, "slot.foundation.note", [txt.Para((txt.Run("Built in wave 1,", "ink-deep", bold=True, size=10),
                                            txt.Run(" configured by every later wave", "ink", size=10)))], th, size=10, anchor="middle")

# four wave headers, each with its duration
WAVES = [("dev.41", "Wave 1 · Months 1-3"), ("dev.34", "Wave 2 · Months 3-5"),
         ("dev.46", "Wave 3 · Months 5-7"), ("dev.42", "Wave 4 · Months 7-9")]
for i, (n, w) in enumerate(WAVES, 1):
    rename(s, n, "slot.wave.%d.head" % i)
    text(s, "slot.wave.%d.head" % i, [txt.Para((txt.Run(w, "on-accent", bold=True, size=11),), align="center")],
         th, size=11, background="accent", anchor="middle")
rename(s, "dev.98", "slot.wave.note")
move(s, "slot.wave.note", 4.95, 2.80, 6.35, 0.28)
text(s, "slot.wave.note", [txt.Para((txt.Run("Three sites per wave:", "ink-deep", bold=True, size=10),
                                      txt.Run(" office, plant, warehouse", "ink", size=10)),
                                     align="center")], th, size=10, anchor="middle")
FAN = [(31, 32, 33), (35, 36, 37), (38, 39, 40), (43, 44, 45)]
for i, trio in enumerate(FAN, 1):
    for j, n in enumerate(trio, 1):
        rename(s, "dev.%d" % n, "struct.wave.%d.fan.%d" % (i, j))

# twelve site cards: glyph, users, go-live month
CARDS = sorted(range(48, 60), key=lambda n: find(s, "dev.%d" % n).left)
NUMS = sorted(range(73, 85), key=lambda n: find(s, "dev.%d" % n).left)
LABELS = sorted(range(85, 97), key=lambda n: find(s, "dev.%d" % n).left)
CHIPS = sorted(range(60, 72), key=lambda n: find(s, "dev.%d" % n).left)
GLYPHS = ["building", "factory", "warehouse"]
USERS = ["140", "320", "90", "110", "260", "75", "160", "410", "120", "95", "230", "60"]
MONTHS = ["Jan", "Feb", "Mar", "Mar", "Apr", "May", "May", "Jun", "Jul", "Jul", "Aug", "Sep"]
for k in range(12):
    i = k + 1
    cx = find(s, "dev.%d" % CARDS[k]).left / EMU
    rename(s, "dev.%d" % CARDS[k], "struct.site.%d" % i)
    icon(s, "slot.site.%d.icon" % i, GLYPHS[k % 3], cx + 0.19, 3.89, 0.31, th, role="ink-deep")
    rename(s, "dev.%d" % NUMS[k], "slot.site.%d.value" % i)
    tight("slot.site.%d.value" % i, 0.02, 0.0)
    move(s, "slot.site.%d.value" % i, cx + 0.03, 4.27, 0.63, 0.26)
    text(s, "slot.site.%d.value" % i, [txt.Para((txt.Run(USERS[k], "ink-deep", bold=True, size=12),),
                                                align="center")], th, size=12, background="card", anchor="middle")
    rename(s, "dev.%d" % LABELS[k], "slot.site.%d.label" % i)
    tight("slot.site.%d.label" % i, 0.02, 0.0)
    move(s, "slot.site.%d.label" % i, cx + 0.03, 4.53, 0.63, 0.22)
    text(s, "slot.site.%d.label" % i, [txt.Para((txt.Run("users", "ink-muted", size=9),), align="center")], th,
         size=9, background="card", anchor="middle")
    rename(s, "dev.%d" % CHIPS[k], "slot.site.%d.chip" % i)
    tight("slot.site.%d.chip" % i, 0.02, 0.0)
    prims.set_fill(find(s, "slot.site.%d.chip" % i), "ink-deep", theme=th)
    text(s, "slot.site.%d.chip" % i, [txt.Para((txt.Run(MONTHS[k], "paper", bold=True, size=9),),
                                               align="center")], th, size=9, background="ink-deep",
         anchor="middle")

# the four steps every wave repeats
rename(s, "dev.100", "struct.steps.frame")
move(s, "struct.steps.frame", 0.50, 5.20, 12.40, 1.50)
radius("struct.steps.frame")
rename(s, "dev.101", "slot.steps.label")
move(s, "slot.steps.label", 0.70, 5.27, 4.00, 0.28)
text(s, "slot.steps.label", [txt.Para((txt.Run("Every wave runs the same four steps", "ink-deep", bold=True, size=11),))],
     th, size=11, anchor="middle")
STEPS = [("dev.102", "dev.106", "Assess", "Map steps, audit master data"),
         ("dev.103", "dev.107", "Configure", "Set up roles, reports, interfaces"),
         ("dev.104", "dev.108", "Test", "Run tests and a cutover rehearsal"),
         ("dev.105", "dev.109", "Go live", "Switch over, then hypercare")]
for i, (hd, bd, h, b) in enumerate(STEPS, 1):
    rename(s, hd, "slot.step.%d.head" % i)
    prims.set_fill(find(s, "slot.step.%d.head" % i), "accent", theme=th)
    text(s, "slot.step.%d.head" % i, [txt.Para((txt.Run(h, "on-accent", bold=True, size=11),), align="center")],
         th, size=11, background="accent", anchor="middle")
    rename(s, bd, "slot.step.%d.body" % i)
    bx = find(s, "slot.step.%d.head" % i).left / EMU
    move(s, "slot.step.%d.body" % i, bx + 0.12, 6.13, 2.25, 0.46)
    text(s, "slot.step.%d.body" % i, [txt.Para((txt.Run(b, "ink", size=10),), align="center")], th, size=10)

# exit gate card
rename(s, "dev.110", "struct.gate")
move(s, "struct.gate", 10.72, 5.56, 2.04, 1.02)
gate = find(s, "struct.gate")
gate.text_frame.text = ""
txt.textbox(s, Box(10.84, 5.64, 1.40, 0.30), [txt.Para((txt.Run("Exit gate", "ink-deep", bold=True, size=11),))],
            "slot.gate.head", th, background="accent-wash", anchor="middle")
txt.textbox(s, Box(10.84, 6.00, 1.84, 0.50), [txt.Para((txt.Run("Next wave starts after four stable weeks",
                                                                 "ink", size=10),))],
            "slot.gate.body", th, background="accent-wash")
icon(s, "slot.gate.icon", "gauge", 12.32, 5.64, 0.33, th, role="accent")

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
out = save(prs, "DL06", th, archetype="phased-roadmap", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
