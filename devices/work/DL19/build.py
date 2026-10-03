"""DL19: five stage columns, a narrowing funnel and a three-way route, closing on a dark result panel (process-flow)."""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import prims  # noqa: E402
from deckkit import text as txt  # noqa: E402
from deckkit.canvas import Box  # noqa: E402
from deckkit.prims import set_fill, set_line  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL19")


def ungroup(name):
    """Lift a group's children onto the slide in absolute inches, then drop the group."""
    g = find(s, name)
    x = g._element.find(qn("p:grpSpPr") + "/" + qn("a:xfrm"))
    off, ext = x.find(qn("a:off")), x.find(qn("a:ext"))
    choff, chext = x.find(qn("a:chOff")), x.find(qn("a:chExt"))
    sx = int(ext.get("cx")) / max(int(chext.get("cx")), 1)
    sy = int(ext.get("cy")) / max(int(chext.get("cy")), 1)
    tree, at = g._element.getparent(), g._element.getparent().index(g._element)
    for ch in list(g.shapes):
        el = ch._element
        nl = int(off.get("x")) + (ch.left - int(choff.get("x"))) * sx
        nt = int(off.get("y")) + (ch.top - int(choff.get("y"))) * sy
        nw, nh = ch.width * sx, ch.height * sy
        tree.insert(at, el)
        at += 1
        ch.left, ch.top, ch.width, ch.height = int(nl), int(nt), int(nw), int(nh)
    tree.remove(g._element)


for gname in ("dev.19", "dev.39", "dev.60", "dev.63", "dev.66"):
    ungroup(gname)
VARIANT = "funnel-route-columns"
DARK = "ink-deep"
P, R = txt.Para, txt.Run

# chrome the house rules ban: the subtitle sentence; the empty stat backing rect, the label-only row,
# the inner rings and empty boxes of the gap nodes, the corpus vector icons and the lettered roundels
for n in ["dev.59", "dev.92", "dev.113", "dev.118", "dev.62", "dev.65", "dev.68",
          "dev.51", "dev.56"] + ["dev.%d" % k for k in range(77, 116)]:
    try:
        delete(s, n)
    except KeyError:                                   # a child of a vector group already removed
        pass

# open the gutters so each gap node sits clear of both columns: columns 1 to 4 narrow, nodes stay put
OLD = {1: (0.46, 2.75), 2: (2.92, 5.33), 3: (5.49, 7.84), 4: (8.01, 10.43)}
NEW = {1: (0.46, 2.62), 2: (3.05, 5.18), 3: (5.61, 7.69), 4: (8.12, 10.43)}
SC = {k: (NEW[k][1] - NEW[k][0]) / (OLD[k][1] - OLD[k][0]) for k in OLD}


def X(k, x):
    return NEW[k][0] + (x - OLD[k][0]) * SC[k]


for sh in list(s.shapes):
    if sh.name in ("dev.58", "dev.61", "dev.64", "dev.67", "dev.73", "dev.74", "dev.75", "dev.76"):
        continue
    cx = (sh.left + sh.width / 2) / EMU
    for k, (lo, hi) in OLD.items():
        if lo - 0.01 <= cx <= hi + 0.01:
            keep = sh._element.find(".//" + qn("a:prstGeom")) is not None and \
                sh._element.find(".//" + qn("a:prstGeom")).get("prst") == "ellipse"
            w = sh.width / EMU
            nx = X(k, sh.left / EMU + (w / 2 if keep else 0)) - (w / 2 if keep else 0)
            move(s, sh.name, nx, sh.top / EMU, w if keep else w * SC[k], sh.height / EMU)
            break


def radius(name, r=0.05):
    sh = find(s, name)
    gd = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst") + "/" + qn("a:gd"))
    if gd is None:
        av = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst"))
        from lxml import etree
        gd = etree.SubElement(av, qn("a:gd"))
        gd.set("name", "adj")
    gd.set("fmla", "val %d" % round(r / (min(sh.width, sh.height) / EMU) * 100000))


# title: one claim, two-tone
rename(s, "dev.58", "slot.title")
move(s, "slot.title", 0.46, 0.50, 12.45, 0.86)
text(s, "slot.title", [P(tuple(txt.title_runs(
    "Four steps narrow 120K invoices to 900 recoverable payments",
    ("900 recoverable payments",))))], th, size=24, bold=True, anchor="middle")

