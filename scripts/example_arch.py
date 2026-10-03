"""Four architecture slides drawn by deckkit.arch on the fictional Quillmont brief service (ruling 18).

    $PY scripts/example_arch.py [--out .cache/arch/arch.pptx] [--theme themes/sigmoid.json]

  1 solution-architecture:aws-reference      the service in the AWS notation: actors outside the cloud, a Region, a
                                             VPC with private subnets, regional services reached through endpoints,
                                             numbered steps with a legend rail
  2 solution-architecture:azure-reference    the same service in the Azure notation: subscription, resource group,
                                             VNet, subnets and a private endpoint, numbered steps
  3 layered-architecture:l0-house           the house L0 master: six layers, a platform band, product marks only,
                                             no arrows and no numbering
  4 solution-architecture:house-deep-dive    the house grammar with labelled flows between regions

Stack canon: Decks-For-Visuals/acceptance/showcase/canon.json "stack". Fictional client and figures; nothing here
names a real client. The deck.json beside the output grants P15 (four slides of one family is the example's point).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "kit"))

from pptx import Presentation  # noqa: E402

from deckkit import arch, package, prims, tag  # noqa: E402
from deckkit.canvas import WIDE, Box  # noqa: E402
from deckkit.text import title  # noqa: E402
from deckkit.theme import Theme  # noqa: E402

C = WIDE.content
DRAFT = False          # --draft lists what does not fit instead of raising; never for a deck that ships

# one name and role per component across the four slides (house rule 13; gate P26.v holds name to mark)
N = {
    "collect": ("AWS Lambda", "collectors"),
    "sched": ("EventBridge Scheduler", "weekly run"),
    "s3": ("Amazon S3", None),
    "search": ("OpenSearch Service", "claim index"),
    "bedrock": ("Amazon Bedrock", "Claude models"),
    "claude": ("Claude", "model"),
    "ddb": ("Amazon DynamoDB", "decisions"),
    "ses": ("Amazon SES", "Monday email"),
    "scan": ("Scan agent", None),
    "writer": ("Writer agent", None),
    "review": ("Review app", None),
    "rds": ("Amazon RDS", "brief ledger"),
    "standby": ("Amazon RDS", "standby"),
    "cache": ("Amazon ElastiCache", "review state"),
    "cdn": ("Amazon CloudFront", None),
    "dns": ("Amazon Route 53", "DNS"),
    "alb": ("Load balancer", "ALB"),
    "nat": ("NAT gateway", None),
    "actions": ("GitHub Actions", "image builds"),
    "langfuse": ("Langfuse", "traces"),
    "cognito": ("Amazon Cognito", "sign-on"),
    "iam": ("AWS IAM", "roles"),
    "waf": ("AWS WAF", "web ACL"),
    "kms": ("AWS KMS", "encryption"),
    "secrets": ("AWS Secrets Manager", None),
    "watch": ("Amazon CloudWatch", "metrics"),
    "xray": ("AWS X-Ray", "traces"),
    "trail": ("AWS CloudTrail", "audit log"),
    "ecr": ("Amazon ECR", "images"),
}
# the house slides: one name, role and mark per component across the L0 and the deep dive (P26.v)
SOURCES = (("web", "vendor:aws/general/internet-alt1", "Public web", "press, congress"),
           ("registries", "glyph:file-search", "Trial feeds", "registries"),
           ("payers", "glyph:landmark", "Payers", "coverage notices"),
           ("media", "glyph:megaphone", "Congress media", "abstracts"),
           ("partners", "glyph:folder-open", "Partner feeds", "file drops"))
HM = {
    "reps": "vendor:aws/general/users", "app": "vendor:programming/framework/react",
    "portal": "vendor:programming/framework/nextjs", "teams": "vendor:saas/chat/teams", "crm": "glyph:contact",
    "cognito": "vendor:aws/security/cognito", "iam": "vendor:aws/security/identity-and-access-management-iam",
    "kms": "vendor:aws/security/key-management-service", "secrets": "vendor:aws/security/secrets-manager",
    "waf": "vendor:aws/security/waf", "langfuse": "mark:langfuse-icon", "watch": "vendor:aws/management/cloudwatch",
    "xray": "vendor:aws/devtools/x-ray", "trail": "vendor:aws/management/cloudtrail",
    "config": "vendor:aws/management/config", "evals": "vendor:aws/ml/sagemaker-model", "sched": "vendor:aws/integration/eventbridge-scheduler",
    "collect": "vendor:aws/compute/lambda", "flow": "vendor:aws/integration/step-functions",
    "ocr": "vendor:aws/ml/textract", "queue": "vendor:aws/integration/simple-queue-service-sqs",
    "nlp": "vendor:aws/ml/comprehend", "s3": "vendor:aws/storage/simple-storage-service-s3",
    "glue": "vendor:aws/analytics/glue", "search": "vendor:aws/analytics/amazon-opensearch-service",
    "rds": "vendor:aws/database/rds", "bedrock": "vendor:aws/ml/bedrock", "claude": "mark:claude-spark",
    "glacier": "vendor:aws/storage/s3-glacier",
    "graph": "mark:langgraph-logo", "fargate": "vendor:aws/compute/fargate",
    "scan": "vendor:aws/compute/elastic-container-service-task",
    "writer": "vendor:aws/compute/elastic-container-service-task", "api": "vendor:aws/network/api-gateway",
    "ui": "vendor:programming/framework/react", "ddb": "vendor:aws/database/dynamodb",
    "cdn": "vendor:aws/network/cloudfront", "ses": "vendor:aws/engagement/simple-email-service-ses",
    "actions": "vendor:onprem/ci/github-actions", "pipeline": "vendor:aws/devtools/codepipeline",
    "ecr": "vendor:aws/compute/ec2-container-registry", "tf": "vendor:onprem/iac/terraform",
    "py": "vendor:programming/language/python", "lgsdk": "mark:langchain-logo",
}
HN = {
    "reps": ("Field reps", "1,200 reps"), "app": ("Field app", "React Native"), "portal": ("Web portal", "Next.js"),
    "teams": ("Microsoft Teams", "alerts"), "crm": ("CRM", "account plans"),
    "cognito": ("Cognito", "sign-on"), "iam": ("AWS IAM", "roles"), "kms": ("AWS KMS", "keys"),
    "secrets": ("Secrets", None), "waf": ("AWS WAF", "web ACL"),
    "langfuse": ("Langfuse", "traces"), "watch": ("CloudWatch", "metrics"), "xray": ("AWS X-Ray", "tracing"),
    "trail": ("CloudTrail", "audit"), "config": ("AWS Config", "drift"), "evals": ("Evaluations", "golden set"),
    "sched": ("EventBridge", "schedule"), "collect": ("Lambda", "collectors"),
    "flow": ("Step Functions", "pipeline"), "ocr": ("Textract", "PDF text"), "queue": ("Amazon SQS", "retries"),
    "nlp": ("Comprehend", "entities"),
    "s3": ("Amazon S3", "signal lake"), "glue": ("AWS Glue", "catalog"),
    "search": ("OpenSearch", "claim index"), "rds": ("RDS", "brief ledger"),
    "glacier": ("S3 Glacier", "archive"),
    "bedrock": ("Bedrock", "model access"), "claude": ("Claude", "drafting model"),
    "graph": ("LangGraph", "agent graphs"), "fargate": ("AWS Fargate", "agent tasks"),
    "scan": ("Scan agent", None), "writer": ("Writer agent", None),
    "api": ("API Gateway", "brief API"), "ui": ("Review app", "React"), "ddb": ("DynamoDB", "decisions"),
    "cdn": ("CloudFront", "brief site"), "ses": ("Amazon SES", "Monday email"),
    "actions": ("GitHub Actions", "CI builds"), "pipeline": ("CodePipeline", "dev, test, prod"),
    "ecr": ("Amazon ECR", "images"), "tf": ("Terraform", "infrastructure"), "py": ("Python", "agent code"),
    "lgsdk": ("LangChain", "tool calls"),
}
# the ten steps are one service: the AWS and the Azure slides number the same path (house rule 13)
STEPS = {1: "Pull signals", 2: "Land raw signals", 3: "Read privately", 4: "Index claims", 5: "Draft the brief",
         6: "Save the draft", 7: "Request review", 8: "Decide in the app", 9: "Read the brief", 10: "Ship images"}
AZ = {
    "func": "vendor:azure/compute/function-apps", "appgw": "vendor:azure/network/application-gateway",
    "scan": "vendor:azure/other/worker-container-app", "writer": "vendor:azure/other/worker-container-app",
    "review": "vendor:azure/compute/container-apps", "pe": "vendor:azure/other/private-endpoints",
    "blob": "vendor:azure/storage/storage-accounts", "search": "vendor:azure/aimachinelearning/cognitive-search",
    "openai": "vendor:azure/aimachinelearning/azure-openai", "cosmos": "vendor:azure/databases/azure-cosmos-db",
    "vault": "vendor:azure/security/key-vaults", "acr": "vendor:azure/compute/container-registries",
    "mi": "vendor:azure/identity/entra-managed-identities", "entra": "vendor:azure/identity/azure-active-directory",
    "dns": "vendor:azure/network/dns-private-zones", "monitor": "vendor:azure/managementgovernance/monitor",
    "insights": "vendor:azure/monitor/application-insights",
    "logs": "vendor:azure/managementgovernance/log-analytics-workspaces",
    "ddos": "vendor:azure/network/ddos-protection-plans",
}
AZN = {
    "func": ("Azure Functions", "collectors"), "appgw": ("Application Gateway", "WAF"),
    "scan": ("Scan agent", None), "writer": ("Writer agent", None), "review": ("Review app", None),
    "blob": ("Storage account", "signal lake", "Storage PE"),
    "search": ("Azure AI Search", "claim index", "Search PE"),
    "openai": ("Azure OpenAI", "drafting model", "OpenAI PE"),
    "cosmos": ("Azure Cosmos DB", "brief ledger", "Cosmos DB PE"), "vault": ("Key Vault", "secrets", "Key Vault PE"), "acr": ("Container Registry", None), "mi": ("Managed identity", None),
    "entra": ("Microsoft Entra ID", None), "dns": ("Private DNS zones", None), "monitor": ("Azure Monitor", None),
    "insights": ("Application Insights", None), "logs": ("Log Analytics", None),
    "ddos": ("DDoS Protection", None),
}
MARK = {
    "collect": "vendor:aws/compute/lambda", "actions": "vendor:onprem/ci/github-actions",
    "langfuse": "mark:langfuse-icon", "dns": "vendor:aws/network/route-53", "cdn": "vendor:aws/network/cloudfront",
    "alb": "vendor:aws/network/elb-application-load-balancer", "nat": "vendor:aws/network/nat-gateway",
    "s3": "vendor:aws/storage/simple-storage-service-s3", "bedrock": "vendor:aws/ml/bedrock",
    "claude": "mark:claude-spark", "ddb": "vendor:aws/database/dynamodb",
    "ses": "vendor:aws/engagement/simple-email-service-ses",
    "scan": "vendor:aws/compute/elastic-container-service-task",
    "writer": "vendor:aws/compute/elastic-container-service-task",
    "review": "vendor:aws/compute/elastic-container-service-task",
    "search": "vendor:aws/analytics/amazon-opensearch-service", "rds": "vendor:aws/database/rds",
    "standby": "vendor:aws/database/rds", "cache": "vendor:aws/database/elasticache-for-redis", "sched": "vendor:aws/integration/eventbridge-scheduler",
    "cognito": "vendor:aws/security/cognito", "iam": "vendor:aws/security/identity-and-access-management-iam",
    "waf": "vendor:aws/security/waf", "kms": "vendor:aws/security/key-management-service",
    "secrets": "vendor:aws/security/secrets-manager", "watch": "vendor:aws/management/cloudwatch",
    "xray": "vendor:aws/devtools/x-ray", "trail": "vendor:aws/management/cloudtrail",
    "ecr": "vendor:aws/compute/ec2-container-registry",
}


def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[0])


# ---------------------------------------------------------------------------------------------- 1 AWS

def aws(prs, th):
    s = blank(prs)
    tag.tag(s, "solution-architecture", "aws-reference")
    title(s, "One AWS Region runs the brief service behind private endpoints",
          keywords=("private endpoints",), canvas=WIDE, theme=th)
    d = arch.Diagram("aws", grid=(3, 3), weights=[0.95, 10.4, 1.05], head_air=0.13)
    # outside the cloud: sources and CI on the left, the people and the trace store on the right
    d.node("sources", "vendor:aws/general/internet-alt1", "Public sources", at=(0, 0), anchor="left")
    d.node("reps", "vendor:aws/general/users", "Field reps", at=(2, 0))
    d.node("medical", "vendor:aws/general/user", "Medical reviewers", at=(2, 1))
    d.group("saas", "generic", "SaaS · CI", at=(2, 2, 1, 1), grid=(1, 2), drop=0.3)
    d.node("langfuse", MARK["langfuse"], *N["langfuse"], group="saas", at=(0, 0))
    d.node("actions", MARK["actions"], *N["actions"], group="saas", at=(0, 1))
    d.group("cloud", "aws-cloud", "AWS Cloud · production account", at=(1, 0, 1, 3), grid=(2, 1),
            weights=[9.65, 0.95])
    d.node("cdn", MARK["cdn"], *N["cdn"], group="cloud", at=(1, 0))
    d.group("region", "aws-region", "Region eu-west-1 · 2 AZs", parent="cloud", at=(0, 0, 1, 1), grid=(3, 2),
            weights=[1.75, 6.55, 0.8], row_gap=[0.08])
    d.group("edge", "lane", None, parent="region", at=(0, 0, 1, 1), grid=(1, 4))
    d.node("collect", MARK["collect"], *N["collect"], group="edge", at=(0, 0), caption="right", anchor="left")
    d.node("s3", MARK["s3"], *N["s3"], group="edge", at=(0, 1), anchor="left")
    d.node("bedrock", MARK["bedrock"], *N["bedrock"], group="edge", at=(0, 3), anchor="left")
    d.group("vpc", "aws-vpc", "VPC 10.20.0.0/16", parent="region", at=(1, 0, 1, 1), grid=(2, 1), weights=[1.22, 1])
    d.group("az1", "aws-az", "Availability Zone 1", parent="vpc", at=(0, 0, 1, 1), grid=(2, 1), weights=[1.1, 1.15])
    d.group("app1", "aws-private-subnet", "Agents", parent="az1", at=(0, 0, 1, 1), grid=(1, 2))
    d.group("data1", "aws-private-subnet", "Data", parent="az1", at=(1, 0, 1, 1), grid=(1, 2))
    d.group("az2", "aws-az", "Availability Zone 2", parent="vpc", at=(1, 0, 1, 1), grid=(2, 1), weights=[1.2, 1])
    d.group("data2", "aws-private-subnet", "Data", parent="az2", at=(0, 0, 1, 1), grid=(1, 2))
    d.group("app2", "aws-private-subnet", "Agents", parent="az2", at=(1, 0, 1, 1), grid=(1, 2))
    for nid, grp, at in (("search", "data1", (0, 0)), ("standby", "data2", (0, 1)), ("cache", "data2", (0, 0))):
        d.node(nid, MARK[nid], *N[nid], group=grp, at=at, anchor="left")
    d.node("rds", MARK["rds"], *N["rds"], group="data1", at=(0, 1))
    d.node("scan", MARK["scan"], *N["scan"], group="app1", at=(0, 0))
    d.node("writer", MARK["writer"], *N["writer"], group="app1", at=(0, 1))
    d.node("review", MARK["review"], *N["review"], group="app2", at=(0, 0), anchor="right")
    d.node("s3ep", "vendor:aws/network/endpoint", "S3 endpoint", "PrivateLink", group="vpc", at=(0, 0),
           anchor="edge:l")
    d.node("brep", "vendor:aws/network/endpoint", "Bedrock endpoint", "PrivateLink", group="vpc", at=(0, 0),
           anchor="edge:l")
    d.node("alb", MARK["alb"], *N["alb"], group="vpc", at=(1, 0), anchor="edge:r")
    d.node("nat", MARK["nat"], *N["nat"], group="vpc", at=(1, 0), anchor="edge:r")
    d.group("ops", "generic", "Security and operations", parent="region", at=(0, 1, 3, 1), grid=(6, 1), band=True)
    for k, nid in enumerate(("cognito", "waf", "kms", "watch", "xray", "ecr")):
        d.node(nid, MARK[nid], N[nid][0], group="ops", at=(k, 0), caption="right", size=0.34)
    for nid, to, axis in (("s3", "scan", "y"), ("s3ep", "scan", "y"), ("bedrock", "writer", "y"),
                          ("brep", "writer", "y"),
                          ("alb", "review", "y"), ("cdn", "review", "y"), ("medical", "review", "y"),
                          ("nat", "standby", "y"), ("sources", "collect", "y")):
        d.align(nid, to, axis=axis)
    d.flow("sources", "collect", "feeds", step=1)
    d.flow("collect", "s3", step=2)
    d.flow("s3", "s3ep", "raw signals", step=3)
    d.flow("s3ep", "scan")
    d.flow("scan", "search", step=4)
    d.flow("writer", "brep", step=5)
    d.flow("brep", "bedrock", "prompt")
    d.flow("writer", "rds", step=6)
    d.flow("rds", "standby", kind="async")
    d.flow("medical", "cdn", step=7)
    d.flow("reps", "cdn", "read briefs", step=9)
    d.flow("cdn", "alb", "origin")
    d.flow("alb", "review")
    d.flow("review", "cache", step=8)
    d.flow("nat", "langfuse", "traces")
    d.flow("actions", "ecr", step=10)
    d.steps(STEPS)
    return d.render(s, C, th, name="aws", legend="bottom", legend_h=0.31, legend_cols=10, draft=DRAFT)


# ---------------------------------------------------------------------------------------------- 2 Azure

def azure(prs, th):
    s = blank(prs)
    tag.tag(s, "solution-architecture", "azure-reference")
    title(s, "The same brief service runs on Azure behind private endpoints",
          keywords=("private endpoints",), canvas=WIDE, theme=th)
    d = arch.Diagram("azure", grid=(3, 3), weights=[1.0, 8.6, 1.0], head_air=0.15)
    d.node("sources", "glyph:globe", "Internet sources", at=(0, 0), anchor="left")
    d.node("reps", "vendor:azure/identity/users", "Field reps", at=(0, 1), anchor="left")
    d.node("medical", "vendor:azure/identity/users", "Medical reviewers", at=(0, 2), anchor="left")
    d.node("actions", MARK["actions"], *N["actions"], at=(2, 0))
    d.group("region", "azure-region", "Region East US 2 · zone-redundant", at=(1, 0, 1, 3), grid=(1, 1))
    d.group("sub", "azure-subscription", "Subscription: production · brief service", parent="region",
            at=(0, 0, 1, 1), grid=(3, 1), weights=[5.4, 1.62, 1.68])
    d.group("vnet", "azure-vnet", "Virtual network 10.30.0.0/16", parent="sub", at=(0, 0, 1, 1), grid=(3, 2),
            weights=[1.5, 1.85, 1.5])
    d.group("integ", "azure-subnet", "Integration", parent="vnet", at=(0, 0, 1, 1), grid=(1, 1))
    d.node("func", AZ["func"], *AZN["func"], group="integ", at=(0, 0))
    d.group("gw", "azure-subnet", "Gateway", parent="vnet", at=(0, 1, 1, 1), grid=(1, 1))
    d.node("appgw", AZ["appgw"], *AZN["appgw"], group="gw", at=(0, 0))
    d.group("apps", "azure-subnet", "Agents", parent="vnet", at=(1, 0, 1, 2), grid=(1, 3))
    for r, nid in enumerate(("scan", "writer", "review")):
        d.node(nid, AZ[nid], *AZN[nid], group="apps", at=(0, r), anchor="left")
    d.group("pes", "azure-subnet", "Endpoints", parent="vnet", at=(2, 0, 1, 2), grid=(1, 5))
    d.group("paas", "lane", None, parent="sub", at=(1, 0, 1, 1), grid=(1, 5))
    for r, (pid, nid) in enumerate((("pe-blob", "blob"), ("pe-search", "search"), ("pe-ai", "openai"),
                                    ("pe-cosmos", "cosmos"), ("pe-vault", "vault"))):
        d.node(pid, AZ["pe"], AZN[nid][2], group="pes", at=(0, r))
        d.node(nid, AZ[nid], *AZN[nid][:2], group="paas", at=(0, r), caption="right", anchor="left")
        d.align(nid, pid)
    d.group("ops", "generic", "Shared services", parent="sub", at=(2, 0, 1, 1), grid=(1, 8), band=True)
    for k, nid in enumerate(("acr", "mi", "entra", "dns", "ddos", "monitor", "insights", "logs")):
        d.node(nid, AZ[nid], AZN[nid][0], group="ops", at=(0, k), caption="left", anchor="right", size=0.34)
    for nid, to in (("func", "pe-blob"), ("scan", "pe-search"), ("writer", "pe-ai"), ("medical", "appgw"),
                    ("actions", "acr")):
        d.align(nid, to)
    d.flow("sources", "func", "feeds", step=1)
    d.flow("func", "pe-blob", "raw signals", step=2)
    d.flow("scan", "pe-blob", "read", step=3)
    d.flow("scan", "pe-search", "claims", step=4)
    d.flow("writer", "pe-ai", "prompt", step=5)
    d.flow("writer", "pe-cosmos", "draft", step=6)
    d.flow("medical", "appgw", step=7)
    d.flow("appgw", "review", step=8)
    d.flow("review", "pe-cosmos", "decision")
    d.flow("reps", "appgw", step=9)
    d.flow("actions", "acr", step=10)
    for pid, nid in (("pe-blob", "blob"), ("pe-search", "search"), ("pe-ai", "openai"), ("pe-cosmos", "cosmos"),
                     ("pe-vault", "vault")):
        d.flow(pid, nid, kind="private")
    d.steps(STEPS)
    return d.render(s, C, th, name="azure", legend="right", legend_w=1.6, draft=DRAFT)


# ---------------------------------------------------------------------------------------------- 3 house L0

def l0(prs, th):
    s = blank(prs)
    tag.tag(s, "layered-architecture", "l0-house")
    title(s, "Four platform layers carry every brief from public signal to field rep",
          keywords=("Four platform layers",), canvas=WIDE, theme=th)
    d = arch.Diagram("house", l0=True, grid=(3, 1), weights=[1.1, 10.2, 1.1], icon=0.40, head_air=0.12)
    d.group("sources", "region", "Sources", at=(0, 0, 1, 1), grid=(1, 5))
    for r, (nid, mark, name, role) in enumerate(SOURCES):
        d.node(nid, mark, name, group="sources", at=(0, r))
    d.group("field", "region", "Field", at=(2, 0, 1, 1), grid=(1, 5))
    for r, nid in enumerate(("reps", "app", "portal", "teams", "crm")):
        d.node(nid, HM[nid], HN[nid][0], group="field", at=(0, r))
    d.group("plat", "boundary", "Brief platform · one AWS account, eu-west-1", at=(1, 0, 1, 1), grid=(6, 3),
            weights=[1.15, 1.7, 1.65, 2.05, 2.2, 1.15], row_gap=[0.03, 0.03])
    d.group("idrail", "rail", "Identity", parent="plat", at=(0, 0, 1, 2), grid=(1, 4))
    for r, nid in enumerate(("cognito", "iam", "kms", "secrets")):
        d.node(nid, HM[nid], *HN[nid][:1], group="idrail", at=(0, r), size=0.34)
    d.group("obsrail", "rail", "Operations", parent="plat", at=(5, 0, 1, 2), grid=(1, 4))
    for r, nid in enumerate(("langfuse", "xray", "trail", "config")):
        d.node(nid, HM[nid], *HN[nid][:1], group="obsrail", at=(0, r), size=0.34)
    d.group("ingest", "region", "Ingest", parent="plat", at=(1, 0, 2, 1), grid=(3, 2))
    for k, nid in enumerate(("sched", "collect", "flow", "queue", "ocr", "nlp")):
        d.node(nid, HM[nid], HN[nid][0], group="ingest", at=(k % 3, k // 3))
    d.group("store", "region", "Store", parent="plat", at=(3, 0, 2, 1), grid=(2, 1),
            weights=[1, 1.3])
    d.group("lake", "section", "Lake", parent="store", at=(0, 0, 1, 1), grid=(2, 1))
    d.node("s3", HM["s3"], *HN["s3"], group="lake", at=(0, 0), size=0.62)
    d.node("glue", HM["glue"], *HN["glue"], group="lake", at=(1, 0))
    d.group("index", "section", "Indexes", parent="store", at=(1, 0, 1, 1), grid=(2, 1))
    d.node("search", HM["search"], *HN["search"], group="index", at=(0, 0), size=0.62)
    d.node("rds", HM["rds"], *HN["rds"], group="index", at=(1, 0))
    d.group("agents", "region", "Agents", parent="plat", at=(1, 1, 3, 1), grid=(2, 1), weights=[3, 2])
    d.group("models", "section", "Models", parent="agents", at=(0, 0, 1, 1), grid=(3, 1))
    d.node("bedrock", HM["bedrock"], *HN["bedrock"], group="models", at=(0, 0), size=0.62)
    d.node("claude", HM["claude"], *HN["claude"], group="models", at=(1, 0))
    d.node("graph", HM["graph"], *HN["graph"], group="models", at=(2, 0))
    d.group("runtime", "section", "Agents on ECS", parent="agents", at=(1, 0, 1, 1), grid=(2, 1))
    for k, nid in enumerate(("scan", "writer")):
        d.node(nid, HM[nid], *HN[nid], group="runtime", at=(k, 0))
    d.group("review", "region", "Review and serve", parent="plat", at=(4, 1, 1, 1), grid=(2, 2))
    for k, nid in enumerate(("api", "ui", "ddb", "cdn")):
        d.node(nid, HM[nid], HN[nid][0], group="review", at=(k % 2, k // 2))
    d.group("band", "band", "Delivery: build, test, release", parent="plat", at=(0, 2, 6, 1), grid=(6, 1))
    for k, nid in enumerate(("actions", "pipeline", "ecr", "tf", "py", "watch")):
        d.node(nid, HM[nid], HN[nid][0], group="band", at=(k, 0), caption="right", size=0.34)
    return d.render(s, C, th, name="l0", draft=DRAFT)


# ---------------------------------------------------------------------------------------------- 4 house deep dive

def deep(prs, th):
    s = blank(prs)
    tag.tag(s, "solution-architecture", "house-deep-dive")
    title(s, "Six numbered hops take a public signal to an approved brief",
          keywords=("Six numbered hops",), canvas=WIDE, theme=th)
    d = arch.Diagram("house", grid=(3, 1), weights=[1.15, 10.1, 1.15], head_air=0.14)
    d.group("sources", "lane", "Sources", at=(0, 0, 1, 1), grid=(1, 2))
    for r, (nid, mark, name, role) in enumerate(SOURCES[:2]):
        d.node(nid, mark, name, role, group="sources", at=(0, r))
    d.group("field", "lane", "Field", at=(2, 0, 1, 1), grid=(1, 2))
    for r, nid in enumerate(("app", "reps")):
        d.node(nid, HM[nid], *HN[nid], group="field", at=(0, r))
    d.group("acct", "boundary", "AWS account: production · eu-west-1", at=(1, 0, 1, 1), grid=(3, 2),
            weights=[2.45, 4.35, 1.5], gutter=0.62, row_gap=[0.08])
    d.group("ingest", "region", "Ingest and land", parent="acct", at=(0, 0, 1, 1), grid=(2, 2))
    d.node("collect", HM["collect"], *HN["collect"], group="ingest", at=(0, 0), anchor="right")
    d.node("s3", HM["s3"], *HN["s3"], group="ingest", at=(1, 0), anchor="right")
    d.node("sched", HM["sched"], *HN["sched"], group="ingest", at=(0, 1), anchor="right")
    d.group("zone", "zone", "Agent zone: private subnets, egress through an allow-list", parent="acct",
            at=(1, 0, 1, 1), grid=(2, 1), weights=[2.6, 1.35], gutter=0.32, drop=0.12)
    d.group("agents", "region", "Agents", parent="zone", at=(0, 0, 1, 1), grid=(1, 2))
    d.group("fargate", "section", "ECS Fargate", parent="agents", at=(0, 0, 1, 1), grid=(2, 1))
    d.node("scan", HM["scan"], *HN["scan"], group="fargate", at=(0, 0), anchor="right")
    d.node("writer", HM["writer"], *HN["writer"], group="fargate", at=(1, 0))
    d.group("models", "section", "Amazon Bedrock", parent="agents", at=(0, 1, 1, 1), grid=(2, 1))
    d.node("claude", HM["claude"], *HN["claude"], group="models", at=(0, 0))
    d.node("bedrock", HM["bedrock"], *HN["bedrock"], group="models", at=(1, 0))
    d.group("data", "region", "Data", parent="zone", at=(1, 0, 1, 1), grid=(1, 2), drop=0.30)
    for r, nid in enumerate(("search", "rds")):
        d.node(nid, HM[nid], *HN[nid], group="data", at=(0, r))
    d.group("review", "region", "Review", parent="acct", at=(2, 0, 1, 1), grid=(1, 2))
    for r, nid in enumerate(("ui", "api")):
        d.node(nid, HM[nid], *HN[nid], group="review", at=(0, r))
    d.group("band", "band", "Platform: operations and delivery", parent="acct", at=(0, 1, 3, 1), grid=(6, 1))
    for k, nid in enumerate(("watch", "secrets", "cognito", "glue", "glacier", "langfuse")):
        d.node(nid, HM[nid], HN[nid][0], group="band", at=(k, 0), caption="right", size=0.34)
    for nid, to in (("search", "scan"), ("s3", "scan"), ("collect", "s3"), ("web", "collect"), ("api", "rds"),
                    ("app", "ui")):
        d.align(nid, to)
    d.flow("web", "collect", step=1)
    d.flow("registries", "collect", "updates")
    d.flow("sched", "collect", "weekly run", kind="async")
    d.flow("collect", "s3", step=2)
    d.flow("s3", "scan", "new files", step=3)
    d.flow("scan", "search", "claims", step=4, over=True)
    d.flow("writer", "bedrock", step=5, bend=0.2)
    d.flow("bedrock", "claude", "model call")
    d.flow("writer", "rds")
    d.flow("rds", "api", "for review", step=6)
    d.flow("api", "ui", "queue")
    d.flow("ui", "app")
    d.flow("app", "reps", "brief")
    d.steps({1: "Collect public signals", 2: "Land raw files", 3: "Scan new files", 4: "Index cited claims",
             5: "Draft on Bedrock", 6: "Send for review"})
    return d.render(s, C, th, name="deep", legend="bottom", legend_h=0.31, legend_cols=6, draft=DRAFT)


def vendor_media(deck: Path) -> dict:
    """{sha256: reason} for every embedded picture that is a registered vendor mark, byte for byte. Gate P18 matches
    these official icons against the reference decks, which embed the same public artwork; P22 has already verified
    each one against kit/assets/vendor_hashes.json, so the allowance names the mark and that check."""
    import hashlib
    import zipfile
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
    ap.add_argument("--out", default=str(SKILL / ".cache" / "arch" / "arch.pptx"))
    ap.add_argument("--theme", default=str(SKILL / "themes" / "sigmoid.json"))
    ap.add_argument("--draft", action="store_true")
    a = ap.parse_args()
    global DRAFT
    DRAFT = a.draft
    th = Theme.load(a.theme)
    prs = Presentation(str(SKILL / "kit" / "assets" / "base-wide.pptx"))
    prims.bind(th)
    metrics = {"aws": aws(prs, th), "azure": azure(prs, th), "l0": l0(prs, th), "deep": deep(prs, th)}
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sha = package.save(prs, out, title="Architecture engine", theme=th, manifest={"numbers": {}}, overwrite=True,
                       date="2026-10-03")
    dj = {"type": "example", "canvas": "wide", "theme": a.theme, "client": None, "spelling": "US",
          "media_allow": vendor_media(out),
          "overrides": {"P15": "DECISIONS.md ruling 18: the engine's example deck is four architecture slides of one "
                               "family by design"},
          "series": [], "deliverable": out.name,
          "build": ["{python}", str(Path(__file__).resolve()), "--theme", a.theme, "--out", "{out}"]}
    (out.parent / "deck.json").write_text(json.dumps(dj, indent=2) + "\n", encoding="utf-8")
    for k, m in metrics.items():
        print("%-6s %s" % (k, m))
    print("OK %s sha256 %s" % (out, sha[:12]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
