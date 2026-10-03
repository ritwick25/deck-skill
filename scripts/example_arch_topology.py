"""Four topology slides drawn by deckkit.arch on the fictional Quillmont brief service (spec 3.5, ruling 21).

    $PY scripts/example_arch_topology.py [--out .cache/arch/topology.pptx] [--theme themes/sigmoid.json] [--draft]

  1 solution-architecture:arch-deploy-aws     Region > VPC > two AZ columns x three subnet tiers; the ECS service as a
                                              span band across both AZs; Aurora writer and reader; interface
                                              endpoints on the VPC edge; NAT and Network Firewall on the egress path;
                                              a blocked path to the open internet; a four-style line key
  2 solution-architecture:arch-deploy-azure   hub and spoke virtual networks joined by a labelled peering; Azure
                                              Firewall and Bastion in the hub; a private endpoint subnet with one
                                              endpoint per PaaS target; NSG shields; zone-redundant replicas; a
                                              blocked egress path
  3 solution-architecture:arch-dr-aws         an AWS Organizations OU tree with its accounts beside an active and a
                                              passive Region with their recovery point and recovery time
  4 solution-architecture:arch-current-target today's brief pipeline beside the target one, with lettered change
                                              markers keyed in a change rail between them

Stack canon: Decks-For-Visuals/acceptance/showcase/canon.json "stack" and figures (fictional client; the addresses,
counts, RPO and RTO are illustrative). The deck carries no speaker notes (gate P20: notes travel in the presenter
deck). The deck.json beside the output grants P15: four slides of one family is the example's point.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "kit"))
sys.path.insert(0, str(SKILL / "scripts"))

from pptx import Presentation  # noqa: E402

from deckkit import arch, package, prims, tag  # noqa: E402
from deckkit.canvas import WIDE, Box  # noqa: E402
from deckkit.text import title  # noqa: E402
from deckkit.theme import Theme  # noqa: E402

C = WIDE.content
DRAFT = False

V = {   # one mark per component across the slides (house rule 13, gate P26.v)
    "users": "vendor:aws/general/users", "internet": "vendor:aws/general/internet-alt1",
    "r53": "vendor:aws/network/route-53", "cdn": "vendor:aws/network/cloudfront", "waf": "vendor:aws/security/waf",
    "igw": "vendor:aws/network/internet-gateway", "alb": "vendor:aws/network/elb-application-load-balancer",
    "nat": "vendor:aws/network/nat-gateway", "fw": "vendor:aws/network/network-firewall",
    "task": "vendor:aws/compute/fargate", "aurora": "vendor:aws/database/aurora",
    "ep": "vendor:aws/network/endpoint", "bedrock": "vendor:aws/ml/bedrock",
    "s3": "vendor:aws/storage/simple-storage-service-s3", "nacl": "vendor:aws/network/nacl",
    "langfuse": "mark:langfuse-icon", "secrets": "vendor:aws/security/secrets-manager",
    "ecr": "vendor:aws/compute/ec2-container-registry",
}


def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[0])


# ---------------------------------------------------------------------------------------------- 1 AWS deployment

def aws_deploy(prs, th):
    s = blank(prs)
    tag.tag(s, "solution-architecture", "arch-deploy-aws")
    title(s, "Private agents leave the VPC only through endpoints or the firewall",
          keywords=("endpoints or the firewall",), canvas=WIDE, theme=th)
    d = arch.Diagram("aws", grid=(4, 1), weights=[0.8, 1.2, 9.58, 0.82], head_air=0.12, icon=0.38)
    d.group("left", "lane", None, at=(0, 0, 1, 1), grid=(1, 3))
    d.node("reps", V["users"], "Field reps", group="left", at=(0, 0), anchor="left")
    d.node("open", V["internet"], "Open internet", group="left", at=(0, 2), anchor="left")
    d.group("right", "lane", None, at=(3, 0, 1, 1), grid=(1, 3))
    d.node("langfuse", V["langfuse"], "Langfuse", "traces", group="right", at=(0, 0))
    d.group("edge", "lane", "Global edge", at=(1, 0, 1, 1), grid=(1, 3))
    d.node("r53", V["r53"], "Route 53", "DNS", group="edge", at=(0, 0))
    d.node("waf", V["waf"], "AWS WAF", "web ACL", group="edge", at=(0, 1), caption="right", anchor="left")
    d.node("cdn", V["cdn"], "CloudFront", group="edge", at=(0, 2))
    d.group("region", "aws-region", "Region eu-west-1", fact="account brief-prod · 2 AZs", at=(2, 0, 1, 1),
            grid=(4, 1), weights=[0.74, 6.4, 0.82, 1.32], drop=0.17)
    d.group("vpc", "aws-vpc", "VPC 10.20.0.0/16", fact="3 tiers per AZ", parent="region", at=(1, 0, 1, 1),
            grid=(4, 1), weights=[0.2, 1, 0.2, 1], align_rows=True)
    for az, col, wts, inner in (("a", 1, [1.56, 1], 0), ("b", 3, [1, 1.56], 1)):
        d.group("az" + az, "aws-az", "Availability Zone %s" % az, parent="vpc", at=(col, 0, 1, 1), grid=(1, 3),
                row_gap=[0.04, 0.04])
        for r, (tier, kind, name) in enumerate((("pub", "aws-public-subnet", "Public"),
                                                ("app", "aws-private-subnet", "App"),
                                                ("dat", "aws-private-subnet", "Data"))):
            d.group(tier + az, kind, name, parent="az" + az, at=(0, r, 1, 1), grid=(2, 1), weights=wts)
        outer = 1 - inner                                 # the NAT gateways sit beside the gutter, under the gateway
        d.node("fw" + az, V["fw"], "Network Firewall", group="pub" + az, at=(inner, 0),
               caption="left" if az == "a" else "right", anchor="right" if az == "a" else "center")
        d.node("nat" + az, V["nat"], "NAT gateway", group="pub" + az, at=(outer, 0))
        d.node("task" + az, V["task"], "2 agent tasks", "Fargate", group="app" + az, at=(inner, 0), caption="left",
               anchor="right" if az == "a" else "center")
        d.pin("nacl" + az, V["nacl"], "dat" + az, corner="tr" if az == "a" else "bl", label="NACL")
    d.node("writer", V["aurora"], "Aurora writer", group="data", at=(0, 0))
    d.node("reader", V["aurora"], "Aurora reader", group="datb", at=(1, 0))
    d.span("svc", "ECS service", ["appa", "appb"])
    d.node("igw", V["igw"], "Internet gateway", group="vpc", at=(2, 0), anchor="edge:t")
    d.node("alb", V["alb"], "Load balancer", "ALB", group="vpc", at=(0, 0), anchor="edge:l")
    d.node("brep", V["ep"], "Bedrock endpoint", group="vpc", at=(3, 0), anchor="edge:r")
    d.node("s3ep", V["ep"], "S3 endpoint", "gateway", group="vpc", at=(3, 0), anchor="edge:r", caption="below")
    d.group("rcol", "lane", None, parent="region", at=(3, 0, 1, 1), grid=(1, 3))
    d.group("ops", "generic", "Ops", fact="shared", parent="rcol", at=(0, 0, 1, 1), grid=(1, 3), band=True)
    for r, (nid, key, name) in enumerate((("kms", "vendor:aws/security/key-management-service", "AWS KMS"),
                                          ("secrets", V["secrets"], "Secrets"),
                                          ("watch", "vendor:aws/management/cloudwatch", "CloudWatch"))):
        d.node(nid, key, name, group="ops", at=(0, r), size=0.34)
    d.node("bedrock", V["bedrock"], "Bedrock", "Claude models", group="rcol", at=(0, 1))
    d.node("s3", V["s3"], "Amazon S3", "brief files", group="rcol", at=(0, 2))
    for nid, to, axis, off in (("taska", "fwa", "x", 0.0), ("writer", "taska", "x", 0.0), ("taskb", "fwb", "x", 0.0),
                               ("reader", "taskb", "x", 0.0), ("fwa", "nata", "y", 0.0), ("fwb", "natb", "y", 0.0),
                               ("alb", "taska", "y", 0.0), ("cdn", "alb", "y", 0.0),
                               ("waf", "cdn", "y", -1.1), ("r53", "cdn", "y", -2.05), ("reps", "cdn", "y", 0.0),
                               ("brep", "taskb", "y", 0.0), ("s3ep", "reader", "y", 0.0), ("bedrock", "brep", "y", 0.0),
                               ("s3", "s3ep", "y", 0.0), ("open", "writer", "y", 0.0)):
        d.align(nid, to, axis=axis, offset=off)
    d.flow("reps", "cdn", "HTTPS")
    d.flow("reps", "r53", "DNS")
    d.flow("waf", "cdn", "rules", kind="control")
    d.flow("cdn", "alb", "origin")
    d.flow("alb", "svc", "8080")
    d.flow("taska", "writer", "5432 TLS")
    d.flow("taskb", "reader", "reads")
    d.flow("writer", "reader", "replica")
    d.flow("svc", "fwa", "egress")
    d.flow("svc", "fwb", "egress")
    d.flow("fwa", "nata")
    d.flow("fwb", "natb")
    d.flow("nata", "igw", "443")
    d.flow("natb", "igw", "443")
    d.flow("igw", "langfuse", "443 allow-list")
    d.bus("eps", ["taskb"], ["brep", "s3ep"], "443 TLS")
    d.flow("brep", "bedrock", kind="private")
    d.flow("s3ep", "s3", kind="private")
    d.flow("writer", "open", "no route", kind="blocked")
    m = d.render(s, C, th, name="deploy", draft=DRAFT)
    return m

# ---------------------------------------------------------------------------------------------- 2 Azure deployment

Z = {
    "users": "vendor:azure/identity/users", "internet": "vendor:aws/general/internet-alt1",
    "fd": "vendor:azure/networking/front-door-and-cdn-profiles",
    "entra": "vendor:azure/identity/azure-active-directory",
    "appgw": "vendor:azure/networking/application-gateways", "fw": "vendor:azure/networking/firewalls",
    "app": "vendor:azure/compute/container-apps", "agent": "vendor:azure/other/worker-container-app",
    "pe": "vendor:azure/other/private-endpoints", "openai": "vendor:azure/aimachinelearning/azure-openai",
    "search": "vendor:azure/aimachinelearning/cognitive-search", "cosmos": "vendor:azure/databases/azure-cosmos-db",
    "blob": "vendor:azure/storage/storage-accounts", "vault": "vendor:azure/security/key-vaults",
    "monitor": "vendor:azure/managementgovernance/monitor",
    "logs": "vendor:azure/managementgovernance/log-analytics-workspaces",
    "defender": "vendor:azure/security/microsoft-defender-for-cloud",
}


def azure_deploy(prs, th):
    s = blank(prs)
    tag.tag(s, "solution-architecture", "arch-deploy-azure")
    title(s, "Spoke agents reach Azure models only through private endpoints",
          keywords=("only through private endpoints",), canvas=WIDE, theme=th)
    d = arch.Diagram("azure", grid=(3, 1), weights=[0.85, 1.12, 10.43], head_air=0.12, icon=0.38)
    d.group("left", "lane", None, at=(0, 0, 1, 1), grid=(1, 4))
    d.node("reps", Z["users"], "Field reps", group="left", at=(0, 0), anchor="left")
    d.node("allow", Z["internet"], "Approved APIs", group="left", at=(0, 2), anchor="left")
    d.node("open", Z["internet"], "Open internet", group="left", at=(0, 3), anchor="left")
    d.group("edge", "lane", "Global", at=(1, 0, 1, 1), grid=(1, 3))
    d.node("entra", Z["entra"], "Entra ID", "sign-in", group="edge", at=(0, 0))
    d.node("fd", Z["fd"], "Front Door", "WAF", group="edge", at=(0, 1))
    d.group("region", "azure-region", "Region East US 2", fact="3 zones", at=(2, 0, 1, 1), grid=(2, 1),
            weights=[2.82, 6.68], gutter=0.95)
    d.group("hubsub", "azure-subscription", "Subscription: hub", parent="region", at=(0, 0, 1, 1), grid=(1, 2),
            row_gap=[0.08])
    d.group("hub", "azure-vnet", "Hub VNet 10.0.0.0/22", parent="hubsub", at=(0, 0, 1, 1), grid=(1, 2),
            row_gap=[0.06])
    d.group("gwsub", "azure-subnet", "Gateway", parent="hub", at=(0, 0, 1, 1), grid=(1, 1))
    d.node("appgw", Z["appgw"], "App Gateway", "WAF v2", group="gwsub", at=(0, 0))
    d.group("fwsub", "azure-subnet", "Firewall", parent="hub", at=(0, 1, 1, 1), grid=(1, 1))
    d.node("fw", Z["fw"], "Azure Firewall", "allow-list", group="fwsub", at=(0, 0))
    d.group("mon", "generic", "Monitoring", parent="hubsub", at=(0, 1, 1, 1), grid=(3, 1), band=True,
            weights=[1.05, 0.8, 1.15])
    for k, (nid, name) in enumerate((("monitor", "Monitor"), ("logs", "Logs"), ("defender", "Defender"))):
        d.node(nid, Z[nid], name, group="mon", at=(k, 0), size=0.34)
    d.group("spksub", "azure-subscription", "Subscription: brief service", fact="spoke", parent="region",
            at=(1, 0, 1, 1), grid=(2, 1), weights=[4.75, 1.75])
    d.group("spoke", "azure-vnet", "Spoke VNet 10.30.0.0/16", parent="spksub", at=(0, 0, 1, 1), grid=(2, 1),
            weights=[2.6, 1.55])
    d.group("apps", "azure-subnet", "Container Apps", parent="spoke", at=(0, 0, 1, 1), grid=(2, 2))
    d.node("review", Z["app"], "Review app", "zones 1 to 3", group="apps", at=(0, 0))
    d.node("agent", Z["agent"], "Agent app", "zones 1 to 3", group="apps", at=(1, 0))
    d.group("pes", "azure-subnet", "Endpoints", parent="spoke", at=(1, 0, 1, 1), grid=(1, 5))
    d.group("rg", "azure-resource-group", "Brief data", parent="spksub", at=(1, 0, 1, 1), grid=(1, 5),
            lift=0.12)
    for r, (svc, name, pe) in enumerate((("cosmos", "Cosmos DB", "Cosmos PE"), ("openai", "Azure OpenAI", "OpenAI PE"),
                                         ("search", "AI Search", "Search PE"), ("blob", "Storage", "Storage PE"),
                                         ("vault", "Key Vault", "Vault PE"))):
        d.node("pe" + svc, Z["pe"], pe, group="pes", at=(0, r))
        d.node(svc, Z[svc], name, group="rg", at=(0, r))
        d.align(svc, "pe" + svc)
        d.flow("pe" + svc, svc, kind="private")
    d.align("review", "appgw")
    d.align("agent", "review")
    d.align("fd", "appgw")
    d.align("reps", "fd")
    d.flow("reps", "fd", "HTTPS")
    d.flow("reps", "entra", "sign-in")
    d.flow("fd", "appgw", "443")
    d.flow("appgw", "review", "8080")
    d.flow("review", "agent", "draft job")
    d.bus("pe", ["agent"], ["pecosmos", "peopenai", "pesearch", "peblob", "pevault"], "443")
    d.flow("apps", "fw", "egress UDR")
    d.flow("fw", "allow", "443 allow-list")
    d.flow("fw", "open", "no rule", kind="blocked")
    d.flow("hub", "spoke", "VNet peering", kind="peering")
    return d.render(s, C, th, name="azdeploy", draft=DRAFT)


# ---------------------------------------------------------------------------------------------- 3 DR and landing zone

def aws_dr(prs, th):
    s = blank(prs)
    tag.tag(s, "solution-architecture", "arch-dr-aws")
    title(s, "A standby Region restores the brief service within an hour",
          keywords=("within an hour",), canvas=WIDE, theme=th)
    org, ou, acct = ("vendor:aws/management/organizations", "vendor:aws/management/organizations-organizational-unit",
                     "vendor:aws/management/organizations-account")
    d = arch.Diagram("aws", grid=(2, 2), weights=[3.0, 9.4], head_air=0.12, icon=0.38, stretch=[1])
    d.group("org", "generic", "AWS Organizations", fact="3 OUs, 6 accounts", at=(0, 0, 1, 2), grid=(3, 10),
            weights=[0.42, 0.42, 2.2])
    d.node("root", org, "Management", "root · SCPs", group="org", at=(0, 0), caption="right", anchor="left",
           cols=3)
    r = 1
    for oid, oname, accts in (("sec", "Security", ("Log archive", "Audit")),
                              ("infra", "Infrastructure", ("Network", "Shared services")),
                              ("work", "Workloads", ("brief-prod", "brief-staging"))):
        d.node(oid, ou, oname, "OU", group="org", at=(1, r), caption="right", anchor="left", cols=2)
        for j, an in enumerate(accts):
            d.node("%s%d" % (oid, j), acct, an, group="org", at=(2, r + 1 + j), caption="right", anchor="left")
        d.bus("t" + oid, [oid], ["%s0" % oid, "%s1" % oid], tree=True)
        r += 3
    d.bus("scp", ["root"], ["sec", "infra", "work"], tree=True)
    d.group("top", "lane", None, at=(1, 0, 1, 1), grid=(3, 1), weights=[3.5, 1.6, 3.5])
    d.node("reps", V["users"], "Field reps", group="top", at=(1, 0), caption="right")
    d.group("acct", "aws-account", "Account brief-prod", fact="workloads OU", at=(1, 1, 1, 1), grid=(3, 1),
            weights=[3.5, 1.6, 3.5])
    d.group("mid", "lane", None, parent="acct", at=(1, 0, 1, 1), grid=(1, 4))
    d.node("r53", V["r53"], "Route 53", "health checks", group="mid", at=(0, 0))
    for rid, name, fact, outer, inner in (("ra", "Region eu-west-1", "active", 0, 1),
                                          ("rb", "Region eu-central-1", "standby · RTO 1 h", 1, 0)):
        d.group(rid, "aws-region", name, fact=fact, parent="acct", at=(0 if rid == "ra" else 2, 0, 1, 1),
                grid=(2, 4))
        cap = "left" if rid == "ra" else "right"
        d.node(rid + "alb", V["alb"], "Load balancer", group=rid, at=(outer, 0), caption=cap)
        d.node(rid + "ecs", V["task"], "Agent tasks", "4 tasks" if rid == "ra" else "1 task, warm", group=rid,
               at=(outer, 1), caption=cap)
        d.node(rid + "s3", V["s3"], "Amazon S3", group=rid, at=(inner, 1))
        d.node(rid + "db", V["aurora"], "Aurora", "writer" if rid == "ra" else "replica", group=rid, at=(outer, 2))
        d.node(rid + "bk", "vendor:aws/storage/backup", "AWS Backup", "vault", group=rid, at=(outer, 3))
    for a, b in (("rbalb", "raalb"), ("r53", "raalb"), ("rbs3", "ras3"), ("rbdb", "radb"),
                 ("rbbk", "rabk"), ("rbecs", "raecs")):
        d.align(a, b)
    d.align("reps", "r53", axis="x")
    for rid in ("ra", "rb"):
        d.align(rid + "ecs", rid + "alb", axis="x")
        d.align(rid + "db", rid + "alb", axis="x")
        d.align(rid + "bk", rid + "alb", axis="x")
    d.flow("reps", "r53", "DNS")
    d.flow("r53", "raalb", "primary")
    d.flow("r53", "rbalb", "failover")
    for rid in ("ra", "rb"):
        d.flow(rid + "alb", rid + "ecs", "8080")
        d.flow(rid + "ecs", rid + "db", "5432")
    d.flow("raecs", "ras3")
    d.flow("rbecs", "rbs3")
    d.flow("ras3", "rbs3", "CRR · RPO 15 min", kind="async")
    d.flow("radb", "rbdb", "RPO 1 s", kind="async")
    d.flow("rabk", "rbbk", "copy · daily", kind="async")
    return d.render(s, C, th, name="dr", draft=DRAFT)


# ---------------------------------------------------------------------------------------------- 4 current versus target

H = {
    "jenkins": "vendor:onprem/ci/jenkins", "py": "vendor:programming/language/python",
    "pg": "vendor:onprem/database/postgresql", "tableau": "vendor:onprem/analytics/tableau",
    "teams": "vendor:saas/chat/teams", "sched": "vendor:aws/integration/eventbridge-scheduler",
    "lambda": "vendor:aws/compute/lambda", "s3": V["s3"], "scan": "vendor:aws/compute/elastic-container-service-task",
    "search": "vendor:aws/analytics/amazon-opensearch-service", "bedrock": V["bedrock"],
    "writer": "vendor:aws/compute/elastic-container-service-task", "review": "vendor:programming/framework/react",
    "api": "vendor:aws/network/api-gateway", "app": "vendor:programming/framework/react",
}
CHANGES = (("A", "cron scripts on one VM", "scheduled Lambda collectors"),
           ("B", "6 regional drafts in Word", "one cited draft per week"),
           ("C", "review by email thread", "review app, decisions logged"),
           ("D", "PDF posted to a chat channel", "brief in the field app"))


def current_target(prs, th):
    s = blank(prs)
    tag.tag(s, "solution-architecture", "arch-current-target")
    title(s, "Agents cut the brief from five days to one, with review kept",
          keywords=("five days to one",), canvas=WIDE, theme=th)
    rail_w = 2.05
    d = arch.Diagram("house", grid=(1, 2), head_air=0.14, icon=0.38, gaps=[1])
    d.group("cur", "region", "Today", at=(0, 0, 1, 1), grid=(7, 2), row_gap=[0.16])
    d.group("vm", "boundary", "On-premises", fact="one VM", parent="cur", at=(1, 0, 4, 1), grid=(4, 1))
    for k, (nid, key, name, role) in enumerate((("jenkins", "jenkins", "Jenkins", "nightly cron"),
                                               ("py", "py", "Scrapers", "Python, web pages"),
                                               ("pg", "pg", "PostgreSQL", "signal rows"),
                                               ("tableau", "tableau", "Tableau", "extracts"))):
        d.node(nid, H[key], name, role, group="vm", at=(k, 0))
    d.node("drive", "glyph:folder-open", "File share", "exports", group="cur", at=(5, 0))
    d.node("reps0", "glyph:users", "Field reps", group="cur", at=(0, 1))
    d.node("teams", H["teams"], "Teams", "channel", group="cur", at=(1, 1))
    d.node("mail", "glyph:mail", "Email review", "one thread", group="cur", at=(2, 1))
    d.node("analysts", "glyph:user", "Analysts", "6 regions", group="cur", at=(5, 1))
    d.node("drafts", "glyph:file-text", "Word drafts", "6 versions", group="cur", at=(6, 1))
    d.group("tgt", "region", "Target", at=(0, 1, 1, 1), grid=(7, 2), row_gap=[0.16])
    d.group("aws", "boundary", "AWS account", fact="eu-west-1", parent="tgt", at=(1, 0, 6, 2), grid=(6, 2))
    for c, (nid, name, role) in enumerate((("sched", "Scheduler", "weekly"), ("lambda", "Lambda", "collectors"),
                                           ("s3", "Amazon S3", "signal lake"), ("scan", "Scan agent", "ECS"),
                                           ("search", "OpenSearch", "claims"))):
        d.node(nid, H[nid], name, role, group="aws", at=(c, 0))
    for c, (nid, name, role) in ((0, ("api", "API Gateway", "brief API")), (1, ("review", "Review app", "React")),
                                 (4, ("writer", "Writer agent", "ECS")), (5, ("bedrock", "Bedrock", "Claude models"))):
        d.node(nid, H[nid], name, role, group="aws", at=(c, 1))
    d.node("app", H["app"], "Field app", "React Native", group="tgt", at=(0, 1))
    for a_, b_ in (("jenkins", "sched"), ("py", "lambda"), ("pg", "s3"), ("tableau", "scan"), ("drive", "search"),
                   ("teams", "api"), ("mail", "review"), ("analysts", "writer"), ("drafts", "bedrock")):
        d.align(a_, b_, axis="x")
    d.align("drive", "tableau")
    d.flow("jenkins", "py", "runs", kind="control")
    d.flow("py", "pg", "rows")
    d.flow("pg", "tableau", "feeds")
    d.flow("tableau", "drive", "CSV")
    d.flow("drive", "analysts", "reads")
    d.flow("analysts", "drafts", "6 drafts")
    d.flow("analysts", "mail", "PDFs")
    d.flow("mail", "teams", "approved")
    d.flow("teams", "reps0", "post")
    d.flow("sched", "lambda", "runs", kind="control")
    d.flow("lambda", "s3", "signals")
    d.flow("s3", "scan", "new files")
    d.flow("scan", "search", "claims")
    d.flow("search", "writer", "cited claims")
    d.flow("writer", "bedrock", "draft")
    d.flow("writer", "review", "brief", hero=True)
    d.flow("review", "api", "approved", hero=True)
    d.flow("api", "app", "brief", hero=True)
    for letter, (a_, b_) in zip("ABCD", (("py", "lambda"), ("analysts", "writer"), ("mail", "review"),
                                         ("teams", "app"))):
        d.change(a_, letter)
        d.change(b_, letter)
    m = d.render(s, Box(C.x, C.y, C.w - rail_w - 0.25, C.h), th, name="ct", draft=DRAFT)
    arch.change_key(s, Box(C.r - rail_w, C.y + 0.1, rail_w, C.h - 0.75), CHANGES, th, name="ct.key", head="Changes",
                    spread=True)
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(SKILL / ".cache" / "arch" / "topology.pptx"))
    ap.add_argument("--theme", default=str(SKILL / "themes" / "sigmoid.json"))
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    global DRAFT
    DRAFT = a.draft
    th = Theme.load(a.theme)
    prs = Presentation(str(SKILL / "kit" / "assets" / "base-wide.pptx"))
    prims.bind(th)
    builders = {"deploy": aws_deploy, "azure": azure_deploy, "dr": aws_dr, "ct": current_target}
    metrics = {k: fn(prs, th) for k, fn in builders.items() if not a.only or k in a.only.split(",")}
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sha = package.save(prs, out, title="Topology diagrams", theme=th, manifest={"numbers": {}}, overwrite=True,
                       date="2026-10-04")
    from example_arch import vendor_media
    dj = {"type": "example", "canvas": "wide", "theme": a.theme, "client": None, "spelling": "US",
          "media_allow": vendor_media(out),
          "overrides": {"P15": "DECISIONS.md ruling 21: the topology example is four architecture slides of one "
                               "family by design"},
          "series": [], "deliverable": out.name,
          "build": ["{python}", str(Path(__file__).resolve()), "--theme", a.theme, "--out", "{out}"]}
    (out.parent / "deck.json").write_text(json.dumps(dj, indent=2) + "\n", encoding="utf-8")
    for k, m in metrics.items():
        print("%-8s %s" % (k, {x: y for x, y in m.items() if x not in ("problems", "advisories")}))
        for p in m["problems"] + m["advisories"]:
            print("   !", p)
    print("OK %s sha256 %s" % (out, sha[:12]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
