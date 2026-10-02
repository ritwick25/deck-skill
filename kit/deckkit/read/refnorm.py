"""Normalisation and hashing for the leak references (devices/refs). ONE implementation, imported by the
library's harvester (library/tools/harvest_refs.py) and by the skill's leak gate, so a hash computed on a
built deck equals the hash harvested from the corpus.

Every key is hashed as SHA-1 of its UTF-8 bytes, lowercase hex.

names     fold: NFKD, combining marks dropped, typographic quotes to ASCII, casefold.
          name_tokens(): the counted tokens of textmetrics.tokens(); an e-mail or URL token stays whole and
          canonical (scheme, www., query, fragment and trailing slash dropped); any other token loses a trailing
          possessive ('s or s') and splits on every character that is not a letter, digit or '&'.
          A key is the space-joined casefolded tokens. When every token of the gram is 3 characters or
          shorter the key is 'cs:' plus the space-joined case-preserved tokens (short terms match
          case-sensitively). name_keys() gives every 1- to 4-gram key of a text; term_keys() gives the key of a
          denylist term (all 4-token windows when it is longer than 4 tokens). canon_url() keeps v and list on
          video hosts, where the path alone is generic.
shingles  shingle_tokens(): textmetrics.tokens() (so the count equals words()), each folded and stripped of
          leading and trailing characters that are not letters or digits. A shingle is 6 consecutive tokens
          joined by single spaces, computed per text block (one shape or cell).
numbers   num_phrases(): a numeric token (optional currency, digits with optional thousands commas and
          decimals, optional unit suffix) canonicalised (commas dropped, lowercase) and either kept alone when it
          has 3 or more significant digits and a currency, unit, comma or decimal mark, or paired with the next
          word when that word is alphabetic, at least 3 letters, not a stopword, and the number is distinctive
          (marked, or a bare value of 11 or more that is not a year; a bare value of 100 or less followed by a
          time, page or month word is not). A 1-2 letter word between number and noun travels with the noun.
vectors   custgeom_sig(): every a:path of an a:custGeom, coordinates divided by the path w/h (or the point
          extent when w/h is absent) and quantised to a 1/64 grid; arcs keep quantised radii and whole-degree
          angles. Signatures with fewer than 5 points are trivial and return None.
pictures  dhash64(): image composited on white, greyscale, LANCZOS to 9x8, 64 horizontal-gradient bits, hex.
"""
from __future__ import annotations

import hashlib
import io
import re
import unicodedata

from .ns import A, local
from .textmetrics import tokens

QUOTES = str.maketrans({"‘": "'", "’": "'", "‚": "'", "‛": "'", "′": "'",
                        "“": '"', "”": '"', "„": '"', " ": " "})
_EMAIL = re.compile(r"^[\w.+-]+@[\w-]+(?:\.[\w-]+)+$", re.UNICODE)
_URL = re.compile(r"^(?:https?://|www\.)\S+$|^[\w-]+(?:\.[\w-]+)*\.(?:com|org|net|io|ai|co|app|dev|in|uk|de|gov|edu)"
                  r"(?:[/:?#]\S*)?$", re.I | re.UNICODE)
_SPLIT = re.compile(r"[^\w&]+|_", re.UNICODE)
_EDGE = re.compile(r"^[^\w]+|[^\w]+$|^_+|_+$", re.UNICODE)
_TRAIL = ".,;:!?)]}\"'>"
_LEAD = "([{\"'<"


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def fold(s: str, casefold: bool = True) -> str:
    s = unicodedata.normalize("NFKD", (s or "").translate(QUOTES))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.casefold() if casefold else s


_URL_KEEP = {"v", "list"}      # video hosts identify the resource by these query parameters only


def canon_url(tok: str) -> str:
    """Host and path, casefolded, without scheme, www., fragment, trailing slash or query; on a video host
    (youtube.com, youtu.be) the v and list parameters are kept, sorted and case-preserved, because the path
    alone is generic."""
    t = tok.strip(_TRAIL).lstrip(_LEAD).replace("&amp;", "&")
    t = re.sub(r"(?i)^https?://", "", t)
    t = re.sub(r"(?i)^www+\.", "", t)
    t = t.split("#", 1)[0]
    base, _, query = t.partition("?")
    base = base.rstrip("/").casefold()
    host = base.split("/", 1)[0]
    if host.endswith("youtube.com") or host.endswith("youtu.be"):
        keep = sorted(p for p in query.split("&") if p.split("=", 1)[0] in _URL_KEEP and "=" in p)
        if keep:
            base += "?" + "&".join(keep)
    return base


