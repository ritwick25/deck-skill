"""Scaffold a deck project in any folder: deck.json (the build command the gates rebuild), build.py and CLAUDE.md.

    $PY scripts/new_deck.py FOLDER --name "Deck name" [--theme sigmoid|neutral|path/to/theme.json] [--client NAME]

build.py starts as a copy of scripts/example_build.py pointed at the skill's kit, writing FOLDER/<name>.pptx;
replace its two slide functions with the storyline's slides. --theme takes a house theme name or a client
theme.json from scripts/brand.py; the theme must load, and a client theme's brand block (client, logo) is recorded
in deck.json. CLAUDE.md tells a later session in this folder to load /deck before any change, how to build, gate
and render, and which theme is in use, so the skill governs every iteration (ruling 23).

The scaffold is wide (13.333 x 7.5); extending a 10-inch deck means importing STD and base-std.pptx by hand and
re-deriving the geometry. Refuses to overwrite an existing build.py, deck.json or CLAUDE.md. The pptx and its
manifest are written only by build.py, never by hand.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import KIT, PY, SKILL  # noqa: E402

HOUSE = ("sigmoid", "neutral")


def resolve_theme(arg: str) -> Path:
    if arg.endswith(".json"):
        return Path(arg).expanduser().resolve()
    return SKILL / "themes" / (arg + ".json")


def load_theme(path: Path) -> dict:
    """The theme as data, after the kit has loaded it (a theme the kit refuses is refused here)."""
    sys.path.insert(0, str(KIT))
    from deckkit.theme import Theme
    Theme.load(path)
    return json.loads(path.read_text(encoding="utf-8"))


def claude_md(name: str, out: Path, theme: Path, data: dict) -> str:
    """The folder's CLAUDE.md: about a dozen lines, latest state only."""
    brand = data.get("brand") or {}
    if brand:
        logo = (brand.get("logo") or {}).get("file")
        kind = "client theme for %s%s" % (brand.get("client") or "the client",
                                          ", logo %s" % (theme.parent / logo) if logo else ", no logo on file")
    elif theme.parent == SKILL / "themes":
        kind = "house theme %s" % theme.stem
    else:
        kind = "project theme"
    k = "~/.claude/skills/deck"
    return "\n".join([
        "# %s" % name,
        "",
        "Built with the deck skill. Load `/deck` before any change, one slide or one word, and route every later",
        "iteration in the session through it.",
        "",
        "- Source of truth: `build.py`. Never hand-edit `%s`; change `build.py` and rebuild." % out.name,
        "- Interpreter: `PY=%s`" % PY,
        "- Build: `$PY build.py`",
        "- Gates: `$PY %s/gates/run_all.py --deck \"%s\"` must exit 0; fix the slide, never the gate." % (k, out.name),
        "- Render, then read every slide: `$PY %s/scripts/render.py \"%s\"`" % (k, out.name),
        "- Theme: `%s` (%s). A client cut is a theme swap, never a layout change." % (theme, kind),
        "- Rulings and numbers: `DECISIONS.md` and `CANON.md` here when present; the newest ruling wins.",
        "",
    ])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--name", required=True)
    ap.add_argument("--theme", default="sigmoid", help="sigmoid, neutral, or a client theme.json from brand.py")
    ap.add_argument("--client", help="the client this deck is for, when the theme does not name one")
    a = ap.parse_args()
    folder = Path(a.folder).expanduser().resolve()
    theme = resolve_theme(a.theme)
    if not theme.is_file():
        sys.exit("no theme %s" % theme)
    try:
        data = load_theme(theme)
    except Exception as e:  # noqa: BLE001 - any refusal from the kit is reported as is
        sys.exit("theme %s does not load: %s" % (theme, e))
    for f in ("build.py", "deck.json", "CLAUDE.md"):
        if (folder / f).exists():
            sys.exit("%s exists: refusing to overwrite" % (folder / f))
    folder.mkdir(parents=True, exist_ok=True)
    client = a.client or (data.get("brand") or {}).get("client")
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
        "type": "deck", "canvas": "wide", "theme": str(theme), "client": client, "spelling": "US", "overrides": {},
        "budgets": {}, "series": [], "deliverable": out.name,
        "build": ["{python}", str(folder / "build.py"), "--out", "{out}"]}, indent=2) + "\n")
    (folder / "CLAUDE.md").write_text(claude_md(a.name, out, theme, data))
    print("OK %s\n   %s\n   %s\n   %s" % (folder, folder / "build.py", folder / "deck.json", folder / "CLAUDE.md"))
    if client and theme.stem in HOUSE and theme.parent == SKILL / "themes":
        print("NOTE %s is a client deck on the house theme %s. Unless the user chose the house theme, ask for the "
              "brand colours, logo and font and run scripts/brand.py, then rescaffold with --theme." % (client, theme.stem))
    return 0


if __name__ == "__main__":
    sys.exit(main())
