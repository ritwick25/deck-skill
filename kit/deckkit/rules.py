"""Rules the builder and the gates share: one predicate per rule, so a shape the kit refuses to draw and a
shape a gate fails on a read deck are judged by the same code.

is_accent_strip: the left/top accent-bar tell (CLAUDE.md section 4, the left-accent rule).
  geometry  at most BAR_THIN (0.10in x k) thick, longer than BAR_LONG (0.18in x k) and more than BAR_RATIO (2x)
            its thickness. k is the canvas scale against WIDE (1.0 wide, 0.75 compact), as every gate tolerance is.
  colour    not a neutral grey. Neutral is chroma under 0.10 (deckkit.read.colour.is_neutral, the channel spread)
            or the resolved hex of a rule role (hairline, hairline-soft, rule-strong, ink-muted) in the theme.
  name      not state.*: a coloured edge that encodes a state that can change is the one legitimate bar.

line_refusal: what a drawn line may carry. A line in a non-neutral role is a connector (it carries an arrowhead)
  or a shape named state.* or link.*; an undirected coloured line is an edge strip. A non-neutral connector or
  link line is at most CONNECTOR_MAX_PT (1.5pt) heavy. Neutral lines (the rules, the inks, the greys) are free.

contrast_min: the WCAG 2.x text minimum for a run, 4.5:1, or 3.0:1 for large text (14pt bold and larger, or
  18pt and larger).
"""
from __future__ import annotations

from .read.colour import is_neutral

BAR_THIN = 0.10             # a strip at most this thick (x k) ...
BAR_LONG = 0.18             # ... longer than this (x k) ...
BAR_RATIO = 2.0             # ... and more than this many times its thickness is a bar
EPS = 1e-6                  # EMU rounding: 0.10in written and read back is 0.1 exactly, give it a hair
NEUTRAL_ROLES = ("hairline", "hairline-soft", "rule-strong", "ink-muted")
STATE_PREFIX = "state."
LINK_PREFIX = "link."
CONNECTOR_MAX_PT = 1.5
HEADED = ("end", "start", "both")

TEXT_MIN = 4.5
LARGE_TEXT_MIN = 3.0
LARGE_PT = 18.0
LARGE_BOLD_PT = 14.0


def _hex(h) -> str:
    return str(h or "").lstrip("#").upper()


def neutral_hexes(theme) -> set:
    """The resolved hex of every rule role in the theme (empty without a theme)."""
    if theme is None:
        return set()
    out = set()
    for r in NEUTRAL_ROLES:
        try:
            out.add(_hex(theme.hex(r)))
        except Exception:                     # a theme without the role: the chroma test still holds
            continue
    return out


def is_neutral_colour(colour_hex, theme=None) -> bool:
    """A grey: chroma under 0.10, or exactly the hex of a rule role (hairline, hairline-soft, rule-strong,
    ink-muted) in the theme."""
    h = _hex(colour_hex)
    if not h:
        return True                           # no colour, nothing drawn
    return is_neutral(h) or h in neutral_hexes(theme)


def is_neutral_role(role, theme) -> bool:
    """A role whose colour is a grey: one of the rule roles, or a role that resolves to a neutral hex."""
    if role is None:
        return True
    if role in NEUTRAL_ROLES:
        return True
    return is_neutral_colour(theme.hex(role), theme)


def is_strip(width_in: float, height_in: float, *, k: float = 1.0) -> bool:
    """The geometry alone: thin, long, and more than twice as long as it is thick."""
    thin, long_ = min(width_in, height_in), max(width_in, height_in)
    return thin <= BAR_THIN * k + EPS and long_ > BAR_LONG * k and long_ > BAR_RATIO * thin


def is_accent_strip(width_in: float, height_in: float, colour_hex, name, theme, *, k: float = 1.0) -> bool:
    """True when a shape of this size, in this colour, under this name, is the left/top accent bar."""
    if (name or "").startswith(STATE_PREFIX):
        return False
    if not is_strip(width_in, height_in, k=k):
        return False
    return not is_neutral_colour(colour_hex, theme)


def line_refusal(role, head, weight_pt, name, theme) -> str | None:
    """Why a line in `role` with this head and weight may not be drawn, or None when it may."""
    if role is None or is_neutral_role(role, theme):
        return None
    nm = name or ""
    if nm.startswith(STATE_PREFIX):
        return None
    headed = head in HEADED
    if not headed and not nm.startswith(LINK_PREFIX):
        return ("an undirected line in %s (a non-neutral role) is an edge strip; give it an arrowhead, draw it in "
                "a rule role, or name it state.* or link.*" % role)
    if weight_pt is not None and weight_pt > CONNECTOR_MAX_PT + 1e-9:
        return ("a %s line in %s is %.2fpt; a non-neutral connector is at most %.1fpt"
                % ("headed" if headed else "link", role, weight_pt, CONNECTOR_MAX_PT))
    return None


def is_large_text(pt: float, bold: bool) -> bool:
    return pt >= LARGE_PT - 1e-9 or (bool(bold) and pt >= LARGE_BOLD_PT - 1e-9)


def contrast_min(pt: float, bold: bool) -> float:
    return LARGE_TEXT_MIN if is_large_text(pt, bold) else TEXT_MIN


__all__ = ["is_accent_strip", "is_strip", "is_neutral_colour", "is_neutral_role", "neutral_hexes", "line_refusal",
           "contrast_min", "is_large_text", "BAR_THIN", "BAR_LONG", "BAR_RATIO", "NEUTRAL_ROLES", "CONNECTOR_MAX_PT",
           "TEXT_MIN", "LARGE_TEXT_MIN"]