# the five stage columns: numbered disc, head, two-line body
COLS = [("dev.2", "dev.7", "dev.8", "dev.9", "Ingest", "Four ledgers land nightly in one store"),
        ("dev.3", "dev.16", "dev.17", "dev.18", "Narrow", "Rules cut the pool to likely duplicates"),
        ("dev.4", "dev.30", "dev.31", "dev.32", "Route", "Each flagged pair takes one path"),
        ("dev.5", "dev.33", "dev.34", "dev.35", "Recover", "Analysts confirm each case and book the credit"),
        ("dev.6", "dev.36", "dev.37", None, "Each quarter", None)]
for i, (card, disc, head, body, h, b) in enumerate(COLS, 1):
    rename(s, card, "struct.col.%d" % i)
    radius("struct.col.%d" % i)
    col = find(s, "struct.col.%d" % i)
    right = (col.left + col.width) / EMU - 0.12
    rename(s, disc, "struct.col.%d.disc" % i)
    rename(s, head, "slot.col.%d.head" % i)
    dark = i == 5
    bg = DARK if dark else "paper"
    if dark:
        set_fill(find(s, "struct.col.5"), DARK, theme=th)
        set_line(find(s, "struct.col.5"), DARK, 0.75, theme=th)
        set_fill(find(s, "struct.col.5.disc"), DARK, theme=th)
        set_line(find(s, "struct.col.5.disc"), "paper", 1.0, theme=th)
    text(s, "struct.col.%d.disc" % i, [P((R(str(i), "paper" if dark else "on-accent", bold=True, size=13),),
                                         align="center")],
         th, size=13, bold=True, background=DARK if dark else "accent", anchor="middle")
    hx = find(s, "struct.col.%d.disc" % i).left / EMU + 0.43
    move(s, "slot.col.%d.head" % i, hx, 1.82, right - hx, 0.32)
    text(s, "slot.col.%d.head" % i, h, th, size=14, bold=True, role="paper" if dark else "ink-deep",
         background=bg, anchor="middle")
    if body:
        rename(s, body, "slot.col.%d.body" % i)
        move(s, "slot.col.%d.body" % i, hx, 2.14, right - hx, 0.52)
        text(s, "slot.col.%d.body" % i, b, th, size=10, role="ink", background=bg)

# gap nodes between columns: a ringed white disc carrying a chevron
for k, (n, gx) in enumerate((("dev.61", 2.67), ("dev.64", 5.23), ("dev.67", 7.74)), 1):
    rename(s, n, "struct.node.%d" % k)
    move(s, "struct.node.%d" % k, gx, 4.075, 0.33, 0.33)
    sh = find(s, "struct.node.%d" % k)
    set_fill(sh, "paper", theme=th)
    set_line(sh, "rule-strong", 0.75, theme=th)
    icon(s, "struct.node.%d.icon" % k, "chevron-right", sh.left / EMU + 0.065, sh.top / EMU + 0.065, 0.20, th,
         role="ink-muted")

# column 1: the source ledgers in a neutral zone (was a screenshot), three stats under it
Z1 = Box(X(1, 0.571), 2.772, 2.109 * SC[1], 3.123)
prims.card(s, Z1, fill="card", line=None, radius_in=0.05, name="struct.col.1.zone", theme=th)
SOURCES = [("database", "Invoice ledger", "120K rows a quarter"), ("file-spreadsheet", "Vendor master", "8.4K active vendors"),
           ("file-text", "Contract terms", "Rates and credit terms"), ("banknote", "Payment runs", "Weekly, three banks")]
for i, (g, h, b) in enumerate(SOURCES, 1):
    y = Z1.y + 0.22 + (i - 1) * 0.72
    icon(s, "slot.source.%d.icon" % i, g, Z1.x + 0.12, y + 0.04, 0.28, th, role="accent")
    txt.textbox(s, Box(Z1.x + 0.48, y, Z1.w - 0.54, 0.56),
                [P((R(h, "ink-deep", bold=True, size=11),)), P((R(b, "ink-muted", size=10),), space_before=1)],
                "slot.source.%d.text" % i, th, size=11, background="card")
STATS = [("dev.10", "dev.11", "4", "ledgers"), ("dev.12", "dev.13", "24h", "refresh"),
         ("dev.14", "dev.15", "99%", "matched")]
