"""P26 architecture: an architecture slide reads like an enterprise architecture diagram, not a board of tiles (ruling 18).

Scoped to slides tagged layered-architecture or solution-architecture. Measured against eight reference architecture
slides: they carry 20 to 45 product marks (median 36), box 0 to 10% of their icons alone in a tile, and label 7 of 7
to 11 of 14 flows with what moves. Checks follow library/design/tech-diagrams/spec.md section 2 (the letter after each
is the spec's, where it has one):

  (a) product marks: pictures named vendor.* or mark.* (deckkit.icons, byte-verified by P22) whose longer side is at
      least 0.30in, not counting actor and generic glyphs (aws/general/*, onprem/generic/*, generic/*, the Azure users
      mark): at least 20 on an aws or azure variant and on any other solution architecture, 15 on a house deep dive,
      16 on a layered architecture. A deck.json grant "P26:marks" with its source exempts a conceptual architecture;
  (b) icons boxed alone: an icon (a picture or a glyph whose longer side is at least 0.30in) is boxed alone when the
      smallest filled or outlined shape that holds it, 0.6 to 2.4in on each side, holds no other icon. At most 10%
      of a slide's icons (spec 1.3);
  (c) on a variant that does not start with "l0": at least 80% of headed connectors carry a label (a text of 1 to 6
      words whose ink lies within 0.45in of one of the connector's segment midpoints, or a knock-out text filled with
      its ground within 0.20in of a segment, and that is neither a mark's caption nor a tile's own text), a step badge
      (an ellipse whose text is a number, within 0.35in of either end or 0.20in of a segment), or a keyed line style (a dashed kind with a
      sample in the slide's legend, named *.legend.key.*);
  (d) on an "l0-*" variant (the L0 master): no headed connector and no step badge at all (CLAUDE.md section 8);
  (e) every product mark has a caption: a text whose ink starts within 0.35in below the mark and overlaps it across,
      sits within 0.35in beside it and overlaps it down, or (an edge pin) ends within 0.35in above it;
  (h) no two headed connectors cross: a crossing reads as a junction (spec allows a hop gap; the engine draws none);
  (j) step badges: numbered 1..N without a gap, at most 12, one badge size; 5 to 12 steps on an aws variant, 5 to 10
      on azure, 4 to 10 on a house deep dive;
  (k) boundaries: the outer two levels of dashed or notation-coloured frames (cloud, account, subscription, region,
      a platform boundary, a trust zone) state a fact: their label carries a clause after a middot or a colon. At
      least 3 boundary kinds (stroke colour and dash) on an aws or azure variant, 2 on a house slide;
  (l0) an "l0-*" variant varies its regions (at least 4 distinct region top-and-width pairs) and draws two icon tiers;
  (r) no orphan: every product mark outside a platform band (a frame named *.band) is the end of a connector
      (within 0.06in of its box); not judged on an L0 master;
  (s) notation: on an aws variant no actor or generic glyph sits inside the AWS Cloud frame, no managed regional
      service (Bedrock, S3, DynamoDB, SQS, SNS, EventBridge, SES, CloudFront) inside a VPC frame, and every headed
      connector that crosses a VPC border starts or ends on an edge pin (a picture centred on that border); on an
      azure variant no PaaS mark (storage, Cosmos DB, AI Search, OpenAI, Key Vault) sits inside a subnet panel;
  (u) labels and badges collide with nothing: no flow label or step badge lies on a mark or on another connector's
      segment (a knock-out label on its own line is its own);
  (v) one component, one mark: across the deck's architecture slides a caption name is drawn with one vendor mark per
      vendor family (house rule 13);
  (w) marks share one optical size: a mark's ink fills at least 75% of its picture along its longer side, so a
      mark with a transparent margin is cropped to its ink (deckkit.arch does it with a:srcRect).
"""
from __future__ import annotations

import io
import math
import re
import sys

from _shared import FAIL, NOTE, Finding, bx, cli, has_text, ink_box, is_filled, is_lined, text_of
from deckkit.read.ns import A

