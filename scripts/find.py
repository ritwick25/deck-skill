"""Look up archetypes: the chooser list, one archetype's card, budget, exemplars and greeked contact sheet.

    $PY scripts/find.py                      every family and its archetypes, with the wide budget
    $PY scripts/find.py offering-pillars     one archetype (slug or aNN): card, budget, sheet, exemplar views
    $PY scripts/find.py --search "roadmap phases"   archetypes whose name or definition match the words
    $PY scripts/find.py a38 --real           real renders from the optional library (internal; never shared)

Paths printed are absolute and inside the skill (refs/, the greeked reference pack); Read them. A greeked sheet or
view shows layout, type hierarchy and icons with every word and logo painted out: borrow the structure, never the
words. --real needs the library (DECK_LIBRARY or its default home) and prints UNAVAILABLE without it.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ARCH_JSON, LIB, SKILL, library_ready, pack_sheet, pack_view, real_render  # noqa: E402


def load() -> dict:
    if not ARCH_JSON.is_file():
        sys.exit("archetypes/archetypes.json is missing: run scripts/build_archetypes.py")
    return json.loads(ARCH_JSON.read_text())


def resolve(doc: dict, key: str) -> tuple[str, dict]:
    arch = doc["archetypes"]
    if key in arch:
        return key, arch[key]
    for slug, a in arch.items():
        if a["id"] == key:
            return slug, a
    near = [s for s in arch if key.lower() in s]
    sys.exit("no archetype %r%s" % (key, (": try " + ", ".join(near)) if near else ""))


def _mark(p: Path) -> str:
    return "" if p.is_file() else "  MISSING (run build_archetypes.py --pack)"


def show_one(slug: str, a: dict, real: bool) -> None:
    b = a.get("budget") or {}
    print("%s  %s  (%s, family %s)" % (a["id"], slug, a.get("name"), a.get("family")))
    print("  definition  %s" % a.get("definition"))
    for cv in ("wide", "std"):
        if cv in b:
            x = b[cv]
            print("  budget %-4s %s words (advisory floor %s)%s" % (cv, x["budget"], x.get("floor"),
                                                                   "  derived" if x.get("derived") else ""))
    print("  card        %s" % ((SKILL / a["card"]) if a.get("card") else "none yet: build from the family and the "
                                                                           "design system"))
    dj = SKILL / "devices" / "devices.json"
    if dj.is_file():
        for d in json.loads(dj.read_text())["devices"].values():
            if slug in d["archetypes"]:
                print("  device      %s  %s (%s)  %s" % (d["id"], d["name"], d["variant"],
                                                         SKILL / "devices" / "renders" / ("%s-sigmoid.png" % d["id"])))
    p = pack_sheet(a["id"])
    print("  sheet       %s%s" % (p, _mark(p)))
    for sid in a.get("exemplars") or []:
        p = pack_view(sid)
        print("  exemplar    %s  %s%s" % (sid, p, _mark(p)))
    for sid in a.get("anti") or []:
        p = pack_view(sid)
        print("  anti        %s  %s%s" % (sid, p, _mark(p)))
    if real:
        if not library_ready():
            print("  real        UNAVAILABLE (no library at %s; set DECK_LIBRARY). The greeked views above are the "
                  "skill's own." % LIB)
            return
        for sid in (a.get("exemplars") or []) + (a.get("anti") or []):
            p = real_render(sid)
            print("  real        %s  %s%s" % (sid, p, "" if p.is_file() else "  MISSING"))
        print("  NOTE real renders carry client text and marks: look, never copy words, never share")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("key", nargs="?")
    ap.add_argument("--search")
    ap.add_argument("--real", action="store_true")
    a = ap.parse_args()
    doc = load()
    arch = doc["archetypes"]
    if a.search:
        words = [w.lower() for w in a.search.split()]
        hits = []
        for slug, x in arch.items():
            hay = " ".join(str(v) for v in (slug, x.get("name"), x.get("definition"))).lower()
            n = sum(w in hay for w in words)
            if n:
                hits.append((-n, slug))
        for _, slug in sorted(hits)[:8]:
            x = arch[slug]
            print("%s  %-22s %-26s %s" % (x["id"], slug, x.get("family"), (x.get("definition") or "")[:90]))
        return 0 if hits else 1
    if a.key:
        slug, x = resolve(doc, a.key)
        show_one(slug, x, a.real)
        return 0
    fams: dict[str, list] = {}
    for slug, x in arch.items():
        fams.setdefault(x.get("family") or "?", []).append((x["id"], slug, x))
    for fam in sorted(fams, key=lambda f: min(i for i, _, _ in fams[f])):
        print(fam)
        for aid, slug, x in sorted(fams[fam]):
            w = ((x.get("budget") or {}).get("wide") or {}).get("budget")
            print("  %s  %-24s budget %-4s %s" % (aid, slug, w if w is not None else "-",
                                                  "" if x.get("card") else "(no card)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
