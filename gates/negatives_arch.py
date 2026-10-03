"""Planters for gate P26's diagram-type checks (track E1): each appends one architecture slide to the golden that
breaks exactly one rule, and names the text the P26 finding must carry. Discovered by negatives._discover.

    $PY gates/negatives_arch.py            # run these planters alone against the golden, P26 only
"""
from __future__ import annotations

import sys
from pathlib import Path

GATES_DIR = Path(__file__).resolve().parent
if str(GATES_DIR) not in sys.path:
    sys.path.insert(0, str(GATES_DIR))

from negatives import ARCH_KEYS, Planter, _arch_slide, theme, with_prs  # noqa: E402


def _blank(prs, variant, archetype="solution-architecture"):
    from deckkit import tag
    s = prs.slides.add_slide(prs.slide_layouts[0])
    tag.tag(s, archetype, variant)
    return s


def _frame(s, box, line, dash=None, name="frame", weight=1.25):
    """An unfilled outlined boundary frame in a notation or theme stroke."""
    from deckkit import ooxml, prims
    th = theme()
    sh = prims._add(s, "RECTANGLE", box, name)
    prims.set_fill(sh, None, theme=th)
    prims.set_line(sh, line, weight, theme=th, dash=dash)
    prims._drop_text(sh)
    ooxml.finish(sh)
    return sh


def _text(s, box, t, name, fill=None, pt=9.0):
    from deckkit import prims, text
    from deckkit.text import Para, Run
    sh = text.textbox(s, box, [Para((Run(t, size=pt),))], name, theme())
    if fill:
        prims.set_fill(sh, fill, theme=theme())
    return sh


def _mark(s, key, x, y, name, caption=True):
    from deckkit import icons
    from deckkit.canvas import Box
    pic = icons.vendor(s, key, Box(x, y, 0.42, 0.42), name=name, theme=theme())
    if caption:
        _text(s, Box(x - 0.2, y + 0.47, 0.85, 0.2), "Service %s" % name, "cap.%s" % name)
    return pic


def _arrow(s, p, q, name, head="end", dash=None):
    from deckkit import prims
    return prims.connect(s, p, q, head=head, dash=dash, name=name, theme=theme())


# ------------------------------------------------------------------ (g) heads

def p26_double_head(p, w):
    """A connector headed at both ends that is no peering: a two-way exchange is two flows."""
    def fn(prs):
        s = _arch_slide(prs, flows=2)
        _arrow(s, (0.9 + 0.42, 4.4), (2.9, 4.4), "flow.both", head="both")
        _text(s, __import__("deckkit.canvas", fromlist=["Box"]).Box(1.6, 4.18, 0.8, 0.18), "sync", "flow.both.label")
    with_prs(p, fn)


def p26_bare_peering(p, w):
    """A peering (both heads, lgDashDot) drawn with no label."""
    from deckkit import arch

    def fn(prs):
        s = _arch_slide(prs, flows=2)
        sh = _arrow(s, (0.9 + 0.42, 4.4), (2.9, 4.4), "flow.vnet.peer", head="both")
        arch._set_dash(sh, "lgDashDot")
    with_prs(p, fn)


# ------------------------------------------------------------------ (j) steps by type, (k) kinds by type, (l) nesting

