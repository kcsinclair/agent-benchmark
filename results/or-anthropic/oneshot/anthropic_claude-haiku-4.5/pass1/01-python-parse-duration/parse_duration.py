import re

def parse_duration(text: str) -> float:
    """
    Parse a human-readable duration string and return total seconds.
    
    Args:
        text: A duration string like "1h30m" or "-45m"
        
    Returns:
        Total duration in seconds as a float
        
    Raises:
        TypeError: If text is not a string
        ValueError: If the format is invalid
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")
    
    # Strip leading and trailing whitespace
    text = text.strip()
    
    # Check for empty string
    if not text:
        raise ValueError("Duration string cannot be empty")
    
    # Check for leading minus sign
    negative = False
    if text.startswith('-'):
        negative = True
        text = text[1:]
    
    # Pattern for a component: number (with optional decimal) followed by unit
    # Number: digits with optional decimal point and more digits
    component_pattern = r'^(\d+(?:\.\d+)?)(h|m|s|ms)'
    
    # Units in order of size (descending)
    unit_order = {'h': 0, 'm': 1, 's': 2, 'ms': 3}
    unit_to_seconds = {
        'h': 3600,
        'm': 60,
        's': 1,
        'ms': 0.001
    }
    
    total_seconds = 0.0
    last_unit_order = -1
    pos = 0
    found_any = False
    
    while pos < len(text):
        match = re.match(component_pattern, text[pos:])
        
        if not match:
            raise ValueError(f"Invalid duration format at position {pos}")
        
        number_str = match.group(1)
        unit = match.group(2)
        
        # Validate number format (no leading +, no exponents, no bare . or .5, no trailing dot)
        # The regex already ensures valid format: digits with optional .digits
        try:
            number = float(number_str)
        except ValueError:
            raise ValueError(f"Invalid number: {number_str}")
        
        # Check unit order
        current_unit_order = unit_order[unit]
        if current_unit_order <= last_unit_order:
            raise ValueError(f"Units must be in descending order of size")
        
        last_unit_order = current_unit_order
        
        # Add to total
        total_seconds += number * unit_to_seconds[unit]
        found_any = True
        
        # Move position forward
        pos += len(match.group(0))
    
    # Check if we consumed the entire string
    if pos < len(text):
        raise ValueError(f"Invalid duration format at position {pos}")
    
    # Check that at least one component was found
    if not found_any:
        raise ValueError("At least one component is required")
    
    # Apply negation if needed
    if negative:
        total_seconds = -total_seconds
    
    return total_seconds
