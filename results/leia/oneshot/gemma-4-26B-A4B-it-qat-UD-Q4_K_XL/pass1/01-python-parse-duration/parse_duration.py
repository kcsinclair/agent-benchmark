import re

def parse_duration(text: str) -> float:
    """
    Parses a human-readable duration string and returns the total number of seconds.
    
    Supported units: h (hours), m (minutes), s (seconds), ms (milliseconds).
    Units must be in descending order and appear at most once.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")

    text = text.strip()
    if not text:
        raise ValueError("Empty duration string")

    # Check for leading sign
    sign = 1.0
    if text.startswith('-'):
        sign = -1.0
        text = text[1:]
    elif text.startswith('+'):
        # Rule 1: No leading '+' allowed
        raise ValueError("Leading '+' is not allowed")

    # Regex to find components: a number followed by a unit
    # Number: digits, optional dot followed by digits (e.g., 1, 1.5)
    # Unit: h, m, s, or ms
    # We use a regex that captures the number and the unit separately.
    # The pattern ensures we don't allow trailing dots or bare dots.
    pattern = r'^(\d+(?:\.\d+)?)(h|m|s|ms)$'
    
    # To validate the whole string, we'll find all matches and ensure 
    # they consume the entire string without gaps or invalid characters.
    
    # We'll use finditer to get all matches and track the end position of the last match
    matches = list(re.finditer(pattern, text))
    
    if not matches:
        raise ValueError("No valid duration components found")

    # Check if the matches cover the entire string (no gaps/invalid chars)
    current_pos = 0
    total_seconds = 0.0
    
    # Track units to ensure descending order and no repeats
    # Order: h (3600), m (60), s (1), ms (0.001)
    unit_map = {
        'h': (3600.0, 4),
        'm': (60.0, 3),
        's': (1.0, 2),
        'ms': (0.001, 1)
    }
    
    last_unit_rank = 5 # Higher than any unit rank

    for match in matches:
        start, end = match.span()
        
        # If there is a gap between the last match and this one, it's invalid
        if start != current_pos:
            raise ValueError("Invalid characters or whitespace between components")
        
        val_str, unit_str = match.groups()
        
        # Validate number format (regex handles most, but we check for edge cases)
        try:
            val = float(val_str)
        except ValueError:
            raise ValueError(f"Invalid number: {val_str}")

        # Check unit order and uniqueness
        unit_seconds, unit_rank = unit_map[unit_str]
        if unit_rank >= last_unit_rank:
            raise ValueError(f"Units must be in descending order and unique: {unit_str}")
        
        total_seconds += val * unit_seconds
        last_unit_rank = unit_rank
        current_pos = end

    # If we didn't reach the end of the string, there's trailing garbage
    if current_pos != len(text):
        raise ValueError("Invalid characters at end of string")

    return total_seconds * sign
