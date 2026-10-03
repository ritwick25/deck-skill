"""DL31: a bounded platform core between a sources column and a consumers column, with an access band across its
top, data pipeline lanes and an agent runtime inside, and a shared platform band beneath (solution-architecture)."""
import argparse
import copy
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from devwork import *  # noqa: E402,F403
from deckkit import prims, text as txt  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out")
a = ap.parse_args()

prs, s, th = open_lifted("DL31")
VARIANT = "bounded-core-side-columns"
R, P = txt.Run, txt.Para


def two(head, body, hs=10, bs=9, align="left", hrole="ink-deep", brole="ink-muted"):
    return [P((R(head, hrole, bold=True, size=hs),), align=align),
            P((R(body, brole, size=bs),), align=align, space_before=1)]


def tall(name, h=0.19):
    sh = find(s, name)
    sh.height = int(h * EMU)


def radius(name, r=0.05):
    sh = find(s, name)
    gd = sh._element.find(".//" + qn("a:prstGeom") + "/" + qn("a:avLst") + "/" + qn("a:gd"))
    gd.set("fmla", "val %d" % round(r / min(sh.width, sh.height) * EMU * 100000))


def one(word, size=10, align="left", role="ink-deep", bold=True):
    return [P((R(word, role, bold=bold, size=size),), align=align)]


_ids = [0]


def clone(src, new, dy):
    """Copy a shape below itself by dy inches, with a fresh id and name."""
    el = find(s, src)._element
    dup = copy.deepcopy(el)
    _ids[0] = max(int(e.get("id")) for e in s.shapes._spTree.iter() if e.tag == qn("p:cNvPr"))
    c = dup.find(".//" + qn("p:cNvPr"))
    c.set("id", str(_ids[0] + 1))
    c.set("name", new)
    el.getparent().append(dup)
    sh = find(s, new)
    sh.top = int(sh.top + dy * EMU)


# banned chrome: the subtitle sentence, the arrow captions that cannot fit their gaps at the floor
for n in ("dev.4", "dev.71", "dev.73", "dev.75", "dev.86", "dev.88", "dev.90", "dev.132", "dev.134", "dev.136"):
    delete(s, n)
# decorative accent rules under each zone tab: the tab itself takes a flat card fill instead
for n in ("dev.7", "dev.30", "dev.57", "dev.60", "dev.114"):
    delete(s, n)

rename(s, "dev.2", "struct.page")
rename(s, "dev.3", "slot.title")
move(s, "slot.title", 0.13, 0.10, 13.07, 0.50)
text(s, "slot.title", [P(tuple(txt.title_runs(
    "One governed platform serves every agent from shared, certified data",
    ("One governed platform",))))], th, size=20, bold=True, anchor="middle")

# zone frames and their tabs
ZONES = [("dev.5", "dev.6", "sources", "Sources", 12), ("dev.28", "dev.29", "consumers", "Consumers", 12),
         ("dev.55", "dev.56", "pipelines", "Data pipelines", 12), ("dev.58", "dev.59", "runtime", "Agent runtime", 12),
         ("dev.112", "dev.113", "platform", "Shared platform and governance", 12)]
for frame, tab, part, label, ts in ZONES:
    rename(s, frame, "struct.%s.frame" % part)
    rename(s, tab, "slot.%s.tab" % part)
    prims.set_fill(find(s, "slot.%s.tab" % part), "card", theme=th)
    text(s, "slot.%s.tab" % part, one(label, size=ts), th, size=ts, background="card", anchor="middle")

for fr in ("struct.pipelines.frame", "struct.runtime.frame"):
    move(s, fr, find(s, fr).left / EMU, 1.89, find(s, fr).width / EMU, 4.16)

# access band across the top of the core
rename(s, "dev.45", "struct.access.frame")
rename(s, "dev.46", "slot.access.tab")
text(s, "slot.access.tab", one("Access layer", size=12, role="paper"), th,
     size=12, background="ink-deep", anchor="middle")
ACCESS = [("dev.47", "dev.48", "Agent gateway", "Routes every request", "network"),
          ("dev.49", "dev.50", "Identity", "Single sign-on, roles", "key-round"),
          ("dev.51", "dev.52", "Orchestrator", "Plans multi-step tasks", "workflow"),
          ("dev.53", "dev.54", "Guardrails", "Checks every output", "shield-check")]
for i, (card, body, head, line, g) in enumerate(ACCESS, 1):
    rename(s, card, "struct.access.%d.card" % i)
    rename(s, body, "slot.access.%d.text" % i)
    cx = find(s, "struct.access.%d.card" % i).left / EMU
    icon(s, "slot.access.%d.icon" % i, g, cx + 0.10, 1.14, 0.48, th)
    text(s, "slot.access.%d.text" % i, two(head, line, hs=11, bs=10), th, size=11, anchor="middle")

