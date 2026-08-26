import re

def parse_duration(text: str) -> float:
    """
    Parses a human-readable duration string and returns the total number of seconds as a float.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")

    text = text.strip()
    if not text:
        raise ValueError("Empty duration string")

    # Handle leading minus sign
    is_negative = False
    if text.startswith('-'):
        is_negative = True
        text = text[1:]
        if not text:
            raise ValueError("Duration string contains only a minus sign")

    # Regex for a single component: number followed by unit
    # Number: digits, optional dot, digits. No leading/trailing dot.
    # Unit: h, m, s, ms
    # We use a regex to find all components and check if the whole string is consumed.
    component_pattern = re.compile(r'^(\d+(?:\.\d+)?)(h|m|s|ms)')
    
    total_seconds = 0.0
    remaining = text
    last_unit_index = -1
    
    # Unit order mapping
    unit_map = {'h': 0, 'm': 1, 's': 2, 'ms': 3}
    unit_values = {'h': 3600.0, 'm': 60.0, 's': 1.0, 'ms': 0.001}
    
    while remaining:
        match = component_pattern.match(remaining)
        if not match:
            raise ValueError(f"Invalid duration format at: {remaining}")
        
        val_str, unit = match.groups()
        val = float(val_str)
        
        # Check unit order and uniqueness
        current_unit_index = unit_map[unit]
        if current_unit_index <= last_unit_index:
            raise ValueError(f"Units must be in strictly descending order and unique: {unit}")
        
        total_seconds += val * unit_values[unit]
        last_unit_index = current_unit_index
        remaining = remaining[match.end():]

    result = -total_seconds if is_negative else total_seconds
    return result
