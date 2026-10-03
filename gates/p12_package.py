"""P12 package: no PowerPoint repair trap. deckkit.package.structural_check plus the referenced XSD validator.

Structural: once-only duplicates (a doubled effectLst), every r:* resolving, relationship targets present,
content types (svg included), unique cNvPr ids, glue ids, sldId ranges, control characters, negative
extents, a python-pptx reopen. Then the ISO 29500 validator, referenced in place and never copied, plus the
slide-level pml.xsd pass, over the parts whose root namespace the validator's schema bundle covers: PowerPoint's
own extension parts (authors.xml, revisionInfo.xml, changesInfos/, modern comments) have no schema there and are
printed as SKIPPED notes, never failed or passed silently. buSzPct written in PowerPoint's transitional integer
form (100000 for 100%) is a known PowerPoint value, printed as a note. Glue to a missing shape id stays a defect.
A validator that cannot be found or cannot run is a FAIL, never a pass.
"""
from __future__ import annotations

import sys

from _shared import FAIL, NOTE, Finding, cli
from deckkit import package
from deckkit.errors import ValidatorMissing

GATE, TITLE = "P12", "package"


def run(deck, ctx):
    out = [Finding(GATE, FAIL, None, d.split(":", 1)[0], d.split(":", 1)[1].strip() if ":" in d else d)
           for d in package.structural_check(str(ctx.deck_path))]
    report: dict = {}
    try:
        ok, detail = package.validate_xsd(str(ctx.deck_path), report)
    except ValidatorMissing as e:
        out.append(Finding(GATE, FAIL, None, "xsd", "validator unavailable, so the package is unvalidated: %s" % e))
        return out
    for part, ns in report.get("skipped", []):
        out.append(Finding(GATE, NOTE, None, part, "SKIPPED: no schema in the bundle for %s" % (ns or "(no namespace)")))
    known = report.get("known", [])
    if known:
        out.append(Finding(GATE, NOTE, None, "xsd", "%d known PowerPoint value(s), not errors: %s"
                           % (len(known), "; ".join(sorted(set(k.split(": ", 1)[-1] for k in known)))[:200])))
    if not ok:
        for line in [ln for ln in detail.splitlines() if ln.strip()][:12]:
            out.append(Finding(GATE, FAIL, None, "xsd", line.strip()[:300]))
    return out


if __name__ == "__main__":
    sys.exit(cli(sys.modules[__name__]))
