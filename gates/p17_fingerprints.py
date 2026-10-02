"""P17 fingerprints: no banned glyph, word, phrase, structural tell, jargon or deck-voice pattern on glass.

The patterns are loaded in-process from the one home, ~/.claude/hooks/fingerprints.json, never copied:
tiers glyph, phrase, structural, word-core, word-strong, word-sales (minus sal-harness, a SharePoint-only
ban), jargon, and the opt-in deck-voice tier (first and second person, "Al" typed for "AI", placeholders,
semicolons). Before any slide is read, a canary sentence must produce at least two hits: an empty or
unreadable rules file makes the gate FAIL rather than read as clean. Quotations and the exact phrase
"Thank you" are exempt from dv-person. dv-semicolon is advisory and counted. Text is every text block on
every slide (group children, cells, master and layout chrome) plus every alt text.
"""
from __future__ import annotations

import json
import re
import sys

from _shared import ADVISORY, FAIL, NOTE, Finding, InputMissing, cli, text_of

GATE, TITLE = "P17", "fingerprints"
TIERS = ("glyph", "phrase", "structural", "word-core", "word-strong", "word-sales", "jargon", "deck-voice")
EXCLUDE = {"sal-harness"}
ADVISORY_IDS = {"dv-semicolon"}
CANARY = "We leverage it " + chr(0x2014) + " a seamless start."
MIN_CANARY = 2
QUOTES = ('"', chr(0x201C), chr(0x2018), "'")


def load_rules(path):
    try:
        with open(path, encoding="utf-8") as fh:
            d = json.loads(fh.read() or "{}")
    except FileNotFoundError:
        raise InputMissing("fingerprints file not found: %s" % path) from None
    except ValueError as e:
        raise InputMissing("fingerprints file is not JSON (%s): %s" % (e, path)) from None
    rules, broken = [], []
    for r in d.get("rules", []) if isinstance(d, dict) else []:
        if r.get("tier") not in TIERS or r.get("id") in EXCLUDE:
            continue
        try:
            rules.append((r["id"], r["tier"], re.compile(r["pattern"])))
        except (re.error, KeyError):
            broken.append(r.get("id", "?"))
    return rules, broken


def blocks(ctx, i):
    """(where, text, is_quote) for every text block and alt text on slide i."""
    s = ctx.slide(i)
    out = []
    for L in s["shapes"] + s["chrome"]:
        t = text_of(L)
        if t.strip():
            q = (L.get("role_guess") or {}).get("role") == "quote" or t.lstrip().startswith(QUOTES)
            out.append((L["name"] or "id %s" % L["id"], t, q))
    for c in ctx.slide_root(i).iter("{*}cNvPr"):
        for a in ("descr", "title"):
            if (c.get(a) or "").strip():
                out.append(("%s alt" % (c.get("name") or c.get("id")), c.get(a), False))
    return out


def run(deck, ctx):
    rules, broken = load_rules(ctx.fingerprints)
    out = [Finding(GATE, FAIL, None, "rules", "rule %s does not compile" % b) for b in broken]
    hits = [rid for rid, _t, rx in rules if rx.search(CANARY)]
    if len(hits) < MIN_CANARY:
        out.append(Finding(GATE, FAIL, None, "canary", "the canary produced %d hit(s) from %d rules in %s; a pass "
                           "cannot be trusted" % (len(hits), len(rules), ctx.fingerprints)))
        return out
    semis = 0
    for i in range(1, ctx.n + 1):
        for where, t, is_quote in blocks(ctx, i):
            for rid, tier, rx in rules:
                txt = t.replace("Thank you", "") if rid == "dv-person" else t
                if rid == "dv-person" and is_quote:
                    continue
                for m in rx.finditer(txt):
                    if rid in ADVISORY_IDS:
                        semis += 1
                        continue
                    ctxt = txt[max(0, m.start() - 25): m.end() + 25].replace("\n", " ")
                    out.append(Finding(GATE, FAIL, i, where, "[%s] %r in ...%s..." % (rid, m.group(0), ctxt)))
                    break
    if semis:
        out.append(Finding(GATE, ADVISORY, None, "dv-semicolon", "%d semicolon(s) on glass; adjudicate each in DESIGN.md"
                           % semis))
    out.append(Finding(GATE, NOTE, None, "rules", "%d rules from %s; canary hit %s" % (len(rules), ctx.fingerprints,
                                                                                      ", ".join(hits))))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
