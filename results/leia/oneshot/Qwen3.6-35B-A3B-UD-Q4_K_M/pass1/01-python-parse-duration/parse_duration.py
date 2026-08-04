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
    
    # Check for empty string after stripping
    if not stripped:
        raise ValueError("Empty duration string")
    
    # Check for valid format using regex
    # Pattern: optional minus sign, then one or more components
    # Each component: a non-negative decimal number followed by a unit
    # Units must be in order: h, m, s, ms (each at most once)
    
    # First, let's define the valid number pattern
    # Non-negative decimal: digits with optional fractional part
    # No leading +, no exponents, no bare . or .5, no trailing dot
    # Valid: 2, 1.5, 0.25
    # Invalid: .5, 5., +1, 1e2
    
    number_pattern = r'(?:0|[1-9]\d*)(?:\.\d+)?'
    
    # Unit pattern: ms, s, m, h (but we need to check order separately)
    # We'll parse components manually to enforce order
    
    # Check if the string starts with optional minus
    negative = False
    if stripped.startswith('-'):
        negative = True
        stripped = stripped[1:]
    elif stripped.startswith('+'):
        raise ValueError("Leading + is not allowed")
    
    if not stripped:
        raise ValueError("Empty duration string after removing sign")
    
    # Now parse components
    # Valid units in order: h, m, s, ms
    # Each unit can appear at most once, in descending order of size
    
    # We need to match components from left to right
    # A component is: number followed by unit
    
    # Let's use a regex to find all components
    # The full pattern for a component: number_pattern followed by one of the units
    
    # But we need to ensure no whitespace inside, and proper ordering
    
    # Let's try to match the entire string against a pattern that enforces order
    # Possible patterns:
    # h only
    # h m
    # h s
    # h ms
    # h m s
    # h m ms
    # h s ms
    # h m s ms
    # m only
    # m s
    # m ms
    # m s ms
    # s only
    # s ms
    # ms only
    
    # This is complex. Let's parse manually.
    
    remaining = stripped
    
    # Define the order of units
    units_order = ['h', 'm', 's', 'ms']
    unit_to_seconds = {
        'h': 3600.0,
        'm': 60.0,
        's': 1.0,
        'ms': 0.001
    }
    
    total_seconds = 0.0
    last_unit_index = -1  # Track the index of the last unit used to enforce order
    
    while remaining:
        # Try to match a number followed by a unit
        # Number pattern: (?:0|[1-9]\d*)(?:\.\d+)?
        match = re.match(r'^(0|[1-9]\d*)(?:\.\d+)?', remaining)
        if not match:
            raise ValueError(f"Invalid number in duration string: '{remaining}'")
        
        number_str = match.group(0)
        remaining = remaining[len(number_str):]
        
        # Now we need to match a unit
        # Check for 'ms' first (since 'm' and 's' are prefixes of 'ms')
        if remaining.startswith('ms'):
            unit = 'ms'
            remaining = remaining[2:]
        elif remaining.startswith('h'):
            unit = 'h'
            remaining = remaining[1:]
        elif remaining.startswith('m'):
            unit = 'm'
            remaining = remaining[1:]
        elif remaining.startswith('s'):
            unit = 's'
            remaining = remaining[1:]
        else:
            raise ValueError(f"Invalid unit in duration string: '{remaining}'")
        
        # Check that the unit is in descending order
        unit_index = units_order.index(unit)
        if unit_index <= last_unit_index:
            raise ValueError(f"Units not in descending order or repeated: '{unit}'")
        last_unit_index = unit_index
        
        # Convert number to float and add to total
        number = float(number_str)
        total_seconds += number * unit_to_seconds[unit]
    
    if negative:
        total_seconds = -total_seconds
    
    return total_seconds
