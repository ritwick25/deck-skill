"""deckkit.geom and deckkit.clone, against the read-only flagship reference and synthetic fixtures.

Run: cd ~/.claude/skills/deck && $PY -m unittest tests.test_geom_clone -v
The source deck is opened read-only with python-pptx; plants (alt text, links, custom data) are made in
memory and never saved. The module asserts the source sha256 is unchanged at the end.
"""
from __future__ import annotations

import glob
import hashlib
import os
import posixpath
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "kit"))

from lxml import etree  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.chart.data import CategoryChartData  # noqa: E402
from pptx.enum.chart import XL_CHART_TYPE  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402
from pptx.opc.constants import RELATIONSHIP_TYPE as RT  # noqa: E402
from pptx.opc.package import Part  # noqa: E402
from pptx.opc.packuri import PackURI  # noqa: E402
from pptx.util import Inches, Pt  # noqa: E402

from deckkit import clone, geom  # noqa: E402
from deckkit.errors import GeometryError, UnsupportedPart  # noqa: E402
from deckkit.read import open_deck, read_slide  # noqa: E402
from deckkit.read.ns import NS, A, P, qn  # noqa: E402
from deckkit.read.xform import group_child_to_parent, read_xfrm  # noqa: E402

D01 = os.path.expanduser("~/Codes/Decks-For-Visuals/library/_work/src/d01.pptx")
R_NS = "{%s}" % NS["r"]
PY = sys.executable
_SHA0 = None
_TMP = tempfile.TemporaryDirectory(prefix="deckkit-geom-clone-")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def setUpModule():
    global _SHA0
    _SHA0 = sha256(D01)


def tearDownModule():
    try:
        assert sha256(D01) == _SHA0, "the read-only source changed during the suite"
    finally:
        _TMP.cleanup()


def _near(a, b, tol=0.0015):
    return abs(a - b) <= tol


def _pts(g):
    """Painted points independent of how a flip/rotation pair is spelled: sorted corners plus path ends."""
    return sorted((round(x, 4), round(y, 4)) for x, y in g.corners) + [tuple(round(v, 4) for v in g.start),
                                                                         tuple(round(v, 4) for v in g.end)]


def blank_prs(w_emu=12192000, h_emu=6858000):
    prs = Presentation()
    prs.slide_width, prs.slide_height = w_emu, h_emu
    return prs


def blank_slide(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    for sh in list(s.shapes):
        sh._element.getparent().remove(sh._element)
    return s


def add_group(slide, children, off, ext, ch_off, ch_ext, rot=0, name="G"):
    """A raw grpSp with the given transform; children are (name, x, y, w, h, rot) in child space."""
    tree = slide.shapes._spTree
    g = etree.SubElement(tree, P("grpSp"))
    nv = etree.SubElement(g, P("nvGrpSpPr"))
    etree.SubElement(nv, P("cNvPr"), id=str(900 + len(tree)), name=name)
    etree.SubElement(nv, P("cNvGrpSpPr"))
    etree.SubElement(nv, P("nvPr"))
    gp = etree.SubElement(g, P("grpSpPr"))
    x = etree.SubElement(gp, A("xfrm"))
    if rot:
        x.set("rot", str(int(rot * 60000)))
    etree.SubElement(x, A("off"), x=str(off[0]), y=str(off[1]))
    etree.SubElement(x, A("ext"), cx=str(ext[0]), cy=str(ext[1]))
    etree.SubElement(x, A("chOff"), x=str(ch_off[0]), y=str(ch_off[1]))
    etree.SubElement(x, A("chExt"), cx=str(ch_ext[0]), cy=str(ch_ext[1]))
    for i, (nm, cx_, cy_, cw, chh, crot) in enumerate(children):
        sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx_, cy_, cw, chh)
        sh.name = nm
        if crot:
            sh.rotation = crot
        sh.text_frame.text = nm
        sh.text_frame.paragraphs[0].runs[0].font.size = Pt(18)  # an explicit size baking must not touch
        g.append(sh._element)
    return g


