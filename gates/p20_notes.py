"""P20 notes and alt text: the audience deck carries no speaker notes; every picture has semantic alt text of 120 characters or fewer.

Speaker notes ship as a separate presenter deck (CLAUDE.md section 6), so a deck that travels has empty
notes. deck.json "notes_deck": true marks the presenter deck itself; its own transcript checks (no stage
directions, no colour words, Q&A pairs, chip totals) belong to the notes builder and are reported as not
run here. Alt text is semantic: not empty unless the picture is marked decorative, not a file name or
path, not a default like "Picture 3", not the shape's own name.
"""
from __future__ import annotations

import re
import sys

from _shared import FAIL, NOTE, Finding, cli
from deckkit.read.ns import local
from deckkit.read.textmetrics import para_text

GATE, TITLE = "P20", "notes-alt"
MAX_ALT = 120
GENERIC = re.compile(r"(?i)^(?:picture|image|graphic|icon|logo|photo|img|screenshot|untitled|placeholder)[\s_-]*\d*$")
FILEISH = re.compile(r"(?i)[\\/]|\.(?:png|jpe?g|gif|svg|emf|wmf|bmp|tiff?|webp)\b")


def run(deck, ctx):
    out = []
    dr = ctx.dr
    presenter = bool(ctx.deck_json.get("notes_deck"))
    if presenter:
        out.append(Finding(GATE, NOTE, None, "notes", "presenter deck: notes allowed; transcript checks belong to the "
                                                      "notes builder and are not run here"))
    for i in range(1, ctx.n + 1):
        sp = dr.slide_part(i)
        np_ = dr.rel_target(sp, "/notesSlide")
        if np_ and not presenter and dr.has(np_):
            words = []
            for sh in dr.xml(np_).iter("{*}sp"):
                ph = sh.find(".//{*}ph")
                if ph is not None and ph.get("type") in ("sldImg", "sldNum", "hdr", "ftr", "dt"):
                    continue
                words += [para_text(p) for p in sh.iter("{*}p") if local(p) == "p"]
            t = " ".join(w for w in words if w.strip())
            if t.strip():
                out.append(Finding(GATE, FAIL, i, "notes", "speaker notes in the audience deck: %r" % t[:50]))
        for pic in ctx.slide_root(i).iter("{*}pic"):
            c = pic.find(".//{*}cNvPr")
            name = c.get("name", "") if c is not None else ""
            alt = " ".join((c.get("descr") or "").split()) if c is not None else ""
            deco = any(d.get("val") in ("1", "true") for d in pic.iter("{*}decorative"))
            if deco:
                continue
            if not alt:
                out.append(Finding(GATE, FAIL, i, name, "picture without alt text"))
            elif len(alt) > MAX_ALT:
                out.append(Finding(GATE, FAIL, i, name, "alt text is %d characters (max %d)" % (len(alt), MAX_ALT)))
            elif GENERIC.match(alt) or FILEISH.search(alt) or alt == name:
                out.append(Finding(GATE, FAIL, i, name, "alt text is not semantic: %r" % alt[:60]))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
