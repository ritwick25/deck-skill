"""The architecture diagram engine (deckkit.arch), identity colours, the brand-mark registry and gate P26 (ruling 18).

Run: cd ~/.claude/skills/deck && $PY -m unittest tests.test_arch -v
Every diagram here is drawn on a fresh WIDE deck in the sigmoid theme; checks read the drawn shapes back.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SKILL, "kit"))
sys.path.insert(0, os.path.join(SKILL, "gates"))

from pptx import Presentation  # noqa: E402

from deckkit import arch, icons, package, prims, tag  # noqa: E402
from deckkit.canvas import WIDE, Box  # noqa: E402
from deckkit.errors import GeometryError, Overflows, ThemeInvariant, UnsupportedPart  # noqa: E402
from deckkit.read.ns import NS  # noqa: E402
from deckkit.text import title  # noqa: E402
from deckkit.theme import Theme  # noqa: E402

A = "{%s}" % NS["a"]
P = "{%s}" % NS["p"]
BASE = os.path.join(SKILL, "kit", "assets", "base-wide.pptx")
SIGMOID = os.path.join(SKILL, "themes", "sigmoid.json")
NEUTRAL = os.path.join(SKILL, "themes", "neutral.json")
TH = Theme.load(SIGMOID)
AREA = Box(0.5, 0.9, 12.4, 5.9)
KEYS = ["aws/compute/lambda", "aws/storage/simple-storage-service-s3", "aws/ml/bedrock", "aws/database/rds",
        "aws/analytics/amazon-opensearch-service", "aws/integration/eventbridge", "aws/network/api-gateway",
        "aws/security/cognito", "aws/management/cloudwatch", "aws/security/secrets-manager", "aws/compute/fargate",
        "aws/devtools/codepipeline"]


def slide():
    prs = Presentation(BASE)
    return prs, prs.slides.add_slide(prs.slide_layouts[0])


def tearDownModule():
    prims._ACTIVE.clear()            # no theme stays bound for the next test module


def shapes(s):
    return {sh.name: sh for sh in s.shapes}


def two_row(grammar="aws", l0=False):
    """Six marks in a group, two rows of three, on a 2 x 1 diagram grid with one actor outside."""
    d = arch.Diagram(grammar, l0=l0, grid=(4, 1))
    d.node("user", "glyph:users", "Field reps", at=(0, 0))
    kind = {"aws": "aws-cloud", "azure": "azure-subscription", "house": "region"}[grammar]
    d.group("g", kind, "Cloud", at=(1, 0, 3, 1), grid=(3, 2))
    for k in range(6):
        d.node("n%d" % k, "vendor:" + KEYS[k], "Service %d" % k, "role", group="g", at=(k % 3, k // 3))
    return d


class Placement(unittest.TestCase):
    def test_grid_cells_and_centring(self):
        prs, s = slide()
        d = two_row()
        d.render(s, AREA, TH)
        g = d.groups["g"]
        xs = d._col_x("g", g.inner)
        for k in range(6):
            n = d.nodes["n%d" % k]
            c, r = k % 3, k // 3
            self.assertAlmostEqual(n.icon.cx, (xs[c] + xs[c + 1]) / 2, places=4, msg="centred in its column")
            self.assertTrue(g.inner.contains(n.icon, tol=1e-6) and g.inner.contains(n.cap, tol=1e-6))
            self.assertAlmostEqual(n.cap.cx, n.icon.cx, places=4, msg="caption under its icon")
            self.assertLess(n.icon.b, n.cap.y + 1e-9, msg="caption below the icon")
        # one row shares one icon centre line
        self.assertAlmostEqual(d.nodes["n0"].icon.cy, d.nodes["n2"].icon.cy, places=6)
        self.assertGreater(d.nodes["n3"].icon.y, d.nodes["n0"].cap.b)
        # the group sits on its parent's grid, inside its span with a margin, and its inner grid starts after the tab
        root = d._col_x(None, AREA)
        self.assertAlmostEqual(g.frame.x, root[1] + arch.MARGIN, places=4)
        self.assertAlmostEqual(g.frame.r, root[4] - arch.MARGIN, places=4)
        self.assertAlmostEqual(g.inner.y, g.frame.y + arch.TAB + arch.HEAD_AIR, places=4)

    def test_weights_and_out_of_grid(self):
        d = arch.Diagram("aws", grid=(3, 1), weights=[2, 1, 1])
        xs = d._col_x(None, Box(0, 0, 4.0, 1.0))
        self.assertAlmostEqual(xs[1], 2.0, places=6)
        with self.assertRaises(GeometryError):
            d.node("x", "vendor:" + KEYS[0], "X", at=(3, 0))
        with self.assertRaises(GeometryError):
            d.group("g", "aws-vpc", "VPC", at=(2, 0, 2, 1))
        with self.assertRaises(GeometryError):
            d.group("g2", "region", "Not AWS notation", at=(0, 0, 1, 1))

    def test_no_card_per_icon(self):
        prs, s = slide()
        m = two_row().render(s, AREA, TH)
        self.assertEqual(m["boxed_alone"], 0)
        self.assertEqual(m["marks"], 6)
        pics = [sh for sh in s.shapes if sh.shape_type == 13 and sh.name.startswith("vendor.aws/") and
                ".arch-n-" in sh.name]
        self.assertEqual(len(pics), 6)

    def test_more_chip_counts_the_declared_set(self):
        prs, s = slide()
        d = arch.Diagram("aws", grid=(1, 1))
        d.group("g", "generic", "Tools", at=(0, 0, 1, 1), grid=(3, 1))
        for k in range(5):
            d.node("t%d" % k, "vendor:" + KEYS[k], "Tool %d" % k, group="g")
        m = d.render(s, AREA, TH)
        self.assertEqual(m["hidden"], 3)                   # 2 shown, the third cell holds the chip
        chip = shapes(s)["arch.g.g.more"]
        self.assertEqual(chip.text_frame.text, "+3 more")


class Captions(unittest.TestCase):
    def test_overflow_raises_never_shrinks(self):
        prs, s = slide()
        d = arch.Diagram("aws", grid=(10, 1))
        d.node("x", "vendor:" + KEYS[0], "Extraordinarily long service name that cannot fit", at=(0, 0))
        with self.assertRaises(Overflows):
            d.render(s, AREA, TH)

    def test_caption_sizes(self):
        prs, s = slide()
        d = two_row()
        d.render(s, AREA, TH)
        cap = shapes(s)["arch.n.n0.caption"]
        sizes = [r.font.size.pt for p in cap.text_frame.paragraphs for r in p.runs]
        self.assertEqual(sizes, [arch.NAME_PT, arch.ROLE_PT])
        self.assertFalse(cap.text_frame.paragraphs[0].runs[0].font.bold, "aws names are regular (spec 1.2)")
        prs, s = slide()
        two_row("house").render(s, AREA, TH)
        cap = shapes(s)["arch.n.n0.caption"]
        self.assertTrue(cap.text_frame.paragraphs[0].runs[0].font.bold, "the house grammar keeps bold names")

    def test_group_too_short_raises(self):
        prs, s = slide()
        d = arch.Diagram("aws", grid=(1, 1))
        d.group("g", "aws-cloud", "Cloud", at=(0, 0, 1, 1), grid=(2, 9))
        for k in range(12):
            d.node("n%d" % k, "vendor:" + KEYS[k], "Service %d" % k, "role", group="g", at=(k % 2, k // 2))
        with self.assertRaises(Overflows):
            d.render(s, Box(0.5, 0.9, 6.0, 3.0), TH)


class Flows(unittest.TestCase):
    def _on_edge(self, pt, b, tol=1e-3):
        on_x = (abs(pt[0] - b.x) < tol or abs(pt[0] - b.r) < tol) and b.y - tol <= pt[1] <= b.b + tol
        on_y = (abs(pt[1] - b.y) < tol or abs(pt[1] - b.b) < tol) and b.x - tol <= pt[0] <= b.r + tol
        return on_x or on_y

    def test_ends_land_on_icon_edges_never_the_caption(self):
        prs, s = slide()
        d = two_row()
        d.flow("user", "n0", "brief request", step=1)
        d.flow("n0", "n1", "raw data", step=2)
        d.flow("n1", "n4", "claims", step=3)
        d.flow("n2", "n5", "draft", kind="async")
        d.steps({1: "One", 2: "Two", 3: "Three"})
        m = d.render(s, AREA, TH)
        self.assertEqual((m["flows"], m["labelled"]), (4, 4))
        for f in d.flows:
            S, D = d.nodes[f.src], d.nodes[f.dst]
            self.assertTrue(self._on_edge(f.points[0], S.icon), "start on the source icon's edge")
            self.assertTrue(self._on_edge(f.points[-1], D.icon), "end on the destination icon's edge")
            self.assertNotAlmostEqual(f.points[-1][1], D.icon.b, places=4, msg="never the bottom, where the caption is")
            for (ax, ay), (bx, by) in zip(f.points, f.points[1:]):
                self.assertTrue(abs(ax - bx) < 1e-9 or abs(ay - by) < 1e-9, "orthogonal")
            for p, q in zip(f.points, f.points[1:]):
                for n in d.nodes.values():
                    self.assertFalse(arch._seg_hits(p, q, n.cap, pad=0.0), "a flow never crosses a caption")
        self.assertEqual(len(d.flows[1].points), 2, "aligned icons get a straight line")
        # a label beside its segment's midpoint; a badge beside an end
        for f in d.flows:
            mids = [((p[0] + q[0]) / 2, (p[1] + q[1]) / 2) for p, q in zip(f.points, f.points[1:])]
            self.assertLessEqual(min(arch._dist_pt_box(m_, f.label_box) for m_ in mids), 0.45)
            if f.step:
                self.assertLessEqual(min(arch._dist_pt_box(e, f.badge) for e in (f.points[0], f.points[-1])), 0.35)
        boxes = [f.label_box for f in d.flows] + [f.badge for f in d.flows if f.badge]
        for i, a in enumerate(boxes):
            for b in boxes[i + 1:]:
                self.assertFalse(arch._inter(a, b), "labels and badges never overlap")
        self.assertIn("arch.legend.1.step", shapes(s))
        dashed = shapes(s)["arch.f.4"]._element.find(".//" + A + "prstDash")
        self.assertEqual(dashed.get("val"), "dash", "async is dashed")

    def test_l0_refuses_flows_and_numbering(self):
        d = two_row(grammar="house", l0=True)
        with self.assertRaises(GeometryError):
            d.flow("n0", "n1", "data")
        with self.assertRaises(GeometryError):
            d.steps({1: "x"})
        prs, s = slide()
        d.render(s, AREA, TH)
        self.assertFalse([sh for sh in s.shapes if sh.shape_type == 9 or "arch.f." in sh.name])

    def test_flow_validation(self):
        d = two_row()
        with self.assertRaises(GeometryError):
            d.flow("n0", "n1", "one two three four five six seven")
        with self.assertRaises(GeometryError):
            d.flow("n0", "nowhere")
        d.flow("n0", "n1", step=1)
        prs, s = slide()
        with self.assertRaises(GeometryError):
            d.render(s, AREA, TH)               # step 1 has no legend line


class Identity(unittest.TestCase):
    def test_notation_colours_registered_in_both_themes(self):
        for path in (SIGMOID, NEUTRAL):
            th = Theme.load(path)
            for g in ("aws", "azure"):
                for kind, st in arch.KINDS[g].items():
                    for c in (st.line, st.fill, st.header[1] if st.header[0] == "square" else None):
                        if c and c not in th.roles:
                            self.assertTrue(th.is_identity(c), "%s %s colour %s registered" % (path, kind, c))
            for k in ("aws-cloud", "azure-blue"):
                self.assertTrue(th.identity[k]["reason"])

    def test_identity_fill_writes_srgb_and_role_writes_scheme(self):
        prs, s = slide()
        sh = prims._add(s, "RECTANGLE", Box(1, 1, 1, 1), "probe")
        prims.set_fill(sh, "aws-vpc", theme=TH)
        prims.set_line(sh, "aws-region", 1.25, theme=TH, dash="sysDash")
        sp = sh._element.find(P + "spPr")
        self.assertEqual(sp.find(A + "solidFill/" + A + "srgbClr").get("val"), "8C4FFF")
        self.assertEqual(sp.find(A + "ln/" + A + "solidFill/" + A + "srgbClr").get("val"), "00A4A6")
        prims.set_fill(sh, "card", theme=TH)
        self.assertIsNotNone(sp.find(A + "solidFill/" + A + "schemeClr"))
        with self.assertRaises(ThemeInvariant):
            prims.set_fill(sh, "aws-nonsense", theme=TH)

    def test_identity_strip_is_still_refused(self):
        prs, s = slide()
        with self.assertRaises(GeometryError):
            prims.rect(s, Box(1, 1, 0.05, 2.0), fill="aws-vpc", name="bar", theme=TH)

    def test_identity_cannot_shadow_a_role(self):
        with open(SIGMOID, encoding="utf-8") as fh:
            data = json.load(fh)
        data["identity"]["accent"] = {"hex": "123456", "reason": "x"}
        with self.assertRaises(ThemeInvariant):
            Theme(data)

    def test_badge_numeral_clears_contrast(self):
        from deckkit.read.colour import contrast
        for k in set(arch.BADGE_FILL.values()) - {"accent"}:
            self.assertGreaterEqual(contrast("FFFFFF", TH.identity_hex(k)), 4.5, k)

    def test_text_never_takes_a_notation_colour(self):
        from deckkit import text
        prs, s = slide()
        with self.assertRaises(ThemeInvariant):
            text.textbox(s, Box(1, 1, 2, 0.4), [text.Para((text.Run("x", role="aws-vpc", size=10.0),))], "t", TH)


class Marks(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="marks-")
        self.svg = (b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">'
                    b'<rect x="4" y="4" width="56" height="56" rx="8" fill="#2B6CB0"/></svg>')
        with open(os.path.join(self.dir, "acme.svg"), "wb") as fh:
            fh.write(self.svg)
        reg = {"marks": {"acme": {"name": "Acme", "file": "acme.svg", "sha256": hashlib.sha256(self.svg).hexdigest(),
                                  "source": "fixture", "fetched": "2026-10-03", "url": "https://example.invalid/a.svg"}}}
        with open(os.path.join(self.dir, "registry.json"), "w", encoding="utf-8") as fh:
            json.dump(reg, fh)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_every_kit_mark_matches_its_record(self):
        reg = icons.mark_registry()
        for key, entry in reg.items():
            blob = (icons.marks_dir() / entry["file"]).read_bytes()
            self.assertEqual(hashlib.sha256(blob).hexdigest(), entry["sha256"], key)

    def test_mark_embeds_svg_with_png_fallback_and_records_key(self):
        prs, s = slide()
        pic = icons.mark(s, "acme", Box(1, 1, 0.5, 0.5), registry=self.dir)
        self.assertEqual(pic.name, "mark.acme")
        alt = pic._element.find(".//" + P + "cNvPr").get("descr")
        self.assertEqual(icons.mark_key_of(pic.name, alt), "acme")
        blip = pic._element.find(".//" + A + "blip")
        self.assertTrue(blip.get("{%s}embed" % NS["r"]))
        svgb = [e for e in blip.iter() if "svgBlip" in str(e.tag)]
        self.assertEqual(len(svgb), 1)
        part = s.part.related_part(svgb[0].get("{%s}embed" % NS["r"]))
        self.assertEqual(part.blob, self.svg, "embedded byte for byte")

    def test_wordmark_node_is_drawn_wide_and_counts_as_a_mark(self):
        wide = (b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 80" width="400" height="80">'
                b'<rect x="0" y="0" width="400" height="80" fill="#1C3C3C"/></svg>')
        with open(os.path.join(self.dir, "wide.svg"), "wb") as fh:
            fh.write(wide)
        rp = os.path.join(self.dir, "registry.json")
        with open(rp, encoding="utf-8") as fh:
            reg = json.load(fh)
        reg["marks"]["wide"] = {"name": "Wide", "file": "wide.svg", "sha256": hashlib.sha256(wide).hexdigest(),
                                "source": "fixture", "fetched": "2026-10-03", "url": "https://example.invalid/w.svg"}
        with open(rp, "w", encoding="utf-8") as fh:
            json.dump(reg, fh)
        prs, s = slide()
        d = arch.Diagram("house", grid=(2, 1), marks=self.dir)
        d.node("w", "mark:wide", "Agent graphs", "orchestration", at=(0, 0))
        d.node("a", "mark:acme", "Acme", at=(1, 0))
        with self.assertRaises(GeometryError):
            d.node("x", "mark:nobody", "X", at=(1, 0))
        d.render(s, AREA, TH)
        w = d.nodes["w"].icon
        self.assertAlmostEqual(w.w / w.h, 5.0, places=2)
        self.assertGreater(w.w, arch.ICON)
        self.assertAlmostEqual(w.cy, d.nodes["a"].icon.cy, places=6, msg="on the row's icon line")
        import p26_architecture
        from _shared import Ctx
        tag.tag(s, "solution-architecture", "house-probe")
        out = os.path.join(self.dir, "w.pptx")
        package.save(prs, out, title="w", theme=TH, overwrite=True)
        c = Ctx(out, theme=SIGMOID)
        self.assertEqual(len(p26_architecture.marks(c.slide(1)["shapes"])), 2)

    def test_tampered_file_and_unknown_key_refused(self):
        prs, s = slide()
        with self.assertRaises(UnsupportedPart):
            icons.mark(s, "nobody", Box(1, 1, 0.5, 0.5), registry=self.dir)
        with open(os.path.join(self.dir, "acme.svg"), "ab") as fh:
            fh.write(b"<!-- edited -->")
        with self.assertRaises(UnsupportedPart):
            icons.mark(s, "acme", Box(1, 1, 0.5, 0.5), registry=self.dir)

    def test_p22_passes_a_registered_mark_and_fails_a_forged_one(self):
        import p22_icons
        from _shared import Ctx, run_gate
        prs, s = slide()
        tag.tag(s, "closing", "line")
        icons.mark(s, "acme", Box(1, 1, 0.5, 0.5), registry=self.dir)
        out = os.path.join(self.dir, "m.pptx")
        package.save(prs, out, title="marks", theme=TH, overwrite=True)
        code, found = run_gate(p22_icons, out, Ctx(out, theme=SIGMOID, extra={"marks_dir": self.dir}))
        self.assertEqual(code, 0, [f.msg for f in found])
        rp = os.path.join(self.dir, "registry.json")
        with open(rp, encoding="utf-8") as fh:
            reg = json.load(fh)
        reg["marks"]["acme"]["sha256"] = "0" * 64
        with open(rp, "w", encoding="utf-8") as fh:
            json.dump(reg, fh)
        code, found = run_gate(p22_icons, out, Ctx(out, theme=SIGMOID, extra={"marks_dir": self.dir}))
        self.assertEqual(code, 1)
        self.assertTrue(any("renamed as a brand mark" in f.msg for f in found))


class Notation(unittest.TestCase):
    def test_aws_flow_and_badge_notation(self):
        prs, s = slide()
        d = two_row("aws")
        d.flow("n0", "n1", "raw data", step=1)
        d.steps({1: "Data lands"})
        d.render(s, AREA, TH)
        sh = shapes(s)
        ln = sh["arch.f.1"]._element.find(".//" + A + "ln")
        self.assertEqual(int(ln.get("w")), int(1.25 * 12700), "aws flows are 1.25pt (spec 1.4)")
        self.assertEqual(ln.find(A + "solidFill")[0].get("val"), "232F3E")
        self.assertEqual(ln.find(A + "tailEnd").get("type"), "arrow")
        self.assertAlmostEqual(sh["arch.f.1.step"].width / 914400, arch.BADGE_BY["aws"][0], places=3)

    def test_house_flow_keeps_triangle(self):
        prs, s = slide()
        d = two_row("house")
        d.flow("n0", "n1", "raw data")
        d.render(s, AREA, TH)
        ln = shapes(s)["arch.f.1"]._element.find(".//" + A + "ln")
        self.assertEqual(ln.find(A + "tailEnd").get("type"), "triangle")

    def test_group_labels_regular_in_aws(self):
        prs, s = slide()
        two_row("aws").render(s, AREA, TH)
        lab = shapes(s)["arch.g.g.label"]
        self.assertFalse(lab.text_frame.paragraphs[0].runs[0].font.bold)


class Pins(unittest.TestCase):
    def test_edge_pin_sits_on_the_frame_line_with_its_caption_outside(self):
        prs, s = slide()
        d = arch.Diagram("aws", grid=(3, 1), weights=[1, 4, 1.4])
        d.group("vpc", "aws-vpc", "VPC", at=(1, 0, 1, 1), grid=(2, 1))
        d.node("a", "vendor:" + KEYS[0], "Inside", group="vpc", at=(0, 0))
        d.node("pin", "vendor:aws/network/endpoint", "Endpoint", group="vpc", at=(1, 0), anchor="edge:r")
        d.node("out", "vendor:" + KEYS[1], "Outside", at=(2, 0))
        d.align("pin", "a")
        d.align("out", "a")
        d.flow("a", "pin", "objects")
        d.flow("pin", "out", "private")
        d.render(s, AREA, TH)
        fr, pin = d.groups["vpc"].frame, d.nodes["pin"]
        self.assertAlmostEqual(pin.icon.cx, fr.r, places=6, msg="centred on the frame line")
        self.assertGreaterEqual(pin.cap.x, fr.r, "caption wholly outside the frame")
        self.assertLessEqual(pin.cap.b, pin.icon.y + 1e-6, "a side pin's caption sits above it by default")

    def test_pin_needs_a_group(self):
        d = arch.Diagram("aws")
        with self.assertRaises(GeometryError):
            d.node("p", "vendor:aws/network/endpoint", "Endpoint", at=(0, 0), anchor="edge:r")


class Routing(unittest.TestCase):
    def test_crossings_counted(self):
        self.assertEqual(arch._crossings([(0, 1), (2, 1)], [((1, 0), (1, 2))]), 1)
        self.assertEqual(arch._crossings([(0, 1), (2, 1)], [((3, 0), (3, 2))]), 0)
        self.assertEqual(arch._crossings([(0, 1), (2, 1)], [((0, 1), (0, 3))]), 0, "a shared end is no crossing")

    def test_label_never_wraps(self):
        prs, s = slide()
        d = two_row("aws")
        d.flow("n0", "n1", "regional signals and sourced claim drafts")
        with self.assertRaises(Overflows):
            d.render(s, AREA, TH)

    def test_draft_lists_instead_of_raising(self):
        prs, s = slide()
        d = arch.Diagram("aws", grid=(10, 1))
        d.node("x", "vendor:" + KEYS[0], "Extraordinarily long service name that cannot fit", at=(0, 0))
        m = d.render(s, AREA, TH, draft=True)
        self.assertTrue(m["problems"])

    def test_private_kind_is_keyed(self):
        prs, s = slide()
        d = two_row("azure")
        d.flow("n0", "n1", kind="private")
        d.flow("n1", "n2", "raw data")
        d.render(s, AREA, TH)
        names = [sh.name for sh in s.shapes]
        self.assertTrue(any(n.endswith(".legend.key.private") for n in names), names)


class Metrics(unittest.TestCase):
    def test_actor_glyphs_are_not_marks_and_labelled_counts_placed_labels(self):
        prs, s = slide()
        d = two_row("aws")
        d.flow("n0", "n1", "raw data")
        d.flow("n1", "n2", step=1)
        d.steps({1: "One"})
        m = d.render(s, AREA, TH)
        self.assertEqual(m["actors"], 1)
        self.assertEqual(m["marks"], 6)
        self.assertEqual(m["labelled"], 1)
        self.assertEqual(m["badge_only"], 1)

    def test_one_line_names_on_a_house_deep_dive(self):
        prs, s = slide()
        d = arch.Diagram("house", grid=(8, 1))
        d.node("x", "vendor:" + KEYS[0], "Lengthy service name", at=(0, 0))
        with self.assertRaises(Overflows):
            d.render(s, AREA, TH)
        prs, s = slide()
        d = arch.Diagram("house", l0=True, grid=(8, 1))
        d.node("x", "vendor:" + KEYS[0], "Lengthy service name", at=(0, 0))
        d.render(s, AREA, TH)


class GateP26(unittest.TestCase):
    def _deck(self, build, variant="aws-reference", archetype="solution-architecture"):
        d = tempfile.mkdtemp(prefix="p26-")
        self.addCleanup(shutil.rmtree, d, True)
        prs = Presentation(BASE)
        s = prs.slides.add_slide(prs.slide_layouts[0])
        tag.tag(s, archetype, variant)
        title(s, "A probe architecture", canvas=WIDE, theme=TH)
        build(s)
        out = os.path.join(d, "a.pptx")
        package.save(prs, out, title="p26", theme=TH, overwrite=True)
        return out

    def _run(self, path):
        import p26_architecture
        from _shared import Ctx, run_gate
        return run_gate(p26_architecture, path, Ctx(path, theme=SIGMOID))

    def _full(self, s, l0=False):
        """An aws board the gate accepts: three boundary kinds with facts on the outer two, five numbered steps on a
        chain of six services, fourteen more services in an operations band, the actor outside the cloud."""
        d = arch.Diagram("aws", grid=(4, 1), weights=[1, 3, 3, 3])
        d.node("user", "glyph:users", "Field reps", at=(0, 0))
        d.group("cloud", "aws-cloud", "AWS Cloud · probe account", at=(1, 0, 3, 1), grid=(1, 2))
        d.group("region", "aws-region", "Region eu-west-1 · probe", parent="cloud", at=(0, 0, 1, 2), grid=(1, 2))
        d.group("vpc", "aws-vpc", "VPC", parent="region", at=(0, 0, 1, 1), grid=(6, 1))
        chain = ["aws/compute/lambda", "aws/database/rds", "aws/analytics/amazon-opensearch-service",
                 "aws/compute/fargate", "aws/compute/elastic-container-service-task", "aws/compute/ec2"]
        for k, key in enumerate(chain):
            d.node("c%d" % k, "vendor:" + key, "Chain %d" % k, group="vpc", at=(k, 0))
        d.group("ops", "generic", "Operations · shared", parent="region", at=(0, 1, 1, 1), grid=(7, 2), band=True)
        more = KEYS[1:3] + KEYS[5:10] + KEYS[11:] + ["aws/security/key-management-service", "aws/devtools/x-ray", "aws/management/cloudtrail",
                           "aws/security/waf", "aws/database/dynamodb", "aws/integration/simple-queue-service-sqs",
                           "aws/storage/s3-glacier", "aws/analytics/athena"]
        for k, key in enumerate(more[:14]):
            d.node("o%d" % k, "vendor:" + key, "Ops %d" % k, group="ops", at=(k % 7, k // 7))
        for k in range(5):
            d.flow("c%d" % k, "c%d" % (k + 1), step=k + 1)
        d.steps({k + 1: "Step %d" % (k + 1) for k in range(5)})
        d.render(s, Box(0.5, 0.9, 12.4, 5.9), TH)

    def _l0(self, s):
        """A house L0 the gate accepts: a dashed boundary round four regions of different widths and two icon tiers."""
        d = arch.Diagram("house", l0=True, grid=(1, 1))
        d.group("plat", "boundary", "Probe platform · one account", at=(0, 0, 1, 1), grid=(4, 2),
                weights=[2.2, 2.6, 3.0, 2.4])
        k = 0
        for c, n in enumerate((2, 3, 4, 2)):
            d.group("r%d" % c, "region", "Region %d" % c, parent="plat", at=(c, 0, 1, 1), grid=(n, 1))
            for j in range(n):
                d.node("m%d" % k, "vendor:" + (KEYS * 2)[k], "Mark %d" % k, group="r%d" % c, at=(j, 0),
                       size=0.62 if j == 0 else None)
                k += 1
        d.group("band", "band", "Band · shared", parent="plat", at=(0, 1, 4, 1), grid=(6, 1))
        for j in range(6):
            d.node("b%d" % j, "vendor:" + KEYS[j], "Band %d" % j, group="band", at=(j, 0))
        d.render(s, Box(0.5, 0.9, 12.4, 5.9), TH)

    def test_engine_slide_passes(self):
        code, found = self._run(self._deck(self._full))
        self.assertEqual(code, 0, [f.msg for f in found])
        code, found = self._run(self._deck(self._l0, variant="l0-house", archetype="layered-architecture"))
        self.assertEqual(code, 0, [f.msg for f in found])

    def test_new_checks_fire(self):
        """Crossings, a gap in the steps, a bare outer label, an orphan, an actor in the cloud: each named."""
        def bad(s):
            d = arch.Diagram("aws", grid=(3, 1), weights=[1, 6, 1])
            d.group("cloud", "aws-cloud", "AWS Cloud", at=(1, 0, 1, 1), grid=(4, 2))
            d.node("actor", "vendor:aws/general/users", "Inside actor", group="cloud", at=(3, 1))
            for k in range(6):
                d.node("n%d" % k, "vendor:" + KEYS[k], "Service %d" % k, group="cloud", at=(k % 3, k // 3))
            d.flow("n0", "n1", step=1)
            d.flow("n1", "n2", step=3)
            d.steps({1: "One", 3: "Three"})
            d.render(s, Box(0.5, 0.9, 12.4, 5.9), TH)
        code, found = self._run(self._deck(bad))
        msgs = " ".join(f.msg for f in found)
        self.assertEqual(code, 1)
        for want in ("not 1..N", "bare name", "orphan", "inside the AWS Cloud", "boundary kind"):
            self.assertIn(want, msgs)

    def test_tile_board_fails(self):
        def board(s):
            for k in range(12):
                x, y = 0.8 + (k % 6) * 2.0, 1.4 + (k // 6) * 2.4
                prims.card(s, Box(x, y, 1.2, 1.2), fill="card", line="hairline", name="tile.%d" % k, theme=TH)
                icons.vendor(s, KEYS[k], Box(x + 0.39, y + 0.2, 0.42, 0.42), name="t%d" % k, theme=TH)
            for k in range(3):
                x = 0.8 + k * 2.0
                prims.connect(s, (x + 1.2, 2.0), (x + 2.0, 2.0), name="arrow.%d" % k, theme=TH)
        code, found = self._run(self._deck(board))
        self.assertEqual(code, 1)
        msgs = " ".join(f.msg for f in found)
        self.assertIn("boxed alone", msgs)
        self.assertIn("carry a label", msgs)
        self.assertIn("without a caption", msgs)

    def test_conceptual_grant(self):
        def few(s):
            icons.vendor(s, KEYS[0], Box(1, 1, 0.42, 0.42), name="a", theme=TH)
        path = self._deck(few)
        self.assertEqual(self._run(path)[0], 1)
        with open(os.path.join(os.path.dirname(path), "deck.json"), "w") as fh:
            json.dump({"overrides": {"P26:marks": "DESIGN.md#conceptual"}}, fh)
        code, found = self._run(path)
        msgs = [f.msg for f in found if f.level == "fail"]
        self.assertFalse([m for m in msgs if "product marks" in m], msgs)


if __name__ == "__main__":
    unittest.main()