def audit_package(path):
    """Package-level facts of every slide: unresolved r:* ids, missing rel targets, duplicate ids, banned
    leftovers, svg content types. Read straight from the zip, not through python-pptx."""
    z = zipfile.ZipFile(path)
    names = set(z.namelist())
    ct = z.read("[Content_Types].xml").decode()
    out = {"dangling": [], "missing_target": [], "dup_ids": [], "banned": [], "svg_ct_ok": True, "svg": 0,
           "svg_without_png": 0, "pics": 0, "glue": []}
    for n in sorted(names):
        m = re.match(r"ppt/slides/(slide\d+)\.xml$", n)
        if not m:
            continue
        x = etree.fromstring(z.read(n))
        rels_name = f"ppt/slides/_rels/{m.group(1)}.xml.rels"
        rels = {}
        if rels_name in names:
            for r in etree.fromstring(z.read(rels_name)):
                rels[r.get("Id")] = r
                if r.get("TargetMode") != "External":
                    tgt = posixpath.normpath(posixpath.join("ppt/slides", r.get("Target")))
                    if tgt not in names:
                        out["missing_target"].append((n, r.get("Id"), tgt))
                    if tgt.endswith(".svg"):
                        out["svg"] += 1
                        if not re.search(r'(PartName="/%s" ContentType="image/svg\+xml")|'
                                         r'(Extension="svg" ContentType="image/svg\+xml")' % re.escape(tgt), ct):
                            out["svg_ct_ok"] = False
        for e in x.iter():
            if not isinstance(e.tag, str):
                continue
            for k, v in e.attrib.items():
                if k.startswith(R_NS) and v and v not in rels:
                    out["dangling"].append((n, etree.QName(e).localname, v))
        ids = [c.get("id") for c in x.iter(P("cNvPr"))]
        out["dup_ids"] += [(n, i) for i in set(ids) if ids.count(i) > 1]
        for tag in (A("hlinkClick"), A("hlinkHover"), A("hlinkMouseOver"), P("custDataLst"), qn("a14:imgProps"),
                    qn("mc:AlternateContent")):
            out["banned"] += [(n, etree.QName(tag).localname) for _ in x.iter(tag)]
        for c in x.iter(P("cNvPr")):
            for attr in ("descr", "title"):
                if c.get(attr):
                    out["banned"].append((n, attr))
        for blip in x.iter(A("blip")):
            if blip.find(f"{A('extLst')}/{A('ext')}/{qn('asvg:svgBlip')}") is not None and not blip.get(R_NS + "embed"):
                out["svg_without_png"] += 1
        out["pics"] += len(list(x.iter(P("pic"))))
        valid = set(ids)
        for tag in ("stCxn", "endCxn"):
            for g in x.iter(A(tag)):
                out["glue"].append((n, tag, g.get("id"), g.get("id") in valid))
    return out


def validator():
    hits = sorted(glob.glob(os.path.expanduser("~/.claude/skills/synced/*/pptx/scripts/office/validate.py")))
    if not hits:
        raise AssertionError("XSD validator not found under ~/.claude/skills/synced/*/pptx/scripts/office/; "
                             "validation FAILS rather than passing structure-only")
    return hits[0]


def xsd_validate(path):
    v = validator()
    p = subprocess.run([PY, v, path], cwd=os.path.dirname(v), capture_output=True, text=True, timeout=300)
    return p.returncode, (p.stdout + p.stderr)


# ======================================================================== geometry on the reference

