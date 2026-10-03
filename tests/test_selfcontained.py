"""Ruling 23: the skill runs with no outside folder, and a scaffolded deck folder carries its own CLAUDE.md.

Run: cd ~/.claude/skills/deck && $PY -m unittest tests.test_selfcontained -v

  * the pack: every sheet, exemplar and anti view archetypes.json lists is in refs/ and matches refs/catalog.json;
    cards cite pack paths only; the pack stays near its size budget;
  * with DECK_LIBRARY pointed at nothing: selftest passes, find.py prints in-skill paths and --real says
    UNAVAILABLE, build_archetypes --check prints SKIPPED and exits 0, example_build builds;
  * selftest's pack and path checks fire: a missing view, a stray file, an altered byte, a card citing a library
    path and a planted ~/Codes path each fail it (run on a copy of the skill, never the skill itself);
  * new_deck.py writes CLAUDE.md (load /deck, build, gates, render, theme, never hand-edit), takes a client theme
    with a brand block, records the client, and refuses to overwrite.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
PY = sys.executable
NOLIB = "/nonexistent/deck-library"
sys.path.insert(0, str(SKILL / "scripts"))

import selftest  # noqa: E402
from paths import REFS_CATALOG, pack_sheet, pack_view  # noqa: E402


def run(args, cwd=None, lib=NOLIB):
    env = dict(os.environ, DECK_LIBRARY=lib)
    return subprocess.run([PY, *map(str, args)], capture_output=True, text=True, cwd=cwd, env=env, timeout=600)


class Pack(unittest.TestCase):
    def setUp(self):
        self.arch = json.loads((SKILL / "archetypes" / "archetypes.json").read_text())["archetypes"]
        self.cat = json.loads(REFS_CATALOG.read_text())

    def test_every_listed_image_is_in_the_pack(self):
        for slug, a in self.arch.items():
            self.assertTrue(pack_sheet(a["id"]).is_file(), slug)
            self.assertEqual(a["sheet"], "refs/sheets/%s.jpg" % a["id"])
            for sid in (a["exemplars"] or []) + (a.get("anti") or []):
                self.assertTrue(pack_view(sid).is_file(), sid)
                self.assertIn("refs/views/%s.jpg" % sid, self.cat["files"])

    def test_catalog_lists_match_archetypes(self):
        for slug, a in self.arch.items():
            c = self.cat["archetypes"][slug]
            self.assertEqual([x["id"] for x in c["exemplars"]], a["exemplars"])
            self.assertEqual([x["id"] for x in c["anti"]], a.get("anti") or [])

    def test_pack_is_jpeg_within_its_edges_and_budget(self):
        enc = self.cat["encoding"]
        for rel, f in self.cat["files"].items():
            limit = enc["view_px"] if f["kind"] == "view" else enc["sheet_px"]
            self.assertLessEqual(max(f["px"]), limit, rel)
            self.assertTrue(rel.endswith(".jpg"))
            self.assertTrue(f["source"].startswith(("greeked/", "export/sheets/")), rel)
        self.assertLess(self.cat["bytes"], 18_000_000)

    def test_cards_cite_pack_paths_only(self):
        for card in (SKILL / "archetypes").glob("*.md"):
            body = card.read_text()
            self.assertNotIn("greeked/d", body, card.name)
            for cite in selftest.CITED.findall(body):
                self.assertTrue((SKILL / cite).is_file(), "%s cites %s" % (card.name, cite))

    def test_outside_pattern(self):
        for bad in ('LIB = "/Users/someone/Codes/x"', "see ~/Codes/x", 'Path.home() / "Codes" / "x"'):
            self.assertTrue(selftest.OUTSIDE.search(bad), bad)
        for ok in ("refs/views/d01-s001.jpg", "Decks-For-Visuals/acceptance/showcase", "codes = 3"):
            self.assertFalse(selftest.OUTSIDE.search(ok), ok)


class NoLibrary(unittest.TestCase):
    def test_selftest_passes(self):
        r = run([SKILL / "scripts" / "selftest.py"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("SKIPPED library checks", r.stdout)

    def test_find_prints_in_skill_paths(self):
        r = run([SKILL / "scripts" / "find.py", "the-ask", "--real"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(str(SKILL / "refs" / "sheets" / "a12.jpg"), r.stdout)
        self.assertIn(str(SKILL / "refs" / "views"), r.stdout)
        self.assertIn("UNAVAILABLE", r.stdout)
        self.assertNotIn("MISSING", r.stdout)
        self.assertNotIn(NOLIB + "/renders", r.stdout)
        for line in r.stdout.splitlines():
            if line.strip().startswith(("sheet", "exemplar", "anti")):
                self.assertIn(str(SKILL), line)

    def test_find_list_and_search(self):
        self.assertEqual(run([SKILL / "scripts" / "find.py"]).returncode, 0)
        self.assertEqual(run([SKILL / "scripts" / "find.py", "--search", "roadmap phases"]).returncode, 0)

    def test_build_archetypes_skips(self):
        r = run([SKILL / "scripts" / "build_archetypes.py", "--check"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("SKIPPED", r.stdout)
        self.assertEqual(run([SKILL / "scripts" / "build_archetypes.py", "--pack"]).returncode, 1)

    def test_example_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "x.pptx"
            r = run([SKILL / "scripts" / "example_build.py", "--out", out])
            self.assertEqual(r.returncode, 0, r.stderr[-800:])
            self.assertTrue(out.is_file())


class SelftestFires(unittest.TestCase):
    """Each planted breakage on a copy of the skill fails selftest and is named."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="deck-skill-copy-")
        cls.root = Path(cls.tmp.name) / "deck"
        ign = shutil.ignore_patterns("__pycache__", "*.pyc", "out", "work", "renders")
        for d in ("scripts", "archetypes", "references", "themes", "kit", "gates", "refs"):
            shutil.copytree(SKILL / d, cls.root / d, ignore=ign)
        (cls.root / "devices").mkdir()
        shutil.copy(SKILL / "devices" / "devices.json", cls.root / "devices" / "devices.json")
        for f in ("SKILL.md", "DECISIONS.md"):
            shutil.copy(SKILL / f, cls.root / f)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def selftest(self):
        return run([self.root / "scripts" / "selftest.py"])

    def test_copy_passes(self):
        r = self.selftest()
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_missing_view(self):
        v = self.root / "refs" / "views" / "d01-s053.jpg"
        keep = v.read_bytes()
        v.unlink()
        try:
            r = self.selftest()
            self.assertEqual(r.returncode, 1)
            self.assertIn("refs/views/d01-s053.jpg is not in the pack", r.stdout)
        finally:
            v.write_bytes(keep)

    def test_stray_file(self):
        v = self.root / "refs" / "views" / "d99-s999.jpg"
        v.write_bytes(b"x")
        try:
            r = self.selftest()
            self.assertIn("d99-s999.jpg is not in refs/catalog.json", r.stdout)
        finally:
            v.unlink()

    def test_altered_byte(self):
        v = self.root / "refs" / "sheets" / "a12.jpg"
        keep = v.read_bytes()
        v.write_bytes(keep[:-1] + bytes([keep[-1] ^ 1]))
        try:
            r = self.selftest()
            self.assertIn("refs/sheets/a12.jpg differs from its catalog sha256", r.stdout)
        finally:
            v.write_bytes(keep)

    def test_card_citing_library(self):
        c = self.root / "archetypes" / "the-ask.md"
        keep = c.read_text()
        c.write_text(keep + "\n| d01-s053 | greeked/d01/s053.png | x |\n")
        try:
            r = self.selftest()
            self.assertIn("the-ask.md cites greeked/d01/s053.png, a library path", r.stdout)
        finally:
            c.write_text(keep)

    def test_planted_outside_path(self):
        f = self.root / "kit" / "deckkit" / "planted_canary.py"
        f.write_text('SRC = "~/Codes/elsewhere/data.json"\n')
        try:
            r = self.selftest()
            self.assertIn("kit/deckkit/planted_canary.py:1 names a path outside the skill", r.stdout)
        finally:
            f.unlink()


