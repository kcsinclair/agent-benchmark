import re

def parse_duration(text: str) -> float:
    """
    Parses a human-readable duration string and returns the total number of seconds as a float.
    
    Supported units: h (hours), m (minutes), s (seconds), ms (milliseconds).
    Units must be in descending order and appear at most once.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")

    text = text.strip()
    if not text:
        raise ValueError("Empty duration string")

    # Check for sign
    sign = 1.0
    if text.startswith('-'):
        sign = -1.0
        text = text[1:]
    elif text.startswith('+'):
        raise ValueError("Leading '+' is not allowed")

    # Regex to match components: number followed by unit
    # Number: digits, optional dot followed by digits. 
    # Must not be just '.' or end with '.'
    # Unit: h, m, s, ms
    
    # To handle 'ms' vs 'm' correctly in regex, we put 'ms' first.
    comp_pattern = re.compile(r'(\d+(?:\.\d+)?)(ms|h|m|s)')
    
    # Find all matches
    all_matches = list(comp_pattern.finditer(text))
    
    if not all_matches:
        raise ValueError("No valid components found")
    
    # Check if the matches cover the entire string exactly
    # This ensures no invalid characters or misplaced separators exist.
    reconstructed = "".join(m.group(0) for m in all_matches)
    if reconstructed != text:
        raise ValueError("Invalid characters or format in duration string")

    # Map units to seconds
    unit_map = {
        'h': 3600.0,
        'm': 60.0,
        's': 1.0,
        'ms': 0.001
    }
    
    # Order of units allowed: h -> m -> s -> ms
    allowed_order = ['h', 'm', 's', 'ms']
    last_unit_idx = -1
    total_seconds = 0.0
    
    for m in all_matches:
        val_str = m.group(1)
        unit = m.group(2)
        
        val = float(val_str)
        
        current_unit_idx = allowed_order.index(unit)
        if current_unit_idx <= last_unit_idx:
            raise ValueError("Units must be in strictly descending order and appear at most once")
        
        total_seconds += val * unit_map[unit]
        last_unit_idx = current_unit_idx

    return total_seconds * sign
