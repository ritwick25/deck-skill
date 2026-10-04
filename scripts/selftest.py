"""The skill's own invariants. Exit 1 on any failure.

    $PY scripts/selftest.py

  * SKILL.md frontmatter: name deck, a description of 1024 characters or fewer, no angle brackets
  * every archetype in archetypes.json has a family, a wide budget at or under 250, a card file and 2+ exemplars
  * every slug the chooser in SKILL names exists in archetypes.json, and every archetype is in the chooser
  * archetypes.json is not stale against the library export (build_archetypes --check), when the library exists
  * no denylisted name (the library's leak list, every term and every alias) in any skill text file, tests and caches
    excepted; the scan refuses to run on a missing or short list, or when the alias canary does not fire
  * every reference file SKILL names exists
  * the reference pack (ruling 23): every sheet, exemplar view and anti view archetypes.json lists is in refs/, every
    pack file matches its sha256 in refs/catalog.json, no stray file sits beside them, and every image a card cites
    resolves inside the skill
  * ruling 12: no card's light-bg translation row turns a panel or band pastel (a light surface, row, strip or panel,
    a pale or tint panel); only the slide ground goes light
  * self-contained: no runtime code names a path under ~/Codes except paths.LIB_DEFAULT, which DECISIONS.md documents;
    archetypes.json carries no absolute path
  * portability: kit/assets/fingerprints.json, the copy a machine without the hook file reads, is byte-identical to
    ~/.claude/hooks/fingerprints.json wherever that file exists, so the banned list keeps one home
  * ruling 24: showcase/ holds the showcase deck, its index and one sheet per four slides, the deck matches the sha256
    the index records, and, when the library is present, the copy matches the library's build
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_archetypes import denylist  # noqa: E402
from paths import ARCH_JSON, LIB_DEFAULT, PY, REFS, REFS_CATALOG, SKILL, library_ready, pack_sheet, pack_view  # noqa: E402


OUTSIDE = re.compile(r"/Users/[^/\s\"']+/Codes\b|~/Codes\b|[\"']Codes[\"']")
CITED = re.compile(r"\b(refs/(?:views|sheets)/[\w-]+\.jpg|greeked/d\d{2}/s\d{3}\.png|export/sheets/a\d{2}\.png)")
# Code that names a folder outside the skill and is never run by a build, a gate run or a lookup. Each entry names
# what it is exempt for.
MAINTENANCE = {
    "scripts/build_glyphs.py": "regenerates kit/assets/glyphs.json from a local lucide-react checkout",
    "scripts/lift_device.py": "lifts a device from the library's source decks (re-mining)",
    "gates/characterise.py": "characteriser over the library's real renders; never part of run_all",
    "scripts/selftest.py": "holds the detector pattern and the documented library home it checks against",
}


# Ruling 12, held on the card text a builder follows: the light-bg row's house and consequence cells may say the
# ground goes light, never that a band or panel becomes a light or pastel surface. "Never ... tint" phrasing is allowed.
PASTEL_PANEL = re.compile(r"\b(?:light|pale|tint(?:ed)?)\s+(?:brand\s+tint\s+)?(?:surface|row|strip|panel|band|card|"
                          r"gr[ae]y\s+band)s?\b|\b(?:light|pale)\s+tint\b|\bbrand[- ]tint\b|\bflat\s+light\b", re.I)


def pastel_rows() -> list[str]:
    fails: list[str] = []
    for card in sorted((SKILL / "archetypes").glob("*.md")):
        for n, line in enumerate(card.read_text().splitlines(), 1):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == 4 and cells[0] == "light-bg":
                for cell in cells[2:]:
                    for m in PASTEL_PANEL.finditer(cell):
                        if not re.search(r"\b(?:never|not|no)\b[^.]*$", cell[:m.start()], re.I):
                            fails.append("%s:%d light-bg row turns a panel pastel (%r), against ruling 12"
                                         % (card.name, n, m.group(0)))
    return fails


def pack_failures(arch: dict) -> list[str]:
    """Ruling 23: the pack holds every image the archetypes list, untouched, and nothing else."""
    fails: list[str] = []
    if not REFS_CATALOG.is_file():
        return ["refs/catalog.json is missing: run scripts/build_archetypes.py --pack"]
    cat = json.loads(REFS_CATALOG.read_text())
    files = cat.get("files") or {}
    for slug, a in arch.items():
        want = [pack_sheet(a["id"])] + [pack_view(x) for x in (a.get("exemplars") or []) + (a.get("anti") or [])]
        for pth in want:
            if not pth.is_file():
                fails.append("%s: %s is not in the pack" % (slug, pth.relative_to(SKILL)))
        if a.get("sheet") != str(pack_sheet(a["id"]).relative_to(SKILL)):
            fails.append("%s: archetypes.json sheet %r is not the pack path" % (slug, a.get("sheet")))
    for rel, f in sorted(files.items()):
        pth = SKILL / rel
        if not pth.is_file():
            fails.append("refs/catalog.json lists %s, which is missing" % rel)
        elif hashlib.sha256(pth.read_bytes()).hexdigest() != f.get("sha256"):
            fails.append("%s differs from its catalog sha256" % rel)
    for d in ("sheets", "views"):
        for pth in sorted((REFS / d).glob("*")):
            if str(pth.relative_to(SKILL)) not in files:
                fails.append("%s is not in refs/catalog.json" % pth.relative_to(SKILL))
    for card in sorted((SKILL / "archetypes").glob("*.md")):
        for cite in sorted(set(CITED.findall(card.read_text()))):
            if not cite.startswith("refs/"):
                fails.append("%s cites %s, a library path" % (card.name, cite))
            elif not (SKILL / cite).is_file():
                fails.append("%s cites %s, which is not in the pack" % (card.name, cite))
    return fails


def outside_paths() -> list[str]:
    """Runtime code names no folder under ~/Codes; the one allowed line is paths.LIB_DEFAULT."""
    fails: list[str] = []
    if not LIB_DEFAULT.startswith("~/Codes/Decks-For-Visuals/") or "~/Codes/Decks-For-Visuals/" not in (
            SKILL / "DECISIONS.md").read_text():
        fails.append("paths.LIB_DEFAULT %s is not the library home DECISIONS.md documents" % LIB_DEFAULT)
    for pth in sorted(list((SKILL / "kit").rglob("*.py")) + list((SKILL / "gates").rglob("*.py"))
                      + list((SKILL / "scripts").glob("*.py"))):
        rel = str(pth.relative_to(SKILL))
        if rel in MAINTENANCE or "__pycache__" in rel:
            continue
        for n, line in enumerate(pth.read_text(errors="ignore").splitlines(), 1):
            if OUTSIDE.search(line) and not (rel == "scripts/paths.py" and line.startswith("LIB_DEFAULT = ")):
                fails.append("%s:%d names a path outside the skill" % (rel, n))
    if re.search(r"/Users/|~/", ARCH_JSON.read_text()):
        fails.append("archetypes.json carries an absolute path")
    return fails


def main() -> int:
    fails: list[str] = []
    sk = SKILL / "SKILL.md"
    text = sk.read_text()
    fm = text.split("---")[1] if text.startswith("---") else ""
    name = re.search(r"^name:\s*(\S+)", fm, re.M)
    desc = re.search(r"^description:\s*(.+)$", fm, re.M)
    if not name or name.group(1) != "deck":
        fails.append("frontmatter name is not deck")
    if not desc or len(desc.group(1)) > 1024 or "<" in desc.group(1) or ">" in desc.group(1):
        fails.append("description missing, over 1024 characters, or carries an angle bracket")
    arch = json.loads(ARCH_JSON.read_text())["archetypes"]
    for slug, a in arch.items():
        b = ((a.get("budget") or {}).get("wide") or {}).get("budget")
        if not a.get("family"):
            fails.append("%s: no family" % slug)
        if not isinstance(b, int) or b > 250:
            fails.append("%s: wide budget %r" % (slug, b))
        if not a.get("card") or not (SKILL / a["card"]).is_file():
            fails.append("%s: no card file" % slug)
        if len(a.get("exemplars") or []) < 2:
            fails.append("%s: fewer than 2 exemplars" % slug)
    chooser = set(re.findall(r"^\|[^|]*\| `([a-z-]+)` \|", text, re.M))
    for s in sorted(chooser - set(arch)):
        fails.append("chooser names %s, which is not an archetype" % s)
    for s in sorted(set(arch) - chooser):
        fails.append("archetype %s is missing from the chooser" % s)
    fails += pack_failures(arch)
    import sync_showcase
    fails += sync_showcase.check()
    home_fp = Path("~/.claude/hooks/fingerprints.json").expanduser()
    bundled_fp = SKILL / "kit" / "assets" / "fingerprints.json"
    if not bundled_fp.is_file():
        fails.append("kit/assets/fingerprints.json is missing: a machine without the hook file has no banned list")
    elif home_fp.is_file() and home_fp.read_bytes() != bundled_fp.read_bytes():
        fails.append("kit/assets/fingerprints.json differs from ~/.claude/hooks/fingerprints.json: copy the hook file "
                     "over it")
    fails += pastel_rows()
    fails += outside_paths()
    for ref in set(re.findall(r"`(references/[a-z-]+\.md)`", text)):
        if not (SKILL / ref).is_file():
            fails.append("SKILL names %s, which does not exist" % ref)
    if library_ready():
        r = subprocess.run([PY, str(SKILL / "scripts" / "build_archetypes.py"), "--check"], capture_output=True, text=True)
        if r.returncode:
            fails.append("archetypes stale or leaking: " + " ".join(r.stdout.split()[:12]))
        try:
            pats = denylist()           # every term and alias; raises rather than scan with nothing
        except RuntimeError as e:
            pats = []
            fails.append("name scan cannot run: %s" % e)
        for p in sorted(SKILL.rglob("*")):
            rel = p.relative_to(SKILL)
            if not p.is_file() or p.suffix not in (".md", ".py", ".json") or rel.parts[0] in (".cache", "tests", ".git"):
                continue
            if rel.parts[0] == "devices" or rel.name in ("vendor_hashes.json", "glyphs.json"):
                continue
            body = p.read_text(errors="ignore")
            hit = next((m for rx in pats for m in [rx.search(body)] if m), None)
            if hit:
                # the line, never the term: this output is read in sessions the leak list must stay out of
                fails.append("%s:%d carries a denylisted term" % (rel, body.count("\n", 0, hit.start()) + 1))
    else:
        print("SKIPPED library checks (no library export)")
    for f in fails:
        print("FAIL", f)
    print("%s selftest: %d failure(s)" % ("OK" if not fails else "FAILED", len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
