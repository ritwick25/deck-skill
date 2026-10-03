"""DL44: three operation columns, each a solid numbered header over an input well and a dark output well of icon
rows, closed by the one thing that operation never does (catalogue, variant io-wells)."""
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

prs, s, th = open_lifted("DL44")
VARIANT = "io-wells"
R, P = txt.Run, txt.Para

# banned chrome: the caps kicker, the accent bar under the title, the page number, the band sentence (a subtitle)
for n in ("dev.2", "dev.4", "dev.5", "dev.6"):
    delete(s, n)
# the output wells' caption lines restate their label, and every column keeps three output rows
for n in ("dev.20", "dev.37", "dev.54", "dev.24", "dev.41"):
    delete(s, n)
# the hairline under each header: the solid header now ends the zone
for n in ("dev.14", "dev.31", "dev.48"):
    delete(s, n)

rename(s, "dev.3", "slot.title")
move(s, "slot.title", 0.50, 0.13, 12.40, 0.40)
text(s, "slot.title", [P(tuple(txt.title_runs(
    "Three calls run every invoice match, and each one names what it refuses", ("Three calls",))))],
    th, size=21, bold=True, anchor="middle")


def radius(name, r=0.05):
    sh = find(s, name)
    av = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst"))
    for old in list(av):
        av.remove(old)
    gd = av.makeelement(qn("a:gd"), {"name": "adj"})
    av.append(gd)
    gd.set("fmla", "val %d" % round(r / (min(sh.width, sh.height) / EMU) * 100000))


OPS = [
    dict(card="dev.7", disc="dev.10", num="dev.11", verb="dev.12", purpose="dev.13", inwell="dev.15",
         inlabel="dev.16", intext="dev.17", outwell="dev.18", outlabel="dev.19", rows=("dev.21", "dev.22", "dev.23"),
         rule="dev.25", never="dev.26",
         v="Match", g="scan-search", p="Pair an invoice with its order and receipt",
         ins=("An invoice file, never a free-text request", "Supplier id and invoice number",
              "Currency and total as printed"),
         outs=(("file-text", "Purchase order", "The order line it answers"),
               ("package-check", "Goods receipt", "Quantities booked at the dock"),
               ("circle-check", "Match score", "Price, quantity and tax, each scored")),
         nv="Never: a payment released"),
    dict(card="dev.8", disc="dev.27", num="dev.28", verb="dev.29", purpose="dev.30", inwell="dev.32",
         inlabel="dev.33", intext="dev.34", outwell="dev.35", outlabel="dev.36", rows=("dev.38", "dev.39", "dev.40"),
         rule="dev.42", never="dev.43",
         v="Explain", g="message-square", p="Show why a match passed or was held",
         ins=("A match id from the first call", "One question about one line",
              "The policy version in force"),
         outs=(("list-checks", "Rule trace", "Every tolerance rule it applied"),
               ("triangle-alert", "Held lines", "Each variance above tolerance"),
               ("user-check", "Next owner", "The buyer who clears the hold")),
         nv="Never: a rule rewritten"),
    dict(card="dev.9", disc="dev.44", num="dev.45", verb="dev.46", purpose="dev.47", inwell="dev.49",
         inlabel="dev.50", intext="dev.51", outwell="dev.52", outlabel="dev.53", rows=("dev.55", "dev.56", "dev.57"),
         rule="dev.58", never="dev.59",
         v="Post", g="database", p="Write the approved match to the ledger",
         ins=("An approved match and its sign-off", "The target ledger and period",
              "One approver for each invoice"),
         outs=(("receipt", "Ledger entry", "Posted once, with its journal id"),
               ("clipboard-check", "Audit record", "Who approved it, and when"),
               ("rotate-ccw", "Reversal key", "The undo path in the same period")),
         nv="Never: a second posting"),
]

GAP = 0.30
W = (12.40 - 2 * GAP) / 3
HEAD_Y, HEAD_H = 0.85, 0.66
PUR_Y, PUR_H = 1.62, 0.34
IN_Y, IN_H = 2.06, 1.30
OUT_Y, OUT_H = 3.48, 2.70
ROW_Y0, ROW_P = OUT_Y + 0.46, 0.74
RULE_Y = 6.33
NV_Y, NV_H = 6.42, 0.38

