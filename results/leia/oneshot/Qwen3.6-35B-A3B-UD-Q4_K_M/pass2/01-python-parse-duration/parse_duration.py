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
    
    # Define the pattern for a valid component: number followed by unit
    # Number: non-negative decimal with optional fractional part
    # Valid numbers: digits with optional dot and more digits
    # No leading +, no exponents, no bare . or .5, no trailing dot
    # So: one or more digits, optionally followed by a dot and one or more digits
    number_pattern = r'(\d+(?:\.\d+)?)'
    
    # Units: ms, s, m, h (ms must come before s to avoid ambiguity)
    # We need to match components in order: h, m, s, ms
    # Each unit can appear at most once
    
    # Let's parse the string by finding all components
    # We'll use a regex to find all valid components
    component_pattern = r'(\d+(?:\.\d+)?)(ms|h|m|s)'
    
    # Find all matches
    matches = list(re.finditer(component_pattern, stripped))
    
    # Check that the entire stripped string is consumed by the matches
    if not matches:
        raise ValueError("No valid components found")
    
    # Check that matches cover the entire string with no gaps
    pos = 0
    for match in matches:
        if match.start() != pos:
            raise ValueError("Unexpected characters between components")
        pos = match.end()
    
    if pos != len(stripped):
        raise ValueError("Unexpected characters after last component")
    
    # Now validate the order and uniqueness of units
    unit_order = {'h': 0, 'm': 1, 's': 2, 'ms': 3}
    last_order = -1
    seen_units = set()
    
    total_seconds = 0.0
    
    for match in matches:
        number_str = match.group(1)
        unit = match.group(2)
        
        # Check unit order
        current_order = unit_order[unit]
        if current_order <= last_order:
            raise ValueError(f"Units not in strictly descending order: {unit} after previous unit")
        
        # Check for duplicate units
        if unit in seen_units:
            raise ValueError(f"Duplicate unit: {unit}")
        
        seen_units.add(unit)
        last_order = current_order
        
        # Parse the number
        try:
            number = float(number_str)
        except ValueError:
            raise ValueError(f"Invalid number: {number_str}")
        
        # Convert to seconds based on unit
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
