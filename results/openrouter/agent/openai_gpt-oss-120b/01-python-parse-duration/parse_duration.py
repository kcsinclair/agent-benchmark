"""parse_duration.py

Provides a single function `parse_duration` that parses a human‑readable duration
string and returns the total number of seconds as a float.

The implementation follows the specification given in the problem statement.
"""

from __future__ import annotations

import re
from typing import Dict

__all__ = ["parse_duration"]

# Mapping of unit to its size in seconds and its order index (smaller index = larger unit)
_UNIT_INFO: Dict[str, tuple[float, int]] = {
    "h": (3600.0, 0),
    "m": (60.0, 1),
    "s": (1.0, 2),
    "ms": (0.001, 3),
}

# Regular expression for a non‑negative decimal number as described:
#   one or more digits, optional fractional part consisting of a dot followed by one or more digits.
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def parse_duration(text: str) -> float:
    """Parse a duration string and return the total number of seconds.

    Parameters
    ----------
    text: str
        The duration string to parse.

    Returns
    -------
    float
        Total duration expressed in seconds.

    Raises
    ------
    TypeError
        If *text* is not a string.
    ValueError
        If the string does not conform to the required format.
    """
    if not isinstance(text, str):
        raise TypeError("parse_duration expects a string")

    # Strip leading/trailing whitespace – internal whitespace is not allowed.
    s = text.strip()
    if not s:
        raise ValueError("empty duration string")

    # Detect optional leading minus sign.
    sign = 1
    if s[0] == "-":
        sign = -1
        s = s[1:]
        if not s:
            raise ValueError("duration string contains only a minus sign")

    total_seconds = 0.0
    last_order = -1  # ensures the first unit can be any of the allowed ones.
    used_units = set()
    i = 0
    length = len(s)

    while i < length:
        # Parse number.
        num_match = _NUMBER_RE.match(s, i)
        if not num_match:
            raise ValueError(f"expected number at position {i} in '{s}'")
        num_str = num_match.group(0)
        try:
            value = float(num_str)
        except ValueError as exc:  # Should not happen because regex guarantees format.
            raise ValueError(f"invalid numeric value '{num_str}'") from exc
        i += len(num_str)

        # After a number there must be a unit.
        if i >= length:
            raise ValueError(f"missing unit after number at position {i - len(num_str)}")

        # Determine unit – check for 'ms' first because it starts with 'm'.
        unit = None
        if s.startswith("ms", i):
            unit = "ms"
            i += 2
        else:
            # Single‑character units.
            ch = s[i]
            if ch in ("h", "m", "s"):
                unit = ch
                i += 1
            else:
                raise ValueError(f"unknown unit starting at position {i} in '{s}'")

        # Validate unit ordering and uniqueness.
        if unit in used_units:
            raise ValueError(f"unit '{unit}' appears more than once")
        used_units.add(unit)
        _, order = _UNIT_INFO[unit]
        if order <= last_order:
            raise ValueError("units must appear in descending order of size")
        last_order = order

        # Accumulate seconds.
        factor, _ = _UNIT_INFO[unit]
        total_seconds += value * factor

    # At least one component must have been parsed – the loop would have run at least once.
    # The checks above already guarantee that.
    return sign * total_seconds
