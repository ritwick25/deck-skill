#!/usr/bin/env python3
"""Build kit/assets/base-wide.pptx and kit/assets/base-std.pptx from nothing.

    $PY scripts/make_base.py [--theme themes/sigmoid.json] [--check]

Each base is written part by part, never derived from python-pptx's default template (4:3, Calibri
theme, a generic thumbnail, eleven layouts with placeholders). It carries:

  * one slide master and one layout, "Blank", with no placeholders on either
  * the standard clrMap (bg1=lt1, tx1=dk1, bg2=lt2, tx2=dk2)
  * the theme's clrScheme and fontScheme, and the flat fmtScheme (sigmoid by default)
  * a white background through bg1, text styles in the theme fonts and tx1
  * no thumbnail, no embedded fonts, no TitlesOfParts, fixed docProps and zip timestamps

The output is deterministic: two runs produce byte-identical files. --check also runs
structural_check and the XSD validator on both and exits 1 on any defect.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(SKILL / "kit"))

from deckkit.canvas import STD, WIDE  # noqa: E402
from deckkit.package import app_xml, core_xml, structural_check, validate_xsd, write_members  # noqa: E402
from deckkit.theme import Theme  # noqa: E402

ASSETS = SKILL / "kit" / "assets"
DEFAULT_THEME = SKILL / "themes" / "sigmoid.json"

NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_PR = "http://schemas.openxmlformats.org/package/2006/relationships"
RT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
XMLNS = 'xmlns:a="%s" xmlns:r="%s" xmlns:p="%s"' % (NS_A, NS_R, NS_P)
CT_PML = "application/vnd.openxmlformats-officedocument.presentationml."

MASTER_ID = 2147483648
LAYOUT_ID = 2147483649


def rels(items) -> bytes:
    body = "".join('<Relationship Id="%s" Type="%s" Target="%s"/>' % i for i in items)
    return (DECL + '<Relationships xmlns="%s">%s</Relationships>' % (NS_PR, body)).encode()


def content_types() -> bytes:
    o = [("/ppt/presentation.xml", CT_PML + "presentation.main+xml"),
         ("/ppt/slideMasters/slideMaster1.xml", CT_PML + "slideMaster+xml"),
         ("/ppt/slideLayouts/slideLayout1.xml", CT_PML + "slideLayout+xml"),
         ("/ppt/theme/theme1.xml", "application/vnd.openxmlformats-officedocument.theme+xml"),
         ("/ppt/presProps.xml", CT_PML + "presProps+xml"),
         ("/ppt/viewProps.xml", CT_PML + "viewProps+xml"),
         ("/ppt/tableStyles.xml", CT_PML + "tableStyles+xml"),
         ("/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"),
         ("/docProps/app.xml", "application/vnd.openxmlformats-officedocument.extended-properties+xml")]
    body = ('<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Default Extension="png" ContentType="image/png"/>'
            '<Default Extension="svg" ContentType="image/svg+xml"/>'
            + "".join('<Override PartName="%s" ContentType="%s"/>' % x for x in o))
    return (DECL + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">%s</Types>'
            % body).encode()


def _lvl(n: int, sz: int, font: str) -> str:
    return ('<a:lvl%dpPr marL="0" indent="0" algn="l" defTabSz="914400" rtl="0" eaLnBrk="1" latinLnBrk="0" '
            'hangingPunct="1"><a:lnSpc><a:spcPct val="100000"/></a:lnSpc><a:spcBef><a:spcPts val="0"/></a:spcBef>'
            '<a:buNone/><a:defRPr sz="%d" kern="0"><a:solidFill><a:schemeClr val="tx1"/></a:solidFill>'
            '<a:latin typeface="%s"/><a:ea typeface="+mn-ea"/><a:cs typeface="+mn-cs"/></a:defRPr></a:lvl%dpPr>'
            % (n, sz, font, n))


def _levels(sz: int, font: str) -> str:
    return "".join(_lvl(n, sz, font) for n in range(1, 10))


def presentation(canvas) -> bytes:
    cx, cy = canvas.emu
    body = int(round(canvas.ramp["body"] * 100))
    return (DECL + '<p:presentation %s saveSubsetFonts="1">'
            '<p:sldMasterIdLst><p:sldMasterId id="%d" r:id="rId1"/></p:sldMasterIdLst>'
            '<p:sldSz cx="%d" cy="%d"/><p:notesSz cx="6858000" cy="9144000"/>'
            '<p:defaultTextStyle><a:defPPr><a:defRPr lang="en-US"/></a:defPPr>%s</p:defaultTextStyle>'
            '</p:presentation>' % (XMLNS, MASTER_ID, cx, cy, _levels(body, "+mn-lt"))).encode()


def _sptree() -> str:
    return ('<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/>'
            '<a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree>')


def master(canvas) -> bytes:
    title = int(round(canvas.title_pt * 100))
    body = int(round(canvas.ramp["body"] * 100))
    return (DECL + '<p:sldMaster %s><p:cSld><p:bg><p:bgPr><a:solidFill><a:schemeClr val="bg1"/></a:solidFill>'
            '<a:effectLst/></p:bgPr></p:bg>%s</p:cSld>'
            '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" '
            'accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" '
            'folHlink="folHlink"/>'
            '<p:sldLayoutIdLst><p:sldLayoutId id="%d" r:id="rId1"/></p:sldLayoutIdLst>'
            '<p:txStyles><p:titleStyle>%s</p:titleStyle><p:bodyStyle>%s</p:bodyStyle>'
            '<p:otherStyle><a:defPPr><a:defRPr lang="en-US"/></a:defPPr>%s</p:otherStyle></p:txStyles>'
            '</p:sldMaster>' % (XMLNS, _sptree(), LAYOUT_ID, _lvl(1, title, "+mj-lt").replace('kern="0"', 'b="1" kern="0"'),
                                _levels(body, "+mn-lt"), _levels(body, "+mn-lt"))).encode()


def layout() -> bytes:
    return (DECL + '<p:sldLayout %s preserve="1" userDrawn="1"><p:cSld name="Blank">%s</p:cSld>'
            '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>' % (XMLNS, _sptree())).encode()


def pres_props() -> bytes:
    return (DECL + '<p:presentationPr %s/>' % XMLNS).encode()


def view_props() -> bytes:
    return (DECL + '<p:viewPr %s><p:gridSpacing cx="76200" cy="76200"/></p:viewPr>' % XMLNS).encode()


def table_styles() -> bytes:
    return (DECL + '<a:tblStyleLst xmlns:a="%s" def="{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}"/>' % NS_A).encode()


def members(canvas, theme: Theme) -> dict:
    return {
        "[Content_Types].xml": content_types(),
        "_rels/.rels": rels([
            ("rId1", RT + "officeDocument", "ppt/presentation.xml"),
            ("rId2", "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties",
             "docProps/core.xml"),
            ("rId3", RT + "extended-properties", "docProps/app.xml")]),
        "docProps/core.xml": core_xml(""),
        "docProps/app.xml": app_xml(0),
        "ppt/presentation.xml": presentation(canvas),
        "ppt/_rels/presentation.xml.rels": rels([
            ("rId1", RT + "slideMaster", "slideMasters/slideMaster1.xml"),
            ("rId2", RT + "theme", "theme/theme1.xml"),
            ("rId3", RT + "presProps", "presProps.xml"),
            ("rId4", RT + "viewProps", "viewProps.xml"),
            ("rId5", RT + "tableStyles", "tableStyles.xml")]),
        "ppt/slideMasters/slideMaster1.xml": master(canvas),
        "ppt/slideMasters/_rels/slideMaster1.xml.rels": rels([
            ("rId1", RT + "slideLayout", "../slideLayouts/slideLayout1.xml"),
            ("rId2", RT + "theme", "../theme/theme1.xml")]),
        "ppt/slideLayouts/slideLayout1.xml": layout(),
        "ppt/slideLayouts/_rels/slideLayout1.xml.rels": rels([
            ("rId1", RT + "slideMaster", "../slideMasters/slideMaster1.xml")]),
        "ppt/theme/theme1.xml": theme.theme_xml(),
        "ppt/presProps.xml": pres_props(),
        "ppt/viewProps.xml": view_props(),
        "ppt/tableStyles.xml": table_styles(),
    }


def build(theme_path=DEFAULT_THEME, out_dir=ASSETS) -> dict:
    theme = Theme.load(theme_path)
    out = {}
    for canvas in (WIDE, STD):
        path = Path(out_dir) / ("base-%s.pptx" % canvas.name)
        out[str(path)] = write_members(members(canvas, theme), path)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", default=str(DEFAULT_THEME))
    ap.add_argument("--out", default=str(ASSETS))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    built = build(a.theme, a.out)
    rc = 0
    for path, sha in built.items():
        print("%s  %s" % (os.path.relpath(path, SKILL), sha))
        if a.check:
            defects = structural_check(path)
            ok, detail = validate_xsd(path)
            for d in defects:
                print("  [structure] %s" % d)
            print("  structure %s, xsd %s%s" % ("PASS" if not defects else "FAIL", "PASS" if ok else "FAIL",
                                               "" if ok else "\n" + detail))
            rc |= 1 if (defects or not ok) else 0
    return rc


if __name__ == "__main__":
    sys.exit(main())
