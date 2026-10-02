"""Read-only OPC package access: parts, relationships, content types, slide/layout/master/theme chains.

The source file is opened with zipfile in read mode only; nothing is ever written back.
"""
from __future__ import annotations

import hashlib
import os
import posixpath
import zipfile
from functools import cached_property

from lxml import etree

from .colour import ColourCtx, parse_clrmap, parse_theme
from .ns import P, R, local

_PARSER = etree.XMLParser(huge_tree=True, resolve_entities=False, no_network=True)

TITLE_TYPES = ("title", "ctrTitle")
BODY_TYPES = ("body", "subTitle", "obj", "pic", "tbl", "chart", "clipArt", "dgm", "media")
OTHER_TYPES = ("dt", "ftr", "sldNum", "hdr")


def ph_info(sp) -> dict | None:
    """The p:ph of a shape-like element as {type, idx, has_idx}, or None."""
    nv = None
    for c in sp:
        if local(c).startswith("nv"):
            nv = c
            break
    if nv is None:
        return None
    nvpr = nv.find(P("nvPr"))
    ph = nvpr.find(P("ph")) if nvpr is not None else None
    if ph is None:
        return None
    return {"type": ph.get("type", "obj"), "idx": int(ph.get("idx", "0")), "has_idx": ph.get("idx") is not None}


def master_type(t: str) -> str:
    """Placeholder type as matched on the master: ctrTitle to title, content types to body."""
    if t in TITLE_TYPES:
        return "title"
    if t in BODY_TYPES:
        return "body"
    return t


def txstyle_key(t: str | None) -> str:
    if t in TITLE_TYPES:
        return "titleStyle"
    if t in OTHER_TYPES:
        return "otherStyle"
    return "bodyStyle"


class PhIndex:
    """Placeholders of one layout or master spTree, by idx and by type."""

    def __init__(self, root):
        self.by_idx: dict[int, object] = {}
        self.by_type: dict[str, object] = {}
        self.items: list[tuple[dict, object]] = []
        tree = root.find(P("cSld") + "/" + P("spTree")) if root is not None else None
        if tree is None:
            return
        for el in tree.iter(P("sp"), P("pic"), P("graphicFrame"), P("grpSp"), P("cxnSp")):
            info = ph_info(el)
            if info is None:
                continue
            self.items.append((info, el))
            self.by_idx.setdefault(info["idx"], el)
            self.by_type.setdefault(info["type"], el)
            self.by_type.setdefault("~" + master_type(info["type"]), el)

    def match(self, info: dict, mode: str):
        """mode 'layout': idx then type; mode 'master': type (normalised)."""
        if info is None:
            return None
        if mode == "layout":
            if info["has_idx"] and info["idx"] in self.by_idx:
                return self.by_idx[info["idx"]]
            el = self.by_type.get(info["type"])
            if el is not None:
                return el
            return self.by_type.get("~" + master_type(info["type"]))
        el = self.by_type.get(master_type(info["type"]))
        return el if el is not None else self.by_type.get("~" + master_type(info["type"]))


class MasterInfo:
    def __init__(self, deck: "DeckRead", part: str):
        self.part = part
        self.root = deck.xml(part)
        self.theme_part = deck.rel_target(part, "/theme")
        self.theme = parse_theme(deck.xml(self.theme_part) if self.theme_part else None)
        self.clrmap = parse_clrmap(self.root.find(P("clrMap")))
        self.colour = ColourCtx(self.theme["colors"], dict(self.clrmap), self.theme["fmt"], self.theme["fonts"])
        tx = self.root.find(P("txStyles"))
        self.txstyles = {}
        for k in ("titleStyle", "bodyStyle", "otherStyle"):
            self.txstyles[k] = tx.find(P(k)) if tx is not None else None
        self.ph = PhIndex(self.root)


class LayoutInfo:
    def __init__(self, deck: "DeckRead", part: str):
        self.part = part
        self.root = deck.xml(part)
        self.master_part = deck.rel_target(part, "/slideMaster")
        self.clrmap_ovr = parse_clrmap(self.root.find(P("clrMapOvr")))
        self.show_master_sp = self.root.get("showMasterSp") not in ("0", "false")
        csld = self.root.find(P("cSld"))
        self.name = csld.get("name", "") if csld is not None else ""
        self.type = self.root.get("type", "")
        self.ph = PhIndex(self.root)