class GeomOnReference(unittest.TestCase):
    """abs_box and iter_abs agree with deckkit.read on the flagship, group children included."""

    @classmethod
    def setUpClass(cls):
        cls.prs = Presentation(D01)
        cls.deck = open_deck(D01)

    def test_group_651_rotated_non_uniform(self):
        """Slide 50 'Group 651' (id 652): rot 90 with chExt 902124 onto ext 437161, so x scale 0.4846 and y 1.0.
        Its absolute box and both children's boxes, rotations and mirroring match the read layer."""
        s = self.prs.slides[49]
        g = geom.find(s, 652)
        self.assertEqual(g.name, "Group 651")
        self.assertIs(geom.find(s, "Group 651")._element, g._element)
        r = read_xfrm(geom._xfrm_el(g._element))
        self.assertAlmostEqual(r["rot"], 90.0)
        self.assertAlmostEqual(r["w"] / r["chw"], 0.4846, places=4)
        self.assertAlmostEqual(r["h"] / r["chh"], 1.0)
        rd = read_slide(self.deck, 50)
        grp = next(x for x in rd["groups"] if x["id"] == 652)
        ab = geom.abs_box(g)
        for k, v in (("x_in", ab.x), ("y_in", ab.y), ("w_in", ab.w), ("h_in", ab.h)):
            self.assertTrue(_near(grp["bbox"][k], v), (k, grp["bbox"][k], v))
        self.assertEqual(grp["children"], [650, 651])
        leaves = {L["id"]: L for L in rd["shapes"]}
        for cid in (650, 651):
            mine = geom.abs_box(geom.find(s, cid))
            L = leaves[cid]
            for k, v in (("x_in", mine.x), ("y_in", mine.y), ("w_in", mine.w), ("h_in", mine.h)):
                self.assertTrue(_near(L["bbox"][k], v), (cid, k, L["bbox"][k], v))
            self.assertAlmostEqual(L["frame"]["rot_deg"], mine.rot_deg, places=2)
            self.assertEqual(L["frame"]["mirrored"], mine.mirrored)
            self.assertTrue(_near(L["frame"]["w_in"], mine.frame_w))
            self.assertEqual(mine.depth, 1)
            self.assertEqual(mine.parent_id, 652)
        # the 0.902in child line is drawn 0.437in long and vertical
        self.assertTrue(_near(geom.abs_box(geom.find(s, 650)).h, 0.478, 0.001))

    def test_iter_abs_matches_read_every_slide(self):
        """Every rendered leaf and every positioned group on all 134 slides: boxes within 0.0015in of read."""
        compared, worst, bad = 0, 0.0, []
        for idx in range(1, len(self.prs.slides) + 1):
            rd = read_slide(self.deck, idx, light=True)
            s = self.prs.slides[idx - 1]
            got = {g.id: g for g in geom.iter_abs(s, groups=True, hidden=False)}
            want = [L for L in rd["shapes"] if L["kind"] in ("sp", "pic", "cxn", "graphic")]
            want += [G for G in rd["groups"] if G["bbox"] is not None]
            for L in want:
                g = got.get(L["id"])
                if g is None:
                    bad.append((idx, L["id"], "missing"))
                    continue
                b = L["bbox"]
                d = max(abs(b["x_in"] - g.x), abs(b["y_in"] - g.y), abs(b["w_in"] - g.w), abs(b["h_in"] - g.h))
                worst = max(worst, d)
                compared += 1
                if d > 0.0015:
                    bad.append((idx, L["id"], round(d, 4)))
        self.assertEqual(bad, [])
        self.assertGreater(compared, 10000)
        print(f"\n  iter_abs vs read: {compared} boxes on {len(self.prs.slides)} slides, worst {worst:.4f} in",
              file=sys.stderr)


class BakeOnReference(unittest.TestCase):
    """bake_groups on every slide of the flagship, in memory: same painted points, identity groups, sizes kept."""

    def test_bake_every_slide(self):
        prs = Presentation(D01)       # its own instance: baking mutates it, and it is never saved
        groups = slides = 0
        for idx, s in enumerate(prs.slides, 1):
            before = {g.id: _pts(g) for g in geom.iter_abs(s)}
            sizes = [r.get("sz") for r in s.shapes._spTree.iter(A("rPr"), A("defRPr"), A("endParaRPr"))]
            rep = geom.bake_groups(s)
            groups += len(rep.groups)
            slides += 1
            after = {g.id: _pts(g) for g in geom.iter_abs(s)}
            self.assertEqual(set(before), set(after), idx)
            for i, pts in before.items():
                d = max(max(abs(p[0] - q[0]), abs(p[1] - q[1])) for p, q in zip(pts, after[i]))
                self.assertLess(d, 0.0002, (idx, i, d))
            self.assertEqual(sizes, [r.get("sz") for r in s.shapes._spTree.iter(A("rPr"), A("defRPr"),
                                                                                   A("endParaRPr"))], idx)
            for g in geom.iter_abs(s, groups=True):
                if g.kind == "grp":
                    r = read_xfrm(geom._xfrm_el(g.el))
                    self.assertTrue(r is None or geom._is_identity(group_child_to_parent(r)), (idx, g.id))
            if idx == 50:
                c = geom.abs_box(geom.find(s, 650))
                self.assertAlmostEqual(c.rot_deg, 90.0, places=2)
                self.assertEqual(geom.abs_box(geom.find(s, 650)).group_scale, (1.0, 1.0))
        self.assertEqual(slides, len(prs.slides))
        self.assertGreater(groups, 1000)
        print(f"\n  bake_groups: {groups} groups made identity on {slides} slides, no drift", file=sys.stderr)


# ======================================================================== geometry, synthetic

