# Technical diagrams with the engine

Rulings 18, 20 and 21. Every architecture or technical diagram is declared in code and drawn by one of three engine
modules, never hand-placed as tiles. Gate P26 judges the drawing against the measured grammar for its type. The
diagram chooser in `SKILL.md` maps each type to its tag, module and worked example function.

| Module | Draws | Grammars |
|---|---|---|
| `deckkit.arch` (`Diagram`) | nested groups with floating marks and routed flows: cloud reference, L0 and deep dive, deployment, DR, current versus target | `aws`, `azure`, `house` |
| `deckkit.arch_flow` (`Board` and five builders) | pipelines and graphs: CI/CD, MLOps, medallion and lineage inset, events, agent state machine | house |
| `deckkit.arch_seq` (`Sequence`, `DFD`, `C4`) | sequence, Gane-Sarson DFD and threat model, C4 context and container | house |

Every builder measures before drawing and raises (`Overflows`, `GeometryError`, `Capacity`) instead of shrinking or
clamping. `render(..., draft=True)` (arch, arch_seq DFD and C4) or `Board(..., draft=True)` lists what does not fit in
`metrics["problems"]` while iterating; a draft is never shipped. `Diagram.render` returns a metrics dict (`marks`,
`flows`, `labelled`, `badge_only`, `boxed_alone`, `advisories`, `problems` and more): read a count the title states
back from it rather than typing it.

## Shared foundation

- **Field**: `WIDE.content`, 12.40 x 5.99in at y 0.85. No in-canvas title, footer, subtitle or reading instruction.
  Above the cell ceiling (about 45 marks with short captions) split into a master plus deep dives, never shrink type.
- **Corners**: aws and azure frames square; house cards at the canvas radius 0.05in, header tabs 0.06in.
- **Type ladder**, one family, the theme font:

| Level | Size | Weight |
|---|---|---|
| Layer tab, region header bar | 10pt | bold, `paper` on `navy` |
| Boundary or group label | 9pt | aws regular at every level; azure and house bold for the top two levels |
| Node name | 9pt | regular |
| Node role line | 8pt | regular, `ink-muted` |
| Flow label | 8pt, one line, at most 1.30in, at most 4 words (5 in arch_seq) | regular, on a knock-out of the local ground |
| Legend | 9pt | regular |
| Step numeral | 9pt in a 0.30in badge (aws), 8pt in a 0.22in badge (azure, house) | bold, white |

- **Captions**: at most two lines per part (name, role), at most 1.45in wide, broken between words only. A house deep
  dive refuses a name of three words or fewer that wraps.
- **Marks** are the argument. A product mark is a picture whose alt text records `(vendor mark <key>)` or `(brand mark
  <key>)`, at any size; group tabs, corner icons and pins (`*-tab`, `*-corner`, `*-pin`) and actor glyphs
  (`aws/general/*`, `onprem/generic/*`, `generic/*`, the Azure users mark) are not. Node marks are
  `"vendor:<key>"`, `"mark:<key>"` (the registry) or `"glyph:<name>"` (an actor); `arch` also takes `"mono:<letters>"`.
  Icon 0.42in; house platform tier 0.62in (`size=0.62`) for the five to eight anchor products of an L0; dense
  step-down 0.34in. aws and azure use one service size. Marks are cropped to their ink (`a:srcRect`, bytes untouched),
  never recoloured, rotated or redrawn. Monograms last, at most a fifth of the marks.
- **No boxed icons**: a mark floats on its group ground with its caption under it (or beside it, `caption="right"`).
  At most 10% of icons may sit alone in a tile (DFD and sequence exempt). No brand-colour edge on a chip (ruling 21).
- **Routing**: orthogonal, edge to edge, never from a caption, never along a border or another flow, no crossing
  (P26.h), final leg at least 0.15in, at most two bends in arch_flow. A route that cannot be drawn clear raises.
  `align(node, to, axis=)` puts two marks on one line so the flow runs straight.
