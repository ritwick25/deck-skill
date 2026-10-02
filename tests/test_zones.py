"""deckkit.read.zones: synthetic unit checks, four reference slides read live (read-only), and the corpus.

Run: cd ~/.claude/skills/deck && $PY -m unittest tests.test_zones -v
Acceptance (library DECISIONS, zones rewrite): d08-s007 separates its seven regions at depth 1 or 2;
d01-s069 has a zone per year column; d05-s001 has 5+ zones inside the canvas; d02-s023 has a full-bleed
zone; over every extracted slide no zone box leaves 0..100%, and on slides with 30+ leaves fewer than 15%
have one depth-1 zone holding 85%+ of the leaves (the replaced XY-cut: 274 of 382, 71.7%).
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "kit"))

from lxml import etree  # noqa: E402

from deckkit.read import open_deck, read_slide  # noqa: E402
from deckkit.read.ns import NS  # noqa: E402
from deckkit.read.walk import rect_path  # noqa: E402
from deckkit.read.zones import MAX_ZONES, read_zones, slide_zones, zones  # noqa: E402

LIB = "/Users/Nikunj/Codes/Decks-For-Visuals/library"
MANIFEST = json.load(open(os.path.join(LIB, "manifest.json")))
DECKS = MANIFEST["decks"]
W, H = 13.333, 7.5

_SLIDES: dict = {}
_SHA: dict = {}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def live(sid):
    """read_slide() of a reference slide, opened read-only, cached for the module."""
    if sid not in _SLIDES:
        did, s = sid.split("-")
        path = DECKS[did]["path"]
        _SHA.setdefault(path, sha256(path))
        deck = open_deck(path)
        try:
            _SLIDES[sid] = read_slide(deck, int(s[1:]))
        finally:
            deck.close()
    return _SLIDES[sid]


def tearDownModule():
    for path, before in _SHA.items():
        assert sha256(path) == before, "source changed: " + path


# ---------------------------------------------------------------------------------------------- synthetic

_NEXT = [100]


def leaf(x, y, w, h, kind="sp", prst="rect", fill=None, line=None, text="", group_path=(), z=None, **kw):
    _NEXT[0] += 1
    L = {"id": _NEXT[0], "kind": kind, "z": _NEXT[0] if z is None else z, "group_path": list(group_path),
         "bbox": {"x_in": x, "y_in": y, "w_in": w, "h_in": h},
         "frame": {"w_in": w, "h_in": h, "rot_deg": 0.0},
         "geom": {"prst": prst, "cust": False}, "on_canvas": "in",
         "fill": {"type": "solid", "hex": fill, "alpha": 1.0} if fill else {"type": "none"},
         "line": {"type": "solid", "hex": line, "w_pt": 0.75} if line else {"type": "none"},
         "text": {"text": text, "words": len(text.split())} if text else None, "line_like": False}
    L.update(kw)
    return L


def slide(shapes, icons=()):
    return {"canvas": {"w_in": W, "h_in": H}, "shapes": shapes, "icons": list(icons),
            "background": {"fill": {"type": "solid", "hex": "FFFFFF"}}}


def card(x, y, w, h, n=3):
    """A drawn box with n text atoms stacked inside it."""
    box = leaf(x, y, w, h, fill="EEEEEE", line="999999")
    inner = [leaf(x + 0.1, y + 0.1 + i * (h - 0.2) / n, w - 0.2, (h - 0.2) / n - 0.05, text="item %d" % i)
             for i in range(n)]
    return [box] + inner


def ids_of(zs, zid):
    return set(next(z for z in zs if z["id"] == zid)["ids"])


class TestSynthetic(unittest.TestCase):
    def test_three_columns_and_title(self):
        sh = [leaf(0.5, 0.3, 12.0, 0.6, text="Title of the slide")]
        cols = [card(0.5 + i * 4.2, 1.5, 3.8, 5.0) for i in range(3)]
        for c in cols:
            sh += c
        zs = zones(slide(sh))
        top = [z for z in zs if z["depth"] == 1]
        self.assertEqual(len(top), 4)
        self.assertEqual(zs[0]["ids"], [sh[0]["id"]])               # the title opens the reading order
        boxes = [z for z in top if z["container"] is not None]
        self.assertEqual([z["container"] for z in boxes], [c[0]["id"] for c in cols])
        for z, c in zip(boxes, cols):
            self.assertEqual(set(z["ids"]), {L["id"] for L in c})
        self.assertEqual([z["id"] for z in zs], ["Z%d" % (i + 1) for i in range(len(zs))])

    def test_clipped_to_canvas(self):
        """A shape bleeding off the left and bottom edges still yields a zone inside 0..100%."""
        sh = [leaf(-2.0, 5.0, 6.0, 4.0, fill="CC0000", text="bleeds off the canvas"),
              leaf(8.0, 1.0, 4.0, 1.0, text="other region")]
        zs = zones(slide(sh))
        self.assertTrue(zs)
        for z in zs:
            x, y, w, h = z["box_pct"]
            self.assertGreaterEqual(x, 0.0)
            self.assertGreaterEqual(y, 0.0)
            self.assertLessEqual(x + w, 100.0 + 1e-6)
            self.assertLessEqual(y + h, 100.0 + 1e-6)

    def test_off_canvas_and_chrome_dropped(self):
        a = leaf(1.0, 1.0, 3.0, 1.0, text="kept")
        off = leaf(20.0, 1.0, 2.0, 1.0, text="gone", on_canvas="off")
        ch = leaf(1.0, 6.0, 3.0, 1.0, text="chrome", layer="chrome")
        zs = zones(slide([a, off, ch]))
        self.assertEqual([z["ids"] for z in zs], [[a["id"]]])

    def test_background_is_not_a_zone(self):
        bg = leaf(0.0, 0.0, W, H, fill="F4F4F4")
        cols = card(0.5, 1.0, 5.0, 5.0) + card(7.0, 1.0, 5.0, 5.0)
        zs = zones(slide([bg] + cols))
        self.assertEqual(len([z for z in zs if z["depth"] == 1]), 2)
        self.assertFalse(any(bg["id"] in z["ids"] for z in zs))

    def test_full_bleed_picture(self):
        pic = leaf(0.0, 0.0, W, H, kind="pic", prst=None)
        label = leaf(0.3, 0.2, 1.0, 0.4, text="home")
        zs = zones(slide([pic, label]))
        fb = [z for z in zs if z["full_bleed"]]
        self.assertEqual(len(fb), 1)
        self.assertEqual(fb[0]["ids"], [pic["id"]])
        self.assertEqual(fb[0]["depth"], 1)
        self.assertEqual(zones(slide([pic]))[0]["full_bleed"], True)    # a screenshot slide has a zone

    def test_nesting_by_area(self):
        outer = leaf(0.5, 0.5, 12.0, 6.0, fill="EEEEEE")
        inner = card(1.0, 1.0, 4.0, 4.0)
        loose = [leaf(6.0, 1.0, 5.0, 1.0, text="note one"), leaf(6.0, 3.0, 5.0, 1.0, text="note two")]
        zs = zones(slide([outer] + inner + loose))
        zo = next(z for z in zs if z["container"] == outer["id"])
        zi = next(z for z in zs if z["container"] == inner[0]["id"])
        self.assertEqual(zi["parent"], zo["id"])
        self.assertEqual(zi["depth"], zo["depth"] + 1)
        self.assertTrue(set(zi["ids"]) < set(zo["ids"]))

    def test_header_tab_joins_its_panel(self):
        """A header bar straddling a panel's top edge belongs to the panel, and the zone box covers it."""
        panel = leaf(1.0, 1.2, 5.0, 4.0, line="CC0000")
        tab = leaf(1.0, 1.0, 5.0, 0.5, fill="CC0000", text="Panel header")
        body = [leaf(1.2, 2.0, 4.6, 0.5, text="row one"), leaf(1.2, 3.0, 4.6, 0.5, text="row two")]
        other = card(7.0, 1.0, 5.0, 4.2)
        zs = zones(slide([panel, tab] + body + other))
        zp = next(z for z in zs if z["container"] == panel["id"])
        self.assertIn(tab["id"], zp["ids"])
        self.assertAlmostEqual(zp["box_in"][1], 1.0, places=3)

    def test_rules_turn_rows_into_columns(self):
        """Two rows of three cards with a tight row gap and rules in the gutters read as three columns."""
        sh = []
        for r in range(2):
            for c in range(3):
                sh += card(0.5 + c * 4.3, 0.5 + r * 3.35, 3.9, 3.3, n=2)
        rules = [leaf(4.6 + c * 4.3, 0.4, 0.0, 6.8, kind="cxn", prst="line", line="999999") for c in range(2)]
        zs = zones(slide(sh + rules))
        top = [z for z in zs if z["depth"] == 1]
        self.assertEqual(len(top), 3)
        for z in top:
            self.assertGreater(z["box_in"][3], 6.0)                     # each column runs the full height
        rule_zone = [z for z in zs if rules[0]["id"] in z["ids"]]
        self.assertTrue(rule_zone)                                    # links join a zone

    def test_tiny_parts_merge(self):
        big = card(0.5, 0.5, 8.0, 6.0)
        dots = [leaf(9.5, 0.5 + i * 0.5, 0.2, 0.2, text=str(i)) for i in range(3)]
        zs = zones(slide(big + dots))
        holder = [z for z in zs if dots[0]["id"] in z["ids"] and z["depth"] == 1]
        self.assertEqual(len(holder), 1)
        self.assertTrue({d["id"] for d in dots} <= set(holder[0]["ids"]))

    def test_group_descended_when_big(self):
        """A group covering 40%+ of the canvas is opened; a small group stays one atom."""
        g = 900
        sh = card(0.5, 0.5, 5.5, 6.0) + card(7.0, 0.5, 5.5, 6.0)
        for L in sh:
            L["group_path"] = [g]
        small = [leaf(0.5, 6.8, 0.3, 0.3, text="a", group_path=[901]),
                 leaf(0.9, 6.8, 0.3, 0.3, text="b", group_path=[901])]
        zs = zones(slide(sh + small))
        self.assertTrue(any(z["container"] == sh[0]["id"] for z in zs))
        self.assertTrue(any(z["container"] == sh[4]["id"] for z in zs))
        for z in zs:
            self.assertEqual(small[0]["id"] in z["ids"], small[1]["id"] in z["ids"])

    def test_cap(self):
        sh = []
        for r in range(6):
            for c in range(6):
                sh += card(0.2 + c * 2.2, 0.2 + r * 1.2, 2.0, 1.05, n=3)
        zs = zones(slide(sh))
        self.assertLessEqual(len(zs), MAX_ZONES)
        ids = {z["id"] for z in zs}
        for z in zs:
            self.assertTrue(z["parent"] is None or z["parent"] in ids)
        self.assertEqual(sorted({z["depth"] for z in zs})[0], 1)

    def test_legacy_forms(self):
        sh = card(0.5, 0.5, 5.0, 5.0) + card(7.0, 0.5, 5.0, 5.0)
        s = slide(sh)
        new = zones(s)
        old = zones(sh, W, H)
        self.assertEqual(set(old), {"zones", "containers"})
        self.assertEqual([z["ids"] for z in old["zones"]], [z["ids"] for z in new])
        self.assertEqual(slide_zones(s)["zones"], new)
        self.assertIs(read_zones, zones)
        self.assertEqual(old["containers"][sh[0]["id"]], [L["id"] for L in sh[1:4]])

    def test_empty(self):
        self.assertEqual(zones(slide([])), [])


