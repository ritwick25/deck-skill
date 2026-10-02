"""Typed refusals. The kit never clamps and never truncates: it raises one of these instead.

Every refusal carries four fields so the fix is a decision rather than a search:
  what  the slot, shape or part that refused (a shape name, "title", "card 3 body")
  need  what the content asked for (inches, points, words, a count)
  have  what the slot actually offers, in the same unit
  hint  the smallest change that would make it pass ("cut about 12 words")
"""
from __future__ import annotations


class DeckkitError(Exception):
    """Base refusal. str() reads as one line: what, need against have, then the hint."""

    unit = ""

    def __init__(self, what: str, need=None, have=None, hint: str = "", *, unit: str | None = None):
        self.what = what
        self.need = need
        self.have = have
        self.hint = hint
        if unit is not None:
            self.unit = unit
        super().__init__(self._message())

    @staticmethod
    def _fmt(v) -> str:
        if isinstance(v, float):
            return f"{v:.3f}"
        return str(v)

    def _message(self) -> str:
        msg = f"{self.what}"
        if self.need is not None or self.have is not None:
            u = f" {self.unit}" if self.unit else ""
            msg += f": needs {self._fmt(self.need)}{u}, has {self._fmt(self.have)}{u}"
        if self.hint:
            msg += f". {self.hint}"
        return msg


class Overflows(DeckkitError):
    """Content needs more room than its box offers (height, width, or one unbreakable word)."""
    unit = "in"


class BelowFloor(DeckkitError):
    """A run was asked for below the 8.0pt floor. Raised, never grown to the floor."""
    unit = "pt"


class OverBudget(DeckkitError):
    """Words on glass exceed the archetype's budget."""
    unit = "words"


class Capacity(DeckkitError):
    """More items than a composer or device variant can place (nine pillars on a five-pillar slide)."""
    unit = "items"


class UnknownFace(DeckkitError, LookupError):
    """A font family, weight or style the measurer has no metrics for. Never guessed."""


class UnsupportedPart(DeckkitError):
    """A clone met a part the kit does not carry across packages (chart, OLE, media)."""


class LeakRefused(DeckkitError):
    """A clone or placement carried a hashed reference string, image or vector signature."""


class HandEditDrift(DeckkitError):
    """The pptx on disk differs from its manifest sha: somebody edited it by hand since the build."""


class GeometryError(DeckkitError):
    """A geometry request the kit refuses (radius on a non-rounded preset, shear under rotation)."""


class ThemeInvariant(DeckkitError):
    """A theme touched a fixed slot (dk1, lt1), named an unknown slot or role, or drifted from its record."""


class ValidatorMissing(DeckkitError):
    """The referenced XSD validator could not be found or could not run. Validation fails, never passes."""


__all__ = ["DeckkitError", "Overflows", "BelowFloor", "OverBudget", "Capacity", "UnknownFace",
           "UnsupportedPart", "LeakRefused", "HandEditDrift", "GeometryError", "ThemeInvariant",
           "ValidatorMissing"]
