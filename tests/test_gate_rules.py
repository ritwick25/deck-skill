"""The pass side of the gate rules the negatives prove from the fail side: what a rule must NOT flag.

Run: cd ~/.claude/skills/deck && $PY -m unittest tests.test_gate_rules -v

  * arrows: an enclosing panel is never the touch target; ends rank by edge distance (deckkit.read.connect.touch);
  * page numbers: every spelled-out form in a band is one, a digit on a filled marker or mid-slide is not;
  * figures: ranges and units are figures, ordinals and years are not, a digit in a disc is not;
  * P10: a strip under 1.5pt or a line under 2pt beside text is a divider, never a bar; a 2pt line longer than 1.5x
    its block's height is a reference line; undirected links between two tiles argue the slide;
  * P04/P05: text is judged by its ink box, so a frame past its card or across another frame is not a defect;
  * P06: an end under an opaque shape painted above is skipped; an end on another line is a junction;
  * P17: a banned word inside a URL is not prose; 'WIP' before a capitalised noun is a work-in-process term;
  * P22: a kit vendor mark whose key resolves passes in its own hue; the same picture hand-named icon.aws.* does not;
    a picture captioned as a vendor mark whose bytes are not that key's resource fails;
  * P12: PowerPoint's extension parts are SKIPPED and buSzPct 100000 is a known value, both printed, the deck passes;
  * P02: a shape whose measurement crashes is a finding on that shape and the gate goes on;
  * P18: an index holding only its canary entry is empty;
  * P24: a foot line under content that stops halfway never stretches the extent; the golden fills its band; the
    main mass bridges a one-cell gutter and stops at an empty band row; an untagged slide 1 is a frame;
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

        # a mark whose own hue no identity colour is near (ruling 18 registered the AWS and Azure notation colours,
        # so the first Azure mark, Azure blue, now has one): the hand-placed name is hue-checked and fails
        import p22_icons
        from deckkit.theme import Theme, delta_e00
        ids = [v["hex"] for v in Theme.load(negatives.THEME).identity.values()]
        far = next(k for k in icons.vendor_keys() if k.startswith(("azure/", "gcp/", "aws/"))
                   and (lambda h: h and all(delta_e00(h, i) >= p22_icons.HUE_DE for i in ids))(
                       p22_icons._dominant(icons.vendor_path(k).read_bytes())))

        def fn2(prs):
            pic = icons.vendor(prs.slides[6], far, Box(10.4, 5.6, 0.5, 0.5))
            pic._element.find(".//" + negatives.P + "cNvPr").set("name", "icon." + far.replace("/", "."))
        negatives.with_prs(legacy, fn2)
        code, found = run("P22", legacy)
        self.assertEqual(code, 1)
        self.assertTrue(any("not in the theme identity registry" in f.msg for f in found), [f.line() for f in found])

    def test_vendor_marks_are_checked_by_their_bytes(self):
        """Name and alt text can be typed onto any picture: P22 compares the blob's sha256 with the table, so the
        round-4 forgeries (an off-palette PNG, another key's genuine mark) fail and the kit's own mark passes."""
        from deckkit import icons
        cases = {"off-palette": negatives.png(300, 300, seed=11),
                 "other-key": icons.vendor_path("gcp/analytics/bigquery").read_bytes()}
        for label, blob in cases.items():
            d = self.copy("forged-" + label)
            negatives.with_prs(d, lambda prs, b=blob: negatives.add_picture(
                prs, 7, b, (11.0, 5.5, 0.5, 0.5), "vendor.aws/compute/ec2", "Ec2 (vendor mark aws/compute/ec2)"))
            code, found = run("P22", d)
            self.assertEqual(code, 1, label)
            self.assertTrue(any("renamed as a vendor mark" in f.msg for f in found), [f.line() for f in found])
        for name in ("vendor-forged", "vendor-forged2"):
            probe = SKILL / ".cache" / "vb3" / (name + ".pptx")
            if probe.is_file():
                code, found = run("P22", probe)
                self.assertEqual(code, 1, name)
                self.assertTrue(any(f.where.startswith("vendor.") and "renamed" in f.msg for f in found), name)

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
                extent, share, _n = p24_fill.measures(p24_fill.grid(ctx.slide(i), ctx),
                                                      p24_fill.grid(ctx.slide(i), ctx, drawn_only=True))
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


class TestRulings(Golden):
    """The pass side of the 2026-10-03 gate rulings: what each fix must stop flagging."""

    def _body(self, prs):
        s = prs.slides[1]
        return s, next(sh for sh in s.shapes if sh.name == "pillar.1.text.2")

    def _assert_pass(self, gid, d, slide=None):
        code, found = run(gid, d)
        fails = [f for f in found if f.level == "fail" and (slide is None or f.slide == slide)]
        self.assertEqual(fails, [], [f.line() for f in fails])

    def test_strips_under_the_floor_are_dividers(self):
        d = self.copy("divider")
        negatives._strip_beside_body(d, 0.01, "D91E18", "accent.hair")        # 0.72pt, the old thin-accent-bar
        negatives._line_beside_body(d, 1.0, "accent.rule", gap_in=0.20)        # 1pt, the old thin-accent-line
        self._assert_pass("P10", d)

    def test_a_reference_line_is_not_a_bar(self):
        d = self.copy("refline")
        negatives._line_beside_body(d, 2.25, "chart.ref", span=1.6)           # longer than 1.5x the block
        self._assert_pass("P10", d)

    def test_a_grey_strip_is_not_a_bar(self):
        d = self.copy("greystrip")
        negatives._strip_beside_body(d, 0.05, "4A4F55", "grey.strip")         # HLS saturation 0.07
        self._assert_pass("P10", d)

    def test_undirected_links_between_tiles_argue_the_slide(self):
        from pptx.dml.color import RGBColor
        from pptx.enum.shapes import MSO_CONNECTOR
        from pptx.util import Pt
        d = self.copy("links")
        negatives.p10_no_device(d, None)

        def fn(prs):
            s = prs.slides[1]
            cards = [next(sh for sh in s.shapes if sh.name == "pillar.%d.card" % k) for k in (1, 2, 3)]
            for k, (a, b) in enumerate(zip(cards, cards[1:])):
                y = a.top + a.height // 2
                ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, a.left + a.width, y, b.left, y)
                ln.name = "link.%d" % k
                ln.line.color.rgb = RGBColor.from_string("BFBFBF")
                ln.line.width = Pt(0.75)
        negatives.with_prs(d, fn)
        code, found = run("P10", d)
        self.assertFalse(any("nothing drawn" in f.msg for f in found), [f.line() for f in found])

    def test_a_frame_past_its_card_with_ink_inside_passes_p04(self):
        d = self.copy("inkpad")

        def fn(prs):
            from deckkit import text
            from deckkit.canvas import Box
            from deckkit.text import Para, Run
            s = prs.slides[1]
            card = next(sh for sh in s.shapes if sh.name == "pillar.1.card")
            x, y, cw = card.left / negatives.EMU, card.top / negatives.EMU, card.width / negatives.EMU
            text.textbox(s, Box(x + 0.3, y + 0.9, cw, 0.3), [Para(Run("Weekly", role="ink"))], "wide.frame",
                         negatives.theme(), size=11.0, require_fit=False)          # the frame runs 0.3in past
        negatives.with_prs(d, fn)
        self._assert_pass("P04", d)

    def test_crossing_frames_with_apart_ink_pass_p05(self):
        d = self.copy("inkapart")
        negatives.with_prs(d, lambda prs: (
            negatives._add_text(prs, 7, (0.6, 5.00, 4.0, 0.3), "Pilot regions", 11.0, "ink.a"),
            negatives._add_text(prs, 7, (2.4, 5.06, 4.0, 0.3), "Weekly", 11.0, "ink.b")))
        self._assert_pass("P05", d)

    def test_a_loose_chevron_row_nests(self):
        d = self.copy("looserow")
        negatives.loose_chevrons(d, 0.25)                                       # exactly the 0.5 x 0.5in point
        self._assert_pass("P05", d)

    def test_an_end_under_an_opaque_cover_painted_above_is_skipped(self):
        d = self.copy("hidden")
        negatives.p06_arrow(d, None)
        negatives._cover_arrow(d, "lid.card")
        self._assert_pass("P06", d)

    def test_an_end_on_another_line_is_a_junction(self):
        from pptx.dml.color import RGBColor
        from pptx.enum.shapes import MSO_CONNECTOR
        from pptx.util import Pt
        d = self.copy("junction")
        negatives.p06_arrow(d, None)

        def fn(prs):
            s = prs.slides[2]
            x = int(negatives.ARROW_END[0] * negatives.EMU)
            ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x, int(3.9 * negatives.EMU), x,
                                        int(4.6 * negatives.EMU))
            ln.name = "bus.line"
            ln.line.color.rgb = RGBColor.from_string("BFBFBF")
            ln.line.width = Pt(0.75)
        negatives.with_prs(d, fn)
        self._assert_pass("P06", d)

    def test_urls_and_wip_terms_are_not_prose(self):
        d = self.copy("urls")

        def fn(r):
            t = negatives.first_run(negatives.shape(r, "pillar.1.text.2")).find(negatives.A + "t")
            t.text = ("Source: example.com/blogs/" + "unlock" + "ing-capacity and https://example.org/" + "lever" +
                      "age, WIP Storage and WIP Aging")
        negatives.edit_slide(d, 2, fn)
        self._assert_pass("P17", d)

    def test_strip_urls(self):
        import p17_fingerprints as g
        for raw in ("iqvia.com/locations/blogs/2025/11/unlocking-x", "https://a.b/c?d=e", "www.example.com"):
            self.assertEqual(g.strip_urls(raw).strip(), "", raw)
        for keep in ("e.g. the plan", "fabric.catalog.asset_index", "3.5% of 1.2M"):
            self.assertEqual(g.strip_urls(keep), keep)

    def test_an_untagged_cover_is_a_frame(self):
        d = self.copy("untagged-cover")
        m = negatives.members(d)
        m.pop("docProps/custom.xml")
        negatives.write(d, m)
        for i in range(1, 8):
            negatives.edit_slide(d, i, lambda r: r.find("{*}cSld").attrib.pop("name", None))
        negatives.with_prs(d, lambda prs: negatives._add_text(
            prs, 1, (0.5, 1.0, 12.0, 0.6), " ".join(negatives.FILLER[:24]), 12.0, "cover.lede"))
        code, found = run("P24", d)
        self.assertFalse([f for f in found if f.slide == 1], [f.line() for f in found])


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

    def test_a_foot_sentence_below_an_empty_row_is_not_mass(self):
        """Top 12 rows full, an empty band row, then a full-width two-row sentence at the foot: excluded, however
        wide it runs (it is 14% of the marked cells, well past the 3% tail)."""
        import p24_fill
        cells = [[r < 12 for _c in range(48)] for r in range(27)]
        for r in (24, 25):
            cells[r] = [True] * 48
        extent, share, n = p24_fill.measures(cells)
        self.assertEqual(n, 14 * 48)
        self.assertAlmostEqual(extent, 12 / 27)
        self.assertLess(extent, p24_fill.EXTENT)

    def test_one_cell_gutters_never_split_the_mass(self):
        import p24_fill
        cells = [[c % 16 != 15 for c in range(48)] for _r in range(27)]          # three columns, gutters of one cell
        mm = p24_fill.main_mass(cells)
        self.assertEqual(sum(map(sum, mm)), sum(map(sum, cells)))
        extent, _share, _n = p24_fill.measures(cells)
        self.assertEqual(extent, 1.0)

    def test_a_tall_block_below_an_empty_row_is_still_mass(self):
        """Only a thin foot is a sentence: a four-row block under an empty row counts."""
        import p24_fill
        cells = [[r < 12 for _c in range(48)] for r in range(27)]
        for r in (23, 24, 25, 26):
            cells[r] = [True] * 48
        extent, _share, _n = p24_fill.measures(cells)
        self.assertEqual(extent, 1.0)

    def test_a_drawn_band_at_the_foot_is_mass(self):
        """Ten rows of content and three full foot rows (23% of the marked cells, so the 85% main mass needs them):
        as text alone they are a foot sentence and left out; drawn as a band (a filled box) they are mass."""
        import p24_fill
        cells = [[r < 10 for _c in range(48)] for r in range(27)]
        for r in (24, 25, 26):
            cells[r] = [True] * 48
        text_only, _s, _n = p24_fill.measures(cells)
        self.assertAlmostEqual(text_only, 10 / 27)
        drawn = [[r >= 24 for _c in range(48)] for r in range(27)]
        extent, _share, _n = p24_fill.measures(cells, drawn)
        self.assertEqual(extent, 1.0)

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
