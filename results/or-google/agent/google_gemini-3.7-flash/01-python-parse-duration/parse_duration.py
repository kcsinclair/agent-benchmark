import re

_UNIT_ORDER = {
    'h': 0,
    'm': 1,
    's': 2,
    'ms': 3,
}

_UNIT_FACTORS = {
    'h': 3600.0,
    'm': 60.0,
    's': 1.0,
    'ms': 0.001,
}

_COMPONENT_RE = re.compile(r'(\d+(?:\.\d+)?)(ms|[hms])')


def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError(f"text must be a str, got {type(text).__name__}")

    s = text.strip()
    if not s:
        raise ValueError("empty duration string")

    negative = False
    if s.startswith('-'):
        negative = True
        s = s[1:]

    if not s:
        raise ValueError("missing duration components after minus sign")

    pos = 0
    length = len(s)
    last_order = -1
    total_seconds = 0.0
    count = 0

    while pos < length:
        match = _COMPONENT_RE.match(s, pos)
        if match is None:
            raise ValueError(f"invalid duration format at position {pos}: {s[pos:]!r}")

        num_str, unit = match.groups()
        unit_order = _UNIT_ORDER[unit]
        if unit_order <= last_order:
            raise ValueError(f"unit {unit!r} is out of order or duplicate")

        last_order = unit_order
        total_seconds += float(num_str) * _UNIT_FACTORS[unit]
        count += 1
        pos = match.end()

    if count == 0:
        raise ValueError("at least one duration component is required")

    return -total_seconds if negative else total_seconds
