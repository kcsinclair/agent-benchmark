# parse_duration.py
"""Utility to parse human‑readable duration strings.

The module provides a single public function ``parse_duration`` which accepts a
string such as ``"1h30m"`` and returns the total number of seconds as a ``float``.
It follows the specification given in the problem statement and raises
``ValueError`` for malformed inputs and ``TypeError`` when the argument is not a
string.
"""

from __future__ import annotations
import re

# Mapping of unit to its position in the allowed descending order and to the
# conversion factor to seconds.
_UNIT_ORDER = {"h": 0, "m": 1, "s": 2, "ms": 3}
_UNIT_TO_SECONDS = {
    "h": 3600.0,
    "m": 60.0,
    "s": 1.0,
    "ms": 0.001,
}

# Regular expression that matches a single component: a non‑negative decimal
# number (no leading sign, no exponent) followed by a valid unit.  ``ms`` must be
# matched before the single‑letter units to avoid consuming only the ``m``.
_COMPONENT_RE = re.compile(r"\d+(?:\.\d+)?(?:ms|[hms])")


def parse_duration(text: str) -> float:
    """Parse *text* and return the total duration in seconds.

    Parameters
    ----------
    text: str
        Human‑readable duration string.

    Returns
    -------
    float
        Total number of seconds represented by *text*.

    Raises
    ------
    TypeError
        If *text* is not a string.
    ValueError
        If *text* does not conform to the required format.
    """
    if not isinstance(text, str):
        raise TypeError("parse_duration expects a string argument")

    # Strip surrounding whitespace – internal whitespace is forbidden.
    s = text.strip()
    if not s:
        raise ValueError("empty duration string")
    if any(ch.isspace() for ch in s):
        raise ValueError("whitespace inside duration string is not allowed")

    # Detect a leading minus sign that negates the whole duration.
    negative = False
    if s[0] == "-":
        negative = True
        s = s[1:]
        if not s:
            raise ValueError("minus sign must be followed by a duration component")

    pos = 0
    total_seconds = 0.0
    seen_units = set()
    last_order = -1  # ensures the first unit can be any of the allowed ones.

    while pos < len(s):
        match = _COMPONENT_RE.match(s, pos)
        if not match:
            raise ValueError(f"invalid component starting at position {pos}: '{s[pos:]}'")
        token = match.group()

        # Separate the numeric part from the unit.
        if token.endswith("ms"):
            unit = "ms"
            number_str = token[:-2]
        else:
            unit = token[-1]
            number_str = token[:-1]

        # Enforce ordering and uniqueness of units.
        order = _UNIT_ORDER[unit]
        if order <= last_order:
            raise ValueError("units must appear in descending order without repetition")
        if unit in seen_units:
            raise ValueError("unit appears more than once")
        seen_units.add(unit)
        last_order = order

        # Convert the numeric part to float – the regex guarantees a valid format.
        try:
            value = float(number_str)
        except ValueError as exc:  # pragma: no cover – defensive.
            raise ValueError("invalid numeric value") from exc

        total_seconds += value * _UNIT_TO_SECONDS[unit]
        pos = match.end()

    # ``pos`` should now be at the end of the string; otherwise there is stray data.
    if pos != len(s):
        raise ValueError("trailing characters after last component")

    if negative:
        total_seconds = -total_seconds
    return total_seconds

# The module does not execute any code on import; the function can be imported as:
#   from parse_duration import parse_duration
