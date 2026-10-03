"""The skill's own invariants. Exit 1 on any failure.

    $PY scripts/selftest.py

  * SKILL.md (or SKILL.draft.md) frontmatter: name deck, a description of 1024 characters or fewer, no angle brackets
  * every archetype in archetypes.json has a family, a wide budget at or under 250, a card file and 2+ exemplars
  * every slug the chooser in SKILL names exists in archetypes.json, and every archetype is in the chooser
  * archetypes.json is not stale against the library export (build_archetypes --check), when the library exists
  * no denylisted name (the library's leak list) in any skill text file, tests and caches excepted
  * every reference file SKILL names exists
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_archetypes import denylist  # noqa: E402
from paths import ARCH_JSON, PY, SKILL, library_ready  # noqa: E402


def main() -> int:
    fails: list[str] = []
    sk = SKILL / "SKILL.md"
    sk = sk if sk.is_file() else SKILL / "SKILL.draft.md"
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
    for ref in set(re.findall(r"`(references/[a-z-]+\.md)`", text)):
        if not (SKILL / ref).is_file():
            fails.append("SKILL names %s, which does not exist" % ref)
    if library_ready():
        r = subprocess.run([PY, str(SKILL / "scripts" / "build_archetypes.py"), "--check"], capture_output=True, text=True)
        if r.returncode:
            fails.append("archetypes stale or leaking: " + " ".join(r.stdout.split()[:12]))
        pats = denylist()
        for p in sorted(SKILL.rglob("*")):
            rel = p.relative_to(SKILL)
            if not p.is_file() or p.suffix not in (".md", ".py", ".json") or rel.parts[0] in (".cache", "tests", ".git"):
                continue
            if rel.parts[0] == "devices" or rel.name in ("vendor_hashes.json", "glyphs.json"):
                continue
            body = p.read_text(errors="ignore")
            hit = next((rx for rx in pats if rx.search(body)), None)
            if hit:
                fails.append("%s carries a denylisted term" % rel)
    else:
        print("SKIPPED library checks (no library export)")
    for f in fails:
        print("FAIL", f)
    print("%s selftest: %d failure(s)" % ("OK" if not fails else "FAILED", len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
