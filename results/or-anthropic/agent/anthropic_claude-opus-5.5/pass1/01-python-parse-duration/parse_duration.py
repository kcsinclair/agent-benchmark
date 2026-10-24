"""Parse human-readable duration strings into seconds."""

import re

__all__ = ["parse_duration"]

_COMPONENT = re.compile(r"([0-9]+(?:\.[0-9]+)?)(ms|h|m|s)")

_UNITS = {
    "h": (0, 3600.0),
    "m": (1, 60.0),
    "s": (2, 1.0),
    "ms": (3, 0.001),
}


def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError("parse_duration() argument must be a str, not %s"
                        % type(text).__name__)

    s = text.strip()
    if not s:
        raise ValueError("empty duration string")

    negative = False
    pos = 0
    if s[0] == "-":
        negative = True
        pos = 1

    if pos >= len(s):
        raise ValueError("invalid duration: %r" % text)

    total = 0.0
    last_rank = -1
    count = 0
    n = len(s)
    while pos < n:
        m = _COMPONENT.match(s, pos)
        if m is None:
            raise ValueError("invalid duration: %r" % text)
        number, unit = m.group(1), m.group(2)
        rank, factor = _UNITS[unit]
        if rank <= last_rank:
            raise ValueError("units out of order or repeated in %r" % text)
        last_rank = rank
        total += float(number) * factor
        count += 1
        pos = m.end()

    if count == 0:
        raise ValueError("invalid duration: %r" % text)

    return -total if negative else total