class TestRectPath(unittest.TestCase):
    def path(self, body, w=100, h=50):
        return etree.fromstring('<a:pathLst xmlns:a="%s"><a:path w="%d" h="%d">%s</a:path></a:pathLst>'
                                % (NS["a"], w, h, body))

    def test_rectangle(self):
        pts = "".join('<a:%s><a:pt x="%d" y="%d"/></a:%s>' % (t, x, y, t)
                      for t, x, y in (("moveTo", 0, 0), ("lnTo", 100, 0), ("lnTo", 100, 50), ("lnTo", 0, 50)))
        self.assertTrue(rect_path(self.path(pts + "<a:close/>")))

    def test_not_rectangle(self):
        tri = "".join('<a:%s><a:pt x="%d" y="%d"/></a:%s>' % (t, x, y, t)
                      for t, x, y in (("moveTo", 0, 0), ("lnTo", 100, 0), ("lnTo", 50, 50), ("lnTo", 0, 0)))
        self.assertFalse(rect_path(self.path(tri)))
        curve = ('<a:moveTo><a:pt x="0" y="0"/></a:moveTo><a:cubicBezTo><a:pt x="10" y="0"/><a:pt x="90" y="0"/>'
                 '<a:pt x="100" y="50"/></a:cubicBezTo><a:lnTo><a:pt x="0" y="50"/></a:lnTo>')
        self.assertFalse(rect_path(self.path(curve)))
        self.assertFalse(rect_path(None))


