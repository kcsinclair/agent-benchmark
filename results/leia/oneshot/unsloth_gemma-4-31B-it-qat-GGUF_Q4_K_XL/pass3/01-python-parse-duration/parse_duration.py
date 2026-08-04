import re

def parse_duration(text: str) -> float:
    """
    Parses a human-readable duration string and returns the total number of seconds.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")

    text = text.strip()
    if not text:
        raise ValueError("Duration string cannot be empty")

    # Handle the optional leading minus sign
    is_negative = False
    if text.startswith('-'):
        is_negative = True
        text = text[1:]
        if not text:
            raise ValueError("Duration string contains only a minus sign")

    # Regex for a single component: 
    # Number: digits, optional dot, digits (no leading/trailing dots, no .5)
    # Unit: h, m, s, or ms
    # Pattern: (\d+(\.\d+)?)(h|m|s|ms)
    component_pattern = re.compile(r'^(\d+(?:\.\d+)?)(h|m|s|ms)$')
    
    # We need to parse the string sequentially to ensure no whitespace 
    # and strictly descending order of units.
    units_order = {'h': 3, 'm': 2, 's': 1, 'ms': 0}
    last_unit_rank = 4  # Higher than any possible rank
    total_seconds = 0.0
    remaining = text
    found_component = False

    while remaining:
        # Find the first occurrence of a unit character to split the number from the unit
        # We look for the first character that is part of a unit
        match_idx = -1
        for i, char in enumerate(remaining):
            if char in 'hms':
                match_idx = i
                break
        
        if match_idx == -1:
            raise ValueError("Missing unit in duration string")

        # Extract the potential component (number + unit)
        # Since units can be 'ms', we check if the unit is 'ms' or just 'm'
        if remaining[match_idx:match_idx+2] == 'ms':
            unit = 'ms'
            unit_len = 2
        else:
            unit = remaining[match_idx]
            unit_len = 1
        
        number_part = remaining[:match_idx]
        component = number_part + unit
        
        # Validate the component format using the regex
        match = component_pattern.match(component)
        if not match:
            raise ValueError(f"Invalid component format: {component}")
        
        val_str, unit_str = match.groups()
        val = float(val_str)
        
        # Validate unit order and uniqueness
        current_unit_rank = units_order[unit_str]
        if current_unit_rank >= last_unit_rank:
            raise ValueError(f"Units must be in strictly descending order and unique: {unit_str}")
        
        # Calculate seconds
        if unit_str == 'h':
            total_seconds += val * 3600
        elif unit_str == 'm':
            total_seconds += val * 60
        elif unit_str == 's':
            total_seconds += val
        elif unit_str == 'ms':
            total_seconds += val / 1000.0
            
        last_unit_rank = current_unit_rank
        remaining = remaining[match_idx + unit_len:]
        found_component = True

    if not found_component:
        raise ValueError("No valid duration components found")

    return -total_seconds if is_negative else total_seconds
