"""Fixtures for deckkit.read against the real reference decks (read-only), plus synthetic unit checks.

Run: cd ~/.claude/skills/deck && $PY -m unittest tests.test_read -v
Sources are opened read-only; the module asserts every source sha256 is unchanged at the end.
Expected values follow library/design/pipeline.md 3.8 as adjudicated in this suite (see each docstring).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "kit"))

from deckkit.read import deck_info, open_deck, para_text, read_slide, words  # noqa: E402
from deckkit.read.colour import apply_mods, contrast  # noqa: E402
from deckkit.read.deckinfo import font_words, status_ranges  # noqa: E402
from deckkit.read.ns import NS, A  # noqa: E402
from deckkit.read.xform import EMU_IN, IDENT, group_child_to_parent, leaf_geometry, read_xfrm  # noqa: E402
from deckkit.read.zones import slide_zones  # noqa: E402

LIB = "/Users/Nikunj/Codes/Decks-For-Visuals/library"
MANIFEST = json.load(open(os.path.join(LIB, "manifest.json")))
DECKS = MANIFEST["decks"]
REFERENCE = [k for k, v in DECKS.items() if v["tier"] == "reference"]

_D01 = {}


def d01():
    """The flagship opened once, every slide read once (timed for the performance check)."""
    if not _D01:
        deck = open_deck(DECKS["d01"]["path"])
        t = time.time()
        slides = [read_slide(deck, i) for i in range(1, deck.n_slides + 1)]
        _D01.update(deck=deck, slides=slides, seconds=time.time() - t)
    return _D01


def runs(slide, chrome=False):
    for L in slide["shapes"] + (slide["chrome"] if chrome else []):
        if L.get("text"):
            for p in L["text"]["paragraphs"]:
                for r in p["runs"]:
                    if r["t"].strip():
                        yield L, r


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------------------------- unit

class TestTokenizer(unittest.TestCase):
    def test_words(self):
        self.assertEqual(words("Long Range Supply & Capacity"), 4)        # '&' alone is not a word
        self.assertEqual(words("AI-native  pods, 5 core + 2 fractional"), 6)
        self.assertEqual(words(""), 0)
        self.assertEqual(words(" ".join(chr(c) for c in (0x2014, 0x2022)) + " ..."), 0)

    def test_mid_word_run_split(self):
        from lxml import etree
        p = etree.fromstring(
            '<a:p xmlns:a="%s"><a:r><a:t>L</a:t></a:r><a:r><a:t>eader board</a:t></a:r><a:br/>'
            '<a:fld type="slidenum"><a:t>7</a:t></a:fld></a:p>' % NS["a"])
        self.assertEqual(para_text(p), "Leader board\n7")
        self.assertEqual(words(para_text(p)), 3)


class TestColour(unittest.TestCase):
    def test_contrast(self):
        self.assertAlmostEqual(contrast("000000", "FFFFFF"), 21.0, places=2)
        self.assertAlmostEqual(contrast("FFFFFF", "FFFFFF"), 1.0, places=3)

    def test_epic_modifiers(self):
        """pipeline.md 3.7: bg1 lumMod 75000 = BFBFBF; accent1/accent2 at lumMod 20000 lumOff 80000."""
        deck = d01()["deck"]
        th = deck.master(deck.master_parts[0]).theme["colors"]
        self.assertEqual(apply_mods(th["lt1"], [("lumMod", 75000)]), "BFBFBF")
        self.assertEqual(apply_mods(th["accent1"], [("lumMod", 20000), ("lumOff", 80000)]), "FFCACC")
        self.assertEqual(apply_mods(th["accent2"], [("lumMod", 20000), ("lumOff", 80000)]), "FAE6D8")


class TestXform(unittest.TestCase):
    def test_rotated_nonuniform_group(self):
        """A 90-degree group with x scale 0.5: a child square becomes a 0.5 x 1.0 frame turned on its side."""
        g = dict(x=0, y=0, w=457200, h=914400, rot=90.0, fh=False, fv=False, chx=0, chy=0, chw=914400, chh=914400)
        M = group_child_to_parent(g)
        child = dict(x=0, y=0, w=914400, h=914400, rot=0.0, fh=False, fv=False)
        geo = leaf_geometry(child, M)
        bx, by, bw, bh = geo["bbox_in"]
        self.assertAlmostEqual(bw, 1.0, places=6)
        self.assertAlmostEqual(bh, 0.5, places=6)
        self.assertEqual(geo["group_scale"], (0.5, 1.0))
        self.assertAlmostEqual(geo["frame"]["rot_deg"], 90.0)

    def test_sheared_child(self):
        """A rotated child inside a non-uniformly scaled group is sheared in slide space."""
        g = dict(x=0, y=0, w=457200, h=914400, rot=0.0, fh=False, fv=False, chx=0, chy=0, chw=914400, chh=914400)
        child = dict(x=0, y=0, w=914400, h=914400, rot=45.0, fh=False, fv=False)
        self.assertTrue(leaf_geometry(child, group_child_to_parent(g))["frame"]["sheared"])

    def test_flip_endpoints(self):
        r = dict(x=0, y=0, w=914400, h=914400, rot=0.0, fh=True, fv=False)
        geo = leaf_geometry(r, IDENT)
        self.assertEqual(tuple(round(v, 6) for v in geo["start_in"]), (1.0, 0.0))
        self.assertEqual(tuple(round(v, 6) for v in geo["end_in"]), (0.0, 1.0))
        self.assertTrue(geo["frame"]["mirrored"])


class TestSyntheticPlaceholders(unittest.TestCase):
    """The corpus has no xfrm-less placeholders; python-pptx's default template writes them, so it is the fixture."""

    def test_inherited_geometry_and_txstyles(self):
        from pptx import Presentation
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "ph.pptx")
            prs = Presentation()
            s = prs.slides.add_slide(prs.slide_layouts[0])
            s.shapes.title.text = "Quarterly review"
            s.placeholders[1].text = "Subtitle words here"
            prs.save(path)
            with open_deck(path) as deck:
                sl = read_slide(deck, 1)
                lay = deck.layout(deck.layout_part_of(deck.slide_part(1)))
                lt = next(e for info, e in lay.ph.items if info["type"] == "ctrTitle")
                r = read_xfrm(lt.find("{http://schemas.openxmlformats.org/presentationml/2006/main}spPr")
                              .find(A("xfrm")))
        title = next(L for L in sl["shapes"] if (L["placeholder"] or {}).get("type") == "ctrTitle")
        self.assertEqual(title["placeholder"]["geom_from"], "layout")
        self.assertAlmostEqual(title["bbox"]["x_in"], round(r["x"] / EMU_IN, 3), places=3)
        self.assertAlmostEqual(title["bbox"]["w_in"], round(r["w"] / EMU_IN, 3), places=3)
        run = title["text"]["paragraphs"][0]["runs"][0]
        self.assertEqual(run["size_pt"], 44.0)                 # master titleStyle lvl1 sz 4400
        self.assertEqual(run["size_src"], "master_txStyles")
        self.assertEqual(run["font"], "Calibri")              # +mj-lt through the master theme
        self.assertEqual(run["font_requested"], "+mj-lt")
        self.assertEqual(title["role_guess"]["role"], "title")
        sub = next(L for L in sl["shapes"] if (L["placeholder"] or {}).get("type") == "subTitle")
        self.assertEqual(sub["role_guess"]["role"], "subtitle")


    def test_floor_reads_effective_size(self):
        """Planted negative: 10pt text shrunk by normAutofit fontScale 70% must count as a sub-8pt run."""
        from lxml import etree
        from pptx import Presentation
        from pptx.util import Inches, Pt
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "fs.pptx")
            prs = Presentation()
            s = prs.slides.add_slide(prs.slide_layouts[6])
            tb = s.shapes.add_textbox(Inches(1), Inches(1), Inches(3), Inches(1))
            tb.text_frame.text = "Shrunk caption text"
            tb.text_frame.paragraphs[0].runs[0].font.size = Pt(10)
            bp = tb.text_frame._txBody.find(A("bodyPr"))
            for c in list(bp):
                bp.remove(c)
            etree.SubElement(bp, A("normAutofit")).set("fontScale", "70000")
            prs.save(path)
            with open_deck(path) as deck:
                sl = read_slide(deck, 1)
        r = sl["shapes"][0]["text"]["paragraphs"][0]["runs"][0]
        self.assertEqual((r["size_pt"], r["size_rendered_pt"]), (10.0, 7.0))
        self.assertEqual(sl["text"]["runs_below_8pt"], 1)
        self.assertIn("sub-8pt", [h["kind"] for h in sl["hygiene"]])
        self.assertEqual(sl["fidelity"]["autofit_shrunk"], 1)