for i, op in enumerate(OPS, 1):
    x = 0.50 + (i - 1) * (W + GAP)
    pre = "slot.op.%d" % i
    # solid numbered header (ruling 12): white roundel, white verb, white glyph on brand
    rename(s, op["card"], "struct.op.%d.head" % i)
    move(s, "struct.op.%d.head" % i, x, HEAD_Y, W, HEAD_H)
    prims.set_fill(find(s, "struct.op.%d.head" % i), "accent", theme=th)
    prims.set_line(find(s, "struct.op.%d.head" % i), None, theme=th)
    radius("struct.op.%d.head" % i)
    rename(s, op["disc"], "struct.op.%d.disc" % i)
    move(s, "struct.op.%d.disc" % i, x + 0.16, HEAD_Y + (HEAD_H - 0.38) / 2, 0.38, 0.38)
    prims.set_fill(find(s, "struct.op.%d.disc" % i), "paper", theme=th)
    prims.set_line(find(s, "struct.op.%d.disc" % i), None, theme=th)
    rename(s, op["num"], pre + ".num")
    move(s, pre + ".num", x + 0.16, HEAD_Y + (HEAD_H - 0.38) / 2, 0.38, 0.38)
    text(s, pre + ".num", [P((R(str(i), "accent-ink", bold=True, size=13),), align="center")], th, size=13,
         background="paper", anchor="middle")
    rename(s, op["verb"], pre + ".verb")
    move(s, pre + ".verb", x + 0.66, HEAD_Y, W - 1.30, HEAD_H)
    text(s, pre + ".verb", op["v"], th, role="on-accent", size=18, bold=True, background="accent", anchor="middle")
    icon(s, pre + ".icon", op["g"], x + W - 0.52, HEAD_Y + (HEAD_H - 0.34) / 2, 0.34, th, role="on-accent")

    rename(s, op["purpose"], pre + ".purpose")
    move(s, pre + ".purpose", x, PUR_Y, W, PUR_H)
    text(s, pre + ".purpose", op["p"], th, role="ink-deep", size=12, bold=True, anchor="middle")

    # input well: light card
    rename(s, op["inwell"], "struct.op.%d.in" % i)
    move(s, "struct.op.%d.in" % i, x, IN_Y, W, IN_H)
    prims.set_fill(find(s, "struct.op.%d.in" % i), "card", theme=th)
    prims.set_line(find(s, "struct.op.%d.in" % i), None, theme=th)
    radius("struct.op.%d.in" % i)
    rename(s, op["inlabel"], pre + ".in.label")
    move(s, pre + ".in.label", x + 0.16, IN_Y + 0.12, 1.00, 0.26)
    text(s, pre + ".in.label", "In", th, role="accent-ink", size=10, bold=True, background="card")
    rename(s, op["intext"], pre + ".in.text")
    move(s, pre + ".in.text", x + 0.16, IN_Y + 0.40, W - 0.32, IN_H - 0.50)
    text(s, pre + ".in.text", [P((R(t, "ink", size=11),), space_before=0 if k == 0 else 4)
                               for k, t in enumerate(op["ins"])], th, size=11, background="card")

    # output well: near-black panel (ruling 12), rows of glyph, name and one line
    rename(s, op["outwell"], "struct.op.%d.out" % i)
    move(s, "struct.op.%d.out" % i, x, OUT_Y, W, OUT_H)
    prims.set_fill(find(s, "struct.op.%d.out" % i), "ink-deep", theme=th)
    prims.set_line(find(s, "struct.op.%d.out" % i), None, theme=th)
    radius("struct.op.%d.out" % i)
    rename(s, op["outlabel"], pre + ".out.label")
    move(s, pre + ".out.label", x + 0.16, OUT_Y + 0.12, 1.00, 0.26)
    text(s, pre + ".out.label", "Out", th, role="paper", size=10, bold=True, background="ink-deep")
    for j, (row, (gl, name, line)) in enumerate(zip(op["rows"], op["outs"]), 1):
        ry = ROW_Y0 + (j - 1) * ROW_P
        rn = pre + ".out.%d" % j
        rename(s, row, rn)
        icon(s, rn + ".icon", gl, x + 0.18, ry + 0.06, 0.32, th, role="accent-bright")
        move(s, rn, x + 0.64, ry, W - 0.80, 0.60)
        text(s, rn, [P((R(name, "paper", bold=True, size=12),)),
                     P((R(line, "paper", size=11),), space_before=2)], th, size=12, background="ink-deep")

    rename(s, op["rule"], "struct.op.%d.rule" % i)
    move(s, "struct.op.%d.rule" % i, x, RULE_Y, W, 0.01)
    prims.set_fill(find(s, "struct.op.%d.rule" % i), "hairline", theme=th)
    rename(s, op["never"], pre + ".never")
    move(s, pre + ".never", x, NV_Y, W, NV_H)
    text(s, pre + ".never", op["nv"], th, role="accent-ink", size=12, bold=True, anchor="middle")

from assemble_devices import finish  # noqa: E402  content band (P03), small tints to card (P16)
finish(prs.slides[0], th)
out = save(prs, "DL44", th, archetype="catalogue", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
