# parse_duration.py
"""
A tiny utility to parse human‑readable duration strings.

The public API is a single function:

    parse_duration(text: str) -> float

It converts a string such as ``"1h30m"`` into the total number of seconds
as a float.  The implementation follows the rules described in the
problem statement and raises ``ValueError`` for malformed input or
``TypeError`` if the argument is not a string.
"""

import re
from typing import Dict

__all__ = ["parse_duration"]


def parse_duration(text: str) -> float:
    """
    Parse a duration string and return the total number of seconds.

    Parameters
    ----------
    text : str
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
        If the string does not conform to the required format.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    # Strip leading/trailing whitespace; any internal whitespace is invalid.
    s = text.strip()
    if not s:
        raise ValueError("empty duration string")

    # Handle optional leading minus sign.
    sign = 1
    if s[0] == "-":
        sign = -1
        s = s[1:]
    if not s:
        raise ValueError("duration string missing components")

    # Regular expression for a single component: number + unit.
    # Number: one or more digits, optional fractional part.
    # Unit: one of h, m, s, ms.
    component_re = re.compile(r"(\d+(?:\.\d+)?)(h|m|s|ms)")

    # Mapping of units to their order and conversion factor to seconds.
    unit_order: Dict[str, int] = {"h": 0, "m": 1, "s": 2, "ms": 3}
    unit_factor: Dict[str, float] = {"h": 3600.0, "m": 60.0, "s": 1.0, "ms": 0.001}

    pos = 0
    total_seconds = 0.0
    last_index = -1

    while pos < len(s):
        match = component_re.match(s, pos)
        if not match:
            raise ValueError(f"invalid duration format at position {pos}")

        number_str, unit = match.group(1), match.group(2)

        # Enforce descending order and uniqueness of units.
        idx = unit_order[unit]
        if idx <= last_index:
            raise ValueError(f"unit order violation: '{unit}'")
        last_index = idx

        # Convert the numeric part to float.
        try:
            number = float(number_str)
        except ValueError:
            raise ValueError(f"invalid number: '{number_str}'")

        total_seconds += number * unit_factor[unit]
        pos = match.end()

    # After parsing all components, we should be at the end of the string.
    if pos != len(s):
        raise ValueError("invalid trailing characters")

    return sign * total_seconds
