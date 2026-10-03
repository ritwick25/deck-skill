"""DL20: an indented seven-level ladder, a status rail keyed to its fills, and three cards on what the next rung
takes (maturity-model)."""
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

prs, s, th = open_lifted("DL20")
VARIANT = "indented-ladder-status-rail"
R, P = txt.Run, txt.Para

# banned chrome: the subtitle under the title, the dark foot band and its sentence
for n in ("dev.60", "dev.2", "dev.58"):
    delete(s, n)

# title: one claim, two-tone
rename(s, "dev.59", "slot.title")
move(s, "slot.title", 0.42, 0.40, 12.50, 0.60)
text(s, "slot.title", [P(tuple(txt.title_runs(
    "Payables run at level 2 and rule-based matching is the next rung",
    ("level 2", "next rung"))))], th, size=22, bold=True, anchor="middle")

# section labels
for n, slot, box, word in (("dev.3", "slot.ladder.label", (0.42, 1.15, 7.70, 0.28), "Automation maturity levels"),
                           ("dev.4", "slot.rail.label", (8.44, 1.15, 4.48, 0.28), "Status today"),
                           ("dev.45", "slot.cards.label", (0.42, 5.52, 12.50, 0.28), "What reaching level 3 takes")):
    rename(s, n, slot)
    move(s, slot, *box)
    text(s, slot, [P((R(word, "accent-ink", bold=True, size=12),))], th, size=12, anchor="middle")

# the ladder: seven rows, each indented one step, filled by status
LEVELS = [
    ("Manual entry", "Clerks key every invoice line by hand"),
    ("Standard forms", "Supplier templates remove most keying errors"),
    ("Rule-based matching", "Fixed rules clear routine order matches"),
    ("Assisted review", "Models suggest matches and reviewers approve"),
    ("Exception agents", "Agents resolve known exceptions unaided"),
    ("Self-tuning rules", "Reviewer decisions retune the rules weekly"),
    ("Touchless close", "Month-end close runs with spot checks only"),
]
# (fill, text role) by status: at scale, in pilot, next rung, not started
LGLYPHS = ["file-text", "clipboard-list", "list-checks", "user-check", "bot", "refresh-cw", "calendar-check"]
FILLS = ["ink-deep", "navy", "accent", "card", "card", "card", "card"]
INK = {"ink-deep": ("paper", "paper", "paper"), "navy": ("paper", "paper", "paper"),
       "accent": ("on-accent", "on-accent", "on-accent"), "card": ("accent-ink", "ink-deep", "ink")}
ROWS = [("dev.5", "dev.6", "dev.7", "dev.8"), ("dev.9", "dev.10", "dev.11", "dev.12"),
        ("dev.13", "dev.14", "dev.15", "dev.16"), ("dev.17", "dev.18", "dev.19", "dev.20"),
        ("dev.21", "dev.22", "dev.23", "dev.24"), ("dev.25", "dev.26", "dev.27", "dev.28"),
        ("dev.29", "dev.30", "dev.31", "dev.32")]
Y0, PITCH, RH, STEP, RIGHT, HEAD_END = 1.48, 0.56, 0.48, 0.0975, 8.12, 3.80
for i, ((bar, num, head, body), (h, b), fill, gl) in enumerate(zip(ROWS, LEVELS, FILLS, LGLYPHS), 1):
    x, y = 0.42 + (i - 1) * STEP, Y0 + (i - 1) * PITCH
    rn, rh, rb = INK[fill]
    rename(s, bar, "struct.level.%d" % i)
    move(s, "struct.level.%d" % i, x, y, RIGHT - x, RH)
    prims.set_fill(find(s, "struct.level.%d" % i), fill, theme=th)
    for n, slot in ((num, "slot.level.%d.num" % i), (head, "slot.level.%d.head" % i),
                    (body, "slot.level.%d.body" % i)):
        rename(s, n, slot)
    delete(s, "slot.level.%d.num" % i)                # the level number moves into the head as its own run
    icon(s, "slot.level.%d.icon" % i, gl, x + 0.12, y + (RH - 0.28) / 2, 0.28, th, role=rn)
    move(s, "slot.level.%d.head" % i, x + 0.50, y, HEAD_END - (x + 0.50), RH)   # names share one right edge
    move(s, "slot.level.%d.body" % i, HEAD_END + 0.05, y, RIGHT - 0.14 - (HEAD_END + 0.05), RH)
    text(s, "slot.level.%d.head" % i, [P((R("%02d  " % i, rh, bold=True, size=12), R(h, rh, bold=True, size=12)))],
         th, size=12, background=fill, anchor="middle")
    text(s, "slot.level.%d.body" % i, [P((R(b, rb, size=11),), align="right")], th, size=11, background=fill,
         anchor="middle")

