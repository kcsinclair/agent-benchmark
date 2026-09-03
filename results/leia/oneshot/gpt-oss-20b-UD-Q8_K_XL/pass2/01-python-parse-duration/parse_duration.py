# parse_duration.py
# -----------------
# A tiny module that parses human‑readable duration strings into seconds.

import re

# Regular expression for a single component: a non‑negative decimal number
# followed by one of the allowed units.
_COMPONENT_RE = re.compile(r'(\d+(?:\.\d+)?)(h|m|s|ms)')

# Order of units – lower value means a larger unit.
_UNIT_ORDER = {'h': 0, 'm': 1, 's': 2, 'ms': 3}

# Conversion factors to seconds.
_UNIT_FACTOR = {'h': 3600.0, 'm': 60.0, 's': 1.0, 'ms': 0.001}


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
        The duration expressed in seconds.

    Raises
    ------
    TypeError
        If *text* is not a string.
    ValueError
        If the string does not conform to the required format.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")

    # Strip leading/trailing whitespace.
    stripped = text.strip()
    if not stripped:
        raise ValueError("Empty duration string")

    # Handle optional leading minus sign.
    sign = 1
    if stripped[0] == '-':
        sign = -1
        stripped = stripped[1:]
    elif stripped[0] == '+':
        raise ValueError("Leading '+' not allowed")

    # No whitespace is allowed inside the string.
    if re.search(r'\s', stripped):
        raise ValueError("Whitespace inside duration string")

    if not stripped:
        raise ValueError("No components after sign")

    pos = 0
    total_seconds = 0.0
    last_unit_index = -1
    seen_units = set()

    while pos < len(stripped):
        match = _COMPONENT_RE.match(stripped, pos)
        if not match:
            raise ValueError(f"Invalid component at position {pos}")

        number_str, unit = match.group(1), match.group(2)

        # Check unit order and uniqueness.
        unit_index = _UNIT_ORDER[unit]
        if unit_index <= last_unit_index:
            raise ValueError("Units out of order or repeated")
        if unit in seen_units:
            raise ValueError("Repeated unit")
        seen_units.add(unit)
        last_unit_index = unit_index

        # Convert the numeric part to a float.
        try:
            number = float(number_str)
        except ValueError:
            raise ValueError("Invalid number")

        # Accumulate seconds.
        total_seconds += number * _UNIT_FACTOR[unit]

        pos = match.end()

    # Ensure the entire string was consumed.
    if pos != len(stripped):
        raise ValueError("Trailing characters after last component")

    return sign * total_seconds
