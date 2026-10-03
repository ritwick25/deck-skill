"""The skill's name scan (build_archetypes.denylist, used by selftest and the pack OCR check) reads every term and
every alias of the library leak list, and refuses to run on a list it cannot trust.

    $PY -m unittest tests/test_leak_scan.py -v

Probe names are assembled from pieces so this file carries none whole (selftest skips tests/, the hook does not).
Skipped when the library is absent: the skill runs without it and the scan is a library-side check.
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

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))

import build_archetypes as BA  # noqa: E402
from paths import LIB, PY, library_ready  # noqa: E402

ALIASES = ["Co" + "ke", "T" + "CCC", "K" + "O", "Deb " + "Das", "Rahul " + "Singh", "Kimberly " + "Clark"]
USER_PATH = "/Users/" + "Nik" + "unj/Codes/x.py"

needs_lib = unittest.skipUnless(library_ready() and (LIB / "leak" / "denylist.json").is_file(), "no library")


@needs_lib
class Denylist(unittest.TestCase):
    def setUp(self):
        self.pats = BA.denylist()

    def hit(self, text: str) -> bool:
        return any(rx.search(text) for rx in self.pats)

    def test_terms_and_aliases_compile(self):
        d = json.loads((LIB / "leak" / "denylist.json").read_text())
        n = len({x for e in d["terms"] for x in [e["term"]] + list(e.get("aliases") or [])})
        self.assertEqual(len(self.pats), n)
        self.assertGreaterEqual(len(self.pats), BA.DENY_MIN)

    def test_aliases_and_people_match(self):
        for a in ALIASES:
            self.assertTrue(self.hit("The %s brief." % a), a)
        self.assertTrue(self.hit("See %s for the source." % USER_PATH))

    def test_short_terms_match_case_sensitively(self):
        for w in ("a ko punch", "an <ul> list", "the kc ratio"):
            self.assertFalse(self.hit(w), w)


class Refuses(unittest.TestCase):
    """A scan with no patterns passes everything, so a missing or short list raises."""

    def run_with(self, payload):
        with tempfile.TemporaryDirectory() as tmp:
            lib = Path(tmp)
            if payload is not None:
                (lib / "leak").mkdir()
                (lib / "leak" / "denylist.json").write_text(json.dumps(payload))
            code = ("import sys; sys.path.insert(0, %r); import build_archetypes as B\n"
                    "try:\n    B.denylist(); print('RAN')\nexcept RuntimeError as e:\n    print('REFUSED', e)\n"
                    % str(SKILL / "scripts"))
            r = subprocess.run([PY, "-c", code], capture_output=True, text=True, env=dict(os.environ, DECK_LIBRARY=tmp))
            return r.stdout

    def test_missing_list(self):
        self.assertIn("REFUSED", self.run_with(None))

    def test_short_list(self):
        self.assertIn("REFUSED", self.run_with({"terms": [{"term": "Acme%d" % i, "aliases": []} for i in range(20)]}))

    def test_aliases_ignored_is_caught(self):
        # 250 terms but the canary names live only as aliases: a reader that drops aliases fails the canary
        terms = [{"term": "Acme%d" % i, "aliases": []} for i in range(250)]
        self.assertIn("alias", self.run_with({"terms": terms}))


@needs_lib
class SelftestCatches(unittest.TestCase):
    """selftest on a copy of the skill, against the real library, names a planted alias and a username path."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="deck-leak-copy-")
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
        return subprocess.run([PY, str(self.root / "scripts" / "selftest.py")], capture_output=True, text=True,
                              env=dict(os.environ, DECK_LIBRARY=str(LIB)), timeout=600)

    def plant(self, text: str) -> str:
        f = self.root / "references" / "planted-leak.md"
        f.write_text("# Planted\n\n" + text + "\n")
        try:
            return self.selftest().stdout
        finally:
            f.unlink()

    def test_alias_is_named(self):
        out = self.plant("Built for %s in the spring." % ("Co" + "ke"))
        self.assertIn("references/planted-leak.md:3 carries a denylisted term", out)
        self.assertNotIn("Co" + "ke", out)

    def test_username_path_is_named(self):
        self.assertIn("references/planted-leak.md:3 carries a denylisted term", self.plant("Source: " + USER_PATH))

    def test_pastel_light_bg_row_is_named(self):
        """Ruling 12: a light-bg row that turns a panel pastel fails; one that says never a tint passes."""
        c = self.root / "archetypes" / "closing.md"
        keep = c.read_text()
        bad = "| light-bg | A dark band. | Light slide grounds. | The band becomes a light surface with dark ink. |"
        ok = "| light-bg | A dark band. | Light slide ground. | The band stays solid. Never a pale tint band. |"
        try:
            c.write_text(keep + "\n" + ok + "\n")
            self.assertNotIn("light-bg row turns a panel pastel", self.selftest().stdout)
            c.write_text(keep + "\n" + bad + "\n")
            self.assertIn("closing.md:%d light-bg row turns a panel pastel" % (len(keep.splitlines()) + 2),
                          self.selftest().stdout)
        finally:
            c.write_text(keep)


if __name__ == "__main__":
    unittest.main()
