"""P13 budget: words on glass per slide within the archetype's budget (ceiling 250), counted by deckkit.read.words.

The budget comes from archetypes/archetypes.json for the slide's tagged archetype and the deck's canvas
when the library has published it; a project's deck.json "budgets" ({archetype: words}) wins inside its
folder (the authority ladder: projects keep their own budgets). Everything else, untagged slides included,
is held to the 250-word ceiling. The advisory floor (half the budget, or the published floor) is reported,
never failed.
"""
from __future__ import annotations

import sys

from _shared import ADVISORY, CEILING, FAIL, Finding, cli

GATE, TITLE = "P13", "budget"


def _budget(ctx, archetype):
    proj = (ctx.deck_json.get("budgets") or {}).get(archetype) if archetype else None
    if isinstance(proj, (int, float)):
        return int(proj), None, "deck.json"
    rec = ctx.archetypes.get(archetype) if archetype else None
    b = (rec or {}).get("budget") or {}
    b = b.get(ctx.canvas.name, b) if isinstance(b, dict) else b
    if isinstance(b, dict) and isinstance(b.get("budget"), (int, float)):
        return min(CEILING, int(b["budget"])), b.get("floor"), "archetypes.json"
    if isinstance(b, (int, float)):
        return min(CEILING, int(b)), None, "archetypes.json"
    return CEILING, None, "ceiling"


def run(deck, ctx):
    out = []
    for i in range(1, ctx.n + 1):
        t = ctx.tags()[i - 1]
        n = ctx.slide(i)["text"]["words_content"]
        budget, floor, src = _budget(ctx, t["archetype"])
        if n > budget:
            out.append(Finding(GATE, FAIL, i, t["tag"] or "untagged", "%d words on glass, budget %d (%s)" % (n, budget, src)))
        elif floor and n < floor and not ctx.is_frame(i):
            out.append(Finding(GATE, ADVISORY, i, t["tag"], "%d words, under the advisory floor %d" % (n, floor)))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
