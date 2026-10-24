"""Parse human-readable duration strings into seconds."""

import re

__all__ = ["parse_duration"]

_NUM = r"([0-9]+(?:\.[0-9]+)?)"
_PATTERN = re.compile(
    r"(-)?"
    r"(?:" + _NUM + r"h)?"
    r"(?:" + _NUM + r"m)?"
    r"(?:" + _NUM + r"s)?"
    r"(?:" + _NUM + r"ms)?"
)

_FACTORS = (3600.0, 60.0, 1.0, 0.001)


def parse_duration(text: str) -> float:
    """Parse a duration like '1h30m' or '-250ms' and return seconds as float."""
    if not isinstance(text, str):
        raise TypeError("parse_duration() argument must be str, not %s"
                        % type(text).__name__)
    s = text.strip()
    m = _PATTERN.fullmatch(s)
    if m is None:
        raise ValueError("invalid duration: %r" % (text,))
    parts = m.groups()[1:]
    if all(p is None for p in parts):
        raise ValueError("invalid duration: %r" % (text,))
    total = 0.0
    for value, factor in zip(parts, _FACTORS):
        if value is not None:
            total += float(value) * factor
    if m.group(1):
        total = -total
    return float(total)
