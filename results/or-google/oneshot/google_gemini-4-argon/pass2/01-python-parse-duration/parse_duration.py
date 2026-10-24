import re

# Matches an optional minus sign, followed by optional components in strict
# descending order: h, m, s, ms. Each number must be digits with an optional
# fractional part (digits followed by a dot and more digits).
_DURATION_RE = re.compile(
    r"^(?P<neg>-)?"
    r"(?:(?P<h>\d+(?:\.\d+)?)h)?"
    r"(?:(?P<m>\d+(?:\.\d+)?)m)?"
    r"(?:(?P<s>\d+(?:\.\d+)?)s)?"
    r"(?:(?P<ms>\d+(?:\.\d+)?)ms)?$"
)

_UNIT_MULTIPLIERS = {
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
        raise ValueError(f"Invalid duration format: {text!r}")

    groups = match.groupdict()

    # Ensure at least one component was provided (rejects "" and "-")
    if not any(groups[unit] is not None for unit in _UNIT_MULTIPLIERS):
        raise ValueError(f"Duration must contain at least one component: {text!r}")

    total_seconds = 0.0
    for unit, multiplier in _UNIT_MULTIPLIERS.items():
        val_str = groups[unit]
        if val_str is not None:
            total_seconds += float(val_str) * multiplier

    if groups["neg"]:
        total_seconds = -total_seconds

    return float(total_seconds)
