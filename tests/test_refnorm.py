"""Unit checks for deckkit.read.refnorm, the leak-reference normaliser shared by the harvester and the gate.

Run: cd ~/.claude/skills/deck && $PY -m unittest tests.test_refnorm -v
Synthetic strings only; the fictional entity is the canary's.
"""
from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "kit"))

from lxml import etree  # noqa: E402

from deckkit.read import words  # noqa: E402
from deckkit.read.refnorm import (canon_url, custgeom_sig, dhash64, hamming64, name_keys, num_phrases,  # noqa: E402
                                  sha1, shingle_tokens, shingles, term_keys)

NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"


class TestNames(unittest.TestCase):
    def test_term_found_in_text(self):
        for term, text in [("Quorvane Biologics", "Prepared for QUORVANE Biologics' review."),
                           ("Quorvane", "the Quorvane’s pipeline"),
                           ("Zeta-Corp", "Zeta Corp and partners"),
                           ("Ab&Cd", "Owned by Ab&Cd Holdings")]:
            self.assertTrue(set(term_keys(term)) & name_keys(text), (term, text))

    def test_short_terms_are_case_sensitive(self):
        self.assertEqual(term_keys("QX"), ["cs:QX"])
        self.assertIn("cs:QX", name_keys("QX-FG planners"))
        self.assertNotIn("cs:QX", name_keys("qx planners"))

    def test_long_term_windows(self):
        ks = term_keys("Alpha Beta Gamma Delta Epsilon")
        self.assertEqual(ks, ["alpha beta gamma delta", "beta gamma delta epsilon"])

    def test_contacts(self):
        self.assertEqual(term_keys("Jo.Doe@example.com"), ["jo.doe@example.com"])
        self.assertIn("jo.doe@example.com", name_keys("Email: jo.doe@example.com."))
        self.assertEqual(canon_url("https://www.Example.com/a/B/?x=1#y"), "example.com/a/b")
        self.assertEqual(canon_url("https://www.youtube.com/watch?v=AbC&list=Q1&index=3&t=9s"),
                         "youtube.com/watch?list=Q1&v=AbC")
        self.assertTrue(set(term_keys("+1 (555) 010 0199")) & name_keys("T +1 (555) 010 0199"))


class TestShingles(unittest.TestCase):
    def test_token_count_matches_words(self):
        t = "“Rising Star” — in Retail & CPG, 2026: one two three"
        self.assertEqual(len(shingle_tokens(t)), words(t))

    def test_fold_and_strip(self):
        self.assertEqual(shingles("Café ONE, two three four five."), {"cafe one two three four five"})
        self.assertEqual(sha1("abc"), "a9993e364706816aba3e25717850c26c9cd0d89d")


class TestNumbers(unittest.TestCase):
    def test_phrases(self):
        p = num_phrases("2,000+ suppliers over 12 weeks, ~$160K saved, 7,431 vials, 26 Feb, 100+ AI products, 2026 plan")
        self.assertIn("2000+ suppliers", p)
        self.assertIn("7431 vials", p)
        self.assertIn("7431", p)
        self.assertIn("100+ ai products", p)
        self.assertNotIn("12 weeks", p)
        self.assertNotIn("26 feb", p)
        self.assertFalse(any(x.startswith("2026") for x in p))


class TestVectors(unittest.TestCase):
    def _cg(self, pts, w=100, h=100):
        body = "".join(f'<a:lnTo><a:pt x="{x}" y="{y}"/></a:lnTo>' for x, y in pts[1:])
        xml = (f'<a:custGeom xmlns:a="{NS_A}"><a:pathLst><a:path w="{w}" h="{h}">'
               f'<a:moveTo><a:pt x="{pts[0][0]}" y="{pts[0][1]}"/></a:moveTo>{body}<a:close/></a:path>'
               f'</a:pathLst></a:custGeom>')
        return etree.fromstring(xml)

    def test_scale_invariant_and_trivial(self):
        star = [(50, 0), (61, 35), (98, 35), (68, 57), (79, 91), (50, 70)]
        a = custgeom_sig(self._cg(star))
        b = custgeom_sig(self._cg([(x * 3, y * 7) for x, y in star], w=300, h=700))
        self.assertIsNotNone(a)
        self.assertEqual(a, b)
        self.assertIsNone(custgeom_sig(self._cg([(0, 0), (100, 0), (100, 100), (0, 100)])))


class TestPictures(unittest.TestCase):
    def test_dhash(self):
        from PIL import Image
        import io
        im = Image.new("RGB", (40, 30), "white")
        for x in range(20, 40):
            for y in range(30):
                im.putpixel((x, y), (0, 0, 0))
        buf = io.BytesIO()
        im.save(buf, "PNG")
        h = dhash64(buf.getvalue())
        self.assertRegex(h, r"^[0-9a-f]{16}$")
        self.assertEqual(hamming64(h, h), 0)
        self.assertIsNone(dhash64(b"not an image"))


if __name__ == "__main__":
    unittest.main()