for i, (v, l, vt, lt) in enumerate(STATS, 1):
    x = 0.56 + (i - 1) * 0.68
    rename(s, v, "slot.col.1.stat.%d.value" % i)
    rename(s, l, "slot.col.1.stat.%d.label" % i)
    move(s, "slot.col.1.stat.%d.value" % i, x, 6.06, 0.62, 0.32)
    text(s, "slot.col.1.stat.%d.value" % i, [P((R(vt, "accent-ink", bold=True, size=13),), align="center")],
         th, size=13, anchor="middle")
    move(s, "slot.col.1.stat.%d.label" % i, x, 6.38, 0.62, 0.26)
    text(s, "slot.col.1.stat.%d.label" % i, [P((R(lt, "ink-muted", size=10),), align="center")], th, size=10)

# column 2: the funnel, widest tier on top
TIERS = [("dev.20", "dev.21", "hairline-soft", "ink-deep", "120K invoices"),
         ("dev.22", "dev.23", "hairline", "ink-deep", "38K same vendor"),
         ("dev.24", "dev.25", DARK, "paper", "6.2K same amount"),
         ("dev.26", "dev.27", "accent-wash", "ink-deep", "1.4K flagged"),
         ("dev.28", "dev.29", "accent", "on-accent", "900 likely")]
for i, (shp, lab, fill, ink, t) in enumerate(TIERS, 1):
    rename(s, shp, "struct.funnel.tier.%d" % i)
    set_fill(find(s, "struct.funnel.tier.%d" % i), fill, theme=th)
    rename(s, lab, "slot.funnel.%d" % i)
    sh = find(s, "slot.funnel.%d" % i)
    tier = find(s, "struct.funnel.tier.%d" % i)
    w = tier.width / EMU - 0.24
    move(s, "slot.funnel.%d" % i, tier.left / EMU + 0.12, tier.top / EMU + 0.08, w, 0.38)
    text(s, "slot.funnel.%d" % i, [P((R(t, ink, bold=True, size=10),), align="center")], th, size=10,
         background=fill, anchor="middle")

# column 3: three route cards fed by elbows from the node, plus a fourth hold line
ROUTES = [("dev.69", "circle-x", "Discard", "Recurring fee, not a duplicate"),
          ("dev.70", "clipboard-list", "Review", "Analyst checks both invoices"),
          ("dev.71", "database-search", "Enrich", "Pull missing vendor detail")]
for i, (shp, g, h, b) in enumerate(ROUTES, 1):
    rename(s, shp, "slot.route.%d" % i)
    sh = find(s, "slot.route.%d" % i)
    set_fill(sh, "card", theme=th)
    radius("slot.route.%d" % i)
    text(s, "slot.route.%d" % i, [P((R(h, "ink-deep", bold=True, size=12),)),
                                  P((R(b, "ink", size=10),), space_before=2)], th, size=10, background="card",
         anchor="middle")
    icon(s, "slot.route.%d.icon" % i, g, sh.left / EMU + sh.width / EMU - 0.36, sh.top / EMU + 0.10, 0.24, th,
         role="accent")
rename(s, "dev.72", "slot.route.hold")
move(s, "slot.route.hold", find(s, "slot.route.1").left / EMU, 6.30, 1.60, 0.26)
text(s, "slot.route.hold", [P((R("Hold for next cycle", "ink-muted", italic=True, size=10),))], th, size=10,
     anchor="middle")
for n in ("dev.73", "dev.74", "dev.75", "dev.76"):                 # bent connectors render flipped: redraw
    delete(s, n)
node = find(s, "struct.node.2")
NX, NY = (node.left + node.width) / EMU, (node.top + node.height / 2) / EMU
for k, tgt in enumerate(("slot.route.1", "slot.route.2", "slot.route.3"), 1):
    c = find(s, tgt)
    ty = (c.top + c.height / 2) / EMU
    prims.elbow(s, [(NX, NY), (NX + 0.18, NY), (NX + 0.18, ty), (c.left / EMU, ty)] if abs(ty - NY) > 0.01
                else [(NX, NY), (c.left / EMU, ty)], name="struct.route.arrow.%d" % k, theme=th)
hold = find(s, "slot.route.hold")
HY = (hold.top + hold.height / 2) / EMU
prims.elbow(s, [(NX, NY), (NX + 0.18, NY), (NX + 0.18, HY), (hold.left / EMU, HY)],
            name="struct.route.arrow.4", theme=th)

