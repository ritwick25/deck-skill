"""deckkit.read: the shared OOXML read layer.

One implementation of geometry, colour, type inheritance and word counting, imported by the library's
corpus extractor and by the skill's gates. Sources are opened read-only.
"""
from __future__ import annotations

from .deckinfo import deck_info
from .opc import DeckRead
from .textmetrics import para_text, words
from .walk import read_slide


def open_deck(path: str) -> DeckRead:
    """Open a .pptx read-only. Use as a context manager or call .close()."""
    return DeckRead(path)


__all__ = ["DeckRead", "open_deck", "read_slide", "deck_info", "words", "para_text"]
