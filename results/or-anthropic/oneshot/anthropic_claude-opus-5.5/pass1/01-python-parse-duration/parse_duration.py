"""Parse human-readable duration strings into seconds.

Example: parse_duration("1h30m") returns 5400.0
"""

import re

__all__ = ["parse_duration"]

# One component: a number followed by a unit.
# The number is ASCII digits with an optional fractional part.
# "ms" is listed before "m" so that "250ms" is read as milliseconds.
_COMPONENT_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)(ms|h|m|s)")

# Units in descending order of size, with their length in seconds.
_UNITS = {
    "h": (0, 3600.0),
    "m": (1, 60.0),
    "s": (2, 1.0),
    "ms": (3, 0.001),
}


def parse_duration(text: str) -> float:
    """Return the total number of seconds in a duration string.

    Raises TypeError if text is not a string.
    Raises ValueError if text is not a valid duration.
    """
    if not isinstance(text, str):
        raise TypeError(
            "parse_duration() argument must be str, not %s" % type(text).__name__
        )

    s = text.strip()
    if not s:
        raise ValueError("empty duration string")

    sign = 1.0
    pos = 0
    if s[0] == "-":
        sign = -1.0
        pos = 1

    n = len(s)
    if pos >= n:
        raise ValueError("invalid duration %r: no components" % text)

    total = 0.0
    last_rank = -1
    while pos < n:
        m = _COMPONENT_RE.match(s, pos)
        if m is None:
            raise ValueError(
                "invalid duration %r: unexpected input at position %d" % (text, pos)
            )
        number, unit = m.group(1), m.group(2)
        rank, factor = _UNITS[unit]
        if rank <= last_rank:
            raise ValueError(
                "invalid duration %r: unit %r is repeated or out of order"
                % (text, unit)
            )
        last_rank = rank
        total += float(number) * factor
        pos = m.end()

    return sign * total
