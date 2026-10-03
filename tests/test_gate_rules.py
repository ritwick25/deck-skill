"""The pass side of the gate rules the negatives prove from the fail side: what a rule must NOT flag.

Run: cd ~/.claude/skills/deck && $PY -m unittest tests.test_gate_rules -v

  * arrows: an enclosing panel is never the touch target; ends rank by edge distance (deckkit.read.connect.touch);
  * page numbers: every spelled-out form in a band is one, a digit on a filled marker or mid-slide is not;
  * figures: ranges and units are figures, ordinals and years are not, a digit in a disc is not;
  * P10: a neutral hairline (chroma under 0.10, thinner than 1.5pt) beside text is not an accent bar;
  * P12: PowerPoint's extension parts are SKIPPED and buSzPct 100000 is a known value, both printed, the deck passes;
  * P02: a shape whose measurement crashes is a finding on that shape and the gate goes on;
  * P18: an index holding only its canary entry is empty.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(SKILL / "kit"))
sys.path.insert(0, str(SKILL / "gates"))
sys.path.insert(0, str(HERE))

import build_golden  # noqa: E402
from deckkit.read import connect as cx  # noqa: E402
from deckkit.read import figures  # noqa: E402
from deckkit.read.colour import chroma, is_neutral  # noqa: E402
from deckkit.read.walk import page_number_role  # noqa: E402

import _shared  # noqa: E402
import negatives  # noqa: E402
import run_all  # noqa: E402
from test_gates import Golden, run  # noqa: E402


def leaf(i, x, y, w, h, kind="sp", fill="solid", prst="rect"):
    return {"id": i, "kind": kind, "bbox": {"x_in": x, "y_in": y, "w_in": w, "h_in": h},
            "corners_in": [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], "geom": {"prst": prst},
            "fill": {"type": fill}, "line": {"type": "none"}}


class TestArrowTouch(unittest.TestCase):
    """A panel holding two cards and an arrow between them, as on the golden's process slide."""

    def setUp(self):
        self.leaves = [leaf(1, 0.0, 0.0, 10.0, 4.0),            # the panel
                       leaf(2, 0.5, 0.5, 3.0, 3.0),             # card A
                       leaf(3, 4.0, 0.5, 3.0, 3.0)]             # card B, 0.5in to the right of A

    def test_ends_land_on_the_cards_not_the_panel(self):
        s, e = (3.5, 2.0), (4.0, 2.0)
        st = cx.touch(s, self.leaves, 99, 100.0, other=e)
        en = cx.touch(e, self.leaves, 99, 100.0, other=s)
        self.assertEqual((st["id"], en["id"]), (2, 3))
        self.assertTrue(st["ok"] and en["ok"])

    def test_an_end_short_of_its_card_fails_inside_the_panel(self):
        s, e = (3.5, 2.0), (3.7, 2.0)                           # 0.3in short of card B, deep inside the panel
        en = cx.touch(e, self.leaves, 99, 100.0, other=s)
        self.assertFalse(en["ok"], en)
        self.assertNotEqual(en["id"], 1)

    def test_an_arrowhead_drawn_onto_its_target_touches(self):
        s, e = (3.5, 2.0), (4.4, 2.0)                           # 0.4in into card B
        en = cx.touch(e, self.leaves, 99, 100.0, other=s)
        self.assertEqual(en["id"], 3)
        self.assertTrue(en["ok"] and en["inside"])

    def test_without_the_other_end_nothing_is_excluded(self):
        self.assertIn(cx.touch((3.7, 2.0), self.leaves, 99, 100.0)["id"], (1, 2, 3))


class TestPageNumbers(unittest.TestCase):
    W, H = 13.333, 7.5

    def role(self, t, x, y, w=1.0, h=0.25, sz=10.0, marker=False):
        r = page_number_role(t, sz, {"x_in": x, "y_in": y, "w_in": w, "h_in": h}, self.W, self.H, marker=marker)
        return r and r["role"]

    def test_spelled_out_forms_in_a_band(self):
        for t in ("2 / 34", "2/34", "2 of 34", "2 | 34", "2|34", "Page 2", "page 2 of 34", "p. 12", "Slide 3"):
            self.assertEqual(self.role(t, 11.7, 0.14), "page-number", t)
            self.assertEqual(self.role(t, 0.5, 7.05), "page-number", t)

    def test_not_page_numbers(self):
        self.assertIsNone(self.role("2 / 34", 5.0, 3.5))                 # mid-slide: a fraction or a score
        self.assertIsNone(self.role("2 / 34", 11.7, 0.14, sz=28.0))      # set large: a figure
        self.assertIsNone(self.role("3", 12.6, 7.05, marker=True))       # a digit on its own disc or tab
        self.assertIsNone(self.role("Phase 2", 11.7, 0.14))
        self.assertEqual(self.role("3", 12.6, 7.05), "page-number")      # the bare corner number still is


