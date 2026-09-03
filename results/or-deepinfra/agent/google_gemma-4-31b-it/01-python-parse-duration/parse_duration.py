import re

def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    
    text = text.strip()
    if not text:
        raise ValueError("Empty duration string")
    
    # Handle sign
    multiplier = 1.0
    if text.startswith('-'):
        multiplier = -1.0
        text = text[1:]
        if not text:
            raise ValueError("Duration string contains only a minus sign")
    elif text.startswith('+'):
        # Rule 1: No leading '+'
        raise ValueError("Leading '+' is not allowed")

    # Regex for a single component: number followed by unit
    # Number: digits, optional dot, digits. 
    # No leading/trailing dot, no .5, no 5.
    # Valid: 2, 1.5, 0.25
    num_pattern = r'([0-9]+(?:\.[0-9]+)?)'
    unit_pattern = r'(h|m|s|ms)'
    component_pattern = num_pattern + unit_pattern
    
    # Find all matches
    matches = re.findall(component_pattern, text)
    
    # Reconstruct the string from matches to check for invalid characters/whitespace
    reconstructed = ""
    for num, unit in matches:
        reconstructed += num + unit
    
    if reconstructed != text:
        raise ValueError("Invalid duration format or characters")
    
    if not matches:
        raise ValueError("No valid components found")
    
    # Unit values in seconds
    unit_map = {
        'h': 3600.0,
        'm': 60.0,
        's': 1.0,
        'ms': 0.001
    }
    
    # Order of units
    unit_order = ['h', 'm', 's', 'ms']
    unit_to_rank = {unit: i for i, unit in enumerate(unit_order)}
    
    total_seconds = 0.0
    last_rank = -1
    seen_units = set()
    
    for num_str, unit in matches:
        if unit in seen_units:
            raise ValueError(f"Repeated unit: {unit}")
        
        current_rank = unit_to_rank[unit]
        if current_rank <= last_rank:
            raise ValueError("Units must be in strictly descending order")
        
        total_seconds += float(num_str) * unit_map[unit]
        seen_units.add(unit)
        last_rank = current_rank
        
    return total_seconds * multiplier
