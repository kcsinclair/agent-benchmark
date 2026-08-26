"""Parse human-readable duration strings into seconds.

The module provides a single function ``parse_duration`` that accepts a
duration string and returns the total number of seconds as a ``float``.

The implementation follows the rules described in the problem statement
and raises ``ValueError`` for any malformed input. ``TypeError`` is raised
if the argument is not a string.
"""

from __future__ import annotations

import re

# Regular expression for a non‑negative decimal number with an optional
# fractional part.  It matches at least one digit before an optional
# decimal point and at least one digit after the point.
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")

# Mapping of unit to its order (lower value = larger unit) and its
# multiplier to convert to seconds.
_UNIT_ORDER = {
    "h": 0,
    "m": 1,
    "s": 2,
    "ms": 3,
}
_UNIT_MULTIPLIER = {
    "h": 3600.0,
    "m": 60.0,
    "s": 1.0,
    "ms": 0.001,
}


def parse_duration(text: str) -> float:
    """Parse a duration string and return the total number of seconds.

    Parameters
    ----------
    text:
        The duration string to parse.

    Returns
    -------
    float
        The total duration in seconds.

    Raises
    ------
    TypeError
        If *text* is not a string.
    ValueError
        If the string does not conform to the specification.
    """
    if not isinstance(text, str):
        raise TypeError("parse_duration expects a string input")

    # Strip leading/trailing whitespace; any whitespace inside the string
    # will cause a parsing error later.
    s = text.strip()
    if not s:
        raise ValueError("empty duration string")

    # Handle optional leading minus sign.
    sign = 1
    if s[0] == "-":
        sign = -1
        s = s[1:]
        if not s:
            raise ValueError("duration string contains only a minus sign")

    total_seconds = 0.0
    last_order = -1  # No unit seen yet.
    i = 0
    length = len(s)

    while i < length:
        # Parse the numeric part.
        num_match = _NUMBER_RE.match(s, i)
        if not num_match:
            raise ValueError(f"invalid number at position {i} in '{s}'")
        num_str = num_match.group()
        try:
            value = float(num_str)
        except ValueError:
            # Should not happen because regex guarantees a valid float.
            raise ValueError(f"invalid numeric value '{num_str}'")
        i = num_match.end()

        # Parse the unit.
        if s.startswith("ms", i):
            unit = "ms"
            i += 2
        elif i < length and s[i] in "hms":
            unit = s[i]
            i += 1
        else:
            raise ValueError(f"missing or unknown unit at position {i} in '{s}'")

        # Enforce descending order and uniqueness.
        order = _UNIT_ORDER[unit]
        if order <= last_order:
            raise ValueError(
                f"unit '{unit}' out of order or repeated (previous unit order {last_order})"
            )
        last_order = order

        # Accumulate seconds.
        total_seconds += value * _UNIT_MULTIPLIER[unit]

    if last_order == -1:
        # No components were parsed.
        raise ValueError("no duration components found")

    return sign * total_seconds

# End of module
