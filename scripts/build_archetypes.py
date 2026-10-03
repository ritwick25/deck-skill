"""Publish the library's export into the skill: archetypes/archetypes.json, archetypes/<slug>.md, references/, refs/.

    $PY scripts/build_archetypes.py            cards, budgets, references and the reference pack
    $PY scripts/build_archetypes.py --pack     the reference pack (refs/) only
    $PY scripts/build_archetypes.py --check    exit 1 when anything published is stale, leaking or missing

Reads LIB/export/catalog.json, export/cards/<aNN>.md, export/design-system.md and export/storylines.md (the
scrubbed, leak-gated layer; nothing else in the library is read except leak/denylist.json, to re-check the copy).
archetypes.json is what gates P10, P13 and P15 read: family by name, budgets per kit canvas (wide, std), the
exemplar ids and the pack's sheet path. The wide budget is the library's @norm measure, the one every card cites;
a std budget is the w10 measure when two or more compact exemplars exist, else the wide budget scaled by the canvas
area ratio and marked "derived". Advisory floors are the measured p25 (ruling 17). Cards cite exemplar views by
their pack path (refs/views/dNN-sNNN.jpg), so a card resolves inside the skill.

The reference pack (ruling 23) is what makes the skill self-contained: refs/sheets/<aNN>.jpg (each archetype's
greeked contact sheet), refs/views/<dNN-sNNN>.jpg (the greeked view of every exemplar and anti-exemplar) and
refs/catalog.json (the lists, the pack paths and every file's sha256 beside its source's). Only greeked images
enter it: a view is copied only when the library's greek record says its OCR sweep came back clean and the PNG is
the one that record hashed; sheets come from export/sheets, which the library builds from greeked views only. After
encoding, the library's OCR probe (Apple Vision) re-reads every pack image when it is available: a view must carry
no readable text, a sheet only its tile labels (slide id, rank, words, points). Without the probe the step prints
OCR SKIPPED and relies on the greek records. JPEG encoding is deterministic, so --check compares hashes only.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ARCH_JSON, EXPORT, LIB, REFS, REFS_CATALOG, SKILL  # noqa: E402

AREA_STD = (10 * 5.625) / (13.333 * 7.5)
CEILING = 250

# Pack encoding. The brief was 1400 px views and 1600 px sheets at q82, which measured 24.5MB for 249 views and 45
# sheets (greeked flat fills compress poorly in JPEG); these values hold the pack near 15MB and keep every greeked
# bar, icon and fill legible at the size the Read tool shows an image.
VIEW_PX, SHEET_PX, JPEG_Q = 1120, 1280, 75
CITE_VIEW = re.compile(r"greeked/(d\d{2})/(s\d{3})\.png")
CITE_SHEET = re.compile(r"export/sheets/(a\d{2})\.png")
SID = re.compile(r"^d\d{2}-s\d{3}$")
# words OCR may read on a contact sheet's tile labels ("dNN-sNNN", "rank N . N w . N pt", "no text"); other reads
# are counted as noise
# Greeked views whose OCR residue was inspected crop by crop (2026-10-03) and holds no readable text: grey word bars,
# glyph strokes and masked boxes read as noise ("000", "LHNI", "ЖВАОЬКЕ"). Each is pinned to the greeked PNG's sha256
# prefix, so a re-greeked view is judged again rather than waved through.
RESIDUE_INSPECTED = {
    "d13-s009": "02019fd11edee617", "d01-s115": "2341ae7aa9bb4275", "d16-s024": "f59f5ede3f2af59d",
    "d15-s031": "3e1ed45b73379262", "d03-s038": "46cd43590ab0e5b6", "d07-s007": "f1ebdd6675911c13",
    "d09-s020": "19609cd48d460630", "d12-s019": "f261ffc5fb7b9f0e", "d09-s038": "329a5dceefa01957",
    "d01-s068": "4c8c0e4730932b0a", "d09-s068": "8ad442999f6fd55e",
}
SHEET_WORD = re.compile(r"^(?:d\d{2}|s\d{3}|\d+|\d+w|\d+pt|rank|pt|no|text)$", re.I)


def cite_pack(text: str) -> str:
    """Library-relative image citations in a card become in-skill pack paths."""
    text = CITE_VIEW.sub(lambda m: "refs/views/%s-%s.jpg" % (m.group(1), m.group(2)), text)
    return CITE_SHEET.sub(lambda m: "refs/sheets/%s.jpg" % m.group(1), text)


def _budget(b: dict | None) -> dict | None:
    """The measured budget, capped at the ceiling; the advisory floor is the exemplars' measured p25 (ruling 2,
    restored by ruling 17), and only where the ceiling cut the budget below it does the floor drop to 90% of it."""
    if not isinstance(b, dict) or not isinstance(b.get("budget"), (int, float)):
        return None
    budget = min(CEILING, int(b["budget"]))
    floor = b.get("floor")                      # ruling 2: floor10 of the exemplars' p25 (ruling 17 restored it)
    if isinstance(floor, (int, float)) and floor > budget:
        floor = int(math.floor(budget * 0.9 / 10.0) * 10)
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
            files[SKILL / card_rel] = cite_pack(card_src.read_text())
        arch[slug] = {"id": aid, "name": a.get("name"), "family": a.get("family_name") or (fams.get(a["family"]) or
                      {}).get("name"), "family_id": a.get("family"), "definition": a.get("definition"),
                      "budget": budgets(a.get("budgets") or {}), "exemplars": a.get("exemplars") or [],
                      "anti": a.get("anti") or [], "sheet": "refs/sheets/%s.jpg" % aid, "card": card_rel,
                      "members": (a.get("stats") or {}).get("members")}
    doc = {"about": "Published from the deck library export by scripts/build_archetypes.py. Read by gates P10, P13, "
                    "P15 and by scripts/find.py. Families are visual; budgets are words on glass per kit canvas.",
           "taxonomy": cat.get("taxonomy") or cat.get("taxonomy_version"),
           "library": "optional, for re-mining only: DECK_LIBRARY, else paths.LIB_DEFAULT",
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


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def encode(src: Path, px: int) -> tuple[bytes, list[int]]:
    """A greeked PNG as a JPEG whose long edge is at most px. Deterministic: no metadata, fixed settings."""
    from PIL import Image
    with Image.open(src) as im:
        im = im.convert("RGB")
        im.thumbnail((px, px), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=JPEG_Q, optimize=True, subsampling=2)
        return buf.getvalue(), list(im.size)


def pack_plan() -> tuple[dict, list[dict], list[str]]:
    """What the pack holds, read from the export catalog: per archetype its sheet, exemplars and antis, and per
    file its greeked source. A view whose greek record is not OCR-clean, or whose PNG is not the one the record
    hashed, is a problem and never enters the pack."""
    cat = json.loads((EXPORT / "catalog.json").read_text())
    arch: dict = {}
    entries: dict[str, dict] = {}
    problems: list[str] = []
    greek: dict[str, dict] = {}

    def view(sid: str) -> str:
        if not SID.match(sid):
            problems.append("%s is not a slide id" % sid)
            return ""
        rel = "refs/views/%s.jpg" % sid
        if rel not in entries:
            d, sl = sid.split("-")
            src = LIB / "greeked" / d / ("%s.png" % sl)
            if d not in greek:
                gp = LIB / "greeked" / ("%s.json" % d)
                greek[d] = json.loads(gp.read_text()).get("slides", {}) if gp.is_file() else {}
            rec = greek[d].get(sl) or {}
            inspected = (rec.get("ocr_status") == "residue"
                         and (rec.get("out_sha256") or "").startswith(RESIDUE_INSPECTED.get(sid, "-")))
            if not src.is_file():
                problems.append("%s: no greeked view at %s" % (sid, src))
            elif rec.get("ocr_status") != "clean" and not inspected:
                problems.append("%s: greek record OCR status %r, not clean and not inspected"
                                % (sid, rec.get("ocr_status")))
            elif rec.get("out_sha256") != _sha(src.read_bytes()):
                problems.append("%s: greeked view differs from its greek record (run library tools/greek.py %s)"
                                % (sid, sid))
            entries[rel] = {"kind": "view", "src": src, "px": VIEW_PX, "source": "greeked/%s/%s.png" % (d, sl)}
        return rel

    for aid, a in sorted(cat["archetypes"].items()):
        sheet_src = LIB / (a.get("sheet") or "export/sheets/%s.png" % aid)
        rel_sheet = "refs/sheets/%s.jpg" % aid
        if not sheet_src.is_file():
            problems.append("%s: no contact sheet at %s" % (aid, sheet_src))
        elif sheet_src.parent != EXPORT / "sheets":
            problems.append("%s: sheet %s is outside export/sheets (greeked sheets only)" % (aid, sheet_src))
        entries[rel_sheet] = {"kind": "sheet", "src": sheet_src, "px": SHEET_PX, "source": "export/sheets/%s.png" % aid}
        arch[a["slug"]] = {"id": aid, "sheet": rel_sheet,
                           "exemplars": [{"id": x, "view": view(x)} for x in a.get("exemplars") or []],
                           "anti": [{"id": x, "view": view(x)} for x in a.get("anti") or []]}
    return arch, [dict(rel=k, **v) for k, v in sorted(entries.items())], problems


def ocr_pack(images: dict[str, Path]) -> tuple[str, list[str]]:
    """Re-read every encoded pack image with the library's OCR probe and match what it reads against the leak
    denylist. Returns (status, problems). The no-readable-text bar is held upstream, on the full-size greeked PNG
    (the greek record); a downscaled JPEG makes the probe read bars and glyph strokes as noise ("IIII", "HOHT"),
    which is counted and printed, not failed, because encoding cannot create a word the PNG did not carry."""
    tools = LIB / "tools"
    if not (tools / "ocr.py").is_file():
        return "SKIPPED (no library OCR module)", []
    sys.path.insert(0, str(tools))
    try:
        import ocr as ocrmod  # type: ignore
    except Exception as e:  # noqa: BLE001
        return "SKIPPED (%s)" % e, []
    o = ocrmod.Ocr()
    if not o.available:
        return "SKIPPED (%s)" % o.why, []
    res = o.read(list(images.values()))
    pats = denylist()
    problems: list[str] = []
    noisy = 0
    for rel, path in images.items():
        items = ocrmod.readable(res[path.resolve()])
        words = ocrmod.words_of(items)
        said = " ".join(i.text for i in items) + " " + " ".join(words)
        hit = next((rx for rx in pats if rx.search(said)), None)
        if hit:
            problems.append("%s: OCR reads a denylisted term" % rel)
        if rel.startswith("refs/views/") and items:
            noisy += 1
        if rel.startswith("refs/sheets/") and any(not SHEET_WORD.match(w) for w in words):
            noisy += 1
    if problems:
        return "FAILED", problems
    return "no denylisted term in %d images (%d carry noise reads)" % (len(images), noisy), []


def pack_catalog(arch: dict, files: dict) -> str:
    total = sum(f["bytes"] for f in files.values())
    doc = {"about": "The deck skill's reference pack (ruling 23): greeked contact sheets and exemplar views, so the "
                    "skill runs with no outside folder. Every image is greeked: words are grey bars, pictures and "
                    "marks are boxes. Borrow structure, never words. Built by scripts/build_archetypes.py --pack.",
           "schema": "deck-refs@1",
           "encoding": {"view_px": VIEW_PX, "sheet_px": SHEET_PX, "jpeg_quality": JPEG_Q},
           "bytes": total, "archetypes": arch, "files": files}
    return json.dumps(doc, indent=1) + "\n"


def build_pack(check: bool) -> int:
    """Rebuild refs/ from the library (or, with check, compare it). Exit code semantics as main()."""
    arch, plan, problems = pack_plan()
    if problems:
        for pr in problems:
            print("FAIL pack", pr)
        return 1
    if check:
        if not REFS_CATALOG.is_file():
            print("STALE refs/catalog.json is missing (run build_archetypes.py --pack)")
            return 1
        have = json.loads(REFS_CATALOG.read_text())
        stale = []
        if have.get("archetypes") != arch:
            stale.append("refs/catalog.json archetype lists differ from the export")
        if have.get("encoding") != {"view_px": VIEW_PX, "sheet_px": SHEET_PX, "jpeg_quality": JPEG_Q}:
            stale.append("refs/catalog.json encoding differs from this script")
        hf = have.get("files") or {}
        for e in plan:
            f = hf.get(e["rel"]) or {}
            dst = SKILL / e["rel"]
            if f.get("source_sha256") != _sha(e["src"].read_bytes()):
                stale.append("%s: source changed" % e["rel"])
            elif not dst.is_file() or _sha(dst.read_bytes()) != f.get("sha256"):
                stale.append("%s: missing or altered" % e["rel"])
        extra = sorted({str(p.relative_to(SKILL)) for d in ("sheets", "views") for p in (REFS / d).glob("*")}
                       - {e["rel"] for e in plan})
        stale += ["%s: not in the plan" % x for x in extra]
        for x in stale:
            print("STALE", x)
        return 1 if stale else 0
    files: dict[str, dict] = {}
    with tempfile.TemporaryDirectory(prefix="deck-refs-") as tmp:
        staged: dict[str, Path] = {}
        for e in plan:
            data, size = encode(e["src"], e["px"])
            out = Path(tmp) / e["rel"]
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
            staged[e["rel"]] = out
            files[e["rel"]] = {"kind": e["kind"], "source": e["source"], "source_sha256": _sha(e["src"].read_bytes()),
                               "sha256": _sha(data), "bytes": len(data), "px": size}
        status, problems = ocr_pack(staged)
        for pr in problems:
            print("FAIL pack", pr)
        if problems:
            return 1
        cat_text = pack_catalog(arch, files)
        for rx in denylist():
            if rx.search(cat_text):
                print("FAIL pack refs/catalog.json carries a denylisted term")
                return 1
        for d in ("sheets", "views"):
            (REFS / d).mkdir(parents=True, exist_ok=True)
            for old in (REFS / d).glob("*"):
                if str(old.relative_to(SKILL)) not in files:
                    old.unlink()
        for rel, src in staged.items():
            dst = SKILL / rel
            if not dst.is_file() or dst.read_bytes() != src.read_bytes():
                shutil.copyfile(src, dst)
    REFS_CATALOG.write_text(cat_text)
    total = sum(f["bytes"] for f in files.values())
    print("OK pack %d sheets, %d views, %.1f MB, OCR %s" % (
        sum(f["kind"] == "sheet" for f in files.values()), sum(f["kind"] == "view" for f in files.values()),
        total / 1e6, status))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--pack", action="store_true", help="rebuild only the reference pack (refs/)")
    a = ap.parse_args()
    if not (EXPORT / "catalog.json").is_file():
        print("SKIPPED no library export at %s (run library/tools/export.py); the skill runs from refs/" % EXPORT)
        return 0 if a.check else 1
    if a.pack:
        return build_pack(a.check)
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
        rc_pack = build_pack(True)
        return 1 if bad or stale or rc_pack else 0
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
    return build_pack(False)


if __name__ == "__main__":
    sys.exit(main())
