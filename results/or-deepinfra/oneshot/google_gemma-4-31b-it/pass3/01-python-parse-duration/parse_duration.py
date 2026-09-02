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

    # Handle the leading sign
    is_negative = False
    if text.startswith('-'):
        is_negative = True
        text = text[1:]
        if not text:
            raise ValueError("Duration string contains only a minus sign")

    # Regex to capture components: (number)(unit)
    # Number: digits, optional dot, digits. 
    # Note: we must ensure no trailing dot and no bare dot.
    # The pattern [0-9]*\.?[0-9]+ ensures at least one digit and no trailing dot.
    # However, the prompt says "no bare . or .5", meaning it must start with a digit.
    # Correct number pattern: [0-9]+(\.[0-9]+)?
    pattern = re.compile(r'^([0-9]+(?:\.[0-9]+)?)(h|m|s|ms)$')
    
    total_seconds = 0.0
    units_seen = set()
    last_unit_rank = -1 # Rank: h=0, m=1, s=2, ms=3
    unit_map = {'h': 3600.0, 'm': 60.0, 's': 1.0, 'ms': 0.001}
    unit_rank = {'h': 0, 'm': 1, 's': 2, 'ms': 3}

    while text:
        # We try to match the pattern at the start of the remaining string
        match = re.match(r'^([0-9]+(?:\.[0-9]+)?)(h|m|s|ms)', text)
        if not match:
            raise ValueError(f"Invalid duration format at: {text}")
        
        val_str, unit = match.groups()
        
        # Validate unit order and uniqueness
        rank = unit_rank[unit]
        if rank <= last_unit_rank:
            raise ValueError(f"Units must be in strictly descending order and not repeated: {unit}")
        if unit in units_seen:
            raise ValueError(f"Unit repeated: {unit}")
        
        # Calculate value
        total_seconds += float(val_str) * unit_map[unit]
        
        # Update state
        units_seen.add(unit)
        last_unit_rank = rank
        text = text[match.end():]

    # If we reached here, we have at least one component (checked by while loop and initial empty check)
    # but we must ensure the loop actually processed something.
    if not units_seen:
        raise ValueError("No valid duration components found")

    return -total_seconds if is_negative else total_seconds
