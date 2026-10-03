"""Build kit/assets/vendor_hashes.json: the sha256 of every vendor mark the kit can embed, per key and pixel size.

    $PY scripts/build_vendor_hashes.py [--check]

deckkit.icons.vendor() embeds the diagrams resource PNG for a key byte for byte, so the expected blob for
'aws/compute/ec2' is that file's sha256 at that file's pixel size. Gate P22 compares every vendor.* picture's
blob against this table, so a picture renamed and re-captioned as a vendor mark (any other image under the
same name and alt text) fails. The table is keyed by size so a mark embedded at another rasterised size can
be recorded beside it without changing the gate.

--check rebuilds in memory and exits 1 when the file on disk differs (a diagrams upgrade, a stale table).
Deterministic: same resources, same bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "kit"))

from deckkit import icons  # noqa: E402


def _version() -> str:
    try:
        from importlib.metadata import version
        return version("diagrams")
    except Exception:
        return "unknown"


def build() -> bytes:
    from PIL import Image
    root = icons._resources()
    keys = {}
    for key in icons.vendor_keys():
        blob = (root / (key + ".png")).read_bytes()
        with Image.open(io.BytesIO(blob)) as im:
            w, h = im.size
        keys[key] = {"%dx%d" % (w, h): hashlib.sha256(blob).hexdigest()}
    doc = {"source": "diagrams", "version": _version(), "count": len(keys),
           "note": "sha256 of the resource PNG deckkit.icons.vendor embeds, per key and pixel size; "
                   "rebuilt by scripts/build_vendor_hashes.py",
           "keys": keys}
    return (json.dumps(doc, indent=1, sort_keys=True) + "\n").encode("utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="exit 1 when the table on disk is stale")
    a = ap.parse_args(argv)
    data = build()
    if a.check:
        same = icons.VENDOR_HASHES.is_file() and icons.VENDOR_HASHES.read_bytes() == data
        print("vendor_hashes.json %s (%d keys)" % ("current" if same else "STALE", json.loads(data)["count"]))
        return 0 if same else 1
    icons.VENDOR_HASHES.write_bytes(data)
    print("wrote %s (%d keys, %d bytes)" % (icons.VENDOR_HASHES, json.loads(data)["count"], len(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