# sources column: three groups of systems, each closing on a +N more chip
SRC = [("dev.8", "Operational", [("dev.9", "dev.10", "ERP ledger", "database"), ("dev.11", "dev.12", "CRM", "contact"),
                                 ("dev.13", "dev.14", "Orders", "shopping-cart")], "dev.15", "+4 more"),
       ("dev.16", "Documents", [("dev.17", "dev.18", "Contracts", "file-text"),
                                ("dev.19", "dev.20", "Tickets", "message-square")], "dev.21", "+2 more"),
       ("dev.22", "External feeds", [("dev.23", "dev.24", "Market prices", "trending-up"),
                                     ("dev.25", "dev.26", "Partner files", "folder")], "dev.27", "+3 more")]
k = 0
for g, (lab, glabel, items, more, mtext) in enumerate(SRC, 1):
    rename(s, lab, "slot.sources.group.%d" % g)
    tall("slot.sources.group.%d" % g)
    text(s, "slot.sources.group.%d" % g, one(glabel, size=10, role="ink-muted"), th, size=10, anchor="middle")
    y0 = find(s, items[0][0]).top / EMU
    for m, (card, body, word, gl) in enumerate(items):
        k += 1
        rename(s, card, "struct.source.%d.card" % k)
        rename(s, body, "slot.source.%d.label" % k)
        if g > 1:
            move(s, "struct.source.%d.card" % k, 0.21, y0 + m * 0.625, 1.44, 0.54)
            move(s, "slot.source.%d.label" % k, 0.55, y0 + m * 0.625, 1.05, 0.54)
        c = find(s, "struct.source.%d.card" % k)
        side = 0.24
        icon(s, "slot.source.%d.icon" % k, gl, 0.27, c.top / EMU + (c.height / EMU - side) / 2, side, th)
        text(s, "slot.source.%d.label" % k, one(word, size=10), th, size=10, anchor="middle")
    rename(s, more, "slot.sources.more.%d" % g)
    if g > 1:
        move(s, "slot.sources.more.%d" % g, 0.21, y0 + 2 * 0.625, 1.44, 0.54)
    text(s, "slot.sources.more.%d" % g, one(mtext, size=9, role="ink-muted", bold=False), th, size=9,
         anchor="middle")

# consumers column: two lifted groups and a third cloned from the second, re-laid to fill the column
clone("dev.38", "dev.G3", 0)
for j, (cn, tn) in enumerate((("dev.39", "dev.40"), ("dev.41", "dev.42")), 1):
    clone(cn, "dev.G3c%d" % j, 0)
    clone(tn, "dev.G3t%d" % j, 0)
CON = [("dev.31", "Channels", [("dev.32", "dev.33", "Sales", "CRM copilot", "briefcase"),
                               ("dev.34", "dev.35", "Service", "Case replies", "headphones"),
                               ("dev.36", "dev.37", "Finance", "Close checks", "calculator")]),
       ("dev.38", "Integrations", [("dev.39", "dev.40", "APIs", "Partner apps", "plug"),
                                   ("dev.41", "dev.42", "Reports", "BI views", "chart-column"),
                                   ("dev.43", "dev.44", "Alerts", "Team chat", "bell")]),
       ("dev.G3", "People", [("dev.G3c1", "dev.G3t1", "Analysts", "Self-serve", "users"),
                             ("dev.G3c2", "dev.G3t2", "Leads", "Final sign-off", "user-check")])]
k, y = 0, 1.10
CCH, CGAP = 0.60, 0.08
for g, (lab, glabel, items) in enumerate(CON, 1):
    rename(s, lab, "slot.consumers.group.%d" % g)
    move(s, "slot.consumers.group.%d" % g, 11.71, y, 1.39, 0.19)
    text(s, "slot.consumers.group.%d" % g, one(glabel, size=10, role="ink-muted"), th, size=10, anchor="middle")
    y += 0.21
    for card, body, head, line, gl in items:
        k += 1
        rename(s, card, "struct.consumer.%d.card" % k)
        rename(s, body, "slot.consumer.%d.text" % k)
        move(s, "struct.consumer.%d.card" % k, 11.71, y, 1.39, CCH)
        icon(s, "slot.consumer.%d.icon" % k, gl, 11.79, y + (CCH - 0.32) / 2, 0.32, th)
        move(s, "slot.consumer.%d.text" % k, 12.13, y, 0.95, CCH)
        text(s, "slot.consumer.%d.text" % k, two(head, line, hs=10, bs=9), th, size=10, anchor="middle")
        y += CCH + CGAP
    y += 0.05

