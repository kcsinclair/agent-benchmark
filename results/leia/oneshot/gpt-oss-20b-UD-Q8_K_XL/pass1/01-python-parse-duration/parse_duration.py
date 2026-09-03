"""
parse_duration module

Provides a single function `parse_duration` that converts a human‑readable
duration string into a floating‑point number of seconds.

The implementation follows the specification from the problem statement
exactly and raises `ValueError` for any malformed input and `TypeError`
for non‑string arguments.
"""

import re
from typing import Tuple

# Regular expression that matches the overall structure:
#   optional leading minus sign
#   one or more components (number + unit)
#   no other characters (whitespace is stripped before matching)
_COMPONENTS_RE = re.compile(
    r'^(-)?((?:\d+(?:\.\d+)?(?:h|m|s|ms))+)$'
)

# Regular expression that extracts a single component
#   number (integer or decimal)
#   unit (h, m, s or ms)
_COMPONENT_RE = re.compile(r'(\d+(?:\.\d+)?)(h|m|s|ms)')

# Order of units – higher value means larger unit
_UNIT_ORDER = {'h': 3, 'm': 2, 's': 1, 'ms': 0}

def parse_duration(text: str) -> float:
    """
    Parse a duration string and return the total number of seconds.

    Parameters
    ----------
    text : str
        The duration string to parse.

    Returns
    -------
    float
        The total duration in seconds.

    Raises
    ------
    TypeError
        If *text* is not a string.
    ValueError
        If the string does not conform to the required format.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")

    # Strip leading/trailing whitespace – any other whitespace is invalid
    s = text.strip()
    if not s:
        raise ValueError("Empty duration string")

    # Validate the overall structure
    match = _COMPONENTS_RE.match(s)
    if not match:
        raise ValueError("Invalid duration format")

    sign = -1 if match.group(1) else 1
    components_str = match.group(2)

    # Extract individual components
    comps: list[Tuple[str, str]] = _COMPONENT_RE.findall(components_str)
    if not comps:
        raise ValueError("No components found")

    # Ensure that the concatenation of the extracted components
    # reproduces the original component string – this guarantees
    # that every part of the string was a valid component.
    joined = ''.join(num + unit for num, unit in comps)
    if joined != components_str:
        raise ValueError("Invalid component sequence")

    # Check ordering and uniqueness while accumulating the total
    last_order = 4  # greater than any unit order
    total_seconds = 0.0

    for num_str, unit in comps:
        order = _UNIT_ORDER[unit]
        if order > last_order:
            raise ValueError("Units out of order")
        if order == last_order:
            raise ValueError("Repeated unit")
        last_order = order

        value = float(num_str)
        if unit == 'h':
            total_seconds += value * 3600.0
        elif unit == 'm':
            total_seconds += value * 60.0
        elif unit == 's':
            total_seconds += value
        elif unit == 'ms':
            total_seconds += value / 1000.0

    return sign * total_seconds