def _engine_deploy(prs, steps=0, nest=0, kinds=True):
    """An arch-deploy-aws slide drawn by the engine: a Region with two AZ columns, a chain of services."""
    from deckkit import arch
    from deckkit.canvas import Box
    s = _blank(prs, "arch-deploy-aws")
    d = arch.Diagram("aws", grid=(1, 1))
    parent = None
    if kinds:
        d.group("reg", "aws-region", "Region probe", fact="2 AZs", at=(0, 0, 1, 1), grid=(1, 1))
        d.group("vpc", "aws-vpc", "VPC probe", fact="private", parent="reg", at=(0, 0, 1, 1), grid=(2, 1))
        d.group("aza", "aws-az", "AZ a", parent="vpc", at=(0, 0, 1, 1), grid=(1, 1))
        d.group("azb", "aws-az", "AZ b", parent="vpc", at=(1, 0, 1, 1), grid=(1, 1))
        d.group("sa", "aws-private-subnet", "App", parent="aza", at=(0, 0, 1, 1), grid=(5, 1))
        d.group("sb", "aws-private-subnet", "App", parent="azb", at=(0, 0, 1, 1), grid=(5, 1))
        parents = ["sa"] * 5 + ["sb"] * 5
    else:
        d.group("reg", "aws-region", "Region probe", fact="2 AZs", at=(0, 0, 1, 1), grid=(10, 1))
        parents = ["reg"] * 10
    for k in range(10):
        d.node("n%d" % k, "vendor:" + (ARCH_KEYS * 2)[k], "Service %d" % k, group=parents[k], at=(k % 5 if kinds
                                                                                                else k, 0))
    for k in range(9):
        d.flow("n%d" % k, "n%d" % (k + 1), "data %d" % k, step=(k + 1) if k < steps else None)
    if steps:
        d.steps({k + 1: "Step %d" % (k + 1) for k in range(steps)})
    d.render(s, Box(0.5, 0.9, 12.4, 5.9), theme(), name="probe", legend="bottom" if steps else None,
             legend_h=0.6, draft=True)
    return s


def p26_deploy_steps(p, w):
    """Nine numbered steps on a deployment slide (the type allows 0 to 8)."""
    with_prs(p, lambda prs: _engine_deploy(prs, steps=9))


def p26_deploy_kinds(p, w):
    """A deployment slide with one boundary kind (the type needs 4)."""
    with_prs(p, lambda prs: _engine_deploy(prs, kinds=False))


def p26_nesting(p, w):
    """Five nested dashed boundaries on an arch-* slide (at most 4)."""
    from deckkit.canvas import Box

    def fn(prs):
        s = _blank(prs, "arch-dataflow")
        for k in range(5):
            b = Box(0.6 + 0.35 * k, 1.0 + 0.3 * k, 11.8 - 0.7 * k, 5.6 - 0.6 * k)
            _frame(s, b, "rule-strong", dash="dash", name="zone.%d" % k, weight=0.75)
            _text(s, Box(b.x + 0.08, b.y + 0.04, 2.6, 0.2), "Zone %d · probe" % k, "zone.%d.label" % k)
    with_prs(p, fn)


# ------------------------------------------------------------------ (m) legend

def p26_no_key(p, w):
    """Two line styles on an arch-* slide and no key sample for the dashed one."""
    from deckkit.canvas import Box

    def fn(prs):
        s = _blank(prs, "arch-cicd")
        for k in range(4):
            _mark(s, ARCH_KEYS[k], 1.0 + k * 2.4, 3.0, "m%d" % k)
        for k in range(3):
            x0, x1 = 1.0 + k * 2.4 + 0.42, 1.0 + (k + 1) * 2.4
            _arrow(s, (x0, 3.21), (x1, 3.21), "flow.%d" % k, dash="sysDot" if k == 1 else None)
            _text(s, Box(x0 + 0.4, 2.95, 1.0, 0.18), "hand off %d" % k, "flow.%d.label" % k)
    with_prs(p, fn)


# ------------------------------------------------------------------ (s) deployment semantics, pins, changes

def _azs(s, tops_b=(1.6, 3.4)):
    """Two AZ columns (the AWS AZ dash) with two subnet tiers each; AZ b's tiers at tops_b."""
    from deckkit.canvas import Box
    for k, tops in enumerate(((1.6, 3.4), tops_b)):
        x = 1.0 + k * 5.6
        _frame(s, Box(x, 1.2, 5.2, 5.2), "aws-az", dash="dash", name="az.%d" % k)
        _text(s, Box(x + 2.0, 1.12, 1.4, 0.18), "AZ %d" % k, "az.%d.label" % k)
        for j, t in enumerate(tops):
            _frame(s, Box(x + 0.2, t, 4.8, 1.5), "aws-private-subnet", name="sub.%d.%d" % (k, j))
            _text(s, Box(x + 0.3, t + 0.05, 1.2, 0.18), "Subnet %d" % j, "sub.%d.%d.label" % (k, j))


