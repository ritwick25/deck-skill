"""DL16: three principle columns, each heading over its own mini diagram as proof, two reason cards beneath."""
import argparse
import json
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

HERE = Path(__file__).resolve().parent
prs, s, th = open_lifted("DL16")
VARIANT = "principle-columns-proof-diagrams"
LIFT = json.loads((HERE / "lift.json").read_text())


def P(t, role="ink", bold=False, size=10, align="left", before=0):
    return txt.Para((txt.Run(t, role, bold=bold, size=size),), align=align, space_before=before)


def tight(name, v=0.0, side=0.0):
    bp = find(s, name)._element.find(".//" + qn("a:bodyPr"))
    for k, val in (("tIns", v), ("bIns", v), ("lIns", side), ("rIns", side)):
        bp.set(k, str(int(val * EMU)))


def radius(name, r=0.05):
    sh = find(s, name)
    av = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst"))
    for gd in list(av):
        av.remove(gd)
    etree.SubElement(av, qn("a:gd"), name="adj", fmla="val %d" % round(r / (min(sh.width, sh.height) / EMU) * 100000))


def put(old, new, paras, size, bg="paper", anchor="top", box=None):
    rename(s, old, new)
    if box:
        move(s, new, *box)
    text(s, new, paras, th, size=size, background=bg, anchor=anchor)


# title: one claim, two-tone
put("dev.4", "slot.title", [txt.Para(tuple(txt.title_runs(
    "Three principles keep the platform fast to change and cheap to run",
    ("fast to change", "cheap to run"))))], 21, anchor="middle")

# principle headings and their rules
HEADS = ["Separate storage from compute", "Ship in small, usable releases", "Automate the path to production"]
for i, (n, h) in enumerate(zip(("dev.11", "dev.12", "dev.13"), HEADS), 1):
    put(n, "slot.principle.%d.head" % i, [P(h, "accent-ink", True, 14)], 14, anchor="bottom")
for i, n in enumerate(("dev.5", "dev.6", "dev.7"), 1):
    rename(s, n, "struct.principle.%d.rule" % i)
rename(s, "dev.8", "struct.dividers")
rename(s, "dev.9", "struct.divider.1")
rename(s, "dev.10", "struct.divider.2")

# reason cards: head and a two-line reason
CARDS = [("dev.14", "Scale each layer on its own", "Query load grows with no table copied, and storage cost stays flat."),
         ("dev.15", "Working views before scale", "Each release puts a usable view in front of the team that asked for it."),
         ("dev.16", "No manual release steps", "Every change passes the same test suite before it reaches any user."),
         ("dev.17", "One copy of every table", "All engines read the same files, so every report shows the same number."),
         ("dev.18", "Feedback sets the next step", "Users rank the backlog after each release, and the top item ships next."),
         ("dev.19", "Rollback in minutes", "A failed check returns the last good version without a change ticket.")]
ORDER = [1, 3, 5, 2, 4, 6]       # top row then bottom row, left to right: slot numbers per column then row
for (n, head, body), k in zip(CARDS, ORDER):
    put(n, "slot.card.%d" % k, [P(head, "ink-deep", True, 13), P(body, "ink", False, 12, before=2)], 13,
        bg="accent-wash")

# column 1 proof: a shared layer over two engines on one storage layer, policy beside
rename(s, "dev.22", "struct.proof.1")
put("dev.23", "slot.proof.1.top", [P("Shared semantic layer", "ink", False, 10, "center")], 10, "accent-wash", "middle")
put("dev.24", "slot.proof.1.base", [P("Open table storage", "ink", True, 10, "center")], 10, "accent-wash", "middle")
rename(s, "dev.25", "struct.proof.1.engines")
put("dev.26", "slot.proof.1.engine.1", [P("Query"), P("engine")], 10, "accent-wash", "middle")
put("dev.27", "slot.proof.1.engine.2", [P("Pipeline"), P("jobs")], 10, "accent-wash", "middle")
put("dev.28", "slot.proof.1.policy", [P("Access policy", align="center")], 10, anchor="top",
    box=(3.42, 3.15, 0.90, 0.38))
rename(s, "dev.20", "struct.proof.1.link.1")
rename(s, "dev.21", "struct.proof.1.link.2")
rename(s, "dev.29", "struct.proof.1.policy.link")

