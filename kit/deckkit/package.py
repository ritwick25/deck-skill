"""Package output: a deterministic, normalised save, the XSD validator by reference, and the structural
checks that catch what makes PowerPoint offer a repair while every other reader passes the file.

save() lifts the PMR `_normalise` ideas and adds what the kit needs:
  * fixed zip timestamps and member order ([Content_Types].xml first), so a rebuild is byte-identical
  * docProps rewritten: creator and lastModifiedBy "Sigmoid", fixed dates, no TitlesOfParts, no
    HeadingPairs (app.xml would otherwise list every slide title), no thumbnail part
  * every theme part carries the Theme's clrScheme, fontScheme and flat fmtScheme
  * the svg Default content type is present (python-pptx drops it, orphaning every icon)
  * embedded workbooks flattened (each chart's xlsx carries its own timestamps)
  * a reopen round-trip before anything touches disk, then an atomic os.replace
  * refusal (HandEditDrift) when a ~$ lock exists beside the target, or when the target on disk no
    longer matches the sha its last manifest recorded, unless overwrite=True

The XSD validator is referenced in place, never copied (its skill is all rights reserved). If it cannot
be found or cannot run, validate_xsd raises ValidatorMissing: a missing validator is a failure.
"""
from __future__ import annotations

import collections
import glob
import hashlib
import io
import json
import os
import posixpath
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from lxml import etree

from .errors import HandEditDrift, UnsupportedPart, ValidatorMissing
from .ooxml import once_only_violations
from .read.ns import NS
from .theme import Theme, theme_parts

FIXED_TIME = (1980, 1, 1, 0, 0, 0)
FIXED_DATE = "1980-01-01T00:00:00Z"
AUTHOR = "Sigmoid"
VALIDATOR_GLOB = os.path.expanduser("~/.claude/skills/synced/*/pptx/scripts/office/validate.py")

CT_NS = NS["ct"]
PR_NS = NS["pr"]
R_NS = NS["r"]
_P = "{%s}" % NS["p"]
_A = "{%s}" % NS["a"]
RT_THUMB = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"
SVG_CT = "image/svg+xml"

CORE_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
    'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
    '<dc:title>{title}</dc:title><dc:creator>{author}</dc:creator>'
    '<cp:lastModifiedBy>{author}</cp:lastModifiedBy><cp:revision>1</cp:revision>'
    '<dcterms:created xsi:type="dcterms:W3CDTF">{date}</dcterms:created>'
    '<dcterms:modified xsi:type="dcterms:W3CDTF">{date}</dcterms:modified>'
    '</cp:coreProperties>')

APP_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
    'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
    '<TotalTime>0</TotalTime><Application>Microsoft Office PowerPoint</Application>'
    '<PresentationFormat>Custom</PresentationFormat><Slides>{slides}</Slides>'
    '<Company>{author}</Company><AppVersion>16.0000</AppVersion></Properties>')


def _esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def core_xml(title: str) -> bytes:
    return CORE_XML.format(title=_esc(title), author=AUTHOR, date=FIXED_DATE).encode("utf-8")


def app_xml(n_slides: int) -> bytes:
    return APP_XML.format(slides=int(n_slides), author=AUTHOR).encode("utf-8")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------ deterministic zip

def zip_bytes(members: dict) -> bytes:
    """Members as a zip with fixed metadata: [Content_Types].xml first, then sorted by name."""
    order = sorted(members, key=lambda n: (n != "[Content_Types].xml", n))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in order:
            zi = zipfile.ZipInfo(name, date_time=FIXED_TIME)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.create_system = 0
            zi.external_attr = 0o600 << 16
            z.writestr(zi, members[name])
    return buf.getvalue()


def _atomic_write(data: bytes, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def write_members(members: dict, path) -> str:
    """Write members deterministically and atomically. Returns the sha256 of the written file."""
    data = zip_bytes(members)
    _atomic_write(data, Path(path))
    return sha256_bytes(data)


def _flatten_embedded(blob: bytes) -> bytes:
    """An embedded Office package rewritten with fixed timestamps and no authorship (PMR `_flatten`)."""
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        members = {i.filename: z.read(i.filename) for i in z.infolist()}
    for name in ("docProps/core.xml", "docProps/app.xml"):
        if name in members:
            d = members[name]
            d = re.sub(rb"<dcterms:(created|modified)[^>]*>[^<]*</dcterms:\1>", b"", d)
            d = re.sub(rb"<dc:creator>[^<]*</dc:creator>", b"<dc:creator></dc:creator>", d)
            d = re.sub(rb"<cp:lastModifiedBy>[^<]*</cp:lastModifiedBy>", b"", d)
            members[name] = d
    return zip_bytes(members)


# ------------------------------------------------------------------ normalise

def _rels_name(part: str) -> str:
    d, b = posixpath.split(part)
    return posixpath.join(d, "_rels", b + ".rels")


def _source_of(rels: str) -> str:
    """'ppt/slides/_rels/slide1.xml.rels' to 'ppt/slides/slide1.xml'; '_rels/.rels' to ''."""
    d, b = posixpath.split(rels)
    return posixpath.join(posixpath.dirname(d), b[:-len(".rels")]) if b != ".rels" else ""


def _resolve(source: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(source), target))


