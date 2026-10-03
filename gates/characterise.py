#!/usr/bin/env python3
"""Characteriser: every pptx gate over real decks, measured and reported. It cannot fail.

    $PY gates/characterise.py                         the library's reference-deck copies (d01, d15, d18)
    $PY gates/characterise.py --decks a.pptx b.pptx   any decks (each needs its own deck.json and theme)
    $PY gates/characterise.py --per-gate 3 --seed 7   the sample size and its seed

A gate tests machinery and fails; a characteriser measures the world and cannot. The gates are written for decks the
kit builds, so on a deck built by hand every finding is either a defect the gate is right about or a false positive,
and only a person looking at the slide can say which. This script does the counting and picks what to look at:

  1. stages each deck in its own folder, library/_work/characterise/<stem>/ (a hard link, a copy where linking
     fails), beside a review deck.json (the sigmoid theme, no build command, no notes deck), so no deck borrows the
     deck.json the golden build writes into .cache. Client decks never enter the skill folder (ruling 23, CLAUDE.md
     section 5): the inputs, the staging and the report all live in the library, and without the library the
     characteriser says so and exits 0. Then it runs every implemented pptx gate in gates/registry.json
     over it, in-process, with the same Ctx the runner uses (a gate that crashes or cannot read its input is
     recorded with its exit code, never raised);
  2. writes library/_work/characterise/fp_report.json (it quotes client text, so it stays in the library): per gate, per deck, the exit code, the FAIL / advisory / note counts, the slides
     hit, the share of slides hit, the seconds taken and every finding;
  3. lists a stratified sample of PER_GATE findings per gate for human review: FAIL findings first (advisories only
     when a gate has no FAIL), spread round-robin across the decks that have any, one slide never sampled twice for
     a gate while another slide is left, drawn with a fixed seed so a rerun lists the same rows. Each row names the
     slide's render when the library has one, so the reviewer opens the picture beside the finding.

Exit code: always 0. A missing deck is a row in the report, not a failure. The verdict on each sampled finding (true
defect or false positive) is the reviewer's, written beside the sample, never computed here.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import random
import shutil
import sys
import time
import traceback
from dataclasses import asdict
from pathlib import Path

GATES_DIR = Path(__file__).resolve().parent
SKILL = GATES_DIR.parent
sys.path.insert(0, str(GATES_DIR))
sys.path.insert(0, str(SKILL / "kit"))

from _shared import ADVISORY, FAIL, NOTE, Ctx, InputMissing, run_gate  # noqa: E402

LIBRARY = Path(os.environ.get("DECK_LIBRARY", Path.home() / "Codes" / "Decks-For-Visuals" / "library"))
WORK = LIBRARY / "_work"
DEFAULT_DECKS = [WORK / "src" / ("%s.pptx" % d) for d in ("d01", "d15", "d18")]
STAGE = WORK / "characterise"
DEFAULT_OUT = STAGE / "fp_report.json"
DEFAULT_RENDERS = LIBRARY / "renders"
PER_GATE = 3
SEED = 20261003
REVIEW_JSON = {"type": "review", "theme": str(SKILL / "themes" / "sigmoid.json"), "client": None, "spelling": "US",
               "overrides": {}, "budgets": {}, "series": [], "notes_deck": False}


def inside_skill(p: Path) -> bool:
    try:
        Path(p).resolve().relative_to(SKILL.resolve())
        return True
    except ValueError:
        return False


def stage(path: Path) -> Path:
    """The deck hard-linked (or copied) into its own folder beside a review deck.json; returns the staged path. The
    staging folder is in the library, never in the skill."""
    if inside_skill(STAGE):
        raise RuntimeError("the staging folder %s is inside the skill; client decks never stage there" % STAGE)
    d = STAGE / path.stem
    d.mkdir(parents=True, exist_ok=True)
    dst = d / path.name
    if not dst.exists() or dst.stat().st_size != path.stat().st_size or dst.stat().st_mtime < path.stat().st_mtime:
        if dst.exists():
            dst.unlink()
        try:
            os.link(path, dst)
        except OSError:
            shutil.copy2(path, dst)
    (d / "deck.json").write_text(json.dumps(REVIEW_JSON, indent=1) + "\n", encoding="utf-8")
    return dst


def registry() -> list[dict]:
    return json.loads((GATES_DIR / "registry.json").read_text(encoding="utf-8"))["gates"]


def pptx_gates() -> list[dict]:
    return [g for g in registry() if g["kind"] == "pptx" and (GATES_DIR / (g["module"] + ".py")).is_file()]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def render_of(renders: Path, deck: str, slide) -> str | None:
    if slide is None:
        return None
    p = renders / deck / ("s%03d.png" % slide)
    return str(p) if p.is_file() else None


def characterise_deck(path: Path, gates: list[dict]) -> dict:
    """{"path", "sha256", "slides", "error", "gates": {gid: row}} for one deck. Never raises."""
    out = {"path": str(path), "sha256": None, "slides": None, "error": None, "gates": {}}
    if not path.is_file():
        out["error"] = "deck not found"
        return out
    out["sha256"] = sha(path)
    try:
        path = stage(path)
        out["staged"] = str(path)
        ctx = Ctx(path)
        out["slides"] = ctx.n
    except (InputMissing, Exception) as e:          # a deck the read layer refuses is a row, not a crash
        out["error"] = "%s: %s" % (type(e).__name__, e)
        return out
    try:
        for g in gates:
            t0 = time.time()
            try:
                mod = importlib.import_module(g["module"])
                code, found = run_gate(mod, str(path), ctx)
            except Exception as e:                     # run_gate already catches; this is belt and braces
                code, found = 1, []
                out["gates"][g["id"]] = {"code": code, "error": "%s: %s" % (type(e).__name__, e),
                                         "trace": traceback.format_exc()[-400:]}
                continue
            fails = [f for f in found if f.level == FAIL]
            hit = sorted({f.slide for f in fails if f.slide is not None})
            out["gates"][g["id"]] = {
                "title": g["title"], "code": code, "secs": round(time.time() - t0, 2),
                "fail": len(fails), "advisory": sum(1 for f in found if f.level == ADVISORY),
                "note": sum(1 for f in found if f.level == NOTE),
                "slides_hit": hit, "slide_rate": round(len(hit) / ctx.n, 3) if ctx.n else 0.0,
                "deck_level_fail": sum(1 for f in fails if f.slide is None),
                "findings": [asdict(f) for f in found],
            }
    finally:
        ctx.close()
    return out


def sample(report: dict, per_gate: int, seed: int, renders: Path) -> dict:
    """{gid: [row, ...]}: per_gate findings per gate, FAIL first, round-robin across decks, distinct slides first."""
    rng = random.Random(seed)
    out = {}
    gids = []
    for d in report["decks"].values():
        for gid in d["gates"]:
            if gid not in gids:
                gids.append(gid)
    for gid in gids:
        pools = {}
        for name, d in report["decks"].items():
            row = d["gates"].get(gid) or {}
            fs = row.get("findings") or []
            pools[name] = [f for f in fs if f["level"] == FAIL]
        level = FAIL
        if not any(pools.values()):
            level = ADVISORY
            for name, d in report["decks"].items():
                fs = (d["gates"].get(gid) or {}).get("findings") or []
                pools[name] = [f for f in fs if f["level"] == ADVISORY]
        for name in pools:
            rng.shuffle(pools[name])
        picked, used = [], set()
        decks = [n for n in sorted(pools) if pools[n]]
        while len(picked) < per_gate and any(pools[n] for n in decks):
            for name in decks:
                if len(picked) >= per_gate or not pools[name]:
                    continue
                fresh = [f for f in pools[name] if (name, f["slide"]) not in used]
                f = (fresh or pools[name])[0]
                pools[name].remove(f)
                used.add((name, f["slide"]))
                picked.append({"deck": name, "level": level, "slide": f["slide"], "where": f["where"],
                               "msg": f["msg"], "render": render_of(renders, name, f["slide"]),
                               "verdict": None})
        out[gid] = picked
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--decks", nargs="*", help="decks to characterise (default: the library's d01, d15, d18 copies)")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--renders", default=str(DEFAULT_RENDERS), help="library renders root (dNN/sNNN.png)")
    ap.add_argument("--per-gate", type=int, default=PER_GATE)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--only", default="", help="comma-separated gate ids")
    a = ap.parse_args(argv)
    if not a.decks and not WORK.is_dir():
        print("no reference library at %s (set DECK_LIBRARY); nothing to characterise. A characteriser: exit 0."
              % LIBRARY)
        return 0
    if inside_skill(Path(a.out)):
        print("refused: --out %s is inside the skill; the report quotes client text and stays in the library" % a.out)
        return 0
    decks = [Path(p).resolve() for p in (a.decks or DEFAULT_DECKS)]
    gates = pptx_gates()
    if a.only:
        want = {x.strip().upper() for x in a.only.split(",") if x.strip()}
        gates = [g for g in gates if g["id"] in want]
    t0 = time.time()
    report = {"about": "characteriser, not a gate: counts and a review sample, never a verdict",
              "generated": time.strftime("%Y-%m-%dT%H:%M:%S"), "gates": [g["id"] for g in gates],
              "renders": a.renders, "decks": {}}
    for p in decks:
        t = time.time()
        report["decks"][p.stem] = characterise_deck(p, gates)
        print("read %s: %s slides, %.1fs%s" % (p.stem, report["decks"][p.stem]["slides"], time.time() - t,
                                                ("  (%s)" % report["decks"][p.stem]["error"])
                                                if report["decks"][p.stem]["error"] else ""))
    report["sample"] = sample(report, a.per_gate, a.seed, Path(a.renders))
    report["secs"] = round(time.time() - t0, 1)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")

    names = list(report["decks"])
    print("\n%-5s %-14s " % ("gate", "") + " ".join("%-22s" % n for n in names))
    print("%-5s %-14s " % ("", "") + " ".join("%-22s" % "fail/slides hit/rate" for _ in names))
    for g in gates:
        cells = []
        for n in names:
            r = report["decks"][n]["gates"].get(g["id"])
            if not r or "fail" not in r:
                cells.append("%-22s" % ("-" if not r else "error"))
            else:
                tag = "" if r["code"] != 2 else " input"
                cells.append("%-22s" % ("%d / %d / %.0f%%%s" % (r["fail"], len(r["slides_hit"]),
                                                                 100 * r["slide_rate"], tag)))
        print("%-5s %-14s " % (g["id"], g["title"][:14]) + " ".join(cells))
    print("\nreview sample (%d per gate, seed %d): mark each row true defect or false positive" % (a.per_gate, a.seed))
    for gid, rows in report["sample"].items():
        for r in rows:
            loc = ("s%d" % r["slide"]) if r["slide"] is not None else "deck"
            print("  %-4s %-4s %-5s %-4s %s: %s" % (gid, r["deck"], loc, r["level"][:4], r["where"][:40], r["msg"][:90]))
            if r["render"]:
                print("        %s" % r["render"])
    print("\nwrote %s (%.0fs). A characteriser: exit 0 whatever it found." % (a.out, report["secs"]))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:                                   # cannot fail: a crash is reported, the exit stays 0
        traceback.print_exc()
        sys.exit(0)
