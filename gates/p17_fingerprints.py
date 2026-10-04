"""P17 fingerprints: no banned glyph, word, phrase, structural tell, jargon or deck-voice pattern on glass.

The patterns are loaded in-process from the one home, ~/.claude/hooks/fingerprints.json; on a machine without it, from
the byte-identical copy bundled in kit/assets, which selftest holds equal to the home file wherever that file exists:
tiers glyph, phrase, structural, word-core, word-strong, word-sales (minus sal-harness, a SharePoint-only
ban), jargon, and the opt-in deck-voice tier (first and second person, "Al" typed for "AI", placeholders,
semicolons). Before any slide is read the canary fires: one sentence per dependency (every tier above, and the
deck-voice rules dv-person, dv-al-ai and dv-placeholder by id) must be hit by at least one loaded rule of that
tier or id. A tier missing from the file, emptied, renamed or broken leaves its sentence unhit and the gate FAILS
naming it; an empty or unreadable rules file fails the same way, so it can never read as clean. Quotations and
the exact phrase "Thank you" are exempt from dv-person. dv-semicolon is advisory and counted. Text is every
text block on every slide (group children, cells, master and layout chrome) plus every alt text. URLs are blanked
before any rule reads the text (strip_urls: http and https links, www. hosts and bare domain paths such as
example.com/blogs/unlocking-x), so a word in a source link's slug is never prose on glass.
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
# one sentence per dependency: (tier, rule id or None for any rule of the tier, sentence). chr() keeps the
# banned glyph out of this source.
# The banned words and phrases are joined from pieces split mid-word, so this source never carries one whole
# (the fingerprint hook scans it).
CANARY = (
    ("glyph", None, "One store " + chr(0x2014) + " one owner."),
    ("word-core", None, "Teams " + "lever" + "age the store."),
    ("word-strong", None, "A " + "holi" + "stic review."),
    ("word-sales", None, "Real " + "syn" + "ergy across regions."),
    ("phrase", None, "It's n" + "ot just a store, it's the plan."),
    ("structural", None, "Thi" + "s slide shows the plan."),
    ("jargon", None, "The wow mo" + "ment arrives early."),
    ("deck-voice", "dv-person", "We read the store."),
    ("deck-voice", "dv-al-ai", "Al tools read it."),
    ("deck-voice", "dv-placeholder", "Owner: {{slot:owner}}"),
    ("deck-voice", "dv-maturity", "Run the live demo next week."),
)
QUOTES = ('"', chr(0x201C), chr(0x2018), "'")
URL = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>\"']+"
                 r"|\b[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*\.[a-z]{2,24}/[^\s<>\"']*")


def strip_urls(text: str) -> str:
    """The text with every URL blanked to spaces of the same length (offsets kept): http(s) links, www. hosts and
    bare domain paths (a domain followed by a slash)."""
    return URL.sub(lambda m: " " * len(m.group(0)), text)


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


def canary(rules):
    """(hit rule ids, [(tier, id) of every dependency no loaded rule caught])."""
    hits, missing = [], []
    for tier, want, sentence in CANARY:
        got = [rid for rid, t, rx in rules if t == tier and (want is None or rid == want) and rx.search(sentence)]
        if got:
            hits.extend(g for g in got if g not in hits)
        else:
            missing.append((tier, want))
    return hits, missing


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
    hits, missing = canary(rules)
    for tier, rid in missing:
        n = sum(1 for _r, t, _x in rules if t == tier)
        out.append(Finding(GATE, FAIL, None, "canary", "the canary for %s produced no hit (%d %s rule(s) loaded from %s); "
                           "a pass cannot be trusted" % (rid or "tier " + tier, n, tier, ctx.fingerprints)))
    if missing:
        return out
    semis = 0
    maturity_ok = ctx.overridden("P17:dv-maturity")     # a deck quoting the client's own "alpha" grants it, with a source
    for i in range(1, ctx.n + 1):
        for where, t, is_quote in blocks(ctx, i):
            t = strip_urls(t)
            for rid, tier, rx in rules:
                txt = t.replace("Thank you", "") if rid == "dv-person" else t
                if rid == "dv-person" and is_quote:
                    continue
                if rid == "dv-maturity" and maturity_ok:
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
