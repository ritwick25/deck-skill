"""P21 determinism: rebuilding the deck from its own build command produces the same bytes, and the deck matches its manifest.

The command is deck.json "build" in the deck's folder: a list of arguments where {python} is this
interpreter and {out} is a scratch path. It runs in that folder; its output's sha256 must equal the deck's.
The manifest beside the deck must record the deck's own sha256 (a hand edit or a post-save touch breaks
it). A deck with no build command cannot prove determinism: FAIL, unless deck.json grants "P21" with a source
(a hand-edited deck whose pptx is the source of truth).
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from _shared import FAIL, Finding, InputMissing, cli

GATE, TITLE = "P21", "determinism"
TIMEOUT = 600


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(deck, ctx):
    out = []
    cmd = ctx.deck_json.get("build")
    if not cmd or not isinstance(cmd, list):
        raise InputMissing("deck.json has no 'build' command (a list, with {python} and {out})")
    have = _sha(ctx.deck_path)
    man = ctx.manifest
    if man is None:
        out.append(Finding(GATE, FAIL, None, "manifest", "no manifest beside the deck"))
    elif man.get("sha256") != have:
        out.append(Finding(GATE, FAIL, None, "manifest", "deck sha %s... is not the manifest's %s..."
                           % (have[:12], str(man.get("sha256"))[:12])))
    tmp = Path(tempfile.mkdtemp(prefix="p21-"))
    try:
        target = tmp / ctx.deck_path.name
        argv = [str(a).replace("{python}", sys.executable).replace("{out}", str(target)) for a in cmd]
        r = subprocess.run(argv, cwd=str(ctx.folder), capture_output=True, text=True, timeout=TIMEOUT)
        if r.returncode != 0 or not target.is_file():
            tail = (r.stdout + r.stderr).strip().splitlines()[-1:] or [""]
            out.append(Finding(GATE, FAIL, None, "build", "rebuild failed (exit %d): %s" % (r.returncode, tail[0][:200])))
            return out
        new = _sha(target)
        if new != have:
            out.append(Finding(GATE, FAIL, None, "build", "rebuild sha %s... differs from the deck's %s..." % (new[:12], have[:12])))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