class DeckRead:
    """One opened .pptx, read-only, with cached parsed parts."""

    def __init__(self, path: str):
        self.path = os.path.abspath(path)
        self.zip = zipfile.ZipFile(self.path, "r")
        self._names = set(self.zip.namelist())
        self._xml: dict[str, object] = {}
        self._rels: dict[str, dict] = {}
        self._masters: dict[str, MasterInfo] = {}
        self._layouts: dict[str, LayoutInfo] = {}
        self._bytes: dict[str, bytes] = {}
        self.cache: dict = {}            # free-form caches for other modules (picture facts, fonts)
        pres_part = self._main_part()
        self.pres_part = pres_part
        self.pres = self.xml(pres_part)
        sz = self.pres.find(P("sldSz"))
        self.cx = int(sz.get("cx")) if sz is not None else 12192000
        self.cy = int(sz.get("cy")) if sz is not None else 6858000
        rels = self.rels(pres_part)
        self.slide_parts: list[str] = []
        self.slide_ids: list[int] = []
        lst = self.pres.find(P("sldIdLst"))
        for s in (lst if lst is not None else []):
            rid = s.get(R("id"))
            if rid in rels:
                self.slide_parts.append(rels[rid][1])
                self.slide_ids.append(int(s.get("id", "0")))
        self.master_parts: list[str] = []
        mlst = self.pres.find(P("sldMasterIdLst"))
        for m in (mlst if mlst is not None else []):
            rid = m.get(R("id"))
            if rid in rels:
                self.master_parts.append(rels[rid][1])
        self.default_text_style = self.pres.find(P("defaultTextStyle"))

    # ------------------------------------------------------------ package basics
    def close(self):
        try:
            self.zip.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def _main_part(self) -> str:
        rels = self.rels("")
        for _rid, (typ, target, _mode) in rels.items():
            if typ.endswith("/officeDocument"):
                return target
        return "ppt/presentation.xml"

    def has(self, part: str) -> bool:
        return part in self._names

    def blob(self, part: str) -> bytes:
        b = self._bytes.get(part)
        if b is None:
            b = self.zip.read(part)
        return b

    def size(self, part: str) -> int:
        try:
            return self.zip.getinfo(part).file_size
        except KeyError:
            return 0

    def xml(self, part: str):
        el = self._xml.get(part)
        if el is None:
            el = etree.fromstring(self.zip.read(part), _PARSER)
            self._xml[part] = el
        return el

    def rels(self, part: str) -> dict:
        """rId to (type, absolute target part or URL, mode)."""
        r = self._rels.get(part)
        if r is not None:
            return r
        d, b = posixpath.split(part)
        rp = posixpath.join(d, "_rels", b + ".rels") if part else "_rels/.rels"
        r = {}
        if rp in self._names:
            root = etree.fromstring(self.zip.read(rp), _PARSER)
            for e in root:
                mode = e.get("TargetMode", "Internal")
                tgt = e.get("Target", "")
                if mode != "External":
                    if tgt.startswith("/"):
                        tgt = tgt[1:]
                    else:
                        tgt = posixpath.normpath(posixpath.join(d, tgt))
                r[e.get("Id")] = (e.get("Type", ""), tgt, mode)
        self._rels[part] = r
        return r

    def rel_target(self, part: str, type_suffix: str) -> str | None:
        for _rid, (typ, tgt, mode) in self.rels(part).items():
            if typ.endswith(type_suffix) and mode != "External":
                return tgt
        return None

    @cached_property
    def content_types(self) -> tuple[dict, dict]:
        root = etree.fromstring(self.zip.read("[Content_Types].xml"), _PARSER)
        defaults, overrides = {}, {}
        for e in root:
            n = local(e)
            if n == "Default":
                defaults[e.get("Extension", "").lower()] = e.get("ContentType")
            elif n == "Override":
                overrides[e.get("PartName", "").lstrip("/")] = e.get("ContentType")
        return defaults, overrides

    def content_type(self, part: str) -> str | None:
        defaults, overrides = self.content_types
        if part in overrides:
            return overrides[part]
        ext = part.rsplit(".", 1)[-1].lower() if "." in part else ""
        return defaults.get(ext)

    @cached_property
    def sha256(self) -> str:
        h = hashlib.sha256()
        with open(self.path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    # ------------------------------------------------------------ chains
    @property
    def n_slides(self) -> int:
        return len(self.slide_parts)

    @property
    def w_in(self) -> float:
        return self.cx / 914400.0

    @property
    def h_in(self) -> float:
        return self.cy / 914400.0

    @property
    def canvas_kind(self) -> str:
        w, h = self.w_in, self.h_in
        if h > w:
            return "a4p" if abs(w - 8.27) < 0.1 else "portrait"
        if abs(w - 13.333) < 0.05:
            return "w13"
        if abs(w - 10.0) < 0.05 and abs(h - 5.625) < 0.05:
            return "w10"
        if abs(w - 10.0) < 0.05 and abs(h - 7.5) < 0.05:
            return "s4x3"
        return "other"

    def slide_part(self, index1: int) -> str:
        return self.slide_parts[index1 - 1]

    def layout_part_of(self, slide_part: str) -> str | None:
        return self.rel_target(slide_part, "/slideLayout")

    def layout(self, part: str) -> LayoutInfo:
        li = self._layouts.get(part)
        if li is None:
            li = LayoutInfo(self, part)
            self._layouts[part] = li
        return li

    def master(self, part: str) -> MasterInfo:
        mi = self._masters.get(part)
        if mi is None:
            mi = MasterInfo(self, part)
            self._masters[part] = mi
        return mi

    def layouts_of_master(self, master_part: str) -> list[str]:
        root = self.xml(master_part)
        rels = self.rels(master_part)
        out = []
        lst = root.find(P("sldLayoutIdLst"))
        for e in (lst if lst is not None else []):
            rid = e.get(R("id"))
            if rid in rels:
                out.append(rels[rid][1])
        return out

    def embedded_fonts(self) -> list[str]:
        lst = self.pres.find(P("embeddedFontLst"))
        out = []
        for ef in (lst if lst is not None else []):
            f = ef.find(P("font"))
            if f is not None and f.get("typeface"):
                out.append(f.get("typeface"))
        return out


def open_deck(path: str) -> DeckRead:
    return DeckRead(path)