GATE, TITLE = "P26", "architecture"
SCOPE = {"solution-architecture": 20, "layered-architecture": 16}
VARIANT_FLOOR = {"house-deep-dive": 15}
NOTATION = 0.30
BOX_MIN, BOX_MAX = 0.6, 2.4
BOXED_MAX = 0.10
LABELLED_MIN = 0.80
LABEL_REACH, LABEL_WORDS = 0.45, 6
KNOCKOUT_REACH = 0.20
BADGE_REACH = 0.35
CAPTION_REACH = 0.35
EPS = 0.01
ACTOR_KEYS = ("aws/general/", "onprem/generic/", "generic/", "azure/identity/users", "azure/general/usericon")
STEP_BAND = {"aws": (5, 12), "azure": (5, 10), "house-deep-dive": (4, 10)}
STEP_MAX = 12
KINDS_MIN = {"aws": 3, "azure": 3, "house": 2}
NOTATION_HEX = {"232F3E", "242F3E", "E7157B", "00A4A6", "147EBA", "8C4FFF", "7AA116", "DD344C", "DD3522", "ED7100",
                "7D8998", "0078D4", "0070C0", "A4CBFB", "7A7A7A"}
VPC_HEX = "8C4FFF"
CLOUD_HEX = ("232F3E", "242F3E")
SUBNET_FILL = "F8F8F8"
REGIONAL = ("aws/ml/", "aws/storage/simple-storage-service-s3", "aws/database/dynamodb", "aws/integration/",
            "aws/engagement/", "aws/network/cloudfront")
AZURE_PAAS = ("azure/storage/", "azure/databases/", "azure/database/", "azure/aimachinelearning/",
              "azure/security/key-vaults")
INK_MIN = 0.75
PIN_TOL = 0.02
VENDOR_ALT = re.compile(r"\((?:vendor|brand) mark ([A-Za-z0-9_./-]+)\)\s*$")


def _headed(line) -> bool:
    line = line or {}
    return (line.get("head") or {}).get("type", "none") != "none" or \
           (line.get("tail") or {}).get("type", "none") != "none"


def _path_points(ctx, i, L):
    """Every point of a custGeom open path in slide inches, in order, or None."""
    el = ctx.element(i, L["id"])
    cg = el.find(".//" + A("custGeom")) if el is not None else None
    if cg is None:
        return None
    pts = []
    for path in cg.iter(A("path")):
        w, h = float(path.get("w", "0") or 0), float(path.get("h", "0") or 0)
        for c in path:
            for pt in c.iter(A("pt")):
                try:
                    pts.append((float(pt.get("x")), float(pt.get("y")), w, h))
                except (TypeError, ValueError):
                    pass
    if len(pts) < 2:
        return None
    c0, c1, _c2, c3 = L["corners_in"]
    fh, fv = L["xfrm"]["flipH"], L["xfrm"]["flipV"]
    out = []
    for x, y, w, h in pts:
        u = x / w if w else 0.0
        v = y / h if h else 0.0
        u, v = (1 - u if fh else u), (1 - v if fv else v)
        out.append((c0[0] + u * (c1[0] - c0[0]) + v * (c3[0] - c0[0]),
                    c0[1] + u * (c1[1] - c0[1]) + v * (c3[1] - c0[1])))
    return out


def connectors(ctx, i, leaves):
    """[(leaf, [points])] for every headed connector on slide i: straight connectors and open custom paths."""
    out = []
    for L in leaves:
        if not _headed(L.get("line")):
            continue
        c = L.get("connector")
        if (L.get("geom") or {}).get("cust"):          # an elbow: every corner, not only its two ends
            pts = _path_points(ctx, i, L)
            if pts:
                out.append((L, pts))
                continue
        if c is not None and c.get("start_in") and c.get("end_in"):
            out.append((L, [tuple(c["start_in"]), tuple(c["end_in"])]))
    return out


def _dist(pt, box) -> float:
    x0, y0, x1, y1 = box
    dx = max(x0 - pt[0], 0.0, pt[0] - x1)
    dy = max(y0 - pt[1], 0.0, pt[1] - y1)
    return math.hypot(dx, dy)


def _side(L) -> float:
    """The longer side: a wordmark 0.9 x 0.2in is a product mark; a 0.26in group tab is notation."""
    x0, y0, x1, y1 = bx(L)
    return max(x1 - x0, y1 - y0)


def mark_key(L) -> str | None:
    """The vendor or brand key a mark picture records in its alt text."""
    m = VENDOR_ALT.search(L.get("descr") or "")
    return m.group(1) if m else None