# ---------------------------------------------------------------------------------------------- fixtures

class TestCorpusTotals(unittest.TestCase):
    def test_slides_and_hidden(self):
        """583 slides, 79 hidden (d02 21, d09 7, d12 31, d13 20); every deck agrees with the manifest."""
        total = hidden = 0
        per = {}
        for k, v in DECKS.items():
            with open_deck(v["path"]) as deck:
                n = deck.n_slides
                h = [i for i in range(1, n + 1) if deck.xml(deck.slide_part(i)).get("show") in ("0", "false")]
            self.assertEqual(n, v["slides"], k)
            self.assertEqual(h, v["hidden"], k)
            total += n
            hidden += len(h)
            per[k] = len(h)
        self.assertEqual(total, 583)
        self.assertEqual(hidden, 79)
        self.assertEqual({k: n for k, n in per.items() if n}, {"d02": 21, "d09": 7, "d12": 31, "d13": 20})

    def test_every_slide_reads(self):
        """read_slide succeeds on every slide of every deck and emits the shapes@1 top-level keys."""
        keys = {"schema", "slide_id", "deck_id", "index", "part", "canvas", "hidden", "status", "layout",
                "show_master_shapes", "background", "shapes", "chrome", "groups", "text", "fidelity", "hygiene"}
        for k, v in DECKS.items():
            if k == "d01":
                continue
            with open_deck(v["path"]) as deck:
                for i in range(1, deck.n_slides + 1):
                    s = read_slide(deck, i)
                    self.assertEqual(set(s), keys, (k, i))
                    self.assertEqual(s["hidden"], i in v["hidden"], (k, i))
                    ids = [L["id"] for L in s["shapes"]]
                    self.assertEqual(len(ids), len(set(ids)), (k, i, "duplicate leaf ids"))


