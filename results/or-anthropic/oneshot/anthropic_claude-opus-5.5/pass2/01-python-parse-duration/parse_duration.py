"""Parse human-readable duration strings such as "1h30m" or "250ms"."""

import re
from decimal import Decimal

__all__ = ["parse_duration"]

# A number is ASCII digits with an optional fractional part (digits required on both sides of the dot).
_NUM = r"[0-9]+(?:\.[0-9]+)?"

# Units must appear in strictly descending order, each at most once.
# The regex structure enforces both rules.
# For input like "1ms", backtracking resolves it correctly:
# "1m" would leave a dangling "s" with no number, so the regex matches it as milliseconds.
_PATTERN = re.compile(
    r"(?P<sign>-)?"
    r"(?:(?P<h>" + _NUM + r")h)?"
    r"(?:(?P<m>" + _NUM + r")m)?"
    r"(?:(?P<s>" + _NUM + r")s)?"
    r"(?:(?P<ms>" + _NUM + r")ms)?"
)

_FACTORS = {
    "h": Decimal(3600),
    "m": Decimal(60),
    "s": Decimal(1),
    "ms": Decimal("0.001"),
}


def parse_duration(text: str) -> float:
    """Return the total number of seconds represented by *text*.

    Raises TypeError for non-string input and ValueError for malformed input.
    """
    if not isinstance(text, str):
        raise TypeError(
            "parse_duration() argument must be str, not %s" % type(text).__name__
        )

    stripped = text.strip()
    match = _PATTERN.fullmatch(stripped)
    if match is None:
        raise ValueError("invalid duration string: %r" % text)

    total = Decimal(0)
    found = False
    for unit, factor in _FACTORS.items():
        value = match.group(unit)
        if value is not None:
            found = True
            total += Decimal(value) * factor

    if not found:
        raise ValueError("invalid duration string (no components): %r" % text)

    result = float(total)
    if match.group("sign"):
        result = -result
    return result
