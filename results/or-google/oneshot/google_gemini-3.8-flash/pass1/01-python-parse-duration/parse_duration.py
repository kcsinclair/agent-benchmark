"""Duration string parser."""

import re

_COMPONENT_RE = re.compile(r"(\d+(?:\.\d+)?)(ms|h|m|s)")

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
    """Parse a human-readable duration string into seconds as a float.

    Args:
        text: A duration string (e.g., "1h30m", "-45m", "250ms").

    Returns:
        The total duration in seconds as a float.

    Raises:
        TypeError: If text is not a string.
        ValueError: If text does not conform to the expected duration format.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")

    s = text.strip()
    if not s:
        raise ValueError("Duration string cannot be empty")

    negative = False
    if s.startswith("-"):
        negative = True
        s = s[1:]
        if not s:
            raise ValueError("Duration string cannot be just '-'")

    pos = 0
    n = len(s)
    last_order = -1
    total = 0.0

    while pos < n:
        match = _COMPONENT_RE.match(s, pos)
        if not match:
            raise ValueError(f"Invalid duration component at position {pos}: {s[pos:]!r}")

        num_str, unit = match.groups()
        unit_order = _UNIT_ORDER[unit]
        if unit_order <= last_order:
            raise ValueError(
                f"Unit {unit!r} is out of order or repeated (seen after order {last_order})"
            )

        last_order = unit_order
        total += float(num_str) * _UNIT_MULTIPLIERS[unit]
        pos = match.end()

    return -total if negative else total
