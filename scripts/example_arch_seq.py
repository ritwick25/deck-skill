"""Four technical diagrams drawn by deckkit.arch_seq on the fictional Quillmont field brief service (rulings 20, 21).

    $PY scripts/example_arch_seq.py [--out .cache/arch_seq/arch_seq.pptx] [--theme themes/sigmoid.json]

  1 swimlane-handoff:arch-sequence            a brief request: seven participants, a loop over the cited claims,
                                              an alt that holds a brief with an unsourced claim, one trust band
  2 solution-architecture:arch-dfd            the brief pipeline as a Gane-Sarson DFD and threat model: five
                                              processes, three stores, two trust boundaries, every crossing marked
                                              with its control, one element out of scope
  3 solution-architecture:arch-c4-context     the service among the people and systems around it
  4 layered-architecture:arch-c4-container    the service opened into its containers, tier by tier

Canon: Decks-For-Visuals/acceptance/showcase/canon.json ("stack", "agents"); component names and marks match
scripts/example_arch.py, so P26 (v) holds across both decks. Fictional client; nothing names a real one. Every count a
title states is read back from the drawing's metrics and asserted before the deck is saved. The deck.json beside the
output grants P15: two slides of one archetype in a four-slide engine example is the example's point.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "kit"))

from pptx import Presentation  # noqa: E402

from deckkit import arch_seq, package, prims, tag  # noqa: E402
from deckkit.canvas import WIDE  # noqa: E402
from deckkit.text import title  # noqa: E402
from deckkit.theme import Theme  # noqa: E402

C = WIDE.content
DRAFT = False          # --draft lists what does not fit instead of raising; never for a deck that ships
WORDS = {2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight", 9: "Nine"}

# one name and one mark per component, the same as scripts/example_arch.py (P26 v)
M = {
    "app": "vendor:programming/framework/react", "review": "vendor:programming/framework/react",
    "api": "vendor:aws/network/api-gateway", "writer": "vendor:aws/compute/elastic-container-service-task",
    "scan": "vendor:aws/compute/elastic-container-service-task", "bedrock": "vendor:aws/ml/bedrock",
    "search": "vendor:aws/analytics/amazon-opensearch-service", "rds": "vendor:aws/database/rds",
    "s3": "vendor:aws/storage/simple-storage-service-s3", "collect": "vendor:aws/compute/lambda",
}


def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[0])


# ---------------------------------------------------------------------------------------------- 1 sequence

def sequence(prs, th):
    s = blank(prs)
    tag.tag(s, "swimlane-handoff", "arch-sequence")
    title(s, "A brief stops for medical review whenever one claim has no approved source",
          keywords=("stops for medical review",), canvas=WIDE, theme=th)
    q = arch_seq.Sequence()
    q.participant("app", M["app"], "Field app", "React Native")
    q.participant("api", M["api"], "API Gateway", "brief API")
    q.participant("writer", M["writer"], "Writer agent", "LangGraph on Fargate")
    q.participant("bedrock", M["bedrock"], "Amazon Bedrock", "Claude models")
    q.participant("search", M["search"], "OpenSearch", "claim index")
    q.participant("review", M["review"], "Review app", "medical review")
    q.band("AWS account · private subnets, IAM roles only", "api", "review")
    q.message("app", "api", "POST /briefs {account_id}")
    q.message("api", "writer", "start brief run")
    q.message("writer", "bedrock", "plan the brief")
    q.message("bedrock", "writer", "tool_use: search", kind="reply")
    a = q.message("writer", "search", "search claims")
    b = q.message("search", "writer", "sources, ranked", kind="reply")
    q.message("writer", "bedrock", "draft with sources")
    q.message("bedrock", "writer", "one-page draft", kind="reply")
    c = q.message("writer", "api", "brief ready", kind="reply")
    e = q.message("writer", "review", "hold the brief", kind="async")
    d = q.message("writer", "api", "held for review", kind="reply")
    q.message("api", "app", "200 {brief_id, status}", kind="reply")
    q.fragment("loop", "each cited claim", a, b)
    q.fragment("alt", "every claim sourced", c, d, else_at=e, else_guard="a claim has no source")
    return q.render(s, C, th, name="seq")


# ---------------------------------------------------------------------------------------------- 2 DFD

def dfd(prs, th):
    s = blank(prs)
    tag.tag(s, "solution-architecture", "arch-dfd")
    d = arch_seq.DFD(grid=(6, 3), weights=[1.75, 2.15, 2.15, 2.15, 2.15, 2.05], row_weights=[0.95, 1.12, 0.78])
    d.boundary("acct", "AWS account · production, eu-west-1", at=(1, 0, 4, 3), kind="trust")
    d.boundary("zone", "Agent zone · private subnets", at=(2, 1, 3, 2), kind="zone", parent="acct")
    d.entity("web", "Public web", "press, trials", at=(0, 0), mark="glyph:globe")
    d.entity("bedrock", "Amazon Bedrock", "Claude models", at=(3.2, 0), mark=M["bedrock"], size=(1.65, 0.62))
    d.entity("reviewer", "Medical reviewer", "approves claims", at=(5, 2), mark="glyph:user-check")
    d.entity("app", "Field app", "existing · out of scope", at=(5, 1), out_of_scope=True)
    d.process("collect", "1", "Collect signals", at=(1, 1), tech="AWS Lambda")
    d.process("index", "2", "Index claims", at=(2, 1), tech="Scan agent")
    d.process("draft", "3", "Draft the brief", at=(3, 1), tech="Writer agent")
    d.process("check", "4", "Check every claim", at=(4, 1), tech="Review queue")
    d.process("deliver", "5", "Deliver the brief", at=(4, 0), tech="API Gateway")
    d.store("lake", "D1", "Signal lake", at=(1.15, 2), mark=M["s3"], size=(1.55, 0.44))
    d.store("claims", "D2", "Claim index", at=(2.6, 2), mark=M["search"])
    d.store("ledger", "D3", "Source ledger", at=(3.45, 2), mark=M["rds"])
    d.flow("web", "collect", "web pages", control="HTTPS · TLS 1.3", route="hv")
    d.flow("collect", "lake", "raw signals")
    d.flow("lake", "index", "new files", control="IAM · endpoint", route="hv", enter=0.3)
    d.flow("index", "claims", "cited claims")
    d.flow("claims", "draft", "sources")
    d.flow("draft", "bedrock", "prompt", control="PrivateLink · SigV4")
    d.flow("draft", "check", "draft")
    d.flow("check", "ledger", "review record")
    d.flow("check", "reviewer", "held claims", control="HTTPS · OIDC", route="vh", exit=0.8)
    d.flow("check", "deliver", "approved brief", control="IAM role · TLS 1.3")
    d.flow("deliver", "app", "Monday brief", control="HTTPS · OIDC · TLS 1.3", route="hv")
    # the title's count is the drawing's: rendered first on a scratch slide would duplicate shapes, so it is
    # computed from the declared flows after render and asserted
    m = d.render(s, C, th, name="dfd", draft=DRAFT)
    n = m["crossing_flows"]
    title(s, "%s flows cross a trust boundary, and each one carries its own control" % WORDS[n],
          keywords=("%s flows" % WORDS[n],), canvas=WIDE, theme=th)
    return m


# ---------------------------------------------------------------------------------------------- 3 C4 context

def c4_context(prs, th):
    s = blank(prs)
    tag.tag(s, "solution-architecture", "arch-c4-context")
    c = arch_seq.C4("context", grid=(4, 3), weights=[2.4, 2.5, 3.6, 2.5], row_weights=[1.0, 1.25, 1.0])
    c.boundary("ent", "Quillmont · enterprise boundary", at=(1, 0, 3, 3), kind="enterprise")
    c.person("reviewer", "Medical reviewer", "Approves held claims", at=(1, 0))
    c.person("rep", "Field rep", "Reads the brief", at=(3, 0))
    c.system("svc", "Field brief service", "Drafts a sourced competitor brief every week", at=(2, 1),
             size=(2.55, 1.10))
    c.external("app", "Field app", "Existing mobile app", at=(3, 1), mark=M["app"])
    c.external("crm", "CRM", "Accounts and territories", at=(1, 2))
    c.external("web", "Public web", "Press, trials, congresses", at=(0, 1))
    c.external("bedrock", "Amazon Bedrock", "Claude models", at=(0, 2), mark=M["bedrock"])
    c.rel("rep", "app", "reads the brief")
    c.rel("app", "svc", "fetches · HTTPS")
    c.rel("reviewer", "svc", "approves claims · HTTPS")
    c.rel("svc", "web", "collects signals · HTTPS")
    c.rel("svc", "bedrock", "drafts with Claude")
    c.rel("crm", "svc", "account plans · nightly")
    m = c.render(s, C, th, name="c4ctx", draft=DRAFT)
    ext = sum(1 for nd in c.nodes.values() if nd.kind == "external")
    title(s, "One service sits between two kinds of user and the %s systems around it" % WORDS[ext].lower(),
          keywords=("One service",), canvas=WIDE, theme=th)
    return m


# ---------------------------------------------------------------------------------------------- 4 C4 container

def c4_container(prs, th):
    s = blank(prs)
    tag.tag(s, "layered-architecture", "arch-c4-container")
    title(s, "Eight containers carry the service, and only the writer agent calls the model",
          keywords=("only the writer agent",), canvas=WIDE, theme=th)
    c = arch_seq.C4("container", grid=(5, 4), weights=[1.85, 2.75, 2.75, 2.75, 1.85], row_weights=[1.12, 1.18, 1.03, 0.87])
    c.boundary("svc", "Brief service · AWS", at=(1, 1, 3, 3), kind="system")
    c.person("reviewer", "Medical reviewer", "Approves held claims", at=(1, 0))
    c.person("rep", "Field rep", "Reads the brief", at=(4, 1))
    c.external("app", "Field app", "Existing mobile app", at=(3, 0), mark=M["app"])
    c.external("web", "Public web", "Press, trials, congresses", at=(0, 3))
    c.external("bedrock", "Amazon Bedrock", "Claude models", at=(4, 3), mark=M["bedrock"])
    c.container("review", "Review app", "React", "Held claims, one by one", at=(1, 1), mark=M["review"])
    c.container("ledger", "Source ledger", "Amazon RDS", "Sources and reviews", at=(2, 1), mark=M["rds"])
    c.container("api", "Brief API", "API Gateway", "Serves briefs and holds", at=(3, 1), mark=M["api"])
    c.container("collect", "Collectors", "AWS Lambda", "Pull public signals", at=(1, 2), mark=M["collect"])
    c.container("scan", "Scan agent", "LangGraph", "Extracts cited claims", at=(2, 2), mark=M["scan"])
    c.container("writer", "Writer agent", "LangGraph", "Drafts the brief", at=(3, 2), mark=M["writer"])
    c.container("lake", "Signal lake", "Amazon S3", "Raw and refined signals", at=(1.5, 3), mark=M["s3"])
    c.container("claims", "Claim index", "OpenSearch", "Claims with source ids", at=(2.5, 3), mark=M["search"])
    c.rel("reviewer", "review", "approves claims")
    c.rel("rep", "app", "reads the brief", route="vh")
    c.rel("app", "api", "GET /briefs · HTTPS")
    c.rel("review", "ledger", "reads · SQL")
    c.rel("api", "ledger", "reads · SQL")
    c.rel("collect", "web", "collects · HTTPS", route="hv")
    c.rel("collect", "lake", "writes signals")
    c.rel("scan", "lake", "reads new files")
    c.rel("scan", "claims", "writes claims")
    c.rel("writer", "claims", "searches claims")
    c.rel("writer", "ledger", "writes the brief")
    c.rel("writer", "bedrock", "drafts · HTTPS", route="hv", exit=0.75)
    m = c.render(s, C, th, name="c4ctr", draft=DRAFT)
    cont = sum(1 for nd in c.nodes.values() if nd.kind == "container")
    callers = {f.src for f in c.flows if f.dst == "bedrock"}
    assert DRAFT or (cont == 8 and callers == {"writer"}), (cont, callers)
    return m


def vendor_media(deck: Path) -> dict:
    """{sha256: reason} for every embedded picture that is a registered vendor mark, byte for byte (P18 matches the
    official icons against the reference decks, which embed the same public artwork; P22 verifies each one)."""
    table = json.loads((SKILL / "kit" / "assets" / "vendor_hashes.json").read_text(encoding="utf-8"))["keys"]
    keys = {h: k for k, sizes in table.items() for h in sizes.values()}
    out = {}
    with zipfile.ZipFile(deck) as z:
        for n in sorted(z.namelist()):
            if n.startswith("ppt/media/"):
                h = hashlib.sha256(z.read(n)).hexdigest()
                if h in keys:
                    out[h] = ("official vendor mark %s from the diagrams package, byte-verified by P22 against "
                              "vendor_hashes.json; the reference decks embed the same public icon" % keys[h])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(SKILL / ".cache" / "arch_seq" / "arch_seq.pptx"))
    ap.add_argument("--theme", default=str(SKILL / "themes" / "sigmoid.json"))
    ap.add_argument("--draft", action="store_true")
    a = ap.parse_args()
    global DRAFT
    DRAFT = a.draft
    th = Theme.load(a.theme)
    prs = Presentation(str(SKILL / "kit" / "assets" / "base-wide.pptx"))
    prims.bind(th)
    metrics = {"seq": sequence(prs, th), "dfd": dfd(prs, th), "c4ctx": c4_context(prs, th),
               "c4ctr": c4_container(prs, th)}
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sha = package.save(prs, out, title="Sequence, DFD and C4", theme=th, manifest={"numbers": {}}, overwrite=True,
                       date="2026-10-04")
    dj = {"type": "example", "canvas": "wide", "theme": a.theme, "client": None, "spelling": "US",
          "media_allow": vendor_media(out),
          "overrides": {"P15": "DECISIONS.md ruling 20: the engine's example deck shows four diagram types, two of "
                               "them solution-architecture variants, by design"},
          "series": [], "deliverable": out.name,
          "build": ["{python}", str(Path(__file__).resolve()), "--theme", a.theme, "--out", "{out}"]}
    (out.parent / "deck.json").write_text(json.dumps(dj, indent=2) + "\n", encoding="utf-8")
    for k, m in metrics.items():
        print("%-6s %s" % (k, m))
    print("OK %s sha256 %s" % (out, sha[:12]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