# column 4: the review checklist in a neutral zone (was a screenshot)
Z4 = Box(X(4, 8.199), 2.772, 2.13 * SC[4], 3.90)
prims.card(s, Z4, fill="card", line=None, radius_in=0.05, name="struct.col.4.zone", theme=th)
CHECKS = [("Evidence filed", "Invoices and payment"), ("Vendor confirmed", "Same tax id and bank"),
          ("Credit agreed", "Vendor signs the claim"), ("Recovery booked", "Offset on the next run"),
          ("Rule tuned", "Misses refine the rules")]
for i, (h, b) in enumerate(CHECKS, 1):
    y = Z4.y + 0.20 + (i - 1) * 0.72
    icon(s, "slot.check.%d.icon" % i, "circle-check", Z4.x + 0.12, y + 0.04, 0.28, th, role="accent")
    txt.textbox(s, Box(Z4.x + 0.46, y, Z4.w - 0.52, 0.56),
                [P((R(h, "ink-deep", bold=True, size=11),)), P((R(b, "ink-muted", size=10),), space_before=1)],
                "slot.check.%d.text" % i, th, size=11, background="card")

# column 5: the dark result panel
for k, n in enumerate(("dev.38", "dev.42", "dev.47"), 1):
    rename(s, n, "struct.col.5.rule.%d" % k)
delete(s, "dev.40")
delete(s, "dev.41")
STAT_H = prims.stat_height(s, 1.80, "$2.4M", "recovered per quarter", kind="illustrative", pt=24, label_pt=11,
                           theme=th)
prims.stat(s, Box(10.82, 2.47, 1.80, STAT_H), "$2.4M", "recovered per quarter", kind="illustrative",
               role="paper", pt=24, label_pt=11, label_role="paper", background=DARK, name="slot.result", theme=th)
move(s, "struct.col.5.rule.2", 10.75, 3.56, 1.95, 0)
ROWS = [("dev.116", "dev.117", "Match precision", "94%"), ("dev.43", "dev.44", "Cases per analyst", "60"),
        ("dev.45", "dev.46", "Days to credit", "6")]
for i, (l, v, lt, vt) in enumerate(ROWS, 1):
    y = 3.66 + (i - 1) * 0.40
    rename(s, l, "slot.result.row.%d.label" % i)
    rename(s, v, "slot.result.row.%d.value" % i)
    move(s, "slot.result.row.%d.label" % i, 10.75, y, 1.36, 0.30)
    text(s, "slot.result.row.%d.label" % i, lt, th, size=10, role="paper", background=DARK, anchor="middle")
    move(s, "slot.result.row.%d.value" % i, 12.09, y, 0.64, 0.30)
    text(s, "slot.result.row.%d.value" % i, [P((R(vt, "paper", bold=True, size=13),), align="right")], th,
         size=13, background=DARK, anchor="middle")
CTRLS = [("dev.48", "dev.49", "settings", "Rules signed off"), ("dev.50", "dev.52", "file-check", "Evidence per case"),
         ("dev.53", "dev.54", "mail", "Vendor notified first"), ("dev.55", "dev.57", "shield-check", "Audit trail kept")]
for i, (c, l, g, lt) in enumerate(CTRLS, 1):
    rename(s, c, "struct.control.%d.ring" % i)
    ring = find(s, "struct.control.%d.ring" % i)
    set_fill(ring, DARK, theme=th)
    set_line(ring, "paper", 0.75, theme=th)
    icon(s, "slot.control.%d.icon" % i, g, ring.left / EMU + 0.065, ring.top / EMU + 0.065, 0.20, th, role="paper")
    rename(s, l, "slot.control.%d" % i)
    move(s, "slot.control.%d" % i, 11.16, ring.top / EMU + 0.02, 1.70, 0.30)
    text(s, "slot.control.%d" % i, lt, th, size=10, role="paper", background=DARK, anchor="middle")

from deckkit import ooxml, package, tag  # noqa: E402
NUMBERS = {"slot.result": {"value": "$2.4M", "kind": "illustrative"}}
from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
tag.tag(prs.slides[0], "process-flow", VARIANT)
for sh in prs.slides[0].shapes:
    ooxml.finish(sh)
out = WORK / "DL19" / "device.pptx"
package.save(prs, out, title="Device DL19", theme=th, manifest={"numbers": NUMBERS}, overwrite=True,
             date="2026-10-03")
if a.out:
    shutil.copyfile(out, a.out)
