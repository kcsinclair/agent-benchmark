"""parse_duration.py

A tiny module that parses human‑readable duration strings and returns the total
number of seconds as a float.

The public API consists of a single function:

    parse_duration(text: str) -> float

The implementation follows the specification given in the problem statement.
"""

import re
from typing import Final

# Order of units from largest to smallest.
_UNIT_ORDER: Final[dict[str, int]] = {"h": 0, "m": 1, "s": 2, "ms": 3}
# Conversion factor to seconds.
_UNIT_FACTOR: Final[dict[str, float]] = {"h": 3600.0, "m": 60.0, "s": 1.0, "ms": 0.001}

# Regular expression for a valid decimal number according to the rules:
#   - at least one digit before an optional fractional part,
#   - no leading dot, no trailing dot, no exponent.
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")  # matches from the current position only


def parse_duration(text: str) -> float:
    """
    Parse a duration string and return the total number of seconds.

    Parameters
    ----------
    text : str
        Human‑readable duration, e.g. ``"1h30m"``, ``"-45m"``, ``"250ms"``.

    Returns
    -------
    float
        Total duration expressed in seconds (may be negative).

    Raises
    ------
    TypeError
        If *text* is not a string.
    ValueError
        If the string does not conform to the required format.
    """
    # ---- type check ---------------------------------------------------------
    if not isinstance(text, str):
        raise TypeError("parse_duration expects a string")

    # ---- strip outer whitespace ---------------------------------------------
    s = text.strip()
    if not s:
        raise ValueError("empty duration string")

    # ---- sign handling -------------------------------------------------------
    sign = 1
    if s[0] == "-":
        sign = -1
        s = s[1:]
        if not s:
            raise ValueError("duration string contains only a minus sign")

    # ---- internal whitespace is forbidden -----------------------------------
    if any(ch.isspace() for ch in s):
        raise ValueError("whitespace inside duration string is not allowed")

    # ---- parsing loop --------------------------------------------------------
    i = 0
    total_seconds = 0.0
    last_order = -1          # ensures the first unit can be any (order >=0)
    used_units = set()
    length = len(s)

    while i < length:
        # ---- number ---------------------------------------------------------
        num_match = _NUMBER_RE.match(s, i)
        if not num_match:
            raise ValueError(f"expected number at position {i}")

        num_str = num_match.group()
        try:
            number = float(num_str)
        except ValueError:          # should never happen because of the regex
            raise ValueError(f"invalid number '{num_str}'")

        i = num_match.end()

        # ---- unit -----------------------------------------------------------

        # Try the two‑character unit first (only "ms" exists)
        if s.startswith("ms", i):
            unit = "ms"
            i += 2
        else:
            # Single‑character unit
            if i >= length:
                raise ValueError(f"missing unit after number at position {i}")
            unit = s[i]
            if unit not in ("h", "m", "s"):
                raise ValueError(f"invalid unit '{unit}' at position {i}")
            i += 1

        # ---- validation of unit order and duplication -----------------------
        if unit in used_units:
            raise ValueError(f"unit '{unit}' appears more than once")
        used_units.add(unit)

        order = _UNIT_ORDER[unit]
        if order <= last_order:
            raise ValueError("units must appear in descending order (h > m > s > ms)")
        last_order = order

        # ---- accumulate ------------------------------------------------------
        total_seconds += number * _UNIT_FACTOR[unit]

    # At least one component must have been parsed (guaranteed by loop condition)
    return sign * total_seconds


__all__ = ["parse_duration"]
