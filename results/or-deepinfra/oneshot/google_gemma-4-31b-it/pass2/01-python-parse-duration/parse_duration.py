import re

def parse_duration(text: str) -> float:
    """
    Parses a human-readable duration string and returns the total seconds as a float.
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
            raise ValueError("Duration string must contain at least one component")

    # Regex for a single component: 
    # Number: digits, optional dot, digits. 
    # (Prevents .5 or 5. by requiring digits on both sides of dot if dot exists)
    # Unit: h, m, s, or ms
    pattern = re.compile(r'^(\d+(?:\.\d+)?)(h|m|s|ms)$')
    
    # Units mapping to seconds
    unit_map = {
        'h': 3600.0,
        'm': 60.0,
        's': 1.0,
        'ms': 0.001
    }
    
    # Order of units for validation
    unit_order = ['h', 'm', 's', 'ms']
    
    total_seconds = 0.0
    last_unit_index = -1
    remaining_text = text

    while remaining_text:
        # We need to find the shortest match that satisfies the pattern at the start
        # Since units can be 's' or 'ms', we check for the longest unit match first
        # to avoid 'ms' being parsed as 'm' followed by 's'.
        
        # Try to find a match at the start of the string
        # We iterate through possible unit lengths (2 for 'ms', 1 for others)
        match_found = False
        for unit_len in [2, 1]:
            # This is a bit naive; instead, let's use a regex that captures the 
            # number and the unit specifically.
            pass
        
        # Correct approach: Use a regex to find the first valid component
        # We look for the number and then the unit.
        match = re.match(r'^(\d+(?:\.\d+)?)(h|m|s|ms)', remaining_text)
        if not match:
            raise ValueError(f"Invalid duration format: {remaining_text}")
        
        val_str, unit = match.groups()
        val = float(val_str)
        
        # Validate unit order and uniqueness
        current_unit_index = unit_order.index(unit)
        if current_unit_index <= last_unit_index:
            raise ValueError(f"Units must be in strictly descending order: {unit}")
        
        total_seconds += val * unit_map[unit]
        last_unit_index = current_unit_index
        
        # Advance the string pointer
        remaining_text = remaining_text[match.end():]

    return -total_seconds if is_negative else total_seconds
