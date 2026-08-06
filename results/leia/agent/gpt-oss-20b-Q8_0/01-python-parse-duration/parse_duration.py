"""Parse human‑readable duration strings.

The module exposes a single function :func:`parse_duration` which accepts a
string describing a duration and returns the total number of seconds as a
``float``.

The implementation follows the specification from the problem statement and
raises :class:`ValueError` for any malformed input.  A :class:`TypeError` is
raised if the argument is not a string.
"""

from __future__ import annotations

__all__ = ["parse_duration"]

# Mapping of unit to its multiplier in seconds.
_UNIT_SECONDS = {
    "h": 3600.0,
    "m": 60.0,
    "s": 1.0,
    "ms": 0.001,
}
# Order of units – lower value means larger unit.
_UNIT_ORDER = {"h": 0, "m": 1, "s": 2, "ms": 3}


def parse_duration(text: str) -> float:
    """Parse a duration string and return the total number of seconds.

    Parameters
    ----------
    text:
        The duration string to parse.

    Returns
    -------
    float
        Total duration in seconds.

    Raises
    ------
    TypeError
        If *text* is not a string.
    ValueError
        If *text* does not conform to the format rules.
    """

    if not isinstance(text, str):
        raise TypeError("parse_duration expects a string input")

    # Strip outer whitespace and check for empty string.
    text = text.strip()
    if not text:
        raise ValueError("empty duration string")

    # Reject leading '+' sign.
    if text[0] == "+":
        raise ValueError("leading '+' sign is not allowed")

    # Detect optional leading minus sign.
    sign = 1
    if text[0] == "-":
        sign = -1
        text = text[1:]
        if not text:
            raise ValueError("duration string contains only a sign")

    # No internal whitespace is allowed.
    if any(c.isspace() for c in text):
        raise ValueError("whitespace inside duration string is not allowed")

    total_seconds = 0.0
    i = 0
    last_order = -1  # No unit seen yet.
    component_count = 0

    while i < len(text):
        # Parse number: at least one digit, optional fractional part.
        start = i
        while i < len(text) and text[i].isdigit():
            i += 1
        if start == i:
            raise ValueError("expected digits for number component")

        # Optional fractional part.
        if i < len(text) and text[i] == ".":
            i += 1
            frac_start = i
            while i < len(text) and text[i].isdigit():
                i += 1
            if frac_start == i:
                raise ValueError("expected digits after decimal point")

        number_str = text[start:i]
        try:
            number = float(number_str)
        except ValueError as exc:  # pragma: no cover – defensive
            raise ValueError(f"invalid numeric value: {number_str}") from exc

        # Parse unit.
        if i + 2 <= len(text) and text[i:i + 2] == "ms":
            unit = "ms"
            i += 2
        elif i < len(text) and text[i] in "hms":
            unit = text[i]
            i += 1
        else:
            raise ValueError("unit missing or unrecognised after number")

        # Enforce order and uniqueness.
        order = _UNIT_ORDER[unit]
        if order < last_order:
            raise ValueError("units out of order (must be descending)")
        if order == last_order:
            raise ValueError("unit repeated")
        last_order = order

        # Accumulate.
        total_seconds += number * _UNIT_SECONDS[unit]
        component_count += 1

    if component_count == 0:
        raise ValueError("no components found in duration string")

    return sign * total_seconds

# End of module
