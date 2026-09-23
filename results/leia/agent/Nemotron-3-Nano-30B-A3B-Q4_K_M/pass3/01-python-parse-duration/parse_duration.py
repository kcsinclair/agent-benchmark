import re

def parse_duration(text: str) -> float:
    """
    Parse a human‑readable duration string and return the total number of seconds
    as a float.

    Raises:
        TypeError:  If ``text`` is not a string.
        ValueError: If the string does not conform to the required format.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")

    s = text.strip()
    if not s:
        raise ValueError("Empty duration string")

    # Detect optional leading minus sign
    if s[0] == '-':
        sign = -1
        rest = s[1:]
    else:
        sign = 1
        rest = s

    # Whitespace anywhere else is invalid
    if any(c.isspace() for c in rest):
        raise ValueError("Whitespace not allowed inside duration string")

    # Units in descending order of magnitude
    units = ['h', 'm', 's', 'ms']
    unit_index = {u: i for i, u in enumerate(units)}

    # Pattern: number (digits with optional fractional part) followed by a unit.
    # 'ms' is tried first to avoid matching 'm' when 'ms' is intended.
    pattern = re.compile(r'(\d+(?:\.\d+)?)(ms|h|m|s)')

    i = 0
    current_order = -1  # ensures strictly increasing order
    total_seconds = 0.0

    while i < len(rest):
        match = pattern.match(rest, i)
        if not match:
            raise ValueError("Invalid component format")
        num_str, unit = match.groups()

        # Convert the numeric part to float
        try:
            value = float(num_str)
        except ValueError:
            raise ValueError("Invalid number in duration component")

        # Validate unit order (must be strictly descending)
        idx = unit_index[unit]
        if idx <= current_order:
            raise ValueError("Units are not in strictly descending order")

        # Convert to seconds and accumulate
        factor = {'h': 3600, 'm': 60, 's': 1, 'ms': 0.001}[unit]
        total_seconds += value * factor

        # Update state
        current_order = idx
        i = match.end()

    # Ensure no extra characters remain
    if i != len(rest):
        raise ValueError("Extra characters after valid components")

    return sign * total_seconds
