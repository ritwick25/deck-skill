"""DL10: one record traced across four numbered stage columns (fields in, lines matched in a table with the
exception row marked, the exception checked against five context sources around a hub, outcomes logged), over a
two-sided strip that sets the manual path against the traced one (worked-example)."""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import prims  # noqa: E402
from deckkit import text as txt  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL10")
VARIANT = "stage-columns-hub-trace"

# chrome the house rules ban: the tag chip beside the title, and the duplicate exception disc under its twin
for n in ("dev.82", "dev.45"):
    delete(s, n)


def P(t, role="ink", size=10, bold=False, before=0, align="center"):
    return txt.Para((txt.Run(t, role, bold=bold, size=size),), align=align, space_before=before)


def radius(name, r=0.05):
    sh = find(s, name)
    gd = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst") + "/" + qn("a:gd"))
    gd.set("fmla", "val %d" % round(r / (min(sh.width, sh.height) / EMU) * 100000))


def frame(name, role, line=None, weight=0.75):
    prims.set_fill(find(s, name), role, theme=th)
    if line is not None:
        prims.set_line(find(s, name), line, weight, theme=th)


# title: one claim, two-tone
rename(s, "dev.12", "slot.title")
move(s, "slot.title", 0.50, 0.18, 12.40, 0.52)
text(s, "slot.title", [txt.Para(tuple(txt.title_runs(
    "One invoice cleared in four minutes, with one price gap held for a buyer",
    ("four minutes", "held for a buyer"))))], th, size=22, bold=True, anchor="middle")

# stage numerals and the double chevrons between them
for i, n in enumerate(("dev.69", "dev.70", "dev.71", "dev.72"), 1):
    rename(s, n, "slot.stage.%d.num" % i)
    text(s, "slot.stage.%d.num" % i, [P("%02d" % i, "accent-ink", 18, True)], th, size=18, anchor="middle")
