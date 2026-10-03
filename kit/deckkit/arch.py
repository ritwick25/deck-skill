"""Architecture diagrams: a declared diagram drawn in one grammar (ruling 18).

    d = arch.Diagram("aws", grid=(12, 6))
    d.group("cloud", "aws-cloud", "AWS Cloud", at=(2, 0, 10, 6), grid=(8, 4))
    d.node("bedrock", "vendor:aws/ml/bedrock", "Amazon Bedrock", "Claude models", group="cloud", at=(6, 1))
    d.flow("agents", "bedrock", label="prompt and sources", step=4)
    d.steps({4: "The writer agent drafts the brief from cited sources"})
    metrics = d.render(slide, box, theme)

The engine makes the drawing the references make, and refuses the one they do not:
  * marks float on the group ground with their caption under them. There is no card per icon: nothing here draws a
    box around a single mark (gate P26 (b));
  * every flow runs orthogonally from the edge of one mark to the edge of another, never from a caption (P06, P26),
    straight when the two marks align, else one elbow through the gutter between cells; a route that would cross a
    mark, a caption or a group header is refused, never drawn;
  * a flow carries what moves (an 8pt label on a paper knock-out beside its longest segment) and, optionally, a
    numbered step badge beside its source end that the legend rail explains (P26 (c));
  * l0=True is the L0 master: no arrows and no numbering (CLAUDE.md section 8). flow() and steps() refuse;
  * every caption and label is measured with deckkit.measure before anything is drawn. A caption that needs more than
    two lines per part raises Overflows: type is never shrunk and nothing is clamped. A group that declares more
    auto-placed nodes than it has free cells draws a "+N more" chip counted against the declared set, and the chip is
    measured too (CLAUDE.md section 8).

Layout. Everything sits on measured grids. The diagram's grid divides the drawing area; a group sits on its parent's
grid (or the diagram's) by at=(col, row, cols, rows), and its own grid=(cols, rows) divides its interior after its tab
or header. Columns divide the width evenly. Rows are sized by their content (a node's icon and caption, a child
group's natural height); the room left over goes between rows, so a group hugs its content and a tall rail spreads its
marks from its top to its foot. A node is centred in its cell; the icons of one row of a group share one centre line.

Grammars and their notation colours. Every aws-* and azure-* colour is an identity colour of the notation: registered
in the theme's "identity" block with its reason, written as srgbClr, never moved by a client theme. Text is never set
on a notation colour except the step badge's white numeral, which clears 4.5:1 (gate P25).

  Verified 2026-10-03 against the official AWS Architecture Icons PowerPoint toolkit
  (AWS-Architecture-Icons-Deck_For-Light-BG_07312026.pptx, from aws.amazon.com/architecture/icons, release 07/31/2026),
  slide 25 "Groups 1/5", read from the group shapes' own XML:
    AWS Cloud            border tx1 (black) solid; group icon #242F3E. Drawn here in #232F3E, AWS Squid Ink, the dk2
                         of the toolkit's own theme (a 1-unit difference from the icon's #242F3E).
    AWS account          #E7157B solid
    Region               #00A4A6 sysDash
    Availability Zone    #00A4A6 dash, no group icon (the brief's starting value #147EBA is the pre-2023 notation;
                         the toolkit draws AZs in #00A4A6)
    VPC                  #8C4FFF solid
    Private subnet       #00A4A6 solid, no fill (the brief's #E6F6F7 fill is not in the toolkit: groups carry no fill)
    Public subnet        #7AA116 solid, no fill (likewise #F2F6E8)
    Security group       #DD344C solid, no group icon (the brief's #DD3522 is corrected to the toolkit's #DD344C)
    Auto Scaling group   #ED7100 dash
    Corporate data center #7D8998 solid
    Generic group        #7D8998 dash (and a solid variant)
    Group borders are 1.25pt (15875 EMU) in the toolkit; the group icon is a 0.417in square flush in the top-left
    corner, the label 12pt regular in tx1 beside it. Here the tab is 0.26in and the label 9pt regular at every level,
    the slide's scale. AZ and security group labels sit centred on the top border (no glyph). The toolkit's flows
    are #232F3E 1.25pt with an open arrow head, and its step badges 0.30in #232F3E discs with a 9pt bold white
    numeral (spec 1.4, 1.5, E27): FLOW_BY and BADGE_BY draw both. Service names are regular (spec 1.2).
  Verified 2026-10-03 against the Azure Architecture Center: the icon guidelines
  (learn.microsoft.com/azure/architecture/icons, updated 2026-07-09, icon set V24) publish usage rules (name close to
  the icon, never recolour or crop) and no boundary colours, so the boundaries follow Microsoft's own reference
  diagrams, read from their SVG source:
    baseline-app-service-architecture.svg: virtual network frame #A4CBFB, subnet ground #F8F8F8 with a #BFBFBF outline,
    availability zone #FFD965 at 1.5pt; Azure blue #0078D4 in the private endpoint and DNS marks.
    hub-spoke.svg: region boundary #0070C0 dashed at 0.75pt.
    Subscription and resource group have no published boundary colour: the subscription takes Azure blue solid and
    the resource group the reference diagrams' grey #7A7A7A dashed, house choices recorded as such.
    Step badges are #107C10 green (identity azure-step) by the user's ruling 21, not Azure blue.
    The VNet is drawn as AAC draws it: a filled #A4CBFB ground its subnets tile (the blue shows only as gutters),
    its icon and label above the frame; every subnet carries the NSG shield in its top-right corner.
  Verified 2026-10-03 against Azure_Public_Service_Icons_V24.zip (arch-center.azureedge.net/icons, 714 SVGs): the
    diagrams package already ships the V24 artwork under newer keys, so the azure grammar's examples use them
    (azure/storage/storage-accounts, azure/other/private-endpoints, azure/other/worker-container-app,
    azure/identity/entra-managed-identities, azure/networking/virtual-networks, azure/networking/subnet,
    azure/networking/network-security-groups). V24 carries no plain Microsoft Entra ID service icon (only Entra
    sub-features), so Entra ID keeps azure/identity/azure-active-directory, the newest plain one available.
  house: theme roles only (navy header bars, rule-strong frames, a platform band with an ink-deep header bar over a
  light card body so dark logos stay visible (ruling 21), accent step badges), so a client theme recolours it.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from . import glyphs, icons, measure, ooxml, prims
from . import text as txt
from .canvas import Box
from .errors import Capacity, GeometryError, Overflows
from .text import Para, Run

GRAMMARS = ("aws", "azure", "house")
FLOW_KINDS = {"data": None, "async": "dash", "control": "sysDot", "private": "sysDash"}
FLOW_KEY = {"data": "Request or data", "async": "Event, asynchronous", "control": "Control or configuration",
            "private": "Private link"}

ICON = 0.42              # the AWS standard 48px at 96 dpi is 0.50in; 0.42in at slide scale
WORDMARK_AR = 1.6        # a brand mark wider than this is a wordmark ...
WORDMARK_H = 0.42        # ... drawn this tall (at most: the icon side), as wide as its caption
NAME_PT, ROLE_PT = 9.0, 8.0
CAP_GAP = 0.05           # icon to caption
CAP_MAX_W = 1.45         # a caption never runs wider than this, whatever its cell
CAP_GUTTER = 0.12        # a caption leaves this much of its cell free, the gutter a flow runs down
CAP_LINES = 2            # per part (name, role)
NODE_VPAD = 0.02         # above and below a node unit in its row
MARGIN = 0.05            # a group frame inside its grid span, each side
PAD_X, PAD_B = 0.10, 0.08
ROW_GAP = 0.05           # the least air between two rows of a container
TAB = 0.26               # the AWS group tab square
HEAD_AIR = 0.16          # below a group's tab or label: room for a flow to run between the header and the icons
TAB_GLYPH = 0.17
ABOVE_H = 0.30           # an 'above' header (the Azure VNet): its icon and label sit in this band over the frame
CORNER = 0.18            # a corner mark (the Azure NSG shield on a subnet)
GROUP_PT = 9.0
BAR_H, BAR_PT = 0.30, 10.0
LABEL_PT = 8.0           # flow labels
LABEL_MAX_W = 1.30
LABEL_INS = measure.Insets(0.03, 0.01, 0.03, 0.01)
LABEL_REACH = 0.38       # kept for callers; a label now sits beside any part of its segment (spec 1.5)
BADGE = 0.22             # the house and azure step badge; aws draws its own (BADGE_BY)
BADGE_PT = 8.0
BADGE_BY = {"aws": (0.30, 9.0), "azure": (0.22, 8.0), "house": (0.22, 8.0)}   # spec 1.5, E27: aws 0.30in, 9pt
# flow notation per grammar: (line role or identity, weight pt, head type, head length). aws draws the toolkit's
# #232F3E 1.25pt open arrow (spec 1.4); azure and house keep the 1.0pt filled triangle.
FLOW_BY = {"aws": ("aws-cloud", 1.25, "arrow", "sm"), "azure": ("ink-muted", 1.0, "triangle", "med"),
           "house": ("ink-muted", 1.0, "triangle", "med")}
LAST_LEG = 0.15          # a route's final leg is at least this long, so its arrowhead lands visibly in the icon
PIN_GAP = 0.05           # an edge pin's caption keeps this far outside its group's frame line
PIN_CAP_W = 0.80         # an edge pin's caption width
ONE_LINE_WORDS = 3       # house: a name of this many words or fewer sits on one line (raised, never wrapped)
ACTOR_KEYS = ("aws/general/", "onprem/generic/", "generic/", "azure/identity/users", "azure/general/usericon")
CLEAR = 0.03             # between a label or badge and anything it must not touch
FRAME_CLEAR = 0.05       # a label or badge inside a frame keeps this from its edges
FRAME_POKE = 0.08        # ... or crosses a border by no more than this
NOTATION_MAX = 0.30      # an icon smaller than this is notation (a group tab), not a product mark
MORE_PT = 9.0
LEGEND_PT = 9.0

ACTOR_GLYPHS = ("user", "users", "user-check", "user-plus", "contact", "id-card", "file", "file-text", "files",
                "file-check", "file-search", "file-spreadsheet", "file-chart-column", "folder", "folder-open", "mail",
                "smartphone", "monitor", "building", "building-complex", "hospital", "house", "book", "book-open",
                "clipboard", "clipboard-list", "newspaper", "globe", "landmark", "megaphone", "message-square",
                "headphones", "stethoscope")


@dataclass(frozen=True)
class Style:
    """How one group kind is drawn. line and fill are a theme role or an identity name; header is one of
    ('square', fill, glyph), ('vendor', key, flush), ('label',), ('bar', fill), ('lane',), ('edge',) (a label centred
    on the top border, the AWS AZ and security group), ('above', key) (an icon and label above the frame, the Azure
    VNet), ('glyph', glyph, role) (a small glyph before the label) or ('section',) (a hairline rule and a bold head
    inside a region, no frame). radius rounds the frame (house cards); corner is a vendor key drawn small in the
    frame's top-right corner (the Azure NSG shield); pad overrides the interior inset."""
    line: str | None
    weight: float = 1.25
    dash: str | None = None
    fill: str | None = None
    header: tuple = ("label",)
    radius: float = 0.0
    corner: str | None = None
    pad: float | None = None


HOUSE_RADIUS = 0.05      # house cards (spec 1.1); the header tab takes 0.06
TAB_RADIUS = 0.06
KINDS = {
    "aws": {
        "aws-cloud": Style("aws-cloud", header=("square", "aws-cloud", "cloud")),
        "aws-account": Style("aws-account", header=("square", "aws-account", "user")),
        "aws-region": Style("aws-region", dash="sysDash", header=("square", "aws-region", "flag")),
        "aws-az": Style("aws-az", dash="dash", header=("edge",)),
        "aws-vpc": Style("aws-vpc", header=("vendor", "aws/network/vpc", True)),
        "aws-public-subnet": Style("aws-public-subnet", header=("square", "aws-public-subnet", "lock-open")),
        "aws-private-subnet": Style("aws-private-subnet", header=("square", "aws-private-subnet", "lock")),
        "aws-security-group": Style("aws-security-group", header=("edge",)),
        "aws-asg": Style("aws-asg", dash="dash", header=("square", "aws-asg", "refresh-cw")),
        "corporate-dc": Style("aws-corporate-dc", header=("square", "aws-corporate-dc", "building")),
        "generic": Style("aws-generic", dash="dash"),
        "lane": Style(None, header=("lane",)),
    },
    "azure": {
        "azure-region": Style("azure-region", weight=0.75, dash="dash", header=("glyph", "globe", "azure-region")),
        "azure-subscription": Style("azure-blue", weight=1.0, header=("vendor", "azure/general/subscriptions", False)),
        "azure-resource-group": Style("azure-resource-group", weight=1.0, dash="dash",
                                      header=("vendor", "azure/general/resource-groups", False)),
        # the VNet is a filled ground its subnets tile, so the blue shows only as gutters; its label sits above it
        "azure-vnet": Style(None, weight=0, fill="azure-vnet", header=("above", "azure/networking/virtual-networks"),
                            pad=0.06),
        "azure-subnet": Style("azure-subnet", weight=0.75, fill="azure-subnet-fill",
                              header=("vendor", "azure/networking/subnet", False),
                              corner="azure/networking/network-security-groups"),
        "azure-zone": Style("azure-zone", weight=1.5),
        "generic": Style("azure-subnet", weight=0.75),
        "lane": Style(None, header=("lane",)),
    },
    "house": {
        "region": Style("rule-strong", weight=0.75, header=("bar", "navy"), radius=HOUSE_RADIUS),
        # a rail is a cross-cutting column: a light card with its name in a label tab, no bar
        "rail": Style("hairline", weight=0.75, fill="card", header=("label",), radius=HOUSE_RADIUS),
        "band": Style("rule-strong", weight=0.75, fill="card", header=("bar", "navy"), radius=HOUSE_RADIUS),
        "section": Style(None, header=("section",)),
        "boundary": Style("rule-strong", weight=0.75, dash="dash", header=("label",)),
        "zone": Style("accent-deep", weight=1.0, dash="dash", header=("label",)),
        "lane": Style(None, header=("lane",)),
    },
}
PIN_SIDES = ("edge:l", "edge:r", "edge:t")
BADGE_FILL = {"aws": "aws-cloud", "azure": "azure-step", "house": "accent"}
_ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,40}")


