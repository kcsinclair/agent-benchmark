import re


def parse_duration(text: str) -> float:
    """
    Parse a human-readable duration string and return the total number of seconds as a float.
    
    Args:
        text: A string representing a duration, e.g., "1h30m", "250ms", "-45m"
        
    Returns:
        The total duration in seconds as a float.
        
    Raises:
        TypeError: If text is not a string.
        ValueError: If the duration string is invalid.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    
    # Strip leading and trailing whitespace
    stripped = text.strip()
    
    # Check if empty after stripping
    if not stripped:
        raise ValueError("Empty duration string")
    
    # Check for leading minus sign
    negative = False
    if stripped.startswith('-'):
        negative = True
        stripped = stripped[1:]
        if not stripped:
            raise ValueError("Minus sign with no components")
    
    # The remaining string must consist of one or more components with no whitespace
    # Each component is a number followed by a unit (h, m, s, ms)
    # Units must appear in strictly descending order: h, m, s, ms
    # Each unit appears at most once
    
    # Validate that there's no whitespace in the stripped string (other than what was already stripped)
    if ' ' in stripped or '\t' in stripped or '\n' in stripped or '\r' in stripped:
        raise ValueError("Whitespace not allowed within duration string")
    
    # Define the valid units in order
    units_order = ['h', 'm', 's', 'ms']
    
    # We need to parse the string into components
    # Each component: number (non-negative decimal) followed by a unit
    # The number can be: digits, optionally followed by '.' and more digits
    # Valid number patterns: "1", "1.5", "0.25", "2"
    # Invalid: ".5", "5.", "1e5", "+1"
    
    # Let's use regex to find all components
    # Pattern for a number: one or more digits, optionally followed by a dot and one or more digits
    number_pattern = r'(\d+(?:\.\d+)?)'
    
    # We'll iterate through the string, finding each component
    remaining = stripped
    components = []
    used_units = set()
    
    while remaining:
        # Try to match a number followed by a unit
        # The unit can be 'h', 'm', 's', or 'ms'
        # We need to be careful with 'ms' vs 'm' and 's'
        
        # Try to match the longest possible unit first to avoid ambiguity
        # Check for 'ms' first, then 'h', 'm', 's'
        
        match = re.match(r'^(\d+(?:\.\d+)?)(ms|h|m|s)', remaining)
        if not match:
            raise ValueError(f"Invalid component in duration string: '{remaining}'")
        
        number_str = match.group(1)
        unit = match.group(2)
        
        # Check if the unit has already been used
        if unit in used_units:
            raise ValueError(f"Duplicate unit '{unit}'")
        
        # Check ordering: units must appear in strictly descending order
        # h > m > s > ms
        unit_index = units_order.index(unit)
        if components:
            last_unit_index = units_order.index(components[-1][1])
            if unit_index >= last_unit_index:
                raise ValueError(f"Units not in strictly descending order: '{unit}' after '{components[-1][1]}'")
        
        # Parse the number
        try:
            number = float(number_str)
        except ValueError:
            raise ValueError(f"Invalid number: '{number_str}'")
        
        # Number must be non-negative (it is, since we only match digits and optional decimal)
        # But let's ensure it's not negative (the regex ensures non-negative)
        
        components.append((number, unit))
        used_units.add(unit)
        
        # Move past this component
        remaining = remaining[match.end():]
    
    # Check that we consumed the entire string
    if remaining:
        raise ValueError(f"Unexpected characters at end of duration string: '{remaining}'")
    
    # Check that at least one component exists
    if not components:
        raise ValueError("At least one component is required")
    
    # Calculate total seconds
    total_seconds = 0.0
    for number, unit in components:
        if unit == 'h':
            total_seconds += number * 3600
        elif unit == 'm':
            total_seconds += number * 60
        elif unit == 's':
            total_seconds += number
        elif unit == 'ms':
            total_seconds += number / 1000
    
    if negative:
        total_seconds = -total_seconds
    
    return total_seconds
