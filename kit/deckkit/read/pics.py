"""Picture facts: image part, pixels, crop, effective dpi, SVG and HD Photo layers, recolour, kind guess."""
from __future__ import annotations

import hashlib
import io
import math
import re

from .ns import A, R, local, qn

AI_HINT = re.compile(r"chatgpt|dall|generated", re.I)
RECOLOUR = ("duotone", "biLevel", "lum", "clrChange", "grayscl", "clrRepl")

try:
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
except Exception:      # pragma: no cover
    Image = None


def _image_stats(blob: bytes) -> dict:
    """Pixel size, alpha, unique colours in a 64x64 downsample, and grey-level entropy."""
    out = {"px": None, "has_alpha": False, "alpha_frac": 0.0, "unique64": None, "entropy": None,
           "format": None}
    if Image is None or not blob:
        return out
    try:
        im = Image.open(io.BytesIO(blob))
        out["px"] = [int(im.size[0]), int(im.size[1])]
        out["format"] = im.format
        if im.format in ("WMF", "EMF"):
            return out
        im.draft("RGB", (256, 256))
        mode_alpha = im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info)
        small = im.convert("RGBA").resize((64, 64), Image.Resampling.BILINEAR)
        px = small.tobytes()
        alphas = px[3::4]
        transparent = sum(1 for a in alphas if a < 250)
        out["has_alpha"] = bool(mode_alpha and transparent)
        out["alpha_frac"] = round(transparent / 4096.0, 3)
        opaque = {px[i:i + 3] for i in range(0, len(px), 4) if px[i + 3] >= 128}
        out["unique64"] = len(opaque)
        hist = small.convert("L").histogram()
        n = float(sum(hist)) or 1.0
        out["entropy"] = round(-sum(h / n * math.log2(h / n) for h in hist if h), 3)
    except Exception as e:     # unreadable or unsupported image: keep the bytes facts
        out["error"] = type(e).__name__
    return out


def part_facts(deck, part: str) -> dict:
    """Facts that depend only on the image part; cached per deck."""
    cache = deck.cache.setdefault("pic_parts", {})
    f = cache.get(part)
    if f is not None:
        return f
    blob = deck.blob(part) if deck.has(part) else b""
    f = {"part": "/" + part, "content_type": deck.content_type(part), "bytes": len(blob),
         "sha1": hashlib.sha1(blob).hexdigest() if blob else None}
    f.update(_image_stats(blob))
    cache[part] = f
    return f


def kind_guess(f: dict, w_in: float, h_in: float, bbox: tuple, canvas: tuple[float, float],
               in_chrome: bool) -> str:
    """icon | logo | photo | screenshot | illustration, from pixels, size, aspect and position."""
    long_side = max(w_in, h_in)
    short_side = max(min(w_in, h_in), 1e-6)
    aspect = max(w_in, h_in) / short_side
    uniq = f.get("unique64") or 0
    ent = f.get("entropy") or 0.0
    alpha = f.get("has_alpha")
    cw, ch = canvas
    x, y, w, h = bbox
    near_edge = (y < 0.15 * ch or y + h > 0.85 * ch) and (x < 0.2 * cw or x + w > 0.8 * cw)
    if f.get("format") in ("WMF", "EMF") or (f.get("content_type") or "").endswith("svg+xml"):
        return "icon" if long_side <= 0.8 else "illustration"
    if 0.12 <= long_side <= 0.8 and aspect <= 2.5 and not (in_chrome and near_edge):
        return "icon"
    if (in_chrome or near_edge) and long_side <= 2.5 and (alpha or uniq < 400) and (aspect >= 1.5 or long_side <= 1.2):
        return "logo"
    if uniq >= 1800 and ent >= 6.8 and not alpha:
        return "photo"
    if long_side >= 2.0 and not alpha and uniq < 1800 and ent < 6.8 and aspect <= 2.6:
        return "screenshot"
    if uniq >= 2500 and not alpha:
        return "photo"
    return "illustration"


def picture_facts(deck, slide_part: str, pic, frame_w_in: float, frame_h_in: float, bbox_in: tuple,
                  name: str, descr: str, title: str, in_chrome: bool = False) -> dict | None:
    """p:pic (or a blipFill-bearing element) to the picture block."""
    bf = pic.find(qn("p:blipFill"))
    if bf is None:
        bf = pic.find(A("blipFill"))
    if bf is None:
        return None
    blip = bf.find(A("blip"))
    rels = deck.rels(slide_part)
    part = None
    out: dict = {}
    if blip is not None:
        rid = blip.get(R("embed")) or blip.get(R("link"))
        if rid and rid in rels and rels[rid][2] != "External":
            part = rels[rid][1]
        elif rid and rid in rels:
            out["external"] = rels[rid][1]
    if part is not None:
        out.update(part_facts(deck, part))
    else:
        out.update({"part": None, "content_type": None, "bytes": 0, "sha1": None, "px": None})
    crop = {"l": 0.0, "t": 0.0, "r": 0.0, "b": 0.0}
    sr = bf.find(A("srcRect"))
    if sr is not None:
        for k in crop:
            crop[k] = int(sr.get(k, "0")) / 1e5
    out["crop"] = crop
    out["mode"] = "tile" if bf.find(A("tile")) is not None else "stretch"
    dpi = None
    if out.get("px") and frame_w_in > 0 and frame_h_in > 0:
        vis_w = out["px"][0] * max(1e-6, 1 - crop["l"] - crop["r"])
        vis_h = out["px"][1] * max(1e-6, 1 - crop["t"] - crop["b"])
        dpi = round(min(vis_w / frame_w_in, vis_h / frame_h_in), 1)
    out["dpi_effective"] = dpi
    svg_part = hd_part = None
    artistic, recolour = [], []
    alpha = 1.0
    if blip is not None:
        for ext in blip.iter(A("ext")):
            for c in ext:
                n = local(c)
                if n == "svgBlip":
                    rid = c.get(R("embed"))
                    if rid in rels:
                        svg_part = "/" + rels[rid][1]
                elif n == "imgProps":
                    for layer in c.iter(qn("a14:imgLayer")):
                        rid = layer.get(R("embed"))
                        if rid in rels:
                            hd_part = "/" + rels[rid][1]
                        for eff in layer.iter(qn("a14:imgEffect")):
                            for e in eff:
                                artistic.append(local(e))
        for c in blip:
            n = local(c)
            if n in RECOLOUR:
                recolour.append(n)
            elif n == "alphaModFix":
                alpha = int(c.get("amt", "100000")) / 1e5
    out["svg_part"] = svg_part
    out["hdphoto_part"] = hd_part
    out["artistic"] = artistic
    out["recolour"] = recolour
    out["alpha"] = round(alpha, 3)
    out["kind_guess"] = kind_guess(out, frame_w_in, frame_h_in, bbox_in, (deck.w_in, deck.h_in), in_chrome)
    hint_src = " ".join(x for x in (name, descr, title) if x)
    m = AI_HINT.search(hint_src)
    out["ai_hint"] = m.group(0) if m else None
    out["decorative"] = _decorative(pic)
    return out


def _decorative(pic) -> bool:
    for d in pic.iter(qn("adec:decorative")):
        return d.get("val") in ("1", "true")
    return False
