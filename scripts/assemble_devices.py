"""Assemble the device library from devices/work/DLnn/{device.pptx, device.json} (ruling 3, ruling 14).

    $PY scripts/assemble_devices.py [--no-render] [--out DIR]

Writes devices/devices.pptx (one slide per device, in id order, each tagged with its archetype and variant),
devices/devices.json ({about, devices: {id: entry + index}}), references/device-library.md and
devices/renders/<id>-<theme>.png under the sigmoid and neutral themes. --out DIR writes all of it under DIR
instead (a dry run that leaves the published library alone). Then gates the assembled file for what a library
must hold whatever its contents: P01 floor, P03 bounds, P11 style, P12 package, P16 colour roles, P17
fingerprints, P18 leak, P22 icons, P25 contrast. Exit 1 on a missing or invalid entry, a family outside the
frozen taxonomy, or a failed gate. Device sample strings are expected here; P19 is what catches them once a
device is placed in a deck.

At assembly every device is held to two house rules whatever its build did:
- inside the content band (WIDE.content x 0.50 to 12.90in; bleed.* shapes excepted), by fit_band;
- no accent-tint or accent-wash container under 4 sq in (ruling 12, P16) unless named state.*: it becomes card.

Every entry gains, measured here:
- capacity_words: every text and title slot filled to max_words;
- archetype_floors and short_of_floor: the advisory word floor of each archetype it serves, and the archetypes
  whose floor the device cannot reach on its own (compose a rail or a stat row beside it, or pick another device);
- paras on each text slot: how many paragraphs the sample holds (a list value maps one string to each).

Device builds import fit_band, remap_small_tints and finish from here, so device.pptx and the library agree.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ARCH_JSON, KIT, PY, SKILL  # noqa: E402

sys.path.insert(0, str(KIT))
from pptx import Presentation  # noqa: E402

from deckkit import package, tag  # noqa: E402
from deckkit.clone import DEVICE_STRIP, copy_shapes  # noqa: E402
from deckkit.theme import Theme, apply_theme  # noqa: E402

DEV = SKILL / "devices"
WORK = DEV / "work"
REQUIRED = ("id", "name", "archetypes", "family", "variant", "mechanism", "slots", "samples")
GATES = "P01,P03,P11,P12,P16,P17,P18,P22,P25"
FAMILIES = SKILL / "gates" / "families.json"
EMU = 914400
BAND = (0.50, 12.90)          # WIDE.content left and right edges (P03 content margins)
SMALL_TINT_SQIN = 4.0         # P16: an accent-tint or accent-wash fill below this area is a container, not a ground
TINTS = ("accent-tint", "accent-wash")
A_GRIDCOL = "{http://schemas.openxmlformats.org/drawingml/2006/main}gridCol"


def _local(el) -> str:
    return el.tag.split("}")[1] if isinstance(el.tag, str) and "}" in el.tag else str(el.tag)


def _name_of(el) -> str:
    for c in el:
        if _local(c).startswith("nv"):
            for cc in c:
                if _local(cc) == "cNvPr":
                    return cc.get("name", "")
    return ""


def _xfrm(el):
    if _local(el) == "graphicFrame":
        return next((c for c in el if _local(c) == "xfrm"), None)
    pr = next((c for c in el if _local(c) in ("spPr", "grpSpPr")), None)
    return None if pr is None else next((c for c in pr if _local(c) == "xfrm"), None)


def _top_of(el, tree):
    while el.getparent() is not None and el.getparent() is not tree:
        el = el.getparent()
    return el


def fit_band(slide, lo: float = BAND[0], hi: float = BAND[1], *, title: str = "slot.title") -> float:
    """Hold a device inside the content band (P03): map every top-level shape's x linearly from the device's own
    horizontal extent onto [lo, hi]. bleed.* shapes stay where they are (they run to the slide edge on purpose)
    and the title takes the canvas title band. Widths scale with the map; pictures, rotated shapes and small
    square shapes (discs, glyphs) keep their size and move by their centre, so nothing is distorted. Tables
    scale their grid columns with the frame. Returns the scale applied (1.0 when the device already fits)."""
    from deckkit import geom
    tree = slide.shapes._spTree
    tops = [el for el in tree if _local(el) in ("sp", "cxnSp", "grpSp", "pic", "graphicFrame")]
    keep = {id(el) for el in tops if _name_of(el).startswith("bleed.") or _name_of(el) == title}
    for el in tops:                                  # the title sits in the canvas title band
        if _name_of(el) == title and _xfrm(el) is not None:
            xf = _xfrm(el)
            next(c for c in xf if _local(c) == "off").set("x", str(int(round(lo * EMU))))
            next(c for c in xf if _local(c) == "ext").set("cx", str(int(round((hi - lo) * EMU))))
    xs = []
    for g in geom.iter_abs(slide, hidden=False):
        if id(_top_of(g.el, tree)) in keep or not g.has_xfrm:
            continue
        xs += [g.x, g.x + g.w]
    if not xs:
        return 1.0
    x0, x1 = min(xs), max(xs)
    if x0 >= lo - 1e-3 and x1 <= hi + 1e-3:
        return 1.0
    f = min(1.0, (hi - lo) / (x1 - x0))
    base = lo if f < 1.0 else min(max(x0, lo), hi - (x1 - x0))
    X = lambda x: base + (x - x0) * f            # noqa: E731
    for el in tops:
        xf = _xfrm(el)
        if id(el) in keep or xf is None:
            continue
        off = next(c for c in xf if _local(c) == "off")
        ext = next(c for c in xf if _local(c) == "ext")
        x, w, h = int(off.get("x")) / EMU, int(ext.get("cx")) / EMU, int(ext.get("cy")) / EMU
        rot = (int(xf.get("rot", "0")) / 60000.0) % 180
        if _local(el) == "pic" or (abs(w - h) < 0.02 and max(w, h) <= 1.2):
            nw = w                                   # a glyph, a disc, a picture: same size, centre mapped
        elif abs(rot - 90) < 1:
            nw = w                                   # stored height paints across: scale that instead, same centre
            ext.set("cy", str(int(round(h * f * EMU))))
            off.set("y", str(int(round((int(off.get("y")) / EMU + h * (1 - f) / 2) * EMU))))
        elif rot > 0.5:
            nw = w
        else:
            nw = w * f
        off.set("x", str(int(round((X(x + w / 2) - nw / 2) * EMU))))
        ext.set("cx", str(int(round(nw * EMU))))
        if _local(el) == "graphicFrame" and abs(nw - w) > 1e-9:
            for gc in el.iter(A_GRIDCOL):
                gc.set("w", str(int(round(int(gc.get("w")) * nw / w))))
    return f


def remap_small_tints(slide, theme, *, limit: float = SMALL_TINT_SQIN) -> list[str]:
    """Ruling 12 and P16: pastel tint is for large grounds only. Every shape filled accent-tint or accent-wash
    whose painted area is under `limit` square inches, and that is not named state.*, is refilled card. Returns
    the names changed."""
    from deckkit import geom
    tint = {(theme.roles[r].slot, tuple(theme.roles[r].mods)): r for r in TINTS}
    done = []
    for g in geom.iter_abs(slide, hidden=False):
        if g.name.startswith("state.") or g.w * g.h >= limit:
            continue
        pr = next((c for c in g.el if _local(c) in ("spPr", "grpSpPr")), None)
        sf = None if pr is None else next((c for c in pr if _local(c) == "solidFill"), None)
        clr = None if sf is None or not len(sf) else sf[0]
        if clr is None or _local(clr) != "schemeClr":
            continue
        mods = tuple((_local(m), int(m.get("val"))) for m in clr if isinstance(m.tag, str))
        if (clr.get("val"), mods) not in tint:
            continue
        sf.replace(clr, theme.spec("card"))
        done.append(g.name)
    return done


_P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def bent_points(el) -> list | None:
    """The route PowerPoint draws for a bentConnector2/3/4 (preset path, adjust values, flips, then rotation about
    the centre), in slide inches; None for any other shape. LibreOffice re-routes these between their two ends, so
    a rotated or flipped bent connector renders on another path there than in PowerPoint."""
    import math
    sp = el.find(_P + "spPr")
    xf = None if sp is None else sp.find(_A + "xfrm")
    geo = None if sp is None else sp.find(_A + "prstGeom")
    if xf is None or geo is None or not (geo.get("prst") or "").startswith("bentConnector"):
        return None
    off, ext = xf.find(_A + "off"), xf.find(_A + "ext")
    x, y = int(off.get("x")) / EMU, int(off.get("y")) / EMU
    w, h = int(ext.get("cx")) / EMU, int(ext.get("cy")) / EMU
    adj = {g.get("name"): int(g.get("fmla").split()[1]) / 100000 for g in geo.iter(_A + "gd")}
    a1, a2 = adj.get("adj1", 0.5), adj.get("adj2", 0.5)
    path = {"bentConnector2": [(0, 0), (w, 0), (w, h)],
            "bentConnector3": [(0, 0), (w * a1, 0), (w * a1, h), (w, h)],
            "bentConnector4": [(0, 0), (w * a1, 0), (w * a1, h * a2), (w, h * a2), (w, h)]}.get(geo.get("prst"))
    if path is None:
        return None
    if xf.get("flipH") in ("1", "true"):
        path = [(w - px, py) for px, py in path]
    if xf.get("flipV") in ("1", "true"):
        path = [(px, h - py) for px, py in path]
    t = math.radians(int(xf.get("rot", "0")) / 60000.0)
    c, s_ = math.cos(t), math.sin(t)
    pts = [(x + w / 2 + (px - w / 2) * c - (py - h / 2) * s_, y + h / 2 + (px - w / 2) * s_ + (py - h / 2) * c)
           for px, py in path]
    out = []
    for p in pts:                                    # drop zero-length segments
        if not out or abs(p[0] - out[-1][0]) > 1e-4 or abs(p[1] - out[-1][1]) > 1e-4:
            out.append((round(p[0], 4), round(p[1], 4)))
    return out


def bake_bent(slide, names=None) -> list[str]:
    """Redraw each bent connector (or only those named) as straight connector segments along the route PowerPoint
    draws, keeping its line (colour, weight, dash) and its heads on the first and last segment, so every renderer
    draws one route: the one the reader sees in PowerPoint. LibreOffice never re-routes an unglued straight
    connector. Segments are named <name>.part<k>. Returns the names baked."""
    import copy
    done = []
    tree = slide.shapes._spTree
    top = max(int(c.get("id", "0")) for c in tree.iter(_P + "cNvPr"))
    for el in list(tree.iter(_P + "cxnSp")):
        nm = _name_of(el)
        pts = bent_points(el)
        if pts is None or (names is not None and nm not in names):
            continue
        segs = list(zip(pts, pts[1:]))
        for k, ((x1, y1), (x2, y2)) in enumerate(segs, 1):
            seg = copy.deepcopy(el)
            top += 1
            cnv = seg.find(".//" + _P + "cNvPr")
            cnv.set("id", str(top))
            cnv.set("name", "%s.part%d" % (nm, k))
            for c in seg.findall(".//" + _P + "cNvCxnSpPr"):
                for g in list(c):
                    c.remove(g)                          # unglued, so nothing re-routes it
            pr = seg.find(_P + "spPr")
            xf, geo = pr.find(_A + "xfrm"), pr.find(_A + "prstGeom")
            for att in ("rot", "flipH", "flipV"):
                xf.attrib.pop(att, None)
            if x2 < x1:
                xf.set("flipH", "1")
            if y2 < y1:
                xf.set("flipV", "1")
            xf.find(_A + "off").set("x", str(int(round(min(x1, x2) * EMU))))
            xf.find(_A + "off").set("y", str(int(round(min(y1, y2) * EMU))))
            xf.find(_A + "ext").set("cx", str(int(round(abs(x2 - x1) * EMU))))
            xf.find(_A + "ext").set("cy", str(int(round(abs(y2 - y1) * EMU))))
            geo.set("prst", "straightConnector1")
            av = geo.find(_A + "avLst")
            if av is not None:
                for g in list(av):
                    av.remove(g)
            ln = pr.find(_A + "ln")
            if ln is not None:
                for end, keep in (("headEnd", k == 1), ("tailEnd", k == len(segs))):
                    e = ln.find(_A + end)
                    if e is not None and not keep:
                        e.set("type", "none")
            el.addprevious(seg)
        el.getparent().remove(el)
        done.append(nm)
    return done


def finish(slide, theme) -> None:
    """What every device build ends on before save: inside the content band, no small tint container."""
    fit_band(slide)
    remap_small_tints(slide, theme)


def floors() -> dict:
    """Advisory word floor per archetype on the wide canvas (ruling 17: the measured p25)."""
    if not ARCH_JSON.is_file():
        return {}
    arch = json.loads(ARCH_JSON.read_text())["archetypes"]
    return {k: (v.get("budget", {}).get("wide", {}) or {}).get("floor") for k, v in arch.items()
            if (v.get("budget", {}).get("wide", {}) or {}).get("floor")}


def capacity(entry: dict, fl: dict) -> dict:
    """The device's word capacity (every text and title slot at max_words) against the floor of each archetype it
    serves, so a builder knows before filling when the device cannot reach the floor on its own."""
    cap = sum(int(sl.get("max_words") or 0) for sl in entry["slots"] if sl.get("kind") in ("text", "title"))
    own = {a: fl[a] for a in entry["archetypes"] if a in fl}
    return {"capacity_words": cap, "archetype_floors": own,
            "short_of_floor": sorted(a for a, v in own.items() if cap < v)}


def _paras(el) -> int:
    n = 0
    for p in el.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}p"):
        if "".join(t.text or "" for t in p.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}t")).strip():
            n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--out", help="write the library under this folder instead of devices/ and references/")
    a = ap.parse_args()
    dest = Path(a.out).resolve() if a.out else DEV
    ref_md = (dest / "device-library.md") if a.out else (SKILL / "references" / "device-library.md")
    dest.mkdir(parents=True, exist_ok=True)
    th = Theme.load(SKILL / "themes" / "sigmoid.json")
    fams = set(json.loads(FAMILIES.read_text())["families"])
    fl = floors()
    entries, errs = [], []
    from deckkit.theme import ROLES
    for d in sorted(p for p in WORK.iterdir() if p.is_dir() and p.name.startswith("DL")):
        pj, pp = d / "device.json", d / "device.pptx"
        if not pj.is_file() or not pp.is_file():
            errs.append("%s: device.json or device.pptx missing" % d.name)
            continue
        e = json.loads(pj.read_text())
        miss = [k for k in REQUIRED if k not in e]
        if miss or e.get("id") != d.name:
            errs.append("%s: %s" % (d.name, ("missing " + ", ".join(miss)) if miss else "id does not match its folder"))
            continue
        if e["family"] not in fams:
            errs.append("%s: family %r is not in the frozen taxonomy (%s)" % (d.name, e["family"], ", ".join(sorted(fams))))
            continue
        for sl in e.get("slots", []):                 # a slot's role is a theme colour role; anything else is its purpose
            if sl.get("role") and sl["role"] not in set(ROLES) | {"paper"}:
                sl["purpose"] = sl.pop("role")
        entries.append((e, pp))
    if errs:
        for x in errs:
            print("FAIL", x)
        return 1
    prs = Presentation(str(SKILL / "kit" / "assets" / "base-wide.pptx"))
    out = {}
    for i, (e, pp) in enumerate(entries, 1):
        src = Presentation(str(pp)).slides[0]
        shapes = {}
        stack = list(src.shapes)
        while stack:
            sh = stack.pop()
            shapes[sh.name] = sh._element
            if sh.shape_type == 6:
                stack.extend(sh.shapes)
        missing = [sl["name"] for sl in e["slots"] if sl["name"] not in shapes]
        if missing:                                   # a templated or stale slot name: drop it, say so
            e["slots"] = [sl for sl in e["slots"] if sl["name"] in shapes]
            e["slot_notes"] = "dropped %d slot names with no shape: %s" % (len(missing), ", ".join(missing[:4]))
            print("NOTE %s %s" % (e["id"], e["slot_notes"]))
        for sl in e["slots"]:
            if sl.get("kind") == "text":
                sl["paras"] = max(1, _paras(shapes[sl["name"]]))
        s = prs.slides.add_slide(prs.slide_layouts[0])
        copy_shapes(src, s, strip=DEVICE_STRIP)
        f = fit_band(s)
        tints = remap_small_tints(s, th)
        if abs(f - 1.0) > 1e-3 or tints:
            print("NOTE %s fitted to the content band x%.3f, %d small tint containers to card"
                  % (e["id"], f, len(tints)))
        tag.tag(s, e["archetypes"][0], e["variant"])
        out[e["id"]] = dict(e, **capacity(e, fl), index=i)
    package.save(prs, dest / "devices.pptx", title="Device library", theme=th, overwrite=True, date="2026-10-03")
    (dest / "devices.json").write_text(json.dumps({
        "about": "The device library: native slides lifted from the references, sanitised (identity stripped, every "
                 "word replaced, colours mapped to theme roles, type floored at 8pt) and fitted to the house rules. "
                 "Place one with deckkit.devices.place and fill every slot; a sample left behind fails P19. "
                 "capacity_words is every text slot at max_words; short_of_floor names the archetypes whose word "
                 "floor the device cannot reach alone.",
        "devices": out}, indent=1) + "\n")
    lines = ["# Device library", "", "Native slides lifted from the references, sanitised and theme-mapped (rulings 3 and 14). "
             "Place one with `deckkit.devices.place(prs, id, {slot: value}, theme=th, archetype=...)` and fill every "
             "slot. Words is the capacity with every slot at max_words; a floor marked short cannot be reached by the "
             "device alone. Renders: `devices/renders/<id>-sigmoid.png` and `-neutral.png`.", "",
             "| Id | Device | Archetypes (floor) | Variant | Slots | Words | How it argues |",
             "|---|---|---|---|---|---|---|"]
    for eid, e in out.items():
        arch = ", ".join("%s (%s%s)" % (x, e["archetype_floors"].get(x, "-"),
                                        ", short" if x in e["short_of_floor"] else "") for x in e["archetypes"])
        lines.append("| %s | %s | %s | %s | %d | %d | %s |" % (eid, e["name"], arch, e["variant"], len(e["slots"]),
                                                              e["capacity_words"], e["mechanism"].replace("|", "/")))
    ref_md.write_text("\n".join(lines) + "\n")
    print("OK %d devices -> %s" % (len(out), dest / "devices.pptx"))
    r = subprocess.run([PY, str(SKILL / "gates" / "run_all.py"), "--deck", str(dest / "devices.pptx"), "--only", GATES],
                       capture_output=True, text=True)
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-400:])
    if r.returncode:
        print("\n".join(x for x in r.stdout.splitlines() if "FAIL" in x)[:3000])
    rc = r.returncode
    if not a.no_render:
        rd = dest / "renders"
        rd.mkdir(exist_ok=True)
        for name in ("sigmoid", "neutral"):
            with tempfile.TemporaryDirectory() as tmp:
                deck = Path(tmp) / ("devices-%s.pptx" % name)
                shutil.copy2(dest / "devices.pptx", deck)
                if name != "sigmoid":
                    apply_theme(str(deck), Theme.load(SKILL / "themes" / ("%s.json" % name)), str(deck),
                                from_theme=Theme.load(SKILL / "themes" / "sigmoid.json"))
                subprocess.run([PY, str(SKILL / "scripts" / "render.py"), str(deck), "--out", str(Path(tmp) / "r")],
                               check=True, capture_output=True)
                for j, (eid, _e) in enumerate(out.items(), 1):
                    src = Path(tmp) / "r" / ("slide-%0*d.png" % (len(str(len(out))), j))
                    if not src.is_file():
                        src = Path(tmp) / "r" / ("slide-%d.png" % j)
                    shutil.copy2(src, rd / ("%s-%s.png" % (eid, name)))
        print("rendered %d devices under sigmoid and neutral -> %s" % (len(out), rd))
    return rc


if __name__ == "__main__":
    sys.exit(main())
