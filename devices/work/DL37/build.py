"""DL37: an engagement model read left to right. A ranked intake queue (two live requests in solid brand, four
queued in dashed outline) feeds one squad running two tracks, discovery and delivery, joined by a gated hand-off;
every release lands on a compounding stack of shared assets that widens toward its base (engagement-model)."""
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

prs, s, th = open_lifted("DL37")
VARIANT = "queue-gated-tracks-stack"
P, R = txt.Para, txt.Run

# chrome the house rules ban: the subtitle under the title, the dark summary band along the foot (P09), the
# section pill at the top right and the source line in the corner (no footer). No pictures were removed.
for n in ("dev.3", "dev.4", "dev.46", "dev.47"):
    delete(s, n)

# the subtitle and foot band freed about 1.1in of height: the device takes it with one vertical map, so every
# card, arrow and bar keeps its relation to the others. The chevron marks keep their size and move by centre.
SRC0, SRC1 = 1.26, 6.06                                          # the device's own vertical extent
DST0, DST1 = 0.92, 6.74
F = (DST1 - DST0) / (SRC1 - SRC0)
KEEP_SIZE = {"dev.31", "dev.32", "dev.33"}
for sh in list(s.shapes):
    if sh.name == "dev.2":
        continue
    y, h = sh.top / EMU, sh.height / EMU
    if sh.name in KEEP_SIZE:
        sh.top = int((DST0 + (y + h / 2 - SRC0) * F - h / 2) * EMU)
    else:
        sh.top = int((DST0 + (y - SRC0) * F) * EMU)
        sh.height = int(h * F * EMU)

# title: the kit's wide title geometry, 21pt, one line, two-tone
rename(s, "dev.2", "slot.title")
move(s, "slot.title", 0.50, 0.13, 12.40, 0.40)
bp = find(s, "slot.title")._element.find(".//" + qn("a:bodyPr"))
for k in ("lIns", "tIns", "rIns", "bIns"):
    bp.set(k, "0")
text(s, "slot.title", [P(tuple(txt.title_runs(
    "Requests enter one queue, pass a value gate and build a shared base",
    ("one queue",))))], th, size=21, bold=True, anchor="middle")

# --- the intake queue -------------------------------------------------------------------------------------------
def flat(name):
    bp = find(s, name)._element.find(".//" + qn("a:bodyPr"))
    for k in ("lIns", "tIns", "rIns", "bIns"):
        bp.set(k, "0")


rename(s, "dev.5", "slot.queue.label")
move(s, "slot.queue.label", 0.50, find(s, "slot.queue.label").top / EMU - 0.06, 2.60, 0.30)
flat("slot.queue.label")
text(s, "slot.queue.label", "Intake queue, by rank", th, size=13, bold=True, role="accent-ink",
     anchor="middle")
LIVE = [("dev.7", "In discovery", "Weekly forecast by region for the planning office"),
        ("dev.8", "In delivery", "Planner override log with reasons captured")]
for i, (n, head, body) in enumerate(LIVE, 1):
    rename(s, n, "slot.queue.live.%d" % i)
    text(s, "slot.queue.live.%d" % i, [P((R(head, "on-accent", bold=True, size=12),)),
                                       P((R(body, "on-accent", size=11),), space_before=2)],
         th, size=11, background="accent", anchor="middle")
QUEUED = ["Promotion uplift model", "Supplier lead-time feed", "Stock-out early warning", "New-region onboarding"]
for i, (n, line) in enumerate(zip(("dev.9", "dev.10", "dev.11", "dev.12"), QUEUED), 1):
    rename(s, n, "slot.queue.next.%d" % i)
    text(s, "slot.queue.next.%d" % i, [P((R(line, "ink-deep", bold=True, size=12),))], th, size=12,
         background="paper", anchor="middle")

rename(s, "dev.6", "struct.queue")

# the pull from queue to squad
rename(s, "dev.34", "struct.queue.rule.1")
rename(s, "dev.35", "struct.queue.rule.2")
for k, n in enumerate(("dev.31", "dev.32", "dev.33"), 1):
    rename(s, n, "struct.pull.chevron.%d" % k)
rename(s, "dev.13", "slot.pull.label")
move(s, "slot.pull.label", 2.98, find(s, "slot.pull.label").top / EMU, 0.74, 0.24)
text(s, "slot.pull.label", [P((R("Pull", "ink-muted", italic=True, size=11),), align="center")], th, size=11)

# --- one squad, two tracks, one gate -----------------------------------------------------------------------------
# laid out explicitly so the two tracks fill the column the queue and stack span; each step carries its time box
FX, FW, FH = 3.80, 5.42, 1.80                                   # track frames
F1Y, GAP = 1.20, 0.70
F2Y = F1Y + FH + GAP
SW, SH = 1.46, 0.92                                             # step boxes
SX = [FX + 0.16 + k * (SW + (FW - 0.32 - 3 * SW) / 2) for k in range(3)]
TRACKS = [("dev.14", "dev.36", "search", "Discovery track, two weeks",
           [("dev.38", "Frame the question", "Days 1 to 3"), ("dev.39", "Test on history", "Days 4 to 7"),
            ("dev.40", "Size the value", "Days 8 to 10")],
           ("dev.41", "dev.37")),
          ("dev.16", "dev.17", "rocket", "Delivery track, four weeks",
           [("dev.18", "Build and wire", "Weeks 1 and 2"), ("dev.19", "Run beside plan", "Week 3"),
            ("dev.20", "Hand to planners", "Week 4")],
           ("dev.42", "dev.43"))]
