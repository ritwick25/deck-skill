"""Canvas profiles and the Box arithmetic every composer lays out with.

Two canvases (engineering.md (c), "Canvas profiles"):

    WIDE  13.333 x 7.5 in, the default
    STD   10 x 5.625 in, only when extending an existing 10-inch deck

All lengths are inches. Devices move between canvases only by uniform scale k (4/3 or 3/4), and the
8pt floor then decides whether the move is allowed. Tolerances in the gates are multiplied by k.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .errors import BelowFloor, GeometryError

FLOOR = 8.0            # pt, never below, on the effective size
EMU_PER_IN = 914400


@dataclass(frozen=True)
class Box:
    """An axis-aligned box in inches: left x, top y, width w, height h."""
    x: float
    y: float
    w: float
    h: float

    def __post_init__(self):
        if not (self.w > 0 and self.h > 0):
            raise GeometryError("box", need="w > 0 and h > 0", have="w=%.4f h=%.4f" % (self.w, self.h),
                                hint="a split or inset left no area; use fewer columns or a smaller gutter")

    # edges and centre
    @property
    def r(self) -> float:
        return self.x + self.w

    @property
    def b(self) -> float:
        return self.y + self.h

    @property
    def cx(self) -> float:
        return self.x + self.w / 2.0

    @property
    def cy(self) -> float:
        return self.y + self.h / 2.0

    @property
    def emu(self) -> tuple[int, int, int, int]:
        """(x, y, w, h) in EMU, rounded once here so every creator rounds the same way."""
        return tuple(int(round(v * EMU_PER_IN)) for v in (self.x, self.y, self.w, self.h))

    def inset(self, dx: float, dy: float | None = None) -> "Box":
        dy = dx if dy is None else dy
        return Box(self.x + dx, self.y + dy, self.w - 2 * dx, self.h - 2 * dy)

    def contains(self, other: "Box", tol: float = 0.0) -> bool:
        return (other.x >= self.x - tol and other.y >= self.y - tol and other.r <= self.r + tol
                and other.b <= self.b + tol)

    @staticmethod
    def _shares(n: int, weights, what: str) -> list[float]:
        if n < 1:
            raise GeometryError(what, need="n >= 1", have=n)
        if weights is None:
            return [1.0 / n] * n
        if len(weights) != n or any(w <= 0 for w in weights):
            raise GeometryError(what, need="%d positive weights" % n, have=list(weights))
        t = float(sum(weights))
        return [w / t for w in weights]

    def split_cols(self, n: int, gutter: float, weights=None) -> list["Box"]:
        """n columns across the box, gutter between them (none at the outer edges)."""
        free = self.w - gutter * (n - 1)
        if free <= 0:
            raise GeometryError("split_cols(%d)" % n, need=gutter * (n - 1), have=self.w,
                                hint="the gutters alone are wider than the box")
        out, x = [], self.x
        for s in self._shares(n, weights, "split_cols(%d)" % n):
            w = free * s
            out.append(Box(x, self.y, w, self.h))
            x += w + gutter
        return out

    def split_rows(self, n: int, gutter: float, weights=None) -> list["Box"]:
        """n rows down the box, gutter between them."""
        free = self.h - gutter * (n - 1)
        if free <= 0:
            raise GeometryError("split_rows(%d)" % n, need=gutter * (n - 1), have=self.h,
                                hint="the gutters alone are taller than the box")
        out, y = [], self.y
        for s in self._shares(n, weights, "split_rows(%d)" % n):
            h = free * s
            out.append(Box(self.x, y, self.w, h))
            y += h + gutter
        return out


@dataclass(frozen=True)
class Canvas:
    name: str
    w: float
    h: float
    margin_l: float
    margin_r: float
    title_box: Box
    title_pt: float
    title_max_lines: int
    content: Box
    gutter: float
    radius_in: float
    hairline_pt: float
    ramp: dict = field(hash=False)   # head, body, label, small, numeral_min, numeral, divider (pt)
    k: float = 1.0                    # inch-tolerance scale against WIDE

    def __post_init__(self):
        low = {k: v for k, v in self.ramp.items() if v < FLOOR}
        if self.title_pt < FLOOR:
            low["title"] = self.title_pt
        if low:
            raise BelowFloor("canvas %s type ramp" % self.name, need=FLOOR, have=low,
                             hint="every ramp entry must be at least %.1fpt" % FLOOR)
        page = Box(0, 0, self.w, self.h)
        for nm, bx in (("title_box", self.title_box), ("content", self.content)):
            if not page.contains(bx, tol=1e-6):
                raise GeometryError("canvas %s %s" % (self.name, nm), need="inside the page", have=bx)

    @property
    def page(self) -> Box:
        return Box(0.0, 0.0, self.w, self.h)

    @property
    def emu(self) -> tuple[int, int]:
        return int(round(self.w * EMU_PER_IN)), int(round(self.h * EMU_PER_IN))


# 13.333 in is 12192000 EMU exactly (the 16:9 PowerPoint default); 7.5 in is 6858000.
WIDE = Canvas(
    name="wide", w=12192000 / EMU_PER_IN, h=7.5, margin_l=0.50, margin_r=0.43,
    title_box=Box(0.50, 0.13, 12.40, 0.35), title_pt=21.0, title_max_lines=1,
    content=Box(0.50, 0.85, 12192000 / EMU_PER_IN - 0.50 - 0.43, 6.84 - 0.85),
    gutter=0.20, radius_in=0.05, hairline_pt=0.75,
    ramp={"head": 13.0, "body": 11.0, "label": 10.0, "small": 9.0, "numeral_min": 16.0, "numeral": 28.0,
          "divider": 66.0},
    k=1.0,
)

# The divider numeral on STD is not in the measured table; it is WIDE's 66pt times k (49.5pt).
STD = Canvas(
    name="std", w=10.0, h=5.625, margin_l=0.28, margin_r=0.28,
    title_box=Box(0.28, 0.08, 9.44, 0.75), title_pt=19.0, title_max_lines=2,
    content=Box(0.28, 0.99, 10.0 - 0.28 - 0.28, 5.25 - 0.99),
    gutter=0.15, radius_in=0.04, hairline_pt=0.75,
    ramp={"head": 10.0, "body": 9.0, "label": 8.5, "small": 8.0, "numeral_min": 14.0, "numeral": 22.0,
          "divider": 49.5},
    k=0.75,
)

PROFILES = {"wide": WIDE, "std": STD}


def canvas_of(prs) -> Canvas:
    """The profile matching a Presentation's slide size (or a (cx, cy) EMU tuple). Unknown sizes raise."""
    if isinstance(prs, tuple):
        cx, cy = prs
    else:
        cx, cy = int(prs.slide_width), int(prs.slide_height)
    for c in PROFILES.values():
        ex, ey = c.emu
        if abs(cx - ex) <= 1270 and abs(cy - ey) <= 1270:      # 0.1pt of slack for rounded saves
            return c
    raise GeometryError("slide size", need="WIDE 13.333x7.5 or STD 10x5.625 in",
                        have="%.3fx%.3f in" % (cx / EMU_PER_IN, cy / EMU_PER_IN),
                        hint="start from kit/assets/base-wide.pptx or base-std.pptx")


__all__ = ["Box", "Canvas", "WIDE", "STD", "PROFILES", "FLOOR", "EMU_PER_IN", "canvas_of"]
