import re


def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    text = text.strip()

    if not text:
        raise ValueError("empty string")

    # Check for leading minus
    negative = False
    if text.startswith('-'):
        negative = True
        text = text[1:]
        if not text:
            raise ValueError("just a minus sign")

    # Define unit multipliers and order
    units = {
        'h': 3600.0,
        'm': 60.0,
        's': 1.0,
        'ms': 0.001,
    }

    # Valid unit order
    unit_order = ['h', 'm', 's', 'ms']

    # Parse components
    # Each component is a number followed by a unit
    # Number: non-negative decimal, no leading +, no exponents, no bare . or .5, no trailing dot
    # Pattern for number: digits optionally followed by . and more digits
    # Must have at least one digit before the decimal point
    number_pattern = r'(\d+(?:\.\d+)?)'
    unit_pattern = r'(h|m|s|ms)'
    component_pattern = number_pattern + unit_pattern

    # The entire remaining string should be one or more components concatenated
    full_pattern = '^(' + component_pattern + ')+$'

    if not re.match(full_pattern, text):
        raise ValueError(f"invalid duration string: {text!r}")

    # Now parse each component
    comp_pattern = re.compile(component_pattern)
    components = comp_pattern.findall(text)

    if not components:
        raise ValueError("no components found")

    # Check for repeated units and order
    seen_units = []
    total_seconds = 0.0

    for num_str, unit in components:
        # Check unit order
        if unit in seen_units:
            raise ValueError(f"duplicate unit: {unit}")
        if seen_units and unit_order.index(unit) < unit_order.index(seen_units[-1]):
            raise ValueError(f"unit out of order: {unit} after {seen_units[-1]}")
        seen_units.append(unit)

        num = float(num_str)
        total_seconds += num * units[unit]

    if negative:
        total_seconds = -total_seconds

    return total_seconds