def is_actor(L) -> bool:
    k = mark_key(L) or ""
    return k.startswith(ACTOR_KEYS)


def marks(leaves, actors: bool = False):
    """Product mark pictures (vendor.* or mark.*, at least NOTATION a side); actors=True keeps the actor and generic
    glyphs too (they still need a caption)."""
    return [L for L in leaves if L["kind"] == "pic" and (L.get("name") or "").startswith(("vendor.", "mark."))
            and _side(L) >= NOTATION - EPS and (actors or not is_actor(L))]


def icons(leaves):
    return [L for L in leaves if (L["kind"] == "pic" or L.get("icon_like")) and _side(L) >= NOTATION - EPS]


def _inside(inner, outer, eps=EPS) -> bool:
    """inner lies within outer (eps grows outer; a negative eps asks for clear room inside it)."""
    return inner[0] >= outer[0] - eps and inner[1] >= outer[1] - eps and inner[2] <= outer[2] + eps and \
        inner[3] <= outer[3] + eps


def boxed_alone(leaves, ics):
    """The icons that are the only icon inside the smallest drawn shape of 0.6 to 2.4in a side that holds them."""
    shells = []
    for L in leaves:
        if L["kind"] != "sp" or L.get("line_like") or L.get("icon_like") or L.get("connector") is not None:
            continue
        if not (is_filled(L) or is_lined(L)):
            continue
        x0, y0, x1, y1 = bx(L)
        if BOX_MIN - EPS <= x1 - x0 <= BOX_MAX + EPS and BOX_MIN - EPS <= y1 - y0 <= BOX_MAX + EPS:
            shells.append(L)
    out = []
    for I in ics:
        ib = bx(I)
        holders = [S for S in shells if S is not I and _inside(ib, bx(S))]
        if not holders:
            continue
        S = min(holders, key=lambda s: (bx(s)[2] - bx(s)[0]) * (bx(s)[3] - bx(s)[1]))
        sb = bx(S)
        if sum(1 for J in ics if _inside(bx(J), sb)) == 1:
            out.append((I, S))
    return out


def _is_badge(L) -> bool:
    return (L.get("geom") or {}).get("prst") in ("ellipse", "flowChartConnector") and has_text(L) and \
        text_of(L).strip().isdigit()


def _words(L) -> int:
    return (L.get("text") or {}).get("words", 0)


def _names_something(T, ics, leaves) -> bool:
    """A text that is a mark's caption or a tile's own text is not a flow label: it sits within 0.35in under or
    beside an icon, or inside a drawn shape smaller than 2.4in a side."""
    for I in ics:
        if captioned(I, [T], strict=True):
            return True
    tb = ink_box(T)
    for L in leaves:
        if L is T or L["kind"] != "sp" or L.get("line_like") or L.get("connector") is not None:
            continue
        if not (is_filled(L) or is_lined(L)):
            continue
        x0, y0, x1, y1 = bx(L)
        if x1 - x0 <= BOX_MAX and y1 - y0 <= BOX_MAX and _inside(tb, (x0, y0, x1, y1)) and \
                ((x1 - x0) - (tb[2] - tb[0]) > 0.08 or (y1 - y0) - (tb[3] - tb[1]) > 0.08):
            return True
    return False


def _seg_dist(box, p, q) -> float:
    """The distance from an orthogonal segment to a box (0 when they touch)."""
    x0, y0, x1, y1 = box
    sx0, sx1 = sorted((p[0], q[0]))
    sy0, sy1 = sorted((p[1], q[1]))
    dx = max(x0 - sx1, 0.0, sx0 - x1)
    dy = max(y0 - sy1, 0.0, sy0 - y1)
    return math.hypot(dx, dy)


def carried(cxn_pts, texts, badges, knockouts=()) -> str | None:
    """'label', 'badge' or None for one connector's points."""
    mids = [((p[0] + q[0]) / 2, (p[1] + q[1]) / 2) for p, q in zip(cxn_pts, cxn_pts[1:])]
    for T in texts:
        tb = ink_box(T)
        if any(_dist(m, tb) <= LABEL_REACH for m in mids):
            return "label"
    for T in knockouts:
        if any(_seg_dist(bx(T), p, q) <= KNOCKOUT_REACH for p, q in zip(cxn_pts, cxn_pts[1:])):
            return "label"
    ends = (cxn_pts[0], cxn_pts[-1])
    for B in badges:
        if any(_dist(e, bx(B)) <= BADGE_REACH for e in ends) or \
                any(_seg_dist(bx(B), p, q) <= KNOCKOUT_REACH for p, q in zip(cxn_pts, cxn_pts[1:])):
            return "badge"
    return None


