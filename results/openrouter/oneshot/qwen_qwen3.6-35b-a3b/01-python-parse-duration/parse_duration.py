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
    
    # The remaining string must match the pattern of components
    # Each component is a number followed by a unit
    # Units must appear in order: h, m, s, ms (each at most once)
    
    # Define the valid units in order
    units_order = ['h', 'm', 's', 'ms']
    
    # We need to parse the string into components
    # Each component: number (non-negative decimal) followed by unit
    # Number: digits with optional fractional part, no leading +, no exponents, no bare . or .5, no trailing dot
    
    # Let's use a regex to validate and parse
    # The entire string after stripping minus should be composed of valid components
    
    # Pattern for a number: one or more digits, optionally followed by a dot and one or more digits
    # This ensures no bare . or .5 or trailing dot
    number_pattern = r'\d+(\.\d+)?'
    
    # Pattern for a unit: h, m, s, or ms
    # Note: ms must come before m and s in alternation to avoid partial matches
    unit_pattern = r'(ms|h|m|s)'
    
    # Full component pattern
    component_pattern = number_pattern + unit_pattern
    
    # The entire string should match one or more components concatenated
    full_pattern = '^(' + component_pattern + ')+$'
    
    if not re.match(full_pattern, stripped):
        raise ValueError(f"Invalid duration string: {stripped}")
    
    # Now parse the components
    # Find all matches
    matches = re.finditer(component_pattern, stripped)
    
    components = []
    for match in matches:
        num_str = match.group(0)
        # Extract the number and unit
        # The number is everything before the last 1 or 2 characters (for ms)
        # Actually, let's parse more carefully
        # The match is like "1.5h" or "250ms"
        # We need to separate the number from the unit
        
        # Find where the unit starts
        # Units are: ms, h, m, s
        # Try to match the unit at the end
        if num_str.endswith('ms'):
            unit = 'ms'
            num_part = num_str[:-2]
        elif num_str.endswith('h'):
            unit = 'h'
            num_part = num_str[:-1]
        elif num_str.endswith('m'):
            unit = 'm'
            num_part = num_str[:-1]
        elif num_str.endswith('s'):
            unit = 's'
            num_part = num_str[:-1]
        else:
            raise ValueError(f"Could not parse unit from: {num_str}")
        
        # Validate the number part
        if not re.match(r'^\d+(\.\d+)?$', num_part):
            raise ValueError(f"Invalid number: {num_part}")
        
        num = float(num_part)
        components.append((num, unit))
    
    # Check that units are in strictly descending order and each appears at most once
    seen_units = set()
    last_index = -1
    
    for num, unit in components:
        if unit in seen_units:
            raise ValueError(f"Repeated unit: {unit}")
        seen_units.add(unit)
        
        current_index = units_order.index(unit)
        if current_index <= last_index:
            raise ValueError(f"Units not in descending order: {unit} after previous unit")
        last_index = current_index
    
    # Calculate total seconds
    total_seconds = 0.0
    for num, unit in components:
        if unit == 'h':
            total_seconds += num * 3600
        elif unit == 'm':
            total_seconds += num * 60
        elif unit == 's':
            total_seconds += num
        elif unit == 'ms':
            total_seconds += num / 1000
    
    if negative:
        total_seconds = -total_seconds
    
    return total_seconds
