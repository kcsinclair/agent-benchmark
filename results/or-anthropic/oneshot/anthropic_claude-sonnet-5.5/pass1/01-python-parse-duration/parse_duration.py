# parse_duration.py
import re
from fractions import Fraction

_NUM = r"([0-9]+(?:\.[0-9]+)?)"
_PATTERN = re.compile(
    r"(-)?"
    r"(?:" + _NUM + r"h)?"
    r"(?:" + _NUM + r"m)?"
    r"(?:" + _NUM + r"s)?"
    r"(?:" + _NUM + r"ms)?"
)

# Multipliers (in seconds) for the groups 2..5: h, m, s, ms
_FACTORS = (
    Fraction(3600),
    Fraction(60),
    Fraction(1),
    Fraction(1, 1000),
)


def parse_duration(text: str) -> float:
    """Parse a duration string like '1h30m' or '-2h15m30s500ms' into seconds."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    s = text.strip()
    m = _PATTERN.fullmatch(s)
    if m is None:
        raise ValueError(f"invalid duration: {text!r}")

    values = m.groups()[1:]
    if all(v is None for v in values):
        raise ValueError(f"invalid duration: {text!r}")

    total = Fraction(0)
    for value, factor in zip(values, _FACTORS):
        if value is not None:
            total += Fraction(value) * factor

    if m.group(1):
        total = -total

    try:
        return float(total)
    except OverflowError:
        raise ValueError(f"duration too large: {text!r}") from None
