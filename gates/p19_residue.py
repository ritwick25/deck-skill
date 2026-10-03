"""P19 residue: no layout placeholder, empty text box, "Click to add", slot token, device sample string, hidden slide or hidden shape.

Device sample strings are the sample copy each library device carries (devices/devices.pptx, listed in
devices/devices.json "samples"). On a slide tagged with a device's variant (deckkit.devices.place tags it), a slot
that still holds its own sample was never filled: the check is slot by slot, so a deck's own copy that happens to
match a different slot's sample (a role name such as "Delivery manager") is never residue. Every slide is also
checked against samples of four words or more anywhere, which catches a sample moved out of its slot. A shared basis
label ("Illustrative figures") is P23's copy, never residue. Until the device library is assembled the files do not
exist, and the check prints SKIPPED with the reason rather than passing silently.
"""
from __future__ import annotations

import json
import re
import sys

from _shared import DEVICES_JSON, FAIL, NOTE, Finding, cli, is_filled, is_lined, text_of

DEVICES_PPTX = DEVICES_JSON.parent / "devices.pptx"

GATE, TITLE = "P19", "residue"
CLICK = re.compile(r"(?i)click to (?:add|edit)")
SLOT = re.compile(r"\{\{\s*slot\s*:|\{\{[^}]*\}\}")


DISTINCT_WORDS = 4      # outside a placed device, only a sample this long is distinctive enough to match


def _norm(t: str) -> str:
    return " ".join(t.split())


def _is_basis(t: str) -> bool:
    return t.endswith(" figures") and len(t.split()) == 2


def _slot_samples() -> dict:
    """{variant: {slot name: its sample text}} read from the device library deck, slot by slot."""
    if not DEVICES_JSON.is_file() or not DEVICES_PPTX.is_file():
        return {}
    from pptx import Presentation
    d = json.loads(DEVICES_JSON.read_text(encoding="utf-8"))
    items = d.get("devices", d) if isinstance(d, dict) else d
    lib = Presentation(str(DEVICES_PPTX))
    out = {}

    def walk(shapes):
        for sh in shapes:
            if sh.shape_type == 6:
                yield from walk(sh.shapes)
            else:
                yield sh
    for dev in (items.values() if isinstance(items, dict) else items):
        if not isinstance(dev, dict) or not dev.get("index"):
            continue
        m = out.setdefault(dev.get("variant"), {})
        for sh in walk(lib.slides[dev["index"] - 1].shapes):
            if sh.name.startswith("slot.") and sh.has_text_frame:
                t = _norm(sh.text_frame.text)
                if len(t) >= 6 and len(t.split()) >= 2 and not _is_basis(t):
                    m[sh.name] = t
    return out


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
    slots = _slot_samples() if samples is not None else {}
    if samples is None:
        out.append(Finding(GATE, NOTE, None, "devices.json", "SKIPPED device sample strings: %s not yet published"
                           % DEVICES_JSON))
    dr = ctx.dr
    tags = ctx.tags()
    for i in range(1, ctx.n + 1):
        root = ctx.slide_root(i)
        own = slots.get(tags[i - 1].get("variant"), {}) if samples else {}
        check = samples[1] if samples else set()
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
            mine = own.get(L["name"])
            if mine and mine in _norm(t):
                out.append(Finding(GATE, FAIL, i, L["name"], "slot still holds its device sample %r" % mine[:40]))
                continue
            for smp in sorted(check):
                if not _is_basis(smp) and smp in t:
                    out.append(Finding(GATE, FAIL, i, L["name"], "device sample string %r" % smp[:40]))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