def _check_id(what, v):
    if not isinstance(v, str) or not _ID.fullmatch(v):
        raise GeometryError("%s id" % what, need="lower-case letters, digits, - and _", have=repr(v))
    return v


@dataclass
class _Group:
    id: str
    kind: str
    label: str
    parent: str | None
    at: tuple
    grid: tuple
    style: Style
    frame: Box | None = None
    inner: Box | None = None
    header_h: float = 0.0
    col_w: float = 0.0
    rows: list = field(default_factory=list)
    row_tops: list = field(default_factory=list)
    natural_inner: float = 0.0
    more: int = 0
    more_cell: tuple | None = None


@dataclass
class _Node:
    id: str
    mark: str
    name: str
    role: str | None
    group: str | None
    at: tuple | None
    hidden: bool = False
    cell: tuple | None = None
    cell_box: Box | None = None
    cap_w: float = 0.0
    cap_h: float = 0.0
    paras: list = field(default_factory=list)
    icon: Box | None = None
    cap: Box | None = None


@dataclass
class _Flow:
    src: str
    dst: str
    label: str | None
    step: int | None
    kind: str
    enter: str | None
    bend: float | None
    points: list = field(default_factory=list)
    label_box: Box | None = None
    label_paras: list = field(default_factory=list)
    badge: Box | None = None


def _inter(a: Box, b: Box, pad: float = 0.0) -> bool:
    return a.x < b.r + pad and b.x < a.r + pad and a.y < b.b + pad and b.y < a.b + pad


def _seg_hits(p, q, b: Box, pad: float = 0.02) -> bool:
    """An orthogonal segment p-q passes through box b (grown by pad)."""
    (x1, y1), (x2, y2) = p, q
    if abs(y1 - y2) < 1e-9:
        lo, hi = sorted((x1, x2))
        return b.y - pad < y1 < b.b + pad and lo < b.r + pad and hi > b.x - pad
    lo, hi = sorted((y1, y2))
    return b.x - pad < x1 < b.r + pad and lo < b.b + pad and hi > b.y - pad


def _clean(pts) -> list:
    """Points rounded, repeats dropped and collinear middles merged, so every segment has length and turns."""
    out = []
    for x, y in pts:
        pt = (round(x, 4), round(y, 4))
        if out and abs(out[-1][0] - pt[0]) < 1e-4 and abs(out[-1][1] - pt[1]) < 1e-4:
            continue
        out.append(pt)
    k = 1
    while k < len(out) - 1:
        (ax, ay), (bx_, by), (cx, cy) = out[k - 1], out[k], out[k + 1]
        if (abs(ax - bx_) < 1e-4 and abs(bx_ - cx) < 1e-4) or (abs(ay - by) < 1e-4 and abs(by - cy) < 1e-4):
            out.pop(k)
        else:
            k += 1
    return out


def _crossings(pts, segs) -> int:
    """How many times an orthogonal route crosses the given segments, one horizontal over one vertical, inside both
    (a shared end is no crossing)."""
    n = 0
    for p, q in zip(pts, pts[1:]):
        for e1, e2 in segs:
            if _cross(p, q, e1, e2):
                n += 1
    return n


def _cross(p, q, e1, e2, eps: float = 0.005) -> bool:
    ph, eh = abs(p[1] - q[1]) < 1e-9, abs(e1[1] - e2[1]) < 1e-9
    if ph == eh:
        return False
    (h1, h2), (v1, v2) = ((p, q), (e1, e2)) if ph else ((e1, e2), (p, q))
    y, x = h1[1], v1[0]
    hx0, hx1 = sorted((h1[0], h2[0]))
    vy0, vy1 = sorted((v1[1], v2[1]))
    return hx0 + eps < x < hx1 - eps and vy0 + eps < y < vy1 - eps


_AQ = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
_INK_CACHE: dict = {}


def _ink_box(path: str, sha):
    """(l, t, r, b, px_w, px_h) of an artwork's ink (alpha above 16) as fractions, from its file; an SVG is rasterised
    at 256px. None when the artwork has no alpha channel."""
    key = (path, sha)
    if key in _INK_CACHE:
        return _INK_CACHE[key]
    import io as _io
    from PIL import Image
    with open(path, "rb") as fh:
        blob = fh.read()
    size = None
    if path.lower().endswith(".svg"):
        w, h = icons.svg_size(blob)
        size = (w, h)                                    # the raster may be clamped to a floor: keep the true aspect
        px = 256
        blob = icons.rasterise(blob, px, max(1, round(px * h / w)) if w else px)
    with Image.open(_io.BytesIO(blob)) as im:
        im = im.convert("RGBA")
        W, H = im.size
        bb = im.getchannel("A").point(lambda a: 255 if a > 16 else 0).getbbox()
    sw, sh = size or (W, H)
    out = None if bb is None else (bb[0] / W, bb[1] / H, bb[2] / W, bb[3] / H, sw, sh)
    _INK_CACHE[key] = out
    return out


def _crop_to_ink(pic, ink, box: Box):
    """Crop a picture to its ink with a:srcRect (the artwork's bytes stay untouched) and set it to box."""
    l, t, r, b = ink[:4]
    if l < 0.02 and t < 0.02 and r > 0.98 and b > 0.98:
        pic.left, pic.top, pic.width, pic.height = (int(round(v)) for v in box.emu)
        return
    bf = pic._element.find(".//" + "{http://schemas.openxmlformats.org/presentationml/2006/main}blipFill")
    blip = bf.find(_AQ + "blip")
    old = bf.find(_AQ + "srcRect")
    if old is not None:
        bf.remove(old)
    from lxml import etree as _et
    sr = _et.Element(_AQ + "srcRect")
    for k, v in (("l", l), ("t", t), ("r", 1 - r), ("b", 1 - b)):
        if v > 0:
            sr.set(k, str(int(round(v * 100000))))
    blip.addnext(sr)
    pic.left, pic.top, pic.width, pic.height = (int(round(v)) for v in box.emu)


def _group_alt(g) -> str:
    """A group icon's alt text: its label without the address ranges and separators (a CIDR reads as a path)."""
    t = re.sub(r"\s*\d[\d./]*", "", g.label.split("·")[0]).strip(" :") or g.kind
    return "%s group" % t


def _dist_pt_seg(pt, p, q) -> float:
    (x, y), (x1, y1), (x2, y2) = pt, p, q
    cx = min(max(x, min(x1, x2)), max(x1, x2))
    cy = min(max(y, min(y1, y2)), max(y1, y2))
    return math.hypot(x - cx, y - cy)


def _dist_pt_box(pt, b: Box) -> float:
    dx = max(b.x - pt[0], 0.0, pt[0] - b.r)
    dy = max(b.y - pt[1], 0.0, pt[1] - b.b)
    return math.hypot(dx, dy)