- **Labels** say what moves: a lowercase noun or verb phrase, an optional protocol after a middot (`brief draft ·
  HTTPS`), never "uses", never a lone protocol. A label sits beside the longest segment that holds it plus 0.12in,
  else on its own knock-out; never wrapped. Gutters that carry labelled flows are 0.55in or wider (`gutter=`).
- **Steps**: numbered 1..N without a gap, at most 12, one badge size, beside the source end. `d.steps({n: text})`
  writes the legend rail, one line per step; the narration goes to speaker notes, never a paragraph panel.
- **Boundaries**: every boundary is labelled. The outer two levels (cloud, account or subscription, region, the
  platform boundary, a trust zone) state a fact after a middot or colon (`group(..., fact=)` or the label itself:
  "Region eu-west-1 · 2 AZs"); inner levels may be glyph plus name. A fact holds for every child. Dashed is logical or
  placement (region, AZ, scaling group, trust zone); solid is ownership or network (cloud, account, VPC, subnet).
  External actors and SaaS sit outside the outermost boundary. Controls that guard a boundary are pinned to its edge
  or corner (`anchor="edge:l|edge:r|edge:t"`, `pin(...)`), never drawn as free services. Nesting at most 4 deep.
- **Legend**: whenever more than one line style is drawn, at most 6 keys (`render(legend="right"|"bottom")`).

### Line kinds

