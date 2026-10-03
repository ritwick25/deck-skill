"""Rules the builder and the gates share: one predicate per rule, so a shape the kit refuses to draw and a
shape a gate fails on a read deck are judged by the same code.

is_accent_strip: the left/top accent-bar tell (CLAUDE.md section 4, the left-accent rule).
  geometry  at most BAR_THIN (0.10in x k) thick, longer than BAR_LONG (0.18in x k) and more than BAR_RATIO (2x)
            its thickness. k is the canvas scale against WIDE (1.0 wide, 0.75 compact), as every gate tolerance is.
  paint     two modes of the one predicate, chosen with by=:
            by="role"    (the builder) the paint is a theme role. A strip may be drawn only in a STRIP_ROLES role
                         (hairline, hairline-soft, rule-strong, ink-muted); every other role (navy, the inks, paper,
                         card, accent and its tints, the series) is a bar, whatever its chroma on this theme.
            by="colour"  (the gates, which read hexes, on any deck) the paint is a resolved hex. A strip is a bar
                         only when it is at least BAR_MIN_PT (1.5pt, 0.0208in) thick: a thinner strip is a divider.
                         Grey is HLS saturation under GREY_SAT (0.15) or the hex of a STRIP_ROLES role in the theme
                         (is_grey). A kit deck is held to the stricter role rule when it is built.
  name      not state.*: a coloured edge that encodes a state that can change is the one legitimate bar.

line_refusal: what a drawn line may carry. A line in a STRIP_ROLES role (or, by colour, a neutral grey) is free.
  Any other line is a connector: it carries an arrowhead and is at most CONNECTOR_MAX_PT (1.5pt) heavy. An
  undirected line in any other role is an edge strip and is refused whatever its name; only state.* is exempt.

contrast_min: the WCAG 2.x text minimum for a run, 4.5:1, or 3.0:1 for large text (14pt bold and larger, or
  18pt and larger).
"""
from __future__ import annotations

import colorsys

from .read.colour import is_neutral

BAR_THIN = 0.10             # a strip at most this thick (x k) ...
BAR_LONG = 0.18             # ... longer than this (x k) ...
BAR_RATIO = 2.0             # ... and more than this many times its thickness is a bar
EPS = 1e-6                  # EMU rounding: 0.10in written and read back is 0.1 exactly, give it a hair
STRIP_ROLES = ("hairline", "hairline-soft", "rule-strong", "ink-muted")
NEUTRAL_ROLES = STRIP_ROLES  # the rule roles whose hex a gate reads as neutral (by="colour")
STATE_PREFIX = "state."
CONNECTOR_MAX_PT = 1.5
HEADED = ("end", "start", "both")
BY = ("role", "colour")
BAR_MIN_PT = 1.5            # by colour: a strip thinner than this is a divider, never a bar
GREY_SAT = 0.15             # by colour: HLS saturation under this is grey
PT_IN = 1.0 / 72.0

TEXT_MIN = 4.5
LARGE_TEXT_MIN = 3.0
LARGE_PT = 18.0
LARGE_BOLD_PT = 14.0


def _hex(h) -> str:
    return str(h or "").lstrip("#").upper()


def _by(by: str) -> str:
    if by not in BY:
        raise ValueError("by must be one of %s, not %r" % (" / ".join(BY), by))
    return by


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


def is_strip_role(role) -> bool:
    """The builder's test: a role a strip or an undirected line may be drawn in (None draws nothing)."""
    return role is None or role in STRIP_ROLES


def hls_saturation(colour_hex) -> float:
    """The HLS saturation of a hex colour (0 for a grey, white or black)."""
    h = _hex(colour_hex)
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)[2]


def is_grey(colour_hex, theme=None) -> bool:
    """The bar test's grey (by='colour'): HLS saturation under GREY_SAT, or exactly the hex of a rule role in the
    theme. No colour draws nothing and reads as grey."""
    h = _hex(colour_hex)
    if not h:
        return True
    if len(h) != 6:
        return False
    return hls_saturation(h) < GREY_SAT or h in neutral_hexes(theme)


def neutral_paint(paint, theme=None, *, by: str) -> bool:
    """by='role': paint is a role and must be a STRIP_ROLES role. by='colour': paint is a hex and must be a grey
    (chroma under 0.10, or a rule role's hex; line_refusal's test)."""
    if _by(by) == "role":
        return is_strip_role(paint)
    return is_neutral_colour(paint, theme)


def is_strip(width_in: float, height_in: float, *, k: float = 1.0) -> bool:
    """The geometry alone: thin, long, and more than twice as long as it is thick."""
    thin, long_ = min(width_in, height_in), max(width_in, height_in)
    return thin <= BAR_THIN * k + EPS and long_ > BAR_LONG * k and long_ > BAR_RATIO * thin


def is_accent_strip(width_in: float, height_in: float, paint, name, theme, *, k: float = 1.0,
                    by: str = "colour") -> bool:
    """True when a shape of this size, in this paint, under this name, is the left/top accent bar.

    by='colour' (the gates, any deck): paint is a hex; the strip must be at least BAR_MIN_PT thick (thinner is a
    divider) and not grey by HLS saturation (is_grey). by='role' (the builder): paint is a role, judged by name
    against STRIP_ROLES, so navy or an ink that happens to be grey on one theme is still refused, at any thickness."""
    _by(by)
    if (name or "").startswith(STATE_PREFIX):
        return False
    if not is_strip(width_in, height_in, k=k):
        return False
    if by == "role":
        return not is_strip_role(paint)
    if min(width_in, height_in) < BAR_MIN_PT * PT_IN - EPS:
        return False
    return not is_grey(paint, theme)


def line_refusal(paint, head, weight_pt, name, theme, *, by: str = "role") -> str | None:
    """Why a line in this paint (a role by='role', a hex by='colour') with this head and weight may not be drawn,
    or None when it may. Only state.* is exempt by name."""
    if paint is None or neutral_paint(paint, theme, by=by):
        return None
    if (name or "").startswith(STATE_PREFIX):
        return None
    if head not in HEADED:
        return ("an undirected line in %s is an edge strip whatever its name; give it an arrowhead, draw it in a "
                "rule role (%s), or name it state.* when it encodes a state" % (paint, " / ".join(STRIP_ROLES)))
    if weight_pt is not None and weight_pt > CONNECTOR_MAX_PT + 1e-9:
        return ("a headed line in %s is %.2fpt; a connector outside the rule roles is at most %.1fpt"
                % (paint, weight_pt, CONNECTOR_MAX_PT))
    return None


def is_large_text(pt: float, bold: bool) -> bool:
    return pt >= LARGE_PT - 1e-9 or (bool(bold) and pt >= LARGE_BOLD_PT - 1e-9)


def contrast_min(pt: float, bold: bool) -> float:
    return LARGE_TEXT_MIN if is_large_text(pt, bold) else TEXT_MIN


__all__ = ["is_accent_strip", "is_strip", "is_strip_role", "neutral_paint", "is_neutral_colour", "neutral_hexes",
           "is_grey", "hls_saturation", "BAR_MIN_PT", "GREY_SAT",
           "line_refusal", "contrast_min", "is_large_text", "BAR_THIN", "BAR_LONG", "BAR_RATIO", "STRIP_ROLES",
           "NEUTRAL_ROLES", "CONNECTOR_MAX_PT", "HEADED", "STATE_PREFIX", "BY", "TEXT_MIN", "LARGE_TEXT_MIN"]
