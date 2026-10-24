import re

_NUM = r"(?:\d+(?:\.\d+)?)"
_COMPONENT = re.compile(r"(\d+(?:\.\d+)?)(ms|h|m|s)")
_FULL = re.compile(r"(-?)((?:\d+(?:\.\d+)?(?:ms|h|m|s))+)")

# Rank: larger number = larger unit; must strictly decrease across components.
_RANK = {"h": 4, "m": 3, "s": 2, "ms": 1}
_SECONDS = {"h": 3600.0, "m": 60.0, "s": 1.0, "ms": 0.001}


def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError("parse_duration expects a str")

    s = text.strip()
    if not s:
        raise ValueError("empty duration string")

    full = _FULL.fullmatch(s)
    if full is None:
        raise ValueError(f"invalid duration string: {text!r}")

    sign = -1.0 if full.group(1) == "-" else 1.0
    body = full.group(2)

    total = 0.0
    prev_rank = None
    pos = 0
    while pos < len(body):
        m = _COMPONENT.match(body, pos)
        if m is None:
            raise ValueError(f"invalid duration string: {text!r}")
        number, unit = m.group(1), m.group(2)
        rank = _RANK[unit]
        if prev_rank is not None and rank >= prev_rank:
            raise ValueError(f"units out of order or repeated: {text!r}")
        prev_rank = rank
        total += float(number) * _SECONDS[unit]
        pos = m.end()

    return sign * total
