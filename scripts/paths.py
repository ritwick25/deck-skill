"""Where the skill, its reference pack, the optional library and the pinned interpreter live. Every script imports
this; nothing else names a path outside the skill.

The skill is self-contained (ruling 23): cards, budgets, devices, themes, marks and the greeked reference pack
(`refs/`) all live inside it, and every build and lookup reads only those. The library is optional and internal: it
holds the raw reference decks, their real renders and the mining pipeline, and is read only by `find.py --real`,
`build_archetypes.py` (re-publishing cards and the pack) and the device lifter. DECK_LIBRARY overrides its default
home; when it is absent every library-only lookup prints UNAVAILABLE or SKIPPED rather than pretending.
"""
from __future__ import annotations

import os
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
KIT = SKILL / "kit"
PY = "/Library/Frameworks/Python.framework/Versions/3.14/bin/python3"
ARCH_JSON = SKILL / "archetypes" / "archetypes.json"
CANVAS_KEYS = {"w13": "wide", "w10": "std"}          # library canvas ids to kit canvas names

# The in-skill reference pack: greeked contact sheets and exemplar views, built by build_archetypes.py --pack.
REFS = SKILL / "refs"
REFS_CATALOG = REFS / "catalog.json"

# The optional library (re-mining and real renders only). LIB_DEFAULT is the only path outside the skill that
# runtime code may name; selftest.py holds that line.
LIB_DEFAULT = "~/Codes/Decks-For-Visuals/library"
LIB = Path(os.environ.get("DECK_LIBRARY", LIB_DEFAULT)).expanduser()
EXPORT = LIB / "export"


def library_ready() -> bool:
    """True when the library export exists (re-mining, --real renders, pack rebuilds)."""
    return (EXPORT / "catalog.json").is_file()


def pack_sheet(aid: str) -> Path:
    """The greeked contact sheet of archetype aNN inside the skill."""
    return REFS / "sheets" / ("%s.jpg" % aid)


def pack_view(sid: str) -> Path:
    """The greeked view of slide dNN-sNNN inside the skill."""
    return REFS / "views" / ("%s.jpg" % sid)


def real_render(sid: str) -> Path:
    """The real render of slide dNN-sNNN in the library: client text and marks, look and never copy or share."""
    d, s = sid.split("-")
    return LIB / "renders" / d / ("%s.png" % s)
