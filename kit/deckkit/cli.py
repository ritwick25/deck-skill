"""Command line: python -m deckkit SUBCOMMAND (run with kit/ on sys.path or PYTHONPATH).

    theme check THEME.json      contrast table, derived roles, colour-vision report; exit 1 on a failing pair
    theme solve THEME.json ROLE AGAINST [AGAINST ...] [--min 4.5]
                                lower ROLE's lumMod until it clears the minimum; prints the expression
    theme apply THEME.json DECK.pptx [--out OUT.pptx] [--from-theme BUILT_UNDER.json]
                                swap clrScheme, fontScheme and fmtScheme in every theme part

Exit codes: 0 pass, 1 a gated failure, 2 bad input (a missing file or a refused theme counts as failure).
"""
from __future__ import annotations

import argparse
import sys

from .errors import DeckkitError


def _theme(args) -> int:
    from .theme import Theme, apply_theme
    try:
        t = Theme.load(args.theme)
    except FileNotFoundError as e:
        print("theme: %s" % e, file=sys.stderr)
        return 2
    except (DeckkitError, ValueError) as e:
        print("theme refused: %s" % e, file=sys.stderr)
        return 2
    if args.action == "check":
        text, rc = t.report()
        print(text)
        return rc
    if args.action == "solve":
        try:
            expr, ratio = t.solve(args.role, args.against, args.min)
        except DeckkitError as e:
            print("solve refused: %s" % e, file=sys.stderr)
            return 1
        print("%s = %s  (worst %.2f against %s, min %.1f)" % (args.role, expr, ratio, ", ".join(args.against), args.min))
        return 0
    if args.action == "apply":
        src = None
        if getattr(args, "from_theme", None):
            from .theme import Theme as _T
            src = _T.load(args.from_theme)
        parts = apply_theme(args.deck, t, args.out, from_theme=src)
        print("%s: %d theme part(s) set to %s: %s" % (args.out or args.deck, len(parts), t.name, ", ".join(parts)))
        return 0
    return 2


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="deckkit")
    sub = ap.add_subparsers(dest="cmd", required=True)
    th = sub.add_parser("theme", help="check, solve or apply a theme")
    tsub = th.add_subparsers(dest="action", required=True)
    c = tsub.add_parser("check")
    c.add_argument("theme")
    s = tsub.add_parser("solve")
    s.add_argument("theme")
    s.add_argument("role")
    s.add_argument("against", nargs="+")
    s.add_argument("--min", type=float, default=4.5)
    a = tsub.add_parser("apply")
    a.add_argument("theme")
    a.add_argument("deck")
    a.add_argument("--out")
    a.add_argument("--from-theme", dest="from_theme", help="the theme the deck was built under: remaps its solved roles")
    args = ap.parse_args(argv)
    if args.cmd == "theme":
        return _theme(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
