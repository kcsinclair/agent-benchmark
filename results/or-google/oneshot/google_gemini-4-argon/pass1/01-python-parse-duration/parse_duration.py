# parse_duration.py

import re

# Regex matching an optional minus sign, followed by optional components in strictly
# descending unit order: hours (h), minutes (m), seconds (s), milliseconds (ms).
# Note: this allows matching zero components (e.g., "" or "-"), which is filtered out in code.
_DURATION_RE = re.compile(
    r'^(?P<sign>-)?'
    r'(?:(?P<h>\d+(?:\.\d+)?)h)?'
    r'(?:(?P<m>\d+(?:\.\d+)?)m)?'
    r'(?:(?P<s>\d+(?:\.\d+)?)s)?'
    r'(?:(?P<ms>\d+(?:\.\d+)?)ms)?$'
)

_UNIT_MULTIPLIERS = {
    'h': 3600.0,
    'm': 60.0,
    's': 1.0,
    'ms': 0.001,
}


def parse_duration(text: str) -> float:
    """Parse a human-readable duration string and return the total seconds as a float."""
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")

    stripped = text.strip()
    match = _DURATION_RE.match(stripped)
    if not match:
        raise ValueError(f"Invalid duration format: {text!r}")

    groups = match.groupdict()

    # Rule 3: At least one unit component is required.
    if not any(groups[unit] is not None for unit in _UNIT_MULTIPLIERS):
        raise ValueError(f"Duration must contain at least one component: {text!r}")

    total_seconds = 0.0
    for unit, multiplier in _UNIT_MULTIPLIERS.items():
        val_str = groups[unit]
        if val_str is not None:
            total_seconds += float(val_str) * multiplier

    if groups['sign'] == '-':
        total_seconds = -total_seconds

    return float(total_seconds)