| Kind | `arch` dash | `arch_flow` dash | Meaning |
|---|---|---|---|
| `data` | solid | solid | request or data movement |
| `async` | `dash`, open head | `dash` | event, message, subscribe |
| `control` | `sysDot`, open head | `sysDot` | configuration, control plane |
| `reply` | `sysDash`, 0.75pt, 0.08in beside its request (declare the request first) | | response |
| `private` | `sysDashDot` | | private-endpoint link, keyed in the legend |
| `peering` | `lgDashDot`, both heads, label required | | network peering, the only double head |
| `feedback` | `lgDash`, `accent-deep` in house, perimeter route | `lgDash`, `accent-deep` | retrain, rollback, revise |
| `blocked` | `dashDot`, no-entry glyph before the target | `dash`, no-entry glyph | the forbidden path |
| `conditional` | | `sysDash` | a conditional edge in a state graph |
| hero (`hero=True`) | solid 1.5pt (the kit's connector ceiling; the spec asked 2.0) | | the one path the title claims; hero flows form one chain |

Stroke and head per grammar: aws `#232F3E` 1.25pt open arrow; azure and house `ink-muted` 1.0pt triangle.

## Notation colours

AWS and Azure notation colours are identity colours: registered in each theme's `identity` block, written as srgbClr,
never moved by a client theme (verified 2026-10-03 against the AWS Architecture Icons toolkit of 2026-07-31 and the
Azure Architecture Center reference diagrams; detail in `kit/deckkit/arch.py`'s header). The house grammar uses theme
roles only, so a client theme recolours it.

| Group kind (`group(..., kind)`) | Identity | Stroke |
|---|---|---|
| `aws-cloud` | `aws-cloud` `#232F3E` | solid; also aws flows, badges, hero path |
| `aws-account` | `aws-account` `#E7157B` | solid |
| `aws-region` | `aws-region` `#00A4A6` | `sysDash` |
| `aws-az` | `aws-az` `#00A4A6` | `dash`, label centred on the top edge |
| `aws-vpc` | `aws-vpc` `#8C4FFF` | solid 1.25pt and the corner icon only, never a fill (ruling 21) |
| `aws-public-subnet`, `aws-private-subnet` | `#7AA116`, `#00A4A6` | solid, no fill |
| `aws-security-group` | `aws-security-group` `#DD344C` | solid, label on the top edge |
| `aws-asg` | `aws-asg` `#ED7100` | `dash` |
| `corporate-dc`, `generic` | `aws-corporate-dc`, `aws-generic` `#7D8998` | solid, dashed |
| `azure-region` | `azure-region` `#0070C0` | `dash` 0.75pt |
| `azure-subscription` | `azure-blue` `#0078D4` | solid 1.0pt with the subscription icon |
| `azure-resource-group` | `azure-resource-group` `#7A7A7A` (a house choice) | `dash` |
| `azure-vnet` | `azure-vnet` `#A4CBFB` | a filled ground its subnets tile, label above |
| `azure-subnet` | `azure-subnet` `#BFBFBF` on `azure-subnet-fill` `#F8F8F8` | panel with the NSG shield in its corner |
| `azure-zone` | `azure-zone` `#FFD965` | 1.5pt |
| Azure step badge | `azure-step` `#107C10` (ruling 21) | white numeral |
| house `region`, `band` | `navy` header bar, `rule-strong` frame; a band is a light `card` body (ruling 21: dark logos stay visible) | |
| house `rail` | light `card` with a label tab, `hairline` | |
| house `boundary`, `zone` | `rule-strong` dash (platform frame), `accent-deep` dash (trust zone) | |
| house `section`, `lane` | a hairline-split sub-head; an unframed lane | |

- The VNet, subnet and zone strokes are under 3:1 on white (1.68, 1.84, 1.37). They pass only with a label and a
  corner icon on that boundary (ruling 21).
- aws and azure slides add no hue beyond the notation and the step badge. House slides hold at most three
  structural hues plus neutrals. Product marks are exempt everywhere.
- Medallion tints and a threat red stay off until the user introduces them (ruling 21).

## P26 thresholds per type

The variant's words pick the type: an `arch-*` variant by its words (deploy, network, topology; cicd, release; mlops,
llmops; dfd, threat; dataflow, medallion; lineage; seq, sequence; event; hub; dr, landing; current, target, asis,
tobe; fsm, statemachine, state; c4, context, container; aws; azure), `l0-*` as the L0 master, `house-deep-dive` as the
deep dive, `aws*` and `azure*` as the cloud solutions. Other layered-architecture and solution-architecture slides keep
the legacy floors (16 and 20 marks). "Carried by": label, badge or keyed style (any); label or keyed style; label only.

| Type | Marks | Flows carried | Carried by | Steps | Boundary kinds | Words |
|---|---|---|---|---|---|---|
| aws solution | 20 to 40 | 70% of all | any | 5 to 12 | 3 | 110 to 200 |
| azure solution | 20 to 40 | 70% of all | any | 5 to 10 | 3 | 110 to 200 |
| house L0 master | 25 to 45 | no flows at all | | none | 2 | 120 to 220 |
| house deep dive | 15 to 32 | 80% of all | any | 4 to 10 | 2 | 110 to 200 |
| deployment and network | 18 to 35 | 90% of boundary-crossing | label or keyed | 0 to 8 | 4 | 90 to 180 |
| CI/CD and release | 12 to 24 | 90% of boundary-crossing | label or keyed | 4 to 10 | 2 | 90 to 170 |
| MLOps and LLMOps | 14 to 28 | 85% of all | any | 5 to 10 | 2 | 100 to 190 |
| DFD and threat model | 0 to 12 | 100% | label | every flow | 1 | 70 to 150 |
| data flow, medallion | 20 to 40 | 80% of all | any | 0 to 8 | 2 | 100 to 200 |
| lineage DAG | 0 to 10 | 100% | label | 0 to 8 | 1 | 60 to 200 |
| sequence | 4 to 8 heads | 100% | label | 0 to 16 | 0 | 80 to 160 |
| event-driven | 10 to 22 | 100% | label or keyed | 0 to 6 | 2 | 80 to 160 |
| hub-and-spoke | 7 to 16 | 100% | label or keyed | none | 1 | 70 to 150 |
| DR and landing zone | 18 to 40 | 90% of boundary-crossing | label or keyed | 0 to 8 | 3 | 90 to 190 |
| current versus target | 14 to 40 | 80% of all | any | none | 2 | 90 to 200 |
| agent state machine | 0 to 16 | 100% | label or keyed | none | 0 | 50 to 160 |
| C4 context, container | 0 to 30 | 100% | label or keyed | none | 1 | 70 to 200 |

The other P26 checks hold on every type: every mark captioned; no crossing; a double head only on a labelled
peering; every outer boundary states a fact; every dashed style keyed (at most 6 keys); no orphan mark outside a
platform band (not judged on L0, sequence, DFD, lineage, state); labels and badges collide with nothing; one
component, one mark and one name across the deck's architecture slides; ink at least 75% of a mark. On aws slides no
actor inside the AWS Cloud frame, no regional managed service (Bedrock, S3, DynamoDB, SQS, SNS, EventBridge, SES,
CloudFront) inside a VPC, and every flow crossing the VPC border lands on an edge pin or names its path; on azure
slides no PaaS mark inside a subnet; pins carry no flow. A `"P26:marks"` grant with a source exempts a conceptual
architecture from the mark floor only. The planning values (every word band outside aws and house, every label floor
above 70%, the event and hub rows) are the spec's, not measurements.

## Per type: what the drawing must show

**AWS solution** (`Diagram("aws")`). Actors and SaaS outside the AWS Cloud frame. Cloud, Region, VPC, subnets (an AZ
pair when availability is the point). Managed regional services inside the Region, outside the VPC, reached through
VPC endpoints pinned on the VPC edge (`anchor="edge:l"`); a load balancer and NAT on the edge. A security and
operations band (`band=True`, no flows). 5 to 12 numbered steps with a one-line rail.

**Azure solution** (`Diagram("azure")`). Users left. Region, subscription, VNet (a filled ground), named subnets as
panels with NSG shields. PaaS services outside the VNet, each straight across from its private endpoint in a
private-endpoint subnet, joined by a `private` flow. A shared-services band. Steps in `azure-step` green.

**House L0 master** (`Diagram("house", l0=True)`). Five to seven layers or staggered columns of unequal width (at
least four distinct region top-and-width pairs), a left and right rail for cross-cutting concerns, a full-width
platform band, the client estate outside a dashed platform `boundary`. Two icon tiers. No arrows and no numbers:
`flow()` and `steps()` refuse. Flow detail moves to the deep dives.

**House deep dive** (`Diagram("house")`). One L0 band opened to a slide: three to six regions or sections, flows
between them, a numbered primary path (`hero=True`), a trust `zone` dashed in `accent-deep` with a label that states
its network fact, feedback loops on the perimeter.

**Deployment and network** (`Diagram("aws"|"azure")`). One environment per slide. Region, VPC or VNet, AZ columns
crossing it with identical subnet tiers on one y (`group(..., align_rows=True)`); a cross-AZ service as a `span`
band across at least two AZ columns (`span(id, label, over=[...])`); interface endpoints and the load balancer
pinned; NAT and firewall as nodes on the egress path; at least one `blocked` path; crossings labelled with port or
path (`443 HTTPS`, `PrivateLink`). Azure: hub and spoke VNets joined by a labelled `peering`, Firewall and Bastion in
the hub, a private-endpoint subnet, blocked egress. At most four line styles.

**DR and landing zone** (`Diagram("aws")`). The organisation tree of OUs and accounts as an indented `bus(...,
tree=True)` beside an active and a standby Region, each stating its recovery point and recovery time in its fact.

**Current versus target** (`Diagram` per state, `change(node, letter)`, module `change_key(...)`). Today and the target
on one slide, lettered change markers on both diagrams (P26 fails a letter on one side only) keyed in a rail between
them, the target's hero path drawn.

**CI/CD and release** (`arch_flow.cicd(box, th, spec)`). Left to right in time: the source and tooling account on one
panel, environment accounts as equal columns, gates as nodes on the promotion path (`quality`, `approval`, `health`,
`traffic`; each label a criterion: `SAST clean`, `approval · release lead`, `bake 60 min`) with fail exits, the
artifact digest as one token on a rail (promoted, never rebuilt), a rollback loop on the perimeter, one forbidden
console path as a `blocked` edge. Inter-boundary flows say the literal verb (`git push`, `OIDC token, assume role`).

**MLOps and LLMOps** (`arch_flow.mlops`). Two zones in one segmented frame, the model or prompt registry hinged on the
divider (`register` in, `promote` out); activities as dashed text boxes with no icon; an eval gate with its threshold
and a fail exit; human approval after eval; a canary; online evaluation sampling traces back on the perimeter.

**Data flow, medallion and lineage** (`arch_flow.medallion`). Fixed columns left to right (sources, ingest,
transform, serve, consume); sources as a stacked list; the medallion as one segmented container of Bronze, Silver,
Gold cells; the stream path above the batch path; one excluded record filtered at Silver; hop labels naming the
operation and cadence (`MERGE · dedupe on key`, `hourly`); a lineage inset with an honest `+N more`. Tag it
`arch-medallion`, never with the word lineage (that type is the dataset DAG: tables as nodes, transform jobs as
edges, at most six hops, 0 to 10 marks).

**Event-driven** (`arch_flow.events`). Producers left, the broker centre, consumers right. On a router (EventBridge,
Event Grid, SNS) the node is the event type on the bus, past tense (`brief.drafted`), each consumer edge a rule; on a
log broker (Kafka, Kinesis, Event Hubs) the topic is the node and consumer groups share a frame. A schema registry on
`control` lines, and one dead-letter path labelled with its retry count.

**Agent state machine** (`arch_flow.state_graph`). START, the node path, END; conditional edges dashed and labelled;
a retry loop; a human-review interrupt (`state(..., interrupt=True)`); the services each node calls above or below.

**Sequence** (`arch_seq.Sequence`). Four to eight participants (at most 16 messages) ordered by trust, each head a
mark and a name; messages horizontal and numbered at the label start; every call answered by a reply unless inside
`break`; at least one `alt` or `break` fragment when the sequence argues control; one trust `band(label, first,
last)` with a "name · fact" label; a model's tool request as a `reply` back to the orchestrator.

**DFD and threat model** (`arch_seq.DFD(level="context"|"1"|"2", threat=True)`). Gane-Sarson: processes numbered
(`1` to `n`, `3.1` below), entities on the margins, stores `D1` and on below the process spine; a process at one end
of every flow; a context level has one process and no store. Every flow labelled with the data that moves and
numbered; every flow crossing a trust boundary carries a marker on each intercept and one control chip
(`protocol · auth · encryption`); an out-of-scope element dashed in `ink-muted`.

**C4 context and container** (`arch_seq.C4("context"|"container")`). Context: one system in focus (`accent`), people
(`navy`) and external systems (`card`) around it, every relationship labelled `intent · protocol`. Container: the
system boundary opened into containers, each with a technology line and a 0.28in mark, never a pill per tile.

**Hub-and-spoke** (no builder). One hub card naming its role (`tool gateway · MCP`), six to ten spokes, each ending on
one mark or a small group, every spoke labelled with what moves, no step numbers, one spoke carrying the failure case.
Tag it `arch-hub` and draw it with `Diagram("house")`.

## Defaults from the spec (ruling 21)

- The house platform band is a light `card` under a navy or near-black header bar, so dark logos stay visible.
- No brand-colour edge on a logo chip: the mark carries the brand (the left-accent ban).
- The faint Azure strokes pass only with a label and a corner icon.
- Medallion and threat colours stay off until the user introduces them.
- AWS VPC purple is a 1.25pt stroke and corner icon on AWS-notation slides only, never a fill.
- Azure step badges are `#107C10` green.
