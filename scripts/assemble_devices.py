"""Assemble the device library from devices/work/DLnn/{device.pptx, device.json} (ruling 3, ruling 14).

    $PY scripts/assemble_devices.py [--no-render]

Writes devices/devices.pptx (one slide per device, in id order, each tagged with its archetype and variant),
devices/devices.json ({about, devices: {id: entry + index}}) and devices/renders/<id>-<theme>.png under the
sigmoid and neutral themes. Then gates the assembled file for what a library must hold whatever its contents:
P01 floor, P03 bounds, P11 style, P12 package, P16 colour roles, P17 fingerprints, P18 leak, P22 icons, P25
contrast. Exit 1 on a missing or invalid entry or a failed gate. Device sample strings are expected here; P19 is
what catches them once a device is placed in a deck.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import KIT, PY, SKILL  # noqa: E402

sys.path.insert(0, str(KIT))
from pptx import Presentation  # noqa: E402

from deckkit import package, tag  # noqa: E402
from deckkit.clone import DEVICE_STRIP, copy_shapes  # noqa: E402
from deckkit.theme import Theme, apply_theme  # noqa: E402

DEV = SKILL / "devices"
WORK = DEV / "work"
REQUIRED = ("id", "name", "archetypes", "family", "variant", "mechanism", "slots", "samples")
GATES = "P01,P03,P11,P12,P16,P17,P18,P22,P25"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args()
    th = Theme.load(SKILL / "themes" / "sigmoid.json")
    entries, errs = [], []
    for d in sorted(p for p in WORK.iterdir() if p.is_dir() and p.name.startswith("DL")):
        pj, pp = d / "device.json", d / "device.pptx"
        if not pj.is_file() or not pp.is_file():
            errs.append("%s: device.json or device.pptx missing" % d.name)
            continue
        e = json.loads(pj.read_text())
        miss = [k for k in REQUIRED if k not in e]
        if miss or e.get("id") != d.name:
            errs.append("%s: %s" % (d.name, ("missing " + ", ".join(miss)) if miss else "id does not match its folder"))
            continue
        from deckkit.theme import ROLES
        for sl in e.get("slots", []):                 # a slot's role is a theme colour role; anything else is its purpose
            if sl.get("role") and sl["role"] not in set(ROLES) | {"paper"}:
                sl["purpose"] = sl.pop("role")
        entries.append((e, pp))
    if errs:
        for x in errs:
            print("FAIL", x)
        return 1
    prs = Presentation(str(SKILL / "kit" / "assets" / "base-wide.pptx"))
    out = {}
    for i, (e, pp) in enumerate(entries, 1):
        src = Presentation(str(pp)).slides[0]
        s = prs.slides.add_slide(prs.slide_layouts[0])
        copy_shapes(src, s, strip=DEVICE_STRIP)
        tag.tag(s, e["archetypes"][0], e["variant"])
        out[e["id"]] = dict(e, index=i)
    package.save(prs, DEV / "devices.pptx", title="Device library", theme=th, overwrite=True, date="2026-10-03")
    (DEV / "devices.json").write_text(json.dumps({
        "about": "The device library: native slides lifted from the references, sanitised (identity stripped, every "
                 "word replaced, colours mapped to theme roles, type floored at 8pt) and fitted to the house rules. "
                 "Place one with deckkit.devices.place and fill every slot; a sample left behind fails P19.",
        "devices": out}, indent=1) + "\n")
    lines = ["# Device library", "", "Native slides lifted from the references, sanitised and theme-mapped (rulings 3 and 14). "
             "Place one with `deckkit.devices.place(prs, id, {slot: value}, theme=th)` and fill every slot. Renders: "
             "`devices/renders/<id>-sigmoid.png` and `-neutral.png`.", "",
             "| Id | Device | Archetypes | Variant | Slots | How it argues |", "|---|---|---|---|---|---|"]
    for eid, e in out.items():
        lines.append("| %s | %s | %s | %s | %d | %s |" % (eid, e["name"], ", ".join(e["archetypes"]), e["variant"],
                                                         len(e["slots"]), e["mechanism"].replace("|", "/")))
    (SKILL / "references" / "device-library.md").write_text("\n".join(lines) + "\n")
    print("OK %d devices -> %s" % (len(out), DEV / "devices.pptx"))
    r = subprocess.run([PY, str(SKILL / "gates" / "run_all.py"), "--deck", str(DEV / "devices.pptx"), "--only", GATES],
                       capture_output=True, text=True)
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-400:])
    rc = r.returncode
    if not a.no_render:
        rd = DEV / "renders"
        rd.mkdir(exist_ok=True)
        for name in ("sigmoid", "neutral"):
            with tempfile.TemporaryDirectory() as tmp:
                deck = Path(tmp) / ("devices-%s.pptx" % name)
                shutil.copy2(DEV / "devices.pptx", deck)
                if name != "sigmoid":
                    apply_theme(str(deck), Theme.load(SKILL / "themes" / ("%s.json" % name)), str(deck))
                subprocess.run([PY, str(SKILL / "scripts" / "render.py"), str(deck), "--out", str(Path(tmp) / "r")],
                               check=True, capture_output=True)
                for j, (eid, _e) in enumerate(out.items(), 1):
                    src = Path(tmp) / "r" / ("slide-%0*d.png" % (len(str(len(out))), j))
                    if not src.is_file():
                        src = Path(tmp) / "r" / ("slide-%d.png" % j)
                    shutil.copy2(src, rd / ("%s-%s.png" % (eid, name)))
        print("rendered %d devices under sigmoid and neutral -> %s" % (len(out), rd))
    return rc


if __name__ == "__main__":
    sys.exit(main())
