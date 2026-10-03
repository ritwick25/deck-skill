"""DL41: the brief answered on one slide. Left, the client's ask as a rail of six glyph rows under a solid header;
right, the response in three near-black headed columns (who delivers, what is offered, why it holds), each a lead
claim, one figure and two proof tiles; beneath them a five-stage maturity chevron row with the commercial terms
each stage carries (executive-summary)."""
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

prs, s, th = open_lifted("DL41")
VARIANT = "ask-rail-response"
P, R = txt.Para, txt.Run

# The source's composition stays: the ask as a left rail, the response as three headed columns, a maturity strip
# beneath. Its two logo boxes go (a client logo becomes nothing), its gradients and pastel tiles go (ruling 12),
# the top colour strips on the maturity tiles become a chevron row, the link under the middle column goes. Every
# shape is redrawn flat in the kit so it sits inside the content band and clears the floor with room.
for sh in list(s.shapes):
    if sh.name != "dev.66":
        sh._element.getparent().remove(sh._element)

rename(s, "dev.66", "slot.title")
move(s, "slot.title", 0.50, 0.13, 12.40, 0.40)                   # the kit's wide title geometry, 21pt, one line
bp = find(s, "slot.title")._element.find(".//" + qn("a:bodyPr"))
for k in ("lIns", "tIns", "rIns", "bIns"):
    bp.set(k, "0")
text(s, "slot.title", [P(tuple(txt.title_runs(
    "Every ask in the brief meets a named answer, from concept to full rollout", ("Every ask",))))],
    th, size=21, bold=True, anchor="middle")


def tb(box, paras, name, bg, anchor="top"):
    txt.textbox(s, box, paras, name, th, anchor=anchor, background=bg)


X0, X1, Y0, Y1 = 0.50, 12.90, 0.85, 6.84
LW, GAP = 3.85, 0.25
RX = X0 + LW + GAP
RW = X1 - RX
HEAD_H = 0.40
TOP = Y0 + HEAD_H + 0.12

for nm, (hx, hw, lab) in (("brief", (X0, LW, "What the brief asks")),
                          ("response", (RX, RW, "How the response answers it"))):
    prims.block(s, Box(hx, Y0, hw, HEAD_H), fill="accent", radius_in=0.05, name="struct.%s.head" % nm, theme=th)
    tb(Box(hx + 0.18, Y0 + 0.04, hw - 0.36, HEAD_H - 0.08), [P((R(lab, "on-accent", bold=True, size=14),))],
       "slot.%s.head" % nm, "accent", anchor="middle")

# --- left: the ask, six glyph rows on one card-tone rail ------------------------------------------------------------
ASKS = [("target", "Objective", "Agents that take routine analysis work off the planning teams"),
        ("crosshair", "Scope", "Planning, pricing, marketing and finance across four regions"),
        ("puzzle", "Capabilities", "Research, analysis, reporting and test automation, each as an agent"),
        ("chart-column-increasing", "Maturity range", "From early concepts to agents running in daily work"),
        ("handshake", "Delivery models", "A hosted service, an API, or tools inside current systems"),
        ("shield-check", "Governance", "Audit trails and human sign-off in a regulated setting")]
RAIL = Box(X0, TOP, LW, Y1 - TOP)
prims.card(s, RAIL, fill="card", line="hairline", radius_in=0.05, name="struct.brief.panel", theme=th)
RP = RAIL.h / len(ASKS)
for i, (g, lab, body) in enumerate(ASKS, 1):
    ry = TOP + (i - 1) * RP
    icon(s, "slot.brief.%d.icon" % i, g, X0 + 0.18, ry + 0.16, 0.30, th, role="accent")
    tb(Box(X0 + 0.62, ry + 0.14, LW - 0.80, 0.30), [P((R(lab, "ink-deep", bold=True, size=13),))],
       "slot.brief.%d.label" % i, "card", anchor="middle")
    tb(Box(X0 + 0.62, ry + 0.45, LW - 0.80, RP - 0.52), [P((R(body, "ink", size=11),), line_spacing=0.95)],
       "slot.brief.%d.body" % i, "card")
    if i < len(ASKS):
        prims.hairline(s, (X0 + 0.18, ry + RP), (X0 + LW - 0.18, ry + RP), role="hairline",
                       name="struct.brief.rule.%d" % i, theme=th)

