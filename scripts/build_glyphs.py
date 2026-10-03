"""Build kit/assets/glyphs.json from lucide-react, through deckkit.glyphs' converters.

    $PY scripts/build_glyphs.py [--lucide DIR]

Reads the curated icon set below from lucide-react's dist/esm/icons/*.mjs, converts every node to
DrawingML-ready ops (M L C Z, arcs to cubics) in Lucide's 24-unit space, validates each, and writes the
catalogue with the source version. Lucide's own alias re-exports whose target is curated are recorded,
so the familiar older names (alert-triangle, bar-chart-2, home) resolve. Copies the ISC licence text to
kit/assets/LICENSE-lucide.txt. Deterministic: same source, same bytes.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "kit"))

from deckkit import glyphs  # noqa: E402

LUCIDE = Path("~/Codes/design-systems/design-system-aperture/node_modules/lucide-react").expanduser()

# Consulting-deck vocabulary, grouped by what a slide talks about. Canonical Lucide names.
CURATED = """
bot bot-message-square brain brain-circuit sparkles
database database-zap database-search hard-drive table file-spreadsheet
cloud cloud-cog cloud-upload cloud-download server server-cog cpu monitor smartphone terminal code
shield shield-check shield-alert lock lock-open key key-round scan scan-search eye
users user user-check user-plus contact id-card
building building-complex factory truck package package-check warehouse store shopping-cart boxes container
ship plane route map map-pin globe navigation compass
chart-bar chart-column chart-line chart-pie chart-area chart-scatter chart-no-axes-column
chart-column-increasing trending-up trending-down activity gauge target crosshair
clock calendar calendar-check calendar-days timer hourglass rotate-ccw-clock
check circle-check x circle-x triangle-alert circle-alert info circle-question-mark ban
search funnel sliders-horizontal sliders-vertical settings settings-2 wrench hammer cog
file-text file file-check file-search file-chart-column files folder folder-open archive
layers layout-grid layout-dashboard workflow git-branch git-merge network share-2 link link-2
message-square message-circle messages-square mail phone headphones megaphone send bell
zap refresh-cw refresh-ccw repeat rotate-ccw recycle
scale handshake briefcase graduation-cap book book-open library
clipboard clipboard-check clipboard-list list list-checks list-ordered list-todo kanban
flask-conical microscope pill syringe stethoscope heart-pulse hospital dna leaf sprout
dollar-sign euro pound-sterling indian-rupee percent banknote wallet credit-card piggy-bank coins receipt
calculator tag
lightbulb rocket flag award trophy
arrow-right arrow-left arrow-up arrow-down arrow-up-right arrow-down-right arrow-right-left move-right
chevron-right chevrons-right corner-down-right split merge
plug puzzle box house landmark blocks component
""".split()

_ALIAS = re.compile(r"export\s*\{\s*default\s*\}\s*from\s*'\./([\w-]+)\.mjs'")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--lucide", default=str(LUCIDE))
    a = ap.parse_args(argv)
    root = Path(a.lucide)
    icons = root / "dist" / "esm" / "icons"
    version = json.loads((root / "package.json").read_text(encoding="utf-8"))["version"]
    if len(set(CURATED)) != len(CURATED):
        dup = sorted({n for n in CURATED if CURATED.count(n) > 1})
        print("duplicate curated names: %s" % ", ".join(dup), file=sys.stderr)
        return 1
    out, problems = {}, []
    for n in CURATED:
        canon, nodes = glyphs.read_lucide(icons, n)
        if canon != n:
            problems.append("%s is an alias of %s; curate the canonical name" % (n, canon))
            continue
        groups = glyphs.icon_paths(nodes)
        bad = glyphs.validate_paths(groups)
        if bad:
            problems.append("%s: %s" % (n, "; ".join(bad[:3])))
            continue
        out[n] = {"paths": groups, "filled": any(g["fill"] for g in groups)}
    aliases = {}
    for f in sorted(icons.glob("*.mjs")):
        src = f.read_text(encoding="utf-8")
        m = _ALIAS.search(src)
        if m and "__iconData" not in src and m.group(1) in out:
            aliases[f.stem] = m.group(1)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    cat = {
        "source": "lucide-react %s" % version,
        "license": "ISC (kit/assets/LICENSE-lucide.txt)",
        "space": glyphs.SPACE,
        "stroke": glyphs.LUCIDE_STROKE,
        "ops": "M x y | L x y | C x1 y1 x2 y2 x y | Z, in the 24-unit space, y down",
        "aliases": dict(sorted(aliases.items())),
        "glyphs": dict(sorted(out.items())),
    }
    dst = SKILL / "kit" / "assets" / "glyphs.json"
    dst.write_text(json.dumps(cat, separators=(",", ":"), sort_keys=False) + "\n", encoding="utf-8")
    shutil.copyfile(root / "LICENSE", SKILL / "kit" / "assets" / "LICENSE-lucide.txt")
    print("glyphs.json: %d glyphs, %d aliases, %d bytes, from lucide-react %s"
          % (len(out), len(aliases), dst.stat().st_size, version))
    return 0


if __name__ == "__main__":
    sys.exit(main())
