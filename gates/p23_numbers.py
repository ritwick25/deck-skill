"""P23 numbers: every stat states its kind, planning figures carry their chip, and every value agrees with the manifest.

A stat is a group the kit wrote with alt text "stat kind <kind>" (deckkit.prims.stat). Its kind is one of
measured, delivered, illustrative, target, benchmark; the last three print a basis chip ("Illustrative")
so a planning figure never reads as delivered. A figure set large outside any stat has no kind and fails:
any text leaf whose whole text is a quantity or a range ("42%", "$4.2M", "3x", "5 to 10%") set at 1.4x the
slide's median text size or larger (deckkit.read.figures, whatever role the read layer guessed). Ordinals
("01", "03"), years, a single digit in a disc or step marker, and bare numbers on a Frame slide (a section
numeral on a divider; untagged, 12 content words or fewer) are not figures. Each stat's value and kind must
equal the manifest's "numbers" entry under the stat's name, and every manifest number must be on glass: one
value, one record.
"""
from __future__ import annotations

import re
import sys

from _shared import FAIL, Finding, cli, text_of
from deckkit.prims import STAT_KINDS
from deckkit.read.figures import large_figures

GATE, TITLE = "P23", "numbers"
KIND = re.compile(r"^stat kind ([a-z]+)$")
FEW_WORDS = 12          # an untagged slide this sparse is a divider or a cover


def run(deck, ctx):
    out = []
    man = ctx.manifest or {}
    record = man.get("numbers") or {}
    on_glass = {}
    for i in range(1, ctx.n + 1):
        s = ctx.slide(i)
        root = ctx.slide_root(i)
        stats = {}
        for g in root.iter("{*}grpSp"):
            c = g.find("{*}nvGrpSpPr/{*}cNvPr")
            m = KIND.match((c.get("descr") or "").strip()) if c is not None else None
            if m:
                stats[int(c.get("id"))] = (c.get("name"), m.group(1))
        members = {}
        for L in s["shapes"]:
            for gid in L["group_path"]:
                if gid in stats:
                    members.setdefault(gid, []).append(L)
        for gid, (name, kind) in stats.items():
            if kind not in STAT_KINDS:
                out.append(Finding(GATE, FAIL, i, name, "stat kind %r is not one of %s" % (kind, ", ".join(STAT_KINDS))))
                continue
            texts = {L["name"]: " ".join(text_of(L).split()) for L in members.get(gid, [])}
            chip = STAT_KINDS[kind]
            if chip and not any(t.lower() == chip.lower() for t in texts.values()):
                out.append(Finding(GATE, FAIL, i, name, "%s figure without its %r chip" % (kind, chip)))
            value = texts.get(name + ".value")
            on_glass[name] = (i, value, kind)
        arch = ctx.tags()[i - 1]["archetype"]
        divider = ctx.is_frame(i) if arch else s["text"]["words_content"] <= FEW_WORDS
        for L, ratio in large_figures(s, divider=divider):
            if not any(g in stats for g in L["group_path"]):
                out.append(Finding(GATE, FAIL, i, L["name"], "a figure on glass with no kind: %r at %.1fx the median "
                                   "text size" % (" ".join(text_of(L).split())[:20], ratio)))
    if on_glass and not record:
        out.append(Finding(GATE, FAIL, None, "manifest", "%d stat(s) on glass and no 'numbers' record in the manifest"
                           % len(on_glass)))
        return out
    for name, (i, value, kind) in on_glass.items():
        rec = record.get(name)
        if rec is None:
            out.append(Finding(GATE, FAIL, i, name, "stat %r is not in the manifest" % value))
            continue
        rv, rk = (rec.get("value"), rec.get("kind")) if isinstance(rec, dict) else (rec, None)
        if rv != value:
            out.append(Finding(GATE, FAIL, i, name, "on glass %r, manifest %r" % (value, rv)))
        if rk is not None and rk != kind:
            out.append(Finding(GATE, FAIL, i, name, "kind %s on glass, %s in the manifest" % (kind, rk)))
    for name in record:
        if name not in on_glass:
            out.append(Finding(GATE, FAIL, None, name, "manifest number not on glass"))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
