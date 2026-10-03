#!/usr/bin/env python3
"""Every deck gate, cheapest first, so a failure arrives in a second rather than after an XSD run or a rebuild.

  $PY gates/run_all.py --deck out/x.pptx              every registered gate on one deck
  $PY gates/run_all.py --deck x.pptx --only P01,P17    named gates only
  $PY gates/run_all.py --deck x.pptx --static          the pptx gates only (no render, no twin)
  $PY gates/run_all.py --deck x.pptx --theme T.json    a deck with no deck.json beside it (REVIEW mode)
  $PY gates/run_all.py --list                          the registry, each gate's state and its planters
  $PY gates/run_all.py --negatives                     prove every gate can fail (see below)

The registry (gates/registry.json) lists every gate with its kind (pptx, render, html) and what it needs. A
pptx gate whose module is missing is MISSING and fails the run, so a gate that has not been written can
never be mistaken for one that passed. Render and html gates belong to a later phase: until their module
lands they report PENDING, which is not a pass and not a failure; their rows show with -v or when named in
--only, and the summary counts the implemented gates. A gate that cannot read an input exits 2 and counts as FAIL.
A gate that passes with advisories (P13's thin slides under the measured floor) shows their count and the first
one in the detail column, so a thin slide is visible without -v.

--negatives (the fable runner's design, on copies instead of patched sources):
  1. build the golden fixture (tests/build_golden.py) into .cache/golden.pptx;
  2. assert the golden passes EVERY implemented gate, or the negatives prove nothing;
  3. for each planter in gates/negatives.py and every gates/negatives_*.py module it discovers: copy the golden with its manifest and deck.json into a scratch
     folder, plant one breakage, run the planter's gate, and require exit 1;
  4. fail the run when any implemented gate has no planter.
Rows report: failed as expected, DID NOT FAIL, FAILED ON ANOTHER RULE (the gate went red, but no finding names
the rule the planter targets, so that rule is still unproven), FAILED ON INPUT (exit 2, so the plant broke the
input rather than tripping the check), PLANT ERROR (the planter raised, or changed nothing), GATE MISSING,
NO PLANTER, DISCOVERY ERROR (a negatives_*.py module that did not import: its planters are unproven, never
skipped).
No source file is ever edited, so an interrupted run cannot leave a dirty tree.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

GATES_DIR = Path(__file__).resolve().parent
SKILL = GATES_DIR.parent
sys.path.insert(0, str(GATES_DIR))
sys.path.insert(0, str(SKILL / "kit"))

from _shared import FAIL, Ctx, InputMissing, run_gate  # noqa: E402

REGISTRY = GATES_DIR / "registry.json"
GOLDEN = SKILL / ".cache" / "golden.pptx"
BUILDER = SKILL / "tests" / "build_golden.py"
OK = "failed as expected"


def registry() -> list[dict]:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))["gates"]


def module_path(g) -> Path:
    return GATES_DIR / (g["module"] + ".py")


def load(g):
    """The gate module, or None when its file does not exist yet."""
    if not module_path(g).is_file():
        return None
    return importlib.import_module(g["module"])


def implemented(reg) -> list[dict]:
    return [g for g in reg if g["kind"] == "pptx" and module_path(g).is_file()]


def first_fail(found) -> str:
    for f in found:
        if f.level == FAIL:
            loc = ("s%d " % f.slide) if f.slide is not None else ""
            return (loc + (f.where + ": " if f.where else "") + f.msg)[:110]
    return ""


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ------------------------------------------------------------------ one deck

def run_deck(args, reg) -> int:
    deck = Path(args.deck).resolve()
    sel = reg
    if args.static:
        sel = [g for g in sel if g["kind"] == "pptx"]
    if args.only:
        want = {x.strip().upper() for x in args.only.split(",") if x.strip()}
        unknown = want - {g["id"] for g in reg}
        if unknown:
            print("no gate named %s; gates are %s" % (", ".join(sorted(unknown)), ", ".join(g["id"] for g in reg)))
            return 1
        sel = [g for g in sel if g["id"] in want]
    theme = getattr(args, "theme", None)
    theme = str(Path(theme).resolve()) if isinstance(theme, str) and theme else None    # relative to the cwd
    try:
        ctx = Ctx(deck, refs_dir=args.refs, fingerprints=args.fingerprints, theme=theme, extra={"twin": args.twin})
    except InputMissing as e:
        print("FAIL  %s" % e)
        return 2
    print("\n" + "=" * 92)
    print("  deck gates: %s" % deck)
    print("=" * 92)
    rows = []
    for g in sel:
        t0 = time.time()
        mod = load(g)
        if mod is None:
            state = "PENDING" if g.get("phase") == "later" else "MISSING"
            rows.append((g, state, "%s is not written yet" % module_path(g).name, 0.0))
            continue
        if g["kind"] == "html" and not args.twin:
            rows.append((g, "FAIL", "needs --twin (missing input)", 0.0))
            continue
        code, found = run_gate(mod, str(deck), ctx)
        dt = time.time() - t0
        skipped = [f for f in found if f.level == "note" and f.msg.startswith("SKIPPED")]
        state = ("partial" if skipped else "pass") if code == 0 else "FAIL"     # a skipped sub-check is not a pass
        if code != 0 or args.verbose:
            print("\n%s %s" % (g["id"], g["title"]))
            shown = [f for f in found if f.level == FAIL or args.verbose]
            for f in shown[:25]:
                print(f.line())
            if len(shown) > 25:
                print("  ... and %d more" % (len(shown) - 25))
        adv = [f for f in found if f.level == "advisory"]
        if code:
            detail = first_fail(found)
        elif skipped:
            detail = skipped[0].msg
        elif adv:
            f = adv[0]
            detail = "%d advisory: %s%s" % (len(adv), ("s%d " % f.slide) if f.slide is not None else "", f.msg)
        else:
            detail = next((f.msg for f in found if f.level == "note"), "")
        if code == 2:
            detail = "missing input: " + detail
        rows.append((g, state, detail, dt))
    ctx.close()
    print("\n%-5s %-14s %-8s %6s  %s" % ("gate", "", "result", "secs", "detail"))
    print("-" * 92)
    named = {x.strip().upper() for x in (args.only or "").split(",") if x.strip()}
    for g, state, detail, dt in rows:
        if state == "PENDING" and not (args.verbose or g["id"] in named):
            continue
        print("%-5s %-14s %-8s %6.2f  %s" % (g["id"], g["title"][:14], state, dt, detail[:58]))
    print("-" * 92)
    n_fail = sum(1 for _, s, _, _ in rows if s in ("FAIL", "MISSING"))
    n_pend = sum(1 for _, s, _, _ in rows if s == "PENDING")
    n_pass = sum(1 for _, s, _, _ in rows if s == "pass")
    n_miss = sum(1 for _, s, _, _ in rows if s == "MISSING")
    n_part = sum(1 for _, s, _, _ in rows if s == "partial")
    part = (", %d partial (a sub-check SKIPPED)" % n_part) if n_part else ""
    pend = (", %d later-phase gate(s) pending%s" % (n_pend, "" if args.verbose else " (shown with -v)")) if n_pend else ""
    print("%d gates: %d pass%s, %d fail (%d missing)%s\n"
          % (len(rows) - n_pend, n_pass, part, n_fail, n_miss, pend))
    return 1 if n_fail else 0


# ------------------------------------------------------------------ negatives

def build_golden() -> tuple[bool, str]:
    r = subprocess.run([sys.executable, "-B", str(BUILDER), "--out", str(GOLDEN)], capture_output=True, text=True,
                       timeout=600)
    return r.returncode == 0 and GOLDEN.is_file(), (r.stdout + r.stderr).strip()


def sidecars(deck: Path) -> list[Path]:
    return [p for p in (deck.with_name(deck.stem + ".manifest.json"), deck.parent / "deck.json") if p.is_file()]


def run_negatives(args, reg) -> int:
    from negatives import DISCOVERY_ERRORS, PLANTERS
    t0 = time.time()
    ok, out = build_golden()
    if not ok:
        print("golden build FAILED:\n" + out)
        return 1
    print("golden: %s  sha256 %s" % (GOLDEN, sha(GOLDEN)[:16]))
    gates = implemented(reg)
    only = {x.strip().upper() for x in (args.only or "").split(",") if x.strip()}
    if only:
        gates = [g for g in gates if g["id"] in only]
    # 2. the golden must pass every implemented gate
    ctx = Ctx(GOLDEN)
    dirty = []
    for g in gates:
        code, found = run_gate(load(g), str(GOLDEN), ctx)
        if code != 0:
            dirty.append((g, found))
    ctx.close()
    if dirty:
        print("\nTHE GOLDEN FIXTURE FAILS %d GATE(S). Negatives prove nothing until it is clean." % len(dirty))
        for g, found in dirty:
            print("\n%s %s" % (g["id"], g["title"]))
            for f in [f for f in found if f.level == FAIL][:12]:
                print(f.line())
        return 1
    print("golden passes all %d implemented gate(s)\n" % len(gates))
    # 3. planters
    by_id = {g["id"]: g for g in reg}
    gold_sha = sha(GOLDEN)
    rows = []
    planters = [pl for pl in PLANTERS if not only or pl.gate in only]
    for pl in planters:
        g = by_id.get(pl.gate)
        if g is None:
            rows.append((pl, "UNKNOWN GATE", ""))
            continue
        mod = load(g)
        if mod is None:
            rows.append((pl, "GATE MISSING", module_path(g).name))
            continue
        tmp = Path(tempfile.mkdtemp(prefix="neg-%s-" % pl.name))
        try:
            dst = tmp / GOLDEN.name
            shutil.copy2(GOLDEN, dst)
            for sc in sidecars(GOLDEN):
                shutil.copy2(sc, tmp / sc.name)
            work = tmp / "work"
            work.mkdir()
            try:
                extra = pl.fn(dst, work) or {}
            except Exception as e:  # a planter that breaks is not a passing negative
                rows.append((pl, "PLANT ERROR", "%s: %s" % (type(e).__name__, str(e)[:80])))
                continue
            changed = sha(dst) != gold_sha
            if pl.ctx_only and (changed or not extra):
                rows.append((pl, "PLANT ERROR", "a context-only planter must change the context and not the deck"))
                continue
            if not pl.ctx_only and not changed:
                rows.append((pl, "PLANT ERROR", "the planter left the deck byte-identical"))
                continue
            try:
                c = Ctx(dst, extra=extra)
            except InputMissing as e:
                rows.append((pl, "FAILED ON INPUT", str(e)[:80]))
                continue
            code, found = run_gate(mod, str(dst), c)
            c.close()
            res = {1: OK, 0: "DID NOT FAIL", 2: "FAILED ON INPUT"}.get(code, "exit %d" % code)
            why = first_fail(found)
            if code == 1 and pl.expect:
                hit = [f for f in found if f.level == FAIL and pl.expect.lower() in (f.where + " " + f.msg).lower()]
                if hit:
                    f = hit[0]
                    why = (("s%d " % f.slide) if f.slide is not None else "") + (f.where + ": " if f.where else "") + f.msg
                else:
                    res = "FAILED ON ANOTHER RULE"
                    why = "wanted %r; got %s" % (pl.expect, why)
            rows.append((pl, res, why))
        finally:
            if not args.keep:
                shutil.rmtree(tmp, ignore_errors=True)
    # 4. coverage: every implemented gate has at least one planter
    covered = {pl.gate for pl in PLANTERS}
    missing_planters = [g for g in implemented(reg) if g["id"] not in covered and (not only or g["id"] in only)]
    print("%-24s %-5s %-20s %s" % ("negative", "gate", "result", "caught by"))
    print("-" * 110)
    good = bad = 0
    for pl, res, why in rows:
        print("%-24s %-5s %-20s %s" % (pl.name, pl.gate, res, why[:62]))
        if res == OK:
            good += 1
        else:
            bad += 1
    for g in missing_planters:
        print("%-24s %-5s %-20s %s" % ("-", g["id"], "NO PLANTER", "a gate never seen to fail is unproven"))
        bad += 1
    for mod, err in DISCOVERY_ERRORS:
        print("%-24s %-5s %-20s %s" % (mod, "-", "DISCOVERY ERROR", err[:62]))
        bad += 1
    print("-" * 110)
    n_impl = len(gates)
    print("%d negatives, %d behaved as expected, %d did not; %d/%d implemented gates covered; %d pending (later "
          "phase); %.0fs\n" % (len(rows), good, bad - len(missing_planters) - len(DISCOVERY_ERRORS),
                               n_impl - len(missing_planters), n_impl,
                               sum(1 for g in reg if g.get("phase") == "later" and not module_path(g).is_file()),
                               time.time() - t0))
    return 1 if bad else 0


# ------------------------------------------------------------------ list

def list_gates(reg) -> int:
    from negatives import PLANTERS
    count = {}
    for pl in PLANTERS:
        count[pl.gate] = count.get(pl.gate, 0) + 1
    print("%-5s %-26s %-7s %-10s %-9s %s" % ("id", "title", "kind", "state", "planters", "needs"))
    for g in reg:
        here = module_path(g).is_file()
        state = "ready" if here else ("PENDING" if g.get("phase") == "later" else "MISSING")
        print("%-5s %-26s %-7s %-10s %-9s %s" % (g["id"], g["title"], g["kind"], state, count.get(g["id"], 0),
                                                 ", ".join(g["needs"])))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("deck_pos", nargs="?", help="the deck (or use --deck)")
    ap.add_argument("--deck")
    ap.add_argument("--twin", help="the HTML twin, for the html gates")
    ap.add_argument("--only", default="", help="comma-separated gate ids")
    ap.add_argument("--static", action="store_true", help="pptx gates only")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--negatives", action="store_true")
    ap.add_argument("--refs", help="leak references folder for P18 (default devices/refs)")
    ap.add_argument("--fingerprints", help="fingerprints.json for P17")
    ap.add_argument("--theme", help="theme JSON, for a deck with no deck.json beside it (REVIEW mode)")
    ap.add_argument("--keep", action="store_true", help="keep each negative's scratch folder")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    a.deck = a.deck or a.deck_pos
    reg = registry()
    if a.list:
        return list_gates(reg)
    if a.negatives:
        return run_negatives(a, reg)
    if not a.deck:
        ap.error("give a deck (--deck X.pptx), or --negatives, or --list")
    return run_deck(a, reg)


if __name__ == "__main__":
    sys.exit(main())