def _strip_possessive(t: str) -> str:
    if len(t) > 2 and t[-2:] in ("'s", "'S"):
        return t[:-2]
    if len(t) > 2 and t[-1] == "'" and t[-2] in "sS":
        return t[:-1]
    return t


def name_tokens(text: str) -> list[tuple[str, str]]:
    """(casefolded, case-preserved) name tokens of a text, in order."""
    out: list[tuple[str, str]] = []
    for raw in tokens(fold(text, casefold=False)):
        core = raw.strip(_TRAIL).lstrip(_LEAD)
        if _EMAIL.match(core):
            c = core.rstrip("._").casefold()
            out.append((c, c))
            continue
        if ("/" in core or core.lower().startswith("www.") or "." in core) and _URL.match(core) \
                and not re.fullmatch(r"[\d.,]+", core):
            c = canon_url(core)
            out.append((c, c))
            continue
        core = _strip_possessive(core)
        for part in _SPLIT.split(core):
            if part and re.search(r"[^\W_]", part):
                out.append((part.casefold(), part))
    return out


def _gram_key(gram: list[tuple[str, str]]) -> str:
    if all(len(cs) <= 3 for _cf, cs in gram):
        return "cs:" + " ".join(cs for _cf, cs in gram)
    return " ".join(cf for cf, _cs in gram)


def name_keys(text: str, nmax: int = 4) -> set[str]:
    """Every 1..nmax-gram key of a text (what a gate hashes and looks up in names.sha1)."""
    toks = name_tokens(text)
    keys = set()
    for n in range(1, nmax + 1):
        for i in range(0, len(toks) - n + 1):
            keys.add(_gram_key(toks[i:i + n]))
    return keys


def term_keys(term: str, nmax: int = 4) -> list[str]:
    """Key(s) of one denylist term: the whole term, or every nmax-token window of a longer term."""
    toks = name_tokens(term)
    if not toks:
        return []
    if len(toks) <= nmax:
        return [_gram_key(toks)]
    return sorted({_gram_key(toks[i:i + nmax]) for i in range(0, len(toks) - nmax + 1)})


# ------------------------------------------------------------------ shingles

def shingle_tokens(text: str) -> list[str]:
    out = []
    for t in tokens(text or ""):
        f = _EDGE.sub("", fold(t))
        out.append(f if f else fold(t))
    return out


def shingles(text: str, n: int = 6) -> set[str]:
    toks = shingle_tokens(text)
    return {" ".join(toks[i:i + n]) for i in range(0, len(toks) - n + 1)}


# ------------------------------------------------------------------ numeric phrases

_NUM = re.compile(r"^(?P<pre>[$€£₹¥]|usd|eur|gbp|inr)?"
                  r"(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
                  r"(?P<suf>%|\+|x|×|k|m|mm|mn|bn|b|cr|pp|bps)?(?P<plus>\+)?$", re.I)
STOP = frozenset("a an the of to in on for and or by with at from per vs is are be as than more less over under "
                 "across into via its it this that these those our their your we you was were has have had not no "
                 "all each every any some up out off but so if then when while also still only just even now "
                 "here there what which who whose how why where never always everything nothing".split())
TIME = frozenset("second seconds sec secs minute minutes min mins hour hours hr hrs day days week weeks wk wks "
                 "month months mo year years yr yrs quarter quarters sprint sprints slide slides page pages step "
                 "steps phase phases jan feb mar apr may jun jul aug sep sept oct nov dec january february march "
                 "april june july august september october november december".split())


def _num_parts(tok: str):
    t = fold(tok).strip(_TRAIL).lstrip(_LEAD + "~≈<>≤≥")
    m = _NUM.match(t)
    if not m:
        return None
    num = m.group("num")
    digits = num.replace(",", "").replace(".", "")
    sig = digits.lstrip("0")
    if "." not in num:
        sig = sig.rstrip("0")
    canon = (m.group("pre") or "") + num.replace(",", "") + (m.group("suf") or "") + (m.group("plus") or "")
    marked = bool(m.group("pre") or m.group("suf") or m.group("plus") or "," in num or "." in num)
    try:
        value = float(num.replace(",", ""))
    except ValueError:
        value = 0.0
    year = (not marked) and re.fullmatch(r"(?:19|20)\d\d", num) is not None
    return canon, len(sig), marked, value, year


