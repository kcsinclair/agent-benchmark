import re
from fractions import Fraction

_NUM = r"([0-9]+(?:\.[0-9]+)?)"
_PATTERN = re.compile(
    r"(-)?"
    r"(?:" + _NUM + r"h)?"
    r"(?:" + _NUM + r"m(?!s))?"
    r"(?:" + _NUM + r"s)?"
    r"(?:" + _NUM + r"ms)?"
)

_FACTORS = (Fraction(3600), Fraction(60), Fraction(1), Fraction(1, 1000))


def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    s = text.strip()
    m = _PATTERN.fullmatch(s)
    if m is None:
        raise ValueError("invalid duration: %r" % (text,))
    parts = m.groups()[1:]
    if all(p is None for p in parts):
        raise ValueError("invalid duration: %r" % (text,))
    total = Fraction(0)
    for p, f in zip(parts, _FACTORS):
        if p is not None:
            total += Fraction(p) * f
    result = float(total)
    if m.group(1):
        result = -result
    return result
