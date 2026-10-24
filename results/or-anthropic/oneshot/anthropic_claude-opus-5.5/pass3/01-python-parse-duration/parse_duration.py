"""Parse human-readable duration strings such as "1h30m" or "250ms" into seconds."""

import re
from fractions import Fraction

__all__ = ["parse_duration"]

# One component: a number (digits, with an optional fractional part) followed by a unit.
# "ms" is listed before "m" so that "5ms" is read as milliseconds.
# [0-9] is used instead of \d so that non-ASCII digits are rejected.
_COMPONENT_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)(ms|h|m|s)")

# Rank gives the required order (largest unit first).
# The value is the number of seconds in one unit.
_UNITS = {
    "h": (0, Fraction(3600)),
    "m": (1, Fraction(60)),
    "s": (2, Fraction(1)),
    "ms": (3, Fraction(1, 1000)),
}


def parse_duration(text: str) -> float:
    """Parse a duration string and return the total number of seconds as a float.

    Raises TypeError if ``text`` is not a string.
    Raises ValueError if the string is not a valid duration.
    """
    if not isinstance(text, str):
        raise TypeError(
            "parse_duration() argument must be str, not %s" % type(text).__name__
        )

    s = text.strip()
    if not s:
        raise ValueError("empty duration string")

    negative = False
    pos = 0
    if s[0] == "-":
        negative = True
        pos = 1

    if pos >= len(s):
        raise ValueError("invalid duration %r: no components" % text)

    total = Fraction(0)
    last_rank = -1
    while pos < len(s):
        m = _COMPONENT_RE.match(s, pos)
        if m is None:
            raise ValueError("invalid duration %r at position %d" % (text, pos))
        number, unit = m.group(1), m.group(2)
        rank, factor = _UNITS[unit]
        if rank <= last_rank:
            raise ValueError(
                "invalid duration %r: unit %r out of order or repeated" % (text, unit)
            )
        last_rank = rank
        total += Fraction(number) * factor
        pos = m.end()

    if negative:
        total = -total

    try:
        return float(total)
    except OverflowError:
        raise ValueError("duration %r is too large" % text) from None