def captioned(M, texts, strict: bool = False) -> bool:
    """A text names mark M: it starts within 0.35in below M and overlaps it across, or sits within 0.35in beside it
    and overlaps it down. strict (used to tell a caption from a flow label) also wants it centred: under the mark's
    span, or level with the mark's centre line."""
    mx0, my0, mx1, my1 = bx(M)
    mcx, mcy = (mx0 + mx1) / 2, (my0 + my1) / 2
    for T in texts:
        tx0, ty0, tx1, ty1 = ink_box(T)
        below = my1 - 0.05 <= ty0 <= my1 + CAPTION_REACH and min(mx1, tx1) - max(mx0, tx0) > 0
        beside = min(my1, ty1) - max(my0, ty0) > 0 and (0 <= tx0 - mx1 <= CAPTION_REACH or 0 <= mx0 - tx1 <= CAPTION_REACH)
        above = (not strict) and my0 - CAPTION_REACH <= ty1 <= my0 + 0.05 and min(mx1, tx1) - max(mx0, tx0) > 0
        if strict:
            below = below and mx0 <= (tx0 + tx1) / 2 <= mx1
            beside = beside and ty0 <= mcy <= ty1
        if below or beside or above:
            return True
    return False


def _family(variant: str) -> str:
    v = variant or ""
    return "aws" if v.startswith("aws") else "azure" if v.startswith("azure") else "house"


def _segs(pts):
    return list(zip(pts, pts[1:]))


def _cross(p, q, e1, e2, eps: float = 0.01) -> bool:
    ph, eh = abs(p[1] - q[1]) < 1e-6, abs(e1[1] - e2[1]) < 1e-6
    pv, ev = abs(p[0] - q[0]) < 1e-6, abs(e1[0] - e2[0]) < 1e-6
    if not ((ph and ev) or (pv and eh)):
        return False
    (h1, h2), (v1, v2) = ((p, q), (e1, e2)) if ph else ((e1, e2), (p, q))
    y, x = h1[1], v1[0]
    hx0, hx1 = sorted((h1[0], h2[0]))
    vy0, vy1 = sorted((v1[1], v2[1]))
    return hx0 + eps < x < hx1 - eps and vy0 + eps < y < vy1 - eps


def _hits(box, p, q, shrink: float = 0.005) -> bool:
    x0, y0, x1, y1 = box[0] + shrink, box[1] + shrink, box[2] - shrink, box[3] - shrink
    return _seg_dist((x0, y0, x1, y1), p, q) <= 0.0


def _frames(leaves):
    """Drawn frames: rectangles with an outline or a fill, at least 0.8in a side, that are not text tiles."""
    out = []
    for L in leaves:
        if L["kind"] != "sp" or L.get("line_like") or L.get("connector") is not None or L.get("icon_like"):
            continue
        if not (is_filled(L) or is_lined(L)) or has_text(L):
            continue
        x0, y0, x1, y1 = bx(L)
        if x1 - x0 >= 0.8 and y1 - y0 >= 0.6:
            out.append(L)
    return out


def _line(L):
    ln = L.get("line") or {}
    return (ln.get("hex") or "").upper(), ln.get("dash") or "solid", ln.get("type", "none")


def _label_of(F, texts):
    """The label text of a frame: a text whose ink starts within 0.5in below its top (or just above it, a label set
    over the frame) and within 0.95in of its left edge."""
    x0, y0, x1, y1 = bx(F)
    inside, above = [], []
    for T in texts:
        tx0, ty0, tx1, ty1 = ink_box(T)
        if not (x0 - 0.05 <= tx0 <= x0 + 0.95 and tx1 <= x1 + 0.05):
            continue
        if y0 - 0.02 <= ty0 <= y0 + 0.5:
            inside.append(T)
        elif y0 - 0.35 <= ty0 and ty1 <= y0 + 0.02:
            above.append(T)                               # a label set over the frame (the Azure VNet)
    pool = inside or above
    return min(pool, key=lambda T: abs(ink_box(T)[1] - y0)) if pool else None


