"""P22 icons: every SVG picture has a raster fallback, every raster is at least 2x its displayed size, vendor marks keep a registered hue, no emoji.

  * an svgBlip with no r:embed raster beside it renders blank in older readers;
  * a raster's effective resolution (pixels over displayed inches, crop applied) is at least 192 dpi;
  * a vendor mark (a picture named icon.aws.*, icon.azure.* or icon.gcp.*) keeps its own hue, and that hue
    must be one the theme's identity registry declares (CIEDE2000 under 12), so it is a decision, not drift;
  * emoji are never icons.
"""
from __future__ import annotations

import io
import sys

from _shared import FAIL, Finding, cli, text_of
from deckkit.read.ns import local
from deckkit.read.walk import EMOJI
from deckkit.theme import delta_e00

GATE, TITLE = "P22", "icons"
MIN_DPI = 2 * 96
VENDOR = ("icon.aws.", "icon.azure.", "icon.gcp.")
HUE_DE = 12.0


def _dominant(blob):
    from PIL import Image
    import colorsys
    im = Image.open(io.BytesIO(blob)).convert("RGBA").resize((64, 64))
    counts = {}
    for r, g, b, a in im.getdata():
        if a < 200:
            continue
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if s < 0.25 or l < 0.12 or l > 0.92:
            continue
        key = (r // 16, g // 16, b // 16)
        counts[key] = counts.get(key, 0) + 1
    if not counts:
        return None
    r, g, b = max(counts, key=counts.get)
    return "%02X%02X%02X" % (r * 16 + 8, g * 16 + 8, b * 16 + 8)


def run(deck, ctx):
    out = []
    dr = ctx.dr
    ids = [v["hex"] for v in ctx.theme.identity.values()]
    for i in range(1, ctx.n + 1):
        part = dr.slide_part(i)
        rels = dr.rels(part)
        for pic in ctx.slide_root(i).iter("{*}pic"):
            c = pic.find(".//{*}cNvPr")
            name = c.get("name", "") if c is not None else ""
            blip = pic.find(".//{*}blip")
            if blip is None:
                continue
            svg = [e for e in blip.iter() if isinstance(e.tag, str) and local(e) == "svgBlip"]
            emb = blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
            target = rels.get(emb, (None, None, None))[1] if emb else None
            ct = dr.content_type(target) if target else None
            if svg and (not target or not dr.has(target) or not (ct or "").startswith(("image/png", "image/jpeg"))):
                out.append(Finding(GATE, FAIL, i, name, "SVG picture without a PNG fallback (r:embed %s, %s)" % (emb, ct)))
        for L in ctx.slide(i)["shapes"]:
            pic = L.get("picture")
            if pic and pic.get("dpi_effective") is not None and (pic.get("format") not in ("WMF", "EMF")) \
                    and pic["dpi_effective"] < MIN_DPI:
                out.append(Finding(GATE, FAIL, i, L["name"], "raster at %.0f dpi on glass (min %d, 2x its size)"
                                   % (pic["dpi_effective"], MIN_DPI)))
            if pic and L["name"].startswith(VENDOR) and pic.get("part"):
                hx = _dominant(dr.blob(pic["part"].lstrip("/")))
                if hx and not any(delta_e00(hx, h) < HUE_DE for h in ids):
                    out.append(Finding(GATE, FAIL, i, L["name"], "vendor hue %s is not in the theme identity registry" % hx))
            t = text_of(L)
            if t and EMOJI.search(t):
                out.append(Finding(GATE, FAIL, i, L["name"], "emoji used as an icon: %r" % EMOJI.search(t).group(0)))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
