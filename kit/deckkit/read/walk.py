"""read_slide: one slide to the flattened shapes@1 dict (render block excluded; the extractor adds it).

Walk order: chrome first (master shapes, then layout shapes, honouring showMasterSp), then the slide
spTree depth-first in document order, which is paint order and gives z. graphicFrame tables expand
into cell leaves. Placeholders without xfrm inherit geometry from the layout placeholder (idx, then
type), then the master placeholder (type).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import statistics

from . import connect as cx
from .colour import fill_from, first_colour, resolve_background, resolve_effects, resolve_fill, resolve_line
from .ns import A, P, first_child, is_true, local
from .opc import TITLE_TYPES, DeckRead, ph_info, txstyle_key
from .pics import picture_facts
from .textprops import TextCtx, _fontref_rpr, body_props, read_text
from .xform import EMU_IN, IDENT, group_child_to_parent, group_scale_own, leaf_geometry, local_point, mul, own, read_xfrm
from .zones import contains, is_rect_like

from lxml import etree

SCHEMA = "shapes@1"
FLOOR_PT = 8.0
ICON_MIN_IN, ICON_MAX_IN, ICON_ASPECT = 0.12, 0.8, 2.5
SYMBOL_FACES = re.compile(r"wingding|webding|symbol|marlett|material|fontawesome|font awesome|segoe ui emoji|"
                          r"segoe mdl2|icons?$", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U0001F000-\U0001F02F\U0001F0A0-\U0001F0FF☀-➿"
                   "\U0001F1E6-\U0001F1FF⭐⭕⬆⬇⬅⤴⤵〰〽️]")
STICKY = re.compile(r"^\s*(?:ready|revise|revised|to revise|to review|review|tbc|tbd|wip|draft)\s*[.!:]?\s*$", re.I)
FINGERPRINTS = os.path.expanduser("~/.claude/hooks/fingerprints.json")
_MC_OK = {"a14", "p14", "p15", "a16", "asvg", "v", "p159", "p188", "pr", "a15", "thm15", "x14"}


# ------------------------------------------------------------------ fingerprint patterns (one home)

_FP = None


def fingerprint_rules() -> dict:
    """Glyph tier plus the deck-voice person, Al-for-AI and placeholder rules, read from the single home."""
    global _FP
    if _FP is not None:
        return _FP
    out = {"glyph": [], "person": None, "al": None, "placeholder": None, "source": None}
    try:
        with open(FINGERPRINTS, encoding="utf-8") as f:
            d = json.load(f)
        for r in d.get("rules", []):
            try:
                rx = re.compile(r["pattern"])
            except re.error:
                continue
            if r.get("tier") == "glyph":
                out["glyph"].append((r["id"], rx))
            elif r.get("id") == "dv-person":
                out["person"] = rx
            elif r.get("id") == "dv-al-ai":
                out["al"] = rx
            elif r.get("id") == "dv-placeholder":
                out["placeholder"] = rx
        out["source"] = FINGERPRINTS
    except (OSError, ValueError):
        out["source"] = None
    _FP = out
    return out


# ------------------------------------------------------------------ helpers

def _nv(el):
    for c in el:
        if local(c).startswith("nv"):
            return c
    return None


def _cnvpr(el):
    nv = _nv(el)
    return nv.find(P("cNvPr")) if nv is not None else None


def _sppr(el):
    for tag in ("spPr", "grpSpPr"):
        e = el.find(P(tag))
        if e is not None:
            return e
    return None


def _round(v, n=3):
    return round(v, n) if v is not None else None


def _geom_block(spPr, w_in: float, h_in: float) -> dict:
    out = {"prst": None, "adj": {}, "cust": False, "paths": 0, "radius_in": None, "point_in": None}
    if spPr is None:
        return out
    pg = spPr.find(A("prstGeom"))
    if pg is not None:
        out["prst"] = pg.get("prst")
        av = pg.find(A("avLst"))
        for gd in (av if av is not None else []):
            f = gd.get("fmla", "")
            if f.startswith("val "):
                try:
                    out["adj"][gd.get("name")] = int(f[4:])
                except ValueError:
                    pass
        ss = min(w_in, h_in)
        p = out["prst"]
        if p in ("roundRect", "round1Rect", "round2SameRect", "round2DiagRect", "snipRoundRect"):
            a = out["adj"].get("adj", out["adj"].get("adj1", 16667))
            out["radius_in"] = round(a / 1e5 * ss, 3)
        elif p in ("chevron", "homePlate"):
            a = out["adj"].get("adj", 50000)
            out["point_in"] = round(a / 1e5 * ss, 3)
    cg = spPr.find(A("custGeom"))
    if cg is not None:
        out["cust"] = True
        pl = cg.find(A("pathLst"))
        out["paths"] = len(pl) if pl is not None else 0
        out["rect_path"] = rect_path(pl)
    return out


def rect_path(path_lst, tol: float = 0.02) -> bool:
    """True when a custGeom draws a plain rectangle: one path of moveTo/lnTo/close whose points are exactly
    the four corners of the path box (within tol of its size). Curves, arcs and guide-named points are False."""
    if path_lst is None or len(path_lst) != 1:
        return False
    path = path_lst[0]
    pts = []
    for cmd in path:
        tag = cmd.tag.split("}")[-1]
        if tag == "close":
            continue
        if tag not in ("moveTo", "lnTo"):
            return False
        pt = cmd.find(A("pt"))
        try:
            pts.append((float(pt.get("x")), float(pt.get("y"))))
        except (TypeError, ValueError, AttributeError):
            return False
    if len(pts) < 4:
        return False
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    pw = float(path.get("w") or 0) or (x1 - x0)
    ph = float(path.get("h") or 0) or (y1 - y0)
    if pw <= 0 or ph <= 0 or (x1 - x0) < (1 - 2 * tol) * pw or (y1 - y0) < (1 - 2 * tol) * ph:
        return False
    corners = set()
    for x, y in pts:
        cx = 0 if abs(x - x0) <= tol * pw else 1 if abs(x - x1) <= tol * pw else None
        cy = 0 if abs(y - y0) <= tol * ph else 1 if abs(y - y1) <= tol * ph else None
        if cx is None or cy is None:
            return False
        corners.add((cx, cy))
    return len(corners) == 4


def _on_canvas(b, cw, ch, tol=0.01) -> str:
    x0, y0, w, h = b
    x1, y1 = x0 + w, y0 + h
    if x1 < -tol or y1 < -tol or x0 > cw + tol or y0 > ch + tol:
        return "off"
    if x0 >= -tol and y0 >= -tol and x1 <= cw + tol and y1 <= ch + tol:
        return "in"
    if x1 <= 0 or y1 <= 0 or x0 >= cw or y0 >= ch:
        return "off"
    return "partial"


# ------------------------------------------------------------------ walker

class Walker:
    def __init__(self, deck: DeckRead, slide_part: str, light: bool = False):
        self.deck = deck
        self.light = light
        self.slide_part = slide_part
        self.root = deck.xml(slide_part)
        self.layout_part = deck.layout_part_of(slide_part)
        self.li = deck.layout(self.layout_part) if self.layout_part else None
        self.mi = deck.master(self.li.master_part) if self.li and self.li.master_part else None
        from .colour import parse_clrmap
        ovr = parse_clrmap(self.root.find(P("clrMapOvr")))
        cm = ovr or (self.li.clrmap_ovr if self.li else None) or (self.mi.clrmap if self.mi else None)
        self.cctx = self.mi.colour.with_clrmap(cm) if self.mi else None
        self.cw, self.ch = deck.w_in, deck.h_in
        self.leaves: list[dict] = []
        self.groups: list[dict] = []
        self.hidden_ids: list[int] = []
        self.layer = "content"
        self.max_id = 0
        self.child_order: list[tuple[str, int, int]] = []   # (layer, parent group id, child id) in document order

    # -- text context
    def text_ctx(self, el, ph: dict | None, ph_layout, ph_master, extra_rpr=None) -> tuple[TextCtx, dict]:
        mi = self.mi
        txBody = el.find(P("txBody"))
        if txBody is None:
            txBody = el.find(A("txBody"))
        style = el.find(P("style"))

        def lst(e):
            if e is None:
                return None
            tb = e.find(P("txBody"))
            return tb.find(A("lstStyle")) if tb is not None else None

        def bpr(e):
            if e is None:
                return None
            tb = e.find(P("txBody"))
            if tb is None:
                tb = e.find(A("txBody"))
            return tb.find(A("bodyPr")) if tb is not None else None

        tc = TextCtx(colour=self.cctx, theme_major=mi.theme["fonts"]["major"] if mi else None,
                     theme_minor=mi.theme["fonts"]["minor"] if mi else None,
                     pres_default=self.deck.default_text_style,
                     lst_style=txBody.find(A("lstStyle")) if txBody is not None else None,
                     fontref_rpr=_fontref_rpr(style), extra_rpr=extra_rpr)
        chain_bodies = [txBody.find(A("bodyPr")) if txBody is not None else None]
        if ph is not None:
            tc.ph_type = ph["type"]
            tc.is_title_ph = ph["type"] in TITLE_TYPES
            tc.layout_ph_lst = lst(ph_layout)
            tc.master_ph_lst = lst(ph_master)
            tc.master_txstyle = mi.txstyles.get(txstyle_key(ph["type"])) if mi else None
            chain_bodies += [bpr(ph_layout), bpr(ph_master)]
        body = body_props(chain_bodies, tc)
        if body["autofit"] == "norm":
            tc.font_scale = body["font_scale"]
            tc.ln_spc_reduction = body["ln_spc_reduction"]
        return tc, body

    # -- spTree walk
    def walk(self, tree, part: str, M=IDENT, group_path=(), group_fill=None, parent_gid=0, ph_ok=True):
        for el in tree:
            t = local(el)
            if t == "AlternateContent":
                el = self._mc_pick(el)
                if el is None:
                    continue
                for sub in el:
                    self._one(sub, part, M, group_path, group_fill, parent_gid, ph_ok)
                continue
            self._one(el, part, M, group_path, group_fill, parent_gid, ph_ok)

    def _mc_pick(self, ac):
        for ch in ac:
            if local(ch) == "Choice":
                req = (ch.get("Requires") or "").split()
                if all(r in _MC_OK for r in req):
                    return ch
        for ch in ac:
            if local(ch) == "Fallback":
                return ch
        return None

    def _one(self, el, part, M, group_path, group_fill, parent_gid, ph_ok):
        t = local(el)
        if t not in ("sp", "pic", "cxnSp", "grpSp", "graphicFrame", "contentPart"):
            return
        c = _cnvpr(el)
        sid = int(c.get("id", "0")) if c is not None else 0
        self.max_id = max(self.max_id, sid)
        if c is not None and is_true(c.get("hidden")):
            self.hidden_ids.append(sid)
            return
        ph = ph_info(el)
        if ph is not None and not ph_ok:
            return                      # master/layout placeholders do not render on the slide
        if parent_gid:
            self.child_order.append((self.layer, parent_gid, sid))
        if t == "grpSp":
            self._group(el, part, M, group_path, group_fill, parent_gid, ph_ok)
        elif t == "graphicFrame":
            self._frame(el, part, M, group_path, parent_gid)
        elif t == "contentPart":
            return
        else:
            self._leaf(el, t, part, M, group_path, group_fill, parent_gid, ph)

    def _group(self, el, part, M, group_path, group_fill, parent_gid, ph_ok):
        c = _cnvpr(el)
        gid = int(c.get("id", "0")) if c is not None else 0
        gsp = el.find(P("grpSpPr"))
        r = read_xfrm(gsp.find(A("xfrm")) if gsp is not None else None)
        fill_el = first_child(gsp, ("noFill", "solidFill", "gradFill", "blipFill", "pattFill", "grpFill")) \
            if gsp is not None else None
        gfill = group_fill
        if fill_el is not None and self.cctx is not None:
            gfill = fill_from(fill_el, self.cctx, "grpSpPr", group_fill=group_fill)
        if r is None:
            Mi = M
            rec_geo = None
        else:
            Mi = mul(M, group_child_to_parent(r))
            rec_geo = leaf_geometry(r, M)
        rec = {"id": gid, "name": c.get("name", "") if c is not None else "", "parent": parent_gid,
               "depth": len(group_path) + 1, "layer": self.layer, "bbox": None, "scale": [1.0, 1.0],
               "rot_deg": 0.0, "mirrored": False, "children": []}
        if r is not None:
            sx, sy = group_scale_own(r)
            b = rec_geo["bbox_in"]
            rec.update(bbox=self._bbox(b), scale=[round(sx, 4), round(sy, 4)], rot_deg=round(r["rot"], 2),
                       mirrored=bool(r["fh"]) != bool(r["fv"]),
                       scale_abs=[round(math.hypot(Mi[0], Mi[1]), 4), round(math.hypot(Mi[2], Mi[3]), 4)],
                       rot_abs_deg=rec_geo["frame"]["rot_deg"])
        self.groups.append(rec)
        n0 = len(self.leaves)
        self.walk(el, part, Mi, group_path + (gid,), gfill, gid, ph_ok)
        rec["_leaf_range"] = (n0, len(self.leaves))

    def _bbox(self, b) -> dict:
        x, y, w, h = b
        return {"x_in": round(x, 3), "y_in": round(y, 3), "w_in": round(w, 3), "h_in": round(h, 3),
                "x_pct": round(100 * x / self.cw, 2), "y_pct": round(100 * y / self.ch, 2),
                "w_pct": round(100 * w / self.cw, 2), "h_pct": round(100 * h / self.ch, 2)}

    def _base(self, el, kind, sid, name, c, group_path, parent_gid, r, M) -> dict:
        geo = leaf_geometry(r, M)
        b = geo["bbox_in"]
        fr = geo["frame"]
        rec = {"id": sid, "name": name, "descr": c.get("descr", "") if c is not None else "",
               "title": c.get("title", "") if c is not None else "", "kind": kind, "z": None,
               "group_path": list(group_path), "depth": len(group_path), "placeholder": None,
               "geom": None,
               "xfrm": {"x": r["x"], "y": r["y"], "w": r["w"], "h": r["h"], "rot": round(r["rot"], 3),
                        "flipH": r["fh"], "flipV": r["fv"]},
               "frame": {"cx_in": round(fr["cx_in"], 3), "cy_in": round(fr["cy_in"], 3),
                         "w_in": round(fr["w_in"], 3), "h_in": round(fr["h_in"], 3), "rot_deg": fr["rot_deg"],
                         "mirrored": fr["mirrored"], "sheared": fr["sheared"]},
               "bbox": self._bbox(b),
               "corners_in": [[round(px, 4), round(py, 4)] for px, py in geo["corners_in"]],
               "group_scale": list(geo["group_scale"]),
               "on_canvas": _on_canvas(b, self.cw, self.ch),
               "fill": None, "grad": None, "line": None, "effects": None, "text": None, "picture": None,
               "connector": None, "cell": None, "role_guess": None, "icon_like": False, "line_like": False,
               "container_of": [], "sig": None, "layer": self.layer, "_geo": geo, "_r": r, "_M": M}
        return rec

    def _inherit_ph(self, ph):
        """Layout placeholder (idx then type), then master placeholder (type)."""
        if ph is None or self.layer != "content":
            return None, None
        lay = self.li.ph.match(ph, "layout") if self.li else None
        lay_info = ph_info(lay) if lay is not None else None
        mas = self.mi.ph.match(lay_info or ph, "master") if self.mi else None
        return lay, mas

    def _leaf(self, el, t, part, M, group_path, group_fill, parent_gid, ph):
        c = _cnvpr(el)
        sid = int(c.get("id", "0")) if c is not None else 0
        name = c.get("name", "") if c is not None else ""
        spPr = el.find(P("spPr"))
        ph_lay, ph_mas = self._inherit_ph(ph)
        x = spPr.find(A("xfrm")) if spPr is not None else None
        r = read_xfrm(x)
        geom_from = "own"
        if r is None:
            for src, e in (("layout", ph_lay), ("master", ph_mas)):
                if e is None:
                    continue
                sp2 = _sppr(e)
                r = read_xfrm(sp2.find(A("xfrm")) if sp2 is not None else None)
                if r is not None:
                    geom_from = src
                    break
        if r is None:
            r = dict(x=0, y=0, w=0, h=0, rot=0.0, fh=False, fv=False)
            geom_from = "none"
        kind = {"sp": "sp", "pic": "pic", "cxnSp": "cxn"}[t]
        rec = self._base(el, kind, sid, name, c, group_path, parent_gid, r, M)
        if ph is not None:
            matched = "layout" if ph_lay is not None else ("master" if ph_mas is not None else "none")
            rec["placeholder"] = {"type": ph["type"], "idx": ph["idx"], "matched": matched, "geom_from": geom_from}
        style = el.find(P("style"))
        if style is None:
            for e in (ph_lay, ph_mas):
                if e is not None and e.find(P("style")) is not None:
                    style = e.find(P("style"))
                    break
        # spPr chain for placeholder property inheritance
        chain = [spPr] + [_sppr(e) for e in (ph_lay, ph_mas) if e is not None]
        chain = [s for s in chain if s is not None]
        fill_sp = next((s for s in chain if first_child(s, ("noFill", "solidFill", "gradFill", "blipFill",
                                                            "pattFill", "grpFill")) is not None), spPr)
        ln_sp = next((s for s in chain if s.find(A("ln")) is not None), spPr)
        eff_sp = next((s for s in chain if s.find(A("effectLst")) is not None), spPr)
        fr = rec["frame"]
        rec["geom"] = _geom_block(spPr if (spPr is not None and (spPr.find(A("prstGeom")) is not None or
                                                                  spPr.find(A("custGeom")) is not None))
                                  else (chain[1] if len(chain) > 1 else spPr), fr["w_in"], fr["h_in"])
        if self.cctx is not None:
            f = resolve_fill(fill_sp, style, self.cctx, group_fill)
            rec["grad"] = f.pop("grad", None)
            rec["fill"] = f
            rec["line"] = resolve_line(ln_sp, style, self.cctx)
            rec["effects"] = resolve_effects(eff_sp, style, self.cctx)
        if t == "pic" and not self.light:
            rec["picture"] = picture_facts(self.deck, part, el, fr["w_in"], fr["h_in"],
                                           tuple(rec["_geo"]["bbox_in"]), name, rec["descr"], rec["title"],
                                           in_chrome=self.layer != "content")
        # text
        if t == "sp":
            tb = el.find(P("txBody"))
            if tb is not None and self.cctx is not None:
                tc, body = self.text_ctx(el, ph, ph_lay, ph_mas)
                rec["text"] = read_text(tb, tc, body)
        # line-like and connectors
        prst = rec["geom"]["prst"] or ""
        if t == "cxnSp" or prst in cx.LINE_PRESETS or prst in cx.BLOCK_ARROWS:
            rec["line_like"] = True
            if prst in cx.BLOCK_ARROWS:
                (u0, v0), (u1, v1) = cx.BLOCK_ARROWS[prst]
                s, e = local_point(r, M, u0, v0), local_point(r, M, u1, v1)
            else:
                s, e = rec["_geo"]["start_in"], rec["_geo"]["end_in"]
            rec["connector"] = cx.connector_block(prst or "custom", s, e, rec["line"],
                                                  cx.glue(el) if t == "cxnSp" else None)
        self.leaves.append(rec)

    # -- graphic frames and tables
    def _frame(self, el, part, M, group_path, parent_gid):
        c = _cnvpr(el)
        sid = int(c.get("id", "0")) if c is not None else 0
        name = c.get("name", "") if c is not None else ""
        r = read_xfrm(el.find(P("xfrm")))
        if r is None:
            r = dict(x=0, y=0, w=0, h=0, rot=0.0, fh=False, fv=False)
        gd = el.find(A("graphic") + "/" + A("graphicData"))
        uri = gd.get("uri", "") if gd is not None else ""
        tbl = gd.find(A("tbl")) if gd is not None else None
        if tbl is None:
            rec = self._base(el, "graphic", sid, name, c, group_path, parent_gid, r, M)
            rec["geom"] = {"prst": None, "adj": {}, "cust": False, "paths": 0, "radius_in": None, "point_in": None}
            rec["graphic"] = {"uri": uri, "kind": uri.rsplit("/", 1)[-1]}
            rec["fill"] = {"type": "none", "via": "default"}
            rec["line"] = {"type": "none", "via": "default"}
            rec["effects"] = None
            self.leaves.append(rec)
            return
        self._table(el, tbl, sid, name, c, part, M, group_path, parent_gid, r)

    def _table(self, el, tbl, sid, name, c, part, M, group_path, parent_gid, r):
        grid = [int(g.get("w", "0")) for g in tbl.findall(A("tblGrid") + "/" + A("gridCol"))]
        rows = tbl.findall(A("tr"))
        tblPr = tbl.find(A("tblPr"))
        flags = {k: is_true(tblPr.get(k)) if tblPr is not None else False
                 for k in ("firstRow", "lastRow", "firstCol", "lastCol", "bandRow", "bandCol")}
        style_id = None
        if tblPr is not None:
            sidel = tblPr.find(A("tableStyleId"))
            style_id = sidel.text.strip() if sidel is not None and sidel.text else None
        style = table_style(self.deck, style_id)
        y = r["y"]
        nrows = len(rows)
        ncols = len(grid)
        for ri, tr in enumerate(rows):
            h = int(tr.get("h", "0"))
            xcur = r["x"]
            for ci, tc in enumerate(tr.findall(A("tc"))):
                w = grid[ci] if ci < ncols else 0
                if is_true(tc.get("hMerge")) or is_true(tc.get("vMerge")):
                    xcur += w
                    continue
                gs, rs = int(tc.get("gridSpan", "1")), int(tc.get("rowSpan", "1"))
                cw_ = sum(grid[ci:ci + gs])
                ch_ = sum(int(rows[k].get("h", "0")) for k in range(ri, min(nrows, ri + rs)))
                rr = dict(x=xcur, y=y, w=cw_, h=ch_, rot=0.0, fh=False, fv=False)
                # cells live in the frame's space: apply the frame's own rotation about its centre
                Mc = mul(M, own(r)) if r["rot"] or r["fh"] or r["fv"] else M
                rec = self._base(tc, "cell", 0, "%s r%dc%d" % (name, ri + 1, ci + 1), c, group_path, parent_gid,
                                 rr, Mc)
                rec["id"] = None           # assigned after the walk, above the slide's largest shape id
                rec["descr"] = rec["title"] = ""
                rec["geom"] = {"prst": "rect", "adj": {}, "cust": False, "paths": 0, "radius_in": None,
                               "point_in": None}
                parts = style_parts(flags, ri, ci, nrows, ncols)
                tcPr = tc.find(A("tcPr"))
                fill_el = first_child(tcPr, ("noFill", "solidFill", "gradFill", "blipFill", "pattFill")) \
                    if tcPr is not None else None
                fill_via = "none"
                if fill_el is not None and self.cctx is not None:
                    rec["fill"] = fill_from(fill_el, self.cctx, "tcPr")
                    fill_via = "tcPr"
                else:
                    sf = style.fill(parts, self.cctx) if style is not None and self.cctx is not None else None
                    rec["fill"] = sf or {"type": "none", "via": "default"}
                    fill_via = "tableStyle" if sf else "none"
                rec["grad"] = rec["fill"].pop("grad", None)
                line = {"type": "none", "via": "default"}
                if tcPr is not None and self.cctx is not None:
                    for side in ("lnT", "lnB", "lnL", "lnR"):
                        ln = tcPr.find(A(side))
                        if ln is not None and first_child(ln, ("solidFill", "gradFill")) is not None:
                            wrap = etree.Element(A("spPr"))
                            wrap.append(etree.fromstring(etree.tostring(ln).replace(
                                ("a:" + side).encode(), b"a:ln")))
                            line = resolve_line(wrap, None, self.cctx)
                            line["via"] = "tcPr:" + side
                            break
                rec["line"] = line
                rec["effects"] = None
                extra = style.text_rpr(parts) if style is not None else None
                txb = tc.find(A("txBody"))
                if txb is not None and self.cctx is not None:
                    tctx, body = self.text_ctx(tc, None, None, None, extra_rpr=extra)
                    ins = [tcPr.get(k) if tcPr is not None else None for k in ("marL", "marT", "marR", "marB")]
                    dflt = [91440, 45720, 91440, 45720]
                    body["insets_in"] = [round(int(v if v is not None else d) / EMU_IN, 4) for v, d in zip(ins, dflt)]
                    body["anchor"] = tcPr.get("anchor", "t") if tcPr is not None else "t"
                    rec["text"] = read_text(txb, tctx, body)
                rec["cell"] = {"table_id": sid, "row": ri + 1, "col": ci + 1, "span": [rs, gs],
                               "style_id": style_id, "fill_via": fill_via}
                self.leaves.append(rec)
                xcur += w
            y += h


# ------------------------------------------------------------------ table styles

class TableStyle:
    def __init__(self, el):
        self.el = el

    def _part(self, name):
        return self.el.find(A(name)) if self.el is not None else None

    def fill(self, parts, cctx):
        for pn in parts:
            p = self._part(pn)
            tcs = p.find(A("tcStyle")) if p is not None else None
            if tcs is None:
                continue
            f = tcs.find(A("fill"))
            if f is not None:
                fe = first_child(f, ("noFill", "solidFill", "gradFill", "pattFill"))
                if fe is not None:
                    return fill_from(fe, cctx, "tableStyle:" + pn)
            fr = tcs.find(A("fillRef"))
            if fr is not None:
                from .colour import fill_ref
                return fill_ref(fr, cctx)
        return None

    def text_rpr(self, parts):
        rpr = etree.Element(A("rPr"))
        got = False
        for pn in reversed(parts):     # least specific first, most specific overwrites
            p = self._part(pn)
            ts = p.find(A("tcTxStyle")) if p is not None else None
            if ts is None:
                continue
            for k in ("b", "i"):
                if ts.get(k) in ("on", "off"):
                    rpr.set(k, "1" if ts.get(k) == "on" else "0")
                    got = True
            col = first_colour(ts)
            if col is None:
                fr = ts.find(A("fontRef"))
                col = first_colour(fr) if fr is not None else None
            if col is not None:
                for old in rpr.findall(A("solidFill")):
                    rpr.remove(old)
                sf = etree.SubElement(rpr, A("solidFill"))
                sf.append(etree.fromstring(etree.tostring(col)))
                got = True
        return rpr if got else None


def table_style(deck: DeckRead, style_id: str | None):
    if not style_id:
        return None
    cache = deck.cache.setdefault("table_styles", None)
    if cache is None:
        cache = {}
        part = deck.rel_target(deck.pres_part, "/tableStyles")
        if part and deck.has(part):
            for s in deck.xml(part).findall(A("tblStyle")):
                cache[s.get("styleId")] = s
        deck.cache["table_styles"] = cache
    el = cache.get(style_id)
    return TableStyle(el) if el is not None else None


def style_parts(flags, ri, ci, nrows, ncols) -> list[str]:
    parts = []
    if flags["firstRow"] and ri == 0:
        parts.append("firstRow")
    if flags["lastRow"] and ri == nrows - 1:
        parts.append("lastRow")
    if flags["firstCol"] and ci == 0:
        parts.append("firstCol")
    if flags["lastCol"] and ci == ncols - 1:
        parts.append("lastCol")
    if flags["bandRow"]:
        k = ri - (1 if flags["firstRow"] else 0)
        if k >= 0:
            parts.append("band1H" if k % 2 == 0 else "band2H")
    if flags["bandCol"]:
        k = ci - (1 if flags["firstCol"] else 0)
        if k >= 0:
            parts.append("band1V" if k % 2 == 0 else "band2V")
    parts.append("wholeTbl")
    return parts


# ------------------------------------------------------------------ post-walk passes

def _icon_size(w, h) -> bool:
    lo, hi = min(w, h), max(w, h)
    return ICON_MIN_IN <= hi <= ICON_MAX_IN and lo > 0 and hi / lo <= ICON_ASPECT


def _has_text(L) -> bool:
    return bool(L.get("text") and L["text"]["text"].strip())


def _vector_glyph(L) -> bool:
    """A lone text-free custGeom sp inside the icon size and aspect range (library DECISIONS, refined).
    A preset shape (ellipse, rect, roundRect, ...) never qualifies: discs, dots and chips are components."""
    return (L["kind"] == "sp" and bool((L.get("geom") or {}).get("cust")) and not L.get("line_like")
            and not _has_text(L) and _icon_size(L["frame"]["w_in"], L["frame"]["h_in"]))


def mark_icons(leaves: list[dict], groups: list[dict]) -> list[dict]:
    """Icon definition (library DECISIONS): a picture or vector group with no text, long side 0.12-0.8 in,
    aspect 0.4-2.5; an icon-sized group counts once (outermost wins). Refined: a lone text-free custGeom
    shape in that range is a vector glyph and counts once; "lone" means not already inside an icon-sized
    group. A lone preset shape never counts. Returns the icon units (kind group | pic | vector)."""
    by_gid = {g["id"]: g for g in groups}
    units = []
    icon_groups = set()
    for g in groups:
        if g.get("bbox") is None or "_leaf_range" not in g:
            g["icon_like"] = False
            continue
        a, b = g["_leaf_range"]
        members = leaves[a:b]
        ok = (bool(members) and not any(_has_text(L) for L in members)
              and not any(L["kind"] in ("cell", "graphic", "cxn") for L in members)
              and _icon_size(g["bbox"]["w_in"], g["bbox"]["h_in"]))
        g["icon_like"] = ok
    for g in groups:
        if not g.get("icon_like"):
            continue
        if any(by_gid.get(p, {}).get("icon_like") for p in _ancestors(g, by_gid)):
            continue
        icon_groups.add(g["id"])
        units.append({"kind": "group", "id": g["id"], "bbox": g["bbox"]})
    for L in leaves:
        in_icon = next((gid for gid in L["group_path"] if gid in icon_groups), None)
        if in_icon is not None:
            L["icon_group"] = in_icon
            continue
        if L["kind"] == "pic" and not _has_text(L) and _icon_size(L["frame"]["w_in"], L["frame"]["h_in"]):
            L["icon_like"] = True
            units.append({"kind": "pic", "id": L["id"], "bbox": L["bbox"]})
        elif _vector_glyph(L):
            L["icon_like"] = True
            units.append({"kind": "vector", "id": L["id"], "bbox": L["bbox"]})
    return units


def _ancestors(g, by_gid):
    out = []
    p = g.get("parent")
    while p:
        out.append(p)
        p = by_gid.get(p, {}).get("parent")
    return out


def mark_containers(leaves: list[dict]):
    for L in leaves:
        if not is_rect_like(L):
            continue
        L["container_of"] = [M["id"] for M in leaves if M is not L and M["z"] > L["z"] and contains(L, M)]


OPEN_QUOTES = ('"', chr(0x201C), chr(0x2018))   # chr() keeps the glyphs out of the source
NUMERAL = re.compile(r"^[~<>+\-]?[$€£]?\d[\d.,]*\s?(?:%|x|×|[KkMmBb]n?|pp|pts?|bps|\+)?$")


TITLE_TOP = 0.22          # a top-band title's box top lies in this share of the canvas height
TITLE_RATIO = 1.3         # ... and it is set at least this many times the slide's median body size
TITLE_FEW_WORDS = 12      # dividers, covers, closers: the largest text anywhere is the title
TITLE_DOMINANT = 1.2      # a text this many times larger than every other candidate dominates the slide
_LETTER = re.compile(r"[^\W\d_]")
TITLE_WHY = {"placeholder": (0.95, "title placeholder"),
             "top-band": (0.8, "top band, at least 1.3x the median body size"),
             "few-words": (0.7, "12 content words or fewer, largest text"),
             "dominant": (0.65, "largest text, 1.2x every other and 1.3x their median"),
             "top-largest": (0.6, "top band, largest text on the slide")}


def _title_candidate(L) -> bool:
    """A horizontal, on-canvas text leaf with a letter in it; not a cell, numeral, footer, date or page number."""
    if L["kind"] == "cell" or L.get("on_canvas") == "off" or not _has_text(L) or not L["text"].get("size"):
        return False
    if (L.get("placeholder") or {}).get("type") in ("sldNum", "ftr", "dt"):
        return False
    t = L["text"]["text"].strip()
    if not _LETTER.search(t) or NUMERAL.match(t):
        return False
    if any(c.isdigit() for c in t) and len(_LETTER.findall(t)) <= 3:
        return False                 # a figure ("5 to 10%", "Q3 2026"), not a heading
    return ((L["text"].get("body") or {}).get("vert") or "horz") == "horz"


def pick_title(leaves: list[dict], cw: float, ch: float, words_content: int | None = None):
    """The slide's title leaf and the tier that found it, else (None, None). Tiers, first hit wins:
    placeholder  the title or ctrTitle placeholder, when present and non-empty;
    top-band     the largest-size text leaf whose box top lies in the top 22% of the canvas and whose size is at
                 least 1.3x the slide's median body size (median of the text leaves' dominant sizes);
    few-words    on a slide of 12 or fewer content words (dividers, covers, closers), the largest text anywhere;
    dominant     the largest text anywhere when it is 1.2x every other candidate and 1.3x their median (a cover
                 or divider title set mid-canvas among a date, a kicker and a subtitle);
    top-largest  the largest top-band text when no text on the slide is larger.
    Candidates exclude cells, numerals and figures (a digit with three letters or fewer), page numbers, footers,
    dates, vertical text and text with no letter.
    Largest means dominant size, then nearest the top, then more words."""
    texts = [L for L in leaves if _has_text(L) and L["text"].get("size")]
    ph = next((L for L in texts if (L.get("placeholder") or {}).get("type") in TITLE_TYPES), None)
    if ph is not None:
        return ph, "placeholder"
    if not texts:
        return None, None
    size = lambda L: L["text"]["size"]["dominant_pt"]   # noqa: E731
    key = lambda L: (size(L), -L["bbox"]["y_in"], L["text"]["words"])   # noqa: E731
    med = statistics.median(size(L) for L in texts)
    cands = sorted((L for L in texts if _title_candidate(L)), key=key, reverse=True)
    if not cands:
        return None, None
    top = [L for L in cands if L["bbox"]["y_in"] < TITLE_TOP * ch]
    hit = next((L for L in top if size(L) >= TITLE_RATIO * med), None)
    if hit is not None:
        return hit, "top-band"
    if words_content is None:
        words_content = sum(int(L["text"].get("words") or 0) for L in texts)
    if words_content <= TITLE_FEW_WORDS:
        return cands[0], "few-words"
    first, rest = cands[0], [size(L) for L in cands[1:]]
    if not rest or (size(first) >= TITLE_DOMINANT * rest[0] and size(first) >= TITLE_RATIO * statistics.median(rest)):
        return first, "dominant"
    if top and size(top[0]) >= max(size(L) for L in texts):
        return top[0], "top-largest"
    return None, None


def guess_roles(leaves: list[dict], cw: float, ch: float, find_title: bool = True,
                words_content: int | None = None):
    """Role guesses for every leaf. find_title=False (chrome) never names a title."""
    area = cw * ch
    texts = [L for L in leaves if _has_text(L) and L["text"].get("size")]
    sizes = [L["text"]["size"]["dominant_pt"] for L in texts]
    med = statistics.median(sizes) if sizes else 12.0
    title, tier = pick_title(leaves, cw, ch, words_content) if find_title else (None, None)
    for L in leaves:
        L["role_guess"] = _role(L, title, med, cw, ch, area, tier)


def _role(L, title, med, cw, ch, area, tier=None) -> dict:
    ph = (L.get("placeholder") or {}).get("type")
    b = L["bbox"]
    if L is title:
        conf, why = TITLE_WHY.get(tier or "placeholder", TITLE_WHY["placeholder"])
        return {"role": "title", "conf": conf, "why": why}
    if ph == "subTitle":
        return {"role": "subtitle", "conf": 0.9, "why": "subtitle placeholder"}
    if ph == "sldNum":
        return {"role": "page-number", "conf": 0.9, "why": "slide number placeholder"}
    if ph in ("ftr", "dt"):
        return {"role": "footer", "conf": 0.9, "why": "footer placeholder"}
    if _has_text(L) and L["text"].get("size"):
        t = L["text"]["text"].strip()
        sz = L["text"]["size"]["dominant_pt"]
        w = L["text"]["words"]
        if re.fullmatch(r"\d{1,3}", t) and sz <= 12 and (b["y_in"] > 0.9 * ch or b["y_in"] + b["h_in"] < 0.1 * ch) \
                and (b["x_in"] > 0.85 * cw or b["x_in"] + b["w_in"] < 0.15 * cw):
            return {"role": "page-number", "conf": 0.7, "why": "short number in a corner"}
        if b["y_in"] > 0.92 * ch and sz <= 10:
            return {"role": "footer", "conf": 0.6, "why": "small text in the bottom band"}
        if NUMERAL.match(t) and sz >= 1.4 * med:
            return {"role": "numeral", "conf": 0.7, "why": "figure set large"}
        if title is not None and L["layer"] == "content":
            tb = title["bbox"]
            if 0 <= b["y_in"] - (tb["y_in"] + tb["h_in"]) <= 0.6 and sz < title["text"]["size"]["dominant_pt"] \
                    and w >= 4 and b["w_in"] >= 0.4 * tb["w_in"]:
                return {"role": "subtitle", "conf": 0.6, "why": "directly under the title, smaller"}
        if t[:1] in OPEN_QUOTES:
            return {"role": "quote", "conf": 0.6, "why": "opens with a quotation mark"}
        if L["kind"] == "cell":
            return {"role": "cell", "conf": 0.9, "why": "table cell"}
        if L["text"]["bold_share"] >= 0.6 and w <= 8 and len(L["text"]["paragraphs"]) <= 2:
            return {"role": "card-heading", "conf": 0.55, "why": "short bold text"}
        if w <= 4:
            return {"role": "label", "conf": 0.5, "why": "four words or fewer"}
        return {"role": "body", "conf": 0.5, "why": "multi-word text"}
    if b["w_in"] * b["h_in"] >= 0.9 * area:
        return {"role": "background", "conf": 0.8, "why": "full bleed"}
    if L["kind"] == "pic":
        k = (L.get("picture") or {}).get("kind_guess", "picture")
        return {"role": k if k in ("icon", "logo") else "picture", "conf": 0.6, "why": "picture: " + str(k)}
    if L["kind"] == "cxn":
        return {"role": "connector", "conf": 0.95, "why": "connector shape"}
    if L.get("line_like"):
        return {"role": "arrow" if (L.get("geom") or {}).get("prst") in cx.BLOCK_ARROWS else "line", "conf": 0.8,
                "why": "line-like preset"}
    if L["kind"] == "graphic":
        return {"role": "graphic", "conf": 0.9, "why": (L.get("graphic") or {}).get("kind", "")}
    if L["kind"] == "cell":
        return {"role": "cell", "conf": 0.9, "why": "table cell"}
    if len(L.get("container_of") or []) >= 3:
        return {"role": "container", "conf": 0.7, "why": "contains %d shapes" % len(L["container_of"])}
    if L.get("icon_group"):
        return {"role": "icon-part", "conf": 0.7, "why": "inside an icon-sized group"}
    if L.get("icon_like"):
        return {"role": "icon", "conf": 0.6, "why": "vector glyph: text-free custGeom, icon-sized"}
    return {"role": "shape", "conf": 0.4, "why": "untexted shape"}


def _sig(L) -> str:
    b = L["bbox"]
    key = "%s|%s|%d|%d|%d|%d" % (L["kind"], (L.get("geom") or {}).get("prst"), round(b["x_pct"]),
                                 round(b["y_pct"]), round(b["w_pct"]), round(b["h_pct"]))
    return hashlib.sha1(key.encode()).hexdigest()


def finish_text(L, cw):
    tx = L.get("text")
    if not tx:
        return
    s = tx.get("size")
    if s:
        s["dominant_norm_pt"] = round(s["dominant_pt"] * 13.333 / cw, 2)
    # lines and occupancy, estimated with an average glyph width of 0.5 em
    body = tx["body"]
    ins = body["insets_in"]
    inner_w = max(0.01, L["frame"]["w_in"] - ins[0] - ins[2])
    inner_h = max(0.01, L["frame"]["h_in"] - ins[1] - ins[3])
    lines = 0
    height = 0.0
    for p in tx["paragraphs"]:
        nonblank = [r for r in p["runs"] if r["t"]]
        sz = max((r["size_rendered_pt"] for r in nonblank), default=(s["dominant_pt"] if s else 12.0))
        chars = len(p["text"])
        if body.get("wrap") == "none":
            n = max(1, p["text"].count("\n") + 1)
        else:
            per_line = max(1.0, inner_w / (0.5 * sz / 72.0))
            n = sum(max(1, math.ceil(len(seg) / per_line)) for seg in p["text"].split("\n")) if chars else 1
        lines += n
        height += n * sz * 1.2 * (p.get("ln_spc_pct", 100.0) / 100.0) / 72.0 + \
            (p.get("spc_bef_pt", 0) + p.get("spc_aft_pt", 0)) / 72.0
    tx["lines_est"] = lines
    tx["occupancy"] = round(height / inner_h, 3) if tx["words"] else None


# ------------------------------------------------------------------ hygiene

OVERLAP_SHARE = 0.20       # two text boxes overlapping by this share of the smaller one
OFF_CANVAS_IN = 0.05       # a leaf reaching this far past the canvas edge
SOFT_BLUR_PT = 0.75        # a shadow blurred more than this (the soft-shadow tell)


def _text_box(L):
    """Where a text leaf's glyphs sit, as (x0, y0, x1, y1), drawn box or not. Height: the lines it fills
    (finish_text's occupancy plus 5%, placed by anchor). Width: when every line is estimated to fit unwrapped,
    the longest line at 0.5 em a character (finish_text's estimate), placed by the paragraph's alignment.
    Cells, rotated and vertical text keep the whole frame."""
    b = L["bbox"]
    box = (b["x_in"], b["y_in"], b["x_in"] + b["w_in"], b["y_in"] + b["h_in"])
    tx = L["text"]
    body = tx.get("body") or {}
    fr = L.get("frame") or {}
    if (body.get("vert") or "horz") != "horz" or (fr.get("rot_deg") or 0) % 180 or L["kind"] == "cell":
        return box
    ins = body.get("insets_in") or [0.1, 0.05, 0.1, 0.05]
    inner_w = b["w_in"] - ins[0] - ins[2]
    inner_h = b["h_in"] - ins[1] - ins[3]
    occ = tx.get("occupancy")
    y0, y1 = box[1], box[3]
    if occ and occ < 1 and inner_h > 0:
        th = min(inner_h, occ * inner_h * 1.05)
        anchor = body.get("anchor") or "t"
        top = y1 - ins[3] - th if anchor == "b" else y0 + ins[1] + ((inner_h - th) / 2 if anchor == "ctr" else 0.0)
        y0, y1 = max(y0, top), min(y1, top + th)
    widest = None
    for p in tx.get("paragraphs") or []:
        sz = max((r["size_rendered_pt"] for r in p["runs"] if r["t"].strip()), default=None)
        if sz is None:
            continue
        w = max(len(seg) for seg in p["text"].split("\n")) * 0.5 * sz / 72.0
        if w > inner_w:
            widest = None
            break                            # this paragraph wraps: keep the frame width
        if widest is None or w > widest[0]:
            widest = (w, p.get("algn") or "l")
    x0, x1 = box[0], box[2]
    if widest is not None:
        w, al = widest
        left = b["x_in"] + ins[0] + ((inner_w - w) / 2 if al == "ctr" else (inner_w - w) if al == "r" else 0.0)
        x0, x1 = max(x0, left), min(x1, left + w)
    return (x0, y0, x1, y1) if x1 > x0 and y1 > y0 else box


def _drawn(L) -> bool:
    f = (L.get("fill") or {}).get("type") or "none"
    ln = (L.get("line") or {}).get("type") or "none"
    return f not in ("none", "grp") or ln != "none" or bool(L.get("grad"))


def layout_hygiene(leaves: list[dict], cw: float, ch: float, add) -> None:
    """overlap, partial-off-canvas, degenerate-connector, soft-shadow, gradient, render-divergence-risk."""
    eps = 0.02
    texts = []
    for L in leaves:
        sid = L["id"]
        b = L["bbox"]
        if L.get("on_canvas") == "partial":
            over = max(-b["x_in"], -b["y_in"], b["x_in"] + b["w_in"] - cw, b["y_in"] + b["h_in"] - ch)
            if over >= OFF_CANVAS_IN:
                add("partial-off-canvas", sid, "%d: %.2f in past the edge" % (sid, over))
        k = L.get("connector")
        if k and k.get("class") == "degenerate":
            add("degenerate-connector", sid, "%d: %.3f in long" % (sid, k.get("length_in") or 0.0))
        ef = L.get("effects") or {}
        sh = ef.get("shadow")
        if sh and (sh.get("blur_pt") or 0) > SOFT_BLUR_PT and (sh.get("alpha") is None or sh["alpha"] > 0) \
                and (_drawn(L) or _has_text(L) or L["kind"] == "pic"):
            add("soft-shadow", sid, "%d: blur %.1f pt" % (sid, sh["blur_pt"]))
        if L.get("grad"):
            add("gradient", sid, "%d: %s" % (sid, (L["grad"] or {}).get("kind") or "gradient"))
        if not _has_text(L):
            continue
        body = L["text"].get("body") or {}
        vert = body.get("vert") or "horz"
        fr = L.get("frame") or {}
        x = L.get("xfrm") or {}
        turned = round(fr.get("rot_deg") or 0.0, 1) % 360 != 0 or fr.get("mirrored") or x.get("flipH") or x.get("flipV")
        if vert != "horz":
            add("render-divergence-risk", sid, "%d: vertical text (%s)" % (sid, vert))
        elif turned and body.get("autofit") == "shape":
            add("render-divergence-risk", sid, "%d: rotated or flipped text with spAutoFit" % sid)
        if L.get("on_canvas") != "off":
            texts.append((L, _text_box(L)))
    # overlap: two text leaves whose boxes overlap by 20%+ of the smaller, neither inside the other's container
    texts.sort(key=lambda t: t[1][0])
    for i, (A_, a) in enumerate(texts):
        for B_, b in texts[i + 1:]:
            if b[0] >= a[2]:
                break
            ix = min(a[2], b[2]) - max(a[0], b[0])
            iy = min(a[3], b[3]) - max(a[1], b[1])
            if ix <= 0 or iy <= 0:
                continue
            small = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
            if small <= 0 or ix * iy < OVERLAP_SHARE * small:
                continue
            ca, cb = A_.get("cell") or {}, B_.get("cell") or {}
            if ca and cb and ca.get("table_id") == cb.get("table_id"):
                continue
            if B_["id"] in (A_.get("container_of") or []) or A_["id"] in (B_.get("container_of") or []):
                continue
            ba, bb = _bbox_tuple(A_), _bbox_tuple(B_)
            if (_drawn(A_) and _inside(bb, ba, eps)) or (_drawn(B_) and _inside(ba, bb, eps)):
                continue                       # a label on a drawn card is inside that card, not over it
            add("overlap", A_["id"], "%d+%d: %d%%" % (A_["id"], B_["id"], round(100 * ix * iy / small)))
            add("overlap", B_["id"])


def _bbox_tuple(L):
    b = L["bbox"]
    return (b["x_in"], b["y_in"], b["x_in"] + b["w_in"], b["y_in"] + b["h_in"])


def _inside(inner, outer, eps) -> bool:
    return (inner[0] >= outer[0] - eps and inner[1] >= outer[1] - eps and inner[2] <= outer[2] + eps
            and inner[3] <= outer[3] + eps)


def hygiene(leaves: list[dict], chrome: list[dict], dominant_face: str | None,
            canvas: tuple[float, float] | None = None) -> list[dict]:
    """Scripted hygiene flags on content leaves. With canvas (w_in, h_in), also the layout kinds of
    layout_hygiene (connector classes must already be set)."""
    fp = fingerprint_rules()
    flags: dict[str, dict] = {}

    def add(kind, sid, detail=""):
        f = flags.setdefault(kind, {"kind": kind, "ids": [], "detail": []})
        if sid not in f["ids"]:
            f["ids"].append(sid)
        if detail and detail not in f["detail"] and len(f["detail"]) < 12:
            f["detail"].append(detail)

    counters: dict[str, list] = {}
    mixed: dict[str, int] = {}
    for L in leaves:
        sid = L["id"]
        if L.get("on_canvas") == "off":
            add("off-canvas", sid)
        pic = L.get("picture")
        if pic:
            if pic.get("dpi_effective") is not None and pic["dpi_effective"] < 100:
                add("low-res", sid, "%s dpi" % pic["dpi_effective"])
            if pic.get("ai_hint"):
                add("ai-image", sid, pic["ai_hint"])
        if not _has_text(L):
            continue
        t = L["text"]["text"]
        ts = t.strip()
        if fp["placeholder"] is not None:
            m = fp["placeholder"].search(t)
            if m:
                add("placeholder-text", sid, m.group(0))
        if re.search(r"(?i)click to add", t):
            add("placeholder-text", sid, "Click to add")
        if STICKY.match(ts):
            add("review-sticky", sid, ts)
        if len(ts) == 1 and not ts.isdigit() and not (ts.isalpha() and ts.isupper()
                                                       and max(L["frame"]["w_in"], L["frame"]["h_in"]) <= 0.6):
            add("stray-char", sid, ts)
        if fp["al"] is not None and fp["al"].search(t):
            add("typo", sid, "Al typed for AI")
        if re.fullmatch(r"0?\d{1,2}", ts):
            counters.setdefault(ts.lstrip("0") or "0", []).append(sid)
        for rid, rx in fp["glyph"]:
            m = rx.search(t)
            if m:
                add("glyph", sid, rid)
        if fp["person"] is not None:
            m = fp["person"].search(t)
            if m:
                add("first-person", sid, m.group(0))
        if EMOJI.search(t):
            add("emoji", sid, EMOJI.search(t).group(0))
        for p in L["text"]["paragraphs"]:
            for r in p["runs"]:
                if not r["t"].strip():
                    continue
                if r["size_rendered_pt"] < FLOOR_PT:
                    add("sub-8pt", sid)
                f = r["font"]
                if dominant_face and f and f != dominant_face and not SYMBOL_FACES.search(f):
                    mixed[f] = mixed.get(f, 0) + len(r["t"].strip())
                    add("mixed-font", sid)
    # a repeated step number is a defect only when the sequence also has a gap (1, 2, 2, 4), not when
    # two parallel sequences share numbers (1, 1, 2, 2, 3, 3)
    if len(counters) >= 2:
        vals = sorted(int(v) for v in counters)
        if max(vals) > len(vals) and min(vals) <= 1:
            for v, ids in counters.items():
                if len(ids) >= 2:
                    for sid in ids:
                        add("dup-counter", sid, v)
    if canvas is not None:
        layout_hygiene(leaves, canvas[0], canvas[1], add)
    if "mixed-font" in flags:
        flags["mixed-font"]["detail"] = ["%s: %d chars vs %s" % (f, n, dominant_face)
                                         for f, n in sorted(mixed.items(), key=lambda kv: -kv[1])][:6]
    if fp["source"] is None:
        flags["fingerprints-missing"] = {"kind": "other", "ids": [], "detail": ["fingerprints.json not found"]}
    out = []
    for f in flags.values():
        f["n"] = len(f["ids"])
        f["detail"] = "; ".join(f["detail"])
        out.append(f)
    return out


# ------------------------------------------------------------------ public

def _strip_private(L):
    for k in ("_geo", "_r", "_M"):
        L.pop(k, None)


def chrome_leaves(deck: DeckRead, layout_part: str | None, show_master_shapes: bool, light: bool = False,
                  cctx_from: Walker | None = None) -> list[dict]:
    """Rendered master and layout non-placeholder leaves for a slide, master before layout.
    cctx_from is the slide's Walker, so chrome resolves colours through the slide's effective clrMap."""
    if not show_master_shapes or not layout_part or cctx_from is None:
        return []
    w = cctx_from
    li = w.li
    w.layer = "chrome"
    n0 = len(w.leaves)
    g0 = len(w.groups)
    if li.show_master_sp and w.mi is not None:
        tree = w.mi.root.find(P("cSld") + "/" + P("spTree"))
        if tree is not None:
            w.walk(tree, w.mi.part, ph_ok=False)
    tree = li.root.find(P("cSld") + "/" + P("spTree"))
    if tree is not None:
        w.walk(tree, li.part, ph_ok=False)
    out = w.leaves[n0:]
    del w.leaves[n0:]
    w.chrome_groups = w.groups[g0:]
    del w.groups[g0:]
    w.layer = "content"
    return out


def read_slide(deck: DeckRead, index1: int, *, dominant_face: str | None = None, light: bool = False) -> dict:
    """One slide to the shapes@1 dict, minus render. light=True skips pictures' pixel facts, touch, roles
    and hygiene (used for deck-wide font passes)."""
    part = deck.slide_part(index1)
    w = Walker(deck, part, light=light)
    root = w.root
    csld = root.find(P("cSld"))
    show_master = root.get("showMasterSp") not in ("0", "false")
    chrome = chrome_leaves(deck, w.layout_part, show_master, light, w) if w.li else []
    tree = csld.find(P("spTree")) if csld is not None else None
    if tree is not None:
        w.walk(tree, part)
    leaves = w.leaves
    # ids for table cells, above the slide's largest shape id
    nid = w.max_id
    for L in leaves + chrome:
        if L["id"] is None:
            nid += 1
            L["id"] = nid
    for z, L in enumerate(leaves):
        L["z"] = z
    for i, L in enumerate(chrome):
        L["z"] = i - len(chrome)
    hidden = root.get("show") in ("0", "false")
    # background: slide, then layout, then master
    bg = None
    for src, el in (("slide", root), ("layout", w.li.root if w.li else None), ("master", w.mi.root if w.mi else None)):
        if el is None or w.cctx is None:
            continue
        b = el.find(P("cSld") + "/" + P("bg"))
        f = resolve_background(b, w.cctx)
        if f is not None:
            via = f.pop("via", None)
            bg = {"fill": f, "from": src, "via": via}
            break
    if bg is None:
        bg = {"fill": {"type": "none"}, "from": "default", "via": None}
    for L in leaves + chrome:
        finish_text(L, w.cw)
        L["sig"] = _sig(L)
    out_text = _text_summary(leaves, chrome)
    groups = w.groups
    if not light:
        units = mark_icons(leaves, groups)
        mark_containers(leaves)
        area = w.cw * w.ch
        legend = cx.legend_lines(leaves, area)
        for L in leaves:
            if L.get("connector") is not None:
                c = L["connector"]
                s, e = tuple(c["start_in"]), tuple(c["end_in"])
                c["touch"] = {"start": cx.touch(s, leaves, L["id"], area),
                              "end": cx.touch(e, leaves, L["id"], area)}
                c["contact"] = cx.contact(s, e, leaves, L["id"], area,
                                          straight=c["orientation"] in ("h", "v", "diag"))
                c["class"] = cx.classify(L, legend)
        guess_roles(leaves, w.cw, w.ch, words_content=out_text["words_content"])
        guess_roles(chrome, w.cw, w.ch, find_title=False)
        if dominant_face is None:
            from .deckinfo import dominant_face as _dom
            dominant_face = _dom(deck)
        hyg = hygiene(leaves, chrome, dominant_face, canvas=(w.cw, w.ch))
        if w.hidden_ids:
            hyg.append({"kind": "hidden-shape", "ids": list(w.hidden_ids), "detail": "", "n": len(w.hidden_ids)})
    else:
        units, hyg = [], []
    fid = {"font_substitutions": [], "recolour_effects": {"duotone": 0, "biLevel": 0, "lum": 0, "clrChange": 0},
           "artistic_layers": 0, "svg_blips": 0, "autofit_shrunk": 0}
    for L in leaves:
        pic = L.get("picture")
        if pic:
            for k in pic.get("recolour", []):
                if k in fid["recolour_effects"]:
                    fid["recolour_effects"][k] += 1
            fid["artistic_layers"] += 1 if pic.get("hdphoto_part") else 0
            fid["svg_blips"] += 1 if pic.get("svg_part") else 0
        tx = L.get("text")
        if tx and tx["body"]["autofit"] == "norm" and tx["body"]["font_scale"] < 1.0:
            fid["autofit_shrunk"] += 1
    gmap = {g["id"]: g for g in groups}
    for layer, pid, cid in w.child_order:
        if layer == "content" and pid in gmap:
            gmap[pid]["children"].append(cid)
    for g in groups:
        g.pop("_leaf_range", None)
        g.pop("layer", None)
    for L in leaves + chrome:
        _strip_private(L)
    li = w.li
    status = "hidden" if hidden else _status(deck, index1)
    return {
        "schema": SCHEMA, "slide_id": None, "deck_id": None, "index": index1, "part": "/" + part,
        "canvas": {"w_in": round(w.cw, 3), "h_in": round(w.ch, 3), "kind": deck.canvas_kind},
        "hidden": hidden, "status": status,
        "layout": {"name": li.name if li else None, "part": "/" + li.part if li else None,
                   "master_part": "/" + li.master_part if li and li.master_part else None,
                   "theme_part": "/" + w.mi.theme_part if w.mi and w.mi.theme_part else None},
        "show_master_shapes": show_master,
        "background": bg,
        "shapes": leaves,
        "chrome": chrome,
        "groups": groups,
        "text": out_text,
        "icons": [{"kind": u["kind"], "id": u["id"]} for u in units],
        "fidelity": fid,
        "hygiene": hyg,
    }


def _status(deck, index1) -> str:
    from .deckinfo import status_ranges
    sr = status_ranges(deck)
    for k in ("graveyard", "appendix"):
        for a, b in sr.get(k, []):
            if a <= index1 <= b:
                return k
    return "main"


def _text_summary(leaves, chrome) -> dict:
    paras = runs = below = 0
    wc = wch = 0
    min_pt = None
    for L in leaves:
        tx = L.get("text")
        if not tx:
            continue
        wc += tx["words"]
        for p in tx["paragraphs"]:
            if p["text"].strip():
                paras += 1
            for r in p["runs"]:
                if not r["t"].strip():
                    continue
                runs += 1
                if r["size_rendered_pt"] < FLOOR_PT:
                    below += 1
                min_pt = r["size_rendered_pt"] if min_pt is None else min(min_pt, r["size_rendered_pt"])
    for L in chrome:
        tx = L.get("text")
        if tx:
            wch += tx["words"]
    return {"paragraphs": paras, "words_content": wc, "words_chrome": wch, "runs": runs,
            "runs_below_8pt": below, "min_pt": min_pt}
