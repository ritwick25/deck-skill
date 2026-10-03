"""Client brand intake (ruling 23): make a contrast-solved client theme, and copy the client logo beside it.

    $PY scripts/brand.py --name "Client" --primary "#0B6E4F" [--secondary "#F2A900"] [--accent HEX ...]
                         [--logo logo.svg] [--font "Montserrat"] [--out ./brand]
    $PY scripts/brand.py --name "Client" --from-url https://client.example [--out ./brand]
        reads the site's CSS and prints the candidate brand colours with their counts; nothing is picked.
        Rerun with --from-url and --primary (and --secondary) once the user has confirmed, and the theme records
        the URL and the date the CSS was read.

Writes <out>/theme.json (the sigmoid.json schema: client primary in accent1, dk2 and lt2 derived, series from the
secondaries, identity and vendors copied from the house theme, accent-ink solved to 4.5:1, on-accent picked) and
<out>/logo.svg|png with its sha256 in the theme's "brand" block. A theme that fails `theme check` is refused with
the reason and nothing is written. A font the kit cannot measure, or one not installed, falls back to Arial.

Exit codes: 0 theme written, 1 refused, 2 bad input, 3 candidates printed and waiting for the user's choice.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "kit"))

from deckkit import brand  # noqa: E402
from deckkit.errors import DeckkitError  # noqa: E402


def _print_candidates(url, fetched, read, cands):
    print("brand colours in %s (CSS read %s, %d source(s)):" % (url, fetched, len(read)))
    if not cands:
        print("  no non-neutral colour found; ask the user for the hexes")
        return
    print("  %-3s %-8s %6s %8s  %s" % ("#", "hex", "count", "on white", "custom properties"))
    for i, c in enumerate(cands, 1):
        print("  %-3d #%-7s %6d %7.2f:1  %s" % (i, c["hex"], c["count"], c["on_white"], ", ".join(c["properties"])))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="brand.py", description="Make a client theme and logo record for a deck.")
    ap.add_argument("--name", required=True, help="the client's name as it reads (alt text, theme id)")
    ap.add_argument("--primary", help="the brand's primary hex; goes into accent1")
    ap.add_argument("--secondary", help="the brand's secondary hex; series-1")
    ap.add_argument("--accent", nargs="+", default=[], help="further brand hexes; series-2 onward (at most 4)")
    ap.add_argument("--from-url", dest="url", help="read candidate colours from the client's production CSS")
    ap.add_argument("--logo", help="the client logo, .svg (preferred) or .png")
    ap.add_argument("--font", help="the brand font; Arial when the kit cannot measure it or it is not installed")
    ap.add_argument("--out", default="brand", help="output folder (default ./brand)")
    ap.add_argument("--date", help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    out = Path(a.out).expanduser()
    date = a.date or _dt.date.today().isoformat()

    verified = None
    if a.url:
        try:
            texts, read = brand.fetch_css(a.url)
        except Exception as e:                                         # noqa: BLE001
            print("brand: could not read %s: %s" % (a.url, e), file=sys.stderr)
            return 2
        cands = brand.css_candidates(texts)
        out.mkdir(parents=True, exist_ok=True)
        cfile = out / "brand-candidates.json"
        cfile.write_text(json.dumps({"url": a.url, "fetched": date, "sources": read, "candidates": cands},
                                    indent=1) + "\n", encoding="utf-8")
        _print_candidates(a.url, date, read, cands)
        print("  written %s" % cfile)
        if not a.primary:
            print("\nconfirm the brand colours with the user, then rerun with --from-url %s --primary HEX "
                  "[--secondary HEX]" % a.url)
            return 3
        verified = {"url": a.url, "fetched": date, "candidates_file": cfile.name}
        try:
            p = brand.norm_hex(a.primary, "primary")
        except DeckkitError as e:
            print("brand refused: %s" % e, file=sys.stderr)
            return 2
        if p not in {c["hex"] for c in cands}:
            verified["note"] = "primary %s is not among the colours read from the CSS" % p
            print("note: %s; it is recorded as the user's choice" % verified["note"])
    if not a.primary:
        print("brand: --primary HEX is required (or --from-url URL to list the candidates first)", file=sys.stderr)
        return 2

    logo = None
    try:
        data, notes = brand.make_theme(a.name, a.primary, a.secondary, a.accent, font=a.font, verified=verified,
                                       date=date)
        if a.logo:
            logo = brand.copy_logo(a.logo, out)
            logo["alt"] = "%s logo" % data["brand"]["client"]
            data["brand"]["logo"] = logo
    except DeckkitError as e:
        print("brand refused: %s" % e, file=sys.stderr)
        return 1
    out.mkdir(parents=True, exist_ok=True)
    tpath = out / "theme.json"
    tpath.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    text, rc = brand.check_text(json.loads(tpath.read_text(encoding="utf-8")), str(tpath))   # the file as written
    print(text)
    if rc != 0:
        tpath.unlink()
        print("brand refused: the written theme failed theme check; removed %s" % tpath, file=sys.stderr)
        return 1
    print("")
    for n in notes:
        print("note: %s" % n)
    if logo:
        print("logo: %s  sha256 %s" % (out / logo["file"], logo["sha256"][:12]))
    print("theme: %s  (deck.json \"theme\": \"%s\", or --theme %s)" % ((tpath.resolve(),) * 3))
    return 0


if __name__ == "__main__":
    sys.exit(main())
