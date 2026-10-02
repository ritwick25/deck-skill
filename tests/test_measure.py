"""deckkit.measure: measured fit, faces per weight, refusals instead of clamps.

Run: cd ~/.claude/skills/deck && $PY -m unittest tests.test_measure -v
"""
from __future__ import annotations

import os
import re
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "kit"))

from deckkit import measure as M  # noqa: E402
from deckkit.errors import BelowFloor, Overflows, UnknownFace  # noqa: E402

ARIAL = M.FACES["Arial"]
BOLD = M.FACES["Arial Bold"]
SEMI = M.FACES["Montserrat SemiBold"]
TEXT = "Regional teams agree which accounts move first"


class Slack(unittest.TestCase):
    def test_fits_at_one_but_not_at_slack(self):
        w = M.width_in(TEXT, 12, ARIAL) * 1.05          # 5% wider than the bare advance sum
        self.assertEqual(M.wrap(TEXT, 12, ARIAL, w, slack=1.0), [TEXT])
        self.assertGreater(len(M.wrap(TEXT, 12, ARIAL, w)), 1)
        one_line = (w, M.line_in(12, ARIAL))
        self.assertTrue(M.fits([(TEXT, 12, ARIAL)], one_line, slack=1.0).ok)
        self.assertFalse(M.fits([(TEXT, 12, ARIAL)], one_line).ok)
        with self.assertRaises(Overflows):
            M.require_fit("caption", [(TEXT, 12, ARIAL)], one_line)

    def test_slack_is_read_at_call_time(self):
        """The builder negative patches SLACK; a default bound at import would ignore the patch."""
        w = M.width_in(TEXT, 12, ARIAL) * 1.05
        with mock.patch.object(M, "SLACK", 1.0):
            self.assertEqual(M.wrap(TEXT, 12, ARIAL, w), [TEXT])
        self.assertGreater(len(M.wrap(TEXT, 12, ARIAL, w)), 1)


class Faces(unittest.TestCase):
    def test_bold_measured_wider_than_regular(self):
        self.assertGreater(M.width_in(TEXT, 12, BOLD), M.width_in(TEXT, 12, ARIAL) * 1.03)
        self.assertIs(M.face_for("Arial", bold=True), BOLD)
        self.assertIs(M.face_for("arial", bold=True, italic=True), M.FACES["Arial Bold Italic"])

    def test_bold_run_wraps_where_regular_does_not(self):
        """The PMR defect: a bold title measured with the regular face under-measured its lines."""
        w = M.width_in(TEXT, 14, ARIAL) * M.SLACK * 1.01
        self.assertEqual(len(M.wrap(TEXT, 14, ARIAL, w)), 1)
        self.assertEqual(len(M.wrap(TEXT, 14, BOLD, w)), 2)

    def test_montserrat_dual_metric(self):
        """Montserrat is measured at the wider of itself and Arial Bold (a client may substitute)."""
        for s in ("1,284", "37.5%", "Q3 2026"):
            for k in ("Montserrat", "Montserrat Medium", "Montserrat SemiBold", "Montserrat Bold"):
                self.assertGreaterEqual(M.width_in(s, 24, k), M.width_in(s, 24, BOLD) - 1e-12)
                own = M._units(s, k) * 24 / 72
                self.assertGreaterEqual(M.width_in(s, 24, k), own - 1e-12)
        self.assertIs(M.face_for("Montserrat SemiBold"), SEMI)
        self.assertIs(M.face_for("Montserrat SemiBold", bold=True), M.FACES["Montserrat Bold"])

    def test_unknown_face_raises(self):
        with self.assertRaises(UnknownFace):
            M.face_for("Calibri")
        with self.assertRaises(UnknownFace):
            M.fits([("x", 10, "Calibri")], (1, 1))

    def test_line_height_from_font_metrics_and_calibration(self):
        # Arial hhea: (1854 + 434 + 67) / 2048 = 1.1499; LibreOffice pitch fitted to 1.2 x pt.
        self.assertAlmostEqual(M._font_metrics(ARIAL).line_factor, 2355 / 2048, places=6)
        lh = M.line_in(10, ARIAL) * 72
        self.assertGreaterEqual(lh, 10 * 2355 / 2048 - 1e-9)
        self.assertLess(lh, 10 * 1.25)
        self.assertAlmostEqual(M.line_in(10, ARIAL, 1.5), M.line_in(10, ARIAL) * 1.5)


