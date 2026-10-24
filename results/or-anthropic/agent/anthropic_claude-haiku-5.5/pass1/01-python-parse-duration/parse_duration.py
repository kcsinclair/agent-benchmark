import re

_NUM = r"(\d+(?:\.\d+)?)"

# Components must appear in order h, m, s, ms; each at most once.
# Ordering of alternatives for the minute/second/millisecond tail is
# handled by requiring "m" not to be followed by "s" (which would be "ms"
# only if the unit is 'ms'; "m" followed by "s" is ambiguous, so we use
# explicit lookaheads).
_PATTERN = re.compile(
    r"^"
    r"(?:" + _NUM + r"h)?"
    r"(?:" + _NUM + r"m(?!s))?"
    r"(?:" + _NUM + r"s)?"
    r"(?:" + _NUM + r"ms)?"
    r"$"
)

_FACTORS = (3600.0, 60.0, 1.0, 0.001)


def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError("parse_duration expects a str")

    s = text.strip()
    if not s:
        raise ValueError("empty duration string")

    negative = False
    if s.startswith("-"):
        negative = True
        s = s[1:]

    if not s:
        raise ValueError("no components in duration string")

    match = _PATTERN.match(s)
    if match is None:
        raise ValueError(f"invalid duration string: {text!r}")

    groups = match.groups()
    if all(g is None for g in groups):
        raise ValueError(f"no components in duration string: {text!r}")

    total = 0.0
    for value, factor in zip(groups, _FACTORS):
        if value is not None:
            total += float(value) * factor

    return -total if negative else total