# ---------------------------------------------------------------------------------------------- reference

def text_leaf(s, needle):
    for L in s["shapes"]:
        t = (L.get("text") or {}).get("text") or ""
        if needle in t:
            return L["id"]
    raise AssertionError("no leaf with text %r" % needle)


class TestReferenceSlides(unittest.TestCase):
    def test_d08_s007_regions(self):
        """Data sources, the Fabric panel, integration, agent plane, the external column, the legend and the
        governance band each have their own zone at depth 1 or 2 (a zone holding its markers and no other
        region's)."""
        s = live("d08-s007")
        zs = zones(s)
        regions = {"sources": ["Data Sources"], "fabric": ["Microsoft Fabric", "Consumption Workspace"],
                   "integration": ["Enterprise Integration Subscription"],
                   "agents": ["Cloud Subscription Agent Plane"], "external": ["NAT Gateway", "External agents"],
                   "legend": ["Legend"], "governance": ["Enterprise Governance & Security"]}
        marks = {k: {text_leaf(s, t) for t in v} for k, v in regions.items()}
        found = {}
        for k, mine in marks.items():
            others = set().union(*(v for kk, v in marks.items() if kk != k))
            hit = [z for z in zs if z["depth"] <= 2 and mine <= set(z["ids"]) and not others & set(z["ids"])]
            if hit:
                found[k] = hit[0]["id"]
        self.assertEqual(sorted(found), sorted(regions), found)
        self.assertEqual(len(set(found.values())), len(regions))
        self.assertGreaterEqual(sum(1 for z in zs if z["depth"] <= 2), 6)

    def test_d01_s069_year_columns(self):
        """Each year column (between the dashed rules at 27.2, 50.2 and 73.3% of the width) has a zone of its
        own spanning the agent panel and the platform rows below it."""
        zs = zones(live("d01-s069"))
        edges = [0.0, 27.2, 50.2, 73.3, 100.0]
        for c in range(4):
            col = [z for z in zs if z["depth"] <= 2 and z["box_pct"][0] >= edges[c] - 0.5
                   and z["box_pct"][0] + z["box_pct"][2] <= edges[c + 1] + 0.5 and z["box_pct"][3] >= 50.0]
            self.assertTrue(col, "no zone for year column %d" % (c + 1))

    def test_d05_s001_inside_canvas(self):
        zs = zones(live("d05-s001"))
        self.assertGreaterEqual(len(zs), 5)
        for z in zs:
            x, y, w, h = z["box_pct"]
            self.assertTrue(0 <= x and 0 <= y and x + w <= 100.0001 and y + h <= 100.0001, z)
        self.assertGreaterEqual(sum(1 for z in zs if z["depth"] == 1), 4)

    def test_d02_s023_full_bleed(self):
        zs = zones(live("d02-s023"))
        fb = [z for z in zs if z["full_bleed"]]
        self.assertEqual(len(fb), 1)
        self.assertEqual(fb[0]["depth"], 1)
        self.assertEqual(fb[0]["kinds"], {"pic": 1})


