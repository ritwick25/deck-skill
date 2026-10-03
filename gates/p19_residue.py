"""P19 residue: no layout placeholder, empty text box, "Click to add", slot token, device sample string, hidden slide or hidden shape.

Device sample strings are the sample copy registered for each device in devices/devices.json ("samples"). A
slide tagged with a device's variant (deckkit.devices.place tags it) is checked against all of that device's
samples; every other slide only against samples of four words or more;
a placed device whose sample survived was never filled. Until the device library is assembled that file
does not exist, and the check prints SKIPPED with the reason rather than passing silently.
"""
from __future__ import annotations

import json
import re
import sys

from _shared import DEVICES_JSON, FAIL, NOTE, Finding, cli, is_filled, is_lined, text_of

GATE, TITLE = "P19", "residue"
CLICK = re.compile(r"(?i)click to (?:add|edit)")
SLOT = re.compile(r"\{\{\s*slot\s*:|\{\{[^}]*\}\}")


DISTINCT_WORDS = 4      # outside a placed device, only a sample this long is distinctive enough to match


def _samples():
    """(per-variant samples {variant: set}, distinctive samples set), or None when the library is not published.
    A device's own slide (tagged with its variant) is checked against all its samples; every other slide only
    against samples of DISTINCT_WORDS words or more, so ordinary short copy is never mistaken for filler."""
    if not DEVICES_JSON.is_file():
        return None
    d = json.loads(DEVICES_JSON.read_text(encoding="utf-8"))
    items = d.get("devices", d) if isinstance(d, dict) else d
    per, distinct = {}, set()
    for dev in (items.values() if isinstance(items, dict) else items):
        if not isinstance(dev, dict):
            continue
        ss = {x.strip() for x in dev.get("samples") or [] if isinstance(x, str) and len(x.strip()) >= 6
              and len(x.split()) >= 2}          # a one-word label ("Approach") is ordinary copy, not filler
        per.setdefault(dev.get("variant"), set()).update(ss)
        distinct.update(x for x in ss if len(x.split()) >= DISTINCT_WORDS)
    return per, distinct


def run(deck, ctx):
    out = []
    samples = _samples()
    if samples is None:
        out.append(Finding(GATE, NOTE, None, "devices.json", "SKIPPED device sample strings: %s not yet published"
                           % DEVICES_JSON))
    dr = ctx.dr
    tags = ctx.tags()
    for i in range(1, ctx.n + 1):
        root = ctx.slide_root(i)
        own = samples[0].get(tags[i - 1].get("variant"), set()) if samples else set()
        check = (own | samples[1]) if samples else set()
        if root.get("show") in ("0", "false"):
            out.append(Finding(GATE, FAIL, i, "", "hidden slide travels with the deck"))
        for ph in root.iter("{*}ph"):
            nm = ph.getparent().getparent().find("{*}cNvPr")
            out.append(Finding(GATE, FAIL, i, nm.get("name") if nm is not None else "", "layout placeholder (%s) on a slide"
                               % ph.get("type", "obj")))
        s = ctx.slide(i)
        for sid in next((h["ids"] for h in s["hygiene"] if h["kind"] == "hidden-shape"), []):
            out.append(Finding(GATE, FAIL, i, "id %s" % sid, "hidden shape"))
        for L in s["shapes"]:
            t = text_of(L)
            if L["kind"] == "sp" and L.get("text") is not None and not t.strip() and not is_filled(L) \
                    and not is_lined(L) and not L.get("icon_like") and not (L.get("geom") or {}).get("cust"):
                out.append(Finding(GATE, FAIL, i, L["name"], "empty text box that draws nothing"))
            if not t.strip():
                continue
            if CLICK.search(t):
                out.append(Finding(GATE, FAIL, i, L["name"], "placeholder prompt %r" % t[:40]))
            if SLOT.search(t):
                out.append(Finding(GATE, FAIL, i, L["name"], "unfilled slot token %r" % SLOT.search(t).group(0)))
            for smp in sorted(check):
                if smp in t:
                    out.append(Finding(GATE, FAIL, i, L["name"], "device sample string %r" % smp[:40]))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