class TestD01(unittest.TestCase):
    def slide(self, i):
        return d01()["slides"][i - 1]

    def test_performance(self):
        """read_slide over all 135 d01 slides, cold (including the deck-wide font pass), in under 120 s."""
        sys.stderr.write("[d01 135 slides: %.1f s] " % d01()["seconds"])
        self.assertLess(d01()["seconds"], 120.0)

    def test_s15_title(self):
        """Shape 560 at 0.50, 0.13 in, 12.40 x 0.35 in; 21pt bold; two-tone with an accent1 run."""
        L = next(L for L in self.slide(15)["shapes"] if L["id"] == 560)
        b = L["bbox"]
        for got, want in ((b["x_in"], 0.50), (b["y_in"], 0.13), (b["w_in"], 12.40), (b["h_in"], 0.35)):
            self.assertLessEqual(abs(got - want), 0.01)
        rs = [r for p in L["text"]["paragraphs"] for r in p["runs"]]
        self.assertTrue(all(r["size_rendered_pt"] == 21.0 and r["bold"] for r in rs))
        self.assertTrue(L["text"]["two_tone"])
        self.assertTrue(any("scheme:accent1" in r["colour_src"] for r in rs))
        self.assertEqual(L["role_guess"]["role"], "title")

    def test_s57_pres_default(self):
        """A 14pt run on slide 57 whose size comes from the presentation default."""
        hits = [(L["id"], r) for L, r in runs(self.slide(57)) if r["size_src"] == "pres_default"]
        self.assertTrue(hits)
        self.assertTrue(all(r["size_pt"] == 14.0 for _, r in hits))
        self.assertIn(4, [i for i, _ in hits])

    def test_s50_group(self):
        """'Group 651' (cNvPr id 652): rot 90, own scale 0.4846 x 1.0, bbox computed by hand from off/ext."""
        g = next(g for g in self.slide(50)["groups"] if g["name"] == "Group 651")
        self.assertEqual(g["id"], 652)
        self.assertEqual(g["rot_deg"], 90.0)
        self.assertAlmostEqual(g["scale"][0], 0.4846, places=4)
        self.assertAlmostEqual(g["scale"][1], 1.0, places=4)
        # off (11025982, 4488532) ext (437161, 207358) turned 90 degrees about its centre
        cx, cy = 11025982 + 437161 / 2, 4488532 + 207358 / 2
        want = ((cx - 207358 / 2) / EMU_IN, (cy - 437161 / 2) / EMU_IN, 207358 / EMU_IN, 437161 / EMU_IN)
        got = (g["bbox"]["x_in"], g["bbox"]["y_in"], g["bbox"]["w_in"], g["bbox"]["h_in"])
        for a, b in zip(got, want):
            self.assertLessEqual(abs(a - b), 0.001)
        self.assertEqual(g["children"], [650, 651])

    def test_sub8pt_runs(self):
        """Effective size below 8pt: 1,275 of 6,566 non-blank content runs over 1-135; 799 of 4,449 over 1-104."""
        for lo, hi, want_b, want_n in ((1, 135, 1275, 6566), (1, 104, 799, 4449)):
            n = b = 0
            for s in d01()["slides"][lo - 1:hi]:
                for _L, r in runs(s):
                    n += 1
                    b += r["size_rendered_pt"] < 8.0
            self.assertLessEqual(abs(b - want_b), 0.01 * want_b, (lo, hi, b))
            self.assertLessEqual(abs(n - want_n), 0.01 * want_n, (lo, hi, n))
            self.assertEqual(sum(s["text"]["runs_below_8pt"] for s in d01()["slides"][lo - 1:hi]), b)

    def test_pictures(self):
        """22 svgBlip parts; 105 image layers (92 artisticPhotocopy) on 41 slides; ChatGPT title on 72, 118, 127, 131."""
        svg = layers = photocopy = 0
        layer_slides, chatgpt = set(), set()
        for s in d01()["slides"]:
            for L in s["shapes"]:
                p = L.get("picture")
                if not p:
                    continue
                svg += bool(p["svg_part"])
                if p["hdphoto_part"]:
                    layers += 1
                    layer_slides.add(s["index"])
                photocopy += p["artistic"].count("artisticPhotocopy")
                if re.search("chatgpt", L["title"], re.I):
                    chatgpt.add(s["index"])
                    self.assertEqual(p["ai_hint"].lower(), "chatgpt")
        self.assertEqual(svg, 22)
        self.assertEqual(layers, 105)
        self.assertEqual(photocopy, 92)
        self.assertEqual(len(layer_slides), 41)
        self.assertEqual(chatgpt, {72, 118, 127, 131})

    def test_connectors(self):
        """1,360 cxnSp; 328 glued at both ends. The '424' survey figure is glued at one end or more (377 + 375 - 328)."""
        cxn = [L for s in d01()["slides"] for L in s["shapes"] if L["kind"] == "cxn"]
        g = [L["connector"]["glue"] for L in cxn]
        self.assertEqual(len(cxn), 1360)
        self.assertEqual(sum(1 for x in g if x["start"] and x["end"]), 328)
        self.assertEqual(sum(1 for x in g if x["start"] or x["end"]), 424)
        self.assertEqual(sum(1 for x in g if x["start"]), 377)
        self.assertEqual(sum(1 for x in g if x["end"]), 375)
        # every connector carries a touch verdict at both ends
        self.assertTrue(all(L["connector"]["touch"]["start"] is not None for L in cxn))

    def test_status_ranges(self):
        """d01 1-104 is the narrative (dividers 103 APPENDIX and 104 GRAVEYARD included); 105-135 the graveyard."""
        sr = status_ranges(d01()["deck"])
        self.assertEqual(sr["main"], [[1, 104]])
        self.assertEqual(sr["graveyard"], [[105, 135]])
        self.assertEqual(self.slide(105)["status"], "graveyard")
        self.assertEqual(self.slide(104)["status"], "main")

    def test_zones_and_icons(self):
        z = slide_zones(self.slide(15))["zones"]
        self.assertGreaterEqual(len(z), 2)
        self.assertEqual(z[0]["id"], "Z1")
        self.assertIn(560, z[0]["ids"])            # the title opens the reading order

    def test_deck_info(self):
        info = deck_info(d01()["deck"], deck_id="d01", with_fonts=False)
        self.assertEqual(info["default_text_style"]["lvl1"], {"size_pt": 14.0, "font": "Arial", "bold": False,
                                                               "hex": "000000"})
        self.assertEqual(len(info["masters"]), 5)
        self.assertEqual(info["masters"][4]["theme"]["fonts"]["minor"], "Calibri")
        self.assertTrue(all(m["theme"]["fonts"]["minor"] == "Arial" for m in info["masters"][:4]))
        self.assertEqual(info["status_ranges"]["graveyard"], [[105, 135]])
        self.assertEqual(info["origin"]["guess"], "google-export")


