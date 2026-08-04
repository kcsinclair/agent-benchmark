"""
parse_duration.py

A tiny module that parses human‑readable duration strings and returns the total
number of seconds as a float.

The public API consists of a single function:

    parse_duration(text: str) -> float

The implementation follows the specification given in the problem statement.
"""

from __future__ import annotations

import re
from typing import Final

# --------------------------------------------------------------------------- #
# Regular expression for a *valid* number according to the rules:
#   - one or more digits
#   - optional fractional part consisting of a dot followed by one or more digits
#   - no leading dot, no trailing dot, no exponent, no sign
# --------------------------------------------------------------------------- #
_NUMBER_RE: Final = re.compile(r"\d+(?:\.\d+)?")

# Unit → (order, factor‑in‑seconds)
# The order values enforce the required descending order:
#   h (4) > m (3) > s (2) > ms (1)
_UNIT_INFO: Final[dict[str, tuple[int, float]]] = {
    "h": (4, 3600.0),
    "m": (3, 60.0),
    "s": (2, 1.0),
    "ms": (1, 0.001),
}


def parse_duration(text: str) -> float:
    """
    Parse a duration string and return the total number of seconds.

    Parameters
    ----------
    text: str
        Human‑readable duration, e.g. ``"1h30m"`` or ``"-250ms"``.

    Returns
    -------
    float
        The duration expressed in seconds (may be negative).

    Raises
    ------
    TypeError
        If *text* is not a string.
    ValueError
        If the string violates any of the formatting rules.
    """
    # ------------------------------------------------------------------- #
    # 1. Basic type check and whitespace handling
    # ------------------------------------------------------------------- #
    if not isinstance(text, str):
        raise TypeError("parse_duration expects a string")

    # Strip leading/trailing whitespace – internal whitespace is forbidden
    stripped = text.strip()
    if not stripped:
        raise ValueError("empty duration string")

    if any(ch.isspace() for ch in stripped):
        raise ValueError("whitespace inside duration string is not allowed")

    # ------------------------------------------------------------------- #
    # 2. Detect optional leading minus sign
    # ------------------------------------------------------------------- #
    sign = 1.0
    if stripped[0] == "-":
        sign = -1.0
        stripped = stripped[1:]
        if not stripped:
            raise ValueError("duration string contains only a minus sign")

    # ------------------------------------------------------------------- #
    # 3. Parse components sequentially
    # ------------------------------------------------------------------- #
    i = 0
    total_seconds = 0.0
    seen_units: set[str] = set()
    previous_order: int | None = None
    length = len(stripped)

    while i < length:
        # ---- number ----------------------------------------------------- #
        num_match = _NUMBER_RE.match(stripped, i)
        if not num_match:
            raise ValueError(f"expected number at position {i}")

        num_str = num_match.group()
        i = num_match.end()

        # ---- unit ------------------------------------------------------- #
        # Try the two‑character unit "ms" first, then single‑character units.
        if stripped.startswith("ms", i):
            unit = "ms"
            i += 2
        elif i < length and stripped[i] in ("h", "m", "s"):
            unit = stripped[i]
            i += 1
        else:
            raise ValueError(f"expected unit after number at position {i}")

        # ---- validation of order and duplication ----------------------- #
        if unit in seen_units:
            raise ValueError(f"unit '{unit}' appears more than once")
        order, factor = _UNIT_INFO[unit]

        if previous_order is not None and order >= previous_order:
            # order must strictly decrease (h > m > s > ms)
            raise ValueError("units are not in descending order")
        previous_order = order
        seen_units.add(unit)

        # ---- conversion ------------------------------------------------- #
        try:
            value = float(num_str)
        except ValueError as exc:  # pragma: no cover – should never happen
            raise ValueError(f"invalid numeric value '{num_str}'") from exc

        total_seconds += value * factor

    # At least one component must have been parsed
    if not seen_units:
        raise ValueError("duration string contains no components")

    return sign * total_seconds