# pipeline lanes: two lifted lanes re-spaced, a third cloned from the second
CW, CH = 0.97, 0.94
XS = [1.95, 3.02, 4.09, 5.16]
LANE_Y = [2.29, 3.54, 4.79]
clone("dev.76", "dev.L3", LANE_Y[2] - 3.52)
for j, n in enumerate(("dev.77", "dev.79", "dev.81", "dev.83")):
    clone(n, "dev.L3c%d" % j, 0)
for j, n in enumerate(("dev.78", "dev.80", "dev.82", "dev.84")):
    clone(n, "dev.L3t%d" % j, 0)
for j, n in enumerate(("dev.85", "dev.87", "dev.89")):
    clone(n, "dev.L3a%d" % j, 0)
LANES = [("dev.61", "Batch ingest", ("dev.62", "dev.64", "dev.66", "dev.68"), ("dev.63", "dev.65", "dev.67", "dev.69"),
          ("dev.70", "dev.72", "dev.74"),
          [("Extract", "Nightly loads", "cloud-download"), ("Validate", "Rules and tests", "list-checks"),
           ("Model", "Shared tables", "table"), ("Publish", "Certified sets", "package-check")]),
         ("dev.76", "Streaming", ("dev.77", "dev.79", "dev.81", "dev.83"), ("dev.78", "dev.80", "dev.82", "dev.84"),
          ("dev.85", "dev.87", "dev.89"),
          [("Capture", "Change events", "activity"), ("Enrich", "Join reference", "merge"),
           ("Score", "Live features", "gauge"), ("Land", "Hot store", "hard-drive")]),
         ("dev.L3", "Document intake", ("dev.L3c0", "dev.L3c1", "dev.L3c2", "dev.L3c3"),
          ("dev.L3t0", "dev.L3t1", "dev.L3t2", "dev.L3t3"), ("dev.L3a0", "dev.L3a1", "dev.L3a2"),
          [("Parse", "Text and tables", "file-search"), ("Chunk", "By section", "split"),
           ("Embed", "Vector per chunk", "brain-circuit"), ("Index", "Search ready", "database-search")])]
for ln, (lab, glabel, cards, texts, arrows, steps) in enumerate(LANES, 1):
    ly = LANE_Y[ln - 1]
    rename(s, lab, "slot.lane.%d.label" % ln)
    move(s, "slot.lane.%d.label" % ln, 1.95, ly, 4.18, 0.19)
    text(s, "slot.lane.%d.label" % ln, one(glabel, size=10, role="ink-muted"), th, size=10, anchor="middle")
    cy = ly + 0.21
    for j, (card, body, (head, line, gl)) in enumerate(zip(cards, texts, steps), 1):
        cn, tn = "struct.lane.%d.step.%d.card" % (ln, j), "slot.lane.%d.step.%d.text" % (ln, j)
        rename(s, card, cn)
        rename(s, body, tn)
        move(s, cn, XS[j - 1], cy, CW, CH)
        icon(s, "slot.lane.%d.step.%d.icon" % (ln, j), gl, XS[j - 1] + (CW - 0.34) / 2, cy + 0.07, 0.34, th)
        move(s, tn, XS[j - 1] + 0.03, cy + 0.42, CW - 0.06, 0.50)
        text(s, tn, two(head, line, hs=10, bs=9, align="center"), th, size=10, anchor="top")
    for j, arr in enumerate(arrows, 1):
        an = "struct.lane.%d.arrow.%d" % (ln, j)
        rename(s, arr, an)
        move(s, an, XS[j - 1] + CW - 0.01, cy + CH / 2, XS[j] - XS[j - 1] - CW + 0.02, 0)

# agent runtime: model access, shared services, tools
rename(s, "dev.91", "slot.models.label")
tall("slot.models.label")
text(s, "slot.models.label", one("Model access", size=10, role="ink-muted"), th, size=10, anchor="middle")
rename(s, "dev.92", "struct.models.card")
rename(s, "dev.93", "slot.models.text")
icon(s, "slot.models.icon", "cpu", 6.53, 2.56, 0.40, th)
text(s, "slot.models.text", two("Model router", "Every call logged", hs=11,
                                bs=10), th, size=11, anchor="middle")

rename(s, "dev.94", "slot.services.label")
tall("slot.services.label")
text(s, "slot.services.label", one("Shared services", size=10, role="ink-muted"), th, size=10, anchor="middle")
SVC = [("dev.95", "dev.96", "Memory", "Session context", "brain"),
       ("dev.97", "dev.98", "Retrieval", "Indexed documents", "search"),
       ("dev.99", "dev.100", "Evaluation", "Scores each answer", "chart-line")]