def _ext(name: str) -> str:
    """Lower-case extension by OPC rules: '_rels/.rels' is 'rels' (splitext treats it as a stem)."""
    b = posixpath.basename(name)
    return b.rsplit(".", 1)[1].lower() if "." in b else ""


def _xml(b: bytes):
    return etree.fromstring(b, etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True))


def _ser(root) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def normalise(members: dict, *, title: str, theme: Theme) -> dict:
    """The normalised member map. Pure: same input, same output."""
    m = dict(members)
    # thumbnail part and its package relationship
    rels = _xml(m["_rels/.rels"])
    for rel in list(rels):
        if rel.get("Type") == RT_THUMB:
            m.pop(_resolve("", rel.get("Target")), None)
            rels.remove(rel)
    m["_rels/.rels"] = _ser(rels)
    # docProps
    n_slides = sum(1 for n in m if re.fullmatch(r"ppt/slides/slide\d+\.xml", n))
    m["docProps/core.xml"] = core_xml(title)
    m["docProps/app.xml"] = app_xml(n_slides)
    # theme parts
    for n in theme_parts(list(m), m.get("[Content_Types].xml")):
        m[n] = theme.retheme_part(m[n])
    # embedded workbooks
    for n in list(m):
        if n.startswith("ppt/embeddings/") and n.endswith(".xlsx"):
            m[n] = _flatten_embedded(m[n])
    # content types: svg Default, no Override pointing at a part that is gone
    ct = _xml(m["[Content_Types].xml"])
    q = "{%s}" % CT_NS
    defaults = {d.get("Extension", "").lower(): d for d in ct.findall(q + "Default")}
    if "svg" not in defaults:
        el = etree.Element(q + "Default", Extension="svg", ContentType=SVG_CT)
        first_override = ct.find(q + "Override")
        if first_override is not None:
            first_override.addprevious(el)
        else:
            ct.append(el)
    else:
        defaults["svg"].set("ContentType", SVG_CT)
    for o in ct.findall(q + "Override"):
        if o.get("PartName", "").lstrip("/") not in m:
            ct.remove(o)
    ext_used = {_ext(n) for n in m}
    for ext, d in defaults.items():
        if ext not in ext_used and ext not in ("rels", "xml", "svg"):
            ct.remove(d)
    m["[Content_Types].xml"] = _ser(ct)
    return m


# ------------------------------------------------------------------ save

def manifest_path(path) -> Path:
    p = Path(path)
    return p.with_name(p.stem + ".manifest.json")


def lock_path(path) -> Path:
    p = Path(path)
    return p.with_name("~$" + p.name)