for t, (frame, head, g, label, steps, arrows) in enumerate(TRACKS, 1):
    fy = F1Y if t == 1 else F2Y
    rename(s, frame, "struct.track.%d" % t)
    move(s, "struct.track.%d" % t, FX, fy, FW, FH)
    rename(s, head, "slot.track.%d.head" % t)
    move(s, "slot.track.%d.head" % t, FX + 0.56, fy + 0.18, 4.40, 0.32)
    flat("slot.track.%d.head" % t)
    text(s, "slot.track.%d.head" % t, label, th, size=14, bold=True, role="ink-deep", anchor="middle")
    icon(s, "slot.track.%d.icon" % t, g, FX + 0.18, fy + 0.18, 0.30, th, role="accent")
    sy = fy + 0.66
    for k, (n, step, when) in enumerate(steps, 1):
        nm = "slot.track.%d.step.%d" % (t, k)
        rename(s, n, nm)
        move(s, nm, SX[k - 1], sy, SW, SH)
        text(s, nm, [P((R(step, "ink-deep", bold=True, size=12),), align="center"),
                     P((R(when, "accent-ink", size=11),), align="center", space_before=3)],
             th, size=12, background="card", anchor="middle")
    for k, n in enumerate(arrows, 1):
        nm = "struct.track.%d.arrow.%d" % (t, k)
        rename(s, n, nm)
        x0 = SX[k - 1] + SW
        move(s, nm, x0, sy + SH / 2, SX[k] - x0, 0)

rename(s, "dev.44", "struct.gate.arrow")                       # frame 1 foot to frame 2 head
move(s, "struct.gate.arrow", FX + FW / 2, F1Y + FH, 0, GAP)
rename(s, "dev.15", "slot.gate.label")
gy = F1Y + FH + GAP / 2 - 0.15
move(s, "slot.gate.label", FX + FW / 2 + 0.48, gy, 2.40, 0.30)
flat("slot.gate.label")
text(s, "slot.gate.label", [P((R("Value gate, go or stop", "accent-ink", bold=True, size=13),))], th, size=13,
     anchor="middle")
icon(s, "slot.gate.icon", "shield-check", FX + FW / 2 + 0.14, gy + 0.02, 0.26, th, role="accent")

rename(s, "dev.21", "slot.squad.note")
move(s, "slot.squad.note", FX + 0.30, F2Y + FH + 0.22, FW - 0.60, 0.60)
text(s, "slot.squad.note", [P((R("One squad runs both tracks", "ink-deep", bold=True, size=13),), align="center"),
                            P((R("Discovery on the next request while delivery ships", "ink", italic=True,
                                 size=12),), align="center", space_before=2)], th, size=12)

# --- the compounding stack ---------------------------------------------------------------------------------------
delete(s, "dev.29")                                              # a free-standing growth axis lands on nothing (P06)
rename(s, "dev.22", "slot.stack.label")
sy = find(s, "slot.stack.label").top / EMU
move(s, "slot.stack.label", 10.40, sy - 0.06, 2.40, 0.30)
flat("slot.stack.label")
text(s, "slot.stack.label", "Shared base grows", th, size=13, bold=True, role="accent-ink",
     anchor="middle")
icon(s, "slot.stack.icon", "layers", 10.06, sy - 0.03, 0.26, th, role="accent")
LAYERS = ["Faster starts", "Review screens", "Accuracy monitors", "Tested forecast models",
          "Shared feature store", "Clean order history"]
for i, (n, line) in enumerate(zip(("dev.23", "dev.24", "dev.25", "dev.26", "dev.27", "dev.28"), LAYERS), 1):
    rename(s, n, "slot.stack.layer.%d" % i)
    text(s, "slot.stack.layer.%d" % i, [P((R(line, "on-accent", bold=True, size=12),), align="center")], th,
         size=12, background="accent", anchor="middle")
# every release lands on the stack: the arrow runs from the delivery frame to the layer level with it
mid = lambda sh: (sh.top + sh.height / 2) / EMU                 # noqa: E731
hit = min((find(s, "slot.stack.layer.%d" % i) for i in range(1, 7)), key=lambda sh: abs(mid(sh) - F2Y - FH / 2))
ry = mid(hit)
rename(s, "dev.45", "struct.release.arrow")
move(s, "struct.release.arrow", FX + FW, ry, hit.left / EMU - FX - FW, 0)
rename(s, "dev.30", "slot.stack.note")
text(s, "slot.stack.note", [P((R("Each release adds a layer", "ink-deep", bold=True, size=12),), align="center"),
                            P((R("The next request starts higher up the stack", "ink", italic=True, size=11),),
                              align="center", space_before=2)], th, size=11)

def radius(sh, r=0.05, sx=1.0, sy=1.0):                         # the canvas card radius on every rounded box
    av = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst"))
    for old in list(av):
        av.remove(old)
    gd = av.makeelement(qn("a:gd"), {"name": "adj"})
    av.append(gd)
    gd.set("fmla", "val %d" % round(r / (min(sh.width * sx, sh.height * sy) / EMU) * 100000))


from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
for sh in list(s.shapes):
    kids, sx, sy = [sh], 1.0, 1.0
    if sh.shape_type == 6:                                       # a group: children scale by ext over chExt
        ch = sh._element.find(qn("p:grpSpPr") + "/" + qn("a:xfrm") + "/" + qn("a:chExt"))
        sx, sy = sh.width / int(ch.get("cx")), sh.height / int(ch.get("cy"))
        kids = list(sh.shapes)
    for k in kids:
        g = k._element.find(qn("p:spPr") + "/" + qn("a:prstGeom"))
        if g is not None and g.get("prst") == "roundRect":
            radius(k, sx=sx, sy=sy)
out = save(prs, "DL37", th, archetype="engagement-model", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