# column 2 proof: requester, brief and platform in a loop, adoption rising in steps
rename(s, "dev.36", "struct.proof.2.loop")
put("dev.40", "slot.proof.2.actor.1", [P("Analyst", align="center")], 10, box=(4.88, 2.32, 0.72, 0.20))
put("dev.37", "slot.proof.2.actor.2", [P("Use case brief", align="center")], 10, box=(5.62, 2.32, 0.92, 0.36))
rename(s, "dev.38", "slot.proof.2.link")
tight("slot.proof.2.link")
put("slot.proof.2.link", "slot.proof.2.link", [P("Weekly feedback", align="center")], 10, box=(6.29, 1.76, 1.30, 0.22))
put("dev.39", "slot.proof.2.actor.3", [P("Platform", align="center")], 10, box=(7.45, 2.32, 0.80, 0.20))
rename(s, "dev.41", "struct.proof.2.arrow")
move(s, "struct.proof.2.arrow", 6.21, 2.08, 1.45, 0)          # lands on the brief and the platform glyphs
rename(s, "dev.31", "struct.proof.2.steps")
put("dev.32", "slot.proof.2.step.1", [P("Pilot", align="center")], 11, anchor="middle")
put("dev.33", "slot.proof.2.step.2", [P("Second team", align="center")], 11, anchor="middle")
put("dev.34", "slot.proof.2.step.3", [P("All regions", align="center")], 11, "accent-wash", "middle")
rename(s, "dev.35", "struct.proof.2.axis")
put("dev.30", "slot.proof.2.caption", [P("Adoption grows with each release", align="center", size=12)], 12,
    box=(4.95, 3.95, 3.13, 0.22))

# column 3 proof: a four-stage pipeline with a rollback loop, fanning out to every environment
rename(s, "dev.42", "struct.proof.3.pipeline")
for k, n in enumerate((43, 44, 45, 46), 1):
    rename(s, "dev.%d" % n, "struct.proof.3.stage.%d" % k)
STAGES = [("dev.47", "Ingest", 9.17), ("dev.48", "Test", 9.70), ("dev.49", "Build", 10.23), ("dev.50", "Release", 10.79)]
for k, (n, lab, cx) in enumerate(STAGES, 1):
    put(n, "slot.proof.3.stage.%d" % k, [P(lab, align="center", size=8)], 8, "card", box=(cx - 0.26, 2.88, 0.52, 0.14))
put("dev.60", "slot.proof.3.loop", [P("Rollback", align="center", size=8)], 8, "card")
put("dev.66", "slot.proof.3.reach", [P("One run reaches every environment", align="center")], 10,
    box=(10.62, 1.68, 1.92, 0.34))
for k, n in enumerate(range(51, 59), 1):
    rename(s, "dev.%d" % n, "struct.proof.3.env.%d" % k)
rename(s, "dev.59", "struct.proof.3.loop.line")
for k, n in enumerate((61, 62, 63), 1):
    rename(s, "dev.%d" % n, "struct.proof.3.link.%d" % k)
rename(s, "dev.64", "struct.proof.3.fan.1")
rename(s, "dev.65", "struct.proof.3.fan.2")
rename(s, "dev.3", "struct.proof.3.row.1")
rename(s, "dev.2", "struct.proof.3.row.2")
rename(s, "dev.67", "struct.proof.3.brace")

# house finish: no theme style references, card radius at the canvas value
for st in list(s._element.iter(qn("p:style"))):
    st.getparent().remove(st)
for n in ("slot.proof.1.top", "slot.proof.1.base", "slot.proof.1.engine.1", "slot.proof.1.engine.2",
          "struct.proof.3.pipeline"):
    radius(n)

# glyphs at every removed icon box, keyed by position
GLYPHS = {(2.826, 3.734): ("slot.proof.1.base.icon", "database"),
          (1.338, 2.906): ("slot.proof.1.engine.1.icon", "cpu"),
          (2.784, 2.902): ("slot.proof.1.engine.2.icon", "cog"),
          (3.716, 2.798): ("slot.proof.1.policy.icon", "lock"),
          (5.063, 1.899): ("slot.proof.2.actor.1.icon", "user"),
          (5.887, 1.899): ("slot.proof.2.actor.2.icon", "clipboard-list"),
          (7.679, 1.913): ("slot.proof.2.actor.3.icon", "network"),
          (9.087, 2.61): ("slot.proof.3.stage.1.icon", "database-zap"),
          (9.62, 2.609): ("slot.proof.3.stage.2.icon", "flask-conical"),
          (10.154, 2.609): ("slot.proof.3.stage.3.icon", "cog"),
          (10.712, 2.609): ("slot.proof.3.stage.4.icon", "package-check")}
for p in LIFT["pictures_removed"]:
    x, y, w, h = p["box_in"]
    nm, g = GLYPHS[(round(x, 3), round(y, 3))]
    side = max(w, h)
    icon(s, nm, g, x + (w - side) / 2, y + (h - side) / 2, side, th, role="accent")

# every bent link on the route PowerPoint draws (LibreOffice re-routes them); on that route the rollback loop
# runs under its label, so the label knocks the line out in the zone's own fill
from assemble_devices import bake_bent  # noqa: E402
bake_bent(s)
from deckkit import prims  # noqa: E402
prims.set_fill(find(s, "slot.proof.3.loop"), "card", theme=th)
_el = find(s, "slot.proof.3.loop")._element
_el.getparent().remove(_el)
s.shapes._spTree.append(_el)

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
out = save(prs, "DL16", th, archetype="principles", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
