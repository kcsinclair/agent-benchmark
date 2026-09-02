import re

_COMPONENT_RE = re.compile(r"^(\d+(?:\.\d+)?)(ms|h|m|s)")

_UNIT_ORDER = {
    "h": 0,
    "m": 1,
    "s": 2,
    "ms": 3,
}

_UNIT_MULTIPLIERS = {
    "h": 3600.0,
    "m": 60.0,
    "s": 1.0,
    "ms": 0.001,
}


def parse_duration(text: str) -> float:
    """Parse a human-readable duration string and return total seconds as a float."""
    if not isinstance(text, str):
        raise TypeError(f"text must be a string, got {type(text).__name__}")

    stripped = text.strip()
    if not stripped:
        raise ValueError("Duration string cannot be empty")

    negative = False
    if stripped.startswith("-"):
        negative = True
        stripped = stripped[1:]
        if not stripped:
            raise ValueError("Duration string contains only a minus sign")

    last_unit_idx = -1
    total_seconds = 0.0
    pos = 0

    while pos < len(stripped):
        match = _COMPONENT_RE.match(stripped, pos)
        if not match:
            raise ValueError(f"Invalid duration component at position {pos}: {stripped[pos:]!r}")

        num_str, unit_str = match.groups()
        unit_idx = _UNIT_ORDER[unit_str]
        if unit_idx <= last_unit_idx:
            raise ValueError(f"Unit {unit_str!r} out of order or repeated")

        last_unit_idx = unit_idx
        total_seconds += float(num_str) * _UNIT_MULTIPLIERS[unit_str]
        pos = match.end()

    return -total_seconds if negative else total_seconds
