import re

# Matches an optional minus sign, followed by optional components in strict descending order.
_DURATION_RE = re.compile(
    r"^(?P<sign>-?)"
    r"(?:(?P<h>\d+(?:\.\d+)?)h)?"
    r"(?:(?P<m>\d+(?:\.\d+)?)m)?"
    r"(?:(?P<s>\d+(?:\.\d+)?)s)?"
    r"(?:(?P<ms>\d+(?:\.\d+)?)ms)?$"
)

_UNIT_FACTORS = {
    "h": 3600.0,
    "m": 60.0,
    "s": 1.0,
    "ms": 0.001,
}


def parse_duration(text: str) -> float:
    """Parse a human-readable duration string and return total seconds as a float."""
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")

    stripped = text.strip()
    match = _DURATION_RE.match(stripped)

    if not match:
        raise ValueError(f"Invalid duration string: {text!r}")

    groups = match.groupdict()
    sign_str = groups.pop("sign")

    # Ensure at least one unit component was present
    if all(val is None for val in groups.values()):
        raise ValueError(f"Duration must contain at least one component: {text!r}")

    total_seconds = 0.0
    for unit, val in groups.items():
        if val is not None:
            total_seconds += float(val) * _UNIT_FACTORS[unit]

    if sign_str == "-":
        total_seconds = -total_seconds

    return total_seconds