class NewDeck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_claude_md_and_build(self):
        folder = self.dir / "proj"
        r = run([SKILL / "scripts" / "new_deck.py", folder, "--name", "Test Deck"])
        self.assertEqual(r.returncode, 0, r.stderr)
        md = (folder / "CLAUDE.md").read_text()
        lines = md.strip().splitlines()
        self.assertLessEqual(len(lines), 14)
        for want in ("/deck", "build.py", "run_all.py", "render.py", "themes/sigmoid.json", "house theme sigmoid",
                     "Never hand-edit `Test Deck.pptx`"):
            self.assertIn(want, md)
        b = run([folder / "build.py"], cwd=folder)
        self.assertEqual(b.returncode, 0, b.stderr[-800:])
        self.assertTrue((folder / "Test Deck.pptx").is_file())
        again = run([SKILL / "scripts" / "new_deck.py", folder, "--name", "Test Deck"])
        self.assertNotEqual(again.returncode, 0)
        self.assertIn("refusing to overwrite", again.stderr)

    def test_client_theme(self):
        data = json.loads((SKILL / "themes" / "sigmoid.json").read_text())
        data["brand"] = {"client": "Acme Health", "logo": {"file": "logo.svg"}}
        theme = self.dir / "brand" / "theme.json"
        theme.parent.mkdir()
        theme.write_text(json.dumps(data))
        folder = self.dir / "proj"
        r = run([SKILL / "scripts" / "new_deck.py", folder, "--name", "Acme POV", "--theme", theme])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads((folder / "deck.json").read_text())["client"], "Acme Health")
        md = (folder / "CLAUDE.md").read_text()
        self.assertIn("client theme for Acme Health", md)
        self.assertIn(str(theme.parent.resolve() / "logo.svg"), md)
        self.assertNotIn("NOTE", r.stdout)

    def test_client_on_house_theme_is_flagged(self):
        r = run([SKILL / "scripts" / "new_deck.py", self.dir / "p", "--name", "X", "--client", "Acme"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("brand.py", r.stdout)

    def test_bad_theme_refused(self):
        bad = self.dir / "bad.json"
        bad.write_text("{}")
        r = run([SKILL / "scripts" / "new_deck.py", self.dir / "p", "--name", "X", "--theme", bad])
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.dir / "p" / "build.py").exists())


if __name__ == "__main__":
    unittest.main()