# status rail: four keys in the ladder's fills, each with what the status means
KEYS = [("dev.33", "dev.34", "dev.35", "ink-deep", "paper", "At scale",
         ("Live in every business unit", "and measured monthly")),
        ("dev.36", "dev.37", "dev.38", "navy", "paper", "In pilot",
         ("Two business units, with", "results due next quarter")),
        ("dev.39", "dev.40", "dev.41", "card", "ink-deep", "Not started",
         ("Funded once the next", "rung proves out")),
        ("dev.42", "dev.43", "dev.44", "accent", "on-accent", "Next rung",
         ("Twelve-week build on", "one ledger first"))]
KH, KP = 0.86, 0.99
for i, (box, lab, body, fill, role, word, desc) in enumerate(KEYS, 1):
    y = Y0 + (i - 1) * KP
    delete(s, box)                                    # the head shape carries the fill: one tile per key
    rename(s, lab, "slot.key.%d.head" % i)
    rename(s, body, "slot.key.%d.body" % i)
    move(s, "slot.key.%d.head" % i, 8.44, y, 1.47, KH)
    move(s, "slot.key.%d.body" % i, 10.04, y, 2.88, KH)
    prims.set_fill(find(s, "slot.key.%d.head" % i), fill, theme=th)
    text(s, "slot.key.%d.head" % i, [P((R(word, role, bold=True, size=12),), align="center")], th, size=12,
         background=fill, anchor="middle")
    text(s, "slot.key.%d.body" % i, [P((R(d, "ink", size=11),), space_before=0 if j == 0 else 2) for j, d in enumerate(desc)], th, size=11, anchor="middle")
for n, slot, y in (("dev.61", "struct.rail.rule.1", Y0 + KH + (KP - KH) / 2),
                   ("dev.62", "struct.rail.rule.2", Y0 + 2 * KP + KH + (KP - KH) / 2)):
    rename(s, n, slot)
    move(s, slot, 8.44, y, 4.48, 0)

# three cards: what moving to the next rung needs, the middle one in focus
CARDS = [("dev.46", "dev.47", "dev.48", "dev.49", 0.42, "navy", "paper", "01  Clean supplier master",
          ("Duplicate and stale supplier records", "merged before any rule goes live")),
         ("dev.50", "dev.51", "dev.52", "dev.53", 4.67, "accent", "on-accent", "02  Shared rule library",
          ("One owner keeps every matching rule", "versioned, tested and documented")),
         ("dev.54", "dev.55", "dev.56", "dev.57", 8.91, "card", "ink-deep", "03  Named reviewer roles",
          ("Held lines cleared by a named", "reviewer within one working day"))]
GLYPHS = ("database", "library", "users")
CY, CH, HH = 5.84, 0.98, 0.32
for i, ((frame, band, head, body, x, fill, role, h, b), g) in enumerate(zip(CARDS, GLYPHS), 1):
    rename(s, frame, "struct.card.%d" % i)
    rename(s, band, "struct.card.%d.band" % i)
    rename(s, head, "slot.card.%d.head" % i)
    rename(s, body, "slot.card.%d.body" % i)
    move(s, "struct.card.%d" % i, x, CY, 4.00, CH)
    prims.set_fill(find(s, "struct.card.%d" % i), "paper", theme=th)
    prims.set_line(find(s, "struct.card.%d" % i), "hairline", 0.75, theme=th)
    move(s, "struct.card.%d.band" % i, x, CY, 4.00, HH)
    prims.set_fill(find(s, "struct.card.%d.band" % i), fill, theme=th)
    move(s, "slot.card.%d.head" % i, x + 0.12, CY, 3.76, HH)
    move(s, "slot.card.%d.body" % i, x + 0.66, CY + HH + 0.04, 3.22, CH - HH - 0.08)
    icon(s, "slot.card.%d.icon" % i, g, x + 0.14, CY + HH + (CH - HH - 0.40) / 2, 0.40, th, role="accent")
    text(s, "slot.card.%d.head" % i, [P((R(h, role, bold=True, size=12),))], th, size=12, background=fill,
         anchor="middle")
    text(s, "slot.card.%d.body" % i, [P((R(d, "ink", size=11),), space_before=0 if j == 0 else 2) for j, d in enumerate(b)], th, size=11, anchor="middle")

out = save(prs, "DL20", th, archetype="maturity-model", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