class GeomSynthetic(unittest.TestCase):

    def setUp(self):
        self.prs = blank_prs()
        self.s = blank_slide(self.prs)

    def test_shear_refused_before_writing(self):
        """A 30-degree child under 2:1 group scale is a shear: GeometryError, and the slide is untouched."""
        add_group(self.s, [("tilted", Inches(1), Inches(1), Inches(2), Inches(1), 30)],
                  off=(Inches(1), Inches(1)), ext=(Inches(4), Inches(1)),
                  ch_off=(Inches(1), Inches(1)), ch_ext=(Inches(2), Inches(1)))
        xml0 = etree.tostring(self.s.shapes._spTree)
        self.assertTrue(geom.abs_box(geom.find(self.s, "tilted")).sheared)
        with self.assertRaises(GeometryError) as cm:
            geom.bake_groups(self.s)
        self.assertIn("non-uniform", str(cm.exception))
        self.assertEqual(xml0, etree.tostring(self.s.shapes._spTree))

    def test_quarter_turn_under_non_uniform_scale_bakes(self):
        """90 degrees under 2:1 scale is not a shear: it bakes, the painted box is kept, the font is not scaled."""
        add_group(self.s, [("turned", Inches(1), Inches(1), Inches(2), Inches(1), 90),
                           ("flat", Inches(4), Inches(1), Inches(1), Inches(1), 0)],
                  off=(Inches(1), Inches(2)), ext=(Inches(8), Inches(2)),
                  ch_off=(Inches(1), Inches(1)), ch_ext=(Inches(4), Inches(2)), rot=0)
        before = {g.name: _pts(g) for g in geom.iter_abs(self.s)}
        sz = [r.get("sz") for r in self.s.shapes._spTree.iter(A("rPr"))]
        rep = geom.bake_groups(self.s)
        self.assertEqual(len(rep.groups), 1)
        self.assertEqual(sorted(rep.leaves), sorted(geom.shape_id(e) for e in self.s.shapes._spTree.iter(P("sp"))))
        after = {g.name: _pts(g) for g in geom.iter_abs(self.s)}
        self.assertEqual(before, after)
        self.assertEqual(sz, [r.get("sz") for r in self.s.shapes._spTree.iter(A("rPr"))])
        turned = geom.abs_box(geom.find(self.s, "turned"))
        self.assertAlmostEqual(turned.rot_deg, 90.0)
        self.assertAlmostEqual(turned.frame_w, 2.0 * 1.0, places=4)   # 2in long axis scaled by the y factor 1
        self.assertAlmostEqual(turned.frame_h, 1.0 * 2.0, places=4)   # 1in short axis scaled by the x factor 2

    def test_rotated_flipped_group_bakes_exactly(self):
        """A rotated, flipped, scaled group: every child keeps its painted points and path ends."""
        g = add_group(self.s, [("a", Inches(1), Inches(1), Inches(2), Inches(1), 0),
                               ("b", Inches(3), Inches(2), Inches(1), Inches(1), 0)],
                      off=(Inches(2), Inches(2)), ext=(Inches(3), Inches(2)),
                      ch_off=(Inches(1), Inches(1)), ch_ext=(Inches(3), Inches(2)), rot=35)
        geom._xfrm_el(g).set("flipV", "1")
        cx = self.s.shapes.add_connector(1, Inches(1.5), Inches(1.5), Inches(3.5), Inches(2.5))
        cx.name = "line"
        g.append(cx._element)
        before = {x.name: _pts(x) for x in geom.iter_abs(self.s)}
        geom.bake_groups(self.s)
        after = {x.name: _pts(x) for x in geom.iter_abs(self.s)}
        for k in before:
            d = max(max(abs(p[0] - q[0]), abs(p[1] - q[1])) for p, q in zip(before[k], after[k]))
            self.assertLess(d, 0.0002, k)

    def test_identity_group(self):
        a = self.s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(1), Inches(1), Inches(1))
        b = self.s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(3), Inches(2), Inches(1), Inches(2))
        top = self.s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(5), Inches(1), Inches(1), Inches(1))
        b.rotation = 45
        before = {geom.shape_id(x): _pts(geom.abs_box(x)) for x in (a, b, top)}
        g = geom.identity_group(self.s, [b, a], "zone.pair")
        tree = self.s.shapes._spTree
        kids = [e for e in tree if etree.QName(e).localname in geom.SHAPE_TAGS]
        self.assertIs(kids[0], g._element)          # took the lower member's z position
        self.assertIs(kids[1], top._element)
        self.assertEqual([geom.shape_id(e) for e in g._element if etree.QName(e).localname == "sp"],
                         [a.shape_id, b.shape_id])    # members keep their paint order
        r = read_xfrm(geom._xfrm_el(g._element))
        self.assertTrue(geom._is_identity(group_child_to_parent(r)))
        self.assertEqual(g.name, "zone.pair")
        ids = [c.get("id") for c in tree.iter(P("cNvPr"))]
        self.assertEqual(len(ids), len(set(ids)))
        for x in (a, b, top):
            self.assertEqual(before[geom.shape_id(x)], _pts(geom.abs_box(x)))
        gb = geom.abs_box(g)
        bb = geom.abs_box(b)
        self.assertAlmostEqual(gb.x, 1.0, places=4)
        self.assertAlmostEqual(gb.b, bb.b, places=4)
        with self.assertRaises(GeometryError):
            geom.identity_group(self.s, [a], "")

    def test_find_errors(self):
        self.s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(1), Inches(1)).name = "twin"
        self.s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(1), Inches(1)).name = "twin"
        with self.assertRaises(KeyError):
            geom.find(self.s, "absent")
        with self.assertRaises(LookupError) as cm:
            geom.find(self.s, "twin")
        self.assertIn("ids", str(cm.exception))

    def test_rotated_box_and_body_extent(self):
        l, t, r, b = geom.rotated_box((1.0, 1.0, 2.0, 1.0), 90)
        self.assertAlmostEqual(l, 1.5)
        self.assertAlmostEqual(t, 0.5)
        self.assertAlmostEqual(r - l, 1.0)
        self.assertAlmostEqual(b - t, 2.0)
        with self.assertRaises(GeometryError):
            geom.body_extent(self.s, 1.0)
        title = self.s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(0.3), Inches(5), Inches(0.6))
        title.name = "title"
        self.s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(1.5), Inches(5), Inches(2))
        self.s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(4), Inches(5), Inches(1))
        self.assertEqual(geom.body_extent(self.s, 0.0, skip=["title"]), (1.5, 5.0))

    def test_affine_y_moves_groups_by_centre(self):
        tall = self.s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(2), Inches(1), Inches(2))
        g = add_group(self.s, [("k", Inches(3), Inches(2), Inches(1), Inches(1), 0)],
                      off=(Inches(3), Inches(2)), ext=(Inches(1), Inches(1)),
                      ch_off=(Inches(3), Inches(2)), ch_ext=(Inches(1), Inches(1)))
        f = geom.affine_y(self.s, 2.0, 4.0, 2.0, 5.0)
        self.assertAlmostEqual(f, 1.5)
        self.assertAlmostEqual(geom.abs_box(tall).h, 3.0, places=4)
        gb = geom.abs_box(g)
        self.assertAlmostEqual(gb.h, 1.0, places=4)               # never stretched
        self.assertAlmostEqual(gb.cy, 2.0 + (2.5 - 2.0) * 1.5, places=4)

    def test_to_front(self):
        a = self.s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(1), Inches(1))
        self.s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(1), Inches(1))
        geom.to_front(self.s, a)
        self.assertIs(self.s.shapes._spTree[-1], a._element)