def num_phrases(text: str) -> set[str]:
    raw = tokens(text or "")
    out: set[str] = set()
    for i, tok in enumerate(raw):
        p = _num_parts(tok)
        if p is None:
            continue
        canon, nsig, marked, value, year = p
        if year:
            continue
        if nsig >= 3 and marked:
            out.add(canon)
        distinctive = marked or value >= 11
        if not distinctive or i + 1 >= len(raw):
            continue
        nxt = _strip_possessive(fold(raw[i + 1]).strip(_TRAIL).lstrip(_LEAD))
        if re.fullmatch(r"[^\W\d_]{1,2}", nxt) and nxt not in STOP and i + 2 < len(raw):
            # a short acronym between the number and its noun ("100+ AI products") travels with the noun
            nxt2 = _strip_possessive(fold(raw[i + 2]).strip(_TRAIL).lstrip(_LEAD))
            if re.fullmatch(r"[^\W\d_]{3,}", nxt2) and nxt2 not in STOP:
                out.add(canon + " " + nxt + " " + nxt2)
            continue
        if not re.fullmatch(r"[^\W\d_]{3,}", nxt) or nxt in STOP:
            continue
        if not marked and nxt in TIME and value <= 100:
            continue
        out.add(canon + " " + nxt)
    return out


# ------------------------------------------------------------------ vectors

def _q(v: float, Q: int = 64) -> int:
    return int(round(v * Q))


def custgeom_sig(cg, Q: int = 64, min_points: int = 5) -> str | None:
    """Normalised signature of one a:custGeom element, or None when trivial."""
    pl = cg.find(A("pathLst"))
    if pl is None:
        return None
    sigs = []
    npts = 0
    for path in pl:
        if local(path) != "path":
            continue
        cmds = []
        pts_all = []
        for c in path:
            name = local(c)
            pts = []
            for pt in c.iter(A("pt")):
                pts.append((pt.get("x", "0"), pt.get("y", "0")))
            cmds.append((name, pts, c))
            pts_all.extend(pts)

        def num(v):
            try:
                return float(v)
            except (TypeError, ValueError):
                return None
        xs = [num(x) for x, _y in pts_all if num(x) is not None]
        ys = [num(y) for _x, y in pts_all if num(y) is not None]
        w = num(path.get("w")) or (max(xs) - min(xs) if xs else 0) or 1.0
        h = num(path.get("h")) or (max(ys) - min(ys) if ys else 0) or 1.0
        x0 = 0.0 if num(path.get("w")) else (min(xs) if xs else 0.0)
        y0 = 0.0 if num(path.get("h")) else (min(ys) if ys else 0.0)
        letter = {"moveTo": "M", "lnTo": "L", "cubicBezTo": "C", "quadBezTo": "Q", "arcTo": "A", "close": "Z"}
        parts = []
        for name, pts, el in cmds:
            L = letter.get(name, "?" + name)
            coords = []
            for x, y in pts:
                nx, ny = num(x), num(y)
                coords.append(str(_q((nx - x0) / w, Q)) if nx is not None else "g:" + str(x))
                coords.append(str(_q((ny - y0) / h, Q)) if ny is not None else "g:" + str(y))
            if name == "arcTo":
                for k, d in (("wR", w), ("hR", h)):
                    v = num(el.get(k))
                    coords.append(str(_q(v / d, Q)) if v is not None else "g:" + str(el.get(k)))
                for k in ("stAng", "swAng"):
                    v = num(el.get(k))
                    coords.append(str(int(round(v / 60000.0))) if v is not None else "g:" + str(el.get(k)))
            npts += len(pts) + (1 if name == "arcTo" else 0)
            parts.append(L + (" " + " ".join(coords) if coords else ""))
        sigs.append(" ".join(parts))
    if npts < min_points or not sigs:
        return None
    return " | ".join(sigs)


# ------------------------------------------------------------------ pictures

def dhash64(blob: bytes) -> str | None:
    """64-bit difference hash of a raster image blob, or None for vector and unreadable formats."""
    try:
        from PIL import Image
    except Exception:      # pragma: no cover
        return None
    try:
        im = Image.open(io.BytesIO(blob))
        if im.format in ("WMF", "EMF") or im.format is None:
            return None
        if im.format == "JPEG":
            im.draft("RGB", (64, 64))
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        bg.alpha_composite(im)
        g = bg.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
        px = g.tobytes()
        bits = 0
        for r in range(8):
            row = px[r * 9:(r + 1) * 9]
            for c in range(8):
                bits = (bits << 1) | (1 if row[c + 1] > row[c] else 0)
        return "%016x" % bits
    except Exception:
        return None


def hamming64(a: str, b: str) -> int:
    return (int(a, 16) ^ int(b, 16)).bit_count()
