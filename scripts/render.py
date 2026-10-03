"""Render a deck to one PNG per slide, hidden slides included, then print the paths to read.

    $PY scripts/render.py deck.pptx [--out DIR] [--dpi 110] [--sheet]

LibreOffice headless (an isolated profile, so a running instance does not swallow the job) to PDF, poppler to
PNG. The page count must equal the slide count or the render FAILS: a skipped hidden slide is a slide nobody
read. --sheet also writes contact.png, every slide in a grid, for a first look; the per-slide PNGs are still
what "read every slide" means. Renders land in <deck folder>/render/<deck stem>/ by default, never beside
the source deck's own files.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from pptx import Presentation


def render(pptx: Path, out: Path, dpi: int = 110) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("slide-*.png"):
        old.unlink()
    n = len(Presentation(str(pptx)).slides)
    with tempfile.TemporaryDirectory(prefix="deck-render-") as tmp:
        tmp = Path(tmp)
        src = tmp / pptx.name                     # a copy, so no lock file lands beside the deck
        shutil.copy2(pptx, src)
        prof = (tmp / "profile").as_uri()
        flt = 'pdf:impress_pdf_Export:{"ExportHiddenSlides":{"type":"boolean","value":"true"}}'
        subprocess.run(["soffice", "-env:UserInstallation=" + prof, "--headless", "--convert-to", flt,
                        "--outdir", str(tmp), str(src)], check=True, timeout=300, capture_output=True)
        pdf = src.with_suffix(".pdf")
        if not pdf.exists():
            raise SystemExit("FAIL no PDF from LibreOffice for %s" % pptx)
        pages = int(next(L.split()[-1] for L in subprocess.run(["pdfinfo", str(pdf)], capture_output=True,
                                                                 text=True, check=True).stdout.splitlines()
                         if L.startswith("Pages:")))
        if pages != n:
            raise SystemExit("FAIL %d slides, %d pages: a slide was skipped" % (n, pages))
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(out / "slide")], check=True, timeout=300)
    return sorted(out.glob("slide-*.png"))


def sheet(pngs: list[Path], dst: Path, cols: int = 4, w: int = 480) -> None:
    from PIL import Image, ImageDraw
    ims = [Image.open(p) for p in pngs]
    h = int(w * ims[0].height / ims[0].width)
    rows = (len(ims) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * (w + 12) + 12, rows * (h + 30) + 12), "white")
    d = ImageDraw.Draw(canvas)
    for i, im in enumerate(ims):
        x, y = 12 + (i % cols) * (w + 12), 12 + (i // cols) * (h + 30)
        canvas.paste(im.convert("RGB").resize((w, h)), (x, y + 18))
        d.rectangle([x, y + 18, x + w - 1, y + 18 + h - 1], outline="#BFBFBF")
        d.text((x, y + 2), str(i + 1), fill="black")
    canvas.save(dst)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("deck")
    ap.add_argument("--out")
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--sheet", action="store_true")
    a = ap.parse_args()
    deck = Path(a.deck).resolve()
    out = Path(a.out) if a.out else deck.parent / "render" / deck.stem
    pngs = render(deck, out, a.dpi)
    for p in pngs:
        print(p)
    if a.sheet:
        sheet(pngs, out / "contact.png")
        print(out / "contact.png")
    print("OK %d slides rendered; now read every one" % len(pngs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