# --- right: three response columns ----------------------------------------------------------------------------------
CG = 0.16
CW = (RW - 2 * CG) / 3
COLS = [
    ("Who delivers", "A data and AI engineering firm with delivery at enterprise scale",
     ("1,200+", "engineers in data and AI delivery"),
     ("Teams spanning data, engineering and domain consulting",
      "Reusable assets carried from one value chain to the next")),
    ("What is offered", "A modular set of agents built to run in production",
     ("20+", "agents covering the full planning cycle"),
     ("Orchestration that lets several agents share one task",
      "One framework, reused and adapted for each team")),
    ("Why it holds", "A partner already fluent in the data and ways of working",
     ("60+", "people trained on the same data and processes"),
     ("A record of scaling agents across business units",
      "Domain consulting that turns each agent into daily use")),
]
NUMBERS = {}
HD_Y, HD_H = TOP, 0.36
LEAD_Y, LEAD_H = HD_Y + HD_H + 0.10, 0.58
STAT_Y, STAT_H = LEAD_Y + LEAD_H + 0.08, 1.04
TILE_H, TG = 0.64, 0.10
for c, (head, lead, (val, slab), tiles) in enumerate(COLS, 1):
    cx = RX + (c - 1) * (CW + CG)
    solid = c == 2                                               # the offer column carries the brand fill
    fill = "accent" if solid else "card"
    ink = "on-accent" if solid else "ink"
    prims.block(s, Box(cx, HD_Y, CW, HD_H), fill="ink-deep", radius_in=0.05, name="struct.col.%d.head" % c, theme=th)
    tb(Box(cx + 0.10, HD_Y + 0.03, CW - 0.20, HD_H - 0.06), [P((R(head, "paper", bold=True, size=13),),
                                                             align="center")],
       "slot.col.%d.head" % c, "ink-deep", anchor="middle")
    tb(Box(cx + 0.04, LEAD_Y, CW - 0.08, LEAD_H), [P((R(lead, "accent-ink", bold=True, size=12),),
                                                     line_spacing=0.95)],
       "slot.col.%d.lead" % c, "paper")
    sb = Box(cx, STAT_Y, CW, STAT_H)
    if solid:
        prims.block(s, sb, fill="accent", radius_in=0.05, name="struct.col.%d.tile.1" % c, theme=th)
    else:
        prims.card(s, sb, fill="card", line="hairline", radius_in=0.05, name="struct.col.%d.tile.1" % c, theme=th)
    NUMBERS["slot.col.%d.stat" % c] = {"value": val, "kind": "illustrative"}
    prims.stat(s, Box(cx + 0.16, STAT_Y + 0.07, CW - 0.32, STAT_H - 0.14), val, slab, kind="illustrative",
               role="on-accent" if solid else "accent-ink", label_role=ink, background=fill, pt=24, label_pt=11,
               basis=False, name="slot.col.%d.stat" % c, theme=th)
    for k, body in enumerate(tiles, 2):
        ty = STAT_Y + STAT_H + TG + (k - 2) * (TILE_H + TG)
        tbx = Box(cx, ty, CW, TILE_H)
        if solid:
            prims.block(s, tbx, fill="accent", radius_in=0.05, name="struct.col.%d.tile.%d" % (c, k), theme=th)
        else:
            prims.card(s, tbx, fill="card", line="hairline", radius_in=0.05,
                       name="struct.col.%d.tile.%d" % (c, k), theme=th)
        tb(Box(cx + 0.16, ty + 0.05, CW - 0.32, TILE_H - 0.10), [P((R(body, ink, size=11),), line_spacing=0.95)],
           "slot.col.%d.tile.%d" % (c, k), fill, anchor="middle")
COL_END = STAT_Y + STAT_H + TG + 2 * TILE_H + TG
tb(Box(X1 - 2.40, COL_END + 0.04, 2.40, 0.20), [P((R("Illustrative figures", "ink-muted", size=9),), align="right")],
   "slot.basis", "paper", anchor="middle")

# --- beneath: five maturity stages and the terms each carries -------------------------------------------------------
STAGES = [("Full release", "Enterprise scale"), ("Limited release", "Controlled rollout"),
          ("Pilot", "Real workflow tests"), ("Early build", "Concept validated"),
          ("Concept", "Scope and roadmap")]
SH_Y, SH_H = COL_END + 0.30, 0.40
prims.step_header(s, Box(RX, SH_Y, RW, SH_H), [n for n, _ in STAGES], fill="ink-strong", pt=11,
                  name="slot.stages", theme=th)
n = len(STAGES)
d = 0.33 * SH_H
sw = (RW + (n - 1) * (d - 0.04)) / n
pitch = sw - d + 0.04
SUB_Y = SH_Y + SH_H + 0.04
for i, (_, sub) in enumerate(STAGES, 1):
    sx = RX + (i - 1) * pitch
    tb(Box(sx, SUB_Y, sw - d, 0.22), [P((R(sub, "ink-muted", size=10),), align="center")],
       "slot.stage.%d.sub" % i, "paper", anchor="middle")
TERMS = [((1, 1), "Configured on day one, with fixed commercial levers"),
         ((2, 2), "Limited tailoring, with differentiated levers"),
         ((3, 5), "A roadmap shaped to the client's needs, with upfront investment")]
TY = SUB_Y + 0.22 + 0.08
TH = Y1 - TY
for k, ((a_, b_), body) in enumerate(TERMS, 1):
    x0 = RX + (a_ - 1) * pitch + (0.05 if a_ > 1 else 0)
    x1 = X1 if b_ == n else RX + (b_ - 1) * pitch + sw - d - 0.05
    bx = Box(x0, TY, x1 - x0, TH)
    prims.card(s, bx, fill="card", line="hairline", radius_in=0.05, name="struct.term.%d" % k, theme=th)
    tb(Box(bx.x + 0.12, bx.y + 0.06, bx.w - 0.24, bx.h - 0.12), [P((R(body, "ink", size=10),), align="center",
                                                                     line_spacing=0.95)],
       "slot.term.%d" % k, "card", anchor="middle")

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
from deckkit import package, tag  # noqa: E402
tag.tag(prs.slides[0], "executive-summary", VARIANT)
for sh in prs.slides[0].shapes:
    ooxml.finish(sh)
out = WORK / "DL41" / "device.pptx"
package.save(prs, out, title="Device DL41", theme=th, manifest={"numbers": NUMBERS}, overwrite=True,
             date="2026-10-03")
if a.out:
    shutil.copyfile(out, a.out)