for i, (card, body, head, line, gl) in enumerate(SVC, 1):
    rename(s, card, "struct.service.%d.card" % i)
    rename(s, body, "slot.service.%d.text" % i)
    c = find(s, "struct.service.%d.card" % i)
    radius("struct.service.%d.card" % i)
    icon(s, "slot.service.%d.icon" % i, gl, c.left / EMU + 0.10, c.top / EMU + (c.height / EMU - 0.36) / 2, 0.36, th)
    move(s, "slot.service.%d.text" % i, c.left / EMU + 0.50, c.top / EMU + 0.04, c.width / EMU - 0.54,
         c.height / EMU - 0.08)
    text(s, "slot.service.%d.text" % i, two(head, line, hs=10, bs=9), th, size=10, anchor="middle")

rename(s, "dev.101", "slot.tools.label")
tall("slot.tools.label")
text(s, "slot.tools.label", one("Agent tools", size=10, role="ink-muted"), th, size=10, anchor="middle")
TOOLS = [("dev.102", "dev.103", "Search", "Catalog and files", "file-search"),
         ("dev.104", "dev.105", "Compute", "Governed metrics", "calculator"),
         ("dev.106", "dev.107", "Draft", "Replies for review", "file-text"),
         ("dev.108", "dev.109", "Escalate", "Hand off to a person", "route"),
         ("dev.110", "dev.111", "Act", "Gated writes", "check")]
TY, TH_ = 4.61, 1.38
for i, (card, body, head, line, gl) in enumerate(TOOLS, 1):
    rename(s, card, "struct.tool.%d.card" % i)
    rename(s, body, "slot.tool.%d.text" % i)
    c = find(s, "struct.tool.%d.card" % i)
    move(s, "struct.tool.%d.card" % i, c.left / EMU, TY, c.width / EMU, TH_)
    x, w = c.left / EMU, c.width / EMU
    icon(s, "slot.tool.%d.icon" % i, gl, x + (w - 0.40) / 2, TY + 0.14, 0.40, th)
    move(s, "slot.tool.%d.text" % i, x + 0.02, TY + 0.62, w - 0.04, TH_ - 0.70)
    text(s, "slot.tool.%d.text" % i, two(head, line, hs=10, bs=9, align="center"), th, size=10,
         background="card", anchor="top")

# shared platform band: its top clears the foot zone, chips centred in what is left
PB, PCH = 6.16, 0.62
move(s, "struct.platform.frame", 1.87, PB, 9.60, 7.37 - PB)
move(s, "slot.platform.tab", 1.87, PB, 9.60, 0.32)
PCY = PB + 0.32 + (7.37 - PB - 0.32 - PCH) / 2
PLAT = [("dev.115", "dev.116", "Code", "git-branch"), ("dev.117", "dev.118", "Deploy", "rocket"),
        ("dev.119", "dev.120", "Catalog", "library"), ("dev.121", "dev.122", "Lineage", "share-2"),
        ("dev.123", "dev.124", "Access", "lock"), ("dev.125", "dev.126", "Audit", "clipboard-check"),
        ("dev.127", "dev.128", "Monitor", "activity"), ("dev.129", "dev.130", "Spend", "coins")]
_ln = find(s, "dev.115")._element.find(".//" + qn("a:ln"))
for n in ("dev.127", "dev.129"):
    old_ln = find(s, n)._element.find(".//" + qn("a:ln"))
    old_ln.getparent().replace(old_ln, copy.deepcopy(_ln))
for i, (card, body, word, gl) in enumerate(PLAT, 1):
    rename(s, card, "struct.platform.%d.card" % i)
    rename(s, body, "slot.platform.%d.label" % i)
    c = find(s, "struct.platform.%d.card" % i)
    x, w = c.left / EMU, c.width / EMU
    move(s, "struct.platform.%d.card" % i, x, PCY, w, PCH)
    if gl:
        icon(s, "slot.platform.%d.icon" % i, gl, x + 0.07, PCY + (PCH - 0.30) / 2, 0.30, th)
        move(s, "slot.platform.%d.label" % i, x + 0.37, PCY, w - 0.39, PCH)
        text(s, "slot.platform.%d.label" % i, one(word, size=10), th, size=10, anchor="middle")
    else:
        move(s, "slot.platform.%d.label" % i, x + 0.06, PCY, w - 0.12, PCH)
        text(s, "slot.platform.%d.label" % i, one(word, size=10, align="center"), th, size=10, anchor="middle")

# boundary crossings: sources into the core, pipelines into the runtime, the core out to consumers
rename(s, "dev.131", "struct.flow.in")
rename(s, "dev.135", "struct.flow.across")
rename(s, "dev.133", "struct.flow.out")

out = save(prs, "DL31", th, archetype="solution-architecture", variant=VARIANT)
if a.out:
    shutil.copyfile(out, a.out)
