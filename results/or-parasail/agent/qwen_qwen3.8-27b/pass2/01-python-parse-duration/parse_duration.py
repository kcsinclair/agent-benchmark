"""Parse human-readable duration strings into total seconds."""

import re

# A single component: a non-negative decimal number followed by a unit.
# Number: digits with optional fractional part (no bare '.', no trailing dot).
_COMPONENT_RE = re.compile(r'(\d+(?:\.\d+)?)(h|ms|m|s)\Z')

# Unit sizes in seconds, and their required order.
_UNIT_SECONDS = {
    'h': 3600.0,
    'm': 60.0,
    's': 1.0,
    'ms': 0.001,
}
_UNIT_ORDER = {'h': 0, 'm': 1, 's': 2, 'ms': 3}


def parse_duration(text: str) -> float:
    """Parse a duration string and return the total number of seconds.

    >>> parse_duration("90s")
    90.0
    >>> parse_duration("1h30m")
    5400.0
    >>> parse_duration("2h15m30s500ms")
    8130.5
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    s = text.strip()
    if not s:
        raise ValueError("empty duration string")

    negative = False
    if s[0] == '-':
        negative = True
        s = s[1:]
        if not s:
            raise ValueError("missing components after sign")

    total = 0.0
    last_order = -1

    while s:
        m = _COMPONENT_RE.match(s)
        if not m:
            raise ValueError("invalid duration string: %r" % text)
        number_str, unit = m.group(1), m.group(2)
        s = s[m.end():]

        order = _UNIT_ORDER[unit]
        if order <= last_order:
            raise ValueError("units out of order or repeated: %r" % text)
        last_order = order

        total += float(number_str) * _UNIT_SECONDS[unit]

    return -total if negative else total