def save(prs, path, *, title: str, theme: Theme, manifest: dict | None = None, overwrite: bool = False) -> str:
    """Save prs to path, normalised and atomic. Writes <stem>.manifest.json beside it. Returns sha256."""
    from pptx import Presentation
    path = Path(path)
    if lock_path(path).exists():
        raise HandEditDrift(str(path), need="no lock file", have=lock_path(path).name,
                            hint="the deck is open in PowerPoint; close it before rebuilding")
    if path.exists() and not overwrite:
        mp = manifest_path(path)
        have = sha256_file(path)
        try:
            prev = json.loads(mp.read_text(encoding="utf-8")).get("sha256")
        except (FileNotFoundError, ValueError):
            prev = None
        if prev != have:
            raise HandEditDrift(str(path), need=prev or "a manifest from the last build", have=have,
                                hint="the file changed since the kit wrote it; keep the hand edits (accept) "
                                     "or rebuild with overwrite=True")
    buf = io.BytesIO()
    prs.save(buf)
    with zipfile.ZipFile(io.BytesIO(buf.getvalue())) as z:
        members = {i.filename: z.read(i.filename) for i in z.infolist() if not i.is_dir()}
    data = zip_bytes(normalise(members, title=title, theme=theme))
    back = Presentation(io.BytesIO(data))                      # round-trip before touching disk
    if len(back.slides) != len(prs.slides):
        raise UnsupportedPart("normalised package %s" % path.name, need=len(prs.slides), have=len(back.slides),
                              hint="slides were lost on reopen; a part the normaliser does not know was dropped")
    _atomic_write(data, path)
    sha = sha256_bytes(data)
    man = dict(manifest or {})
    man.update({"pptx": path.name, "sha256": sha, "title": title, "theme": theme.name,
                "slides": len(prs.slides)})
    _atomic_write((json.dumps(man, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"),
                  manifest_path(path))
    return sha


# ------------------------------------------------------------------ validation

def find_validator() -> Path:
    hits = sorted(glob.glob(VALIDATOR_GLOB))
    if not hits:
        raise ValidatorMissing("XSD validator", need=VALIDATOR_GLOB, have="no match",
                               hint="the synced pptx skill is missing; validation fails until it is back")
    return Path(hits[0])


_PML = {}
_MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
_PART_XSD = re.compile(r"ppt/(slides|slideLayouts|slideMasters|notesSlides|notesMasters|handoutMasters)/[^/]+\.xml$")


def _pml_schema(validator: Path):
    """The validator bundle's own pml.xsd, loaded in place (never copied)."""
    key = str(validator)
    if key not in _PML:
        xsd = validator.parent / "schemas" / "ISO-IEC29500-4_2016" / "pml.xsd"
        if not xsd.is_file():
            raise ValidatorMissing("pml.xsd", need=str(xsd), have="missing",
                                   hint="the validator's schema bundle moved; slide parts cannot be checked")
        _PML[key] = etree.XMLSchema(etree.parse(str(xsd)))
    return _PML[key]


def _strip_mc(root):
    """mc:AlternateContent replaced by its Fallback (or dropped), as a reader without the extension would."""
    for ac in list(root.iter("{%s}AlternateContent" % _MC)):
        parent = ac.getparent()
        fb = ac.find("{%s}Fallback" % _MC)
        i = parent.index(ac)
        for c in (list(fb) if fb is not None else []):
            parent.insert(i, c)
            i += 1
        parent.remove(ac)
    ign = root.get("{%s}Ignorable" % _MC)
    if ign is not None:
        del root.attrib["{%s}Ignorable" % _MC]
    return root


def part_xsd(path, validator: Path | None = None) -> list[str]:
    """Schema errors in slide, layout, master and notes parts.

    The referenced validator maps a schema only for parts directly under ppt/, so every slide, layout
    and master is reported "Skipped (no schema)" and a foreign element in a master passes (measured
    2026-10-03 with a planted <p:bogus/>). This pass closes that gap with the bundle's own pml.xsd.
    """
    schema = _pml_schema(validator or find_validator())
    errs = []
    with zipfile.ZipFile(path) as z:
        for n in sorted(z.namelist()):
            if not _PART_XSD.match(n):
                continue
            root = _strip_mc(_xml(z.read(n)))
            if not schema.validate(root):
                for e in list(schema.error_log)[:3]:
                    errs.append("%s:%d: %s" % (n, e.line, e.message[:240]))
    return errs


def validate_xsd(path) -> tuple[bool, str]:
    """(ok, detail): the referenced ISO 29500 validator, plus part_xsd over slide-level parts.

    Raises ValidatorMissing when the validator or its schema bundle cannot be found or cannot run.
    """
    v = find_validator()
    r = subprocess.run([sys.executable, str(v), os.path.abspath(str(path))], cwd=str(v.parent),
                       env=dict(os.environ, PYTHONPATH=str(v.parent)), capture_output=True, text=True,
                       timeout=600)
    out = (r.stdout + r.stderr).strip()
    if r.returncode not in (0, 1) or "Traceback" in out or (r.returncode == 0 and "PASSED" not in out):
        raise ValidatorMissing("XSD validator run", need="exit 0 or 1", have="exit %d" % r.returncode,
                               hint=(out.splitlines() or [""])[-1][:300])
    parts = part_xsd(path, v)
    ok = r.returncode == 0 and not parts
    detail = [out.splitlines()[-1] if (ok and out) else out] if r.returncode != 0 or ok else []
    if parts:
        detail.append("slide-level parts against pml.xsd:")
        detail += ["  " + e for e in parts]
    return ok, "\n".join(d for d in detail if d)


_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_SHAPE_PARTS = re.compile(r"ppt/(slides|slideLayouts|slideMasters|notesSlides|notesMasters|handoutMasters)/\w+\d+\.xml$")


def structural_check(path) -> list[str]:
    """Package defects as 'part: message' strings. Empty list is a pass.

    Once-only duplicates, dangling r:ids, missing relationship targets, content types (svg included),
    unique cNvPr ids per part, glue ids that exist, sldId >= 256, no control characters, no negative
    extents, and a python-pptx reopen.
    """
    out = []
    with zipfile.ZipFile(path) as z:
        names = [i.filename for i in z.infolist() if not i.is_dir()]
        blobs = {n: z.read(n) for n in names}
    nameset = set(names)
    if "[Content_Types].xml" not in nameset:
        return ["[Content_Types].xml: missing"]
    q = "{%s}" % CT_NS
    ct = _xml(blobs["[Content_Types].xml"])
    defaults = {d.get("Extension", "").lower(): d.get("ContentType") for d in ct.findall(q + "Default")}
    overrides = {o.get("PartName", "").lstrip("/"): o.get("ContentType") for o in ct.findall(q + "Override")}
    for ext in ("rels", "xml"):
        if ext not in defaults:
            out.append("[Content_Types].xml: no Default for .%s" % ext)
    for pn in overrides:
        if pn not in nameset:
            out.append("[Content_Types].xml: Override for a missing part /%s" % pn)
    for n in names:
        if n == "[Content_Types].xml":
            continue
        ext = _ext(n)
        t = overrides.get(n) or defaults.get(ext)
        if t is None:
            out.append("%s: no content type" % n)
        elif ext == "svg" and t != SVG_CT:
            out.append("%s: svg typed %s" % (n, t))
    # relationships
    rel_ids = collections.defaultdict(set)
    for n in names:
        if not n.endswith(".rels"):
            continue
        src = _source_of(n)
        if src and src not in nameset:
            out.append("%s: rels for a missing part %s" % (n, src))
        try:
            root = _xml(blobs[n])
        except etree.XMLSyntaxError as e:
            out.append("%s: not well-formed (%s)" % (n, e))
            continue
        for rel in root:
            rid = rel.get("Id")
            if rid in rel_ids[src]:
                out.append("%s: duplicate relationship id %s" % (n, rid))
            rel_ids[src].add(rid)
            if rel.get("TargetMode") == "External":
                continue
            tgt = _resolve(src, rel.get("Target", ""))
            if tgt not in nameset:
                out.append("%s: %s targets missing part %s" % (n, rid, tgt))
    # XML parts
    for n in names:
        if not (n.endswith(".xml") or n.endswith(".rels")):
            continue
        text = blobs[n].decode("utf-8", "replace")
        if _CTRL.search(text):
            out.append("%s: control character in XML" % n)
        if n.endswith(".rels"):
            continue
        try:
            root = _xml(blobs[n])
        except etree.XMLSyntaxError as e:
            out.append("%s: not well-formed (%s)" % (n, e))
            continue
        rids = rel_ids.get(n, set())
        for el in root.iter():
            if not isinstance(el.tag, str):
                continue
            for k, v in el.attrib.items():
                if k.startswith("{%s}" % R_NS) and v and v not in rids:
                    out.append("%s: r:%s=%s has no relationship" % (n, etree.QName(k).localname, v))
            if etree.QName(el).localname in ("ext", "chExt") and el.tag.startswith(_A):
                for a in ("cx", "cy"):
                    if el.get(a) is not None and int(el.get(a)) < 0:
                        out.append("%s: negative extent %s=%s" % (n, a, el.get(a)))
        if _SHAPE_PARTS.match(n):
            for container, child, k, sid in once_only_violations(root):
                out.append("%s: <%s> holds <%s> x%d (shape id %s)" % (n, container, child, k, sid))
            ids = [e.get("id") for e in root.iter(_P + "cNvPr")]
            for i, k in collections.Counter(ids).items():
                if k > 1:
                    out.append("%s: cNvPr id %s used %d times" % (n, i, k))
            idset = set(ids)
            for tag in ("stCxn", "endCxn"):
                for e in root.iter(_A + tag):
                    if e.get("id") not in idset:
                        out.append("%s: %s glued to missing shape id %s" % (n, tag, e.get("id")))
        if n == "ppt/presentation.xml":
            for e in root.iter(_P + "sldId"):
                v = int(e.get("id", "0"))
                if not 256 <= v <= 2147483647:
                    out.append("%s: sldId %d outside 256..2147483647" % (n, v))
            for tag in ("sldMasterId", "sldLayoutId"):
                for e in root.iter(_P + tag):
                    if int(e.get("id", "0")) < 2147483648:
                        out.append("%s: %s %s below 2147483648" % (n, tag, e.get("id")))
        if n.startswith("ppt/slideMasters/"):
            for e in root.iter(_P + "sldLayoutId"):
                if int(e.get("id", "0")) < 2147483648:
                    out.append("%s: sldLayoutId %s below 2147483648" % (n, e.get("id")))
    try:
        from pptx import Presentation
        prs = Presentation(str(path))
        for s in prs.slides:
            list(s.shapes)
    except Exception as e:                                  # any reopen failure is a defect
        out.append("reopen: %s: %s" % (type(e).__name__, e))
    return out


__all__ = ["save", "validate_xsd", "part_xsd", "structural_check", "find_validator", "normalise", "write_members",
           "zip_bytes", "core_xml", "app_xml", "sha256_file", "sha256_bytes", "manifest_path", "lock_path",
           "FIXED_TIME", "FIXED_DATE", "AUTHOR", "VALIDATOR_GLOB"]
