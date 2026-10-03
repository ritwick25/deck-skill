"""The pass side of the gate rules the negatives prove from the fail side: what a rule must NOT flag.

Run: cd ~/.claude/skills/deck && $PY -m unittest tests.test_gate_rules -v

  * arrows: an enclosing panel is never the touch target; ends rank by edge distance (deckkit.read.connect.touch);
  * page numbers: every spelled-out form in a band is one, a digit on a filled marker or mid-slide is not;
  * figures: ranges and units are figures, ordinals and years are not, a digit in a disc is not;
  * P10: a neutral hairline (chroma under 0.10, thinner than 1.5pt) beside text is not an accent bar;
  * P22: a kit vendor mark whose key resolves passes in its own hue; the same picture hand-named icon.aws.* does not;
  * P12: PowerPoint's extension parts are SKIPPED and buSzPct 100000 is a known value, both printed, the deck passes;
  * P02: a shape whose measurement crashes is a finding on that shape and the gate goes on;
  * P18: an index holding only its canary entry is empty;
  * P24: a foot line under content that stops halfway never stretches the extent; the golden fills its band;
  * P25: text under an opaque shape drawn over it is noted, never measured;
  * P07: fitted frames agree on tops or on centres; a centre-anchored frame with room compares its centre;
  * P09: page labels count only in a page-number position.
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

    def test_resolving_vendor_marks_pass_without_a_hue_check(self):
        """A kit vendor mark keeps the vendor's own hue (AWS orange, Azure blue): the key resolves, so P22 passes.
        The same picture under a hand-placed icon.aws.* name is hue-checked and fails, so the pass is the rule."""
        from deckkit import icons
        from deckkit.canvas import Box
        keys = [next(k for k in icons.vendor_keys() if k.startswith(v + "/")) for v in ("aws", "azure", "gcp")]
        d = self.copy("vendor")

        def fn(prs):
            for j, k in enumerate(keys):
                icons.vendor(prs.slides[6], k, Box(10.4 + 0.7 * j, 5.6, 0.5, 0.5))
        negatives.with_prs(d, fn)
        code, found = run("P22", d)
        self.assertEqual(code, 0, [f.line() for f in found])
        legacy = self.copy("vendor-legacy")

        def fn2(prs):                                   # a blue mark: no identity colour is near it
            pic = icons.vendor(prs.slides[6], keys[1], Box(10.4, 5.6, 0.5, 0.5))
            pic._element.find(".//" + negatives.P + "cNvPr").set("name", "icon." + keys[1].replace("/", "."))
        negatives.with_prs(legacy, fn2)
        code, found = run("P22", legacy)
        self.assertEqual(code, 1)
        self.assertTrue(any("not in the theme identity registry" in f.msg for f in found), [f.line() for f in found])

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
        """Content mass, not a union box: every golden content slide reaches 85% of the band with 35% of it marked,
        and its mass runs to within an inch of the band's foot."""
        import p24_fill
        ctx = _shared.Ctx(self.deck)
        try:
            band = ctx.canvas.content
            for i in range(2, 7):
                extent, share, _n = p24_fill.measures(p24_fill.grid(ctx.slide(i), ctx))
                self.assertGreaterEqual(extent, p24_fill.EXTENT, i)
                self.assertGreaterEqual(share, p24_fill.SHARE, i)
                self.assertGreater(band.y + extent * band.h, band.y + band.h - 1.0, i)
        finally:
            ctx.close()

    def test_text_under_an_opaque_shape_is_not_measured(self):
        """White text with an opaque card drawn over it is not on glass: P25 notes it and passes."""
        d = self.copy("covered")
        from deckkit import prims
        from deckkit.canvas import Box
        th = negatives.theme()

        def fn(prs):
            negatives._add_text(prs, 7, (1.2, 4.8, 5.6, 0.3), "Pilot regions confirm by month end", 12.0, "hid.text")
            with prims.use(th):
                prims.card(prs.slides[6], Box(1.0, 4.6, 6.0, 1.0), fill="card", line="hairline", name="lid.card")
        negatives.with_prs(d, fn)
        negatives.edit_slide(d, 7, lambda r: negatives._recolour_runs(negatives.shape(r, "hid.text"), "FFFFFF"))
        code, found = run("P25", d)
        self.assertEqual(code, 0, [f.line() for f in found])
        self.assertTrue(any("under an opaque shape" in f.msg for f in found), [f.line() for f in found])