class TestFigures(unittest.TestCase):
    def test_figures(self):
        for t in ("42%", "5 to 10%", "+6 to 7%", "$4.2M", "3x", "2,000+", "~$18" + chr(0x2013) + "21M", "EUR 5bn",
                  "250", "10 to 20%", "-12%", "1.8k"):
            self.assertTrue(figures.is_figure(t), t)

    def test_not_figures(self):
        for t in ("01", "03", "007", "2026", "1999", "PHASE 1", "Q3", "Step 2", "Wave two", ""):
            self.assertFalse(figures.is_figure(t), t)

    def _slide(self, extra):
        base = [{"id": k, "text": {"text": "Body copy here", "size": {"dominant_pt": 11.0}}, "bbox":
                 {"x_in": 0.0, "y_in": k, "w_in": 3.0, "h_in": 0.3}, "fill": {"type": "none"}} for k in range(1, 6)]
        return {"shapes": base + extra}

    def test_a_digit_in_a_disc_is_an_ordinal(self):
        disc = {"id": 9, "text": {"text": "1", "size": {"dominant_pt": 16.5}}, "fill": {"type": "solid"},
                "bbox": {"x_in": 6.0, "y_in": 1.0, "w_in": 0.55, "h_in": 0.55}}
        self.assertEqual(figures.large_figures(self._slide([disc])), [])
        loose = dict(disc, fill={"type": "none"}, id=10)
        self.assertEqual([L["id"] for L, _r in figures.large_figures(self._slide([loose]))], [10])

    def test_bare_numbers_on_a_divider_are_section_numerals(self):
        n = {"id": 9, "text": {"text": "3", "size": {"dominant_pt": 66.0}}, "fill": {"type": "none"},
             "bbox": {"x_in": 1.0, "y_in": 2.0, "w_in": 1.0, "h_in": 1.0}}
        self.assertEqual(figures.large_figures(self._slide([n]), divider=True), [])
        self.assertEqual(len(figures.large_figures(self._slide([n]), divider=False)), 1)


class TestNeutral(unittest.TestCase):
    def test_chroma(self):
        self.assertLess(chroma("DDE4F6"), 0.10)          # a pale tint reads grey
        self.assertTrue(is_neutral("D9D9D9"))
        self.assertFalse(is_neutral("2E8BFF"))
        self.assertFalse(is_neutral("D91E18"))


class TestPassSide(Golden):
    def test_neutral_hairline_beside_text_is_not_a_bar(self):
        d = self.copy("hair")
        from deckkit.canvas import Box
        from deckkit import ooxml, prims

        def fn(prs):
            s = prs.slides[1]
            body = next(sh for sh in s.shapes if sh.name == "pillar.1.text.2")
            x, y, w = body.left / negatives.EMU, body.top / negatives.EMU, body.width / negatives.EMU
            bar = prims._add(s, "RECTANGLE", Box(x, y - 0.06, w, 0.01), "pale.rule")
            bar.fill.solid()
            from pptx.dml.color import RGBColor
            bar.fill.fore_color.rgb = RGBColor.from_string("DDE4F6")
            bar.line.fill.background()
            prims._drop_text(bar)
            ooxml.finish(bar)
        negatives.with_prs(d, fn)
        code, found = run("P10", d)
        self.assertEqual(code, 0, [f.line() for f in found])

    def test_extension_parts_skipped_and_known_bullet_size(self):
        d = self.copy("ext")
        negatives._authors_part(d)

        def fn(r):
            para = negatives.shape(r, "pillar.1.text.2").find(".//" + negatives.A + "p")
            ppr = para.find(negatives.A + "pPr")
            from lxml import etree
            bu = etree.Element(negatives.A + "buSzPct", val="100000")
            later = [c for c in ppr if etree.QName(c).localname in ("buFont", "buNone", "buChar", "tabLst", "defRPr")]
            (later[0].addprevious(bu) if later else ppr.append(bu))
        negatives.edit_slide(d, 2, fn)
        code, found = run("P12", d)
        self.assertEqual(code, 0, [f.line() for f in found])
        notes = [f.where + " " + f.msg for f in found if f.level == "note"]
        self.assertTrue(any("ppt/authors.xml SKIPPED" in n for n in notes), notes)
        self.assertTrue(any("buSzPct 100000" in n for n in notes), notes)

    def test_a_crashing_shape_is_a_finding_and_the_gate_goes_on(self):
        d = self.copy("crash")
        negatives.p02_words(d, d.parent)                  # a real overflow on slide 2, pillar.2.text.2
        real = _shared.need_in

        def flaky(ctx, i, L, slack, unknown=None):
            if L["name"] == "pillar.1.text.2":
                raise RuntimeError("planted")
            return real(ctx, i, L, slack, unknown)
        import p02_fit
        with mock.patch.object(p02_fit, "need_in", flaky):
            code, found = run("P02", d)
        msgs = [f.where + ": " + f.msg for f in found if f.level == "fail"]
        self.assertEqual(code, 1)
        self.assertTrue(any(m.startswith("pillar.1.text.2: could not check: RuntimeError") for m in msgs), msgs)
        self.assertTrue(any(m.startswith("pillar.2.text.2: needs") for m in msgs), msgs)

    def test_an_index_holding_only_its_canary_is_empty(self):
        refs = Path(tempfile.mkdtemp(prefix="refs-", dir=self.tmp))
        src = SKILL / "devices" / "refs"
        for f in src.iterdir():
            if f.is_file() and f.name != "names.sha1":
                os.symlink(f, refs / f.name)
        canary = json.loads((src / "canary.json").read_text(encoding="utf-8"))
        (refs / "names.sha1").write_text("\n".join(canary["names_sha1"]) + "\n", encoding="utf-8")
        code, found = run("P18", self.deck, refs_dir=str(refs))
        self.assertEqual(code, 1)
        self.assertTrue(any("names.sha1 holds only its canary" in f.msg for f in found), [f.line() for f in found])

    def test_every_golden_content_slide_fills_its_band(self):
        import p24_fill
        ctx = _shared.Ctx(self.deck)
        try:
            band = ctx.canvas.content
            for i in range(2, 7):
                l, t, r, b = p24_fill.content_box(ctx.slide(i), ctx)
                self.assertGreaterEqual((b - t) / band.h, p24_fill.EXTENT, i)
        finally:
            ctx.close()


if __name__ == "__main__":
    unittest.main()
