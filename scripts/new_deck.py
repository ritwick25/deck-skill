"""Scaffold a deck project in any folder: deck.json (the build command the gates rebuild) and build.py.

    $PY scripts/new_deck.py FOLDER --name "Deck name" [--theme sigmoid|neutral|path.json]

build.py starts as a copy of scripts/example_build.py pointed at the skill's kit, writing FOLDER/<name>.pptx;
replace its two slide functions with the storyline's slides. The scaffold is wide (13.333 x 7.5); extending a
10-inch deck means importing STD and base-std.pptx by hand and re-deriving the geometry. Refuses to overwrite an existing build.py or
deck.json. The pptx and its manifest are written only by build.py, never by hand.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import SKILL  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--name", required=True)
    ap.add_argument("--theme", default="sigmoid")
    a = ap.parse_args()
    folder = Path(a.folder).expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)
    theme = Path(a.theme).expanduser().resolve() if a.theme.endswith(".json") else SKILL / "themes" / (a.theme + ".json")
    if not theme.is_file():
        sys.exit("no theme %s" % theme)
    for f in ("build.py", "deck.json"):
        if (folder / f).exists():
            sys.exit("%s exists: refusing to overwrite" % (folder / f))
    stem = re.sub(r"[^\w .-]", "", a.name).strip() or "deck"
    out = folder / (stem + ".pptx")
    src = (SKILL / "scripts" / "example_build.py").read_text()
    src = src.replace('SKILL = Path(__file__).resolve().parent.parent',
                      'SKILL = Path("~/.claude/skills/deck").expanduser()')
    src = src.replace('default=str(SKILL / ".cache" / "example" / "example.pptx")', 'default=%r' % str(out))
    src = src.replace('default=str(SKILL / "themes" / "sigmoid.json")', 'default=%r' % str(theme))
    src = src.replace('title="Example deck"', 'title=%r' % a.name)
    (folder / "build.py").write_text(src)
    (folder / "deck.json").write_text(json.dumps({
        "type": "deck", "canvas": "wide", "theme": str(theme), "client": None, "spelling": "US", "overrides": {},
        "budgets": {}, "series": [], "deliverable": out.name,
        "build": ["{python}", str(folder / "build.py"), "--out", "{out}"]}, indent=2) + "\n")
    print("OK %s\n   %s\n   %s" % (folder, folder / "build.py", folder / "deck.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
