import re


def parse_duration(text: str) -> float:
    """
    Parse a human-readable duration string and return total seconds as a float.
    
    Format: optional minus sign followed by one or more components (number + unit).
    Units: h (hours), m (minutes), s (seconds), ms (milliseconds)
    Units must appear in descending order and each at most once.
    
    Args:
        text: A duration string (e.g., "1h30m", "250ms", "-45m")
    
    Returns:
        Total duration in seconds as a float
    
    Raises:
        TypeError: If text is not a string
        ValueError: If the format is invalid
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected string, got {type(text).__name__}")
    
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
    
    # Check if anything remains after removing minus
    if not text:
        raise ValueError("Duration string cannot be just a minus sign")
    
    # Pattern to match components: number (with optional decimal) followed by unit
    # Number: digits with optional decimal point and more digits
    # Unit: h, m, s, or ms
    pattern = r'^([0-9]+(?:\.[0-9]+)?)(h|m|s|ms)(.*)$'
    
    total_seconds = 0.0
    last_unit_order = -1  # Track order: h=3, m=2, s=1, ms=0
    unit_order = {'h': 3, 'm': 2, 's': 1, 'ms': 0}
    unit_to_seconds = {'h': 3600, 'm': 60, 's': 1, 'ms': 0.001}
    
    remaining = text
    
    while remaining:
        match = re.match(pattern, remaining)
        
        if not match:
            raise ValueError(f"Invalid duration format: '{text}'")
        
        number_str, unit, rest = match.groups()
        
        # Validate number format
        if not re.match(r'^[0-9]+(?:\.[0-9]+)?$', number_str):
            raise ValueError(f"Invalid number format: '{number_str}'")
        
        # Check for invalid patterns like "5." or ".5"
        if number_str.endswith('.') or number_str.startswith('.'):
            raise ValueError(f"Invalid number format: '{number_str}'")
        
        try:
            number = float(number_str)
        except ValueError:
            raise ValueError(f"Invalid number: '{number_str}'")
        
        # Check unit order (must be descending)
        current_unit_order = unit_order[unit]
        if current_unit_order >= last_unit_order:
            raise ValueError(f"Units must be in descending order (h > m > s > ms)")
        
        last_unit_order = current_unit_order
        
        # Add to total
        total_seconds += number * unit_to_seconds[unit]
        
        remaining = rest
    
    # Check if there's any remaining text that couldn't be parsed
    if remaining:
        raise ValueError(f"Invalid duration format: '{text}'")
    
    # Apply negative sign if present
    if negative:
        total_seconds = -total_seconds
    
    return total_seconds
