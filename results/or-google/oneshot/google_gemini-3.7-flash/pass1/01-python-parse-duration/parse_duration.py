"""Duration string parser module."""

import re

_UNIT_MULTIPLIERS = {
    "h": 3600.0,
    "m": 60.0,
    "s": 1.0,
    "ms": 0.001,
}

_UNIT_ORDER = {
    "h": 0,
    "m": 1,
    "s": 2,
    "ms": 3,
}

_COMPONENT_REGEX = re.compile(r"(\d+(?:\.\d+)?)(h|ms|m|s)")


def parse_duration(text: str) -> float:
    """Parse a human-readable duration string and return the total seconds as a float."""
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")

    s = text.strip()
    if not s:
        raise ValueError("Empty duration string")

    is_negative = False
    if s.startswith("-"):
        is_negative = True
        s = s[1:]
        if not s:
            raise ValueError("Duration string contains only a minus sign")

    pos = 0
    last_order = -1
    total_seconds = 0.0
    count = 0

    while pos < len(s):
        match = _COMPONENT_REGEX.match(s, pos)
        if not match:
            raise ValueError(f"Invalid duration component starting at index {pos}")

        num_str, unit = match.groups()
        order = _UNIT_ORDER[unit]
        if order <= last_order:
            raise ValueError(f"Unit '{unit}' is out of order or duplicated")

        last_order = order
        val = float(num_str)
        total_seconds += val * _UNIT_MULTIPLIERS[unit]
        pos = match.end()
        count += 1

    if count == 0 or pos != len(s):
        raise ValueError("Invalid duration format")

    return -total_seconds if is_negative else total_seconds
