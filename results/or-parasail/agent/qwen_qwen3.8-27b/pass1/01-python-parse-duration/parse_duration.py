"""Parse human-readable duration strings into total seconds."""

import re

# A single component: a non-negative decimal number followed by a unit.
# Number: digits with optional fractional part (no bare dot, no trailing dot).
_COMPONENT_RE = re.compile(r'(\d+(?:\.\d+)?)(h|ms|m|s)')

# Multipliers in seconds.
_UNIT_SECONDS = {
    'h': 3600.0,
    'm': 60.0,
    's': 1.0,
    'ms': 0.001,
}

# Strictly descending order of unit size.
_UNIT_ORDER = {'h': 0, 'm': 1, 's': 2, 'ms': 3}


def parse_duration(text: str) -> float:
    """Parse a duration string and return the total number of seconds.

    >>> parse_duration("90s")
    90.0
    >>> parse_duration("1h30m")
    5400.0
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    stripped = text.strip()
    if not stripped:
        raise ValueError("empty duration string")

    negative = False
    if stripped.startswith('-'):
        negative = True
        stripped = stripped[1:]
        if not stripped:
            raise ValueError("missing components after sign")

    # Find all components and verify they cover the entire string.
    matches = list(_COMPONENT_RE.finditer(stripped))
    if not matches:
        raise ValueError("no valid components found")

    # Ensure the components are contiguous and cover the whole string.
    pos = 0
    for match in matches:
        if match.start() != pos:
            raise ValueError("invalid characters in duration string")
        pos = match.end()
    if pos != len(stripped):
        raise ValueError("invalid characters in duration string")

    total = 0.0
    last_order = -1
    for match in matches:
        number_str, unit = match.group(1), match.group(2)
        order = _UNIT_ORDER[unit]
        if order <= last_order:
            raise ValueError("units must appear in strictly descending order")
        last_order = order
        total += float(number_str) * _UNIT_SECONDS[unit]

    if negative:
        total = -total
    return total