# ======================================================================== clone

class CloneAcrossPackages(unittest.TestCase):
    """d01 slide 15 (11 pictures, one SVG-only icon, four glued connectors) into python-pptx's default template."""

    @classmethod
    def setUpClass(cls):
        cls.src = Presentation(D01)
        s15 = cls.src.slides[14]
        cls.s15 = s15
        tree = s15.shapes._spTree
        # in-memory plants (never saved): alt text, title, a click link with its rel, custom data with a tags part
        pics = list(tree.iter(P("pic")))
        cls.alt_pic = pics[1]
        pics[1].find(f"{P('nvPicPr')}/{P('cNvPr')}").set("descr", "/tmp/claude-0/leak.png")
        pics[2].find(f"{P('nvPicPr')}/{P('cNvPr')}").set("title", "scraped page title")
        sp = next(e for e in tree if etree.QName(e).localname == "sp")
        rid = s15.part.relate_to("https://example.invalid/x", RT.HYPERLINK, is_external=True)
        etree.SubElement(sp.find(f"{P('nvSpPr')}/{P('cNvPr')}"), A("hlinkClick")).set(R_NS + "id", rid)
        tags = Part(PackURI("/ppt/tags/tag9001.xml"),
                    "application/vnd.openxmlformats-officedocument.presentationml.tags+xml", s15.part.package,
                    b'<p:tagLst xmlns:p="%s"><p:tag name="SRC" val="x"/></p:tagLst>' % NS["p"].encode())
        trid = s15.part.relate_to(tags, RT.TAGS)
        nvpr = sp.find(f"{P('nvSpPr')}/{P('nvPr')}")
        cdl = etree.SubElement(nvpr, P("custDataLst"))
        etree.SubElement(cdl, P("tags")).set(R_NS + "id", trid)
        cls.planted_sp = int(sp.find(f"{P('nvSpPr')}/{P('cNvPr')}").get("id"))
        cls.n_top = sum(1 for e in tree if etree.QName(e).localname in geom.SHAPE_TAGS)
        cls.n_pics = len(pics)

    def _fresh(self):
        dst = blank_prs(self.src.slide_width, self.src.slide_height)
        return dst, blank_slide(dst)

    def test_copy_round_trip(self):
        dst, slide = self._fresh()
        m = clone.copy_shapes(self.s15, slide)
        self.assertEqual(len(m.top), self.n_top)
        out = os.path.join(_TMP.name, "s15.pptx")
        dst.save(out)
        again = Presentation(out)                     # reopens
        self.assertEqual(len(again.slides), 1)
        a = audit_package(out)
        self.assertEqual(a["dangling"], [])
        self.assertEqual(a["missing_target"], [])
        self.assertEqual(a["dup_ids"], [])
        self.assertEqual(a["banned"], [])
        self.assertEqual(a["pics"], self.n_pics)
        self.assertEqual(a["svg"], 1)
        self.assertTrue(a["svg_ct_ok"])
        self.assertEqual(a["svg_without_png"], 0)
        self.assertEqual(a["glue"], [])               # DEVICE_STRIP strips all glue
        names = zipfile.ZipFile(out).namelist()
        self.assertFalse([n for n in names if n.startswith("ppt/tags/") or n.endswith(".wdp")])
        self.assertEqual(len([n for n in names if n.startswith("ppt/media/")]), self.n_pics + 1)  # + PNG fallback
        # geometry carried exactly, keyed by source id through the IdMap
        src_abs = {g.id: _pts(g) for g in geom.iter_abs(self.s15)}
        dst_abs = {g.id: _pts(g) for g in geom.iter_abs(again.slides[0])}
        for sid, pts in src_abs.items():
            self.assertEqual(pts, dst_abs[m[sid]], sid)
        # the read layer sees the same pictures, the fallback raster at twice the displayed size
        rd = read_slide(open_deck(out), 1)
        pics = [L for L in rd["shapes"] if L["kind"] == "pic"]
        self.assertEqual(len(pics), self.n_pics)
        svgp = [L for L in pics if L["picture"].get("svg_part")]
        self.assertEqual(len(svgp), 1)
        code, log = xsd_validate(out)
        self.assertEqual(code, 0, log[-2000:])

    def test_alt_and_links_were_planted(self):
        """The plants are real, so the strip assertions above are not vacuous."""
        tree = self.s15.shapes._spTree
        self.assertEqual(len(list(tree.iter(A("hlinkClick")))), 1)
        self.assertEqual(len(list(tree.iter(P("custDataLst")))), 1)
        self.assertTrue(any(c.get("descr") for c in tree.iter(P("cNvPr"))))
        self.assertTrue(any(etree.QName(e).localname == "svgBlip" for e in tree.iter()))

    def test_glue_remapped_or_stripped(self):
        src_glue = [(etree.QName(g).localname, int(g.get("id"))) for g in self.s15.shapes._spTree.iter(A("stCxn"),
                                                                                                        A("endCxn"))]
        self.assertEqual(len(src_glue), 7)
        # remap: every glue id now names the copy of its target
        dst, slide = self._fresh()
        m = clone.copy_shapes(self.s15, slide, strip=clone.CLEAN_STRIP)
        got = [(etree.QName(g).localname, int(g.get("id"))) for g in slide.shapes._spTree.iter(A("stCxn"),
                                                                                              A("endCxn"))]
        self.assertEqual(got, [(t, m[i]) for t, i in src_glue])
        self.assertEqual((m.glue_remapped, m.glue_stripped), (7, 0))
        out = os.path.join(_TMP.name, "glue.pptx")
        dst.save(out)
        a = audit_package(out)
        self.assertEqual(len(a["glue"]), 7)
        self.assertTrue(all(ok for *_, ok in a["glue"]))
        # partial copy: the connectors alone, so their targets are absent and every glue element goes
        conn_ids = {int(c.getparent().find(P("cNvPr")).get("id"))
                    for c in self.s15.shapes._spTree.iter(P("cNvCxnSpPr")) if c.find(A("stCxn")) is not None
                    or c.find(A("endCxn")) is not None}
        top_ids = {geom.shape_id(e) for e in self.s15.shapes._spTree}
        dst2, slide2 = self._fresh()
        m2 = clone.copy_shapes(self.s15, slide2, select=conn_ids & top_ids, strip=clone.CLEAN_STRIP)
        self.assertGreater(len(m2.top), 0)
        self.assertEqual(list(slide2.shapes._spTree.iter(A("stCxn"), A("endCxn"))), [])
        self.assertEqual(m2.glue_remapped, 0)

    def test_select_by_name_and_id(self):
        top = [e for e in self.s15.shapes._spTree if etree.QName(e).localname in geom.SHAPE_TAGS]
        pick = {geom.shape_name(top[0]), geom.shape_id(top[3])}
        dst, slide = self._fresh()
        m = clone.copy_shapes(self.s15, slide, select=pick)
        self.assertEqual(len(m.top), 2)
        self.assertIn(geom.shape_id(top[3]), m)
        with self.assertRaises(KeyError):
            clone.copy_shapes(self.s15, self._fresh()[1], select={"no such shape"})

    def test_same_package_adds_no_parts(self):
        prs = Presentation(D01)
        s = prs.slides.add_slide(prs.slide_layouts[6])
        for sh in list(s.shapes):
            sh._element.getparent().remove(sh._element)
        m = clone.copy_shapes(prs.slides[14], s, strip=clone.StripPolicy(glue="remap"))
        # every image part is shared; the one new part is the PNG fallback the SVG-only icon never had
        self.assertEqual(len(m.parts_added), 1)
        self.assertTrue(m.parts_added[0].endswith(".png"))
        self.assertEqual(m.glue_remapped, 7)

    def test_custom_data_kept_cross_package_refuses(self):
        """Keeping custom data across packages would need the tags part: refused, nothing written."""
        dst, slide = self._fresh()
        before = etree.tostring(slide.shapes._spTree)
        with self.assertRaises(UnsupportedPart) as cm:
            clone.copy_shapes(self.s15, slide, strip=clone.StripPolicy(cust_data=False))
        self.assertIn("tags", str(cm.exception))
        self.assertEqual(before, etree.tostring(slide.shapes._spTree))
        self.assertEqual(len(slide.part.rels), 1)      # the layout only

    def test_reuse_picture(self):
        dst, slide = self._fresh()
        src_pic = next(sh for sh in self.s15.shapes if sh.shape_type == 13 and
                       sh._element.find(f".//{qn('asvg:svgBlip')}") is None)
        a = clone.reuse_picture(slide, src_pic, (1.0, 1.0, 0.5, 0.5), name="icon.one", alt="Calendar")
        b = clone.reuse_picture(slide, src_pic, (2.0, 1.0, 0.5, 0.5), name="icon.two")
        self.assertEqual((a.name, b.name), ("icon.one", "icon.two"))
        self.assertEqual(a._element.find(f"{P('nvPicPr')}/{P('cNvPr')}").get("descr"), "Calendar")
        self.assertIsNone(b._element.find(f"{P('nvPicPr')}/{P('cNvPr')}").get("descr"))
        for pic in (a, b):
            self.assertIsNone(pic._element.find(P("style")))
            self.assertEqual(len(pic._element.find(P("spPr")).findall(A("effectLst"))), 1)
            self.assertEqual(len(pic._element.find(P("spPr")).find(A("effectLst"))), 0)
        self.assertAlmostEqual(geom.abs_box(b).x, 2.0, places=4)
        img_rels = [r for r in slide.part.rels.values() if r.reltype == RT.IMAGE]
        self.assertEqual(len(img_rels), 1)             # one part, related once, reused twice
        with self.assertRaises(GeometryError):
            clone.reuse_picture(slide, src_pic, (0, 0, 1, 1), name="")


