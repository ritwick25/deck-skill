"""Publish the library's export into the skill: archetypes/archetypes.json, archetypes/<slug>.md, references/.

    $PY scripts/build_archetypes.py [--check]

Reads LIB/export/catalog.json, export/cards/<aNN>.md, export/design-system.md and export/storylines.md (the
scrubbed, leak-gated layer; nothing else in the library is read except leak/denylist.json, to re-check the copy).
archetypes.json is what gates P10, P13 and P15 read: family by name, budgets per kit canvas (wide, std), the
exemplar ids and the greeked sheet path. The wide budget is the library's @norm measure, the one every card cites;
a std budget is the w10 measure when two or more compact exemplars exist, else the wide budget scaled by the canvas
area ratio and marked "derived". Advisory floors never exceed half their budget. --check rebuilds in
memory and exits 1 if the published files differ (stale) or any copied text carries a denylisted term.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ARCH_JSON, EXPORT, LIB, SKILL  # noqa: E402

AREA_STD = (10 * 5.625) / (13.333 * 7.5)
CEILING = 250


def _budget(b: dict | None) -> dict | None:
    """The measured budget, capped at the ceiling; the advisory floor never above half the budget (a floor near a
    capped budget would push copy to the ceiling, the opposite of cut-to-the-device)."""
    if not isinstance(b, dict) or not isinstance(b.get("budget"), (int, float)):
        return None
    budget = min(CEILING, int(b["budget"]))
    floor = b.get("floor")
    half = int(math.floor(budget / 2 / 10.0) * 10)
    if isinstance(floor, (int, float)) and floor > half:
        floor = half
    return {"budget": budget, "floor": floor, "n": b.get("n"), "p25": b.get("p25"), "p75": b.get("p75")}


def budgets(src: dict) -> dict:
    wide = _budget(src.get("norm")) or _budget(src.get("w13"))          # the cards cite @norm
    out = {}
    if wide:
        out["wide"] = wide
    std = _budget(src.get("w10"))
    if std and (std.get("n") or 0) >= 2:
        out["std"] = std
    elif wide:
        b = int(math.ceil(wide["budget"] * AREA_STD / 10.0) * 10)
        out["std"] = {"budget": b, "floor": int(math.floor(b / 2 / 10.0) * 10), "derived": "wide x area ratio"}
    return out


def denylist() -> list[re.Pattern]:
    p = LIB / "leak" / "denylist.json"
    if not p.is_file():
        return []
    d = json.loads(p.read_text())
    terms = d["terms"] if isinstance(d, dict) and "terms" in d else d
    return [re.compile(r"\b%s\b" % re.escape(t if isinstance(t, str) else t.get("term", "")), re.I)
            for t in terms if (t if isinstance(t, str) else t.get("term"))]


def build() -> dict[Path, str]:
    cat = json.loads((EXPORT / "catalog.json").read_text())
    fams = cat.get("families") or {}
    files: dict[Path, str] = {}
    arch = {}
    for aid, a in sorted(cat["archetypes"].items()):
        slug = a["slug"]
        card_src = EXPORT / "cards" / ("%s.md" % aid)
        card_rel = "archetypes/%s.md" % slug if card_src.is_file() else None
        if card_rel:
            files[SKILL / card_rel] = card_src.read_text()
        arch[slug] = {"id": aid, "name": a.get("name"), "family": a.get("family_name") or (fams.get(a["family"]) or
                      {}).get("name"), "family_id": a.get("family"), "definition": a.get("definition"),
                      "budget": budgets(a.get("budgets") or {}), "exemplars": a.get("exemplars") or [],
                      "anti": a.get("anti") or [], "sheet": a.get("sheet"), "card": card_rel,
                      "members": (a.get("stats") or {}).get("members")}
    doc = {"about": "Published from the deck library export by scripts/build_archetypes.py. Read by gates P10, P13, "
                    "P15 and by scripts/find.py. Families are visual; budgets are words on glass per kit canvas.",
           "taxonomy": cat.get("taxonomy") or cat.get("taxonomy_version"), "library": str(LIB),
           "families": {f: v.get("name") for f, v in sorted(fams.items())}, "archetypes": arch}
    files[ARCH_JSON] = json.dumps(doc, indent=1, sort_keys=False) + "\n"
    devs = cat.get("devices") or {}
    if devs:
        lines = ["# Device registry", "", "The visual mechanisms the archetype cards cite as `dvNN` (taxonomy %s). A device is how a "
                 "slide argues: the archetype is the job, the device is the drawing." % ((doc["taxonomy"] or {}).get("version") if isinstance(doc["taxonomy"], dict) else doc["taxonomy"]), "",
                 "| Id | Device | Mechanism |", "|---|---|---|"]
        lines += ["| %s | %s | %s |" % (k, v.get("name"), (v.get("mechanism") or "").replace("|", "/"))
                  for k, v in sorted(devs.items())]
        files[SKILL / "references" / "devices.md"] = "\n".join(lines) + "\n"
    for name in ("design-system.md", "storylines.md"):
        src = EXPORT / name
        if src.is_file():
            files[SKILL / "references" / name] = src.read_text()
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not (EXPORT / "catalog.json").is_file():
        print("SKIPPED no library export at %s (run library/tools/export.py)" % EXPORT)
        return 0 if a.check else 1
    files = build()
    bad = []
    pats = denylist()
    for p, text in files.items():
        for rx in pats:
            if rx.search(text):
                bad.append("%s: a denylisted term (%s)" % (p.relative_to(SKILL), rx.pattern[:2] + "..."))
                break
    stale = [p for p, t in files.items() if not p.is_file() or p.read_text() != t]
    if a.check:
        for b in bad:
            print("FAIL", b)
        for p in stale:
            print("STALE", p.relative_to(SKILL))
        return 1 if bad or stale else 0
    if bad:
        for b in bad:
            print("FAIL", b)
        return 1
    for p, t in files.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(t)
    n_cards = sum(1 for p in files if p.parent.name == "archetypes" and p.suffix == ".md")
    print("OK %d archetypes, %d cards, %d references" % (len(json.loads(files[ARCH_JSON])["archetypes"]), n_cards,
                                                       sum(1 for p in files if p.parent.name == "references")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
