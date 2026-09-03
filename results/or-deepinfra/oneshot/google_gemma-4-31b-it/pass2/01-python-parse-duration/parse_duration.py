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
            raise ValueError("Duration string contains only a minus sign")

    # Regex to find components: (number)(unit)
    # Number: digits, optional dot, digits. 
    # Note: .5 and 5. are forbidden per rules.
    # Valid number: \d+(\.\d+)?
    pattern = re.compile(r'^(\d+(?:\.\d+)?)(ms|h|m|s)$')
    
    # We will iterate through the string and extract components
    total_seconds = 0.0
    last_unit_rank = 5  # Rank to ensure strictly descending order
    
    # Unit mapping: rank for order, multiplier for seconds
    units_map = {
        'h': (4, 3600.0),
        'm': (3, 60.0),
        's': (2, 1.0),
        'ms': (1, 0.001)
    }
    
    remaining = text
    found_any = False
    
    while remaining:
        # We need to find the shortest possible match at the start of the string
        # because 'ms' starts with 'm'. We check for the unit.
        match_found = False
        # Try to match the longest possible unit first (ms) to avoid greedy 'm'
        for unit_key in ['ms', 'h', 'm', 's']:
            # This is a bit tricky with regex; let's use a more robust approach.
            # We look for the first occurrence of any unit character.
            pass
        
        # Better approach: find the first character that is a unit
        # Since numbers are \d and ., the first non-digit/non-dot is the unit start.
        split_idx = -1
        for i, char in enumerate(remaining):
            if char in 'hms':
                split_idx = i
                break
        
        if split_idx == -1:
            raise ValueError("Missing unit in duration string")
            
        # Extract the number part and the unit part
        num_str = remaining[:split_idx]
        # The unit could be 's', 'm', 'h', or 'ms'
        # Check if it's 'ms' first
        if remaining[split_idx:].startswith('ms'):
            unit = 'ms'
            unit_len = 2
        else:
            unit = remaining[split_idx]
            unit_len = 1
            
        # Validate number format (no leading/trailing dots, no bare dots)
        if not num_str or not re.fullmatch(r'\d+(\.\d+)?', num_str):
            raise ValueError(f"Invalid number format: {num_str}")
            
        # Validate unit order and uniqueness
        rank, multiplier = units_map[unit]
        if rank >= last_unit_rank:
            raise ValueError(f"Units must be in strictly descending order: {unit}")
        
        total_seconds += float(num_str) * multiplier
        last_unit_rank = rank
        found_any = True
        
        # Advance the string
        remaining = remaining[split_idx + unit_len:]
        
        # Check for illegal whitespace between components
        if remaining and remaining[0].isspace():
            raise ValueError("Whitespace not allowed between components")

    if not found_any:
        raise ValueError("No valid duration components found")

    return -total_seconds if is_negative else total_seconds
