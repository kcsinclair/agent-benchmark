"""Duration string parser.

Public API:
    parse_duration(text: str) -> float
"""

from __future__ import annotations

import re

__all__ = ["parse_duration"]


# Units ordered from largest to smallest.  The integer index in this tuple
# must strictly decrease across consecutive components.
_UNITS = ("h", "m", "s", "ms")

# Map unit -> index in _UNITS (used for the ordering check).
_UNIT_RANK = {unit: i for i, unit in enumerate(_UNITS)}

# Multiplier from the unit to seconds.
_UNIT_SECONDS = {
    "h": 3600.0,
    "m": 60.0,
    "s": 1.0,
    "ms": 0.001,
}

# A "number followed by a unit" component.  The unit alternation is ordered
# so that "ms" is matched before "m" (regex alternation is left-biased).
# Numbers: digits, optional "." followed by digits.  No bare "." and no
# trailing "." allowed.
_COMPONENT_RE = re.compile(
    r"(?P<number>\d+(?:\.\d+)?)(?P<unit>ms|h|m|s)"
)


def parse_duration(text: str) -> float:
    """Parse a human-readable duration string into seconds.

    See the module docstring / problem statement for the accepted grammar.

    Raises
    ------
    TypeError
        If ``text`` is not a string.
    ValueError
        If ``text`` does not conform to the duration grammar.
    """
    if not isinstance(text, str):
        raise TypeError(
            f"parse_duration() expected str, got {type(text).__name__}"
        )

    # Rule 5: strip leading/trailing whitespace.  Any whitespace *inside*
    # the string will cause a match failure below.
    stripped = text.strip()

    if not stripped:
        # Rule 3: at least one component.
        raise ValueError("empty duration string")

    # Rule 4: optional leading minus sign.
    negative = False
    if stripped.startswith("-"):
        negative = True
        stripped = stripped[1:]
        if not stripped:
            raise ValueError("duration missing after '-' sign")

    # Parse the components greedily and ensure the entire string is consumed.
    pos = 0
    total = 0.0
    last_rank = len(_UNITS)  # larger than any real rank

    matches = list(_COMPONENT_RE.finditer(stripped))
    if not matches:
        raise ValueError(f"invalid duration string: {text!r}")

    for match in matches:
        if match.start() != pos:
            # Gap between components (stray character, whitespace, sign, ...).
            raise ValueError(f"invalid duration string: {text!r}")
        pos = match.end()

        rank = _UNIT_RANK[match.group("unit")]
        if rank >= last_rank:
            # Wrong order or repeated unit.
            raise ValueError(
                f"units out of order or repeated in {text!r}"
            )
        last_rank = rank

        number_str = match.group("number")
        # ``number_str`` is validated by the regex: it can't be ".", "5.",
        # ".5", or contain an exponent / sign.
        value = float(number_str)
        total += value * _UNIT_SECONDS[match.group("unit")]

    if pos != len(stripped):
        # Trailing garbage (e.g. "90sfoo" or trailing whitespace that slipped
        # past the strip only if it was internal, but be safe).
        raise ValueError(f"invalid duration string: {text!r}")

    return -total if negative else total
