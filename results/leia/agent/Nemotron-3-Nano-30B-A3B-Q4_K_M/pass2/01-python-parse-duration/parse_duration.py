import re

def parse_duration(text: str) -> float:
    """
    Parse a human‑readable duration string and return the total number of seconds
    as a float.

    Raises:
        TypeError: If ``text`` is not a string.
        ValueError: If the string does not conform to the required format.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")

    # Strip leading/trailing whitespace
    text = text.strip()
    if not text:
        raise ValueError("Empty duration string")

    # Handle optional leading minus sign
    sign = 1
    if text[0] == '-':
        sign = -1
        text = text[1:]
        if not text:
            raise ValueError("Minus sign without following duration")

    # Regex for a non‑negative decimal number followed by a unit
    # Allows: 1, 1.5, 0.25 but not .5, 5., etc.
    pattern = re.compile(r'(\d+(?:\.\d+)?)(h|m|s|ms)')

    # Order indices for validation of descending size
    order_idx = {'h': 0, 'm': 1, 's': 2, 'ms': 3}
    seen_units = set()
    total_seconds = 0.0
    pos = 0  # current parsing position in the string

    prev_order = -1  # to enforce strictly increasing order

    for match in pattern.finditer(text):
        num_str, unit = match.group(1), match.group(2)

        # Unit must not repeat
        if unit in seen_units:
            raise ValueError(f"Unit {unit} repeated")
        seen_units.add(unit)

        # Validate ordering: units must appear in strictly descending size order
        current_order = order_idx[unit]
        if current_order <= prev_order:
            raise ValueError("Components are not in descending order")
        prev_order = current_order

        # Convert the numeric part to float
        try:
            value = float(num_str)
        except ValueError:
            raise ValueError("Invalid numeric format")

        # Convert to seconds based on unit
        if unit == 'h':
            secs = value * 3600.0
        elif unit == 'm':
            secs = value * 60.0
        elif unit == 's':
            secs = value
        elif unit == 'ms':
            secs = value * 0.001
        else:
            # This should never happen because of the regex, but keep for safety
            raise ValueError("Invalid unit")

        # Ensure there are no gaps between components
        if match.start() != pos:
            raise ValueError("Extra characters before component")
        pos = match.end()

        total_seconds += secs

    # After processing all matches, we must have consumed the entire string
    if pos != len(text):
        raise ValueError("Extra characters after valid components")

    # If no components were found, the input was invalid
    if not seen_units:
        raise ValueError("Missing unit")

    return sign * total_seconds