def _ink_ratio(ctx, i, L):
    """The share of a mark picture its ink fills along the longer side, through its a:srcRect crop; None when the
    picture's blob cannot be read or has no alpha channel."""
    try:
        from PIL import Image
        shape = next(sh for sh in ctx.prs().slides[i - 1].shapes if sh.shape_id == L["id"])
        blob = shape.image.blob
        el = ctx.element(i, L["id"])
        sr = el.find(".//" + A("srcRect")) if el is not None else None
        cl = ct = cr = cb = 0.0
        if sr is not None:
            cl, ct = int(sr.get("l", 0)) / 1e5, int(sr.get("t", 0)) / 1e5
            cr, cb = int(sr.get("r", 0)) / 1e5, int(sr.get("b", 0)) / 1e5
        with Image.open(io.BytesIO(blob)) as im:
            if "A" not in im.getbands() and im.mode != "P":
                return None
            im = im.convert("RGBA")
            W, H = im.size
            box = (round(cl * W), round(ct * H), round(W - cr * W), round(H - cb * H))
            crop = im.crop(box)
            cw, chh = crop.size
            bb = crop.getchannel("A").point(lambda a: 255 if a > 16 else 0).getbbox()
        if bb is None or not cw or not chh:
            return None
        return max((bb[2] - bb[0]) / cw, (bb[3] - bb[1]) / chh)
    except Exception:
        return None