class Refusals(unittest.TestCase):
    def test_unbreakable_word_raises(self):
        word = "Interoperabilityassessment"
        with self.assertRaises(Overflows) as cm:
            M.wrap(word, 12, ARIAL, 1.0)
        self.assertIn(word, cm.exception.what)
        self.assertGreater(cm.exception.need, cm.exception.have)
        with self.assertRaises(Overflows) as cm:
            M.require_fit("card 2 body", [("Short " + word, 12, ARIAL)], (1.0, 5.0))
        self.assertTrue(cm.exception.what.startswith("card 2 body"))

    def test_hyphenated_word_breaks_at_the_hyphen(self):
        lines = M.wrap("end-to-end-traceability-review", 12, ARIAL, 1.2)
        self.assertGreater(len(lines), 1)
        self.assertEqual("".join(lines), "end-to-end-traceability-review")

    def test_below_floor_raises_never_clamps(self):
        with self.assertRaises(BelowFloor) as cm:
            M.wrap("label", 7.5, ARIAL, 2.0)
        self.assertEqual((cm.exception.need, cm.exception.have), (8.0, 7.5))
        with self.assertRaises(BelowFloor):
            M.fits([("label", 7.9, ARIAL)], (2.0, 1.0))
        with self.assertRaises(BelowFloor):
            M.capacity_words((2.0, 1.0), 7, ARIAL)
        self.assertEqual(M.wrap("label", 8.0, ARIAL, 2.0), ["label"])
        # a gate reading a foreign deck may measure sub-floor text by lowering the floor explicitly
        self.assertEqual(M.wrap("label", 7.5, ARIAL, 2.0, floor=0), ["label"])

    def test_require_fit_hint_names_words_to_cut_and_the_cut_fits(self):
        para = ("Regional teams review the plan and agree which accounts move first, then publish "
                "one shared view of demand and supply for every market before the review", 12, ARIAL)
        box = (2.5, M.line_in(12, ARIAL) * 3)
        with self.assertRaises(Overflows) as cm:
            M.require_fit("usecase body", [para], box)
        m = re.search(r"cut (\d+) of (\d+) words", cm.exception.hint)
        self.assertIsNotNone(m, cm.exception.hint)
        cut, total = int(m.group(1)), int(m.group(2))
        kept = " ".join(para[0].split()[:total - cut])
        self.assertTrue(M.fits([(kept, 12, ARIAL)], box).ok)
        one_more = " ".join(para[0].split()[:total - cut + 1])
        self.assertFalse(M.fits([(one_more, 12, ARIAL)], box).ok)


class Layout(unittest.TestCase):
    def test_need_height_counts_lines_spacing_and_insets(self):
        p = M.MPara((M.MRun("One line", 10, ARIAL),), space_before_pt=6, space_after_pt=3)
        ins = M.Insets(0.1, 0.05, 0.1, 0.05)
        need = M.need_height([p, p], 3.0, ins)
        self.assertAlmostEqual(need, 2 * M.line_in(10, ARIAL) + 2 * 9 / 72 + 0.10, places=9)

    def test_mixed_runs_wrap_as_one_paragraph(self):
        p = M.MPara((M.MRun("Demand ", 14, ARIAL), M.MRun("doubled", 14, BOLD),
                     M.MRun(" in two markets", 14, ARIAL)))
        f = M.fits([p], (10.0, 1.0))
        self.assertEqual(f.lines, ("Demand doubled in two markets",))
        self.assertTrue(f.ok)

    def test_hard_break_starts_a_line(self):
        self.assertEqual(M.wrap("first\nsecond", 10, ARIAL, 5.0), ["first", "second"])

    def test_duck_typed_runs(self):
        class R:
            def __init__(self, text, size, bold=False):
                self.text, self.size, self.bold, self.family = text, size, bold, "Arial"

        class P:
            def __init__(self, runs):
                self.runs = runs

        a = M.fits([P([R("Plan ", 12), R("first", 12, True)])], (4, 1))
        b = M.fits([M.MPara((M.MRun("Plan ", 12, ARIAL), M.MRun("first", 12, BOLD)))], (4, 1))
        self.assertEqual(a, b)
        with self.assertRaises(ValueError):
            M.fits([P([R("no size", None)])], (4, 1))


class Capacity(unittest.TestCase):
    def test_capacity_monotonic_in_box_size(self):
        sizes = [0.5, 0.8, 1.0, 1.5, 2.0, 2.7, 3.5, 5.0]
        for face in (ARIAL, BOLD, SEMI):
            for pt in (8, 10, 14):
                grid = [[M.capacity_words((w, h), pt, face) for h in sizes] for w in sizes]
                for i in range(len(sizes)):
                    for j in range(len(sizes)):
                        if i + 1 < len(sizes):
                            self.assertLessEqual(grid[i][j], grid[i + 1][j])
                        if j + 1 < len(sizes):
                            self.assertLessEqual(grid[i][j], grid[i][j + 1])
                self.assertGreater(grid[-1][-1], grid[0][0])

    def test_capacity_shrinks_with_larger_type(self):
        caps = [M.capacity_words((3.0, 2.0), pt, ARIAL) for pt in (8, 10, 12, 16, 24)]
        self.assertEqual(caps, sorted(caps, reverse=True))

    def test_capacity_is_a_fair_estimate(self):
        """Prose cut to the estimate fits the box it was estimated for, at 10pt in a 3 x 2 box."""
        n = M.capacity_words((3.0, 2.0), 10, ARIAL)
        prose = " ".join(((M.CAPACITY_SAMPLE + " ") * 10).split()[:n])
        f = M.fits([(prose, 10, ARIAL)], (3.0, 2.0))
        self.assertLessEqual(f.need_in, 2.0 * 1.10, f)


if __name__ == "__main__":
    unittest.main()