def p26_tiers(p, w):
    """The subnet tiers of two AZ columns at different heights."""
    with_prs(p, lambda prs: _azs(_blank(prs, "arch-deploy-aws"), tops_b=(1.9, 3.7)))


def p26_span_one_az(p, w):
    """A span band laid inside one AZ column only."""
    from deckkit import ooxml, prims
    from deckkit.canvas import Box

    def fn(prs):
        s = _blank(prs, "arch-deploy-aws")
        _azs(s)
        b = Box(1.3, 2.0, 4.0, 0.9)
        for k, (p_, q_) in enumerate((((b.x, b.y), (b.r, b.y)), ((b.r, b.y), (b.r, b.b)), ((b.r, b.b), (b.x, b.b)),
                                       ((b.x, b.b), (b.x, b.y)))):
            sh = prims._connector(s, p_, q_, "state.probe.span.svc.%s" % "trbl"[k])
            prims.set_line(sh, "aws-asg", 1.25, theme=theme(), dash="dash")
            ooxml.finish(sh)
    with_prs(p, fn)


def p26_pin_flow(p, w):
    """A corner pin (*-pin) with a flow landing on it: a pin carries no edges."""
    from deckkit import icons
    from deckkit.canvas import Box

    def fn(prs):
        s = _arch_slide(prs, flows=2)
        icons.vendor(s, "aws/network/nacl", Box(6.0, 4.0, 0.22, 0.22), name="probe-g-sub-pin", theme=theme())
        _arrow(s, (4.9 + 0.42, 4.11), (6.0, 4.11), "flow.topin")
    with_prs(p, fn)


def p26_change_once(p, w):
    """A current versus target slide whose change letter marks one diagram only."""
    from deckkit import prims
    from deckkit.canvas import Box

    def fn(prs):
        s = _arch_slide(prs, variant="arch-current-target", flows=2)
        prims.disc(s, Box(1.4, 1.3, 0.3, 0.3), "A", fill="accent", name="probe.n.n0.change.A", theme=theme())
    with_prs(p, fn)


def p26_vpc_cross(p, w):
    """A flow crossing the VPC border with no edge pin and no label naming its path."""
    from deckkit.canvas import Box

    def fn(prs):
        s = _arch_slide(prs, flows=0)
        _frame(s, Box(4.4, 1.3, 4.6, 4.0), "aws-vpc", name="vpc")
        _text(s, Box(4.5, 1.33, 2.0, 0.18), "VPC · probe", "vpc.label")
        _arrow(s, (2.9 + 0.42, 1.81), (4.9, 1.81), "flow.in")
    with_prs(p, fn)


# ------------------------------------------------------------------ (u) collisions, (c) crossing labels, words, marks

def p26_label_touch(p, w):
    """Two flow labels knocked out on top of each other."""
    from deckkit.canvas import Box

    def fn(prs):
        s = _arch_slide(prs, flows=2)
        _text(s, Box(1.45, 2.18, 0.7, 0.16), "raw rows", "flow.a.label", fill="paper", pt=8.0)
        _text(s, Box(1.55, 2.22, 0.7, 0.16), "new rows", "flow.b.label", fill="paper", pt=8.0)
    with_prs(p, fn)


def p26_crossing_bare(p, w):
    """A deployment slide whose flows cross a boundary with no label."""
    from deckkit.canvas import Box

    def fn(prs):
        s = _arch_slide(prs, variant="arch-deploy-aws", flows=0)
        _frame(s, Box(2.2, 1.2, 3.2, 1.6), "aws-region", dash="sysDash", name="region")
        _text(s, Box(2.3, 1.23, 2.0, 0.18), "Region · probe", "region.label")
        for k in range(4):
            a = (0.9 + k * 2.0 + 0.42, 1.81)
            _arrow(s, a, (a[0] + 1.58, 1.81), "flow.%d" % k)
    with_prs(p, fn)


