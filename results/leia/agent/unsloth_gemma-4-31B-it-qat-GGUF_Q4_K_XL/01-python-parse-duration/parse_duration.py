import re

def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    
    text = text.strip()
    if not text:
        raise ValueError("Empty duration string")
    
    # Handle sign
    is_negative = False
    if text.startswith('-'):
        is_negative = True
        text = text[1:]
    
    # Regex for a single component: number followed by unit
    # Number: digits, optional dot, digits. 
    # No leading +, no exponents, no bare ., no trailing dot.
    # Valid: 2, 1.5, 0.25. Invalid: .5, 5.
    num_pattern = r'([0-9]+(?:\.[0-9]+)?)'
    unit_pattern = r'(h|m|s|ms)'
    component_pattern = num_pattern + unit_pattern
    
    # Find all components
    matches = list(re.finditer(component_pattern, text))
    
    if not matches:
        raise ValueError("No valid duration components found")
    
    # Check if the concatenated matches cover the entire string
    # This ensures no invalid characters or whitespace are inside
    reconstructed = "".join(m.group(0) for m in matches)
    if reconstructed != text:
        raise ValueError("Invalid characters or format in duration string")
    
    # Unit multipliers
    multipliers = {
        'h': 3600.0,
        'm': 60.0,
        's': 1.0,
        'ms': 0.001
    }
    
    # Order of units for validation
    unit_order = ['h', 'm', 's', 'ms']
    
    total_seconds = 0.0
    last_unit_index = -1
    
    for match in matches:
        val_str, unit = match.groups()
        val = float(val_str)
        
        unit_index = unit_order.index(unit)
        
        # Rule 2: Strictly descending order and no repeats
        if unit_index <= last_unit_index:
            raise ValueError(f"Units must be in strictly descending order and not repeated: {unit}")
        
        total_seconds += val * multipliers[unit]
        last_unit_index = unit_index
        
    return -total_seconds if is_negative else total_seconds
