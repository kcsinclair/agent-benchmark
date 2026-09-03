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

    # Check for sign
    is_negative = False
    if text.startswith('-'):
        is_negative = True
        text = text[1:]
    elif text.startswith('+'):
        raise ValueError("Invalid duration format")

    # Component regex: number followed by unit.
    # Number: \d+(?:\.\d+)?
    # Unit: ms|s|m|h (order matters for 'ms' vs 's')
    # We use ms|s|m|h to ensure 'ms' is matched before 's'.
    component_regex = re.compile(r'(\d+(?:\.\d+)?)(ms|s|m|h)')
    
    matches = list(component_regex.finditer(text))
    
    if not matches:
        raise ValueError("No valid components found")
    
    # Check if the matches cover the entire string without gaps or extra characters
    last_end = 0
    for m in matches:
        if m.start() != last_end:
            raise ValueError("Invalid characters or gaps between components")
        last_end = m.end()
    
    if last_end != len(text):
        raise ValueError("Trailing characters after components")
        
    # Now validate order and uniqueness
    current_unit_idx = -1
    unit_order_map = {'h': 0, 'm': 1, 's': 2, 'ms': 3}
    unit_values = {'h': 3600.0, 'm': 60.0, 's': 1.0, 'ms': 0.001}
    
    total_seconds = 0.0
    
    for m in matches:
        val_str, unit = m.groups()
        val = float(val_str)
        
        u_idx = unit_order_map[unit]
        # The rule says "strictly descending order of size (h before m before s before ms)".
        # This means the indices in unit_order_map must be strictly increasing.
        if u_idx <= current_unit_idx:
            raise ValueError("Units must be in descending order and unique")
        
        current_unit_idx = u_idx
        total_seconds += val * unit_values[unit]
        
    if is_negative:
        total_seconds = -total_seconds
        
    return total_seconds
