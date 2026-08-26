import re


def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    text = text.strip()

    if not text:
        raise ValueError("empty duration string")

    # Check for leading minus
    negative = False
    if text.startswith('-'):
        negative = True
        text = text[1:]
        if not text:
            raise ValueError("empty duration string after minus sign")

    # Define unit order and conversion factors
    unit_order = ['h', 'm', 's', 'ms']
    unit_seconds = {
        'h': 3600.0,
        'm': 60.0,
        's': 1.0,
        'ms': 0.001,
    }

    # Pattern for a valid number: digits with optional fractional part
    # No leading +, no exponents, no bare . or .5, no trailing dot
    # Valid: 2, 1.5, 0.25
    # Invalid: .5, 5., 1e2, +1
    number_pattern = r'(\d+(?:\.\d+)?)'

    # Build a pattern to match components
    # Each component is a number followed by a unit
    # Units must appear in strictly descending order, each at most once
    # We need to parse the string and validate the order

    # First, let's try to match the entire string as a sequence of components
    # We'll use a regex that captures all components
    # The pattern: number followed by one of the units, repeated in order

    # We need to ensure:
    # 1. Units appear in strictly descending order (h, m, s, ms)
    # 2. Each unit appears at most once
    # 3. At least one component

    # Let's parse manually to have better control

    remaining = text
    total_seconds = 0.0
    last_unit_index = -1  # Track the index of the last unit used

    while remaining:
        # Try to match a number followed by a unit
        match = re.match(r'^(\d+(?:\.\d+)?)(h|m|s|ms)', remaining)
        if not match:
            raise ValueError(f"invalid component in duration: {remaining}")

        number_str = match.group(1)
        unit = match.group(2)

        # Check that the unit is in strictly descending order
        unit_index = unit_order.index(unit)
        if unit_index <= last_unit_index:
            raise ValueError(f"unit '{unit}' is not in strictly descending order")

        last_unit_index = unit_index

        # Convert number to float
        number = float(number_str)

        # Add to total
        total_seconds += number * unit_seconds[unit]

        # Move past this component
        remaining = remaining[match.end():]

    if not text:
        raise ValueError("empty duration string")

    if negative:
        total_seconds = -total_seconds

    return total_seconds