def p26_words_over(p, w):
    """A hub view (at most 150 words) carrying a 160-word block."""
    from deckkit.canvas import Box

    def fn(prs):
        s = _arch_slide(prs, variant="arch-hub", flows=0, keys=ARCH_KEYS[:10])
        _text(s, Box(0.6, 5.7, 12.0, 1.1), " ".join(["agents read cited claims"] * 40), "body")
    with_prs(p, fn)


def p26_marks_over(p, w):
    """A hub view (7 to 16 marks) carrying 18."""
    def fn(prs):
        s = _arch_slide(prs, variant="arch-hub", flows=0)
        for k in range(6):
            _mark(s, ARCH_KEYS[k], 0.9 + k * 2.0, 6.0, "x%d" % k, caption=False)
    with_prs(p, fn)


PLANTERS = [
    Planter("arch-double-head", "P26", "a connector headed at both ends that is no peering", p26_double_head,
            "headed at both ends"),
    Planter("arch-bare-peering", "P26", "a peering line with no label", p26_bare_peering, "peering without its label"),
    Planter("arch-deploy-steps", "P26", "nine numbered steps on a deployment slide", p26_deploy_steps,
            "numbered steps on a"),
    Planter("arch-deploy-kinds", "P26", "a deployment slide with one boundary kind", p26_deploy_kinds,
            "boundary kind"),
    Planter("arch-nesting", "P26", "five nested boundaries on an arch-* slide", p26_nesting, "nest 5 deep"),
    Planter("arch-no-key", "P26", "a dotted flow with no key sample on an arch-* slide", p26_no_key,
            "no key sample"),
    Planter("arch-tiers", "P26", "subnet tiers of two AZ columns at different heights", p26_tiers, "share one y"),
    Planter("arch-span-one-az", "P26", "a span band inside one AZ column", p26_span_one_az, "span band crosses"),
    Planter("arch-pin-flow", "P26", "a flow landing on a corner pin", p26_pin_flow, "pin carries a flow"),
    Planter("arch-change-once", "P26", "a change letter on one diagram only", p26_change_once,
            "marks one diagram only"),
    Planter("arch-vpc-cross", "P26", "a flow crossing the VPC border with no pin or label", p26_vpc_cross,
            "crosses the VPC border"),
    Planter("arch-label-touch", "P26", "two flow labels knocked out on top of each other", p26_label_touch,
            "touches label"),
    Planter("arch-crossing-bare", "P26", "boundary-crossing flows with no label on a deployment slide",
            p26_crossing_bare, "boundary-crossing"),
    Planter("arch-words-over", "P26", "a hub view over its word band", p26_words_over, "words on a"),
    Planter("arch-marks-over", "P26", "a hub view over its mark band", p26_marks_over, "at most 16"),
]


def main() -> int:
    """Run these planters alone: build the golden, plant each, run P26, check its finding."""
    import shutil
    import tempfile
    import run_all
    from _shared import FAIL, Ctx, run_gate
    import p26_architecture as g
    ok, out = run_all.build_golden()
    if not ok:
        print(out)
        return 1
    bad = 0
    for pl in PLANTERS:
        tmp = Path(tempfile.mkdtemp(prefix="neg-arch-"))
        dst = tmp / run_all.GOLDEN.name
        shutil.copy2(run_all.GOLDEN, dst)
        for sc in run_all.sidecars(run_all.GOLDEN):
            shutil.copy2(sc, tmp / sc.name)
        try:
            pl.fn(dst, tmp)
            c = Ctx(dst)
            code, found = run_gate(g, str(dst), c)
            c.close()
            hit = [f for f in found if f.level == FAIL and pl.expect.lower() in (f.where + " " + f.msg).lower()]
            res = "ok" if code == 1 and hit else "MISSED"
            why = hit[0].msg if hit else "; ".join(f.msg for f in found if f.level == FAIL)[:200]
        except Exception as e:  # noqa: BLE001
            res, why = "PLANT ERROR", "%s: %s" % (type(e).__name__, e)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        bad += res != "ok"
        print("%-20s %-11s %s" % (pl.name, res, why[:110]))
    print("%d planters, %d did not behave" % (len(PLANTERS), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
