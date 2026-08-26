"""
parse_duration.py

Provides a single function ``parse_duration`` that converts a human‑readable
duration string into a total number of seconds (float).

The accepted format follows the specification given in the problem
statement.  Any violation raises ``ValueError``; a non‑string argument raises
``TypeError``.
"""

from __future__ import annotations

import re
from typing import Final

__all__: Final = ["parse_duration"]


# --------------------------------------------------------------------------- #
# Helper data
# --------------------------------------------------------------------------- #
_UNITS_ORDER = ["h", "m", "s", "ms"]               # descending size
_UNIT_FACTOR = {
    "h": 3600.0,   # hours → seconds
    "m": 60.0,     # minutes → seconds
    "s": 1.0,      # seconds → seconds
    "ms": 0.001,   # milliseconds → seconds
}

# Regular expression for a non‑negative decimal number without leading '+',
# without exponent, without a leading dot and without a trailing dot.
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")  # e.g. 2, 1.5, 0.25


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def parse_duration(text: str) -> float:
    """
    Parse a duration string and return the total number of seconds.

    Parameters
    ----------
    text: str
        Human‑readable duration (e.g. ``"1h30m"``, ``"-250ms"``).

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
    # ------------------------------------------------------------------- #
    # Type checking
    # ------------------------------------------------------------------- #
    if not isinstance(text, str):
        raise TypeError("duration must be a string")

    # Strip outer whitespace – internal whitespace is forbidden.
    s = text.strip()
    if not s:
        raise ValueError("empty duration string")

    if any(ch.isspace() for ch in s):
        raise ValueError("whitespace inside duration string is not allowed")

    # ------------------------------------------------------------------- #
    # Sign handling
    # ------------------------------------------------------------------- #
    sign = 1.0
    if s[0] == "-":
        sign = -1.0
        s = s[1:]
        if not s:
            raise ValueError("duration string contains only a sign")

    total_seconds = 0.0
    last_unit_index = -1          # ensures strictly descending order
    components_parsed = 0

    # ------------------------------------------------------------------- #
    # Main parsing loop
    # ------------------------------------------------------------------- #
    while s:
        # ---- number ----------------------------------------------------- #
        num_match = _NUMBER_RE.match(s)
        if not num_match:
            raise ValueError(f"expected a number at position {len(text) - len(s)}")

        number_str = num_match.group(0)
        try:
            number_val = float(number_str)
        except ValueError as exc:          # pragma: no cover (should never happen)
            raise ValueError("invalid numeric value") from exc

        s = s[num_match.end():]            # consume the number

        # ---- unit ------------------------------------------------------- #
        if s.startswith("ms"):
            unit = "ms"
            s = s[2:]
        elif s and s[0] in ("h", "m", "s"):
            unit = s[0]
            s = s[1:]
        else:
            raise ValueError(f"expected a unit after number '{number_str}'")

        # ---- order / repetition check ----------------------------------- #
        unit_index = _UNITS_ORDER.index(unit)
        if unit_index <= last_unit_index:
            raise ValueError("units must appear in descending order and not repeat")
        last_unit_index = unit_index

        # ---- accumulate ------------------------------------------------- #
        total_seconds += number_val * _UNIT_FACTOR[unit]
        components_parsed += 1

    if components_parsed == 0:
        raise ValueError("duration string contains no components")

    return sign * total_seconds
