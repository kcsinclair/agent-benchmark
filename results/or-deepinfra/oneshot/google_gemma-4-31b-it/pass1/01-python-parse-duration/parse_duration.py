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
            raise ValueError("Duration string must contain at least one component")

    # Regex to capture components: (number)(unit)
    # Number: digits, optional dot, digits. 
    # No leading dot, no trailing dot, no exponents.
    pattern = re.compile(r'^(\d+(?:\.\d+)?)(ms|h|m|s)$')
    
    # We will iterate through the string, extracting components one by one
    total_seconds = 0.0
    last_unit_rank = 5  # Rank: h=4, m=3, s=2, ms=1. Start at 5 to allow any first unit.
    unit_ranks = {'h': 4, 'm': 3, 's': 2, 'ms': 1}
    unit_multipliers = {'h': 3600.0, 'm': 60.0, 's': 1.0, 'ms': 0.001}
    seen_units = set()

    remaining = text
    while remaining:
        # Try to find the shortest possible match at the start of the string
        # Since units can be 's' or 'ms', we check for the longest unit match first 
        # or use a regex that handles the boundary.
        
        # We look for a number followed by one of the valid units.
        # We use a regex to find the first valid component.
        match = re.match(r'^(\d+(?:\.\d+)?)(ms|h|m|s)', remaining)
        if not match:
            raise ValueError(f"Invalid duration format at: {remaining}")
        
        val_str, unit = match.groups()
        
        # Validate unit order and uniqueness
        rank = unit_ranks[unit]
        if rank >= last_unit_rank:
            raise ValueError(f"Units must be in strictly descending order and not repeated: {unit}")
        if unit in seen_units:
            raise ValueError(f"Unit repeated: {unit}")
        
        # Calculate value
        total_seconds += float(val_str) * unit_multipliers[unit]
        
        # Update state
        seen_units.add(unit)
        last_unit_rank = rank
        remaining = remaining[match.end():]

    result = -total_seconds if is_negative else total_seconds
    return result