def run(deck, ctx):
    out = []
    tags = ctx.tags()
    scoped = 0
    names = {}                                            # (v): caption name -> {(family, key): slide}
    for i in range(1, ctx.n + 1):
        t = tags[i - 1]
        arch = t.get("archetype")
        if arch not in SCOPE:
            continue
        scoped += 1
        variant = t.get("variant") or ""
        fam = _family(variant)
        l0 = variant.startswith("l0")
        leaves = ctx.slide(i)["shapes"]
        texts = [L for L in leaves if has_text(L) and L.get("name") != "title" and not _is_badge(L)]
        ms = marks(leaves)
        allm = marks(leaves, actors=True)
        # (a)
        need = VARIANT_FLOOR.get(variant, SCOPE[arch])
        src = ctx.overridden("P26:marks")
        if len(ms) < need:
            if src:
                out.append(Finding(GATE, NOTE, i, "marks", "%d product marks, under %d; granted by deck.json (%s)"
                                   % (len(ms), need, src)))
            else:
                out.append(Finding(GATE, FAIL, i, "marks", "%d product marks on a %s slide, needs %d (the references "
                                   "carry 20 to 45; actor and generic glyphs do not count); draw services with "
                                   "deckkit.icons vendor or mark" % (len(ms), variant or arch, need)))
        # (b)
        ics = icons(leaves)
        alone = boxed_alone(leaves, ics)
        if ics and len(alone) / len(ics) > BOXED_MAX + 1e-9:
            nm = ", ".join(sorted({S.get("name") or str(S["id"]) for _I, S in alone})[:4])
            out.append(Finding(GATE, FAIL, i, "boxed", "%d of %d icons boxed alone (%.0f%%, at most %.0f%%), in %s: "
                               "float marks on the group ground, one card per icon is the generated look"
                               % (len(alone), len(ics), 100.0 * len(alone) / len(ics), 100 * BOXED_MAX, nm)))
        # (c) and (d)
        cx = connectors(ctx, i, leaves)
        badges = [L for L in leaves if _is_badge(L)]
        keyed = {_line(L)[1] for L in leaves if ".legend.key." in (L.get("name") or "") and not _headed(L.get("line"))}
        knockouts = [T for T in texts if is_filled(T) and 1 <= _words(T) <= LABEL_WORDS
                     and not _names_something(T, ics, leaves)]
        if l0:
            if cx:
                out.append(Finding(GATE, FAIL, i, "l0", "%d headed connector(s) on an L0 master (%s); the L0 master "
                                   "carries no arrows and no numbering" % (len(cx), cx[0][0].get("name"))))
            if badges:
                out.append(Finding(GATE, FAIL, i, "l0", "%d step badge(s) on an L0 master; the L0 master carries no "
                                   "numbering" % len(badges)))
        elif cx:
            labels = [T for T in texts if 1 <= _words(T) <= LABEL_WORDS and not _names_something(T, ics, leaves)]
            bare = [L for L, pts in cx if carried(pts, labels, badges, knockouts) is None
                    and _line(L)[1] not in (keyed - {"solid"})]
            share = 1.0 - len(bare) / len(cx)
            if share + 1e-9 < LABELLED_MIN:
                out.append(Finding(GATE, FAIL, i, "flows", "%d of %d headed connectors carry a label, a step badge or a "
                                   "keyed line style (%.0f%%, needs %.0f%%); unlabelled: %s"
                                   % (len(cx) - len(bare), len(cx), 100 * share, 100 * LABELLED_MIN,
                                      ", ".join(L.get("name") or str(L["id"]) for L in bare[:4]))))
        # (e)
        bare_marks = [M for M in allm if not captioned(M, texts)]
        for M in bare_marks[:6]:
            out.append(Finding(GATE, FAIL, i, M.get("name") or str(M["id"]), "product mark without a caption below, "
                               "beside or (an edge pin) above it (within %.2fin)" % CAPTION_REACH))
        if len(bare_marks) > 6:
            out.append(Finding(GATE, FAIL, i, "captions", "and %d more marks without a caption" % (len(bare_marks) - 6)))
        # (h) crossings
        crossings = []
        for k1 in range(len(cx)):
            for k2 in range(k1 + 1, len(cx)):
                for p, q in _segs(cx[k1][1]):
                    for e1, e2 in _segs(cx[k2][1]):
                        if _cross(p, q, e1, e2):
                            crossings.append((cx[k1][0].get("name"), cx[k2][0].get("name")))
        if crossings:
            out.append(Finding(GATE, FAIL, i, "crossings", "%d connector crossing(s), e.g. %s over %s: re-seat a node "
                               "or route round (spec P26.h)" % (len(crossings), *crossings[0])))
        # (j) steps
        nums = sorted({int(text_of(B).strip()) for B in badges})
        if badges and not l0:
            sizes = {round(bx(B)[2] - bx(B)[0], 2) for B in badges}
            lo, hi = STEP_BAND.get(variant if variant in STEP_BAND else fam, (1, STEP_MAX))
            if nums != list(range(1, len(nums) + 1)):
                out.append(Finding(GATE, FAIL, i, "steps", "step numbers %s are not 1..N without a gap" % nums))
            if len(nums) > STEP_MAX:
                out.append(Finding(GATE, FAIL, i, "steps", "%d steps, at most %d" % (len(nums), STEP_MAX)))
            if len(sizes) > 1:
                out.append(Finding(GATE, FAIL, i, "steps", "step badges in %d sizes %s: one badge size per slide"
                                   % (len(sizes), sorted(sizes))))
            if (variant in STEP_BAND or fam in ("aws", "azure")) and not lo <= len(nums) <= hi:
                out.append(Finding(GATE, FAIL, i, "steps", "%d numbered steps on a %s slide, needs %d to %d"
                                   % (len(nums), variant, lo, hi)))
        elif variant in STEP_BAND and not l0 and cx:
            lo, hi = STEP_BAND[variant]
            out.append(Finding(GATE, FAIL, i, "steps", "no numbered steps on a %s slide, needs %d to %d: number the "
                               "primary path and add the legend" % (variant, lo, hi)))
        # (k) boundaries
        frames = _frames(leaves)
        bounds = [F for F in frames if _line(F)[2] != "none" and (_line(F)[1] != "solid" or _line(F)[0] in NOTATION_HEX)]
        def depth(F, pool):
            fb = bx(F)
            return sum(1 for G in pool if G is not F and _inside(fb, bx(G)) and
                       (bx(G)[2] - bx(G)[0]) * (bx(G)[3] - bx(G)[1]) > (fb[2] - fb[0]) * (fb[3] - fb[1]))
        for F in bounds:
            if depth(F, bounds) > 1:
                continue
            lab = _label_of(F, texts)
            txt_ = text_of(lab).strip() if lab is not None else ""
            if not txt_:
                out.append(Finding(GATE, FAIL, i, F.get("name") or str(F["id"]), "an outer boundary without a label "
                                   "(spec 1.6: every boundary carries one)"))
            elif not re.search(r"[·:]\s*\S", txt_):
                out.append(Finding(GATE, FAIL, i, F.get("name") or str(F["id"]), "outer boundary label %r is a bare "
                                   "name; the outer two levels state a fact after a middot or colon ('Region "
                                   "eu-west-1 · 2 AZs')" % txt_[:40]))
        kinds = {(_line(F)[0], _line(F)[1]) for F in frames if _line(F)[2] != "none"}
        if not l0 or True:
            want = KINDS_MIN[fam]
            if len(kinds) < want:
                out.append(Finding(GATE, FAIL, i, "boundaries", "%d boundary kind(s), needs %d (a %s slide nests "
                                   "distinct boundaries: cloud, region, network; a platform boundary and a trust zone)"
                                   % (len(kinds), want, fam)))
        # (l0) varied regions and two tiers
        if l0:
            regions = [F for F in frames if sum(1 for M in ms if _inside(bx(M), bx(F))) >= 2]
            pairs = {(round(bx(F)[1], 1), round(bx(F)[2] - bx(F)[0], 1)) for F in regions}
            tiers = {round(_side(M) / 0.05) for M in ms}
            if len(pairs) < 4:
                out.append(Finding(GATE, FAIL, i, "regions", "%d distinct region top-and-width pairs, needs 4: an "
                                   "evenly sized tile grid is the generated look (spec 3.3)" % len(pairs)))
            if len(tiers) < 2:
                out.append(Finding(GATE, FAIL, i, "tiers", "one icon size; the L0 master draws its anchor products "
                                   "larger (two tiers, spec 3.3)"))
        # (r) orphans
        if not l0:
            bands = [F for F in leaves if (F.get("name") or "").endswith(".band")]
            ends = [pt for _L, pts in cx for pt in (pts[0], pts[-1])]
            orphans = []
            for M in ms:
                mb = bx(M)
                if any(_inside(mb, bx(B)) for B in bands):
                    continue
                if not any(_dist(pt, mb) <= 0.06 for pt in ends):
                    orphans.append(M)
            for M in orphans[:4]:
                out.append(Finding(GATE, FAIL, i, M.get("name") or str(M["id"]), "orphan: a product mark with no flow "
                                   "outside a platform band (spec P26.r); connect it or move it into the band"))
            if len(orphans) > 4:
                out.append(Finding(GATE, FAIL, i, "orphans", "and %d more orphan marks" % (len(orphans) - 4)))
        # (s) notation
        if fam == "aws":
            clouds = [F for F in frames if _line(F)[0] in CLOUD_HEX and _line(F)[1] == "solid"]
            vpcs = [F for F in frames if _line(F)[0] == VPC_HEX]
            for M in allm:
                if is_actor(M) and any(_inside(bx(M), bx(F)) for F in clouds):
                    out.append(Finding(GATE, FAIL, i, M.get("name") or str(M["id"]), "an actor or generic glyph inside "
                                       "the AWS Cloud frame: actors sit outside the cloud (spec 3.1)"))
                if (mark_key(M) or "").startswith(REGIONAL) and any(_inside(bx(M), bx(V), -0.03) for V in vpcs):
                    out.append(Finding(GATE, FAIL, i, M.get("name") or str(M["id"]), "a managed regional service "
                                       "inside the VPC: draw it in the Region, reached through an endpoint"))
            pics = [L for L in leaves if L["kind"] == "pic"]
            for V in vpcs:
                v0, v1, v2, v3 = bx(V)
                pins = [P for P in pics if _pin_on(P, (v0, v1, v2, v3))]
                for L, pts in cx:
                    crosses = any(_crosses_border((v0, v1, v2, v3), p, q) for p, q in _segs(pts))
                    if crosses and not any(_dist(e, bx(P)) <= 0.06 for P in pins for e in (pts[0], pts[-1])):
                        out.append(Finding(GATE, FAIL, i, L.get("name") or str(L["id"]), "crosses the VPC border "
                                           "without landing on an edge pin (an endpoint, a load balancer, a NAT "
                                           "gateway on the border; spec P26.s)"))
        if fam == "azure":
            panels = [F for F in frames if ((F.get("fill") or {}).get("hex") or "").upper() == SUBNET_FILL]
            for M in ms:
                if (mark_key(M) or "").startswith(AZURE_PAAS) and any(_inside(bx(M), bx(F)) for F in panels):
                    out.append(Finding(GATE, FAIL, i, M.get("name") or str(M["id"]), "a PaaS service inside a subnet: "
                                       "PaaS sits outside the VNet, reached through its private endpoint (spec 3.2)"))
        # (u) collisions
        if not l0:
            items = [(T, "label") for T in knockouts] + [(B, "badge") for B in badges
                                                         if ".legend." not in (B.get("name") or "")]
            for T, what in items:
                tb = bx(T)
                tcx, tcy = (tb[0] + tb[2]) / 2, (tb[1] + tb[3]) / 2
                for L, pts in cx:
                    for p, q in _segs(pts):
                        if not _hits(tb, p, q):
                            continue
                        own = what == "label" and (abs(p[1] - q[1]) < 1e-6 and abs(p[1] - tcy) < 0.03 or
                                                   abs(p[0] - q[0]) < 1e-6 and abs(p[0] - tcx) < 0.03)
                        if not own:
                            out.append(Finding(GATE, FAIL, i, T.get("name") or str(T["id"]), "a flow %s lies on "
                                               "connector %s (spec P26.u)" % (what, L.get("name") or L["id"])))
                            break
                for M in allm:
                    mb = bx(M)
                    if min(tb[2], mb[2]) - max(tb[0], mb[0]) > 0.01 and min(tb[3], mb[3]) - max(tb[1], mb[1]) > 0.01:
                        out.append(Finding(GATE, FAIL, i, T.get("name") or str(T["id"]), "a flow %s lies on mark %s "
                                           "(spec P26.u)" % (what, M.get("name") or M["id"])))
        # (v) collect names
        for M in ms:
            k = mark_key(M)
            caps = [T for T in texts if captioned(M, [T], strict=True)]
            if not caps or not k:
                continue
            mx0, my0, mx1, my1 = bx(M)
            T = min(caps, key=lambda T_: _dist(((mx0 + mx1) / 2, (my0 + my1) / 2), ink_box(T_)))
            nm = (text_of(T).splitlines() or [""])[0].strip()
            if nm:
                names.setdefault(nm, {}).setdefault((k.split("/")[0], k), i)
        # (w) ink fills the mark
        for M in ms:
            r = _ink_ratio(ctx, i, M)
            if r is not None and r < INK_MIN:
                out.append(Finding(GATE, FAIL, i, M.get("name") or str(M["id"]), "mark ink fills %.0f%% of its picture "
                                   "(at least %.0f%%): crop it to its ink so marks share one optical size"
                                   % (100 * r, 100 * INK_MIN)))
        out.append(Finding(GATE, NOTE, i, t.get("tag") or "", "%d marks, %d icons, %d boxed alone, %d headed "
                           "connectors, %d steps" % (len(ms), len(ics), len(alone), len(cx), len(nums))))
    # (v) across slides
    for nm, keys in sorted(names.items()):
        fams = {}
        for (fam_, k), sl in keys.items():
            fams.setdefault(fam_, {})[k] = sl
        for fam_, ks in fams.items():
            if len(ks) > 1:
                out.append(Finding(GATE, FAIL, min(ks.values()), nm, "one component drawn with %d marks across the "
                                   "architecture slides (%s): one name, one mark (house rule 13)"
                                   % (len(ks), ", ".join("%s on s%d" % kv for kv in sorted(ks.items())))))
    if not scoped:
        out.append(Finding(GATE, NOTE, None, "", "no layered-architecture or solution-architecture slide"))
    return out


def _pin_on(P, box) -> bool:
    x0, y0, x1, y1 = bx(P)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    l, t, r, b = box
    return ((abs(cx - l) <= PIN_TOL or abs(cx - r) <= PIN_TOL) and t <= cy <= b) or \
        ((abs(cy - t) <= PIN_TOL or abs(cy - b) <= PIN_TOL) and l <= cx <= r)


def _crosses_border(box, p, q) -> bool:
    """An orthogonal segment passes through one of the box's four edges (from inside to outside)."""
    l, t, r, b = box
    (x1, y1), (x2, y2) = p, q
    if abs(y1 - y2) < 1e-6:
        if not (t < y1 < b):
            return False
        lo, hi = sorted((x1, x2))
        return lo < l < hi or lo < r < hi
    if not (l < x1 < r):
        return False
    lo, hi = sorted((y1, y2))
    return lo < t < hi or lo < b < hi


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
