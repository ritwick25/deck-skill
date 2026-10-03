"""Where the skill, the library and the pinned interpreter live. Every script imports this, nothing hardcodes.

The library (renders, records, measures, greeked sheets) is internal and optional: DECK_LIBRARY overrides
its default home. When it is absent the skill still works from its own cards and gates, and every lookup
that needs it prints SKIPPED rather than pretending.
"""
from __future__ import annotations

import os
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
KIT = SKILL / "kit"
PY = "/Library/Frameworks/Python.framework/Versions/3.14/bin/python3"
LIB = Path(os.environ.get("DECK_LIBRARY", "~/Codes/Decks-For-Visuals/library")).expanduser()
EXPORT = LIB / "export"
ARCH_JSON = SKILL / "archetypes" / "archetypes.json"
CANVAS_KEYS = {"w13": "wide", "w10": "std"}          # library canvas ids to kit canvas names


def library_ready() -> bool:
    return (EXPORT / "catalog.json").is_file()