class Diagram:
    """A declared architecture diagram in one grammar: groups, nodes, flows and steps, drawn by render()."""

    def __init__(self, grammar: str, l0: bool = False, *, grid=(12, 6), icon: float = ICON, weights=None,
                 stretch=None, gaps=None, head_air: float = HEAD_AIR, marks=None, one_line_names=None):
        """grid (cols, rows) divides the drawing area; weights sets relative column widths; stretch lists the rows that
        take the room left over, or gaps weighs the gaps between rows that take it (default: every gap alike, so
        groups hug their content); head_air is the room under a group's header where an over-the-row flow and its
        label run; marks is a folder holding a mark registry.json (a test fixture), else the kit's. one_line_names
        (default: on for a house deep dive, off for an L0 master and the aws and azure notations, which wrap long
        service names as AWS and Azure do) refuses a name of three words or fewer that breaks over two lines."""
        if grammar not in GRAMMARS:
            raise GeometryError("diagram grammar", need=" / ".join(GRAMMARS), have=grammar)
        self.grammar = grammar
        self.l0 = bool(l0)
        self.one_line_names = (grammar == "house" and not self.l0) if one_line_names is None else bool(one_line_names)
        self.grid = self._grid("diagram", grid)
        self.weights = self._weights("diagram", weights, self.grid[0])
        self.stretch = list(stretch) if stretch else None
        self.gaps = list(gaps) if gaps else None
        if self.gaps and (len(self.gaps) != self.grid[1] - 1 or any(g < 0 for g in self.gaps) or not sum(self.gaps)):
            raise GeometryError("diagram gaps", need="%d non-negative weights, not all 0" % (self.grid[1] - 1),
                                have=gaps)
        self.head_air = float(head_air)
        self.gutter = 2 * MARGIN
        if not 0.12 <= self.head_air <= 0.60:
            raise GeometryError("diagram head_air", need="0.12..0.60in", have=head_air, unit="in")
        if self.stretch and any(not isinstance(k, int) or not 0 <= k < self.grid[1] for k in self.stretch):
            raise GeometryError("diagram stretch", need="row indices 0..%d" % (self.grid[1] - 1), have=stretch)
        self.icon = float(icon)
        if not (0.30 <= self.icon <= 0.80):
            raise GeometryError("diagram icon side", need="0.30..0.80in", have=self.icon, unit="in")
        self.groups: dict[str, _Group] = {}
        self.nodes: dict[str, _Node] = {}
        self.flows: list[_Flow] = []
        self.legend: dict[int, str] = {}
        self._order: list = []          # declaration order of ('g'|'n', id), for placement
        self._aligns: list = []
        self.marks_registry = marks     # a folder holding registry.json; None is the kit's kit/assets/marks

    # ------------------------------------------------------------------ declaring
    @staticmethod
    def _weights(what, weights, cols):
        if weights is None:
            return None
        w = list(weights)
        if len(w) != cols or any(not isinstance(v, (int, float)) or v <= 0 for v in w):
            raise GeometryError("%s weights" % what, need="%d positive column weights" % cols, have=weights)
        return w

    @staticmethod
    def _grid(what, grid):
        if not (isinstance(grid, (tuple, list)) and len(grid) == 2 and all(isinstance(v, int) and v >= 1 for v in grid)):
            raise GeometryError("%s grid" % what, need="(cols, rows) of positive ints", have=grid)
        return tuple(grid)

    def _col_x(self, parent, inner: Box) -> list:
        """The x of every column edge of a container (cols + 1 values), from its weights (even by default)."""
        cols, _rows = self._container_grid(parent)
        wts = self.weights if parent is None else self.groups[parent].weights
        wts = list(wts) if wts else [1.0] * cols
        t = float(sum(wts))
        xs, x = [inner.x], inner.x
        for w in wts:
            x += inner.w * w / t
            xs.append(x)
        return xs

    def _container_grid(self, parent):
        return self.grid if parent is None else self.groups[parent].grid

    def _check_span(self, what, parent, at):
        cols, rows = self._container_grid(parent)
        c, r, cs, rs = at
        if not (0 <= c and 0 <= r and cs >= 1 and rs >= 1 and c + cs <= cols and r + rs <= rows):
            raise GeometryError("%s at" % what, need="inside the %dx%d grid of %s" % (cols, rows, parent or "the diagram"),
                                have=at)

    def group(self, id, kind, label, parent=None, at=(0, 0, 1, 1), grid=(1, 1), weights=None, *, band=False,
              drop=0.0, row_gap=None, gutter=None):
        """A boundary or region on its parent's grid (or the diagram's), with an inner grid for its children.
        band=True declares a platform or operations band: its marks may carry no flow (gate P26.r), and its frame is
        named <name>.g.<id>.band so the gate knows. drop (inches) lowers the frame's top inside its span, for the
        staggered columns of an L0 master (spec 3.3). row_gap (inches) is the least air between the group's rows:
        room for the pins on a child's top edge and the flows that reach them. gutter (inches) is the air between
        sibling child groups side by side, where a labelled flow runs (spec 1.1: 0.55in or more)."""
        _check_id("group", id)
        if id in self.groups or id in self.nodes:
            raise GeometryError("group %s" % id, need="a unique id", have="duplicate")
        styles = KINDS[self.grammar]
        if kind not in styles:
            raise GeometryError("group %s kind" % id, need=" / ".join(styles), have=kind,
                                hint="the %s grammar draws only its own notation" % self.grammar)
        if parent is not None and parent not in self.groups:
            raise GeometryError("group %s parent" % id, need="a declared group", have=parent)
        if not (isinstance(at, (tuple, list)) and len(at) == 4 and all(isinstance(v, int) for v in at)):
            raise GeometryError("group %s at" % id, need="(col, row, cols, rows)", have=at)
        if not str(label or "").strip() and kind != "lane":
            raise GeometryError("group %s label" % id, need="a label", have=repr(label),
                                hint="only a lane (a layout row with no frame) may go unlabelled")
        self._check_span("group %s" % id, parent, tuple(at))
        self.groups[id] = _Group(id, kind, str(label or "").strip(), parent, tuple(at), self._grid("group %s" % id, grid),
                                 styles[kind])
        self.groups[id].weights = self._weights("group %s" % id, weights, self.groups[id].grid[0])
        if not (0.0 <= float(drop) <= 2.0):
            raise GeometryError("group %s drop" % id, need="0..2in", have=drop, unit="in")
        self.groups[id].band = bool(band) or kind == "band"
        self.groups[id].drop = float(drop)
        rgs = [row_gap] * max(0, self.groups[id].grid[1] - 1) if not isinstance(row_gap, (list, tuple)) else list(row_gap)
        if row_gap is not None and (len(rgs) != max(0, self.groups[id].grid[1] - 1) or
                                    any(not (0.0 <= float(v) <= 1.5) for v in rgs)):
            raise GeometryError("group %s row_gap" % id, need="0..1.5in, one per gap between rows", have=row_gap)
        self.groups[id].row_gaps = [ROW_GAP] * max(0, self.groups[id].grid[1] - 1) if row_gap is None else \
            [float(v) for v in rgs]
        if gutter is not None and not (0.0 <= float(gutter) <= 1.5):
            raise GeometryError("group %s gutter" % id, need="0..1.5in", have=gutter, unit="in")
        self.groups[id].gutter = 2 * MARGIN if gutter is None else float(gutter)
        self._order.append(("g", id))
        return id

    def node(self, id, mark, name, role=None, group=None, at=None, anchor="center", *, size=None, caption=None):
        """A floating icon with its caption. mark: 'vendor:<key>', 'mark:<key>', 'glyph:<actor glyph>' or
        'mono:<letters>' (a product with no offline mark). A wordmark (a brand mark wider than 1.6:1) is drawn as wide as
        its caption, so its caption names the job, not the product again. at=None places it in the group's next free
        cell. anchor
        ('center', 'left', 'right') sets it in its cell: an actor column anchored left leaves the gap before the
        cloud for the labels of the flows that cross it; all the left-anchored icons of one column share one left
        edge, their captions left-aligned under them. anchor 'edge:l', 'edge:r' or 'edge:t' is an edge pin (a VPC
        endpoint, a load balancer at the VPC ingress): its icon is centred on its group's frame line, its caption sits
        wholly outside the frame (above the icon for a side edge, beside it above the line for the top edge), it
        takes no cell (at gives its row, and for edge:t its column), and a flow may leave or reach it on any side its
        caption leaves free. size (0.30..0.80in) draws one node larger or smaller than the diagram's icon: the
        platform tier of an L0 master (spec 3.3). caption='right' sets the caption beside the icon, left-aligned
        (the AWS reference practice for a row of regional services): the icon's bottom is then free, so a flow may
        drop straight down from it or land on it from below. caption='left' mirrors it (right-aligned, the icon's
        right side free)."""
        if anchor in ("edge:l", "edge:r"):                 # a side pin's caption: above (default) or below the icon
            if caption not in (None, "above", "below"):
                raise GeometryError("node %s caption" % id, need="above or below for a side pin", have=caption)
            pin_cap = caption or "above"
            caption = "below"
        else:
            pin_cap = None
            caption = caption or "below"
            if caption not in ("below", "right", "left"):
                raise GeometryError("node %s caption" % id, need="below, right or left", have=caption)
            if caption != "below" and anchor in PIN_SIDES:
                raise GeometryError("node %s caption" % id, need="a pin places its own caption", have=caption)
        if anchor not in ("center", "left", "right") + PIN_SIDES:
            raise GeometryError("node %s anchor" % id, need="center, left, right, edge:l, edge:r or edge:t",
                                have=anchor)
        if anchor in PIN_SIDES and (group is None or at is None):
            raise GeometryError("node %s edge pin" % id, need="a group and at=(col, row)", have=(group, at),
                                hint="a pin sits on its group's frame line")
        if size is not None and not (0.30 <= float(size) <= 0.80):
            raise GeometryError("node %s size" % id, need="0.30..0.80in", have=size, unit="in")
        _check_id("node", id)
        if id in self.groups or id in self.nodes:
            raise GeometryError("node %s" % id, need="a unique id", have="duplicate")
        if group is not None and group not in self.groups:
            raise GeometryError("node %s group" % id, need="a declared group", have=group)
        kind, _, key = str(mark).partition(":")
        if kind not in ("vendor", "mark", "glyph", "mono") or not key:
            raise GeometryError("node %s mark" % id, need="vendor:<key>, mark:<key>, glyph:<name> or mono:<AB>",
                                have=mark)
        if kind == "mark" and key not in icons.mark_registry(self.marks_registry):
            raise GeometryError("node %s mark" % id, need="a key in the mark registry (ruling 19)", have=key,
                                hint="registered: " + ", ".join(sorted(icons.mark_registry(self.marks_registry))))
        if kind == "vendor" and not icons.vendor_resolves(key):
            raise GeometryError("node %s mark" % id, need="a vendor key (deckkit.icons.vendor_keys)", have=key)
        if kind == "glyph":
            if glyphs.resolve(key) not in ACTOR_GLYPHS:
                raise GeometryError("node %s glyph" % id, need="an actor, user or document glyph: " + ", ".join(ACTOR_GLYPHS),
                                    have=key, hint="a product with a mark is drawn with its mark, never a glyph")
        if not str(name or "").strip():
            raise GeometryError("node %s name" % id, need="a caption name", have=repr(name))
        if at is not None:
            if not (isinstance(at, (tuple, list)) and len(at) == 2 and all(isinstance(v, int) for v in at)):
                raise GeometryError("node %s at" % id, need="(col, row)", have=at)
            self._check_span("node %s" % id, group, (at[0], at[1], 1, 1))
        self.nodes[id] = _Node(id, str(mark), str(name).strip(), (str(role).strip() or None) if role else None, group,
                               tuple(at) if at is not None else None)
        self.nodes[id].anchor = anchor
        self.nodes[id].size = float(size) if size is not None else None
        self.nodes[id].capside = caption
        self.nodes[id].pin_cap = pin_cap
        self._order.append(("n", id))
        return id

    def flow(self, src, dst, label=None, step=None, kind="data", *, enter=None, bend=None, over=False):
        """A connector from src to dst; async is dashed, control dotted, private (a private endpoint's link to its
        service) short-dashed and keyed once in the legend instead of labelled. step draws a numbered badge and feeds the
        legend. enter='t' lands on the top edge of a node below (an L route); bend (0..1) places the elbow; over=True
        prefers a U route that leaves the source's top, runs above the row and lands on the destination's top. When the
        planned route is blocked the engine tries an L, then a U, and refuses only when every one is."""
        if self.l0:
            raise GeometryError("flow %s to %s" % (src, dst), need="no flows on an L0 master", have="a flow",
                                hint="the L0 master carries no arrows and no numbering (CLAUDE.md section 8); "
                                     "flows belong in the deep dives")
        for n in (src, dst):
            if n not in self.nodes:
                raise GeometryError("flow %s to %s" % (src, dst), need="declared nodes", have=n)
        if src == dst:
            raise GeometryError("flow %s" % src, need="two different nodes", have="the same node twice")
        if kind not in FLOW_KINDS:
            raise GeometryError("flow kind", need=" / ".join(FLOW_KINDS), have=kind)
        if step is not None and not (isinstance(step, int) and 1 <= step <= 99):
            raise GeometryError("flow step", need="an int 1..99", have=step)
        if label is not None:
            label = str(label).strip()
            if not label or len(label.split()) > 6:
                raise GeometryError("flow %s to %s label" % (src, dst), need="1 to 6 words: what moves", have=label)
        if enter not in (None, "t"):
            raise GeometryError("flow enter", need="None or 't'", have=enter,
                                hint="a flow never lands on an icon's bottom edge, where its caption sits")
        if bend is not None and not (0.05 <= float(bend) <= 0.95):
            raise GeometryError("flow bend", need="0.05..0.95", have=bend)
        fl = _Flow(src, dst, label, step, kind, enter, None if bend is None else float(bend))
        fl.over = bool(over)
        self.flows.append(fl)
        return len(self.flows)

    def align(self, node, to, axis="y"):
        """Move node so its icon shares to's centre line (axis 'y', the default: a horizontal flow between them then
        runs straight) or centre column (axis 'x': a vertical one does). Refused when the move would take it out of
        its group or onto another node."""
        for n in (node, to):
            if n not in self.nodes:
                raise GeometryError("align %s to %s" % (node, to), need="declared nodes", have=n)
        if axis not in ("x", "y"):
            raise GeometryError("align axis", need="x or y", have=axis)
        self._aligns.append((node, to, axis))

    def steps(self, mapping):
        """The legend text for each numbered step."""
        if self.l0:
            raise GeometryError("steps", need="no numbering on an L0 master", have=len(mapping))
        for k, v in dict(mapping).items():
            if not (isinstance(k, int) and 1 <= k <= 99) or not str(v or "").strip():
                raise GeometryError("step %r" % (k,), need="an int 1..99 and its text", have=v)
            self.legend[k] = str(v).strip()

    # ------------------------------------------------------------------ measuring
    def _children(self, parent):
        gs = [g for g in self.groups.values() if g.parent == parent]
        ns = [n for n in self.nodes.values() if n.group == parent]
        return gs, ns

    def _air(self, g: _Group) -> float:
        """Room under a header. A group whose only child is one group insets it 0.10in below its tab row (spec
        1.1): no flow runs there."""
        gs, ns = self._children(g.id)
        if len(gs) == 1 and not ns:
            return 0.10
        return self.head_air

    def _header(self, g: _Group, th) -> float:
        h = g.style.header
        face = measure.face_for(txt._default_face(th), True)
        lh = measure.line_in(GROUP_PT, face) * measure.SLACK
        air = self._air(g)
        if h[0] in ("square", "vendor"):
            return (TAB + air) if (h[0] == "square" or h[2]) else (0.05 + 0.24 + air)
        if h[0] == "bar":
            return BAR_H + air
        if h[0] == "lane":
            return (lh + 0.06) if g.label else 0.0
        if h[0] == "edge":
            return lh / 2 + 0.07
        if h[0] == "above":
            return ABOVE_H + (g.style.pad if g.style.pad is not None else PAD_X)
        if h[0] == "section":
            return 0.07 + lh + 0.05
        return 0.06 + lh + air

    def _side_pads(self, g):
        """(left, right) interior insets: a side that carries edge pins keeps its children clear of the pins."""
        px, _pb = self._pad(g)
        pins = [n for n in self.nodes.values() if n.group == g.id and n.anchor in ("edge:l", "edge:r")]
        pl = max([px] + [self._side(n) / 2 + 0.08 for n in pins if n.anchor == "edge:l"])
        pr = max([px] + [self._side(n) / 2 + 0.08 for n in pins if n.anchor == "edge:r"])
        return pl, pr

    def _pad(self, g):
        if g.style.header[0] in ("lane", "section"):
            return (0.0, 0.0)
        if g.style.pad is not None:
            return (g.style.pad, g.style.pad)
        return (PAD_X, PAD_B)

    def _assign_cells(self, parent, cols, rows, what):
        """Occupancy of a container's grid; auto nodes fill free cells row-major, the overflow folds into a chip."""
        gs, ns = self._children(parent)
        taken = {}
        for g in gs:
            c, r, cs, rs = g.at
            for cc in range(c, c + cs):
                for rr in range(r, r + rs):
                    if (cc, rr) in taken:
                        raise GeometryError("%s cell %d,%d" % (what, cc, rr), need="one child per cell",
                                            have="%s and %s" % (taken[(cc, rr)], g.id))
                    taken[(cc, rr)] = g.id
        for n in ns:
            if n.anchor in PIN_SIDES:
                n.cell = n.at                           # a pin takes no cell: at gives its row (and edge:t its column)
                continue
            if n.at is not None:
                if n.at in taken:
                    raise GeometryError("%s cell %d,%d" % (what, *n.at), need="one child per cell",
                                        have="%s and %s" % (taken[n.at], n.id))
                taken[n.at] = n.id
                n.cell = n.at
        auto = [n for n in ns if n.at is None and n.anchor not in PIN_SIDES]
        free = [(c, r) for r in range(rows) for c in range(cols) if (c, r) not in taken]
        more = None
        if len(auto) > len(free):
            if not free:
                raise Capacity("%s" % what, need=len(auto), have=0, hint="give the group a larger grid")
            shown = len(free) - 1
            for n, cell in zip(auto[:shown], free):
                n.cell = cell
            for n in auto[shown:]:
                n.hidden = True
            more = (len(auto) - shown, free[shown])
        else:
            for n, cell in zip(auto, free):
                n.cell = cell
        return more

    def _cap_align(self, n: _Node) -> str:
        if getattr(n, "capside", "below") in ("right", "left"):
            return "left"
        if getattr(n, "capside", "below") == "left":
            return "right"
        return {"edge:r": "left", "edge:t": "left", "edge:l": "right", "left": "left", "right": "right"}.get(
            n.anchor, "center")

    def _problem(self, err):
        """Raise err, or in draft mode list it and carry on (render(draft=True))."""
        if not getattr(self, "draft", False):
            raise err
        self.problems.append(str(err))

    def _caption(self, n: _Node, th):
        al = self._cap_align(n)
        # spec 1.2: node names regular; the house grammar keeps its bold names (the user's own boards)
        paras = [Para((Run(n.name, role="ink-deep", bold=self.grammar == "house", size=NAME_PT),), align=al)]
        if n.role:
            paras.append(Para((Run(n.role, role="ink-muted", size=ROLE_PT),), align=al))
        for k, p in enumerate(paras):
            try:
                fit = txt.check_fit("node %s caption" % n.id, [p], (n.cap_w, 100.0), th)
            except Overflows as err:                      # a word wider than the cell
                self._problem(err)
                n.cap_w = max(n.cap_w, 1.0)
                fit = txt.check_fit("node %s caption" % n.id, [p], (n.cap_w, 100.0), th)
            if fit.n_lines > CAP_LINES:
                self._problem(Overflows("node %s caption %r" % (n.id, p.runs[0].text), need=fit.n_lines,
                                        have=CAP_LINES, unit="lines", hint="at %.2fin it wraps to %d lines; cut words "
                                        "or widen the cell (a wider group or fewer columns), never smaller type"
                                        % (n.cap_w, fit.n_lines)))
            elif k == 0 and self.one_line_names and fit.n_lines > 1 and len(n.name.split()) <= ONE_LINE_WORDS:
                face = measure.face_for(txt._default_face(th), True)
                need = measure.width_in(n.name, NAME_PT, face) * measure.SLACK + 0.02
                self._problem(Overflows("node %s name %r" % (n.id, n.name), need=round(need + CAP_GUTTER, 3),
                                        have=round(n.cap_w + CAP_GUTTER, 3), unit="in",
                                        hint="a name of %d words or fewer sits on one line: widen its cell (fewer "
                                             "columns or a wider group), never break it" % ONE_LINE_WORDS))
        n.paras = paras
        # the caption box hugs its widest wrapped line, so a label or a badge may sit beside a short caption
        widest = 0.0
        for p in paras:
            r = p.runs[0]
            face = measure.face_for(txt._default_face(th), r.bold)
            for line in txt.check_fit("node %s caption" % n.id, [p], (n.cap_w, 100.0), th).lines:
                widest = max(widest, measure.width_in(line, r.size, face) * measure.SLACK)
        tight = min(n.cap_w, math.ceil((widest + 0.02) * 1000) / 1000.0)
        if tight < n.cap_w:
            lines = [txt.check_fit("node %s caption" % n.id, [p], (tight, 100.0), th).n_lines for p in paras]
            full = [txt.check_fit("node %s caption" % n.id, [p], (n.cap_w, 100.0), th).n_lines for p in paras]
            if lines == full:
                n.cap_w = tight
        n.cap_h = math.ceil(txt.need_height(paras, n.cap_w, th) * 10000 + 1) / 10000.0

    def _aspect(self, n: _Node) -> float:
        """Width over height of a brand mark's artwork (1.0 for every other mark)."""
        kind, _, key = n.mark.partition(":")
        if kind != "mark":
            return 1.0
        entry = icons.mark_registry(self.marks_registry).get(key)
        if entry is None:
            raise GeometryError("node %s mark" % n.id, need="a key in the mark registry", have=key)
        blob = (icons.marks_dir(self.marks_registry) / entry["file"]).read_bytes()
        if entry["file"].lower().endswith(".svg"):
            w, h = icons.svg_size(blob)
        else:
            w, h = icons._png_size(blob)
        return w / h if h else 1.0

    def _side(self, n: _Node) -> float:
        return n.size or self.icon

    def _unit(self, n: _Node) -> float:
        if n.anchor == "edge:t":
            return 0.0                                   # it sits on its group's top line
        if getattr(n, "capside", "below") in ("right", "left"):
            return max(self._side(n), n.cap_h)
        return self._side(n) + CAP_GAP + n.cap_h

    def _widths(self, parent, inner: Box, th):
        cols, rows = self._container_grid(parent)
        what = parent or "the diagram"
        xs = self._col_x(parent, inner)
        more = self._assign_cells(parent, cols, rows, "group %s" % what if parent else what)
        if parent is not None:
            g = self.groups[parent]
            g.col_w = min(xs[k + 1] - xs[k] for k in range(cols))
            if more:
                g.more, g.more_cell = more
        gs, ns = self._children(parent)
        for n in ns:
            if n.hidden:
                continue
            c = n.cell[0]
            cw = xs[c + 1] - xs[c]
            n.cap_w = min(cw - CAP_GUTTER, CAP_MAX_W)
            if n.anchor in PIN_SIDES:                    # a pin's caption sits in a gutter: the narrowest two lines
                n.cap_w = PIN_CAP_W
                for w_ in [0.45 + 0.05 * k for k in range(16)]:
                    try:
                        ok_ = all(txt.check_fit("pin", [Para((Run(t, size=sz),))], (w_, 100.0), th).n_lines <= CAP_LINES
                                  for t, sz in ((n.name, NAME_PT), (n.role or "", ROLE_PT)) if t)
                    except Overflows:
                        ok_ = False
                    if ok_:
                        n.cap_w = w_
                        break
            if getattr(n, "capside", "below") in ("right", "left"):
                n.cap_w = min(cw - CAP_GUTTER - self._side(n) - 0.06, CAP_MAX_W)
                if n.cap_w < 0.4:
                    self._problem(Overflows("node %s cell" % n.id, need=round(self._side(n) + 0.46 + CAP_GUTTER, 3),
                                            have=round(cw, 3), hint="a caption beside its icon needs a wider cell"))
                    n.cap_w = 0.4
            elif n.cap_w < self._side(n) and n.anchor not in PIN_SIDES:
                self._problem(Overflows("node %s cell" % n.id, need=round(self._side(n) + CAP_GUTTER, 3),
                                        have=round(cw, 3), hint="the %s grid is too fine for its icons; fewer columns"
                                        % what))
                n.cap_w = self._side(n)
            self._caption(n, th)
        gut = (self.gutter if parent is None else self.groups[parent].gutter) / 2.0
        for g in gs:
            c, r, cs, rs = g.at
            lm = gut if c > 0 else MARGIN                 # the gutter sits between siblings, not at the edges
            rm = gut if c + cs < cols else MARGIN
            fx = xs[c] + lm
            fw = xs[c + cs] - xs[c] - lm - rm
            pl, pr = self._side_pads(g)
            g.header_h = self._header(g, th)
            g.frame = Box(fx, 0.0, fw, 1.0)                      # y and h are set by _place
            self._widths(g.id, Box(fx + pl, 0.0, fw - pl - pr, 1.0), th)

    def _natural(self, parent) -> tuple[list, float]:
        """(row heights, natural inner height) of a container, bottom-up."""
        cols, rows = self._container_grid(parent)
        gs, ns = self._children(parent)
        heights = [0.0] * rows
        spans = []
        for n in ns:
            if not n.hidden:
                heights[n.cell[1]] = max(heights[n.cell[1]], self._unit(n) + 2 * NODE_VPAD)
        if parent is not None and self.groups[parent].more_cell:
            r = self.groups[parent].more_cell[1]
            heights[r] = max(heights[r], 0.30 + 2 * NODE_VPAD)
        for g in gs:
            nat = self._group_natural(g) + 2 * MARGIN + getattr(g, "drop", 0.0)
            c, r, cs, rs = g.at
            if rs == 1:
                heights[r] = max(heights[r], nat)
            else:
                spans.append((r, rs, nat))
        for r, rs, nat in spans:
            have = sum(heights[r:r + rs]) + sum(self._gaps0(parent)[r:r + rs - 1])
            if nat > have:
                add = (nat - have) / rs
                for k in range(r, r + rs):
                    heights[k] += add
        return heights, sum(heights) + sum(self._gaps0(parent))

    def _gaps0(self, parent) -> list:
        """The least gap under each row of a container but its last."""
        rows = self._container_grid(parent)[1]
        return [ROW_GAP] * max(0, rows - 1) if parent is None else list(self.groups[parent].row_gaps)

    def _group_natural(self, g: _Group) -> float:
        rows, inner = self._natural(g.id)
        g.rows, g.natural_inner = rows, inner
        _px, pb = self._pad(g)
        return g.header_h + inner + pb

    def _place(self, parent, inner: Box):
        """Top-down: row tops in a container whose inner box is final, then every child's frame or cell."""
        cols, rows = self._container_grid(parent)
        heights, nat = self._natural(parent)
        extra = inner.h - nat
        what = "group %s" % parent if parent else "the diagram"
        if extra < -1e-6:
            self._problem(Overflows("%s height" % what, need=round(nat, 3), have=round(inner.h, 3),
                                    hint="its content needs %.2fin more; fewer rows, a larger icon grid span or a "
                                         "taller box" % -extra))
            extra = 0.0
        gaps = self._gaps0(parent)
        gap = ROW_GAP
        grow = self.stretch if parent is None else None
        if grow:
            for k in grow:
                heights[k] += extra / len(grow)
        elif parent is None and self.gaps:
            t = float(sum(self.gaps))
            gaps = [g0 + extra * w / t for g0, w in zip(gaps, self.gaps)]
        elif rows > 1:
            gaps = [g0 + extra / (rows - 1) for g0 in gaps]
        elif parent is not None and all(g.style.header[0] in ("section", "lane") for g in self._children(parent)[0]):
            gaps = []                                     # one row of marks or sections: centred, top and foot alike
            inner = Box(inner.x, inner.y + extra / 2, inner.w, inner.h - extra)
        else:
            heights[0] += extra
        tops, y = [], inner.y
        for k, h in enumerate(heights):
            tops.append(y)
            y += h + (gaps[k] if k < len(gaps) else 0.0)
        xs = self._col_x(parent, inner)
        gs, ns = self._children(parent)
        if parent is not None:
            self.groups[parent].row_tops = tops
            self.groups[parent].rows = heights
        else:
            self._root_tops, self._root_rows, self._root_gap = tops, heights, gap
        rowmax = {}
        for n in ns:
            if not n.hidden:
                rowmax[n.cell[1]] = max(rowmax.get(n.cell[1], 0.0), self._unit(n))
        rowicon = {}                                       # one centre line per row: the row's largest icon
        for n in ns:
            if not n.hidden and n.anchor != "edge:t":
                rowicon[n.cell[1]] = max(rowicon.get(n.cell[1], 0.0), self._side(n))
        lefts = {}                                         # left-anchored icons of one column share one left edge
        for n in ns:
            if not n.hidden and n.anchor in ("left", "right"):
                lefts.setdefault((n.cell[0], n.anchor), []).append(n)
        for n in ns:
            if n.hidden:
                continue
            c, r = n.cell
            cell = Box(xs[c], tops[r], xs[c + 1] - xs[c], heights[r])
            n.cell_box = cell
            side = self._side(n)
            top = cell.y + (cell.h - rowmax.get(r, 0.0)) / 2 + (rowicon.get(r, side) - side) / 2
            al = self._cap_align(n)
            if n.anchor in PIN_SIDES:
                fr = self.groups[parent].frame
                if n.anchor == "edge:t":
                    icon = Box(cell.cx - side / 2, fr.y - side / 2, side, side)
                    cap = Box(icon.r + 0.05, fr.y - 0.04 - n.cap_h, n.cap_w, n.cap_h)
                else:
                    ex = fr.r if n.anchor == "edge:r" else fr.x
                    icon = Box(ex - side / 2, top, side, side)
                    cx0 = ex + PIN_GAP if n.anchor == "edge:r" else ex - PIN_GAP - n.cap_w
                    if n.pin_cap == "below":
                        cap = Box(cx0, icon.b + CAP_GAP, n.cap_w, n.cap_h)
                    else:
                        cap = Box(cx0, icon.y - CAP_GAP - n.cap_h, n.cap_w, n.cap_h)    # above, outside the frame
                n.icon, n.cap = icon, cap
                continue
            if getattr(n, "capside", "below") in ("right", "left"):
                unit_w = side + 0.06 + n.cap_w
                if n.anchor == "left":
                    x0 = xs[c] + CAP_GUTTER / 2
                elif n.anchor == "right":
                    x0 = xs[c + 1] - CAP_GUTTER / 2 - unit_w
                else:
                    x0 = cell.cx - unit_w / 2
                ry = cell.y + (cell.h - rowmax.get(r, 0.0)) / 2 + rowmax.get(r, 0.0) / 2
                if n.capside == "right":
                    n.icon = Box(x0, ry - side / 2, side, side)
                    n.cap = Box(n.icon.r + 0.06, ry - n.cap_h / 2, n.cap_w, n.cap_h)
                else:
                    n.cap = Box(x0, ry - n.cap_h / 2, n.cap_w, n.cap_h)
                    n.icon = Box(n.cap.r + 0.06, ry - side / 2, side, side)
                continue
            if n.anchor == "left":
                x0 = xs[c] + CAP_GUTTER / 2
                n.icon = Box(x0, top, side, side)
                n.cap = Box(x0, top + side + CAP_GAP, n.cap_w, n.cap_h)
            elif n.anchor == "right":
                x1 = xs[c + 1] - CAP_GUTTER / 2
                n.icon = Box(x1 - side, top, side, side)
                n.cap = Box(x1 - n.cap_w, top + side + CAP_GAP, n.cap_w, n.cap_h)
            else:
                cx = cell.cx
                n.icon = Box(cx - side / 2, top, side, side)
                n.cap = Box(cx - n.cap_w / 2, top + side + CAP_GAP, n.cap_w, n.cap_h)
            ar = self._aspect(n)
            if ar > WORDMARK_AR:                      # a wordmark: as wide as its caption, centred on the icon line
                w = min(max(n.cap_w, side), WORDMARK_H * ar)
                h = w / ar
                ic = n.icon
                n.icon = Box(ic.cx - w / 2 if al == "center" else (ic.x if al == "left" else ic.r - w),
                             top + (side - h) / 2, w, h)
        for g in gs:
            c, r, cs, rs = g.at
            sy = tops[r] + g.drop
            sh = sum(heights[r:r + rs]) + sum(gaps[r:r + rs - 1]) - g.drop
            g.span = Box(g.frame.x, sy + MARGIN, g.frame.w, sh - 2 * MARGIN)
            if g.style.header[0] == "above":              # the label and icon sit above the frame
                g.frame = Box(g.frame.x, sy + MARGIN + ABOVE_H, g.frame.w, sh - 2 * MARGIN - ABOVE_H)
            else:
                g.frame = Box(g.frame.x, sy + MARGIN, g.frame.w, sh - 2 * MARGIN)
            px, pb = self._pad(g)
            pl, pr = self._side_pads(g)
            top_in = g.header_h - (ABOVE_H if g.style.header[0] == "above" else 0.0)
            g.inner = Box(g.frame.x + pl, g.frame.y + top_in, g.frame.w - pl - pr,
                          g.frame.h - top_in - pb)
            self._place(g.id, g.inner)
        if parent is not None:
            g = self.groups[parent]
            if g.more_cell:
                c, r = g.more_cell
                g.more_box = Box(xs[c], tops[r], xs[c + 1] - xs[c], heights[r])

    # ------------------------------------------------------------------ routing
    def _obstacles(self, routing: bool = False):
        """What a flow (routing=True) or a label or badge must keep clear of: every icon and caption, every group
        header (for a route, only the words of a header bar: a line may cross the bar itself) and every chip."""
        out = []
        for n in self.nodes.values():
            if n.hidden:
                continue
            out.append((n.icon, "icon %s" % n.id, n.id))
            out.append((n.cap, "caption %s" % n.id, n.id))
            if routing and getattr(n, "capside", "below") in ("right", "left"):       # no line between an icon and its caption
                x0, x1 = min(n.icon.x, n.cap.x), max(n.icon.r, n.cap.r)
                u = Box(x0, min(n.icon.y, n.cap.y), x1 - x0, max(n.icon.b, n.cap.b) - min(n.icon.y, n.cap.y))
                out.append((u, "unit %s" % n.id, n.id))
        for g in self.groups.values():
            hb = getattr(g, "route_box", None) if routing else None
            out.append((hb or g.header_box, "header %s" % g.id, None))
            if getattr(g, "corner_box", None) is not None:
                out.append((g.corner_box, "corner %s" % g.id, None))
            if getattr(g, "chip", None) is not None:
                out.append((g.chip, "chip %s" % g.id, None))
        return out

    def _plan(self, f: _Flow):
        """(mode, source side, destination side): straight when the two icons share a centre line, an L into the top
        of a node below when asked, a Z through the gutter between two columns, else a C beside one column."""
        ns, nd = self.nodes[f.src], self.nodes[f.dst]
        S, D = ns.icon, nd.icon
        if abs(S.cx - D.cx) < 0.02:                      # one column: straight down or up, where no caption sits
            if D.y > S.b + 0.1 and not self._cap_below(ns):
                return ("V", "b", "t")
            if S.y > D.b + 0.1 and not self._cap_below(nd):
                return ("V", "t", "b")
        if f.over and abs(D.cx - S.cx) > 0.3:
            return ("U", "t", "t")
        if abs(S.cy - D.cy) < 1e-3 and (D.x > S.r + 0.1 or S.x > D.r + 0.1):
            return ("straight",) + (("r", "l") if D.x > S.r else ("l", "r"))
        if f.enter == "t":
            if D.y <= S.cy + 0.1:
                raise GeometryError("flow %s to %s" % (f.src, f.dst), need="a destination below the source to enter "
                                    "its top", have="destination above", hint="enter='t' lands on a node below")
            return ("L", "r" if D.cx > S.cx else "l", "t")
        if D.x > S.r + 0.2 or S.x > D.r + 0.2:
            return ("Z",) + (("r", "l") if D.x > S.r else ("l", "r"))
        side = "r" if (f.bend is None or f.bend >= 0.5) else "l"
        return ("C", side, side)

    PORT = 0.13          # the furthest a port moves from an edge's centre (the icon's half side is 0.21)

    def _cap_below(self, n: _Node) -> bool:
        """The node's caption sits under its icon (every node but a top-edge pin and a caption-right node)."""
        return n.anchor != "edge:t" and getattr(n, "capside", "below") == "below"

    def _ports(self):
        """Flows that share one side of one icon leave or land at distinct points along it, ordered by where their
        other end lies, so no two lines run on top of each other. A straight flow keeps the centre when it can."""
        uses = {}
        for f in self.flows:
            f.mode, f.ss, f.ds = self._plan(f)
            uses.setdefault((f.src, f.ss), []).append((f, "s", f.dst))
            uses.setdefault((f.dst, f.ds), []).append((f, "d", f.src))
        for f in self.flows:
            f.off = {"s": 0.0, "d": 0.0}
        for (nid, side), lst in uses.items():
            if len(lst) < 2:
                continue
            axis = (lambda o: self.nodes[o].icon.cx) if side in ("t", "b") else (lambda o: self.nodes[o].icon.cy)
            lst = sorted(lst, key=lambda t: (axis(t[2]), t[0].src, t[0].dst))
            k = len(lst)
            straight = [t for t in lst if t[0].mode in ("straight", "V")]
            if len(straight) == 1 and k <= 3:
                me = axis(nid)
                st = straight[0]
                for t in lst:
                    if t is st:
                        continue
                    t[0].off[t[1]] = -self.PORT if axis(t[2]) < me else self.PORT
                below = [t for t in lst if t is not st and t[0].off[t[1]] > 0]
                above = [t for t in lst if t is not st and t[0].off[t[1]] < 0]
                if len(below) > 1 or len(above) > 1:
                    straight = []
                else:
                    continue
            for j, (g, end, _o) in enumerate(lst):
                g.off[end] = -self.PORT + 2 * self.PORT * j / (k - 1)

    def _port(self, nid, side, off):
        b = self.nodes[nid].icon
        if side == "r":
            return (b.r, b.cy + off)
        if side == "l":
            return (b.x, b.cy + off)
        if side == "b":
            return (b.cx + off, b.b)
        return (b.cx + off, b.y)

    def _frame_edges(self):
        """Every drawn group border as four segments: a flow never runs along one (it would read as the border)."""
        out = []
        for g in self.groups.values():
            if g.style.line is None:
                continue
            fr = g.frame
            out += [((fr.x, fr.y), (fr.r, fr.y)), ((fr.x, fr.b), (fr.r, fr.b)), ((fr.x, fr.y), (fr.x, fr.b)),
                    ((fr.r, fr.y), (fr.r, fr.b))]
        return out

    @staticmethod
    def _runs_along(p, q, e1, e2, tol) -> bool:
        """Segment p-q runs parallel to segment e1-e2 within tol, with some overlap along their length."""
        ph = abs(p[1] - q[1]) < 1e-9
        eh = abs(e1[1] - e2[1]) < 1e-9
        if ph != eh:
            return False
        if ph:
            if abs(p[1] - e1[1]) > tol:
                return False
            lo, hi = sorted((p[0], q[0]))
            elo, ehi = sorted((e1[0], e2[0]))
        else:
            if abs(p[0] - e1[0]) > tol:
                return False
            lo, hi = sorted((p[1], q[1]))
            elo, ehi = sorted((e1[1], e2[1]))
        return min(hi, ehi) - max(lo, elo) > 0.02

    @staticmethod
    def _free_xs(a, b, obstacles, edges, own) -> list:
        """x positions for the vertical leg of a Z between a and b: the middles of the gaps left by every mark, caption
        and header in the leg's height and every group border (kept 0.06in off), widest gap first, then fractions."""
        lo, hi = sorted((a[0], b[0]))
        ylo, yhi = sorted((a[1], b[1]))
        bad = []
        for bx_, what, nid in obstacles:
            if bx_.y < yhi + 0.02 and bx_.b > ylo - 0.02:
                bad.append((bx_.x - 0.03, bx_.r + 0.03))
        for e1, e2 in edges:
            if abs(e1[0] - e2[0]) < 1e-9 and min(e1[1], e2[1]) < yhi and max(e1[1], e2[1]) > ylo:
                bad.append((e1[0] - 0.06, e1[0] + 0.06))
        bad.sort()
        free, x = [], lo + 0.06
        for b0, b1 in bad:
            if b0 > x:
                free.append((x, min(b0, hi - 0.06)))
            x = max(x, b1)
        if x < hi - 0.06:
            free.append((x, hi - 0.06))
        free = [(u, v) for u, v in free if v - u > 0.0]
        free.sort(key=lambda t: -(t[1] - t[0]))
        out = [(u + v) / 2 for u, v in free]
        out += [lo + (hi - lo) * fr for fr in (0.5, 0.35, 0.65, 0.2, 0.8, 0.12, 0.88)]
        return out

    def _route(self, f: _Flow, obstacles, taken=()):
        """The first candidate route clear of every mark, caption and header (its own two icons only at its ends),
        that never runs along a group border or along another flow."""
        own = (f.src, f.dst)
        ns, nd = self.nodes[f.src], self.nodes[f.dst]
        a = self._port(f.src, f.ss, f.off["s"])
        b = self._port(f.dst, f.ds, f.off["d"])
        edges = self._frame_edges()

        def clear(pts):
            for p, q in zip(pts, pts[1:]):
                for bx_, what, nid in obstacles:
                    if nid in own and what.startswith("unit"):
                        continue
                    if nid in own and what.startswith("icon"):
                        if _seg_hits(p, q, bx_.inset(0.01), pad=0.0):      # its own icons, at its ends only
                            return what
                        continue
                    if _seg_hits(p, q, bx_):
                        return what
                for e1, e2 in edges:
                    if self._runs_along(p, q, e1, e2, 0.05):
                        return "a group border"
                for e1, e2 in taken:
                    if self._runs_along(p, q, e1, e2, 0.06):
                        return "another flow"
            return None

        cands = []
        if f.mode == "U":
            pass                                                 # built with the fallbacks below
        elif f.mode == "V":
            cands.append([a, (a[0], b[1])] if abs(a[0] - b[0]) < 1e-6 else [a, (a[0], (a[1] + b[1]) / 2),
                                                                          (b[0], (a[1] + b[1]) / 2), b])
        elif f.mode == "straight" and abs(a[1] - b[1]) < 1e-6:
            cands.append([a, b])
        elif f.mode == "L":
            cands.append([a, (b[0], a[1]), b])
        elif f.mode in ("straight", "Z"):
            if f.bend is not None:
                xs = [a[0] + (b[0] - a[0]) * f.bend]
            else:
                xs = self._free_xs(a, b, obstacles, edges, own)
            for gx in xs:
                cands.append([a, (gx, a[1]), (gx, b[1]), b])
        elif f.mode == "C":                                      # one column: a C route through a side gutter
            if f.ss == "r":
                gx0 = max(ns.icon.r, nd.icon.r, ns.cap.r, nd.cap.r)
                xs = [gx0 + d for d in (0.12, 0.05, 0.2, 0.3)]
            else:
                gx0 = min(ns.icon.x, nd.icon.x, ns.cap.x, nd.cap.x)
                xs = [gx0 - d for d in (0.12, 0.05, 0.2, 0.3)]
            cands += [[a, (gx, a[1]), (gx, b[1]), b] for gx in xs]
        # fallbacks, so the right drawing is the easy one: an L into the top of a node below, then a U over the row
        S, D = ns.icon, nd.icon
        if f.over or f.mode != "L":
            Ls = []
            if D.y > S.cy + 0.1 and abs(D.cx - S.cx) > 0.3:
                aa = (S.r, S.cy) if D.cx > S.cx else (S.x, S.cy)
                for dx in (0.0, -0.09, 0.09):
                    Ls.append([aa, (D.cx + dx, S.cy), (D.cx + dx, D.y)])
            if D.b < S.y - 0.1 and abs(D.cx - S.cx) > 0.3:          # up and across into the side of a node above
                bb = (D.x, D.cy) if S.cx < D.cx else (D.r, D.cy)
                for dx in (0.0, 0.09, -0.09):
                    Ls.append([(S.cx + dx, S.y), (S.cx + dx, D.cy), bb])
            if not self._cap_below(ns) and D.y > S.b + 0.1 and abs(D.cx - S.cx) > 0.3:   # a pin: down, then across
                bb = (D.x, D.cy) if S.cx < D.cx else (D.r, D.cy)
                Ls.append([(S.cx, S.b), (S.cx, D.cy), bb])
            if not self._cap_below(nd) and D.b < S.y - 0.1 and abs(D.cx - S.cx) > 0.3:   # across, then up into a pin
                aa = (S.r, S.cy) if D.cx > S.cx else (S.x, S.cy)
                Ls.append([aa, (D.cx, S.cy), (D.cx, D.b)])
            ups = []
            if abs(D.cx - S.cx) > 0.3:
                top = min(S.y, D.y)
                so = f.off["s"] if f.mode == "U" else 0.0
                do = f.off["d"] if f.mode == "U" else 0.0
                for d in (0.12, 0.18, 0.26, 0.36, 0.46, 0.56, 0.66, 0.76):
                    for dx in ((0.0,) if f.mode == "U" else (0.0, 0.09, -0.09)):
                        ly = top - d
                        ups.append([(S.cx + so + dx, S.y), (S.cx + so + dx, ly), (D.cx + do - dx, ly),
                                    (D.cx + do - dx, D.y)])
            downs = []
            if not self._cap_below(ns) and not self._cap_below(nd) and abs(D.cx - S.cx) > 0.3:
                bot = max(S.b, D.b)
                for d in (0.12, 0.18, 0.26, 0.36):
                    downs.append([(S.cx, S.b), (S.cx, bot + d), (D.cx, bot + d), (D.cx, D.b)])
            cands = (ups + Ls + downs) if f.over else (cands + Ls + downs + ups)
        whys = []
        best = None
        for k, pts in enumerate(cands):
            pts = _clean(pts)
            if len(pts) < 2:
                continue
            why = clear(pts)
            if why is None:
                (px, py), (qx, qy) = pts[-2], pts[-1]
                if abs(px - qx) + abs(py - qy) < LAST_LEG - 1e-6:
                    why = "a final leg under %.2fin (the arrowhead would miss the icon)" % LAST_LEG
            if why is None:
                cost = (_crossings(pts, taken), k)      # the fewest crossings with the flows already drawn, then order
                if best is None or cost < best[0]:
                    best = (cost, pts)
                if cost[0] == 0:
                    break
                continue
            if why not in whys:
                whys.append(why)
        if best is not None:
            return best[1]
        raise GeometryError("flow %s to %s" % own, need="a route clear of marks, captions and headers",
                            have="every route crosses something: %s" % ", ".join(whys[:4]),
                            hint="move a node, give the flow a bend (0..1), or enter='t'")

    def _label_sizes(self, f: _Flow, th) -> list:
        """[(w, h)] of the label on one line, measured. A label is never wrapped (spec 1.5): one that does not fit
        LABEL_MAX_W is refused."""
        face = measure.face_for(txt._default_face(th), False)
        one = measure.width_in(f.label, LABEL_PT, face) * measure.SLACK + LABEL_INS.l + LABEL_INS.r + 0.01
        paras = [Para((Run(f.label, role="ink", size=LABEL_PT),), align="center")]
        f.label_paras = paras
        if one > LABEL_MAX_W:
            self._problem(Overflows("flow label %r" % f.label, need=round(one, 3), have=LABEL_MAX_W, unit="in",
                                    hint="a flow label names what moves in a few words, on one line"))
        w = min(one, LABEL_MAX_W)
        h = math.ceil(txt.need_height(paras, w, th, LABEL_INS) * 10000 + 1) / 10000.0
        return [(w, h)]

    def _ok_box(self, b: Box, hard, frames, area: Box, segs=None, poke: bool = True):
        if not area.contains(b, tol=1e-6):
            return False
        for o in hard:
            if _inter(b, o, CLEAR):
                return False
        for fr in frames:
            inside = fr.x + FRAME_CLEAR <= b.x and b.r <= fr.r - FRAME_CLEAR and fr.y + FRAME_CLEAR <= b.y and \
                b.b <= fr.b - FRAME_CLEAR
            apart = not _inter(b, fr, CLEAR)
            ow = min(b.r, fr.r) - max(b.x, fr.x)
            oh = min(b.b, fr.b) - max(b.y, fr.y)
            # a knock-out may sit across a border when it reaches in from outside, no deeper than FRAME_POKE
            # (gate P05 reads an overlap under 0.10 x 0.10 as none; gate P04 judges only children that start inside)
            starts_out = b.x < fr.x - 0.025 or b.y < fr.y - 0.025         # gate P04 reads it as no child of the frame
            shallow = poke and starts_out and (0 < ow <= FRAME_POKE or 0 < oh <= FRAME_POKE)
            if not (inside or apart or shallow):
                return False
        for p, q in segs or ():
            if _seg_hits(p, q, b, pad=0.01):
                return False
        return True

    def _place_labels(self, th, area: Box):
        """Step badges first (one placement per slide, beside the source end, where the reader starts), then labels,
        which may sit anywhere along their segment."""
        hard = [b for b, what, _ in self._obstacles()]
        frames = [g.frame for g in self.groups.values() if g.style.line is not None]
        all_segs = [(f, list(zip(f.points, f.points[1:]))) for f in self.flows]
        segs_all = [s_ for _g, ss in all_segs for s_ in ss]
        self._badges = []
        for f in self.flows:
            if f.step is None:
                continue
            try:
                f.badge = self._badge_place(f, hard, frames, area, segs_all)
            except Overflows as err:
                self._problem(err)
                continue
            hard.append(f.badge)
            self._badges.append((f, f.badge))
        for f in self.flows:
            if f.label is None:
                continue
            self._place_one_label(f, th, hard, frames, area, all_segs)

    def _place_one_label(self, f: _Flow, th, hard, frames, area, all_segs):
        """The label on one line beside a segment long enough to hold it (its length at least the label's extent
        plus 0.2in), the longest first, within reach of the segment's midpoint; clear of every mark, caption, header,
        badge and label and of every flow line, its own included; wholly inside or wholly outside every group frame;
        first at least 0.3in from any other flow and on the side away from a parallel one, then closer."""
        (w, h), = self._label_sizes(f, th)
        mine = list(zip(f.points, f.points[1:]))
        others = [s_ for g, ss in all_segs if g is not f for s_ in ss]

        def length(sg):
            (p, q) = sg
            return abs(p[0] - q[0]) + abs(p[1] - q[1])

        def horiz(sg):
            return abs(sg[0][1] - sg[1][1]) < 1e-9

        def fits(sg):
            return length(sg) >= (w if horiz(sg) else h) + 0.2

        def near(b):
            c = (b.cx, b.cy)
            return min((_dist_pt_seg(c, p, q) for p, q in others), default=9.0)

        segs = sorted(mine, key=lambda sg: (not fits(sg), -length(sg)))
        placed = None
        for apart, poke in ((0.3, False), (0.3, True), (0.0, False), (0.0, True)):
            for (p, q) in segs:
                mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
                hz = horiz((p, q))
                # beside the segment, near its midpoint first, else anywhere along it (spec 1.5: within reach of the
                # edge); the label's centre never runs past the segment's ends
                half = max(0.0, length((p, q)) / 2 - (w if hz else h) / 2)
                shifts = [0.0]
                k = 1
                while k * 0.1 <= half + 1e-9:
                    shifts += [-k * 0.1, k * 0.1]
                    k += 1
                shifts += [-half, half]
                for sh in shifts:
                    if hz:
                        cx = mx + sh
                        opts = [Box(cx - w / 2, my - CLEAR - h, w, h), Box(cx - w / 2, my + CLEAR, w, h)]
                    else:
                        cy = my + sh
                        opts = [Box(mx + CLEAR + 0.01, cy - h / 2, w, h), Box(mx - CLEAR - 0.01 - w, cy - h / 2, w, h)]
                    opts.sort(key=lambda b: -near(b))                # the side away from a parallel flow first
                    for b in opts:
                        if apart and near(b) < apart:
                            continue
                        if self._ok_box(b, hard, frames, area, mine + others, poke):
                            placed = b
                            break
                    if placed:
                        break
                if placed:
                    break
            if placed:
                break
        if placed is None:                               # on the line, knocked out of it (spec 1.5)
            for (p, q) in segs:
                if not fits((p, q)):
                    continue
                mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
                hz = horiz((p, q))
                span = length((p, q)) / 2 - (w if hz else h) / 2 - 0.08
                for sh in (0.0, -0.1, 0.1, -0.2, 0.2, -0.3, 0.3, -0.4, 0.4):
                    if abs(sh) > max(0.0, span):
                        continue
                    cx, cy = (mx + sh, my) if hz else (mx, my + sh)
                    b = Box(cx - w / 2, cy - h / 2, w, h)
                    rest = [sg for sg in mine if sg != (p, q)] + others
                    if self._ok_box(b, hard, frames, area, rest, True):
                        placed = b
                        f.on_line = True
                        break
                if placed:
                    break
        if placed is None:
            self._problem(Overflows("flow %s to %s label %r" % (f.src, f.dst, f.label), need="%.2f x %.2fin" % (w, h),
                                    have="no clear place beside any segment",
                                    hint="shorten the label, move a node, or give the route a bend"))
            return
        f.label_box = placed
        hard.append(placed)

    def _badge_place(self, f: _Flow, hard, frames, area, segs_all) -> Box:
        """A clear spot for the step badge beside the source end, one placement per slide (spec 1.5): either side of
        the first segment, stepping along it, never over a flow line. A spot 0.45in or more from every badge already
        placed wins over a nearer one, so two badges never flank one icon."""
        B = self.badge
        e = f.points[0]
        off = B / 2 + CLEAR + 0.01
        ok = []
        walked = 0.0
        for si, (p0, p1) in enumerate(zip(f.points[:2], f.points[1:3])):    # the first segment, then the second
            ux, uy = p1[0] - p0[0], p1[1] - p0[1]
            ln = math.hypot(ux, uy) or 1.0
            ux, uy = ux / ln, uy / ln
            nx, ny = -uy, ux
            for along in (CLEAR + B / 2 + 0.02, 0.12 + B / 2, 0.24 + B / 2, 0.36 + B / 2, 0.5 + B / 2, 0.65 + B / 2,
                          0.8 + B / 2, 0.95 + B / 2):
                if along - B / 2 > ln - 0.05 or walked + along > 2.5:
                    break
                for sgn in (-1, 1):
                    cx = p0[0] + ux * along + nx * off * sgn
                    cy = p0[1] + uy * along + ny * off * sgn
                    b = Box(cx - B / 2, cy - B / 2, B, B)
                    if self._ok_box(b, hard, frames, area, segs_all):
                        ok.append(b)
            walked += ln
            if ok:
                break
        S = self.nodes[f.src].icon                       # beside the source icon, 0.04 to 0.08in clear (AWS practice)
        for gap in (0.04, 0.08):
            for cx, cy in ((S.x - gap - B / 2, S.y + B / 2 - 0.06), (S.r + gap + B / 2, S.y + B / 2 - 0.06),
                           (S.x - gap - B / 2, S.b - B / 2 + 0.06), (S.r + gap + B / 2, S.b - B / 2 + 0.06),
                           (S.x + B / 2 - 0.06, S.y - gap - B / 2), (S.r - B / 2 + 0.06, S.y - gap - B / 2)):
                b = Box(cx - B / 2, cy - B / 2, B, B)
                if _dist_pt_box(e, b) <= 0.33 and self._ok_box(b, hard, frames, area, segs_all):
                    ok.append(b)
        for b in ok:
            if all(math.hypot(b.cx - o.cx, b.cy - o.cy) >= 0.45 for _f, o in getattr(self, "_badges", [])):
                return b
        if ok:
            return ok[0]
        raise Overflows("flow %s to %s step %d badge" % (f.src, f.dst, f.step), need=B,
                        have="no clear place beside its source end", hint="move a node or give the route a bend")

    # ------------------------------------------------------------------ drawing
    def _bg(self, gid, th) -> str:
        while gid is not None:
            g = self.groups[gid]
            if g.style.fill is not None:
                return g.style.fill
            gid = g.parent
        return "paper"

    def _lead(self, g) -> float:
        h = g.style.header
        if h[0] == "square" or (h[0] == "vendor" and h[2]):
            return TAB + 0.07
        if h[0] == "vendor":
            return 0.05 + 0.24 + 0.06
        if h[0] == "above":
            return 0.24 + 0.06
        if h[0] == "glyph":
            return 0.06 + 0.20 + 0.06
        if h[0] == "label":
            return 0.08
        return 0.0

    def _depth(self, g) -> int:
        d, p = 0, g.parent
        while p is not None:
            d, p = d + 1, self.groups[p].parent
        return d

    def _label_bold(self, g) -> bool:
        """aws: group labels regular at every level (toolkit slide 25); azure and house: bold on the top two levels
        (spec 1.2). A house section head and a rail tab are bold."""
        if g.style.header[0] in ("section",) or g.kind == "rail":
            return True
        return self.grammar != "aws" and self._depth(g) < 2

    def _prep_header(self, g: _Group, th):
        """Measure the group's label (one line, refused when it does not fit) and record what its header occupies,
        so flows, labels and badges keep clear of it."""
        h = g.style.header
        f = g.frame
        if h[0] == "bar":
            paras = [Para((Run(g.label, role=prims.ON_FILL[h[1]], bold=True, size=BAR_PT),), align="center")]
            fit = txt.check_fit("group %s label" % g.id, paras, (f.w - 0.2, 100), th)
            if fit.n_lines > 1:
                self._problem(Overflows("group %s label %r" % (g.id, g.label), need=fit.n_lines, have=1,
                                        unit="lines", hint="a header names the region in a few words"))
            g.label_paras = paras
            g.label_h = math.ceil(txt.need_height(paras, f.w - 0.2, th) * 10000 + 1) / 10000.0
            g.label_w = f.w - 0.2
            g.header_box = Box(f.x, f.y, f.w, BAR_H)
            face = measure.face_for(txt._default_face(th), True)
            tw = min(f.w, measure.width_in(g.label, BAR_PT, face) * measure.SLACK + 0.2)
            g.route_box = Box(f.cx - tw / 2, f.y, tw, BAR_H)      # a flow may cross a bar, never its words
            return
        if h[0] == "lane" and not g.label:
            g.label_paras = None
            g.header_box = Box(f.x, f.y, 0.01, 0.01)
            return
        role = "ink-muted" if h[0] == "lane" else "ink-deep"
        bold = self._label_bold(g) if h[0] != "lane" else True
        paras = [Para((Run(g.label, role=role, bold=bold, size=GROUP_PT),))]
        lead = self._lead(g)
        avail = f.w - lead - 0.08 - (CORNER + 0.08 if g.style.corner else 0.0)
        face = measure.face_for(txt._default_face(th), bold)
        lw = min(avail, measure.width_in(g.label, GROUP_PT, face) * measure.SLACK + 0.02)
        try:
            fit = txt.check_fit("group %s label" % g.id, paras, (lw, 100), th)
        except Overflows as err:                          # a word wider than the group
            self._problem(err)
            lw = measure.width_in(g.label, GROUP_PT, face) * measure.SLACK + 0.02
            fit = txt.check_fit("group %s label" % g.id, paras, (lw, 100), th)
        if fit.n_lines > 1 or lw <= 0:
            self._problem(Overflows("group %s label %r" % (g.id, g.label), need=fit.n_lines, have=1, unit="lines",
                                    hint="the group is %.2fin wide; a shorter label or a wider span" % f.w))
        lh = math.ceil(txt.need_height(paras, lw, th) * 10000 + 1) / 10000.0
        g.label_paras, g.label_w, g.label_h = paras, lw, lh
        if h[0] == "square" or (h[0] == "vendor" and h[2]):
            g.label_y = f.y + TAB / 2 - lh / 2
            g.header_box = Box(f.x, f.y, lead + lw, TAB)
        elif h[0] == "vendor":
            g.label_y = f.y + 0.05 + 0.12 - lh / 2
            g.header_box = Box(f.x, f.y, lead + lw, 0.05 + 0.24 + 0.02)
        elif h[0] == "edge":                             # centred on the top border, knocked out of the line
            g.label_x = f.cx - lw / 2
            g.label_y = f.y - lh / 2
            g.header_box = Box(g.label_x - 0.04, g.label_y, lw + 0.08, lh)
        elif h[0] == "above":                            # icon and label in the band above the frame
            top = g.span.y
            g.label_y = top + (ABOVE_H - lh) / 2
            g.header_box = Box(f.x, top, lead + lw, ABOVE_H)
        elif h[0] == "section":
            g.label_x = f.x
            g.label_y = f.y + 0.07
            g.header_box = Box(f.x, f.y, lw, 0.07 + lh)
        else:
            g.label_y = f.y + 0.06
            g.header_box = Box(f.x, f.y, lead + lw, 0.06 + lh)
        if g.style.corner:
            g.corner_box = Box(f.r - CORNER - 0.05, f.y + 0.05, CORNER, CORNER)

    def _draw_group(self, slide, g: _Group, th, nm):
        st = g.style
        h = st.header
        base = "%s.g.%s" % (nm, g.id)
        if h[0] == "square":
            sq = Box(g.frame.x, g.frame.y, TAB, TAB)
            prims.rect(slide, sq, fill=h[1], name=base + ".tab", theme=th)     # under the frame: the corner is notation
        elif h[0] == "vendor" and h[2]:
            icons.vendor(slide, h[1], Box(g.frame.x, g.frame.y, TAB, TAB), name="%s-g-%s-tab" % (nm, g.id),
                         alt=_group_alt(g), theme=th)
        if st.line is not None or st.fill is not None:
            kind = "band" if g.band else "frame"
            if st.radius:
                fr = prims._add(slide, "ROUNDED_RECTANGLE", g.frame, "%s.%s" % (base, kind))
                fr.adjustments[0] = prims._adj(st.radius, g.frame)
            else:
                fr = prims._add(slide, "RECTANGLE", g.frame, "%s.%s" % (base, kind))
            prims.set_fill(fr, st.fill, theme=th)
            if st.line is not None:
                prims.set_line(fr, st.line, st.weight, theme=th, dash=st.dash)
            else:
                prims.set_line(fr, None, theme=th)
            prims._drop_text(fr)
            ooxml.finish(fr)
        bg = self._bg(g.id, th)
        if h[0] == "square":
            gl = Box(g.frame.x + (TAB - TAB_GLYPH) / 2, g.frame.y + (TAB - TAB_GLYPH) / 2, TAB_GLYPH, TAB_GLYPH)
            glyphs.glyph(slide, h[2], gl, role="paper", shape_name=base + ".tab.icon", theme=th)
        elif h[0] == "vendor" and not h[2]:
            icons.vendor(slide, h[1], Box(g.frame.x + 0.05, g.frame.y + 0.05, 0.24, 0.24),
                         name="%s-g-%s-tab" % (nm, g.id), alt=_group_alt(g), theme=th)
        elif h[0] == "above":
            icons.vendor(slide, h[1], Box(g.frame.x, g.span.y + (ABOVE_H - 0.24) / 2, 0.24, 0.24),
                         name="%s-g-%s-tab" % (nm, g.id), alt=_group_alt(g), theme=th)
        elif h[0] == "glyph":
            glyphs.glyph(slide, h[1], Box(g.frame.x + 0.06, g.frame.y + 0.06, 0.20, 0.20), role=h[2],
                         shape_name=base + ".tab.icon", theme=th)
        if g.style.corner:
            icons.vendor(slide, g.style.corner, g.corner_box, name="%s-g-%s-corner" % (nm, g.id),
                         alt="Network security group", theme=th)
        if h[0] == "bar":
            bar = Box(g.frame.x, g.frame.y, g.frame.w, BAR_H)
            if st.radius:                                # a header tab: top corners rounded (spec 3.3)
                sh = prims._add(slide, "ROUND_2_SAME_RECTANGLE", bar, base + ".bar")
                sh.adjustments[0] = prims._adj(TAB_RADIUS, bar)
                sh.adjustments[1] = 0.0
                prims.set_fill(sh, h[1], theme=th)
                prims.set_line(sh, None, theme=th)
                prims._drop_text(sh)
                ooxml.finish(sh)
            else:
                prims.rect(slide, bar, fill=h[1], name=base + ".bar", theme=th)
            txt.textbox(slide, Box(bar.x + 0.1, bar.cy - g.label_h / 2, g.label_w, g.label_h), g.label_paras,
                        base + ".label", th, background=h[1])
            return
        if h[0] == "section":
            parent_inner = self.groups[g.parent].inner if g.parent else self._area
            if g.frame.y - parent_inner.y > 0.12:          # a rule between sections, never under the header bar
                prims.hairline(slide, (g.frame.x, g.frame.y + 0.02), (g.frame.r, g.frame.y + 0.02), role="hairline",
                           name=base + ".rule", theme=th)
        if g.label_paras is None:
            return
        if h[0] in ("edge", "section"):
            x0 = g.label_x
        else:
            x0 = g.frame.x + self._lead(g)
        lbg = self._bg(g.parent, th) if h[0] in ("edge", "above") else bg
        sh = txt.textbox(slide, Box(x0, g.label_y, g.label_w, g.label_h), g.label_paras, base + ".label", th,
                         background=lbg)
        if h[0] == "edge":                               # knock the label out of the border it sits on
            prims.set_fill(sh, lbg, theme=th)

    def _ink(self, n: _Node):
        """(l, t, r, b) of a picture mark's ink as fractions of its canvas, or None (a glyph or a monogram). Measured
        on the artwork's own pixels (alpha above 16), so marks with transparent margins draw at one optical size."""
        kind, _, key = n.mark.partition(":")
        if kind == "vendor":
            return _ink_box(str(icons.vendor_path(key)), None)
        if kind == "mark":
            entry = icons.mark_registry(self.marks_registry).get(key)
            path = icons.marks_dir(self.marks_registry) / entry["file"]
            return _ink_box(str(path), entry["sha256"])
        return None

    def _ink_fit(self):
        """Every picture mark's icon box shrinks to its ink's aspect, centred where it was, so a flow lands on the
        artwork rather than on a transparent margin, and the ink fills the tier's size (spec 1.3)."""
        for n in self.nodes.values():
            if n.hidden or n.icon is None:
                continue
            ink = self._ink(n)
            n.ink = ink
            if ink is None:
                continue
            l, t, r, b, pw, ph = ink
            ar = ((r - l) * pw) / max(1e-9, (b - t) * ph)
            ic = n.icon
            if ar >= ic.w / ic.h:
                w, h = ic.w, ic.w / ar
            else:
                w, h = ic.h * ar, ic.h
            n.icon = Box(ic.cx - w / 2, ic.cy - h / 2, w, h)

    def _draw_node(self, slide, n: _Node, th, nm):
        kind, _, key = n.mark.partition(":")
        suffix = "%s-n-%s" % (nm, n.id)
        pic = None
        if kind == "vendor":
            pic = icons.vendor(slide, key, n.icon, name=suffix, alt=n.name, theme=th)
        elif kind == "mark":
            ink = getattr(n, "ink", None)
            big = n.icon
            if ink is not None:                          # rasterise for the uncropped size, so the crop keeps 2x
                l, t, r, b = ink[:4]
                big = Box(n.icon.x, n.icon.y, n.icon.w / max(0.05, r - l), n.icon.h / max(0.05, b - t))
            pic = icons.mark(slide, key, big, name=suffix, registry=self.marks_registry)   # alt: the product
        elif kind == "glyph":
            glyphs.glyph(slide, key, n.icon, role="ink-strong", shape_name="%s.n.%s.icon" % (nm, n.id), theme=th)
        else:
            icons.monogram(slide, n.icon, key, role="ink-strong", name="%s.n.%s.icon" % (nm, n.id), theme=th)
        ink = getattr(n, "ink", None)
        if pic is not None and ink is not None:
            _crop_to_ink(pic, ink, n.icon)
        txt.textbox(slide, n.cap, n.paras, "%s.n.%s.caption" % (nm, n.id), th, background=self._bg(n.group, th))

    def _badge(self, slide, box: Box, n: int, th, name):
        fill = BADGE_FILL[self.grammar]
        ink = prims.ON_FILL.get(fill, "paper")
        paras = [Para((Run(str(n), role=ink, bold=True, size=self.badge_pt),), align="center")]
        txt.check_contrast(name, paras, th, fill)
        txt.check_fit(name, paras, (box.w * math.sqrt(0.5), box.h * math.sqrt(0.5)), th)
        sh = prims._add(slide, "OVAL", box, name)
        prims.set_fill(sh, fill, theme=th)
        prims.set_line(sh, None, theme=th)
        txt.write(sh.text_frame, paras, th, measure.ZERO, anchor="middle", background=fill)
        ooxml.finish(sh)
        return sh

    def _kinds(self) -> list:
        """The flow kinds drawn, when more than one line style is on the slide (a key is needed: spec 1.4)."""
        kinds = [k for k in FLOW_KINDS if any(f.kind == k for f in self.flows)]
        return kinds if len(kinds) > 1 or (kinds and kinds[0] != "data") else []

    def _flow_line(self, slide, points, kind, name, th):
        """One connector in the grammar's flow notation (FLOW_BY)."""
        role, wt, head, hlen = FLOW_BY[self.grammar]
        if len(points) == 2:
            sh = prims.connect(slide, points[0], points[1], head="end", dash=FLOW_KINDS[kind], role=role,
                               weight_pt=wt, name=name, theme=th)
        else:
            sh = prims.elbow(slide, points, head="end", dash=FLOW_KINDS[kind], role=role, weight_pt=wt, name=name,
                             theme=th)
        tail = sh._element.find(".//" + _AQ + "ln/" + _AQ + "tailEnd")
        if tail is not None:
            tail.set("type", head)
            tail.set("w", "med")
            tail.set("len", hlen)
        return sh

    def _key_line(self, slide, x0, y, kind, nm, th):
        """A key sample: a short line in the grammar's flow stroke and dash, no head (it points at nothing, so it is
        named state.*: the line encodes a flow kind, gate P06 does not judge it as an arrow)."""
        role, wt, _head, _len = FLOW_BY[self.grammar]
        sh = prims._connector(slide, (x0, y), (x0 + 0.45, y), "state.%s.legend.key.%s" % (nm, kind))
        prims.set_line(sh, role, wt, theme=th, dash=FLOW_KINDS[kind])
        ooxml.finish(sh)
        return sh

    def _key_row(self, slide, box: Box, kinds, th, nm):
        """The flow-kind key as one row: a short line in the grammar's notation and its meaning, per kind."""
        x = box.x
        for k in kinds:
            paras = [Para((Run(FLOW_KEY[k], role="ink-muted", size=LEGEND_PT),))]
            face = measure.face_for(txt._default_face(th), False)
            tw = measure.width_in(FLOW_KEY[k], LEGEND_PT, face) * measure.SLACK + 0.04
            h = math.ceil(txt.need_height(paras, tw, th) * 10000 + 1) / 10000.0
            if x + 0.55 + tw > box.r + 1e-6:
                self._problem(Overflows("flow key", need=round(x + 0.55 + tw - box.x, 3), have=round(box.w, 3),
                                        unit="in"))
                return
            self._key_line(slide, x, box.y + h / 2, k, nm, th)
            txt.textbox(slide, Box(x + 0.55, box.y, tw, h), paras, "%s.legend.key.%s.text" % (nm, k), th)
            x += 0.55 + tw + 0.30

    def _legend(self, slide, box: Box, where: str, th, nm):
        items = sorted(self.legend.items())
        kinds = self._kinds()
        B = self.badge
        tw_gap = B + 0.10
        if where == "right":
            cols = [box]
        else:
            ncol = self.legend_cols or max(1, min(4, math.ceil(len(items) / 3)))
            cols = box.split_cols(ncol, 0.25)
        per = math.ceil(len(items) / len(cols)) if items else 0
        y_end = box.y
        for ci, col in enumerate(cols):
            y = col.y
            for n, t in items[ci * per:(ci + 1) * per]:
                paras = [Para((Run(t, role="ink", size=LEGEND_PT),))]
                tw = col.w - tw_gap
                h = math.ceil(txt.need_height(paras, tw, th) * 10000 + 1) / 10000.0
                rowh = max(h, B)
                if y + rowh > col.b + 1e-6:
                    self._problem(Overflows("step legend", need=round(y + rowh - col.y, 3), have=round(col.h, 3),
                                            hint="shorter step texts or a wider rail"))
                self._badge(slide, Box(col.x, y + (rowh - B) / 2 if h < B else y, B, B), n, th,
                            "%s.legend.%d.step" % (nm, n))
                txt.textbox(slide, Box(col.x + tw_gap, y + (rowh - h) / 2, tw, h), paras,
                            "%s.legend.%d.text" % (nm, n), th)
                y += rowh + (0.10 if where == "right" else 0.06)
            y_end = max(y_end, y)
        if kinds:
            if where == "right":
                y = y_end + 0.06
                for k in kinds:
                    paras = [Para((Run(FLOW_KEY[k], role="ink-muted", size=LEGEND_PT),))]
                    h = math.ceil(txt.need_height(paras, box.w - 0.6, th) * 10000 + 1) / 10000.0
                    if y + h > box.b + 1e-6:
                        self._problem(Overflows("flow key", need=round(y + h - box.y, 3), have=round(box.h, 3)))
                    self._key_line(slide, box.x, y + h / 2, k, nm, th)
                    txt.textbox(slide, Box(box.x + 0.55, y, box.w - 0.6, h), paras,
                                "%s.legend.key.%s.text" % (nm, k), th)
                    y += h + 0.08
            else:
                self._key_row(slide, Box(box.x, y_end + 0.02, box.w, max(0.2, box.b - y_end)), kinds, th, nm)

    def _validate_steps(self):
        used = sorted(f.step for f in self.flows if f.step is not None)
        if len(used) != len(set(used)):
            raise GeometryError("steps", need="each step number once", have=used)
        if set(used) != set(self.legend):
            raise GeometryError("steps", need="a legend line for every numbered flow and no other",
                                have="flows %s, legend %s" % (used, sorted(self.legend)))
        for f in self.flows:
            for nid in (f.src, f.dst):
                if self.nodes[nid].hidden:
                    raise GeometryError("flow %s to %s" % (f.src, f.dst), need="visible nodes",
                                        have="%s is folded into its group's +N more chip" % nid)

    def render(self, slide, box: Box, theme=None, name: str = "arch", *, legend: str | None = None,
               legend_w: float = 2.35, legend_h: float = 1.0, legend_cols: int | None = None,
               draft: bool = False) -> dict:
        """Lay out, route, measure and draw the diagram inside box. legend: 'right' or 'bottom' places the steps
        legend rail (default right when there are steps); legend_cols sets the bottom rail's columns. A diagram with
        more than one line style and no steps draws its flow key as one row along the foot. Returns {marks, actors,
        icons, flows, labelled, badge_only, boxed_alone, hidden, groups, problems}. draft=True is for iterating on a
        layout only: a caption, height, route, label or badge that does not fit is listed in problems and drawn
        anyway (an unlabelled flow then fails gate P26), instead of raising."""
        th = prims.theme_of(theme)
        self.draft = bool(draft)
        self.problems = []
        self.badge, self.badge_pt = BADGE_BY[self.grammar]
        self.legend_cols = legend_cols
        nm = str(name)
        if not re.fullmatch(r"[A-Za-z0-9_-]+", nm):
            raise GeometryError("diagram name", need="letters, digits, - and _", have=nm)
        if not self.nodes:
            raise GeometryError("diagram", need="at least one node", have=0)
        if legend is None and self.legend:
            legend = "right"
        if legend not in (None, "right", "bottom"):
            raise GeometryError("legend", need="right or bottom", have=legend)
        area = box
        rail = None
        keyrow = None
        if legend is None and self._kinds():                    # a key whenever more than one line style
            keyrow = Box(box.x + MARGIN, box.b - 0.20, box.w - 2 * MARGIN, 0.20)
            area = Box(box.x, box.y, box.w, box.h - 0.30)
        if legend == "right":
            rail = Box(box.r - legend_w, box.y + MARGIN, legend_w, box.h - 2 * MARGIN)
            area = Box(box.x, box.y, box.w - legend_w - 0.15, box.h)
        elif legend == "bottom":
            rail = Box(box.x + MARGIN, box.b - legend_h, box.w - 2 * MARGIN, legend_h)
            area = Box(box.x, box.y, box.w, box.h - legend_h - 0.12)
        self._area = area
        with prims.use(th):
            self._widths(None, area, th)
            self._place(None, area)
            for g in self.groups.values():                       # header boxes before routing
                self._prep_header(g, th)
                if g.more:
                    face = measure.face_for(txt._default_face(th), False)
                    t = "+%d more" % g.more
                    cw = measure.width_in(t, MORE_PT, face) * measure.SLACK + 0.30
                    mb = g.more_box
                    g.chip = Box(mb.cx - cw / 2, mb.cy - 0.15, cw, 0.30)
                    if cw > mb.w:
                        raise Overflows("group %s +N more chip" % g.id, need=round(cw, 3), have=round(mb.w, 3))
            moved = []
            for nid, to, axis in self._aligns:              # every move first, so chained moves do not block
                n, t = self.nodes[nid], self.nodes[to]
                if n.hidden or t.hidden:
                    raise GeometryError("align %s to %s" % (nid, to), need="visible nodes", have="a folded node")
                dy = t.icon.cy - n.icon.cy if axis == "y" else 0.0
                dx = t.icon.cx - n.icon.cx if axis == "x" else 0.0
                n.icon = Box(n.icon.x + dx, n.icon.y + dy, n.icon.w, n.icon.h)
                n.cap = Box(n.cap.x + dx, n.cap.y + dy, n.cap.w, n.cap.h)
                moved.append((n, t, dx, dy))
            for n, t, dx, dy in moved:
                icon, cap = n.icon, n.cap
                inner = self.groups[n.group].inner if n.group else self._area
                if n.anchor in PIN_SIDES:
                    inner = self.groups[n.group].span if n.group else self._area
                others = [b for m in self.nodes.values() if m is not n and not m.hidden for b in (m.icon, m.cap)]
                lo = min(icon.y, cap.y)
                if (n.anchor not in PIN_SIDES and (lo < inner.y - 1e-6 or cap.b > inner.b + 1e-6 or
                                                   min(icon.x, cap.x) < inner.x - 1e-6 or
                                                   max(icon.r, cap.r) > inner.r + 1e-6)) or \
                        any(_inter(icon, b, 0.04) or _inter(cap, b, 0.04) for b in others):
                    blockers = [m.id for m in self.nodes.values() if m is not n and not m.hidden and
                                (_inter(icon, m.icon, 0.04) or _inter(icon, m.cap, 0.04) or _inter(cap, m.icon, 0.04)
                                 or _inter(cap, m.cap, 0.04))]
                    self._problem(GeometryError("align %s to %s" % (n.id, t.id),
                                                need="room to move %s %.2fin" % (n.id, dy or dx),
                                                have="in the way: %s" % (", ".join(blockers) or "its group's edge"),
                                                hint="align a node with free room beside it, or move it to the "
                                                     "same row or column"))
            self._ink_fit()
            self._check_pins()
            self._validate_steps()
            obstacles = self._obstacles(routing=True)
            self._ports()
            taken = []
            for f in self.flows:
                try:
                    f.points = self._route(f, obstacles, taken)
                    taken += list(zip(f.points, f.points[1:]))
                except GeometryError as err:
                    if not self.draft:
                        raise
                    self.problems.append(str(err))
                    f.points = [self._port(f.src, f.ss, 0.0), self._port(f.dst, f.ds, 0.0)]
                    f.points = _clean([f.points[0], (f.points[1][0], f.points[0][1]), f.points[1]])
            self._place_labels(th, area)
            # draw: groups outer first, then flows, then nodes, then labels and badges, then the legend
            def depth(g):
                d, p = 0, g.parent
                while p is not None:
                    d, p = d + 1, self.groups[p].parent
                return d
            for g in sorted(self.groups.values(), key=depth):
                self._draw_group(slide, g, th, nm)
                if g.more:
                    prims.pill(slide, g.chip, "+%d more" % g.more, fill="card", line="hairline", role="ink-muted",
                               pt=MORE_PT, name="%s.g.%s.more" % (nm, g.id), theme=th)
            for i, f in enumerate(self.flows, start=1):
                self._flow_line(slide, f.points, f.kind, "%s.f.%d" % (nm, i), th)
            for n in self.nodes.values():
                if not n.hidden:
                    self._draw_node(slide, n, th, nm)
            for i, f in enumerate(self.flows, start=1):
                if f.label_box is not None:
                    gr = self._ground(f.label_box)
                    sh = txt.textbox(slide, f.label_box, f.label_paras, "%s.f.%d.label" % (nm, i), th,
                                     insets=LABEL_INS, anchor="middle", background=gr)
                    prims.set_fill(sh, gr, theme=th)
                if f.badge is not None:
                    self._badge(slide, f.badge, f.step, th, "%s.f.%d.step" % (nm, i))
            if rail is not None and self.legend:
                self._legend(slide, rail, legend, th, nm)
            elif keyrow is not None:
                self._key_row(slide, keyrow, self._kinds(), th, nm)
        return self.metrics()

    def _ground(self, b: Box) -> str:
        """The fill under a box: the innermost filled group frame that holds it, else paper. A knock-out takes it."""
        best = None
        for g in self.groups.values():
            if g.style.fill is None or g.frame is None or not g.frame.contains(b, tol=1e-6):
                continue
            if best is None or g.frame.w * g.frame.h < best.frame.w * best.frame.h:
                best = g
        return best.style.fill if best is not None else "paper"

    def _check_pins(self):
        """An edge pin's icon and caption keep clear of every other node and of every header; its caption lies wholly
        outside its own frame."""
        for n in self.nodes.values():
            if n.hidden or n.anchor not in PIN_SIDES:
                continue
            fr = self.groups[n.group].frame
            if _inter(n.cap, fr.inset(0.001)) and n.anchor != "edge:t":
                self._problem(GeometryError("pin %s caption" % n.id, need="outside its group's frame",
                                            have="inside", hint="give the pin's side of the frame room"))
            par = self.groups[n.group].parent
            pf = self.groups[par].frame if par is not None else self._area
            if not pf.inset(FRAME_CLEAR).contains(n.cap, tol=1e-6):
                self._problem(GeometryError("pin %s caption" % n.id, need="inside the frame around its group",
                                            have="crossing it", hint="widen the column beside the pinned edge"))
            for m in self.nodes.values():
                if m is n or m.hidden:
                    continue
                for a_, b_ in ((n.icon, m.icon), (n.icon, m.cap), (n.cap, m.icon), (n.cap, m.cap)):
                    if _inter(a_, b_, 0.03):
                        self._problem(GeometryError("pin %s" % n.id, need="clear of node %s" % m.id,
                                                    have="overlapping", hint="move the pin to another row"))
            for g in self.groups.values():
                hb = getattr(g, "header_box", None)
                if hb is not None and (_inter(n.icon, hb, 0.02) or _inter(n.cap, hb, 0.02)):
                    self._problem(GeometryError("pin %s" % n.id, need="clear of group %s's header" % g.id,
                                                have="overlapping", hint="move the pin along its edge"))

    @staticmethod
    def is_actor(mark: str) -> bool:
        """An actor or generic resource glyph (a person, the internet, a generic database): not a product mark."""
        kind, _, key = mark.partition(":")
        return kind == "glyph" or (kind == "vendor" and key.startswith(ACTOR_KEYS))

    def metrics(self) -> dict:
        """marks counts product marks only (vendor and brand marks, no actor or generic glyph); labelled counts the
        flows whose label was placed; badge_only the flows that carry only a placed step badge."""
        shown = [n for n in self.nodes.values() if not n.hidden]
        marks = [n for n in shown if n.mark.split(":")[0] in ("vendor", "mark") and not self.is_actor(n.mark)]
        return {"marks": len(marks), "actors": sum(1 for n in shown if self.is_actor(n.mark)), "icons": len(shown),
                "flows": len(self.flows),
                "labelled": sum(1 for f in self.flows if f.label_box is not None),
                "badge_only": sum(1 for f in self.flows if f.label_box is None and f.badge is not None),
                "boxed_alone": self.boxed_alone(),
                "hidden": sum(1 for n in self.nodes.values() if n.hidden), "groups": len(self.groups),
                "problems": list(getattr(self, "problems", []))}

    def boxed_alone(self) -> int:
        """Icons that are the only icon inside a drawn group of 0.6 to 2.4in a side (P26 (b) on the declared form)."""
        shown = [n for n in self.nodes.values() if not n.hidden and n.icon is not None]
        out = 0
        for n in shown:
            best = None
            for g in self.groups.values():
                if g.style.line is None or g.frame is None:
                    continue
                if g.frame.contains(n.icon) and 0.6 <= g.frame.w <= 2.4 and 0.6 <= g.frame.h <= 2.4:
                    if best is None or g.frame.w * g.frame.h < best.w * best.h:
                        best = g.frame
            if best is not None and sum(1 for m in shown if best.contains(m.icon)) == 1:
                out += 1
        return out


__all__ = ["Diagram", "GRAMMARS", "KINDS", "FLOW_KINDS", "ICON", "ACTOR_GLYPHS", "BADGE_FILL"]
