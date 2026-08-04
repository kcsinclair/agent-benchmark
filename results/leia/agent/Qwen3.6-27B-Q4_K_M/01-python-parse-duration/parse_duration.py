"""Parse human-readable duration strings into total seconds."""

import re


def parse_duration(text: str) -> float:
    """Parse a duration string and return the total number of seconds as a float.

    Args:
        text: A string representing a duration, e.g. "1h30m", "250ms", "-1.5h".

    Returns:
        The total duration in seconds as a float.

    Raises:
        TypeError: If text is not a string.
        ValueError: If the string does not conform to the duration format.
    """
    if not isinstance(text, str):
        raise TypeError("Expected a string, got {}".format(type(text).__name__))

    stripped = text.strip()
    if not stripped:
        raise ValueError("Empty string is not a valid duration")

    # Check for internal whitespace (after stripping leading/trailing)
    if any(c in stripped for c in ' \t\n\r'):
        raise ValueError("Internal whitespace is not allowed")

    # Determine sign
    negative = False
    if stripped.startswith('-'):
        negative = True
        stripped = stripped[1:]
    elif stripped.startswith('+'):
        raise ValueError("Leading '+' is not allowed")

    if not stripped:
        raise ValueError("No components found")

    # Define units in descending order
    units = ['h', 'm', 's', 'ms']
    unit_values = {'h': 3600, 'm': 60, 's': 1, 'ms': 0.001}

    # Parse components one by one and validate order
    remaining = stripped
    last_unit_index = -1  # Index in units list of the last unit seen
    total_seconds = 0.0

    while remaining:
        # Try to match a component at the start of remaining
        # Number: one or more digits, optionally followed by dot and one or more digits
        # Unit: h, m, s, or ms (ms must be checked before m and s)
        match = re.match(r'^(\d+(\.\d+)?)(h|ms|m|s)', remaining)
        if not match:
            raise ValueError("Invalid component: {}".format(remaining))

        num_str = match.group(1)
        unit = match.group(3)

        # Check that the unit is in strictly descending order
        unit_index = units.index(unit)
        if unit_index <= last_unit_index:
            raise ValueError("Units must be in strictly descending order")
        last_unit_index = unit_index

        # Convert number to float
        num = float(num_str)

        # Add to total
        total_seconds += num * unit_values[unit]

        # Move past this component
        remaining = remaining[match.end():]

    if negative:
        total_seconds = -total_seconds

    return total_seconds