def tleaf(y, h, anchor="t", occ=1.0, autofit="none", w=1.0):
    return {"kind": "sp", "bbox": {"x_in": 0.0, "y_in": y, "w_in": w, "h_in": h},
            "text": {"text": "Heading", "words": 1, "occupancy": occ,
                     "body": {"anchor": anchor, "autofit": autofit}}}


class TestRowOffsets(unittest.TestCase):
    """P07 offsets: anchor-aware, with fitted frames judged by tops or by centres."""

    def test_fitted_frames_top_aligned_pass(self):
        import p07_row
        firsts = [tleaf(1.59, 0.52, "ctr", autofit="shape"), tleaf(1.60, 0.34, "ctr", autofit="shape")]
        self.assertLessEqual(p07_row.spread(firsts, [1.47, 1.47]), p07_row.HEAD_TOL)

    def test_fitted_frames_centred_pass(self):
        import p07_row
        firsts = [tleaf(4.90, 0.56, "ctr", autofit="shape"), tleaf(5.00, 0.37, "ctr", autofit="shape")]
        self.assertLessEqual(p07_row.spread(firsts, [4.77, 4.77]), p07_row.HEAD_TOL)

    def test_roomy_centre_anchored_frames_compare_centres(self):
        import p07_row
        same = [tleaf(1.0, 0.6, "ctr", occ=0.4), tleaf(0.9, 0.8, "ctr", occ=0.3)]     # centres both at 1.30
        self.assertLessEqual(p07_row.spread(same, [0.5, 0.5]), p07_row.HEAD_TOL)
        off = [tleaf(1.0, 0.6, "ctr", occ=0.4), tleaf(1.0, 0.9, "ctr", occ=0.3)]      # tops agree, centres 0.15 apart
        self.assertGreater(p07_row.spread(off, [0.5, 0.5]), p07_row.HEAD_TOL)

    def test_bottom_anchored_frames_compare_bottoms(self):
        import p07_row
        firsts = [tleaf(1.0, 0.6, "b", occ=0.4), tleaf(0.8, 0.8, "b", occ=0.4)]       # bottoms both at 1.60
        self.assertLessEqual(p07_row.spread(firsts, [0.5, 0.5]), p07_row.HEAD_TOL)


class TestFillGrid(unittest.TestCase):
    """P24 measures on synthetic grids: a three-cell foot line never stretches the extent."""

    def test_top_half_plus_a_foot_line_fails_extent(self):
        import p24_fill
        cells = [[r < 12 for _c in range(48)] for r in range(27)]
        cells[26][0:5] = [True] * 5
        extent, share, n = p24_fill.measures(cells)
        self.assertEqual(n, 12 * 48 + 5)
        self.assertAlmostEqual(extent, 12 / 27)
        self.assertLess(extent, p24_fill.EXTENT)

    def test_full_band_passes(self):
        import p24_fill
        cells = [[c % 2 == 0 for c in range(48)] for _r in range(27)]
        extent, share, _n = p24_fill.measures(cells)
        self.assertEqual(extent, 1.0)
        self.assertAlmostEqual(share, 0.5)


class TestPageLabels(unittest.TestCase):
    """P09 page labels: 'A1'..'A9', 'Appendix N' and 'N / M' in a page-number position, nowhere else."""
    W, H = 13.333, 7.5

    def lab(self, t, x, y, w=0.6, h=0.25, pt=10.0, fill="none"):
        import p09_chrome
        L = {"bbox": {"x_in": x, "y_in": y, "w_in": w, "h_in": h}, "fill": {"type": fill},
             "text": {"size": {"dominant_pt": pt}}}
        return p09_chrome.page_label(L, t, self.W, self.H)

    def test_in_position(self):
        for t in ("A1", "A9", "Appendix 2", "appendix 12", "2 / 34"):
            self.assertTrue(self.lab(t, 12.5, 7.05), t)             # bottom-right corner
            self.assertTrue(self.lab(t, 0.4, 0.14), t)              # top-left corner
        self.assertTrue(self.lab("A3", 6.37, 7.05))                 # centred at the foot

    def test_not_page_labels(self):
        self.assertFalse(self.lab("A3", 6.0, 3.5))                  # mid-slide: a grid reference
        self.assertFalse(self.lab("A3", 12.5, 7.05, fill="solid"))  # on its own tab
        self.assertFalse(self.lab("A3", 12.5, 7.05, pt=28.0))       # set large
        self.assertFalse(self.lab("A10", 12.5, 7.05))
        self.assertFalse(self.lab("Appendix", 12.5, 7.05))
        self.assertFalse(self.lab("A3", 4.0, 7.05))                 # in the band, neither a side nor the centre


if __name__ == "__main__":
    unittest.main()
