import re

_COMPONENT = re.compile(r"(\d+(?:\.\d+)?)(ms|h|m|s)")

# Rank increases as units get smaller; order must be strictly increasing.
_RANK = {"h": 0, "m": 1, "s": 2, "ms": 3}
_SECONDS = {"h": 3600.0, "m": 60.0, "s": 1.0, "ms": 0.001}


def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError("parse_duration expects a str")

    s = text.strip()
    if not s:
        raise ValueError("empty duration string")

    sign = 1.0
    if s.startswith("-"):
        sign = -1.0
        s = s[1:]

    if not s:
        raise ValueError("no components in duration string")

    pos = 0
    last_rank = -1
    total = 0.0
    while pos < len(s):
        match = _COMPONENT.match(s, pos)
        if match is None:
            raise ValueError(f"invalid duration component at position {pos}: {text!r}")
        number, unit = match.group(1), match.group(2)
        rank = _RANK[unit]
        if rank <= last_rank:
            raise ValueError(f"units out of order or repeated: {text!r}")
        last_rank = rank
        total += float(number) * _SECONDS[unit]
        pos = match.end()

    return sign * total