class TestCorpus(unittest.TestCase):
    def test_corpus(self):
        """Every extracted slide (shapes/dNN/sNNN.json): no zone outside the canvas, at most 24 zones, a zone
        on every slide with on-canvas content, and the dominant-zone share on dense slides under 15%."""
        files = sorted(glob.glob(os.path.join(LIB, "shapes", "d*", "s*.json")))
        self.assertEqual(len(files), sum(d["slides"] for d in DECKS.values()))
        dense = dominant = outside = 0
        for f in files:
            s = json.load(open(f))
            zs = zones(s)
            self.assertLessEqual(len(zs), MAX_ZONES, f)
            if any(L.get("on_canvas") != "off" for L in s["shapes"]):
                self.assertTrue(zs, f)
            for z in zs:
                x, y, w, h = z["box_pct"]
                outside += not (x >= 0 and y >= 0 and x + w <= 100.0001 and y + h <= 100.0001)
            n = len(s["shapes"])
            if n >= 30:
                dense += 1
                dominant += any(z["depth"] == 1 and z["n"] >= 0.85 * n for z in zs)
        print("\n[zones corpus: %d slides, %d dense, %d dominant (%.1f%%), %d outside]"
              % (len(files), dense, dominant, 100.0 * dominant / max(dense, 1), outside))
        self.assertEqual(outside, 0)
        self.assertLess(dominant / dense, 0.15)


if __name__ == "__main__":
    unittest.main()
