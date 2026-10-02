"""P18 leak: nothing on or in the deck matches the hashed corpus references, and the package carries no residue.

References live in devices/refs (or the folder a run names): SHA-1 digests only, never plaintext, all keyed
by deckkit.read.refnorm, the one normalisation the harvester used too. The canary in refs/canary.json is
fired first: its probe must hit names, 6-grams and numeric phrases, and its clean sentence must hit none,
or no pass is trusted. A missing refs folder or file is a FAIL.

  text      every text block on slides, layouts and masters, notes, alt text, shape names and docProps text:
            1-4-gram name keys (names.sha1), shared 6-word shingles (ngrams6.sha1), distinctive numeric
            phrases (numphrases.sha1). deck.json "client" allows that client's own name on its own deck.
  pictures  every media part: sha256 in media.json fails unless deck.json "media_allow" names it with a
            reason; a dHash within Hamming distance 5 of any corpus raster fails.
  vectors   every custGeom signature (refnorm.custgeom_sig) against vectors.sha1.
  alt text  no file paths, no scrape tails.
  package   no notes text, comments, comment authors, customXml, tags, custData, embedded fonts, thumbnail,
            TitlesOfParts or HeadingPairs, revision parts, HD Photo layers, external links, "Google Shape;"
            names, custom properties other than the kit's tags; creator and lastModifiedBy "Sigmoid"; a kit
            build's master and layout equal the kit base.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile

from _shared import ADVISORY, FAIL, NOTE, SKILL, Finding, InputMissing, cli, text_of
from deckkit.read import refnorm as rn
from deckkit.read.ns import local
from deckkit.read.textmetrics import para_text

GATE, TITLE = "P18", "leak"
FILES = ("names.sha1", "ngrams6.sha1", "numphrases.sha1", "vectors.sha1", "media.json", "canary.json")
DHASH_MIN = 6
ALT_PATH = re.compile(r"(?:^|\s)(?:/[\w.~-]+){2,}|[A-Za-z]:\\|\b[\w-]+\.(?:png|jpe?g|gif|svg|emf|wmf|bmp|tiff?|webp|wdp)\b",
                      re.I)
SCRAPE = re.compile(r"wikimedia|png vector|preencoded|chatgpt image|free d(?:ownload)?\b|stock photo|shutterstock|"
                    r"getty|clipart|vector \(pdf\)", re.I)
RESIDUE = (
    (re.compile(r"ppt/comments/|ppt/commentAuthors\.xml$|ppt/authors\.xml$"), "comments or comment authors"),
    (re.compile(r"^customXml/"), "customXml"),
    (re.compile(r"ppt/tags/"), "tags"),
    (re.compile(r"ppt/fonts/"), "embedded font"),
    (re.compile(r"docProps/thumbnail"), "thumbnail"),
    (re.compile(r"revisionInfo\.xml$|changesInfos/"), "revision history"),
    (re.compile(r"\.wdp$"), "HD Photo layer"),
)


def _set(p):
    return {ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()}


class Refs:
    def __init__(self, folder):
        if not folder.is_dir():
            raise InputMissing("leak references folder missing: %s" % folder)
        for f in FILES:
            if not (folder / f).is_file():
                raise InputMissing("leak reference missing: %s" % (folder / f))
        self.names = _set(folder / "names.sha1")
        self.ngrams = _set(folder / "ngrams6.sha1")
        self.nums = _set(folder / "numphrases.sha1")
        self.vectors = _set(folder / "vectors.sha1")
        media = json.loads((folder / "media.json").read_text(encoding="utf-8"))
        items = media.get("items", [])
        self.media_sha = {m["sha256"] for m in items if m.get("sha256")}
        self.dhashes = [m["dhash"] for m in items if m.get("dhash")]
        self.canary = json.loads((folder / "canary.json").read_text(encoding="utf-8"))

    def text_hits(self, text, allow=frozenset()):
        out = []
        for k in rn.name_keys(text):
            if k not in allow and rn.sha1(k) in self.names:
                out.append(("name", k))
        for sh in rn.shingles(text):
            if rn.sha1(sh) in self.ngrams:
                out.append(("6-gram", sh))
        for n in rn.num_phrases(text):
            if rn.sha1(n) in self.nums:
                out.append(("number", n))
        return out


def _canary(refs):
    c = refs.canary
    probe = refs.text_hits(c.get("probe_text", ""))
    kinds = {k for k, _ in probe}
    clean = refs.text_hits(c.get("clean_text", ""))
    bad = []
    for k in ("name", "6-gram", "number"):
        if k not in kinds:
            bad.append("the canary probe produced no %s hit" % k)
    if clean:
        bad.append("the canary's clean sentence hit %s" % clean[:3])
    return bad


def _texts(ctx):
    """(slide or None, where, text) for every text the package carries."""
    dr = ctx.dr
    out = []
    for i in range(1, ctx.n + 1):
        s = ctx.slide(i)
        for L in s["shapes"] + s["chrome"]:
            if text_of(L).strip():
                out.append((i, L["name"] or "id %s" % L["id"], text_of(L)))
        for c in ctx.slide_root(i).iter("{*}cNvPr"):
            for a in ("descr", "title"):
                if (c.get(a) or "").strip():
                    out.append((i, "%s alt" % (c.get("name") or c.get("id")), c.get(a)))
            if c.get("name"):
                out.append((i, "shape name", c.get("name")))
    with zipfile.ZipFile(ctx.deck_path) as z:
        for n in sorted(z.namelist()):
            if re.match(r"ppt/(slideLayouts|slideMasters|notesSlides|notesMasters|handoutMasters)/[^/]+\.xml$", n):
                root = dr.xml(n)
                for p in root.iter("{*}p"):
                    if local(p) == "p" and p.getparent() is not None and local(p.getparent()) == "txBody":
                        t = para_text(p)
                        if t.strip():
                            out.append((None, n, t))
            elif n in ("docProps/core.xml", "docProps/app.xml"):
                root = dr.xml(n)
                for el in root.iter():
                    if isinstance(el.tag, str) and (el.text or "").strip():
                        out.append((None, n, el.text))
    return out


def _base_c14n(ctx):
    from lxml import etree
    base = SKILL / "kit" / "assets" / ("base-%s.pptx" % ctx.canvas.name)
    out = {}
    with zipfile.ZipFile(base) as z:
        for n in ("ppt/slideMasters/slideMaster1.xml", "ppt/slideLayouts/slideLayout1.xml"):
            out[n] = etree.tostring(etree.fromstring(z.read(n)), method="c14n")
    return out


def run(deck, ctx):
    from lxml import etree
    refs = ctx.refs_dir
    R = Refs(refs)
    bad = _canary(R)
    if bad:
        return [Finding(GATE, FAIL, None, "canary", b + " (%s); no pass can be trusted" % refs) for b in bad]
    out = [Finding(GATE, NOTE, None, "refs", "%s: %d names, %d 6-grams, %d numbers, %d vectors, %d media; canary caught"
                   % (refs, len(R.names), len(R.ngrams), len(R.nums), len(R.vectors), len(R.media_sha)))]
    dj = ctx.deck_json
    allow = set()
    if dj.get("client"):
        allow = rn.name_keys(str(dj["client"]))
    seen = set()
    for i, where, t in _texts(ctx):
        for kind, key in R.text_hits(t, allow):
            if (i, where, kind, key) in seen:
                continue
            seen.add((i, where, kind, key))
            out.append(Finding(GATE, FAIL, i, where, "%s matches the corpus: %r" % (kind, key)))
    # pictures
    media_allow = dj.get("media_allow") or {}
    dr = ctx.dr
    with zipfile.ZipFile(ctx.deck_path) as z:
        names = sorted(z.namelist())
        for n in names:
            if not n.startswith("ppt/media/"):
                continue
            blob = z.read(n)
            sha = hashlib.sha256(blob).hexdigest()
            if sha in R.media_sha and not media_allow.get(sha):
                out.append(Finding(GATE, FAIL, None, n, "picture bytes are a corpus image (sha256 %s...)" % sha[:12]))
                continue
            dh = rn.dhash64(blob)
            if dh:
                near = min((rn.hamming64(dh, c) for c in R.dhashes), default=64)
                if near < DHASH_MIN and not media_allow.get(sha):
                    out.append(Finding(GATE, FAIL, None, n, "picture is within dHash distance %d of a corpus image" % near))
        # package residue
        for n in names:
            for rx, what in RESIDUE:
                if rx.search(n):
                    out.append(Finding(GATE, FAIL, None, n, "package residue: %s" % what))
        for n in names:
            if n.endswith(".rels"):
                for rel in etree.fromstring(z.read(n)):
                    if rel.get("TargetMode") == "External" and rel.get("Target") not in (dj.get("links_allow") or []):
                        out.append(Finding(GATE, FAIL, None, n, "external link %s" % rel.get("Target", "")[:80]))
        for n in names:
            if re.match(r"ppt/notesSlides/[^/]+\.xml$", n):
                t = " ".join(para_text(p) for p in dr.xml(n).iter("{*}p") if local(p) == "p").strip()
                if t and not re.fullmatch(r"\d+", t):
                    out.append(Finding(GATE, FAIL, None, n, "notes text travels with the deck: %r" % t[:40]))
        if "docProps/app.xml" in names:
            app = dr.xml("docProps/app.xml")
            for el in app.iter():
                if isinstance(el.tag, str) and local(el) in ("TitlesOfParts", "HeadingPairs"):
                    out.append(Finding(GATE, FAIL, None, "docProps/app.xml", "%s lists the deck's parts" % local(el)))
        if "docProps/core.xml" in names:
            core = dr.xml("docProps/core.xml")
            for el in core.iter():
                if isinstance(el.tag, str) and local(el) in ("creator", "lastModifiedBy"):
                    if (el.text or "").strip() != "Sigmoid":
                        out.append(Finding(GATE, FAIL, None, "docProps/core.xml", "%s is %r, not 'Sigmoid'"
                                           % (local(el), (el.text or "").strip())))
        if "docProps/custom.xml" in names:
            from deckkit import tag as tagmod
            for k in tagmod.parse_props(z.read("docProps/custom.xml")):
                if not k.startswith(tagmod.PREFIX):
                    out.append(Finding(GATE, FAIL, None, "docProps/custom.xml", "custom property %r" % k))
        if dr.embedded_fonts():
            out.append(Finding(GATE, FAIL, None, "ppt/presentation.xml", "embedded fonts: %s" % ", ".join(dr.embedded_fonts())))
        for n in names:
            if not re.match(r"ppt/(slides|slideLayouts|slideMasters)/[^/]+\.xml$", n):
                continue
            root = dr.xml(n)
            for el in root.iter():
                if not isinstance(el.tag, str):
                    continue
                ln = local(el)
                if ln == "custGeom":
                    sig = rn.custgeom_sig(el)
                    if sig and rn.sha1(sig) in R.vectors:
                        out.append(Finding(GATE, FAIL, None, n, "custom geometry matches a corpus vector"))
                elif ln in ("custDataLst", "tags"):
                    out.append(Finding(GATE, FAIL, None, n, "package residue: %s" % ln))
                elif ln == "cNvPr":
                    nm = el.get("name") or ""
                    if nm.startswith("Google Shape;"):
                        out.append(Finding(GATE, FAIL, None, n, "export residue in a shape name: %r" % nm[:40]))
                    for a in ("descr", "title"):
                        v = el.get(a) or ""
                        if ALT_PATH.search(v) or SCRAPE.search(v):
                            out.append(Finding(GATE, FAIL, None, n, "alt text carries a path or a scrape tail: %r" % v[:60]))
    # base master and layout
    if ctx.manifest is not None:
        try:
            base = _base_c14n(ctx)
        except (KeyError, FileNotFoundError) as e:
            out.append(Finding(GATE, ADVISORY, None, "base", "kit base not comparable: %s" % e))
            base = {}
        for n, want in base.items():
            if not dr.has(n):
                out.append(Finding(GATE, FAIL, None, n, "the kit base part is missing"))
                continue
            have = etree.tostring(etree.fromstring(dr.blob(n)), method="c14n")
            if have != want:
                out.append(Finding(GATE, FAIL, None, n, "differs from the kit base: a foreign master or layout travelled"))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