for k, n in enumerate(range(73, 82)):
    nm = "struct.chevron.%d.%d" % (k // 3 + 1, k % 3 + 1)
    rename(s, "dev.%d" % n, nm)
    for st in list(find(s, nm)._element.iter(qn("p:style"))):
        st.getparent().remove(st)

# stage headers and frames
HEADS = [("dev.14", "dev.13", "Invoice in", "INV-20418"),
         ("dev.20", "dev.10", "Lines matched", "Order, receipt and price"),
         ("dev.22", "dev.9", "Gap checked", "Five sources around one case"),
         ("dev.23", "dev.11", "Outcome logged", "Every step traceable")]
for i, (hd, fr, h, sub) in enumerate(HEADS, 1):
    rename(s, hd, "slot.stage.%d.head" % i)
    rename(s, fr, "struct.stage.%d.frame" % i)
    frame("slot.stage.%d.head" % i, "accent", "accent")
    frame("struct.stage.%d.frame" % i, "paper", "hairline")
    hb = find(s, "slot.stage.%d.head" % i)
    move(s, "struct.stage.%d.frame" % i, hb.left / EMU, hb.top / EMU, hb.width / EMU, 5.46 - hb.top / EMU)
    radius("struct.stage.%d.frame" % i)
    text(s, "slot.stage.%d.head" % i, [P(h, "on-accent", 13, True), P(sub, "on-accent", 10)], th, size=10,
         background="accent", anchor="middle")

# stage 1: the record's fields, the last one flagged
FIELDS = [("Received", "Mon, 09:12"), ("Supplier", "Packaging vendor"), ("Order", "PO-7731, net 30"),
          ("Total billed", "$48,260"), ("Line 4 price", "$6.40 a unit")]
for i, (n, (h, v)) in enumerate(zip(("dev.15", "dev.16", "dev.17", "dev.18", "dev.19"), FIELDS), 1):
    nm = "slot.field.%d" % i
    rename(s, n, nm)
    move(s, nm, 0.61, 1.88 + (i - 1) * 0.70, 1.51, 0.62)
    flag = i == len(FIELDS)
    frame(nm, "accent-wash" if flag else "card", "accent" if flag else "hairline")
    text(s, nm, [P(h, "ink-deep", 10, True), P(v, "ink", 10, before=1)], th, size=10,
         background="accent-wash" if flag else "card", anchor="middle")
icon(s, "slot.field.5.icon", "triangle-alert", 1.90, 4.73, 0.18, th, role="accent")

# stage 2: five checks with glyphs, the line table, the exception note
CHECKS = [("Supplier", "building", 2.67), ("Order", "file-text", 3.514), ("Receipt", "package-check", 4.359),
          ("Price", "tag", 5.204), ("Tax", "receipt", 6.077)]
for i, (n, (lab, g, gx)) in enumerate(zip(("dev.33", "dev.34", "dev.35", "dev.36", "dev.37"), CHECKS), 1):
    rename(s, n, "slot.check.%d.label" % i)
    text(s, "slot.check.%d.label" % i, [P(lab, "ink", 10)], th, size=10, anchor="middle")
    icon(s, "slot.check.%d.icon" % i, g, gx, 1.888, 0.24, th, role="accent")
for k, n in enumerate(("dev.38", "dev.39", "dev.40", "dev.41"), 1):
    rename(s, n, "struct.check.rule.%d" % k)

rename(s, "dev.21", "slot.lines.table")
tbl = find(s, "slot.lines.table").table
for c, w in zip(tbl.columns, (0.72, 0.64, 1.34, 0.63, 0.78)):
    c.width = int(w * EMU)
ROWS = [("Line", "Qty", "Item", "Gap", "Status"),
        ("Line 1", "1,200", "Shipping cartons", "0%", "Matched"),
        ("Line 2", "800", "Divider inserts", "0%", "Matched"),
        ("Line 3", "2,000", "Pallet wrap", "0%", "Matched"),
        ("Line 4", "3,100", "Printed sleeves", "+8.5%", "Held")]


def cell_fill(cell, role):
    pr = cell._tc.get_or_add_tcPr()
    for f in pr.findall(qn("a:solidFill")):
        pr.remove(f)
    sf = pr.makeelement(qn("a:solidFill"), {})
    sf.append(th.spec(role))
    pr.append(sf)


for r, row in enumerate(ROWS):
    for c, v in enumerate(row):
        cell = tbl.cell(r, c)
        bg = "card" if r == 0 else ("accent-wash" if r == 4 else "paper")
        cell_fill(cell, bg)
        role = "ink-deep" if r in (0, 4) else "ink"
        bold = r == 0 or (r == 4 and c in (0, 3, 4))
        txt.write(cell.text_frame, [P(v, role, 10, bold, align="left")], th, size=10, anchor="middle",
                  background=bg)

rename(s, "dev.42", "struct.note.frame")
frame("struct.note.frame", "accent-wash", "hairline")
rename(s, "dev.43", "slot.note")
text(s, "slot.note", [P("Line 4 breaks the 5% price tolerance, so it is held", "ink-deep", 10, True,
                        align="left")], th, size=10, background="accent-wash", anchor="middle")
for n, nm in (("dev.44", "struct.flag.1.disc"), ("dev.46", "struct.flag.1.star"),
              ("dev.47", "struct.flag.2.disc"), ("dev.48", "struct.flag.2.star")):
    rename(s, n, nm)

# stage 3: the exception checked against five sources around one hub
rename(s, "dev.50", "struct.hub.ring")
# the ring is drawn as one open stroke, a line around the hub rather than a box the discs sit in
ring = find(s, "struct.hub.ring")._element
sp = ring.find(qn("p:spPr"))
pg = sp.find(qn("a:prstGeom"))
W_, H_ = ring.find(".//" + qn("a:ext")).get("cx"), ring.find(".//" + qn("a:ext")).get("cy")
w_, h_ = int(W_), int(H_)
k_ = 0.5523
cx_, cy_, rx_, ry_ = w_ / 2, h_ / 2, w_ / 2, h_ / 2
pts = [(cx_, 0),
       ((cx_ + k_ * rx_, 0), (w_, cy_ - k_ * ry_), (w_, cy_)),
       ((w_, cy_ + k_ * ry_), (cx_ + k_ * rx_, h_), (cx_, h_)),
       ((cx_ - k_ * rx_, h_), (0, cy_ + k_ * ry_), (0, cy_)),
       ((0, cy_ - k_ * ry_), (cx_ - k_ * rx_, 0), (cx_ + 1, 0))]
cg = sp.makeelement(qn("a:custGeom"), {})
for t in ("avLst", "gdLst", "ahLst", "cxnLst"):
    cg.append(cg.makeelement(qn("a:" + t), {}))
rc = cg.makeelement(qn("a:rect"), {"l": "0", "t": "0", "r": "r", "b": "b"})
cg.append(rc)
pl = cg.makeelement(qn("a:pathLst"), {})
path = pl.makeelement(qn("a:path"), {"w": str(w_), "h": str(h_), "fill": "none"})
mv = path.makeelement(qn("a:moveTo"), {})
mv.append(mv.makeelement(qn("a:pt"), {"x": str(int(pts[0][0])), "y": "0"}))
path.append(mv)
for seg in pts[1:]:
    cb = path.makeelement(qn("a:cubicBezTo"), {})
    for (x_, y_) in seg:
        cb.append(cb.makeelement(qn("a:pt"), {"x": str(int(round(x_))), "y": str(int(round(y_)))}))
    path.append(cb)
pl.append(path)
cg.append(pl)
pg.addprevious(cg)
sp.remove(pg)
prims.set_fill(find(s, "struct.hub.ring"), None, theme=th)
rename(s, "dev.51", "struct.hub.core")
icon(s, "slot.hub.icon", "bot", 8.348, 3.45, 0.45, th, role="on-accent")
for k, n in enumerate(range(4, 9), 1):
    rename(s, "dev.%d" % n, "struct.hub.spoke.%d" % k)
    prims.set_line(find(s, "struct.hub.spoke.%d" % k), "rule-strong", 0.75, theme=th, dash="dash")
    find(s, "struct.hub.ring")._element.addprevious(find(s, "struct.hub.spoke.%d" % k)._element)   # above the frame
SOURCES = [  # satellite, label shape, label box, glyph, glyph box, head, value
    ("dev.52", "dev.60", (7.80, 1.88, 1.58, 0.50), "file-text", (8.476, 2.607), "Contract terms", "$5.90 a unit to June"),
    ("dev.56", "dev.57", (6.88, 2.42, 0.98, 0.70), "rotate-ccw-clock", (7.623, 3.401), "Order history",
     "Six at $5.90"),
    ("dev.53", "dev.49", (9.46, 2.50, 0.92, 0.70), "message-square", (9.339, 3.362), "Supplier note",
     "Resin surcharge"),
    ("dev.55", "dev.58", (7.04, 4.72, 1.42, 0.58), "chart-line", (7.87, 4.301), "Price index",
     "Resin up 9%"),
    ("dev.54", "dev.59", (8.74, 4.72, 1.42, 0.58), "user-check", (9.054, 4.294), "Buyer queue",
     "Routed with evidence")]
for i, (sat, lab, (x, y, w, h), g, (gx, gy), hd, v) in enumerate(SOURCES, 1):
    rename(s, sat, "struct.source.%d.disc" % i)
    icon(s, "slot.source.%d.icon" % i, g, gx, gy, 0.222, th, role="accent")
    rename(s, lab, "slot.source.%d" % i)
    move(s, "slot.source.%d" % i, x, y, w, h)
    text(s, "slot.source.%d" % i, [P(hd, "ink-deep", 10, True), P(v, "ink", 10, before=1)], th, size=10)

# stage 4: five outcomes, one glyph each, ruled apart
OUTS = [("dev.24", "circle-check", "Lines 1 to 3 posted", "$28,420 paid on day 30"),
        ("dev.25", "shield-alert", "Line 4 held", "$1,550 gap with the buyer"),
        ("dev.26", "user-check", "Buyer decision", "Surcharge approved to June"),
        ("dev.27", "sliders-horizontal", "Rule tuned", "Surcharges flagged on arrival"),
        ("dev.28", "clipboard-check", "Audit trail", "Eleven checks, each sourced")]
for i, (n, g, hd, v) in enumerate(OUTS, 1):
    y = 1.90 + (i - 1) * 0.71
    rename(s, n, "slot.outcome.%d" % i)
    move(s, "slot.outcome.%d" % i, 10.97, y, 1.85, 0.60)
    text(s, "slot.outcome.%d" % i, [P(hd, "ink-deep", 10, True, align="left"),
                                    P(v, "ink", 10, before=1, align="left")], th, size=10, anchor="middle")
    icon(s, "slot.outcome.%d.icon" % i, g, 10.630, y + 0.17, 0.26, th, role="accent")
for k, n in enumerate(("dev.29", "dev.30", "dev.31", "dev.32"), 1):
    rename(s, n, "struct.outcome.rule.%d" % k)
    move(s, "struct.outcome.rule.%d" % k, 10.73, 1.90 + k * 0.71 - 0.055, 2.02, 0)

# the strip: the manual path against the traced one, on a light card
rename(s, "dev.2", "struct.paths.frame")
frame("struct.paths.frame", "card", "hairline")
radius("struct.paths.frame")
rename(s, "dev.3", "struct.paths.divider")
prims.set_line(find(s, "struct.paths.divider"), "rule-strong", 0.75, theme=th, dash="dash")
rename(s, "dev.61", "slot.paths.head")
frame("slot.paths.head", "accent")
text(s, "slot.paths.head", [P("Same invoice, two paths", "on-accent", 10, True)], th, size=10,
     background="accent", anchor="middle")
rename(s, "dev.62", "slot.paths.versus")
text(s, "slot.paths.versus", [P("vs", "on-accent", 11, True)], th, size=11, background="accent", anchor="middle")
for nm, sh, g in (("struct.paths.before.disc", "dev.63", "user"), ("struct.paths.after.disc", "dev.66", "bot")):
    rename(s, sh, nm)
    frame(nm, "paper", "hairline")
    sp = find(s, nm)
    side = sp.width / EMU
    sp.text_frame.text = ""
    icon(s, nm.replace("struct", "slot").replace(".disc", ".icon"), g, sp.left / EMU + side * 0.22,
         sp.top / EMU + side * 0.22, side * 0.56, th, role="accent")

SIDES = [("before", "dev.83", "Manual review", "dev.64", "Keyed and matched by hand",
          "Price gaps surface after the payment run", ("dev.65", "3 days to clear"), ("dev.85", "6 touches")),
         ("after", "dev.84", "With the agent", "dev.67", "Matched on arrival",
          "Only the price gap reaches a person", ("dev.68", "4 minutes to clear"), ("dev.86", "1 touch"))]
for side, hn, ht, bn, bh, bb, c1, c2 in SIDES:
    rename(s, hn, "slot.%s.head" % side)
    hb = find(s, "slot.%s.head" % side)
    move(s, "slot.%s.head" % side, hb.left / EMU, 5.64, hb.width / EMU, 0.30)
    text(s, "slot.%s.head" % side, [P(ht, "ink-deep", 12, True, align="left")], th, size=12, background="card",
         anchor="middle")
    rename(s, bn, "slot.%s.body" % side)
    text(s, "slot.%s.body" % side, [P(bh, "ink-deep", 11, True, align="left"),
                                    P(bb, "ink", 10, before=2, align="left")], th, size=10, background="card",
         anchor="middle")
    for k, (cn, ct) in enumerate((c1, c2), 1):
        rename(s, cn, "slot.%s.stat.%d" % (side, k))
        frame("slot.%s.stat.%d" % (side, k), "paper", "hairline")
        text(s, "slot.%s.stat.%d" % (side, k), [P(ct, "accent-ink", 10, True)], th, size=10,
             background="paper", anchor="middle")

# inside the content band (P03): stage 4 and the strip's right end give up the 0.15in they ran past 12.90in
for nm in ("slot.stage.4.head", "struct.stage.4.frame", "struct.paths.frame"):
    find(s, nm).width = int(find(s, nm).width - 0.15 * EMU)
for nm in ("slot.after.head", "slot.after.stat.1", "slot.after.stat.2"):
    find(s, nm).left = int(find(s, nm).left - 0.15 * EMU)

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
out = save(prs, "DL10", th, archetype="worked-example", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