class CloneRefusalsAndStrips(unittest.TestCase):

    def test_chart_refused_before_writing(self):
        src = blank_prs()
        s = blank_slide(src)
        data = CategoryChartData()
        data.categories = ["a", "b"]
        data.add_series("s", (1, 2))
        s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(1), Inches(1), Inches(4), Inches(3), data)
        s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(1), Inches(1))
        dst = blank_prs()
        d = blank_slide(dst)
        before = etree.tostring(d.shapes._spTree)
        with self.assertRaises(UnsupportedPart) as cm:
            clone.copy_shapes(s, d)
        self.assertIn("chart", str(cm.exception))
        self.assertEqual(before, etree.tostring(d.shapes._spTree))

    def test_hdphoto_layers_stripped(self):
        """d01 slide 14 carries four a14:imgProps layers with .wdp parts: none survive the copy."""
        src = Presentation(D01)
        s14 = src.slides[13]
        self.assertEqual(len(list(s14.shapes._spTree.iter(qn("a14:imgProps")))), 4)
        dst = blank_prs(src.slide_width, src.slide_height)
        d = blank_slide(dst)
        clone.copy_shapes(s14, d)
        out = os.path.join(_TMP.name, "s14.pptx")
        dst.save(out)
        a = audit_package(out)
        self.assertEqual((a["banned"], a["dangling"], a["missing_target"], a["dup_ids"]), ([], [], [], []))
        self.assertEqual(a["svg_without_png"], 0)
        names = zipfile.ZipFile(out).namelist()
        self.assertFalse([n for n in names if n.endswith(".wdp")])
        self.assertFalse([r for r in d.part.rels.values() if r.reltype.endswith("/hdphoto")])

    def test_alternate_content_takes_fallback(self):
        src = blank_prs()
        s = blank_slide(src)
        choice = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(1), Inches(1))
        choice.name = "choice"
        fb = s.shapes.add_shape(MSO_SHAPE.OVAL, 0, 0, Inches(1), Inches(1))
        fb.name = "fallback"
        tree = s.shapes._spTree
        ac = etree.SubElement(tree, qn("mc:AlternateContent"))
        etree.SubElement(ac, qn("mc:Choice"), Requires="p14").append(choice._element)
        etree.SubElement(ac, qn("mc:Fallback")).append(fb._element)
        dst = blank_prs()
        d = blank_slide(dst)
        m = clone.copy_shapes(s, d)
        self.assertEqual(len(m.top), 1)
        self.assertEqual(geom.find(d, "fallback").name, "fallback")
        with self.assertRaises(KeyError):
            geom.find(d, "choice")
        self.assertEqual(list(d.shapes._spTree.iter(qn("mc:AlternateContent"))), [])

    def test_ids_fresh_above_destination(self):
        src = blank_prs()
        s = blank_slide(src)
        for i in range(3):
            s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(1), Inches(1)).name = f"r{i}"
        dst = blank_prs()
        d = blank_slide(dst)
        d.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(1), Inches(1)).name = "existing"
        top_before = max(int(c.get("id")) for c in d.shapes._spTree.iter(P("cNvPr")))
        m1 = clone.copy_shapes(s, d)
        m2 = clone.copy_shapes(s, d)
        ids = [int(c.get("id")) for c in d.shapes._spTree.iter(P("cNvPr"))]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(v > top_before for v in m1.ids.values()))
        self.assertTrue(min(m2.ids.values()) > max(m1.ids.values()))
        self.assertEqual(m1["r1"] + 3, m2["r1"])

    def test_clone_shape_same_slide(self):
        prs = blank_prs()
        s = blank_slide(prs)
        card = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1), Inches(1), Inches(2), Inches(1))
        card.name = "card.one"
        two = clone.clone_shape(s, card, name="card.two")
        self.assertEqual(two.name, "card.two")
        self.assertNotEqual(two.shape_id, card.shape_id)
        self.assertEqual(_pts(geom.abs_box(two)), _pts(geom.abs_box(card)))
        self.assertIs(s.shapes._spTree[-1], two._element)

    def test_add_svg_part(self):
        prs = blank_prs()
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10"/></svg>'
        p1 = clone.add_svg_part(prs, svg)
        prs.slides.add_slide(prs.slide_layouts[6]).part.relate_to(p1, RT.IMAGE)
        p2 = clone.add_svg_part(prs, svg)
        self.assertIs(p1, p2)
        self.assertEqual(p1.content_type, "image/svg+xml")
        self.assertTrue(str(p1.partname).endswith(".svg"))
        with self.assertRaises(UnsupportedPart):
            clone.add_svg_part(prs, b"\x89PNG not an svg")
        png = clone.rasterise_svg(svg, 20, 20)
        self.assertTrue(png.startswith(b"\x89PNG"))


if __name__ == "__main__":
    unittest.main()
