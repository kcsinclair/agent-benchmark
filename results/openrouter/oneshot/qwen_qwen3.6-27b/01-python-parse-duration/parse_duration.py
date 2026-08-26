"""Duration string parser module."""

import re


def parse_duration(text: str) -> float:
    """Parse a human-readable duration string and return total seconds as float.
    
    Args:
        text: A duration string like "1h30m", "90s", "-1.5h", etc.
        
    Returns:
        Total duration in seconds as a float.
        
    Raises:
        TypeError: If input is not a string.
        ValueError: If the string doesn't match the expected format.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    
    # Strip leading and trailing whitespace
    text = text.strip()
    
    if not text:
        raise ValueError("Empty string is not a valid duration")
    
    # Check for internal whitespace (any whitespace in the middle is invalid)
    if ' ' in text or '\t' in text or '\n' in text or '\r' in text:
        raise ValueError("Internal whitespace is not allowed")
    
    # Determine sign
    negative = False
    if text.startswith('-'):
        negative = True
        text = text[1:]
        if not text:
            raise ValueError("Minus sign with no following content")
    
    # Define the pattern for a single component: number followed by unit
    # Number: digits with optional fractional part, but no leading +, no exponents,
    # no bare . or .5, no trailing dot
    # Valid numbers: 2, 1.5, 0.25
    # Invalid: +2, 2e3, .5, 5.
    number_pattern = r'(\d+(?:\.\d+)?)'
    unit_pattern = r'(h|m|s|ms)'
    component_pattern = number_pattern + unit_pattern
    
    # Full pattern: one or more components in strict order h, m, s, ms
    # Each unit appears at most once, in descending order
    # We'll parse components and validate order
    
    # First, let's try to match the entire string as a sequence of components
    full_pattern = r'^(' + component_pattern + r')+$'
    
    match = re.match(full_pattern, text)
    if not match:
        raise ValueError(f"Invalid duration format: '{text}'")
    
    # Extract all components
    # We need to find all matches of the component pattern
    components = re.findall(component_pattern, text)
    
    if not components:
        raise ValueError("No components found")
    
    # Validate that the entire string was consumed (no extra characters)
    # Reconstruct from components and compare
    reconstructed = ''.join(f"{num}{unit}" for num, unit in components)
    if reconstructed != text:
        raise ValueError(f"Invalid duration format: '{text}'")
    
    # Define unit order and values
    unit_order = {'h': 0, 'm': 1, 's': 2, 'ms': 3}
    unit_values = {'h': 3600.0, 'm': 60.0, 's': 1.0, 'ms': 0.001}
    
    # Check for duplicate units and correct order
    seen_units = set()
    last_order = -1
    
    for num_str, unit in components:
        if unit in seen_units:
            raise ValueError(f"Duplicate unit: '{unit}'")
        seen_units.add(unit)
        
        current_order = unit_order[unit]
        if current_order <= last_order:
            raise ValueError(f"Units not in descending order: '{unit}' after previous unit")
        last_order = current_order
        
        # Parse the number
        try:
            num = float(num_str)
        except ValueError:
            raise ValueError(f"Invalid number: '{num_str}'")
    
    # Calculate total seconds
    total_seconds = 0.0
    for num_str, unit in components:
        num = float(num_str)
        total_seconds += num * unit_values[unit]
    
    if negative:
        total_seconds = -total_seconds
    
    return total_seconds