class TestFontWords(unittest.TestCase):
    """Words by requested font. The survey figures (Calibri 9,106; Space Grotesk 5,858 +327 Light +49 Medium)
    were measured over the 14 reference decks with str.split() per a:r run and explicit rPr latin faces only.
    Under the ruled word definition, paragraph-joined, with the inheritance chain, the true figures differ;
    both are asserted so the adjudication stays reproducible."""

    @classmethod
    def setUpClass(cls):
        cls.ruled14, cls.ruled18 = {}, {}
        for k, v in DECKS.items():
            with open_deck(v["path"]) as deck:
                fw = font_words(deck)
            for f, n in fw.items():
                cls.ruled18[f] = cls.ruled18.get(f, 0) + n
                if k in REFERENCE:
                    cls.ruled14[f] = cls.ruled14.get(f, 0) + n

    def test_ruled_definition(self):
        r14, r18 = self.ruled14, self.ruled18
        self.assertEqual(r14.get("Calibri"), 8212)
        self.assertEqual(r14.get("Space Grotesk"), 5502)
        self.assertEqual(r14.get("Space Grotesk Light"), 328)
        self.assertEqual(r14.get("Space Grotesk Medium"), 272)    # 227 of these inherit from a layout placeholder
        self.assertEqual(r18.get("Calibri"), 10105)
        self.assertEqual(next(iter(sorted(r18, key=lambda f: -r18[f]))), "Arial")

    def test_legacy_survey_method_reproduces(self):
        """Characteriser, not a tokenizer used anywhere: re-runs the superseded survey method."""
        legacy = {}
        for k in REFERENCE:
            with open_deck(DECKS[k]["path"]) as deck:
                for i in range(1, deck.n_slides + 1):
                    for r in deck.xml(deck.slide_part(i)).iter(A("r")):
                        rpr = r.find(A("rPr"))
                        lat = rpr.find(A("latin")) if rpr is not None else None
                        t = r.find(A("t"))
                        f = lat.get("typeface") if lat is not None else None
                        legacy[f] = legacy.get(f, 0) + len(((t.text or "") if t is not None else "").split())
        self.assertEqual(legacy["Calibri"], 9106)
        self.assertEqual(legacy["Space Grotesk"], 5858)
        self.assertEqual(legacy["Space Grotesk Light"], 327)
        self.assertEqual(legacy["Space Grotesk Medium"], 49)


class TestZSourcesUntouched(unittest.TestCase):
    """A1: every source sha256 equals the manifest after the suite (runs last by name)."""

    def test_sha256(self):
        for k, v in DECKS.items():
            self.assertEqual(sha256(v["path"]), v["sha256"], k)


if __name__ == "__main__":
    unittest.main()
