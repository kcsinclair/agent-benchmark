# parse_duration.py
import re
from fractions import Fraction

_NUM = r"([0-9]+(?:\.[0-9]+)?)"

_PATTERN = re.compile(
    r"(?P<neg>-)?"
    r"(?:" + _NUM.replace("(", "(?P<h>", 1) + r"h)?"
    r"(?:" + _NUM.replace("(", "(?P<m>", 1) + r"m(?!s))?"
    r"(?:" + _NUM.replace("(", "(?P<s>", 1) + r"s)?"
    r"(?:" + _NUM.replace("(", "(?P<ms>", 1) + r"ms)?",
    re.ASCII,
)

_MULTIPLIERS = (
    ("h", Fraction(3600)),
    ("m", Fraction(60)),
    ("s", Fraction(1)),
    ("ms", Fraction(1, 1000)),
)


def parse_duration(text: str) -> float:
    """Parse a duration string like '1h30m' or '2h15m30s500ms' into seconds."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    s = text.strip()
    match = _PATTERN.fullmatch(s)
    if match is None:
        raise ValueError(f"invalid duration: {text!r}")

    total = Fraction(0)
    found = False
    for name, mult in _MULTIPLIERS:
        value = match.group(name)
        if value is not None:
            found = True
            total += Fraction(value) * mult

    if not found:
        raise ValueError(f"invalid duration: {text!r}")

    if match.group("neg"):
        total = -total

    try:
        return float(total)
    except OverflowError:
        raise ValueError(f"duration too large: {text!r}") from None
